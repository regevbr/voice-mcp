"""
Tests for TTS (Text-to-Speech) functionality using Coqui TTS.
"""

import sys
from unittest.mock import Mock, patch

# Mock the TTS module before importing our code
sys.modules["TTS"] = Mock()
sys.modules["TTS.api"] = Mock()

from voice_mcp.voice.tts import CoquiTTSEngine, TTSManager, Voice


class TestVoice:
    """Test Voice dataclass."""

    def test_voice_creation(self):
        """Test creating a Voice object."""
        voice = Voice(
            id="tts_models/en/ljspeech/tacotron2-DDC",
            name="LJSpeech Tacotron2",
            language="en",
            description="English female voice",
        )

        assert voice.id == "tts_models/en/ljspeech/tacotron2-DDC"
        assert voice.name == "LJSpeech Tacotron2"
        assert voice.language == "en"
        assert voice.description == "English female voice"


class TestCoquiTTSEngine:
    """Test Coqui TTS engine."""

    @patch("voice_mcp.voice.tts.AudioManager")
    def test_engine_initialization_success(self, mock_audio_manager_class):
        """Test successful engine initialization."""
        mock_audio_manager = Mock()
        mock_audio_manager_class.return_value = mock_audio_manager

        # Mock the TTS constructor
        with patch("TTS.api.TTS") as mock_tts_class:
            mock_tts_instance = Mock()
            mock_tts_class.return_value = mock_tts_instance

            engine = CoquiTTSEngine("test_model")

            assert engine.is_available() is True
            mock_tts_class.assert_called_once_with(
                "test_model", progress_bar=False, gpu=False
            )

    @patch("TTS.api.TTS")
    @patch("voice_mcp.voice.tts.AudioManager")
    def test_engine_initialization_failure(
        self, mock_audio_manager_class, mock_tts_class
    ):
        """Test failed engine initialization."""
        mock_audio_manager = Mock()
        mock_audio_manager_class.return_value = mock_audio_manager

        mock_tts_class.side_effect = Exception("TTS not available")

        engine = CoquiTTSEngine("test_model")

        assert engine.is_available() is False

    @patch("TTS.api.TTS")
    @patch("voice_mcp.voice.tts.AudioManager")
    def test_speak_success(self, mock_audio_manager_class, mock_tts_class):
        """Test successful speech synthesis."""
        # Setup mocks
        mock_tts_instance = Mock()
        mock_tts_instance.tts.return_value = b"fake_audio_data"
        mock_tts_class.return_value = mock_tts_instance

        mock_audio_manager = Mock()
        mock_audio_manager.is_available = True
        mock_audio_manager_class.return_value = mock_audio_manager

        # Mock audio playback method
        with patch.object(
            CoquiTTSEngine, "_play_audio_data_directly", return_value=True
        ) as mock_play:
            engine = CoquiTTSEngine("test_model")
            result = engine.speak("Hello, world!")

            assert result is True
            mock_tts_instance.tts.assert_called_once_with(text="Hello, world!")
            mock_play.assert_called_once_with(b"fake_audio_data")

    @patch("TTS.api.TTS")
    def test_speak_engine_unavailable(self, mock_tts_class):
        """Test speak when engine is unavailable."""
        mock_tts_class.side_effect = Exception("TTS not available")

        engine = CoquiTTSEngine("test_model")
        result = engine.speak("Hello, world!")

        assert result is False

    @patch("TTS.api.TTS")
    @patch("voice_mcp.voice.tts.AudioManager")
    def test_speak_synthesis_error(self, mock_audio_manager_class, mock_tts_class):
        """Test speak when synthesis fails."""
        mock_tts_instance = Mock()
        mock_tts_instance.tts.side_effect = Exception("Synthesis failed")
        mock_tts_class.return_value = mock_tts_instance

        mock_audio_manager = Mock()
        mock_audio_manager_class.return_value = mock_audio_manager

        engine = CoquiTTSEngine("test_model")
        result = engine.speak("Hello, world!")

        assert result is False

    @patch("TTS.api.TTS")
    def test_get_voices(self, mock_tts_class):
        """Test getting available voices."""
        mock_tts_instance = Mock()
        mock_tts_class.return_value = mock_tts_instance

        engine = CoquiTTSEngine("test_model")
        voices = engine.get_voices()

        # Should return the predefined list of voices
        assert len(voices) == 3
        assert voices[0].id == "tts_models/en/ljspeech/tacotron2-DDC"
        assert voices[0].name == "LJSpeech Tacotron2"
        assert voices[0].language == "en"

    @patch("TTS.api.TTS")
    def test_get_voices_engine_unavailable(self, mock_tts_class):
        """Test getting voices when engine is unavailable."""
        mock_tts_class.side_effect = Exception("TTS not available")

        engine = CoquiTTSEngine("test_model")
        voices = engine.get_voices()

        assert voices == []

    @patch("TTS.api.TTS")
    @patch("voice_mcp.voice.tts.AudioManager")
    def test_stop(self, mock_audio_manager_class, mock_tts_class):
        """Test stopping playback."""
        mock_tts_instance = Mock()
        mock_tts_class.return_value = mock_tts_instance

        mock_audio_manager = Mock()
        mock_audio_manager_class.return_value = mock_audio_manager

        engine = CoquiTTSEngine("test_model")
        engine.stop()

        # Should just log a warning since stop is not implemented
        # No assertions needed as it just logs


class TestTTSManager:
    """Test TTS manager."""

    @patch("voice_mcp.voice.tts.CoquiTTSEngine")
    def test_manager_initialization(self, mock_engine_class):
        """Test TTS manager initialization."""
        mock_engine_instance = Mock()
        mock_engine_class.return_value = mock_engine_instance

        manager = TTSManager("test_model")

        mock_engine_class.assert_called_once_with("test_model")
        assert manager._engine == mock_engine_instance

    @patch("voice_mcp.voice.tts.CoquiTTSEngine")
    def test_speak_success(self, mock_engine_class):
        """Test successful speech through manager."""
        mock_engine_instance = Mock()
        mock_engine_instance.is_available.return_value = True
        mock_engine_instance.speak.return_value = True
        mock_engine_class.return_value = mock_engine_instance

        manager = TTSManager("test_model")
        result = manager.speak("Hello, world!")

        assert "Successfully spoke" in result
        mock_engine_instance.speak.assert_called_once_with(
            "Hello, world!", None, None, None
        )

    @patch("voice_mcp.voice.tts.CoquiTTSEngine")
    def test_speak_engine_unavailable(self, mock_engine_class):
        """Test speak when engine is unavailable."""
        mock_engine_instance = Mock()
        mock_engine_instance.is_available.return_value = False
        mock_engine_class.return_value = mock_engine_instance

        manager = TTSManager("test_model")
        result = manager.speak("Hello, world!")

        assert "Coqui TTS engine not available" in result

    @patch("voice_mcp.voice.tts.CoquiTTSEngine")
    def test_speak_empty_text(self, mock_engine_class):
        """Test speak with empty text."""
        mock_engine_instance = Mock()
        mock_engine_instance.is_available.return_value = True
        mock_engine_class.return_value = mock_engine_instance

        manager = TTSManager("test_model")
        result = manager.speak("")

        assert "No text provided" in result

    @patch("voice_mcp.voice.tts.CoquiTTSEngine")
    def test_speak_long_text(self, mock_engine_class):
        """Test speak with very long text."""
        mock_engine_instance = Mock()
        mock_engine_instance.is_available.return_value = True
        mock_engine_instance.speak.return_value = True
        mock_engine_class.return_value = mock_engine_instance

        manager = TTSManager("test_model")
        long_text = "This is a very long text. " * 100  # > 1000 chars
        result = manager.speak(long_text)

        # Should truncate and still succeed
        assert "Successfully spoke" in result
        # Verify the engine was called with truncated text
        called_text = mock_engine_instance.speak.call_args[0][0]
        assert len(called_text) <= 1000 + len("... (truncated)")

    @patch("voice_mcp.voice.tts.CoquiTTSEngine")
    def test_get_voices(self, mock_engine_class):
        """Test getting voices through manager."""
        mock_engine_instance = Mock()
        test_voices = [
            Voice("model1", "Voice 1", "en", "Test voice 1"),
            Voice("model2", "Voice 2", "es", "Test voice 2"),
        ]
        mock_engine_instance.get_voices.return_value = test_voices
        mock_engine_class.return_value = mock_engine_instance

        manager = TTSManager("test_model")
        voices = manager.get_voices()

        assert len(voices) == 2
        assert voices[0].id == "model1"
        assert voices[1].id == "model2"

    @patch("voice_mcp.voice.tts.CoquiTTSEngine")
    def test_get_voice_info_available(self, mock_engine_class):
        """Test getting voice info when engine is available."""
        mock_engine_instance = Mock()
        mock_engine_instance.is_available.return_value = True
        mock_engine_instance._model_name = "test_model"
        test_voices = [Voice("model1", "Voice 1", "en", "Test voice")]
        mock_engine_instance.get_voices.return_value = test_voices
        mock_engine_class.return_value = mock_engine_instance

        manager = TTSManager("test_model")
        info = manager.get_voice_info()

        assert info["status"] == "available"
        assert info["engine"] == "CoquiTTS"
        assert info["model"] == "test_model"
        assert info["voice_count"] == 1

    @patch("voice_mcp.voice.tts.CoquiTTSEngine")
    def test_get_voice_info_unavailable(self, mock_engine_class):
        """Test getting voice info when engine is unavailable."""
        mock_engine_instance = Mock()
        mock_engine_instance.is_available.return_value = False
        mock_engine_class.return_value = mock_engine_instance

        manager = TTSManager("test_model")
        info = manager.get_voice_info()

        assert info["status"] == "no_engine"
        assert info["voices"] == []

    @patch("voice_mcp.voice.tts.CoquiTTSEngine")
    def test_stop(self, mock_engine_class):
        """Test stopping through manager."""
        mock_engine_instance = Mock()
        mock_engine_class.return_value = mock_engine_instance

        manager = TTSManager("test_model")
        manager.stop()

        mock_engine_instance.stop.assert_called_once()

    @patch("voice_mcp.voice.tts.CoquiTTSEngine")
    def test_is_available(self, mock_engine_class):
        """Test availability check through manager."""
        mock_engine_instance = Mock()
        mock_engine_instance.is_available.return_value = True
        mock_engine_class.return_value = mock_engine_instance

        manager = TTSManager("test_model")
        assert manager.is_available() is True

        mock_engine_instance.is_available.return_value = False
        assert manager.is_available() is False

