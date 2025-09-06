"""
Tests for the loading.py module covering background loading state management.
"""

from unittest.mock import Mock, patch

import pytest

from voice_mcp.loading import (
    ComponentStatus,
    ComponentType,
    LoadingStateManager,
    get_loading_manager,
)


class TestLoadingStateManager:
    """Test cases for LoadingStateManager."""

    def setup_method(self):
        """Reset singleton before each test."""
        # Clear singleton instance for clean test isolation
        LoadingStateManager._instance = None
        import voice_mcp.loading

        voice_mcp.loading._loading_manager = None

    def test_singleton_pattern(self):
        """Test that LoadingStateManager implements singleton pattern correctly."""
        manager1 = LoadingStateManager()
        manager2 = LoadingStateManager()
        assert manager1 is manager2

    def test_init_already_initialized(self):
        """Test that __init__ returns early when already initialized."""
        manager = LoadingStateManager()
        # First initialization happens
        assert hasattr(manager, "_initialized")

        # Second call should return early
        old_status = manager._component_status.copy()
        manager.__init__()  # This should return early
        assert manager._component_status == old_status

    def test_start_background_loading_already_started(self):
        """Test that start_background_loading returns early when already started."""
        manager = LoadingStateManager()

        # Mock the executor to simulate already started
        manager._executor = Mock()

        with patch.object(manager, "_start_component_loading") as mock_start:
            manager.start_background_loading()
            # Should not call _start_component_loading since executor already exists
            mock_start.assert_not_called()

    def test_start_component_loading_not_started(self):
        """Test _start_component_loading when component is not NOT_STARTED."""
        manager = LoadingStateManager()
        manager._executor = Mock()

        # Set component to LOADING state
        manager._component_status[ComponentType.TTS] = ComponentStatus.LOADING

        # Should return early without changing status
        manager._start_component_loading(ComponentType.TTS, Mock())
        assert manager._component_status[ComponentType.TTS] == ComponentStatus.LOADING

    def test_start_component_loading_no_executor(self):
        """Test _start_component_loading when executor is None."""
        manager = LoadingStateManager()

        # Ensure component starts as NOT_STARTED
        manager._component_status[ComponentType.TTS] = ComponentStatus.NOT_STARTED
        manager._executor = None  # No executor available

        manager._start_component_loading(ComponentType.TTS, Mock())

        # Should set status to FAILED and record error
        assert manager._component_status[ComponentType.TTS] == ComponentStatus.FAILED
        assert (
            "Executor not initialized" in manager._component_errors[ComponentType.TTS]
        )

    def test_load_component_safely_success(self):
        """Test _load_component_safely with successful loading."""
        manager = LoadingStateManager()

        # Mock successful loader function
        mock_loader = Mock(return_value=True)

        manager._load_component_safely(ComponentType.TTS, mock_loader)

        assert manager._component_status[ComponentType.TTS] == ComponentStatus.READY
        mock_loader.assert_called_once()

    def test_load_component_safely_failure(self):
        """Test _load_component_safely with failed loading."""
        manager = LoadingStateManager()

        # Mock failed loader function
        mock_loader = Mock(return_value=False)

        manager._load_component_safely(ComponentType.TTS, mock_loader)

        assert manager._component_status[ComponentType.TTS] == ComponentStatus.FAILED
        assert "tts preloading failed" in manager._component_errors[ComponentType.TTS]
        mock_loader.assert_called_once()

    def test_load_component_safely_exception(self):
        """Test _load_component_safely with exception during loading."""
        manager = LoadingStateManager()

        # Mock loader function that raises exception
        mock_loader = Mock(side_effect=Exception("Test error"))

        manager._load_component_safely(ComponentType.TTS, mock_loader)

        assert manager._component_status[ComponentType.TTS] == ComponentStatus.FAILED
        assert (
            "Error during tts preloading: Test error"
            in manager._component_errors[ComponentType.TTS]
        )

    def test_load_tts_exception(self):
        """Test _load_tts with exception."""
        manager = LoadingStateManager()

        with patch.object(manager, "_load_tts") as mock_load:
            mock_load.side_effect = Exception("TTS error")
            with pytest.raises(Exception, match="TTS error"):
                manager._load_tts()

        # Test the real method with mock
        with patch(
            "voice_mcp.tools.get_tts_manager", side_effect=Exception("TTS error")
        ):
            result = manager._load_tts()
            assert result is False

    def test_load_tts_unavailable(self):
        """Test _load_tts when TTS manager is not available."""
        manager = LoadingStateManager()

        # Mock TTS manager that's not available
        mock_tts_manager = Mock()
        mock_tts_manager.is_available.return_value = False

        with patch("voice_mcp.tools.get_tts_manager", return_value=mock_tts_manager):
            result = manager._load_tts()
            assert result is False

    def test_load_stt_exception(self):
        """Test _load_stt with exception."""
        manager = LoadingStateManager()

        with patch(
            "voice_mcp.voice.stt.get_transcription_handler",
            side_effect=Exception("STT error"),
        ):
            result = manager._load_stt()
            assert result is False

    def test_load_stt_preload_failure(self):
        """Test _load_stt when preload fails."""
        manager = LoadingStateManager()

        # Mock STT handler with failed preload
        mock_stt_handler = Mock()
        mock_stt_handler.preload.return_value = False

        with patch(
            "voice_mcp.voice.stt.get_transcription_handler",
            return_value=mock_stt_handler,
        ):
            result = manager._load_stt()
            assert result is False

    def test_load_hotkey_exception(self):
        """Test _load_hotkey with exception."""
        manager = LoadingStateManager()

        with patch(
            "voice_mcp.tools.VoiceTools.start_hotkey_monitoring",
            side_effect=Exception("Hotkey error"),
        ):
            result = manager._load_hotkey()
            assert result is False

    def test_load_hotkey_failure(self):
        """Test _load_hotkey when start_hotkey_monitoring returns failure."""
        manager = LoadingStateManager()

        # Mock VoiceTools to return failure result (no ✅)
        with patch(
            "voice_mcp.tools.VoiceTools.start_hotkey_monitoring",
            return_value="❌ Failed to start",
        ):
            result = manager._load_hotkey()
            assert result is False

    def test_get_error_no_error(self):
        """Test get_error when component has no error."""
        manager = LoadingStateManager()
        # Make sure component has no error by not setting one
        manager._component_errors.clear()
        error = manager.get_error(ComponentType.TTS)
        assert error is None

    def test_get_error_with_error(self):
        """Test get_error when component has error."""
        manager = LoadingStateManager()
        manager._component_errors[ComponentType.TTS] = "Test error"
        error = manager.get_error(ComponentType.TTS)
        assert error == "Test error"

    def test_is_ready_true(self):
        """Test is_ready returns True when component is ready."""
        manager = LoadingStateManager()
        manager._component_status[ComponentType.TTS] = ComponentStatus.READY
        assert manager.is_ready(ComponentType.TTS) is True

    def test_is_ready_false(self):
        """Test is_ready returns False when component is not ready."""
        manager = LoadingStateManager()
        manager._component_status[ComponentType.TTS] = ComponentStatus.LOADING
        assert manager.is_ready(ComponentType.TTS) is False

    def test_wait_for_ready_success(self):
        """Test wait_for_ready returns True when component becomes ready quickly."""
        manager = LoadingStateManager()
        manager._component_status[ComponentType.TTS] = ComponentStatus.READY

        result = manager.wait_for_ready(ComponentType.TTS, timeout=1.0)
        assert result is True

    def test_wait_for_ready_failure(self):
        """Test wait_for_ready returns False when component fails."""
        manager = LoadingStateManager()
        manager._component_status[ComponentType.TTS] = ComponentStatus.FAILED

        result = manager.wait_for_ready(ComponentType.TTS, timeout=1.0)
        assert result is False

    def test_wait_for_ready_timeout(self):
        """Test wait_for_ready returns False on timeout."""
        manager = LoadingStateManager()
        manager._component_status[ComponentType.TTS] = ComponentStatus.LOADING

        # Use very short timeout to force timeout
        result = manager.wait_for_ready(ComponentType.TTS, timeout=0.01)
        assert result is False

    @patch("voice_mcp.loading.config")
    def test_get_overall_status(self, mock_config):
        """Test get_overall_status returns comprehensive status."""
        mock_config.tts_preload_enabled = True
        mock_config.stt_enabled = True
        mock_config.enable_hotkey = True

        manager = LoadingStateManager()
        manager._component_status[ComponentType.TTS] = ComponentStatus.READY
        manager._component_status[ComponentType.STT] = ComponentStatus.FAILED
        manager._component_errors[ComponentType.STT] = "STT error"

        status = manager.get_overall_status()

        assert status["tts"]["status"] == "ready"
        assert status["tts"]["enabled"] is True
        assert status["stt"]["status"] == "failed"
        assert status["stt"]["error"] == "STT error"
        assert status["stt"]["enabled"] is True
        assert status["hotkey"]["enabled"] is True

    def test_shutdown_no_executor(self):
        """Test shutdown when executor is None."""
        manager = LoadingStateManager()
        manager._executor = None

        # Should not raise any exception
        manager.shutdown()

    def test_shutdown_with_executor(self):
        """Test shutdown with active executor and futures."""
        manager = LoadingStateManager()

        # Mock executor and futures
        mock_executor = Mock()
        mock_future1 = Mock()
        mock_future1.done.return_value = False
        mock_future2 = Mock()
        mock_future2.done.return_value = True

        manager._executor = mock_executor
        manager._loading_futures = {
            ComponentType.TTS: mock_future1,
            ComponentType.STT: mock_future2,
        }

        manager.shutdown()

        # Should cancel pending future
        mock_future1.cancel.assert_called_once()
        mock_future2.cancel.assert_not_called()  # Already done

        # Should shutdown executor
        mock_executor.shutdown.assert_called_once_with(wait=True)

        # Should cleanup
        assert manager._executor is None

    @patch("voice_mcp.loading.config")
    def test_background_loading_with_disabled_components(self, mock_config):
        """Test background loading when some components are disabled."""
        mock_config.tts_preload_enabled = False
        mock_config.stt_enabled = False
        mock_config.enable_hotkey = True

        manager = LoadingStateManager()

        with patch.object(manager, "_start_component_loading") as mock_start:
            manager.start_background_loading()

            # Should only start hotkey loading
            mock_start.assert_called_once_with(
                ComponentType.HOTKEY, manager._load_hotkey
            )


def test_get_loading_manager_singleton():
    """Test get_loading_manager returns singleton instance."""
    # Clear any existing instance first
    import voice_mcp.loading

    voice_mcp.loading._loading_manager = None

    manager1 = get_loading_manager()
    manager2 = get_loading_manager()
    assert manager1 is manager2
    assert isinstance(manager1, LoadingStateManager)


def test_component_status_enum():
    """Test ComponentStatus enum values."""
    assert ComponentStatus.NOT_STARTED.value == "not_started"
    assert ComponentStatus.LOADING.value == "loading"
    assert ComponentStatus.READY.value == "ready"
    assert ComponentStatus.FAILED.value == "failed"


def test_component_type_enum():
    """Test ComponentType enum values."""
    assert ComponentType.TTS.value == "tts"
    assert ComponentType.STT.value == "stt"
    assert ComponentType.HOTKEY.value == "hotkey"
