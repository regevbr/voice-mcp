"""
Comprehensive tests for the AudioManager class.

These tests use proper mocking to prevent actual audio output during testing
while ensuring all functionality works correctly.
"""

import threading
import wave
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np

from voice_mcp.voice.audio import AudioManager


class TestAudioManager:
    """Test suite for AudioManager functionality."""

    def test_init_without_pyaudio(self):
        """Test AudioManager initialization when PyAudio is not available."""
        with (
            patch("voice_mcp.voice.audio.PYAUDIO_AVAILABLE", False),
            patch(
                "voice_mcp.voice.audio.pyaudio.PyAudio",
                side_effect=Exception("No PyAudio"),
            ),
        ):
            audio_manager = AudioManager()
            assert not audio_manager.is_available

    @patch("voice_mcp.voice.audio.pyaudio")
    def test_init_with_pyaudio_success(self, mock_pyaudio):
        """Test successful AudioManager initialization with PyAudio available."""
        mock_audio_instance = Mock()
        mock_pyaudio.PyAudio.return_value = mock_audio_instance

        with patch("voice_mcp.voice.audio.PYAUDIO_AVAILABLE", True):
            audio_manager = AudioManager()

            assert audio_manager.is_available
            assert audio_manager.audio == mock_audio_instance
            mock_pyaudio.PyAudio.assert_called_once()

    @patch("voice_mcp.voice.audio.pyaudio")
    def test_init_with_pyaudio_failure(self, mock_pyaudio):
        """Test AudioManager initialization when PyAudio initialization fails."""
        mock_pyaudio.PyAudio.side_effect = Exception("Audio device not found")

        with patch("voice_mcp.voice.audio.PYAUDIO_AVAILABLE", True):
            audio_manager = AudioManager()

            assert not audio_manager.is_available
            assert audio_manager.audio is None

    def test_resolve_assets_path_default(self):
        """Test default assets path resolution."""
        audio_manager = AudioManager()
        assert audio_manager._assets_path.name == "assets"

    def test_resolve_assets_path_custom(self, tmp_path):
        """Test custom assets path resolution."""
        custom_path = tmp_path / "custom_assets"
        custom_path.mkdir()

        audio_manager = AudioManager(assets_path=custom_path)
        assert audio_manager._assets_path == custom_path

    @patch("voice_mcp.voice.audio.pyaudio")
    @patch("voice_mcp.voice.audio.wave")
    def test_preload_audio_files_success(self, mock_wave, mock_pyaudio, tmp_path):
        """Test successful audio file preloading."""
        # Setup
        mock_audio_instance = Mock()
        mock_pyaudio.PyAudio.return_value = mock_audio_instance
        mock_audio_instance.get_format_from_width.return_value = 1

        # Create mock wave file
        mock_wave_file = MagicMock()
        mock_wave_file.readframes.return_value = b"audio_data"
        mock_wave_file.getnframes.return_value = 1000
        mock_wave_file.getsampwidth.return_value = 2
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.__enter__.return_value = mock_wave_file
        mock_wave_file.__exit__.return_value = None
        mock_wave.open.return_value = mock_wave_file

        # Create actual files
        (tmp_path / "on.wav").touch()
        (tmp_path / "off.wav").touch()

        with patch("voice_mcp.voice.audio.PYAUDIO_AVAILABLE", True):
            audio_manager = AudioManager(assets_path=tmp_path)

            assert "on.wav" in audio_manager.audio_data
            assert "off.wav" in audio_manager.audio_data
            assert audio_manager.audio_data["on.wav"]["frames"] == b"audio_data"
            assert audio_manager.audio_data["on.wav"]["rate"] == 16000

    @patch("voice_mcp.voice.audio.pyaudio")
    def test_preload_audio_files_missing_files(self, mock_pyaudio, tmp_path):
        """Test preloading when audio files are missing."""
        mock_audio_instance = Mock()
        mock_pyaudio.PyAudio.return_value = mock_audio_instance

        with patch("voice_mcp.voice.audio.PYAUDIO_AVAILABLE", True):
            audio_manager = AudioManager(assets_path=tmp_path)

            assert len(audio_manager.audio_data) == 0

    def test_play_audio_file_not_available(self):
        """Test audio playback when system is not available."""
        with (
            patch("voice_mcp.voice.audio.PYAUDIO_AVAILABLE", False),
            patch(
                "voice_mcp.voice.audio.pyaudio.PyAudio",
                side_effect=Exception("No PyAudio"),
            ),
        ):
            audio_manager = AudioManager()

            result = audio_manager.play_audio_file("on.wav")
            assert result is False

    @patch("voice_mcp.voice.audio.pyaudio")
    def test_play_audio_file_not_preloaded(self, mock_pyaudio):
        """Test audio playback when file is not preloaded."""
        mock_audio_instance = Mock()
        mock_pyaudio.PyAudio.return_value = mock_audio_instance

        with patch("voice_mcp.voice.audio.PYAUDIO_AVAILABLE", True):
            audio_manager = AudioManager()

            result = audio_manager.play_audio_file("nonexistent.wav")
            assert result is False

    @patch("voice_mcp.voice.audio.pyaudio")
    @patch("voice_mcp.voice.audio.threading.Thread")
    def test_play_audio_file_success(self, mock_thread, mock_pyaudio):
        """Test successful audio file playback."""
        mock_audio_instance = Mock()
        mock_pyaudio.PyAudio.return_value = mock_audio_instance
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        with patch("voice_mcp.voice.audio.PYAUDIO_AVAILABLE", True):
            audio_manager = AudioManager()

            # Manually add audio data for testing
            audio_manager.audio_data["test.wav"] = {
                "frames": b"test_audio_data",
                "format": 1,
                "channels": 1,
                "rate": 16000,
                "duration": 1.0,
            }

            result = audio_manager.play_audio_file("test.wav")

            assert result is True
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()

    @patch("voice_mcp.voice.audio.pyaudio")
    def test_play_audio_thread_success(self, mock_pyaudio):
        """Test the internal audio playback thread."""
        mock_audio_instance = Mock()
        mock_stream = Mock()
        mock_audio_instance.open.return_value = mock_stream
        mock_pyaudio.PyAudio.return_value = mock_audio_instance

        with patch("voice_mcp.voice.audio.PYAUDIO_AVAILABLE", True):
            audio_manager = AudioManager()

            # Manually add audio data for testing
            audio_data = {
                "frames": b"test_audio_data",
                "format": 1,
                "channels": 1,
                "rate": 16000,
                "duration": 1.0,
            }
            audio_manager.audio_data["test.wav"] = audio_data

            # Call the thread method directly
            audio_manager._play_audio_thread("test.wav")

            # Verify the audio stream was used correctly
            mock_audio_instance.open.assert_called_once_with(
                format=1, channels=1, rate=16000, output=True
            )
            mock_stream.write.assert_called_once_with(b"test_audio_data")
            mock_stream.stop_stream.assert_called_once()
            mock_stream.close.assert_called_once()

    @patch("voice_mcp.voice.audio.pyaudio")
    def test_play_audio_thread_exception(self, mock_pyaudio):
        """Test audio playback thread with exception."""
        mock_audio_instance = Mock()
        mock_audio_instance.open.side_effect = Exception("Stream error")
        mock_pyaudio.PyAudio.return_value = mock_audio_instance

        with patch("voice_mcp.voice.audio.PYAUDIO_AVAILABLE", True):
            audio_manager = AudioManager()

            # Manually add audio data for testing
            audio_manager.audio_data["test.wav"] = {
                "frames": b"test_audio_data",
                "format": 1,
                "channels": 1,
                "rate": 16000,
                "duration": 1.0,
            }

            # Should not raise exception
            audio_manager._play_audio_thread("test.wav")

    @patch("voice_mcp.voice.audio.pyaudio")
    def test_play_on_sound(self, mock_pyaudio):
        """Test play_on_sound method."""
        mock_audio_instance = Mock()
        mock_pyaudio.PyAudio.return_value = mock_audio_instance

        with patch("voice_mcp.voice.audio.PYAUDIO_AVAILABLE", True):
            audio_manager = AudioManager()

            with patch.object(audio_manager, "play_audio_file") as mock_play:
                mock_play.return_value = True
                result = audio_manager.play_on_sound()

                assert result is True
                mock_play.assert_called_once_with("on.wav")

    @patch("voice_mcp.voice.audio.pyaudio")
    def test_play_off_sound(self, mock_pyaudio):
        """Test play_off_sound method."""
        mock_audio_instance = Mock()
        mock_pyaudio.PyAudio.return_value = mock_audio_instance

        with patch("voice_mcp.voice.audio.PYAUDIO_AVAILABLE", True):
            audio_manager = AudioManager()

            with patch.object(audio_manager, "play_audio_file") as mock_play:
                mock_play.return_value = True
                result = audio_manager.play_off_sound()

                assert result is True
                mock_play.assert_called_once_with("off.wav")

    @patch("voice_mcp.voice.audio.pyaudio")
    def test_cleanup(self, mock_pyaudio):
        """Test cleanup method."""
        mock_audio_instance = Mock()
        mock_pyaudio.PyAudio.return_value = mock_audio_instance

        with patch("voice_mcp.voice.audio.PYAUDIO_AVAILABLE", True):
            audio_manager = AudioManager()

            # Add some test data
            audio_manager.audio_data["test.wav"] = {"data": "test"}

            audio_manager.cleanup()

            mock_audio_instance.terminate.assert_called_once()
            assert audio_manager.audio is None
            assert not audio_manager.is_available
            assert len(audio_manager.audio_data) == 0

    @patch("voice_mcp.voice.audio.pyaudio")
    def test_cleanup_with_exception(self, mock_pyaudio):
        """Test cleanup method with exception."""
        mock_audio_instance = Mock()
        mock_audio_instance.terminate.side_effect = Exception("Cleanup error")
        mock_pyaudio.PyAudio.return_value = mock_audio_instance

        with patch("voice_mcp.voice.audio.PYAUDIO_AVAILABLE", True):
            audio_manager = AudioManager()

            # Should not raise exception
            audio_manager.cleanup()

            assert audio_manager.audio is None
            assert not audio_manager.is_available

    @patch("voice_mcp.voice.audio.pyaudio")
    def test_context_manager(self, mock_pyaudio):
        """Test AudioManager as context manager."""
        mock_audio_instance = Mock()
        mock_pyaudio.PyAudio.return_value = mock_audio_instance

        with patch("voice_mcp.voice.audio.PYAUDIO_AVAILABLE", True):
            with AudioManager() as audio_manager:
                assert audio_manager.is_available
                assert isinstance(audio_manager, AudioManager)

            # Cleanup should have been called
            mock_audio_instance.terminate.assert_called_once()


class TestAudioManagerIntegration:
    """Integration tests for AudioManager with real file operations."""

    def create_test_wav_file(self, file_path: Path, duration: float = 0.1) -> None:
        """Create a test WAV file."""
        sample_rate = 16000
        frequency = 440  # A4 note

        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
        audio_data = (audio_data * 32767).astype(np.int16)

        with wave.open(str(file_path), "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

    @patch("voice_mcp.voice.audio.pyaudio")
    def test_integration_with_real_wav_files(self, mock_pyaudio, tmp_path):
        """Test AudioManager with real WAV files."""
        mock_audio_instance = Mock()
        mock_audio_instance.get_format_from_width.return_value = 1
        mock_pyaudio.PyAudio.return_value = mock_audio_instance

        # Create real test WAV files
        on_file = tmp_path / "on.wav"
        off_file = tmp_path / "off.wav"
        self.create_test_wav_file(on_file, 0.1)
        self.create_test_wav_file(off_file, 0.1)

        with patch("voice_mcp.voice.audio.PYAUDIO_AVAILABLE", True):
            audio_manager = AudioManager(assets_path=tmp_path)

            # Verify files were preloaded
            assert "on.wav" in audio_manager.audio_data
            assert "off.wav" in audio_manager.audio_data

            # Verify audio data structure
            on_data = audio_manager.audio_data["on.wav"]
            assert "frames" in on_data
            assert "format" in on_data
            assert "channels" in on_data
            assert "rate" in on_data
            assert "duration" in on_data
            assert on_data["channels"] == 1
            assert on_data["rate"] == 16000

    @patch("voice_mcp.voice.audio.pyaudio")
    def test_thread_safety(self, mock_pyaudio):
        """Test AudioManager thread safety."""
        mock_audio_instance = Mock()
        mock_pyaudio.PyAudio.return_value = mock_audio_instance

        with patch("voice_mcp.voice.audio.PYAUDIO_AVAILABLE", True):
            audio_manager = AudioManager()

            # Manually add test data
            audio_manager.audio_data["test.wav"] = {
                "frames": b"test_data",
                "format": 1,
                "channels": 1,
                "rate": 16000,
                "duration": 1.0,
            }

            # Create multiple threads trying to play audio
            threads = []
            results = []

            def play_audio():
                result = audio_manager.play_audio_file("test.wav")
                results.append(result)

            for _ in range(5):
                thread = threading.Thread(target=play_audio)
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            # All calls should succeed
            assert all(results)
            assert len(results) == 5
