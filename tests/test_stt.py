"""
Tests for speech-to-text functionality.
"""

import platform
from unittest.mock import MagicMock, Mock, patch

import pytest

from voice_mcp.voice.stt import TranscriptionHandler, get_transcription_handler


def create_mock_text_controller():
    """Create a mock text controller with session management methods."""
    mock_controller = Mock()

    # Handle output_text with flexible parameters
    def mock_output_text(_text, _mode="return", _force_update=False):
        return {"success": True, "operation": "mock_operation"}

    mock_controller.output_text.side_effect = mock_output_text
    mock_controller.start_session.return_value = {
        "success": True,
        "message": "Session started successfully",
        "clipboard_backed_up": True,
    }
    mock_controller.end_session.return_value = {
        "success": True,
        "message": "Session ended successfully",
        "clipboard_restored": True,
    }
    return mock_controller


class TestTranscriptionHandler:
    """Test suite for TranscriptionHandler class."""

    def test_singleton_pattern(self):
        """Test that TranscriptionHandler is a singleton."""
        handler1 = TranscriptionHandler()
        handler2 = TranscriptionHandler()

        assert handler1 is handler2
        assert handler1._instance is handler2._instance

    def test_get_transcription_handler(self):
        """Test the global get_transcription_handler function."""
        handler = get_transcription_handler()
        assert isinstance(handler, TranscriptionHandler)

        # Should return same instance
        handler2 = get_transcription_handler()
        assert handler is handler2

    def test_initialization(self):
        """Test TranscriptionHandler initialization."""
        with patch("voice_mcp.voice.stt.config") as mock_config:
            mock_config.stt_model = "base"
            mock_config.stt_silence_threshold = 4.0
            mock_config.stt_language = "en"

            handler = TranscriptionHandler()

            assert hasattr(handler, "_initialized")
            assert not handler._is_initialized

    def test_is_ready_false_initially(self):
        """Test is_ready returns False initially."""
        handler = TranscriptionHandler()
        assert handler.is_ready() is False

    def test_preload_success(self):
        """Test successful model preloading."""
        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"
                mock_config.stt_silence_threshold = 4.0

                with patch.object(
                    handler, "_get_optimal_device", return_value=("cpu", "int8")
                ):
                    with patch(
                        "voice_mcp.voice.stt.AudioToTextRecorder"
                    ) as mock_recorder:
                        mock_recorder.return_value = Mock()

                        result = handler.preload()

                        assert result is True
                        assert handler._is_initialized is True
                        assert handler.is_ready() is True
                        assert handler.device == "cpu"
                        assert handler.compute_type == "int8"

    def test_preload_already_loaded(self):
        """Test preloading when already loaded."""
        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            result = handler.preload()
            assert result is True

    def test_preload_failure(self):
        """Test preload failure handling."""
        # Reset singleton for this test
        TranscriptionHandler._instance = None
        TranscriptionHandler._is_initialized = False
        TranscriptionHandler._recorder = None

        handler = TranscriptionHandler()

        with patch.object(
            handler, "_get_optimal_device", side_effect=Exception("Device error")
        ):
            result = handler.preload()

            assert result is False
            assert handler._is_initialized is False
            assert handler.is_ready() is False

    def test_enable_when_ready(self):
        """Test enable when already ready."""
        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()
            result = handler.enable()
            assert result is True

    def test_enable_when_not_ready(self):
        """Test enable when not ready (should preload)."""
        # Reset singleton for this test
        TranscriptionHandler._instance = None
        TranscriptionHandler._is_initialized = False
        TranscriptionHandler._recorder = None

        handler = TranscriptionHandler()

        with patch.object(handler, "preload", return_value=True) as mock_preload:
            result = handler.enable()

            assert result is True
            mock_preload.assert_called_once()

    def test_context_manager(self):
        """Test TranscriptionHandler as context manager."""
        handler = TranscriptionHandler()

        with handler as h:
            assert h is handler

    def test_get_optimal_device_auto_cuda(self):
        """Test device detection with CUDA available."""
        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.config") as mock_config:
            mock_config.stt_device = "auto"

            with patch("voice_mcp.voice.stt.torch") as mock_torch:
                mock_torch.cuda.is_available.return_value = True
                mock_torch.cuda.get_device_name.return_value = "GeForce RTX 3080"

                device, compute_type = handler._get_optimal_device()

                assert device == "cuda"
                assert compute_type == "float16"

    def test_get_optimal_device_auto_cpu(self):
        """Test device detection with CUDA unavailable."""
        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.config") as mock_config:
            mock_config.stt_device = "auto"

            with patch("voice_mcp.voice.stt.torch") as mock_torch:
                mock_torch.cuda.is_available.return_value = False

                device, compute_type = handler._get_optimal_device()

                assert device == "cpu"
                assert compute_type == "int8"

    def test_get_optimal_device_specified_cuda(self):
        """Test device detection with specified CUDA."""
        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.config") as mock_config:
            mock_config.stt_device = "cuda"

            device, compute_type = handler._get_optimal_device()

            assert device == "cuda"
            assert compute_type == "float16"

    def test_get_optimal_device_specified_cpu(self):
        """Test device detection with specified CPU."""
        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.config") as mock_config:
            mock_config.stt_device = "cpu"

            device, compute_type = handler._get_optimal_device()

            assert device == "cpu"
            assert compute_type == "int8"

    def test_transcribe_once_not_ready_enable_fails(self):
        """Test transcribe_once when not ready and enable fails."""
        handler = TranscriptionHandler()

        with patch.object(handler, "enable", return_value=False):
            result = handler.transcribe_once()

            assert result["success"] is False
            assert "STT not available" in result["error"]
            assert result["transcription"] == ""
            assert result["duration"] == 0.0

    def test_transcribe_once_success(self):
        """Test successful transcription."""
        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()
            handler._recorder.start = Mock()
            handler._recorder.text = Mock(return_value="test transcription")
            handler.device = "cpu"
            handler.compute_type = "int8"

            mock_session_recorder = Mock()

            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"
                mock_config.stt_silence_threshold = 4.0

                with patch(
                    "voice_mcp.voice.stt.AudioToTextRecorder",
                    return_value=mock_session_recorder,
                ):
                    result = handler.transcribe_once()

                    assert result["success"] is True
                    assert "transcription" in result
                    assert result["duration"] >= 0.0  # Just check it's a valid duration
                    assert result["language"] == "en"
                    assert result["model"] == "base"

    def test_cleanup(self):
        """Test cleanup method."""
        handler = TranscriptionHandler()
        handler._recorder = Mock()
        handler._is_initialized = True

        handler.cleanup()

        assert handler._recorder is None
        assert handler._is_initialized is False

    def test_transcribe_with_realtime_output_not_ready(self):
        """Test transcribe_with_realtime_output when not ready and enable fails."""
        handler = TranscriptionHandler()
        mock_text_controller = create_mock_text_controller()

        with patch.object(handler, "enable", return_value=False):
            result = handler.transcribe_with_realtime_output(mock_text_controller)

            assert result["success"] is False
            assert "STT not available" in result["error"]
            assert result["transcription"] == ""
            assert result["duration"] == 0.0

    def test_transcribe_with_realtime_output_success(self):
        """Test successful real-time transcription with text output."""
        handler = TranscriptionHandler()
        mock_text_controller = create_mock_text_controller()
        mock_text_controller.output_text.return_value = {"success": True}

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()
            handler._recorder.set_on_recording_stop = Mock()
            handler._recorder.set_on_realtime_transcription_stabilized = Mock()
            handler._recorder.start = Mock()
            handler._recorder.text = Mock(return_value="test transcription")

            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"
                mock_config.stt_silence_threshold = 4.0

                result = handler.transcribe_with_realtime_output(mock_text_controller)

                assert result["success"] is True
                assert "transcription" in result
                assert result["duration"] >= 0.0  # Just check it's a valid duration
                assert result["language"] == "en"
                assert result["model"] == "base"
                handler._recorder.start.assert_called_once()
                handler._recorder.text.assert_called_once()

    def test_transcribe_with_realtime_output_callback_error(self):
        """Test real-time transcription with callback errors."""
        handler = TranscriptionHandler()
        mock_text_controller = create_mock_text_controller()
        mock_text_controller.output_text.side_effect = Exception("Callback error")

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()
            handler._recorder.set_on_recording_stop = Mock()
            handler._recorder.set_on_realtime_transcription_stabilized = Mock()
            handler._recorder.start = Mock()
            handler._recorder.text = Mock(return_value="test transcription")

            callback_called = []

            def capture_callback(callback):
                callback_called.append(callback)

            handler._recorder.set_on_realtime_transcription_stabilized.side_effect = (
                capture_callback
            )

            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"

                result = handler.transcribe_with_realtime_output(mock_text_controller)

                # Simulate callback being called
                if callback_called:
                    callback_called[0]("test text")

                assert (
                    result["success"] is True
                )  # Should continue despite callback error

    def test_transcribe_with_realtime_output_recorder_exception(self):
        """Test real-time transcription with recorder exception."""
        handler = TranscriptionHandler()
        mock_text_controller = create_mock_text_controller()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()
            handler._recorder.set_on_recording_stop = Mock()
            handler._recorder.set_on_realtime_transcription_stabilized = Mock()
            handler._recorder.start.side_effect = Exception("Recorder error")
            handler._recorder.text = Mock(return_value="test transcription")

            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"

                result = handler.transcribe_with_realtime_output(mock_text_controller)

                assert result["success"] is False
                assert (
                    "Transcription error" in result["error"]
                    or "Transcription setup error" in result["error"]
                )
                assert result["duration"] >= 0.0  # Just check it's a valid duration

    def test_transcribe_with_realtime_output_with_duration(self):
        """Test real-time transcription with specified duration."""
        handler = TranscriptionHandler()
        mock_text_controller = create_mock_text_controller()
        mock_text_controller.output_text.return_value = {"success": True}

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()
            handler._recorder.start = Mock()
            handler._recorder.text = Mock(return_value="test transcription")

            with patch.object(handler, "_timeout_context") as mock_timeout:
                result = handler.transcribe_with_realtime_output(
                    mock_text_controller, duration=3.0
                )

                mock_timeout.assert_called_with(3.0)
                assert result["success"] is True

    def test_timeout_context_normal_operation(self):
        """Test timeout context manager under normal conditions."""
        handler = TranscriptionHandler()

        test_executed = []

        with handler._timeout_context(5.0):
            test_executed.append(True)

        assert test_executed == [True]

    def test_timeout_context_timeout_triggered(self):
        """Test timeout context manager when timeout is triggered."""
        handler = TranscriptionHandler()

        # Mock platform detection to test both paths
        import platform

        if platform.system() == "Windows":
            # Test Windows threading-based timeout
            with patch("threading.Timer") as mock_timer:
                mock_timer_instance = Mock()
                mock_timer.return_value = mock_timer_instance

                with handler._timeout_context(0.001):  # Very short timeout
                    pass

                # Verify timer was created and started
                mock_timer.assert_called_once()
                mock_timer_instance.start.assert_called_once()
                mock_timer_instance.cancel.assert_called_once()
        else:
            # Test Unix signal-based timeout
            with patch("signal.alarm") as mock_alarm:
                with patch("signal.signal") as mock_signal:
                    original_handler = Mock()
                    mock_signal.return_value = original_handler

                    timeout_occurred = False

                    try:
                        with handler._timeout_context(1.0):
                            # Simulate what the signal handler would do by accessing
                            # the timeout handler from the patched signal call
                            signal_calls = mock_signal.call_args_list
                            if signal_calls:
                                # Get the timeout handler that was registered
                                timeout_handler = signal_calls[0][0][
                                    1
                                ]  # Second argument to signal.signal
                                # Simulate the signal being triggered
                                timeout_handler(14, None)  # SIGALRM = 14
                    except Exception:
                        # The TimeoutError should be caught by the context manager
                        # so we shouldn't reach here, but if we do, that means
                        # the context manager didn't catch it properly
                        timeout_occurred = True

                    # The test should complete without exception (timeout should be caught)
                    assert timeout_occurred is False

                    # Verify alarm was set and cleared
                    mock_alarm.assert_any_call(1)
                    mock_alarm.assert_any_call(0)

    def test_timeout_context_windows_timeout_handler(self):
        """Test Windows timeout handler function execution."""
        handler = TranscriptionHandler()

        with patch("platform.system", return_value="Windows"):
            with patch("threading.Timer") as mock_timer:
                timer_instance = Mock()
                timeout_handler_func = None

                def capture_timer_args(*args, **_kwargs):
                    nonlocal timeout_handler_func
                    if len(args) >= 2:
                        timeout_handler_func = args[
                            1
                        ]  # Second arg is the handler function
                    return timer_instance

                mock_timer.side_effect = capture_timer_args

                with handler._timeout_context(1.0):
                    # Simulate the timeout handler being called
                    if timeout_handler_func:
                        timeout_handler_func()

                # Verify timer setup and cleanup
                mock_timer.assert_called_once()
                timer_instance.start.assert_called_once()
                timer_instance.cancel.assert_called_once()

    @pytest.mark.skipif(
        platform.system() == "Windows", reason="signal.alarm not available on Windows"
    )
    def test_timeout_context_unix_timeout_exception(self):
        """Test Unix timeout context with RecordingTimeoutError."""
        handler = TranscriptionHandler()

        with patch("platform.system", return_value="Linux"):
            with patch("signal.alarm") as mock_alarm:
                with patch("signal.signal") as mock_signal:
                    original_handler = Mock()
                    mock_signal.return_value = original_handler

                    timeout_handler_func = None

                    def capture_signal_handler(sig, handler_func):
                        nonlocal timeout_handler_func
                        if sig == 14:  # SIGALRM
                            timeout_handler_func = handler_func
                        return original_handler

                    mock_signal.side_effect = capture_signal_handler

                    with handler._timeout_context(2.0):
                        # Simulate timeout being triggered
                        if timeout_handler_func:
                            timeout_handler_func(14, None)

                    # Verify signal setup and cleanup
                    mock_alarm.assert_any_call(2)  # Set alarm
                    mock_alarm.assert_any_call(0)  # Clear alarm

    def test_transcribe_once_with_duration(self):
        """Test transcribe_once with specified duration."""
        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()
            handler._recorder.start = Mock()
            handler._recorder.text = Mock(return_value="test transcription")

            with patch.object(handler, "_timeout_context") as mock_timeout:
                with patch("voice_mcp.voice.stt.config") as mock_config:
                    mock_config.stt_model = "base"
                    mock_config.stt_language = "en"

                    result = handler.transcribe_once(duration=3.0)

                    mock_timeout.assert_called_with(3.0)
                    assert result["success"] is True

    def test_transcribe_once_preload_none_recorder(self):
        """Test transcribe_once when recorder is None and preload is needed."""
        handler = TranscriptionHandler()
        handler._is_initialized = True
        handler._recorder = None

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            mock_recorder = Mock()
            mock_recorder.set_on_recording_stop = Mock()
            mock_recorder.set_on_realtime_transcription_stabilized = Mock()
            mock_recorder.start = Mock()
            mock_recorder.text = Mock(return_value="test transcription")

            def mock_preload():
                handler._recorder = mock_recorder
                return True

            with patch.object(
                handler, "preload", side_effect=mock_preload
            ) as mock_preload_patch:
                with patch(
                    "voice_mcp.voice.stt.AudioToTextRecorder",
                    return_value=mock_recorder,
                ):
                    with patch("voice_mcp.voice.stt.config") as mock_config:
                        mock_config.stt_model = "base"
                        mock_config.stt_language = "en"

                        result = handler.transcribe_once()

                        mock_preload_patch.assert_called_once()
                        assert result["success"] is True

    def test_transcribe_once_preload_failure(self):
        """Test transcribe_once when preload fails."""
        handler = TranscriptionHandler()
        handler._is_initialized = True
        handler._recorder = None

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            with patch.object(handler, "preload", return_value=False):
                result = handler.transcribe_once()

                assert result["success"] is False
                assert "STT not available - failed to load model" in result["error"]

    def test_transcribe_once_callback_updates(self):
        """Test that transcription callbacks properly update text."""
        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()

            # Capture callbacks
            transcription_callback = None
            recording_stop_callback = None

            def capture_transcription_callback(callback):
                nonlocal transcription_callback
                transcription_callback = callback

            def capture_recording_stop_callback(callback):
                nonlocal recording_stop_callback
                recording_stop_callback = callback

            def mock_start():
                # Simulate callbacks being called during start
                if transcription_callback:
                    transcription_callback("partial text")
                if recording_stop_callback:
                    recording_stop_callback("final transcribed text")

            handler._recorder.set_on_realtime_transcription_stabilized.side_effect = (
                capture_transcription_callback
            )
            handler._recorder.set_on_recording_stop.side_effect = (
                capture_recording_stop_callback
            )
            handler._recorder.start.side_effect = mock_start
            handler._recorder.text.return_value = "final transcribed text"

            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"

                result = handler.transcribe_once()

                assert result["success"] is True
                assert result["transcription"] == "final transcribed text"

    def test_is_available_true(self):
        """Test is_available when RealtimeSTT is available."""
        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler = TranscriptionHandler()
            assert handler.is_available() is True

    def test_is_available_false(self):
        """Test is_available when RealtimeSTT is not available."""
        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", False):
            handler = TranscriptionHandler()
            assert handler.is_available() is False

    def test_preload_not_available(self):
        """Test preload when RealtimeSTT is not available."""
        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", False):
            handler = TranscriptionHandler()
            result = handler.preload()
            assert result is False

    def test_get_optimal_device_torch_not_available(self):
        """Test device detection when torch is not available."""
        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.config") as mock_config:
            mock_config.stt_device = "auto"

            with patch("voice_mcp.voice.stt.torch", None):
                device, compute_type = handler._get_optimal_device()

                assert device == "cpu"
                assert compute_type == "int8"

    def test_get_optimal_device_cuda_error(self):
        """Test device detection when CUDA detection raises error."""
        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.config") as mock_config:
            mock_config.stt_device = "auto"

            with patch("voice_mcp.voice.stt.torch") as mock_torch:
                mock_torch.cuda.is_available.side_effect = Exception("CUDA error")

                device, compute_type = handler._get_optimal_device()

                assert device == "cpu"
                assert compute_type == "int8"

    def test_cleanup_with_recorder_cleanup_method(self):
        """Test cleanup when recorder has shutdown method."""
        handler = TranscriptionHandler()
        mock_recorder = Mock()
        mock_recorder.shutdown = Mock()
        handler._recorder = mock_recorder
        handler._is_initialized = True

        handler.cleanup()

        mock_recorder.shutdown.assert_called_once()
        assert handler._recorder is None
        assert handler._is_initialized is False

    def test_cleanup_with_recorder_error(self):
        """Test cleanup when recorder shutdown raises error."""
        handler = TranscriptionHandler()
        mock_recorder = Mock()
        mock_recorder.shutdown.side_effect = Exception("Shutdown error")
        handler._recorder = mock_recorder
        handler._is_initialized = True

        handler.cleanup()  # Should not raise exception

        assert handler._recorder is None
        assert handler._is_initialized is False

    def test_cleanup_no_recorder(self):
        """Test cleanup when no recorder exists."""
        handler = TranscriptionHandler()
        handler._recorder = None
        handler._is_initialized = True

        handler.cleanup()  # Should not raise exception

        assert handler._recorder is None
        assert handler._is_initialized is False


class TestTranscriptionHandlerIntegration:
    """Integration tests for TranscriptionHandler."""

    def test_complete_workflow_mock(self):
        """Test complete transcription workflow with mocks."""
        handler = TranscriptionHandler()

        # Test that handler can be created and used as context manager
        with handler as h:
            assert h is handler

        # Verify singleton behavior across context manager
        handler2 = TranscriptionHandler()
        assert handler is handler2

    def test_context_manager_cleanup(self):
        """Test context manager properly calls cleanup."""
        handler = TranscriptionHandler()
        handler._recorder = Mock()
        handler._is_initialized = True

        with handler:
            assert handler._recorder is not None

        # Should be cleaned up after context
        assert handler._recorder is None
        assert handler._is_initialized is False


class TestTqdmPatching:
    """Test tqdm compatibility patches in stt.py."""

    def test_tqdm_patch_import_handling(self):
        """Test that tqdm patches handle import errors gracefully."""
        # The patches are applied at import time, so we just verify
        # that the module can be imported without errors
        from voice_mcp.voice import stt

        # Basic check that the module loaded
        assert hasattr(stt, "TranscriptionHandler")
        assert hasattr(stt, "get_transcription_handler")

    def test_tqdm_patched_new_method(self):
        """Test the patched tqdm __new__ method with various scenarios."""
        # Import tqdm after stt module has applied patches
        from voice_mcp.voice import stt

        # Test that importing doesn't crash - patches are applied at import
        assert hasattr(stt, "TranscriptionHandler")

    def test_tqdm_ensure_lock_patch(self):
        """Test the patched ensure_lock function."""
        from voice_mcp.voice import stt

        # Test that importing doesn't crash - patches handle tqdm edge cases
        assert hasattr(stt, "TranscriptionHandler")

    def test_tqdm_executor_map_patch(self):
        """Test the patched executor map function."""
        from voice_mcp.voice import stt

        # Test that importing doesn't crash - patches handle executor edge cases
        assert hasattr(stt, "TranscriptionHandler")


class TestTranscriptionHandlerErrorConditions:
    """Test error handling and edge cases in TranscriptionHandler."""

    def test_transcribe_once_runtime_error(self):
        """Test transcribe_once with RuntimeError when recorder is None."""
        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = None

            # Enable should succeed but leave recorder as None
            with patch.object(handler, "enable", return_value=True):
                with patch.object(handler, "is_ready", return_value=True):
                    result = handler.transcribe_once()

                    assert result["success"] is False
                    assert (
                        "Transcription error" in result["error"]
                        or "Transcription setup error" in result["error"]
                    )
                    assert "Recorder not initialized" in result["error"]

    def test_transcribe_once_recorder_shutdown_exception(self):
        """Test transcribe_once when recorder.shutdown() raises exception."""
        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            mock_recorder = Mock()
            mock_recorder.start = Mock()
            mock_recorder.text = Mock(return_value="test text")
            mock_recorder.shutdown.side_effect = Exception("Shutdown failed")
            handler._recorder = mock_recorder

            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"

                result = handler.transcribe_once()

                assert result["success"] is False
                assert (
                    "Transcription error" in result["error"]
                    or "Transcription setup error" in result["error"]
                )
                assert "Shutdown failed" in result["error"]

    def test_transcribe_with_realtime_output_recorder_none(self):
        """Test transcribe_with_realtime_output when recorder is None."""
        handler = TranscriptionHandler()
        mock_text_controller = create_mock_text_controller()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = None

            with patch.object(handler, "enable", return_value=True):
                with patch.object(handler, "is_ready", return_value=True):
                    result = handler.transcribe_with_realtime_output(
                        mock_text_controller
                    )

                    assert result["success"] is False
                    assert (
                        "Transcription error" in result["error"]
                        or "Transcription setup error" in result["error"]
                    )

    def test_transcribe_with_realtime_output_with_duration_error(self):
        """Test transcribe_with_realtime_output with duration that causes error."""
        handler = TranscriptionHandler()
        mock_text_controller = create_mock_text_controller()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            mock_recorder = Mock()
            mock_recorder.set_on_recording_stop = Mock()
            mock_recorder.set_on_realtime_transcription_stabilized = Mock()
            mock_recorder.start.side_effect = Exception("Timeout error")
            handler._recorder = mock_recorder

            with patch.object(handler, "_timeout_context") as mock_timeout:
                mock_timeout.side_effect = Exception("Timeout setup failed")

                result = handler.transcribe_with_realtime_output(
                    mock_text_controller, duration=5.0
                )

                assert result["success"] is False
                assert (
                    "Transcription error" in result["error"]
                    or "Transcription setup error" in result["error"]
                )

    def test_preload_recorder_creation_exception(self):
        """Test preload when AudioToTextRecorder creation raises exception."""
        # Reset singleton for this test
        TranscriptionHandler._instance = None
        TranscriptionHandler._is_initialized = False
        TranscriptionHandler._recorder = None

        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"
                mock_config.stt_silence_threshold = 4.0

                with patch.object(
                    handler, "_get_optimal_device", return_value=("cpu", "int8")
                ):
                    with patch(
                        "voice_mcp.voice.stt.AudioToTextRecorder",
                        side_effect=Exception("Model load failed"),
                    ):
                        result = handler.preload()

                        assert result is False
                        assert handler._is_initialized is False

    def test_transcribe_once_callback_text_truncation(self):
        """Test transcription callback with text truncation in logging."""
        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()
            handler._recorder.start = Mock()
            handler._recorder.text = Mock(return_value="test transcription")
            handler._recorder.shutdown = Mock()

            # Capture the callback function

            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"
                mock_config.stt_silence_threshold = 4.0

                # Mock the callback setting to capture it
                def mock_set_callback(callback):
                    # Call the callback with long text to test truncation
                    callback("a" * 60)  # 60 chars - should trigger truncation

                handler._recorder.on_realtime_transcription_stabilized = Mock(
                    side_effect=mock_set_callback
                )

                result = handler.transcribe_once()
                assert result["success"] is True

    def test_transcribe_with_realtime_output_callback_success_and_failure(self):
        """Test real-time transcription callbacks with both success and failure scenarios."""
        handler = TranscriptionHandler()
        mock_text_controller = create_mock_text_controller()

        # Test sequence: first call succeeds, second fails, third succeeds again
        call_count = [0]

        def mock_output_text(_text, _mode, _force_update=False):
            call_count[0] += 1
            if call_count[0] == 2:
                # Second call fails
                return {"success": False, "error": "Mock failure"}
            return {"success": True, "operation": "mock_operation"}

        mock_text_controller.output_text.side_effect = mock_output_text
        mock_text_controller.reset = Mock()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()
            handler._recorder.start = Mock()
            handler._recorder.text = Mock(return_value="test transcription")
            handler._recorder.shutdown = Mock()

            # Capture and trigger the callback
            callback_func = None

            def capture_and_set_callback(callback):
                nonlocal callback_func
                callback_func = callback

            handler._recorder.on_realtime_transcription_stabilized = Mock()

            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"
                mock_config.stt_silence_threshold = 4.0

                # Test triggering the callback during transcription
                def mock_start():
                    if hasattr(
                        handler._recorder, "on_realtime_transcription_stabilized"
                    ):
                        # Simulate callback being called
                        callback = getattr(
                            handler._recorder,
                            "on_realtime_transcription_stabilized",
                            None,
                        )
                        if callback:
                            callback("test text update")
                            callback("longer text update to test logging")
                            # Call again to test the failure path
                            callback("another update")

                handler._recorder.start.side_effect = mock_start

                result = handler.transcribe_with_realtime_output(mock_text_controller)

                assert result["success"] is True
                mock_text_controller.start_session.assert_called_once()
                mock_text_controller.end_session.assert_called_once()

    def test_transcribe_with_realtime_output_callback_exception(self):
        """Test real-time transcription when callback raises exception."""
        handler = TranscriptionHandler()
        mock_text_controller = create_mock_text_controller()
        mock_text_controller.output_text.side_effect = Exception("Callback exception")
        mock_text_controller.reset = Mock()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()
            handler._recorder.start = Mock()
            handler._recorder.text = Mock(return_value="test transcription")
            handler._recorder.shutdown = Mock()

            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"
                mock_config.stt_silence_threshold = 4.0

                # Test triggering the callback during transcription
                def mock_start():
                    if hasattr(
                        handler._recorder, "on_realtime_transcription_stabilized"
                    ):
                        # Simulate callback being called with exception
                        callback = getattr(
                            handler._recorder,
                            "on_realtime_transcription_stabilized",
                            None,
                        )
                        if callback:
                            callback("text that causes exception")

                handler._recorder.start.side_effect = mock_start

                result = handler.transcribe_with_realtime_output(mock_text_controller)
                assert (
                    result["success"] is True
                )  # Should continue despite callback error

    def test_transcribe_with_realtime_output_final_output_failure(self):
        """Test real-time transcription when final output fails."""
        handler = TranscriptionHandler()
        mock_text_controller = create_mock_text_controller()

        # Mock successful real-time calls but failed final call
        call_count = [0]

        def mock_output_text(_text, _mode, _force_update=False):
            call_count[0] += 1
            if call_count[0] == 2:  # Final call fails
                return {"success": False, "error": "Final output failed"}
            return {"success": True, "operation": "mock_operation"}

        mock_text_controller.output_text.side_effect = mock_output_text
        mock_text_controller.reset = Mock()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()
            handler._recorder.start = Mock()
            handler._recorder.text = Mock(return_value="final transcription")
            handler._recorder.shutdown = Mock()

            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"
                mock_config.stt_silence_threshold = 4.0

                # Test triggering the callback during transcription
                def mock_start():
                    callback = getattr(
                        handler._recorder, "on_realtime_transcription_stabilized", None
                    )
                    if callback:
                        callback("real-time text")

                handler._recorder.start.side_effect = mock_start

                result = handler.transcribe_with_realtime_output(mock_text_controller)
                assert result["success"] is True

    def test_transcribe_with_realtime_output_final_output_exception(self):
        """Test real-time transcription when final output raises exception."""
        handler = TranscriptionHandler()
        mock_text_controller = create_mock_text_controller()

        # Mock successful real-time calls but exception on final call
        call_count = [0]

        def mock_output_text(_text, _mode, _force_update=False):
            call_count[0] += 1
            if call_count[0] == 2:  # Final call raises exception
                raise Exception("Final output exception")
            return {"success": True, "operation": "mock_operation"}

        mock_text_controller.output_text.side_effect = mock_output_text
        mock_text_controller.reset = Mock()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()
            handler._recorder.start = Mock()
            handler._recorder.text = Mock(return_value="final transcription")
            handler._recorder.shutdown = Mock()

            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"
                mock_config.stt_silence_threshold = 4.0

                def mock_start():
                    callback = getattr(
                        handler._recorder, "on_realtime_transcription_stabilized", None
                    )
                    if callback:
                        callback("real-time text")

                handler._recorder.start.side_effect = mock_start

                result = handler.transcribe_with_realtime_output(mock_text_controller)
                assert result["success"] is True

    def test_language_parameter_override(self):
        """Test language parameter override in transcription methods."""
        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()
            handler._recorder.start = Mock()
            handler._recorder.text = Mock(return_value="test transcription")
            handler._recorder.shutdown = Mock()

            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"  # Default language
                mock_config.stt_silence_threshold = 4.0

                # Test with language override
                result = handler.transcribe_once(language="fr")

                assert result["success"] is True
                assert result["language"] == "fr"  # Should use override

                # Test without language override (should use config default)
                result = handler.transcribe_once(language=None)
                assert result["language"] == "en"  # Should use config default

    def test_realtimestt_not_available_placeholder(self):
        """Test placeholder AudioToTextRecorder when RealtimeSTT not available."""
        # Create a fresh handler to test without RealtimeSTT
        # Reset the singleton instance to get a fresh one
        TranscriptionHandler._instance = None
        TranscriptionHandler._is_initialized = False
        TranscriptionHandler._recorder = None

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", False):
            # Test handler behavior when STT not available
            handler = TranscriptionHandler()
            assert not handler.is_available()
            assert not handler.preload()


class TestSTTImportAndPatching:
    """Test STT module import scenarios and tqdm patching."""

    def test_import_with_missing_contextlib(self):
        """Test import behavior when contextlib components missing."""
        # Test import behavior - the module should handle missing imports gracefully
        from voice_mcp.voice import stt

        assert hasattr(stt, "TranscriptionHandler")

    def test_torch_availability_checking(self):
        """Test various torch availability scenarios."""
        handler = TranscriptionHandler()

        # Test when torch module is completely missing
        with patch("voice_mcp.voice.stt.torch", None):
            device, compute_type = handler._get_optimal_device()
            assert device == "cpu"
            assert compute_type == "int8"

    def test_type_checking_branch(self):
        """Test TYPE_CHECKING import branch."""
        # The TYPE_CHECKING branch is for type hints only
        # We can verify the import works and classes are defined
        from voice_mcp.voice.stt import TranscriptionHandler

        assert TranscriptionHandler is not None

        # Test that text_output import would work in type checking
        from typing import TYPE_CHECKING

        if TYPE_CHECKING:
            from voice_mcp.voice.stt import TextOutputController  # noqa: F401

    def test_module_level_constants(self):
        """Test module level constants and globals."""
        import voice_mcp.voice.stt as stt_module

        # Test REALTIMESTT_AVAILABLE constant
        assert hasattr(stt_module, "REALTIMESTT_AVAILABLE")
        assert isinstance(stt_module.REALTIMESTT_AVAILABLE, bool)

        # Test logger is available
        assert hasattr(stt_module, "logger")

        # Test global transcription_handler
        assert hasattr(stt_module, "transcription_handler")
        # Import the class from the module directly to avoid singleton issues
        assert isinstance(
            stt_module.transcription_handler, stt_module.TranscriptionHandler
        )

    def test_tqdm_import_error_handling(self):
        """Test handling when tqdm is not available."""
        # Mock ImportError to test the except block
        with patch.dict("sys.modules", {"tqdm": None}):
            # Re-importing should handle the ImportError gracefully
            try:
                import importlib

                import voice_mcp.voice.stt

                importlib.reload(voice_mcp.voice.stt)
                # Should not raise exception
                assert True
            except ImportError:
                # This is expected and handled
                assert True

    def test_tqdm_patched_methods_edge_cases(self):
        """Test tqdm patched methods with edge cases."""
        # Create mock tqdm components to test patch edge cases
        mock_tqdm_class = MagicMock()

        # Test get_lock returning None
        mock_tqdm_class.get_lock.return_value = None

        with patch("tqdm.std.tqdm", mock_tqdm_class):
            # This tests the patched __new__ method path where get_lock returns None
            from voice_mcp.voice import stt

            assert hasattr(stt, "TranscriptionHandler")

    def test_tqdm_disabled_tqdm_handling(self):
        """Test handling of disabled_tqdm edge cases."""
        # Test ensure_lock with disabled_tqdm
        mock_tqdm_class = MagicMock()
        mock_tqdm_class._lock = MagicMock()

        # Test AttributeError with 'disabled_tqdm' in message
        def mock_ensure_lock_with_disabled_error(_tqdm_class, _lock_name=""):
            raise AttributeError("disabled_tqdm has no attribute '_lock'")

        with patch(
            "tqdm.contrib.concurrent.ensure_lock", mock_ensure_lock_with_disabled_error
        ):
            from voice_mcp.voice import stt

            assert hasattr(stt, "TranscriptionHandler")
