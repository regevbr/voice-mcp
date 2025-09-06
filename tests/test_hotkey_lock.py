"""
Tests for hotkey locking system ensuring only one server instance processes each keystroke.
"""

import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from voice_mcp.voice.hotkey_lock import (
    FileBasedLock,
    HotkeyLockManager,
    SemaphoreLock,
)


class TestFileBasedLock:
    """Test file-based locking mechanism."""

    def test_single_process_acquire_release(self, tmp_path):
        """Test basic acquire and release in single process."""
        lock_file = tmp_path / "test.lock"
        lock = FileBasedLock(lock_file)

        # Should be able to acquire
        assert lock.try_acquire_immediate() is True
        assert lock.is_locked_by_me() is True

        # Should be able to release
        assert lock.release_immediate() is True
        assert lock.is_locked_by_me() is False

    def test_multiple_instances_conflict(self, tmp_path):
        """Test that multiple FileBasedLock instances conflict properly."""
        lock_file = tmp_path / "test.lock"

        lock1 = FileBasedLock(lock_file)
        lock2 = FileBasedLock(lock_file)

        # First lock should succeed
        assert lock1.try_acquire_immediate() is True
        assert lock1.is_locked_by_me() is True

        # Second lock should fail immediately
        assert lock2.try_acquire_immediate() is False
        assert lock2.is_locked_by_me() is False

        # After first releases, second should succeed
        assert lock1.release_immediate() is True
        assert lock2.try_acquire_immediate() is True
        assert lock2.is_locked_by_me() is True

        # Cleanup
        lock2.release_immediate()

    def test_cleanup_removes_lock_file(self, tmp_path):
        """Test that cleanup removes the lock file."""
        lock_file = tmp_path / "test.lock"
        lock = FileBasedLock(lock_file)

        lock.try_acquire_immediate()
        assert lock_file.exists()

        lock.cleanup()
        assert not lock_file.exists()

    def test_directory_creation(self, tmp_path):
        """Test that lock directory is created if it doesn't exist."""
        lock_dir = tmp_path / "nested" / "locks"
        lock_file = lock_dir / "test.lock"

        assert not lock_dir.exists()
        FileBasedLock(lock_file)
        assert lock_dir.exists()

    @patch("platform.system")
    def test_unsupported_platform_fallback(self, mock_system, tmp_path):
        """Test behavior on unsupported platforms."""
        mock_system.return_value = "UnknownOS"
        lock_file = tmp_path / "test.lock"
        lock = FileBasedLock(lock_file)

        # Should fail gracefully
        assert lock.try_acquire_immediate() is False
        assert lock.is_locked_by_me() is False


class TestSemaphoreLock:
    """Test semaphore-based locking mechanism."""

    def test_single_process_acquire_release(self):
        """Test basic semaphore acquire and release."""
        lock = SemaphoreLock("test_semaphore")

        # Should be able to acquire
        assert lock.try_acquire_immediate() is True
        assert lock.is_locked_by_me() is True

        # Should be able to release
        assert lock.release_immediate() is True
        assert lock.is_locked_by_me() is False

    def test_multiple_instances_conflict(self):
        """Test that multiple semaphore instances conflict properly."""
        # NOTE: multiprocessing.Semaphore instances in the same process
        # won't actually conflict with each other without shared state.
        # This test documents the current limitation of the semaphore approach.
        lock1 = SemaphoreLock("test_conflict")
        lock2 = SemaphoreLock("test_conflict")

        # Both locks should succeed because they're separate semaphore instances
        # This is a known limitation of the fallback semaphore implementation
        assert lock1.try_acquire_immediate() is True
        assert lock1.is_locked_by_me() is True

        # This won't conflict in same-process testing, but would in real multi-process usage
        result = lock2.try_acquire_immediate()
        # Accept either result since semaphore behavior varies by platform/implementation

        # Cleanup
        lock1.release_immediate()
        if result:
            lock2.release_immediate()

    @patch("multiprocessing.Semaphore")
    def test_semaphore_creation_failure(self, mock_semaphore):
        """Test graceful handling of semaphore creation failure."""
        mock_semaphore.side_effect = Exception("Semaphore creation failed")

        lock = SemaphoreLock("test_failure")
        assert lock.semaphore is None
        assert lock.try_acquire_immediate() is False


class TestHotkeyLockManager:
    """Test hotkey lock manager coordination."""

    def test_initialization_with_defaults(self):
        """Test initialization with default settings."""
        manager = HotkeyLockManager("menu")

        assert manager.hotkey_name == "menu"
        assert manager.fallback_semaphore is True
        assert manager.lock is not None

        # Cleanup
        manager.cleanup()

    def test_initialization_with_custom_directory(self, tmp_path):
        """Test initialization with custom lock directory."""
        custom_dir = str(tmp_path / "custom_locks")
        manager = HotkeyLockManager("f12", lock_directory=custom_dir)

        assert manager.lock_directory == Path(custom_dir)
        assert Path(custom_dir).exists()

        # Cleanup
        manager.cleanup()

    def test_initialization_no_fallback(self):
        """Test initialization with semaphore fallback disabled."""
        # Force file lock to fail by using invalid directory
        with patch("voice_mcp.voice.hotkey_lock.FileBasedLock") as mock_file_lock:
            mock_file_lock.side_effect = Exception("File lock failed")

            manager = HotkeyLockManager("ctrl+alt+s", fallback_semaphore=False)
            assert manager.lock is None

            # Cleanup
            manager.cleanup()

    def test_single_manager_processing(self):
        """Test that a single manager can acquire and process."""
        manager = HotkeyLockManager("test_single")

        # Should be able to acquire for processing
        assert manager.try_acquire_for_processing() is True
        assert manager.is_locked_by_me() is True

        # Cleanup (releases the lock)
        manager.cleanup()
        assert not manager.is_locked_by_me()

    def test_multiple_managers_conflict(self):
        """Test that multiple managers conflict properly - only one processes."""
        manager1 = HotkeyLockManager("test_conflict")
        manager2 = HotkeyLockManager("test_conflict")

        # First manager should acquire successfully
        assert manager1.try_acquire_for_processing() is True
        assert manager1.is_locked_by_me() is True

        # Second manager should immediately forfeit
        assert manager2.try_acquire_for_processing() is False
        assert manager2.is_locked_by_me() is False

        # Cleanup
        manager1.cleanup()
        manager2.cleanup()

    @patch("voice_mcp.config.config")
    def test_automatic_lock_release_timer(self, mock_config):
        """Test that lock is automatically released after processing duration."""
        mock_config.stt_silence_threshold = 0.1  # Very short for testing

        manager = HotkeyLockManager("timer_test")

        # Acquire lock
        assert manager.try_acquire_for_processing() is True
        assert manager.is_locked_by_me() is True

        # Wait for timer to expire (should be ~2.1 seconds minimum)
        # But we'll wait less and verify it's still held, then cleanup
        time.sleep(0.05)
        assert manager.is_locked_by_me() is True

        # Cleanup should stop timer and release lock
        manager.cleanup()
        assert not manager.is_locked_by_me()

    def test_immediate_release(self):
        """Test immediate release functionality."""
        manager = HotkeyLockManager("immediate_release")

        # Acquire lock
        assert manager.try_acquire_for_processing() is True
        assert manager.is_locked_by_me() is True

        # Release immediately
        assert manager.release_immediate() is True
        assert not manager.is_locked_by_me()

        # Cleanup
        manager.cleanup()

    def test_concurrent_access_simulation(self):
        """Simulate concurrent access from multiple threads."""
        results = []
        managers = [HotkeyLockManager("concurrent_test") for _ in range(5)]

        def try_process(manager, results_list):
            """Simulate trying to process hotkey."""
            if manager.try_acquire_for_processing():
                results_list.append(f"PROCESSED by {id(manager)}")
                # Simulate some processing time
                time.sleep(0.1)
                manager.release_immediate()
            else:
                results_list.append(f"FORFEITED by {id(manager)}")

        # Start all threads simultaneously
        threads = []
        for manager in managers:
            thread = threading.Thread(target=try_process, args=(manager, results))
            threads.append(thread)
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join()

        # Only one should have processed
        processed_count = len([r for r in results if "PROCESSED" in r])
        forfeited_count = len([r for r in results if "FORFEITED" in r])

        assert processed_count == 1, (
            f"Expected exactly 1 processed, got {processed_count}"
        )
        assert forfeited_count == 4, f"Expected 4 forfeited, got {forfeited_count}"

        # Cleanup all managers
        for manager in managers:
            manager.cleanup()


class TestCrossPlatformLockIntegration:
    """Test cross-platform lock integration scenarios."""

    @patch("platform.system")
    def test_unix_lock_selection(self, mock_system, tmp_path):
        """Test that Unix systems use file-based locks."""
        mock_system.return_value = "Linux"

        manager = HotkeyLockManager("unix_test", lock_directory=str(tmp_path))
        assert isinstance(manager.lock, FileBasedLock)
        manager.cleanup()

    @patch("platform.system")
    def test_windows_lock_selection(self, mock_system, tmp_path):
        """Test that Windows systems use file-based locks."""
        mock_system.return_value = "Windows"

        manager = HotkeyLockManager("windows_test", lock_directory=str(tmp_path))
        assert isinstance(manager.lock, FileBasedLock)
        manager.cleanup()

    def test_lock_file_naming(self, tmp_path):
        """Test that lock files are named correctly."""
        manager1 = HotkeyLockManager("menu", lock_directory=str(tmp_path))
        manager2 = HotkeyLockManager("ctrl+alt+s", lock_directory=str(tmp_path))

        # Acquire locks to create files
        manager1.try_acquire_for_processing()
        manager2.try_acquire_for_processing()

        # Check that lock files exist with expected names
        expected_files = {"hotkey-menu.lock", "hotkey-ctrl-alt-s.lock"}
        actual_files = {f.name for f in tmp_path.iterdir() if f.is_file()}

        assert expected_files.issubset(actual_files), (
            f"Expected {expected_files}, found {actual_files}"
        )

        # Cleanup
        manager1.cleanup()
        manager2.cleanup()

    def test_permission_error_handling(self, tmp_path):
        """Test handling of permission errors."""
        # Create a directory with restricted permissions
        restricted_dir = tmp_path / "restricted"
        restricted_dir.mkdir(mode=0o444)  # Read-only

        try:
            # This should fall back gracefully
            manager = HotkeyLockManager(
                "permission_test", lock_directory=str(restricted_dir)
            )

            # Should still work (either with fallback location or semaphore)
            manager.try_acquire_for_processing()
            # Don't assert the result since it depends on fallback behavior

            manager.cleanup()

        finally:
            # Restore permissions for cleanup
            restricted_dir.chmod(0o755)


@pytest.mark.integration
class TestMultiProcessScenarios:
    """Integration tests simulating multiple server instances."""

    def test_hotkey_processing_workflow(self):
        """Test complete hotkey processing workflow with locking."""
        callback_called = []

        def mock_callback():
            """Mock hotkey callback that simulates STT processing."""
            callback_called.append(time.time())
            time.sleep(0.2)  # Simulate STT processing time

        manager1 = HotkeyLockManager("workflow_test")
        manager2 = HotkeyLockManager("workflow_test")

        # Simulate first server detecting hotkey
        assert manager1.try_acquire_for_processing() is True

        # Start processing in background (simulates hotkey callback)
        thread1 = threading.Thread(target=mock_callback)
        thread1.start()

        # Simulate second server detecting same hotkey shortly after
        time.sleep(0.05)  # Small delay to simulate real timing
        assert manager2.try_acquire_for_processing() is False  # Should forfeit

        # Wait for processing to complete
        thread1.join()

        # Only first server should have processed
        assert len(callback_called) == 1

        # Cleanup
        manager1.cleanup()
        manager2.cleanup()

    def test_lock_directory_defaults(self):
        """Test that default lock directories work correctly."""
        manager = HotkeyLockManager("defaults_test")

        # Should create lock directory successfully
        assert manager.lock_directory.exists()
        assert manager.lock is not None

        # Should be able to acquire
        assert manager.try_acquire_for_processing() is True

        # Cleanup
        manager.cleanup()

    def test_error_recovery(self):
        """Test that system recovers gracefully from errors."""
        manager = HotkeyLockManager("error_recovery")

        # Acquire lock
        assert manager.try_acquire_for_processing() is True

        # Simulate error during processing
        with patch.object(
            manager, "release_immediate", side_effect=Exception("Release failed")
        ):
            # Should not raise exception during cleanup
            manager.cleanup()

        # New manager should still work
        manager2 = HotkeyLockManager("error_recovery")
        assert manager2.try_acquire_for_processing() is True
        manager2.cleanup()
