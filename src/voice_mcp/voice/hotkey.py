"""
Hotkey monitoring functionality for voice-mcp with configurable global hotkeys.
"""

import threading
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    pass

from .hotkey_lock import HotkeyLockManager

logger = structlog.get_logger(__name__)


# Lazy imports to avoid issues in headless environments
def _get_keyboard_modules():
    """Lazy import keyboard modules to avoid headless environment issues."""
    try:
        from pynput import keyboard
        from pynput.keyboard import Key, KeyCode

        return keyboard, Key, KeyCode
    except ImportError as e:
        logger.warning(
            "pynput not available, hotkey functionality disabled", error=str(e)
        )
        return None, None, None


class HotkeyManager:
    """Manages global hotkey monitoring for STT activation."""

    def __init__(self, on_hotkey_pressed: Callable[[], None] | None = None):
        """
        Initialize the hotkey manager.

        Args:
            on_hotkey_pressed: Callback function to call when hotkey is pressed
        """
        self.on_hotkey_pressed = on_hotkey_pressed
        self._listener: Any | None = None
        self._is_monitoring = False
        self._monitoring_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Current hotkey configuration
        self._hotkey_name = ""
        self._hotkey_keys: set[Any] = set()
        self._is_combination = False
        self._pressed_keys: set[Any] = set()

        # Thread safety
        self._lock = threading.RLock()

        # Hotkey lock manager for cross-process coordination
        self._lock_manager: HotkeyLockManager | None = None

        logger.info(
            "HotkeyManager initialized",
        )

    def _parse_hotkey(self, hotkey_name: str) -> dict[str, Any]:
        """
        Parse hotkey name into keyboard keys.

        Args:
            hotkey_name: Name like "menu", "f12", "ctrl+alt+s", etc.

        Returns:
            Dictionary with parsed hotkey information
        """

        hotkey_name = hotkey_name.lower().strip()

        try:
            # Handle combination keys
            if "+" in hotkey_name:
                parts = [part.strip() for part in hotkey_name.split("+")]
                keys = set()

                for part in parts:
                    key = self._parse_single_key(part)
                    if key is None:
                        return {"success": False, "error": f"Unknown key: {part}"}
                    keys.add(key)

                return {
                    "success": True,
                    "keys": keys,
                    "is_combination": True,
                    "description": f"Combination: {hotkey_name}",
                }

            # Handle single keys
            else:
                key = self._parse_single_key(hotkey_name)
                if key is None:
                    return {"success": False, "error": f"Unknown key: {hotkey_name}"}

                return {
                    "success": True,
                    "keys": {key},
                    "is_combination": False,
                    "description": f"Single key: {hotkey_name}",
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error parsing hotkey '{hotkey_name}': {str(e)}",
            }

    def _parse_single_key(self, key_name: str) -> Any | None:
        """
        Parse a single key name into a pynput key.

        Args:
            key_name: Single key name like "menu", "f12", "ctrl", etc.

        Returns:
            pynput Key or KeyCode, or None if unknown
        """
        keyboard, Key, KeyCode = _get_keyboard_modules()
        if not Key or not KeyCode:
            return None

        key_name = key_name.lower()

        # Special keys
        special_keys = {
            "menu": Key.menu,
            "alt": Key.alt_l,
            "alt_l": Key.alt_l,
            "alt_r": Key.alt_r,
            "ctrl": Key.ctrl_l,
            "ctrl_l": Key.ctrl_l,
            "ctrl_r": Key.ctrl_r,
            "shift": Key.shift_l,
            "shift_l": Key.shift_l,
            "shift_r": Key.shift_r,
            "cmd": Key.cmd,
            "win": Key.cmd,
            "windows": Key.cmd,
            "space": Key.space,
            "enter": Key.enter,
            "return": Key.enter,
            "esc": Key.esc,
            "escape": Key.esc,
            "tab": Key.tab,
            "backspace": Key.backspace,
            "delete": Key.delete,
            "insert": Key.insert,
            "home": Key.home,
            "end": Key.end,
            "page_up": Key.page_up,
            "page_down": Key.page_down,
            "up": Key.up,
            "down": Key.down,
            "left": Key.left,
            "right": Key.right,
            "pause": Key.pause,
            "scroll_lock": Key.scroll_lock,
            "caps_lock": Key.caps_lock,
            "num_lock": Key.num_lock,
        }

        if key_name in special_keys:
            return special_keys[key_name]

        # Function keys
        if key_name.startswith("f") and key_name[1:].isdigit():
            f_number = int(key_name[1:])
            if 1 <= f_number <= 12:
                f_keys = {
                    1: Key.f1,
                    2: Key.f2,
                    3: Key.f3,
                    4: Key.f4,
                    5: Key.f5,
                    6: Key.f6,
                    7: Key.f7,
                    8: Key.f8,
                    9: Key.f9,
                    10: Key.f10,
                    11: Key.f11,
                    12: Key.f12,
                }
                return f_keys[f_number]

        # Single character keys (a-z, 0-9)
        if len(key_name) == 1:
            if key_name.isalnum():
                return KeyCode.from_char(key_name)

        # Unknown key
        return None

    def _on_key_press(self, key: Any) -> None:
        """Handle key press events with lock coordination."""
        with self._lock:
            self._pressed_keys.add(key)

            # Check if all required keys are pressed
            if self._hotkey_keys and self._hotkey_keys.issubset(self._pressed_keys):
                logger.debug("Hotkey detected", keys=self._hotkey_keys)

                # Try to acquire exclusive processing lock immediately
                if (
                    self._lock_manager
                    and not self._lock_manager.try_acquire_for_processing()
                ):
                    logger.debug("Another process is handling this hotkey, forfeiting")
                    return  # Forfeit immediately - another server will handle it

                logger.info("Processing hotkey with exclusive lock")

                # Call the callback in a separate thread to avoid blocking
                if self.on_hotkey_pressed:
                    callback_thread = threading.Thread(
                        target=self._process_hotkey_with_lock, daemon=True
                    )
                    callback_thread.start()

    def _on_key_release(self, key: Any) -> None:
        """Handle key release events."""
        with self._lock:
            self._pressed_keys.discard(key)

    def start_monitoring(self, hotkey_name: str) -> dict[str, Any]:
        """
        Start hotkey monitoring.

        Args:
            hotkey_name: Hotkey to monitor (e.g., "menu", "f12", "ctrl+alt+s")

        Returns:
            Dictionary with operation results
        """

        with self._lock:
            if self._is_monitoring:
                return {
                    "success": False,
                    "error": f"Already monitoring hotkey: {self._hotkey_name}",
                }

            # Parse the hotkey
            parse_result = self._parse_hotkey(hotkey_name)
            if not parse_result["success"]:
                return parse_result

            try:
                keyboard, Key, KeyCode = _get_keyboard_modules()
                if not keyboard:
                    return {
                        "success": False,
                        "error": "pynput not available - hotkey functionality disabled",
                    }

                # Set up hotkey configuration
                self._hotkey_name = hotkey_name
                self._hotkey_keys = parse_result["keys"]
                self._is_combination = parse_result["is_combination"]
                self._pressed_keys.clear()

                # Initialize lock manager for this hotkey
                try:
                    from ..config import config

                    if (
                        hasattr(config, "hotkey_lock_enabled")
                        and config.hotkey_lock_enabled
                    ):
                        self._lock_manager = HotkeyLockManager(
                            hotkey_name=hotkey_name,
                            lock_directory=config.hotkey_lock_directory,
                            fallback_semaphore=config.hotkey_lock_fallback_semaphore,
                        )
                        logger.debug(
                            f"Lock manager initialized for hotkey: {hotkey_name}"
                        )
                    else:
                        logger.debug("Hotkey locking disabled in configuration")
                except Exception as e:
                    logger.warning(f"Failed to initialize lock manager: {e}")
                    self._lock_manager = None

                # Reset stop event
                self._stop_event.clear()

                # Start keyboard listener
                self._listener = keyboard.Listener(
                    on_press=self._on_key_press, on_release=self._on_key_release
                )

                # Start listener in background thread
                self._monitoring_thread = threading.Thread(
                    target=self._run_listener, daemon=True
                )
                self._monitoring_thread.start()

                # Give the listener a moment to start
                time.sleep(0.1)

                self._is_monitoring = True

                logger.info(
                    "Hotkey monitoring started",
                    hotkey=hotkey_name,
                    description=parse_result["description"],
                )

                return {
                    "success": True,
                    "hotkey": hotkey_name,
                    "description": parse_result["description"],
                    "message": f"Hotkey monitoring started ({parse_result['description']})",
                }

            except Exception as e:
                logger.error("Failed to start hotkey monitoring", error=str(e))
                return {
                    "success": False,
                    "error": f"Failed to start monitoring: {str(e)}",
                }

    def _run_listener(self) -> None:
        """Run the keyboard listener in a background thread."""
        try:
            if self._listener and self._listener is not None:
                self._listener.start()

                # Keep the listener running until stop is requested
                while not self._stop_event.is_set():
                    time.sleep(0.1)

                if self._listener and self._listener is not None:
                    self._listener.stop()

        except Exception as e:
            logger.error("Keyboard listener error", error=str(e))
        finally:
            with self._lock:
                self._is_monitoring = False
                logger.debug("Keyboard listener stopped")

    def stop_monitoring(self) -> dict[str, Any]:
        """
        Stop hotkey monitoring.

        Returns:
            Dictionary with operation results
        """
        with self._lock:
            if not self._is_monitoring:
                return {"success": True, "message": "Hotkey monitoring was not active"}

            try:
                # Signal stop
                self._stop_event.set()

                # Stop the listener first
                if self._listener and self._listener is not None:
                    try:
                        self._listener.stop()
                    except Exception as e:
                        logger.warning("Error stopping keyboard listener", error=str(e))
                    self._listener = None

                # Wait for monitoring thread to finish with extended timeout
                if self._monitoring_thread and self._monitoring_thread.is_alive():
                    self._monitoring_thread.join(timeout=5.0)
                    if self._monitoring_thread.is_alive():
                        logger.warning(
                            "Monitoring thread did not stop gracefully, forcing cleanup"
                        )
                        # For non-daemon threads that won't stop, we can't force kill them
                        # but we can mark them as such and continue cleanup

                self._is_monitoring = False
                self._monitoring_thread = None

                # Cleanup lock manager
                if self._lock_manager:
                    try:
                        self._lock_manager.cleanup()
                        logger.debug("Lock manager cleaned up")
                    except Exception as e:
                        logger.warning(f"Error cleaning up lock manager: {e}")
                    self._lock_manager = None

                # Clear state
                previous_hotkey = self._hotkey_name
                self._hotkey_name = ""
                self._hotkey_keys.clear()
                self._pressed_keys.clear()

                logger.info(
                    "Hotkey monitoring stopped", previous_hotkey=previous_hotkey
                )

                return {
                    "success": True,
                    "message": f"Hotkey monitoring stopped (was: {previous_hotkey})",
                }

            except Exception as e:
                logger.error("Failed to stop hotkey monitoring", error=str(e))
                # Cleanup lock manager even on error
                if self._lock_manager:
                    try:
                        self._lock_manager.cleanup()
                    except Exception:
                        pass
                    self._lock_manager = None

                # Even if there's an error, mark as stopped to prevent hanging
                self._is_monitoring = False
                self._monitoring_thread = None
                return {
                    "success": False,
                    "error": f"Failed to stop monitoring: {str(e)}",
                }

    def get_status(self) -> dict[str, Any]:
        """
        Get current hotkey monitoring status.

        Returns:
            Dictionary with current status
        """
        with self._lock:
            return {
                "active": self._is_monitoring,
                "hotkey": self._hotkey_name if self._is_monitoring else None,
                "is_combination": self._is_combination if self._is_monitoring else None,
                "thread_alive": (
                    self._monitoring_thread.is_alive()
                    if self._monitoring_thread
                    else False
                ),
                "lock_enabled": self._lock_manager is not None,
                "lock_held": (
                    self._lock_manager.is_locked_by_me()
                    if self._lock_manager
                    else False
                ),
            }

    def is_monitoring(self) -> bool:
        """Check if currently monitoring hotkeys."""
        with self._lock:
            return self._is_monitoring

    def _process_hotkey_with_lock(self) -> None:
        """Process hotkey while holding exclusive lock for the entire duration."""
        try:
            logger.debug("Starting hotkey processing with lock held")

            # Process the hotkey callback
            if self.on_hotkey_pressed:
                self.on_hotkey_pressed()  # This will take several seconds for STT

            logger.debug("Hotkey processing completed successfully")

        except Exception as e:
            logger.error(f"Error during hotkey processing: {e}", exc_info=True)
        finally:
            # Lock will be automatically released by the timer in HotkeyLockManager
            logger.debug("Hotkey processing finished, lock release scheduled")

    def __del__(self) -> None:
        """Cleanup resources when object is destroyed."""
        try:
            self.stop_monitoring()
        except Exception:
            pass  # Ignore cleanup errors
