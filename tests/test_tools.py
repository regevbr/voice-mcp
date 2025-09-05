"""
Tests for Voice MCP tools.
"""

import pytest

from voice_mcp.tools import VoiceTools


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

    def test_speak_long_text(self, mock_tts_manager):
        """Test speak tool with long text."""
        long_text = "This is a very long text " * 20
        result = VoiceTools.speak(long_text)

        assert isinstance(result, str)
        assert "successfully spoke" in result.lower()
        mock_tts_manager.speak.assert_called_once()

    def test_start_hotkey_monitoring(self, mock_hotkey_manager):
        """Test starting hotkey monitoring."""
        result = VoiceTools.start_hotkey_monitoring()

        assert isinstance(result, str)
        assert "✅" in result
        assert "started" in result.lower()
        mock_hotkey_manager.start_monitoring.assert_called_once()

    def test_stop_hotkey_monitoring(self, mock_hotkey_manager):
        """Test stopping hotkey monitoring."""
        result = VoiceTools.stop_hotkey_monitoring()

        assert isinstance(result, str)
        assert "✅" in result
        assert "stopped" in result.lower()
        mock_hotkey_manager.stop_monitoring.assert_called_once()


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


class TestVoiceToolsHotkey:
    """Test suite for VoiceTools hotkey functionality."""

    def test_start_hotkey_monitoring_success(self, mock_hotkey_manager):
        """Test successful hotkey monitoring start."""
        result = VoiceTools.start_hotkey_monitoring()

        assert isinstance(result, str)
        assert "✅" in result
        assert "started" in result.lower()
        mock_hotkey_manager.start_monitoring.assert_called_once()

    def test_stop_hotkey_monitoring_success(self, mock_hotkey_manager):
        """Test successful hotkey monitoring stop."""
        result = VoiceTools.stop_hotkey_monitoring()

        assert isinstance(result, str)
        assert "✅" in result
        assert "stopped" in result.lower()
        mock_hotkey_manager.stop_monitoring.assert_called_once()

    def test_start_hotkey_monitoring_error(self, mock_hotkey_manager):
        """Test hotkey monitoring start when error occurs."""
        mock_hotkey_manager.start_monitoring.side_effect = Exception("Hotkey error")

        result = VoiceTools.start_hotkey_monitoring()

        assert isinstance(result, str)
        assert "❌" in result
        assert "Hotkey error" in result

    def test_stop_hotkey_monitoring_error(self, mock_hotkey_manager):
        """Test hotkey monitoring stop when error occurs."""
        mock_hotkey_manager.stop_monitoring.side_effect = Exception("Stop error")

        result = VoiceTools.stop_hotkey_monitoring()

        assert isinstance(result, str)
        assert "❌" in result
        assert "Stop error" in result
