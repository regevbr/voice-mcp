"""
Tests for Voice MCP tools.
"""

from unittest.mock import Mock, patch

import pytest

from voice_mcp.tools import (
    VoiceTools,
    _on_hotkey_pressed,
    get_audio_manager,
    get_hotkey_manager,
    get_text_output_controller,
    get_tts_manager,
)


class TestManagerGetters:
    """Test suite for manager getter functions."""

    def test_get_tts_manager_singleton(self):
        """Test TTS manager singleton behavior."""
        # Clear global state first
        import voice_mcp.tools

        voice_mcp.tools._tts_manager = None

        with patch("voice_mcp.tools.TTSManager") as mock_tts_class:
            mock_instance = Mock()
            mock_tts_class.return_value = mock_instance

            # First call creates instance
            manager1 = get_tts_manager()
            assert manager1 == mock_instance
            mock_tts_class.assert_called_once()

            # Second call returns same instance
            manager2 = get_tts_manager()
            assert manager2 == mock_instance
            assert manager1 is manager2
            # Should not create another instance
            mock_tts_class.assert_called_once()

        # Clean up
        voice_mcp.tools._tts_manager = None

    def test_get_audio_manager_singleton(self):
        """Test AudioManager singleton behavior."""
        # Clear global state first
        import voice_mcp.tools

        voice_mcp.tools._audio_manager = None

        with patch("voice_mcp.tools.AudioManager") as mock_audio_class:
            mock_instance = Mock()
            mock_audio_class.return_value = mock_instance

            # First call creates instance
            manager1 = get_audio_manager()
            assert manager1 == mock_instance
            mock_audio_class.assert_called_once()

            # Second call returns same instance
            manager2 = get_audio_manager()
            assert manager2 == mock_instance
            assert manager1 is manager2
            mock_audio_class.assert_called_once()

        # Clean up
        voice_mcp.tools._audio_manager = None

    def test_get_text_output_controller_singleton(self):
        """Test TextOutputController singleton behavior."""
        # Clear global state first
        import voice_mcp.tools

        voice_mcp.tools._text_output_controller = None

        with patch("voice_mcp.tools.TextOutputController") as mock_controller_class:
            mock_instance = Mock()
            mock_controller_class.return_value = mock_instance

            # First call creates instance
            controller1 = get_text_output_controller()
            assert controller1 == mock_instance
            mock_controller_class.assert_called_once()

            # Second call returns same instance
            controller2 = get_text_output_controller()
            assert controller2 == mock_instance
            assert controller1 is controller2
            mock_controller_class.assert_called_once()

        # Clean up
        voice_mcp.tools._text_output_controller = None

    def test_get_hotkey_manager_singleton(self):
        """Test HotkeyManager singleton behavior."""
        # Clear global state first
        import voice_mcp.tools

        voice_mcp.tools._hotkey_manager = None

        with patch("voice_mcp.tools.HotkeyManager") as mock_hotkey_class:
            mock_instance = Mock()
            mock_hotkey_class.return_value = mock_instance

            # First call creates instance with callback
            manager1 = get_hotkey_manager()
            assert manager1 == mock_instance
            mock_hotkey_class.assert_called_once_with(
                on_hotkey_pressed=_on_hotkey_pressed
            )

            # Second call returns same instance
            manager2 = get_hotkey_manager()
            assert manager2 == mock_instance
            assert manager1 is manager2
            mock_hotkey_class.assert_called_once()

        # Clean up
        voice_mcp.tools._hotkey_manager = None


class TestHotkeyCallback:
    """Test suite for hotkey callback functionality."""

    @patch("voice_mcp.tools.get_transcription_handler")
    @patch("voice_mcp.tools.get_text_output_controller")
    @patch("voice_mcp.tools.get_audio_manager")
    def test_hotkey_callback_typing_mode_success(
        self, mock_get_audio, mock_get_text, mock_get_stt
    ):
        """Test successful hotkey callback with typing mode."""
        # Setup mocks
        mock_audio_manager = Mock()
        mock_audio_manager.is_available = True
        mock_get_audio.return_value = mock_audio_manager

        mock_text_controller = Mock()
        mock_text_controller.end_session_delayed.return_value = {
            "success": True,
            "message": "Session ended successfully",
            "clipboard_restored": True,
        }
        mock_get_text.return_value = mock_text_controller

        mock_stt_handler = Mock()
        mock_stt_handler.transcribe_with_realtime_output.return_value = {
            "success": True,
            "transcription": "Hello world",
            "duration": 3.5,
        }
        mock_get_stt.return_value = mock_stt_handler

        with patch("voice_mcp.tools.config.hotkey_output_mode", "typing"):
            with patch("voice_mcp.tools.config.stt_language", "en"):
                _on_hotkey_pressed()

                # Verify audio feedback
                mock_audio_manager.play_on_sound.assert_called_once()
                mock_audio_manager.play_off_sound.assert_called_once()

                # Verify STT was called with auto_end_session=False
                mock_stt_handler.transcribe_with_realtime_output.assert_called_once_with(
                    text_output_controller=mock_text_controller,
                    duration=None,
                    language="en",
                    auto_end_session=False,
                )

    @patch("voice_mcp.tools.VoiceTools.listen")
    def test_hotkey_callback_non_typing_mode(self, mock_listen):
        """Test hotkey callback with non-typing output mode."""
        mock_listen.return_value = {
            "status": "success",
            "transcription": "Test output",
            "duration": 2.0,
            "output_mode": "clipboard",
        }

        with patch("voice_mcp.tools.config.hotkey_output_mode", "clipboard"):
            with patch("voice_mcp.tools.config.stt_language", "en"):
                _on_hotkey_pressed()

                mock_listen.assert_called_once_with(
                    duration=None,
                    language="en",
                    output_mode="clipboard",
                )

    @patch("voice_mcp.tools.get_transcription_handler")
    @patch("voice_mcp.tools.get_text_output_controller")
    @patch("voice_mcp.tools.get_audio_manager")
    def test_hotkey_callback_stt_failure(
        self, mock_get_audio, mock_get_text, mock_get_stt
    ):
        """Test hotkey callback when STT fails."""
        mock_audio_manager = Mock()
        mock_audio_manager.is_available = True
        mock_get_audio.return_value = mock_audio_manager

        mock_text_controller = Mock()
        mock_get_text.return_value = mock_text_controller

        mock_stt_handler = Mock()
        mock_stt_handler.transcribe_with_realtime_output.return_value = {
            "success": False,
            "error": "Microphone not found",
        }
        mock_get_stt.return_value = mock_stt_handler

        with patch("voice_mcp.tools.config.hotkey_output_mode", "typing"):
            _on_hotkey_pressed()  # Should not raise exception

            mock_stt_handler.transcribe_with_realtime_output.assert_called_once()

    @patch("voice_mcp.tools.get_transcription_handler")
    @patch("voice_mcp.tools.get_text_output_controller")
    @patch("voice_mcp.tools.get_audio_manager")
    def test_hotkey_callback_audio_unavailable(
        self, mock_get_audio, mock_get_text, mock_get_stt
    ):
        """Test hotkey callback when audio is unavailable."""
        mock_audio_manager = Mock()
        mock_audio_manager.is_available = False
        mock_get_audio.return_value = mock_audio_manager

        mock_text_controller = Mock()
        mock_get_text.return_value = mock_text_controller

        mock_stt_handler = Mock()
        mock_stt_handler.transcribe_with_realtime_output.return_value = {
            "success": True,
            "transcription": "Test",
            "duration": 1.0,
        }
        mock_get_stt.return_value = mock_stt_handler

        with patch("voice_mcp.tools.config.hotkey_output_mode", "typing"):
            _on_hotkey_pressed()

            # Audio methods should not be called
            mock_audio_manager.play_on_sound.assert_not_called()
            mock_audio_manager.play_off_sound.assert_not_called()

    @patch("voice_mcp.tools.get_transcription_handler")
    def test_hotkey_callback_exception_handling(self, mock_get_stt):
        """Test hotkey callback exception handling."""
        mock_get_stt.side_effect = Exception("STT initialization failed")

        # Should not raise exception
        _on_hotkey_pressed()


class TestVoiceTools:
    """Test suite for VoiceTools class."""

    def test_speak_implementation(self, mock_tts_manager):
        """Test speak tool implementation."""
        result = VoiceTools.speak("Hello, world!")

        assert isinstance(result, str)
        assert "successfully spoke" in result.lower()
        mock_tts_manager.speak.assert_called_once()

    def test_speak_with_parameters(self, mock_tts_manager):
        """Test speak tool with optional parameters."""
        result = VoiceTools.speak(
            "Test message", voice="test_voice", rate=150, volume=0.8
        )

        assert isinstance(result, str)
        assert "successfully spoke" in result.lower()
        mock_tts_manager.speak.assert_called_once_with(
            "Test message", "test_voice", 150, 0.8
        )

    def test_speak_with_config_defaults(self, mock_tts_manager):
        """Test speak with configuration defaults."""
        with patch("voice_mcp.tools.config.tts_rate", 1.5):
            with patch("voice_mcp.tools.config.tts_volume", 0.7):
                result = VoiceTools.speak("Test message")

                assert isinstance(result, str)
                assert "successfully spoke" in result.lower()
                mock_tts_manager.speak.assert_called_once_with(
                    "Test message", None, 1.5, 0.7
                )

    def test_speak_exception_handling(self):
        """Test speak exception handling."""
        with patch("voice_mcp.tools.get_tts_manager") as mock_get_tts:
            mock_get_tts.side_effect = Exception("TTS initialization failed")

            result = VoiceTools.speak("Test message")

            assert isinstance(result, str)
            assert "❌ TTS error: TTS initialization failed" in result

    def test_speak_long_text(self, mock_tts_manager):
        """Test speak tool with long text."""
        long_text = "This is a very long text " * 20
        result = VoiceTools.speak(long_text)

        assert isinstance(result, str)
        assert "successfully spoke" in result.lower()
        mock_tts_manager.speak.assert_called_once()


class TestVoiceToolsSTT:
    """Test suite for VoiceTools STT functionality."""

    @patch("voice_mcp.tools.get_transcription_handler")
    @patch("voice_mcp.tools.get_audio_manager")
    def test_listen_success_return_mode(self, mock_get_audio, mock_get_stt):
        """Test successful listen with return mode."""
        # Setup mocks
        mock_audio_manager = Mock()
        mock_audio_manager.is_available = True
        mock_get_audio.return_value = mock_audio_manager

        mock_stt_handler = Mock()
        mock_stt_handler.transcribe_once.return_value = {
            "success": True,
            "transcription": "Hello world",
            "duration": 3.5,
            "language": "en",
            "model": "base",
        }
        mock_get_stt.return_value = mock_stt_handler

        result = VoiceTools.listen(duration=5.0, language="en", output_mode="return")

        assert result["status"] == "success"
        assert result["transcription"] == "Hello world"
        assert result["duration"] == 3.5
        assert result["language"] == "en"
        assert result["output_mode"] == "return"

        # Verify audio feedback
        mock_audio_manager.play_on_sound.assert_called_once()
        mock_audio_manager.play_off_sound.assert_called_once()

        # Verify STT was called
        mock_stt_handler.transcribe_once.assert_called_once_with(
            duration=5.0, language="en"
        )

    @patch("voice_mcp.tools.get_transcription_handler")
    @patch("voice_mcp.tools.get_audio_manager")
    @patch("voice_mcp.tools.get_text_output_controller")
    def test_listen_with_output_mode(self, mock_get_text, mock_get_audio, mock_get_stt):
        """Test listen with typing output mode."""
        mock_audio_manager = Mock()
        mock_audio_manager.is_available = True
        mock_get_audio.return_value = mock_audio_manager

        mock_text_controller = Mock()
        mock_text_controller.output_text.return_value = {"success": True}
        mock_get_text.return_value = mock_text_controller

        mock_stt_handler = Mock()
        mock_stt_handler.transcribe_once.return_value = {
            "success": True,
            "transcription": "Hello world",
            "duration": 2.0,
            "language": "en",
        }
        mock_get_stt.return_value = mock_stt_handler

        result = VoiceTools.listen(output_mode="typing")

        assert result["status"] == "success"
        assert result["transcription"] == "Hello world"
        mock_text_controller.output_text.assert_called_once_with(
            "Hello world", "typing"
        )

    @patch("voice_mcp.tools.get_transcription_handler")
    @patch("voice_mcp.tools.get_audio_manager")
    @patch("voice_mcp.tools.get_text_output_controller")
    def test_listen_output_failure(self, mock_get_text, mock_get_audio, mock_get_stt):
        """Test listen when text output fails."""
        mock_audio_manager = Mock()
        mock_audio_manager.is_available = True
        mock_get_audio.return_value = mock_audio_manager

        mock_text_controller = Mock()
        mock_text_controller.output_text.return_value = {
            "success": False,
            "error": "Clipboard not available",
        }
        mock_get_text.return_value = mock_text_controller

        mock_stt_handler = Mock()
        mock_stt_handler.transcribe_once.return_value = {
            "success": True,
            "transcription": "Hello world",
            "duration": 2.0,
        }
        mock_get_stt.return_value = mock_stt_handler

        result = VoiceTools.listen(output_mode="clipboard")

        assert result["status"] == "partial_success"
        assert "Transcription successful but output failed" in result["warning"]

    @patch("voice_mcp.tools.get_transcription_handler")
    @patch("voice_mcp.tools.get_audio_manager")
    def test_listen_stt_failure(self, mock_get_audio, mock_get_stt):
        """Test listen when STT fails."""
        mock_audio_manager = Mock()
        mock_audio_manager.is_available = True
        mock_get_audio.return_value = mock_audio_manager

        mock_stt_handler = Mock()
        mock_stt_handler.transcribe_once.return_value = {
            "success": False,
            "transcription": "",
            "error": "No microphone detected",
            "duration": 0.0,
        }
        mock_get_stt.return_value = mock_stt_handler

        result = VoiceTools.listen()

        assert result["status"] == "error"
        assert result["error"] == "No microphone detected"
        assert result["transcription"] == ""

    @patch("voice_mcp.tools.get_transcription_handler")
    @patch("voice_mcp.tools.get_audio_manager")
    def test_listen_exception_handling(self, mock_get_audio, mock_get_stt):
        """Test listen exception handling."""
        mock_audio_manager = Mock()
        mock_audio_manager.is_available = True
        mock_get_audio.return_value = mock_audio_manager

        mock_get_stt.side_effect = Exception("STT service unavailable")

        result = VoiceTools.listen()

        assert result["status"] == "error"
        assert "STT error: STT service unavailable" in result["error"]

        # Should still try to play off sound
        mock_audio_manager.play_off_sound.assert_called()


class TestVoiceToolsHotkey:
    """Test suite for VoiceTools hotkey functionality."""

    def test_start_hotkey_monitoring_disabled(self):
        """Test starting hotkey monitoring when disabled."""
        with patch("voice_mcp.tools.config.enable_hotkey", False):
            result = VoiceTools.start_hotkey_monitoring()

            assert "⚠️  Hotkey monitoring is disabled" in result

    def test_start_hotkey_monitoring_success(self, mock_hotkey_manager):
        """Test successful hotkey monitoring start."""
        mock_hotkey_manager.start_monitoring.return_value = {
            "success": True,
            "description": "menu key",
        }

        with patch("voice_mcp.tools.config.enable_hotkey", True):
            with patch("voice_mcp.tools.config.hotkey_name", "menu"):
                result = VoiceTools.start_hotkey_monitoring()

                assert isinstance(result, str)
                assert "✅" in result
                assert "started" in result.lower()
                mock_hotkey_manager.start_monitoring.assert_called_once_with("menu")

    def test_start_hotkey_monitoring_failure(self, mock_hotkey_manager):
        """Test hotkey monitoring start failure."""
        mock_hotkey_manager.start_monitoring.return_value = {
            "success": False,
            "error": "Hotkey already in use",
        }

        with patch("voice_mcp.tools.config.enable_hotkey", True):
            result = VoiceTools.start_hotkey_monitoring()

            assert "❌ Failed to start hotkey monitoring" in result
            assert "Hotkey already in use" in result

    def test_start_hotkey_monitoring_error(self, mock_hotkey_manager):
        """Test hotkey monitoring start when error occurs."""
        mock_hotkey_manager.start_monitoring.side_effect = Exception("Hotkey error")

        with patch("voice_mcp.tools.config.enable_hotkey", True):
            result = VoiceTools.start_hotkey_monitoring()

            assert isinstance(result, str)
            assert "❌" in result
            assert "Hotkey error" in result

    def test_stop_hotkey_monitoring_success(self, mock_hotkey_manager):
        """Test successful hotkey monitoring stop."""
        mock_hotkey_manager.stop_monitoring.return_value = {
            "success": True,
            "message": "Hotkey monitoring stopped",
        }

        result = VoiceTools.stop_hotkey_monitoring()

        assert isinstance(result, str)
        assert "✅" in result
        assert "stopped" in result.lower()
        mock_hotkey_manager.stop_monitoring.assert_called_once()

    def test_stop_hotkey_monitoring_failure(self, mock_hotkey_manager):
        """Test hotkey monitoring stop failure."""
        mock_hotkey_manager.stop_monitoring.return_value = {
            "success": False,
            "error": "No monitoring active",
        }

        result = VoiceTools.stop_hotkey_monitoring()

        assert "❌ Failed to stop hotkey monitoring" in result
        assert "No monitoring active" in result

    def test_stop_hotkey_monitoring_error(self, mock_hotkey_manager):
        """Test hotkey monitoring stop when error occurs."""
        mock_hotkey_manager.stop_monitoring.side_effect = Exception("Stop error")

        result = VoiceTools.stop_hotkey_monitoring()

        assert isinstance(result, str)
        assert "❌" in result
        assert "Stop error" in result

    def test_get_hotkey_status_success(self, mock_hotkey_manager):
        """Test getting hotkey status successfully."""
        mock_hotkey_manager.get_status.return_value = {
            "active": True,
            "hotkey": "menu",
            "thread_alive": True,
        }

        with patch("voice_mcp.tools.config.enable_hotkey", True):
            with patch("voice_mcp.tools.config.hotkey_name", "menu"):
                with patch("voice_mcp.tools.config.hotkey_output_mode", "typing"):
                    with patch("voice_mcp.tools.config.stt_language", "en"):
                        result = VoiceTools.get_hotkey_status()

                        assert result["active"] is True
                        assert result["hotkey"] == "menu"
                        assert result["configuration"]["enabled"] is True
                        assert result["configuration"]["hotkey_name"] == "menu"
                        assert result["configuration"]["output_mode"] == "typing"
                        assert result["configuration"]["language"] == "en"

    def test_get_hotkey_status_error(self, mock_hotkey_manager):
        """Test getting hotkey status when error occurs."""
        mock_hotkey_manager.get_status.side_effect = Exception("Status error")

        result = VoiceTools.get_hotkey_status()

        assert result["status"] == "error"
        assert result["error"] == "Status error"
        assert result["active"] is False


@pytest.mark.parametrize(
    "text,_expected_in_result",
    [
        ("", ""),
        ("Hello", "Hello"),
        ("Test with special chars: !@#$%", "Test with special"),
        ("Very long text " * 50, "Very long text"),
    ],
)
def test_speak_text_handling(text, _expected_in_result, mock_tts_manager):
    """Test speak tool with various text inputs."""
    result = VoiceTools.speak(text)

    assert isinstance(result, str)

    if not text.strip():
        # Empty text should return error without calling TTS manager
        assert "❌ No text provided to speak" in result
        mock_tts_manager.speak.assert_not_called()
    else:
        # Non-empty text should call TTS manager and succeed
        assert "successfully spoke" in result.lower()
        mock_tts_manager.speak.assert_called_once()
