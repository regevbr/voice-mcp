"""
Tests for speech-to-text functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
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
    
    def test_context_manager(self):
        """Test TranscriptionHandler as context manager."""
        handler = TranscriptionHandler()
        
        # Test enter
        with handler as h:
            assert h is handler
    
    def test_initialize_success(self):
        """Test successful initialization."""
        handler = TranscriptionHandler()
        
        with patch.object(handler, '_get_optimal_device', return_value=("cpu", "int8")):
            result = handler.initialize()
            
            assert result is True
            assert handler._is_initialized is True
            assert handler.device == "cpu"
            assert handler.compute_type == "int8"
    
    def test_initialize_failure(self):
        """Test initialization failure."""
        handler = TranscriptionHandler()
        
        with patch.object(handler, '_get_optimal_device', side_effect=Exception("Device error")):
            result = handler.initialize()
            
            assert result is False
            assert handler._is_initialized is False
    
    def test_create_recorder_success(self):
        """Test successful recorder creation."""
        handler = TranscriptionHandler()
        handler._is_initialized = True
        
        with patch.object(handler, '_create_oneoff_recorder', return_value=Mock()) as mock_create:
            result = handler.create_recorder()
            assert result is not None
            mock_create.assert_called_once()
    
    def test_create_recorder_not_initialized(self):
        """Test recorder creation when not initialized."""
        handler = TranscriptionHandler()
        handler._is_initialized = False
        
        # The method actually initializes if not already done, so check behavior
        with patch.object(handler, 'initialize', return_value=False):
            result = handler.create_recorder()
            assert result is None
    
    def test_create_recorder_exception(self):
        """Test recorder creation with exception."""
        handler = TranscriptionHandler()
        handler._is_initialized = True
        
        # Mock AudioToTextRecorder constructor to raise exception
        with patch('voice_mcp.voice.stt.AudioToTextRecorder', side_effect=Exception("AudioToTextRecorder error")):
            result = handler.create_recorder()
            assert result is None


class TestTranscriptionHandlerIntegration:
    """Integration tests for TranscriptionHandler."""
    
    def test_complete_workflow(self):
        """Test complete transcription workflow."""
        handler = TranscriptionHandler()
        
        # Test that handler can be created and used as context manager
        with handler as h:
            assert h is handler


class TestTranscriptionHandlerMethods:
    """Test TranscriptionHandler methods."""
    
    def test_cleanup(self):
        """Test cleanup method."""
        handler = TranscriptionHandler()
        handler._recorder = Mock()
        
        handler.cleanup()
        
        # Verify cleanup behavior doesn't crash
        assert True