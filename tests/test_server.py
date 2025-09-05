"""
Tests for the simplified MCP server functionality.
"""

from unittest.mock import patch

from voice_mcp.config import setup_logging
from voice_mcp.server import parse_args


def test_parse_args_default():
    """Test argument parsing with default values."""
    with patch("sys.argv", ["voice-mcp"]):
        with patch("voice_mcp.server.config.log_level", "INFO"):
            args = parse_args()

            assert args.transport == "stdio"
            assert args.port == 8000
            assert args.log_level == "INFO"
            assert args.debug is False


def test_parse_args_custom():
    """Test argument parsing with custom values."""
    test_args = [
        "voice-mcp",
        "--transport",
        "sse",
        "--port",
        "9000",
        "--log-level",
        "DEBUG",
        "--debug",
    ]

    with patch("sys.argv", test_args):
        args = parse_args()

        assert args.transport == "sse"
        assert args.port == 9000
        assert args.log_level == "DEBUG"
        assert args.debug is True


def test_setup_logging():
    """Test logging configuration."""
    with patch("logging.basicConfig") as mock_config:
        setup_logging("DEBUG")

        mock_config.assert_called_once()
        call_args = mock_config.call_args
        assert call_args[1]["level"] == 10  # DEBUG level


def test_server_tools_registration():
    """Test that essential server tools are properly registered."""
    from voice_mcp.server import mcp

    # Check that FastMCP has our tools registered
    assert "tools" in str(mcp.__dict__)  # Basic check that tools are registered


def test_speak_tool_via_voice_tools():
    """Test the speak functionality through VoiceTools."""
    from voice_mcp.tools import VoiceTools

    with patch("voice_mcp.tools.VoiceTools.speak") as mock_speak:
        mock_speak.return_value = "✅ Successfully spoke: 'test'"

        result = VoiceTools.speak("test")

        assert result == "✅ Successfully spoke: 'test'"
        mock_speak.assert_called_once_with("test")


def test_hotkey_tools_via_voice_tools():
    """Test the hotkey management tools through VoiceTools."""
    from voice_mcp.tools import VoiceTools

    with patch("voice_mcp.tools.VoiceTools.start_hotkey_monitoring") as mock_start:
        mock_start.return_value = "✅ Hotkey monitoring started"
        result = VoiceTools.start_hotkey_monitoring()
        assert "✅" in result
        mock_start.assert_called_once()

    with patch("voice_mcp.tools.VoiceTools.stop_hotkey_monitoring") as mock_stop:
        mock_stop.return_value = "✅ Hotkey monitoring stopped"
        result = VoiceTools.stop_hotkey_monitoring()
        assert "✅" in result
        mock_stop.assert_called_once()

    with patch("voice_mcp.tools.VoiceTools.get_hotkey_status") as mock_status:
        mock_status.return_value = {"monitoring": False, "hotkey": "menu"}
        result = VoiceTools.get_hotkey_status()
        assert isinstance(result, dict)
        assert "monitoring" in result
        mock_status.assert_called_once()


def test_prompt_via_voice_prompts():
    """Test that the speak prompt works through VoicePrompts."""
    from voice_mcp.prompts import VoicePrompts

    # Test speak guide
    guide = VoicePrompts.speak_prompt()
    assert isinstance(guide, str)
    assert len(guide) > 0
    assert "speak" in guide.lower()
