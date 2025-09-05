"""
Tests for speech-to-text functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import time

from voice_mcp.voice.stt import TranscriptionHandler


class TestTranscriptionHandler:
    """Test suite for TranscriptionHandler class."""
    
    def test_initialization_default(self):
        """Test TranscriptionHandler initialization with defaults."""
        with patch('voice_mcp.voice.stt.config') as mock_config:
            mock_config.stt_model = "base"
            mock_config.stt_silence_threshold = 4.0
            mock_config.stt_language = "en"
            
            handler = TranscriptionHandler()
            
            assert handler.model_name == "base"
            assert handler.silence_threshold == 4.0
            assert handler.language == "en"
            assert not handler._is_initialized
    
    def test_initialization_custom(self):
        """Test TranscriptionHandler initialization with custom values."""
        handler = TranscriptionHandler(
            model_name="large",
            silence_threshold=2.5,
            language="es"
        )
        
        assert handler.model_name == "large"
        assert handler.silence_threshold == 2.5
        assert handler.language == "es"
        assert not handler._is_initialized
    
    @patch('voice_mcp.voice.stt.TORCH_AVAILABLE', True)
    @patch('voice_mcp.voice.stt.torch')
    @patch('voice_mcp.voice.stt.REALTIMESTT_AVAILABLE', True)
    def test_check_dependencies_success(self, mock_torch):
        """Test dependency check when all dependencies available."""
        mock_torch.__version__ = '2.0.0'
        handler = TranscriptionHandler()
        result = handler._check_dependencies()
        
        assert result is True
    
    @patch('voice_mcp.voice.stt.REALTIMESTT_AVAILABLE', False)
    def test_check_dependencies_missing_realtimestt(self):
        """Test dependency check when RealtimeSTT is missing."""
        handler = TranscriptionHandler()
        result = handler._check_dependencies()
        
        assert result is False
    
    @patch('voice_mcp.voice.stt.TORCH_AVAILABLE', False)
    @patch('voice_mcp.voice.stt.REALTIMESTT_AVAILABLE', True)
    def test_check_dependencies_missing_torch(self):
        """Test dependency check when PyTorch is missing."""
        handler = TranscriptionHandler()
        result = handler._check_dependencies()
        
        assert result is False
    
    @patch('voice_mcp.voice.stt.TORCH_AVAILABLE', True)
    @patch('voice_mcp.voice.stt.torch')
    def test_get_optimal_device_cuda_available(self, mock_torch):
        """Test device detection when CUDA is available."""
        mock_torch.__version__ = '2.0.0'
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.get_device_name.return_value = "GeForce RTX 3080"
        
        handler = TranscriptionHandler()
        device, compute_type = handler._get_optimal_device()
        
        assert device == "cuda"
        assert compute_type == "float16"
    
    @patch('voice_mcp.voice.stt.TORCH_AVAILABLE', True)
    @patch('voice_mcp.voice.stt.torch')
    def test_get_optimal_device_cuda_unavailable(self, mock_torch):
        """Test device detection when CUDA is unavailable."""
        mock_torch.__version__ = '2.0.0'
        mock_torch.cuda.is_available.return_value = False
        
        handler = TranscriptionHandler()
        device, compute_type = handler._get_optimal_device()
        
        assert device == "cpu"
        assert compute_type == "int8"
    
    @patch('voice_mcp.voice.stt.TORCH_AVAILABLE', True)
    @patch('voice_mcp.voice.stt.torch')
    def test_get_optimal_device_cuda_error(self, mock_torch):
        """Test device detection when CUDA detection raises error."""
        mock_torch.__version__ = '2.0.0'
        mock_torch.cuda.is_available.side_effect = Exception("CUDA error")
        
        handler = TranscriptionHandler()
        device, compute_type = handler._get_optimal_device()
        
        assert device == "cpu"
        assert compute_type == "int8"
    
    @patch('voice_mcp.voice.stt.TORCH_AVAILABLE', True)
    @patch('voice_mcp.voice.stt.REALTIMESTT_AVAILABLE', True)
    @patch('voice_mcp.voice.stt.torch')
    def test_initialize_success(self, mock_torch):
        """Test successful initialization."""
        mock_torch.__version__ = '2.0.0'
        mock_torch.cuda.is_available.return_value = False
        
        handler = TranscriptionHandler()
        result = handler.initialize()
        
        assert result is True
        assert handler._is_initialized is True
        assert handler.device == "cpu"
        assert handler.compute_type == "int8"
    
    @patch('voice_mcp.voice.stt.REALTIMESTT_AVAILABLE', False)
    def test_initialize_failure(self):
        """Test initialization failure when dependencies missing."""
        handler = TranscriptionHandler()
        result = handler.initialize()
        
        assert result is False
        assert handler._is_initialized is False
    
    def test_initialize_already_initialized(self):
        """Test initialization when already initialized."""
        handler = TranscriptionHandler()
        handler._is_initialized = True
        
        result = handler.initialize()
        
        assert result is True
    
    @patch('voice_mcp.voice.stt.TORCH_AVAILABLE', True)
    @patch('voice_mcp.voice.stt.AudioToTextRecorder')
    @patch('voice_mcp.voice.stt.REALTIMESTT_AVAILABLE', True)
    def test_create_recorder_success(self, mock_recorder_class):
        """Test successful recorder creation."""
        mock_recorder = Mock()
        mock_recorder_class.return_value = mock_recorder
        
        handler = TranscriptionHandler()
        handler._is_initialized = True
        handler.device = "cpu"
        handler.compute_type = "int8"
        
        callback = Mock()
        recorder = handler.create_recorder(on_realtime_transcription_callback=callback)
        
        assert recorder is mock_recorder
        mock_recorder_class.assert_called_once()
        # Verify some key configuration parameters
        call_kwargs = mock_recorder_class.call_args.kwargs
        assert call_kwargs['model'] == handler.model_name
        assert call_kwargs['device'] == "cpu"
        assert call_kwargs['compute_type'] == "int8"
    
    @patch('voice_mcp.voice.stt.AudioToTextRecorder', None)
    def test_create_recorder_no_recorder_available(self):
        """Test recorder creation when AudioToTextRecorder not available."""
        handler = TranscriptionHandler()
        handler._is_initialized = True
        
        recorder = handler.create_recorder()
        
        assert recorder is None
    
    def test_create_recorder_not_initialized(self):
        """Test recorder creation when handler not initialized."""
        handler = TranscriptionHandler()
        # Mock _check_dependencies to return False
        with patch.object(handler, '_check_dependencies', return_value=False):
            recorder = handler.create_recorder()
        
        assert recorder is None
    
    @patch('voice_mcp.voice.stt.TORCH_AVAILABLE', True)
    @patch('voice_mcp.voice.stt.AudioToTextRecorder')
    @patch('voice_mcp.voice.stt.REALTIMESTT_AVAILABLE', True)
    def test_create_recorder_exception(self, mock_recorder_class):
        """Test recorder creation when exception occurs."""
        mock_recorder_class.side_effect = Exception("Recorder creation failed")
        
        handler = TranscriptionHandler()
        handler._is_initialized = True
        handler.device = "cpu"
        handler.compute_type = "int8"
        
        recorder = handler.create_recorder()
        
        assert recorder is None
    
    @patch('time.time')
    def test_transcribe_once_success(self, mock_time):
        """Test successful transcription."""
        # Mock time progression
        mock_time.side_effect = [100.0, 103.5]  # 3.5 second duration
        
        handler = TranscriptionHandler()
        
        # Mock successful initialization and recorder creation
        with patch.object(handler, 'initialize', return_value=True), \
             patch.object(handler, 'create_recorder') as mock_create_recorder:
            
            mock_recorder = Mock()
            mock_create_recorder.return_value = mock_recorder
            
            result = handler.transcribe_once(duration=5.0, language="en")
            
            assert result["success"] is True
            assert result["duration"] == 3.5
            assert result["language"] == "en"
            assert result["model"] == handler.model_name
            mock_recorder.listen.assert_called_once()
    
    def test_transcribe_once_initialization_failure(self):
        """Test transcription when initialization fails."""
        handler = TranscriptionHandler()
        
        with patch.object(handler, 'initialize', return_value=False):
            result = handler.transcribe_once()
            
            assert result["success"] is False
            assert "initialization failed" in result["error"]
            assert result["transcription"] == ""
            assert result["duration"] == 0.0
    
    def test_transcribe_once_recorder_creation_failure(self):
        """Test transcription when recorder creation fails."""
        handler = TranscriptionHandler()
        
        with patch.object(handler, 'initialize', return_value=True), \
             patch.object(handler, 'create_recorder', return_value=None):
            
            result = handler.transcribe_once()
            
            assert result["success"] is False
            assert "Failed to create audio recorder" in result["error"]
            assert result["transcription"] == ""
            assert result["duration"] == 0.0
    
    @patch('time.time')
    def test_transcribe_once_exception(self, mock_time):
        """Test transcription when exception occurs."""
        mock_time.side_effect = [100.0, 102.0]
        
        handler = TranscriptionHandler()
        
        with patch.object(handler, 'initialize', return_value=True), \
             patch.object(handler, 'create_recorder') as mock_create_recorder:
            
            mock_recorder = Mock()
            mock_recorder.listen.side_effect = Exception("Recording failed")
            mock_create_recorder.return_value = mock_recorder
            
            result = handler.transcribe_once()
            
            assert result["success"] is False
            assert "Recording failed" in result["error"]
            assert result["duration"] == 2.0
    
    def test_cleanup(self):
        """Test cleanup functionality."""
        handler = TranscriptionHandler()
        mock_recorder = Mock()
        mock_recorder.cleanup = Mock()
        handler._recorder = mock_recorder
        
        handler.cleanup()
        
        mock_recorder.cleanup.assert_called_once()
        assert handler._recorder is None
    
    def test_cleanup_no_recorder(self):
        """Test cleanup when no recorder exists."""
        handler = TranscriptionHandler()
        
        # Should not raise exception
        handler.cleanup()
    
    def test_cleanup_exception(self):
        """Test cleanup when exception occurs."""
        handler = TranscriptionHandler()
        mock_recorder = Mock()
        mock_recorder.cleanup.side_effect = Exception("Cleanup failed")
        handler._recorder = mock_recorder
        
        # Should not raise exception
        handler.cleanup()
        assert handler._recorder is None
    
    def test_context_manager(self):
        """Test context manager functionality."""
        handler = TranscriptionHandler()
        
        with patch.object(handler, 'initialize') as mock_init, \
             patch.object(handler, 'cleanup') as mock_cleanup:
            
            with handler as ctx_handler:
                assert ctx_handler is handler
                mock_init.assert_called_once()
            
            mock_cleanup.assert_called_once()
    
    @patch('voice_mcp.voice.stt.TORCH_AVAILABLE', True)
    def test_is_available_property_true(self):
        """Test is_available property when dependencies are available."""
        handler = TranscriptionHandler()
        
        with patch('voice_mcp.voice.stt.REALTIMESTT_AVAILABLE', True):
            assert handler.is_available is True
    
    def test_is_available_property_false(self):
        """Test is_available property when dependencies are missing."""
        handler = TranscriptionHandler()
        
        with patch('voice_mcp.voice.stt.REALTIMESTT_AVAILABLE', False):
            assert handler.is_available is False
    
    @patch('voice_mcp.voice.stt.TORCH_AVAILABLE', True)
    def test_get_status(self):
        """Test get_status method."""
        handler = TranscriptionHandler(
            model_name="large",
            silence_threshold=3.0,
            language="fr"
        )
        handler._is_initialized = True
        handler.device = "cuda"
        handler.compute_type = "float16"
        
        with patch('voice_mcp.voice.stt.REALTIMESTT_AVAILABLE', True):
            status = handler.get_status()
            
            assert status["available"] is True
            assert status["initialized"] is True
            assert status["model"] == "large"
            assert status["language"] == "fr"
            assert status["silence_threshold"] == 3.0
            assert status["device"] == "cuda"
            assert status["compute_type"] == "float16"
            assert status["realtimestt_available"] is True


class TestTranscriptionHandlerIntegration:
    """Integration tests for TranscriptionHandler (with mocked dependencies)."""
    
    @patch('voice_mcp.voice.stt.TORCH_AVAILABLE', True)
    @patch('voice_mcp.voice.stt.AudioToTextRecorder')
    @patch('voice_mcp.voice.stt.torch')
    @patch('voice_mcp.voice.stt.REALTIMESTT_AVAILABLE', True)
    @patch('time.time')
    def test_full_transcription_workflow(self, mock_time, mock_torch, mock_recorder_class):
        """Test complete transcription workflow with mocked dependencies."""
        # Setup mocks
        mock_torch.__version__ = '2.0.0'
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.get_device_name.return_value = "Test GPU"
        mock_time.side_effect = [100.0, 105.0]
        
        mock_recorder = Mock()
        mock_recorder_class.return_value = mock_recorder
        
        # Create handler and run transcription
        handler = TranscriptionHandler(model_name="base", silence_threshold=2.0)
        
        # Simulate successful transcription with callback
        transcribed_text = ""
        def mock_callback(text):
            nonlocal transcribed_text
            transcribed_text = text
        
        def mock_stop_callback(text):
            nonlocal transcribed_text
            transcribed_text = text
        
        result = handler.transcribe_once(duration=10.0, language="en")
        
        # Verify initialization happened
        assert handler.device == "cuda"
        assert handler.compute_type == "float16"
        
        # Verify recorder was created and called
        mock_recorder_class.assert_called_once()
        mock_recorder.listen.assert_called_once()
        
        # Verify result structure
        assert result["success"] is True
        assert result["duration"] == 5.0
        assert result["language"] == "en"
        assert result["model"] == "base"
    
    @patch('voice_mcp.voice.stt.TORCH_AVAILABLE', False)
    @patch('voice_mcp.voice.stt.REALTIMESTT_AVAILABLE', False)
    def test_graceful_degradation_no_dependencies(self):
        """Test graceful behavior when dependencies are missing."""
        handler = TranscriptionHandler()
        
        # Test initialization
        assert not handler.initialize()
        assert not handler.is_available
        
        # Test transcription
        result = handler.transcribe_once()
        assert result["success"] is False
        assert "initialization failed" in result["error"]
        
        # Test status
        status = handler.get_status()
        assert status["available"] is False
        assert status["realtimestt_available"] is False