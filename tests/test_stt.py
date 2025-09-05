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
