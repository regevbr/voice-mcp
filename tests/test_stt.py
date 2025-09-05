"""
Tests for speech-to-text functionality.
"""

from unittest.mock import Mock, patch

from voice_mcp.voice.stt import TranscriptionHandler, get_transcription_handler


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
                    with patch(
                        "time.time", side_effect=[0.0, 5.0]
                    ):  # Mock start and end time
                        result = handler.transcribe_once()

                        assert result["success"] is True
                        assert "transcription" in result
                        assert result["duration"] == 5.0
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
        mock_text_controller = Mock()

        with patch.object(handler, "enable", return_value=False):
            result = handler.transcribe_with_realtime_output(mock_text_controller)

            assert result["success"] is False
            assert "STT not available" in result["error"]
            assert result["transcription"] == ""
            assert result["duration"] == 0.0

    def test_transcribe_with_realtime_output_success(self):
        """Test successful real-time transcription with text output."""
        handler = TranscriptionHandler()
        mock_text_controller = Mock()
        mock_text_controller.output_text.return_value = {"success": True}

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()
            handler._recorder.set_on_recording_stop = Mock()
            handler._recorder.set_on_realtime_transcription_stabilized = Mock()
            handler._recorder.listen = Mock()

            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"
                mock_config.stt_silence_threshold = 4.0

                with patch("time.time", side_effect=[0.0, 5.0]):
                    result = handler.transcribe_with_realtime_output(
                        mock_text_controller
                    )

                    assert result["success"] is True
                    assert "transcription" in result
                    assert result["duration"] == 5.0
                    assert result["language"] == "en"
                    assert result["model"] == "base"
                    handler._recorder.listen.assert_called_once()

    def test_transcribe_with_realtime_output_callback_error(self):
        """Test real-time transcription with callback errors."""
        handler = TranscriptionHandler()
        mock_text_controller = Mock()
        mock_text_controller.output_text.side_effect = Exception("Callback error")

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()
            handler._recorder.set_on_recording_stop = Mock()
            handler._recorder.set_on_realtime_transcription_stabilized = Mock()
            handler._recorder.listen = Mock()

            callback_called = []

            def capture_callback(callback):
                callback_called.append(callback)

            handler._recorder.set_on_realtime_transcription_stabilized.side_effect = (
                capture_callback
            )

            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"

                with patch("time.time", side_effect=[0.0, 5.0]):
                    result = handler.transcribe_with_realtime_output(
                        mock_text_controller
                    )

                    # Simulate callback being called
                    if callback_called:
                        callback_called[0]("test text")

                    assert (
                        result["success"] is True
                    )  # Should continue despite callback error

    def test_transcribe_with_realtime_output_recorder_exception(self):
        """Test real-time transcription with recorder exception."""
        handler = TranscriptionHandler()
        mock_text_controller = Mock()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()
            handler._recorder.set_on_recording_stop = Mock()
            handler._recorder.set_on_realtime_transcription_stabilized = Mock()
            handler._recorder.listen.side_effect = Exception("Recorder error")

            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"

                with patch("time.time", side_effect=[0.0, 5.0]):
                    result = handler.transcribe_with_realtime_output(
                        mock_text_controller
                    )

                    assert result["success"] is False
                    assert "Transcription error" in result["error"]
                    assert result["duration"] == 5.0

    def test_transcribe_with_realtime_output_with_duration(self):
        """Test real-time transcription with specified duration."""
        handler = TranscriptionHandler()
        mock_text_controller = Mock()
        mock_text_controller.output_text.return_value = {"success": True}

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()

            with patch.object(handler, "_timeout_context") as mock_timeout:
                with patch("time.time", side_effect=[0.0, 3.0]):
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

        # Mock the signal handling
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

    def test_transcribe_once_with_duration(self):
        """Test transcribe_once with specified duration."""
        handler = TranscriptionHandler()

        with patch("voice_mcp.voice.stt.REALTIMESTT_AVAILABLE", True):
            handler._is_initialized = True
            handler._recorder = Mock()

            with patch.object(handler, "_timeout_context") as mock_timeout:
                with patch("voice_mcp.voice.stt.config") as mock_config:
                    mock_config.stt_model = "base"
                    mock_config.stt_language = "en"

                    with patch("time.time", side_effect=[0.0, 3.0]):
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
            mock_recorder.listen = Mock()

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

                        with patch("time.time", side_effect=[0.0, 2.0]):
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

            def mock_listen():
                # Simulate callbacks being called during listen
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
            handler._recorder.listen.side_effect = mock_listen

            with patch("voice_mcp.voice.stt.config") as mock_config:
                mock_config.stt_model = "base"
                mock_config.stt_language = "en"

                with patch("time.time", side_effect=[0.0, 2.0]):
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
        """Test cleanup when recorder has cleanup method."""
        handler = TranscriptionHandler()
        mock_recorder = Mock()
        mock_recorder.cleanup = Mock()
        handler._recorder = mock_recorder
        handler._is_initialized = True

        handler.cleanup()

        mock_recorder.cleanup.assert_called_once()
        assert handler._recorder is None
        assert handler._is_initialized is False

    def test_cleanup_with_recorder_error(self):
        """Test cleanup when recorder cleanup raises error."""
        handler = TranscriptionHandler()
        mock_recorder = Mock()
        mock_recorder.cleanup.side_effect = Exception("Cleanup error")
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
