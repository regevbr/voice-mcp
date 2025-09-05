"""
Pytest configuration and fixtures for Voice MCP Server tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, patch

from voice_mcp.config import ServerConfig


@pytest.fixture
def test_config() -> ServerConfig:
    """Provide a test configuration."""
    return ServerConfig(
        host="localhost",
        port=8080,
        debug=True,
        log_level="DEBUG",
        tts_engine="pyttsx3",
        tts_rate=200,
        tts_volume=0.5,
        stt_model="base",
        stt_language="en",
        stt_silence_threshold=2.0,
        enable_hotkey=False,  # Disable hotkey for tests
        hotkey_name="menu",
        typing_enabled=True,
        clipboard_enabled=True,
        typing_debounce_delay=0.1,
        sample_rate=16000,
        chunk_size=512,
    )


@pytest.fixture
def mock_audio_system():
    """Mock the audio system to avoid hardware dependencies."""
    with patch('pyaudio.PyAudio') as mock_pyaudio:
        mock_instance = Mock()
        mock_pyaudio.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_tts_engine():
    """Mock TTS engine for testing without actual speech synthesis."""
    with patch('pyttsx3.init') as mock_init:
        mock_engine = Mock()
        mock_engine.say = Mock()
        mock_engine.runAndWait = Mock()
        mock_engine.stop = Mock()
        mock_engine.getProperty.return_value = []
        mock_engine.setProperty = Mock()
        mock_init.return_value = mock_engine
        yield mock_engine


@pytest.fixture
def mock_stt_engine():
    """Mock STT engine for testing without actual speech recognition."""
    with patch('realtimestt.AudioToTextRecorder') as mock_recorder:
        mock_instance = Mock()
        mock_recorder.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_tts_manager():
    """Mock TTSManager to prevent actual TTS calls during tests."""
    with patch('voice_mcp.tools.get_tts_manager') as mock_get_manager:
        mock_manager = Mock()
        mock_manager.speak.return_value = "✅ Successfully spoke: 'test text...'"
        mock_manager.stop.return_value = None
        mock_manager.get_voice_info.return_value = {
            "status": "available",
            "engine": "MockEngine",
            "voice_count": 2,
            "voices": [
                {"id": "voice1", "name": "Test Voice 1", "language": "en"},
                {"id": "voice2", "name": "Test Voice 2", "language": "en"}
            ]
        }
        mock_get_manager.return_value = mock_manager
        yield mock_manager


@pytest.fixture
def mock_audio_manager():
    """Mock AudioManager to prevent actual audio playback during tests."""
    with patch('voice_mcp.tools.get_audio_manager') as mock_get_manager:
        mock_manager = Mock()
        mock_manager.is_available = True
        mock_manager.play_audio_file.return_value = True
        mock_manager.play_on_sound.return_value = True
        mock_manager.play_off_sound.return_value = True
        mock_manager.get_status.return_value = {
            "available": True,
            "pyaudio_available": True,
            "assets_path": "/mock/assets/path",
            "preloaded_files": ["on.wav", "off.wav"],
            "audio_system": "MockAudio"
        }
        mock_get_manager.return_value = mock_manager
        yield mock_manager


@pytest.fixture
def mock_stt_handler():
    """Mock STT handler to prevent actual speech recognition during tests."""
    with patch('voice_mcp.tools.get_stt_handler') as mock_get_handler:
        mock_handler = Mock()
        mock_handler.is_available = True
        def mock_transcribe(duration=None, language="en"):
            return {
                "success": True,
                "transcription": "Hello world",
                "duration": 3.5,
                "language": language,  # Return the language that was passed in
                "model": "base"
            }
        
        mock_handler.transcribe_once.side_effect = mock_transcribe
        mock_handler.get_status.return_value = {
            "available": True,
            "initialized": True,
            "model": "base",
            "language": "en",
            "silence_threshold": 4.0,
            "device": "cpu",
            "compute_type": "int8",
            "realtimestt_available": True
        }
        mock_get_handler.return_value = mock_handler
        yield mock_handler


@pytest.fixture
def mock_text_controller():
    """Mock text output controller to prevent actual text output during tests."""
    with patch('voice_mcp.tools.get_text_output_controller') as mock_get_controller:
        mock_controller = Mock()
        mock_controller.output_text.return_value = {
            "success": True,
            "mode": "typing",
            "text": "Hello world",
            "message": "Text typed successfully"
        }
        mock_controller.get_status.return_value = {
            "typing_available": True,
            "clipboard_available": True,
            "debounce_delay": 0.1,
            "last_text_length": 0,
            "pynput_available": True,
            "pyperclip_available": True
        }
        mock_get_controller.return_value = mock_controller
        yield mock_controller


@pytest.fixture
def mock_hotkey_manager():
    """Mock hotkey manager to prevent actual hotkey monitoring during tests."""
    with patch('voice_mcp.tools.get_hotkey_manager') as mock_get_manager:
        mock_manager = Mock()
        mock_manager.start_monitoring.return_value = {
            "success": True,
            "hotkey": "menu",
            "description": "Single key: menu",
            "message": "Hotkey monitoring started (Single key: menu)"
        }
        mock_manager.stop_monitoring.return_value = {
            "success": True,
            "message": "Hotkey monitoring stopped"
        }
        mock_manager.get_status.return_value = {
            "active": False,
            "hotkey": None,
            "is_combination": None,
            "pynput_available": True,
            "thread_alive": False
        }
        mock_manager.is_monitoring.return_value = False
        mock_get_manager.return_value = mock_manager
        yield mock_manager


@pytest.fixture
def mock_pyaudio():
    """Mock PyAudio for testing audio functionality without hardware."""
    with patch('voice_mcp.voice.audio.pyaudio') as mock_pyaudio_module:
        mock_audio_instance = Mock()
        mock_stream = Mock()
        mock_audio_instance.open.return_value = mock_stream
        mock_audio_instance.get_format_from_width.return_value = 1
        mock_pyaudio_module.PyAudio.return_value = mock_audio_instance
        yield mock_pyaudio_module


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mcp_client():
    """Create a test MCP client for integration tests."""
    # This will be implemented when we have the full MCP client setup
    pytest.skip("MCP client fixture not yet implemented")


@pytest.fixture
def sample_audio_file(tmp_path):
    """Create a sample audio file for testing."""
    import wave
    import numpy as np
    
    # Create a simple sine wave audio file
    sample_rate = 16000
    duration = 2.0
    frequency = 440  # A4 note
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
    audio_data = (audio_data * 32767).astype(np.int16)
    
    audio_file = tmp_path / "test_audio.wav"
    
    with wave.open(str(audio_file), 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    return audio_file


@pytest.fixture
def sample_text_short():
    """Short text sample for TTS testing."""
    return "Hello, world!"


@pytest.fixture  
def sample_text_long():
    """Longer text sample for TTS testing."""
    return (
        "This is a longer text sample for testing text-to-speech functionality. "
        "It includes multiple sentences and should provide a good test of the "
        "speech synthesis system's ability to handle longer content."
    )