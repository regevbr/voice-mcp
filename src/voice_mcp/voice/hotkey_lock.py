"""
Cross-platform hotkey locking system for voice-mcp server.

Provides exclusive hotkey binding coordination across multiple server instances
using file-based locks with automatic cleanup and cross-platform compatibility.
"""

import os
import platform
import tempfile
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class CrossPlatformLock(ABC):
    """Abstract base class for cross-platform locking mechanisms."""

    @abstractmethod
    def try_acquire_immediate(self) -> bool:
        """
        Try to acquire lock immediately without blocking.

        Returns:
            True if lock acquired successfully, False if already held by another process
        """
        pass

    @abstractmethod
    def release_immediate(self) -> bool:
        """
        Release the lock immediately.

        Returns:
            True if released successfully, False if not held or error
        """
        pass

    @abstractmethod
    def is_locked_by_me(self) -> bool:
        """
        Check if lock is currently held by this process.

        Returns:
            True if held by this process, False otherwise
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup lock resources."""
        pass


class FileBasedLock(CrossPlatformLock):
    """Cross-platform file-based lock implementation."""

    def __init__(self, lock_file_path: Path):
        """
        Initialize file-based lock.

        Args:
            lock_file_path: Path to the lock file
        """
        self.lock_file_path = lock_file_path
        self.lock_file: Any | None = None
        self._lock = threading.RLock()
        self._acquired = False

        # Ensure lock directory exists
        self.lock_file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.debug("FileBasedLock initialized", path=str(lock_file_path))

    def try_acquire_immediate(self) -> bool:
        """Try to acquire the file lock immediately."""
        with self._lock:
            if self._acquired:
                return True

            try:
                # Open lock file in exclusive mode
                self.lock_file = open(self.lock_file_path, "w")

                # Try platform-specific locking
                if platform.system().lower() in ("linux", "darwin"):
                    success = self._try_unix_lock()
                elif platform.system().lower() == "windows":
                    success = self._try_windows_lock()
                else:
                    logger.warning(
                        "Unsupported platform for file locking",
                        platform=platform.system(),
                    )
                    success = False

                if success:
                    # Write process info to lock file
                    self.lock_file.write(f"{os.getpid()}\n{time.time()}\n")
                    self.lock_file.flush()
                    self._acquired = True
                    logger.debug("File lock acquired successfully")
                    return True
                else:
                    # Failed to acquire, cleanup
                    if self.lock_file:
                        self.lock_file.close()
                        self.lock_file = None
                    return False

            except OSError as e:
                logger.debug(f"Failed to acquire file lock: {e}")
                if self.lock_file:
                    try:
                        self.lock_file.close()
                    except Exception:
                        pass
                    self.lock_file = None
                return False

    def _try_unix_lock(self) -> bool:
        """Try to acquire lock using Unix fcntl."""
        try:
            import fcntl

            if self.lock_file:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            return False
        except (ImportError, OSError):
            return False

    def _try_windows_lock(self) -> bool:
        """Try to acquire lock using Windows msvcrt."""
        try:
            import msvcrt

            # Lock the first byte of the file
            if self.lock_file:
                msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)  # type: ignore[attr-defined]
                return True
            return False
        except (ImportError, OSError):
            return False

    def release_immediate(self) -> bool:
        """Release the file lock immediately."""
        with self._lock:
            if not self._acquired or not self.lock_file:
                return True

            try:
                # Platform-specific unlock
                if platform.system().lower() in ("linux", "darwin"):
                    self._release_unix_lock()
                elif platform.system().lower() == "windows":
                    self._release_windows_lock()

                # Close and cleanup
                self.lock_file.close()
                self.lock_file = None
                self._acquired = False

                # Remove lock file if it exists
                try:
                    if self.lock_file_path.exists():
                        self.lock_file_path.unlink()
                except Exception as e:
                    logger.warning(f"Could not remove lock file: {e}")

                logger.debug("File lock released successfully")
                return True

            except Exception as e:
                logger.error(f"Error releasing file lock: {e}")
                return False

    def _release_unix_lock(self) -> None:
        """Release Unix fcntl lock."""
        try:
            import fcntl

            if self.lock_file:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
        except (ImportError, OSError) as e:
            logger.warning(f"Error releasing Unix lock: {e}")

    def _release_windows_lock(self) -> None:
        """Release Windows msvcrt lock."""
        try:
            import msvcrt

            if self.lock_file:
                msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]
        except (ImportError, OSError) as e:
            logger.warning(f"Error releasing Windows lock: {e}")

    def is_locked_by_me(self) -> bool:
        """Check if lock is held by this process."""
        with self._lock:
            return self._acquired and self.lock_file is not None

    def cleanup(self) -> None:
        """Cleanup lock resources."""
        self.release_immediate()


class SemaphoreLock(CrossPlatformLock):
    """Fallback semaphore-based lock implementation."""

    def __init__(self, lock_name: str):
        """
        Initialize semaphore-based lock.

        Args:
            lock_name: Name for the semaphore
        """
        try:
            import multiprocessing

            self.semaphore: Any | None = multiprocessing.Semaphore(
                1
            )  # Remove name parameter - not supported
            self._acquired = False
            self._lock = threading.RLock()
            logger.debug("SemaphoreLock initialized", name=lock_name)
        except Exception as e:
            logger.error(f"Failed to initialize semaphore lock: {e}")
            self.semaphore = None

    def try_acquire_immediate(self) -> bool:
        """Try to acquire semaphore immediately."""
        if not self.semaphore:
            return False

        with self._lock:
            if self._acquired:
                return True

            try:
                # Non-blocking acquire
                if self.semaphore.acquire(block=False):
                    self._acquired = True
                    logger.debug("Semaphore lock acquired successfully")
                    return True
                else:
                    logger.debug("Semaphore lock already held")
                    return False
            except Exception as e:
                logger.debug(f"Failed to acquire semaphore lock: {e}")
                return False

    def release_immediate(self) -> bool:
        """Release semaphore immediately."""
        if not self.semaphore:
            return True

        with self._lock:
            if not self._acquired:
                return True

            try:
                self.semaphore.release()
                self._acquired = False
                logger.debug("Semaphore lock released successfully")
                return True
            except Exception as e:
                logger.error(f"Error releasing semaphore lock: {e}")
                return False

    def is_locked_by_me(self) -> bool:
        """Check if semaphore is held by this process."""
        with self._lock:
            return self._acquired

    def cleanup(self) -> None:
        """Cleanup semaphore resources."""
        self.release_immediate()


class HotkeyLockManager:
    """Manages exclusive hotkey binding coordination across processes."""

    def __init__(
        self,
        hotkey_name: str,
        lock_directory: str | None = None,
        fallback_semaphore: bool = True,
    ):
        """
        Initialize hotkey lock manager.

        Args:
            hotkey_name: Name of the hotkey to coordinate (e.g., "menu", "f12")
            lock_directory: Optional directory for lock files (auto-detected if None)
            fallback_semaphore: Allow semaphore fallback if file locks fail
        """
        self.hotkey_name = hotkey_name
        self.fallback_semaphore = fallback_semaphore
        self.lock: CrossPlatformLock | None = None
        self._lock_thread: threading.Thread | None = None
        self._stop_lock_thread = threading.Event()

        # Determine lock directory
        if lock_directory:
            self.lock_directory = Path(lock_directory)
        else:
            self.lock_directory = self._get_default_lock_directory()

        logger.info(
            "HotkeyLockManager initialized",
            hotkey=hotkey_name,
            lock_dir=str(self.lock_directory),
        )

        # Create the appropriate lock implementation
        self._create_lock_implementation()

    def _get_default_lock_directory(self) -> Path:
        """Get default lock directory for the platform."""
        try:
            # Try platform-specific locations
            if platform.system().lower() == "windows":
                temp_dir = Path(tempfile.gettempdir()) / "voice-mcp-locks"
            else:
                # Unix-like systems: try XDG_RUNTIME_DIR first, then /tmp
                runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
                if runtime_dir:
                    temp_dir = Path(runtime_dir) / "voice-mcp-locks"
                else:
                    temp_dir = Path(tempfile.gettempdir()) / "voice-mcp-locks"

            # Ensure directory exists
            temp_dir.mkdir(parents=True, exist_ok=True)
            return temp_dir

        except Exception as e:
            logger.warning(f"Could not create lock directory: {e}")
            # Fallback to system temp
            return Path(tempfile.gettempdir()) / "voice-mcp-locks"

    def _create_lock_implementation(self) -> None:
        """Create the appropriate lock implementation for the platform."""
        lock_filename = f"hotkey-{self.hotkey_name.replace('+', '-')}.lock"
        lock_file_path = self.lock_directory / lock_filename

        try:
            # Try file-based lock first
            self.lock = FileBasedLock(lock_file_path)
            logger.debug("Using FileBasedLock implementation")
        except Exception as e:
            logger.warning(f"FileBasedLock failed: {e}")
            # Fallback to semaphore if enabled
            if self.fallback_semaphore:
                try:
                    self.lock = SemaphoreLock(self.hotkey_name)
                    logger.debug("Using SemaphoreLock implementation")
                except Exception as e2:
                    logger.error(f"All lock implementations failed: {e2}")
                    self.lock = None
            else:
                logger.warning("Semaphore fallback disabled, no lock available")
                self.lock = None

    def try_acquire_for_processing(self) -> bool:
        """
        Try to acquire exclusive rights to process the hotkey immediately.

        Returns:
            True if acquired and should process hotkey, False if should forfeit
        """
        if not self.lock:
            logger.warning("No lock implementation available, processing anyway")
            return True

        success = self.lock.try_acquire_immediate()
        if success:
            logger.info(f"Acquired hotkey processing lock for '{self.hotkey_name}'")
            # Start background thread to release lock after processing duration
            self._start_lock_release_timer()
        else:
            logger.debug(
                f"Hotkey lock for '{self.hotkey_name}' held by another process, forfeiting"
            )

        return success

    def _start_lock_release_timer(self) -> None:
        """Start background timer to release lock after processing duration."""
        # Calculate lock duration based on STT settings
        from ..config import config

        lock_duration = max(
            config.stt_silence_threshold + 2.0, 6.0
        )  # Minimum 6 seconds

        logger.debug(f"Starting lock release timer for {lock_duration} seconds")

        self._stop_lock_thread.clear()
        self._lock_thread = threading.Thread(
            target=self._lock_release_worker,
            args=(lock_duration,),
            daemon=True,
            name="hotkey-lock-release",
        )
        self._lock_thread.start()

    def _lock_release_worker(self, duration: float) -> None:
        """Background worker to release lock after specified duration."""
        try:
            # Wait for the duration or stop signal
            if self._stop_lock_thread.wait(timeout=duration):
                logger.debug("Lock release timer stopped early")
            else:
                logger.debug(f"Lock release timer expired after {duration} seconds")

            # Release the lock
            self.release_immediate()

        except Exception as e:
            logger.error(f"Error in lock release worker: {e}")
            # Ensure lock is released even on error
            try:
                self.release_immediate()
            except Exception:
                pass

    def release_immediate(self) -> bool:
        """Release the hotkey processing lock immediately."""
        success = True

        # Stop the release timer if running
        if self._lock_thread and self._lock_thread.is_alive():
            self._stop_lock_thread.set()
            try:
                self._lock_thread.join(timeout=1.0)
            except Exception as e:
                logger.warning(f"Error stopping lock release timer: {e}")

        # Release the actual lock
        if self.lock:
            success = self.lock.release_immediate()
            if success:
                logger.info(f"Released hotkey processing lock for '{self.hotkey_name}'")
            else:
                logger.warning(
                    f"Failed to release hotkey lock for '{self.hotkey_name}'"
                )

        return success

    def is_locked_by_me(self) -> bool:
        """Check if the hotkey lock is currently held by this process."""
        return self.lock.is_locked_by_me() if self.lock else False

    def cleanup(self) -> None:
        """Cleanup all lock resources."""
        logger.debug("Cleaning up HotkeyLockManager")

        # Stop background timer
        if self._lock_thread and self._lock_thread.is_alive():
            self._stop_lock_thread.set()
            try:
                self._lock_thread.join(timeout=2.0)
            except Exception as e:
                logger.warning(f"Error joining lock release thread: {e}")

        # Cleanup lock
        if self.lock:
            self.lock.cleanup()

        logger.debug("HotkeyLockManager cleanup complete")

    def __del__(self) -> None:
        """Ensure cleanup on object destruction."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore cleanup errors during destruction
