"""Tests for CLI module."""

import argparse
import sys
from unittest.mock import Mock, patch

import pytest

from voice_mcp.cli import (
    create_parser,
    handle_server_command,
    handle_test_command,
    handle_version_command,
    main,
)


class TestCreateParser:
    """Test parser creation and argument parsing."""

    def test_create_parser_basic(self):
        """Test basic parser creation."""
        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.prog == "voice-mcp"

    def test_parser_no_command(self):
        """Test parser with no command."""
        parser = create_parser()
        args = parser.parse_args([])
        assert args.command is None

    def test_server_command_defaults(self):
        """Test server command with default arguments."""
        parser = create_parser()
        args = parser.parse_args(["server"])
        assert args.command == "server"
        assert args.transport == "stdio"
        assert args.host == "localhost"
        assert args.port == 8000
        assert args.log_level == "INFO"
        assert args.debug is False

    def test_server_command_all_args(self):
        """Test server command with all arguments."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "server",
                "--transport",
                "sse",
                "--host",
                "127.0.0.1",
                "--port",
                "9000",
                "--log-level",
                "DEBUG",
                "--debug",
            ]
        )
        assert args.command == "server"
        assert args.transport == "sse"
        assert args.host == "127.0.0.1"
        assert args.port == 9000
        assert args.log_level == "DEBUG"
        assert args.debug is True

    def test_server_command_invalid_transport(self):
        """Test server command with invalid transport."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["server", "--transport", "invalid"])

    def test_server_command_invalid_log_level(self):
        """Test server command with invalid log level."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["server", "--log-level", "INVALID"])

    def test_server_command_invalid_port(self):
        """Test server command with invalid port."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["server", "--port", "not_a_number"])

    def test_version_command(self):
        """Test version command parsing."""
        parser = create_parser()
        args = parser.parse_args(["version"])
        assert args.command == "version"

    def test_test_command_defaults(self):
        """Test test command with default arguments."""
        parser = create_parser()
        args = parser.parse_args(["test"])
        assert args.command == "test"
        assert args.tts is False
        assert args.stt is False
        assert args.text == "Hello, this is a test of the voice MCP server."

    def test_test_command_all_args(self):
        """Test test command with all arguments."""
        parser = create_parser()
        args = parser.parse_args(
            ["test", "--tts", "--stt", "--text", "Custom test message"]
        )
        assert args.command == "test"
        assert args.tts is True
        assert args.stt is True
        assert args.text == "Custom test message"


class TestHandleServerCommand:
    """Test server command handling."""

    @patch("voice_mcp.cli.server_main")
    def test_handle_server_command_success(self, mock_server_main):
        """Test successful server command handling."""
        mock_server_main.return_value = None

        args = Mock()
        args.transport = "stdio"
        args.host = "localhost"
        args.port = 8000
        args.log_level = "INFO"
        args.debug = False

        original_argv = sys.argv[:]
        result = handle_server_command(args)

        assert result == 0
        mock_server_main.assert_called_once()
        assert sys.argv == original_argv  # Verify argv is restored

    @patch("voice_mcp.cli.server_main")
    def test_handle_server_command_with_all_args(self, mock_server_main):
        """Test server command with all arguments."""
        mock_server_main.return_value = None

        args = Mock()
        args.transport = "sse"
        args.host = "127.0.0.1"
        args.port = 9000
        args.log_level = "DEBUG"
        args.debug = True

        original_argv = sys.argv[:]
        result = handle_server_command(args)

        assert result == 0
        mock_server_main.assert_called_once()
        assert sys.argv == original_argv

    @patch("voice_mcp.cli.server_main")
    def test_handle_server_command_exception(self, mock_server_main):
        """Test server command handling with exception."""
        mock_server_main.side_effect = Exception("Test error")

        args = Mock()
        args.transport = "stdio"
        args.host = "localhost"
        args.port = 8000
        args.log_level = "INFO"
        args.debug = False

        original_argv = sys.argv[:]
        with patch("builtins.print") as mock_print:
            result = handle_server_command(args)

        assert result == 1
        mock_print.assert_called_with("Error starting server: Test error")
        assert sys.argv == original_argv

    @patch("voice_mcp.cli.server_main")
    def test_handle_server_command_none_values(self, mock_server_main):
        """Test server command with None values."""
        mock_server_main.return_value = None

        args = Mock()
        args.transport = None
        args.host = None
        args.port = None
        args.log_level = None
        args.debug = False

        original_argv = sys.argv[:]
        result = handle_server_command(args)

        assert result == 0
        assert sys.argv == original_argv


class TestHandleVersionCommand:
    """Test version command handling."""

    def test_handle_version_command(self):
        """Test version command handling."""
        args = Mock()

        with patch("voice_mcp.__version__", "1.0.0"):
            with patch("builtins.print") as mock_print:
                result = handle_version_command(args)

            assert result == 0
            mock_print.assert_called_with("Voice MCP Server v1.0.0")

    def test_handle_version_command_different_version(self):
        """Test version command with different version."""
        args = Mock()

        with patch("voice_mcp.__version__", "2.1.3-beta"):
            with patch("builtins.print") as mock_print:
                result = handle_version_command(args)

            assert result == 0
            mock_print.assert_called_with("Voice MCP Server v2.1.3-beta")


class TestHandleTestCommand:
    """Test test command handling."""

    def test_handle_test_command_default(self):
        """Test test command with default settings (both TTS and STT)."""
        args = Mock()
        args.tts = False
        args.stt = False
        args.text = "Test message"

        with patch("voice_mcp.tools.VoiceTools") as mock_voice_tools:
            mock_voice_tools.speak.return_value = "TTS success"
            mock_voice_tools.listen.return_value = "STT success"

            with patch("builtins.print") as mock_print:
                result = handle_test_command(args)

            assert result == 0
            mock_voice_tools.speak.assert_called_with("Test message")
            mock_voice_tools.listen.assert_called_with(5.0)

            # Check that both TTS and STT sections were printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("Testing Text-to-Speech" in call for call in print_calls)
            assert any("Testing Speech-to-Text" in call for call in print_calls)

    def test_handle_test_command_tts_only(self):
        """Test test command with TTS only."""
        args = Mock()
        args.tts = True
        args.stt = False
        args.text = "TTS test message"

        with patch("voice_mcp.tools.VoiceTools") as mock_voice_tools:
            mock_voice_tools.speak.return_value = "TTS success"

            with patch("builtins.print") as mock_print:
                result = handle_test_command(args)

            assert result == 0
            mock_voice_tools.speak.assert_called_with("TTS test message")
            mock_voice_tools.listen.assert_not_called()

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("Testing Text-to-Speech" in call for call in print_calls)
            assert not any("Testing Speech-to-Text" in call for call in print_calls)

    def test_handle_test_command_stt_only(self):
        """Test test command with STT only."""
        args = Mock()
        args.tts = False
        args.stt = True
        args.text = "Not used for STT"

        with patch("voice_mcp.tools.VoiceTools") as mock_voice_tools:
            mock_voice_tools.listen.return_value = "STT success"

            with patch("builtins.print") as mock_print:
                result = handle_test_command(args)

            assert result == 0
            mock_voice_tools.speak.assert_not_called()
            mock_voice_tools.listen.assert_called_with(5.0)

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert not any("Testing Text-to-Speech" in call for call in print_calls)
            assert any("Testing Speech-to-Text" in call for call in print_calls)

    def test_handle_test_command_tts_exception(self):
        """Test test command with TTS exception."""
        args = Mock()
        args.tts = False  # Default - both run
        args.stt = False
        args.text = "Test message"

        with patch("voice_mcp.tools.VoiceTools") as mock_voice_tools:
            mock_voice_tools.speak.side_effect = Exception("TTS failed")
            mock_voice_tools.listen.return_value = "STT success"

            with patch("builtins.print") as mock_print:
                result = handle_test_command(args)

            assert result == 0  # Command succeeds even if individual tests fail

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("TTS Error: TTS failed" in call for call in print_calls)

    def test_handle_test_command_stt_exception(self):
        """Test test command with STT exception."""
        args = Mock()
        args.tts = False  # Default - both run
        args.stt = False
        args.text = "Test message"

        with patch("voice_mcp.tools.VoiceTools") as mock_voice_tools:
            mock_voice_tools.speak.return_value = "TTS success"
            mock_voice_tools.listen.side_effect = Exception("STT failed")

            with patch("builtins.print") as mock_print:
                result = handle_test_command(args)

            assert result == 0

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("STT Error: STT failed" in call for call in print_calls)

    def test_handle_test_command_both_exceptions(self):
        """Test test command with both TTS and STT exceptions."""
        args = Mock()
        args.tts = False  # Default - both run
        args.stt = False
        args.text = "Test message"

        with patch("voice_mcp.tools.VoiceTools") as mock_voice_tools:
            mock_voice_tools.speak.side_effect = Exception("TTS failed")
            mock_voice_tools.listen.side_effect = Exception("STT failed")

            with patch("builtins.print") as mock_print:
                result = handle_test_command(args)

            assert result == 0

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("TTS Error: TTS failed" in call for call in print_calls)
            assert any("STT Error: STT failed" in call for call in print_calls)


class TestMain:
    """Test main CLI function."""

    def test_main_no_command(self):
        """Test main with no command."""
        parser_mock = Mock()
        parser_mock.parse_args.return_value = Mock(command=None)

        with patch("voice_mcp.cli.create_parser", return_value=parser_mock):
            result = main([])

        assert result == 1
        parser_mock.print_help.assert_called_once()

    @patch("voice_mcp.cli.handle_server_command")
    def test_main_server_command(self, mock_handle):
        """Test main with server command."""
        mock_handle.return_value = 0

        result = main(["server"])

        assert result == 0
        mock_handle.assert_called_once()

    @patch("voice_mcp.cli.handle_version_command")
    def test_main_version_command(self, mock_handle):
        """Test main with version command."""
        mock_handle.return_value = 0

        result = main(["version"])

        assert result == 0
        mock_handle.assert_called_once()

    @patch("voice_mcp.cli.handle_test_command")
    def test_main_test_command(self, mock_handle):
        """Test main with test command."""
        mock_handle.return_value = 0

        result = main(["test"])

        assert result == 0
        mock_handle.assert_called_once()

    def test_main_unknown_command(self):
        """Test main with unknown command."""
        # Mock parser to return unknown command
        parser_mock = Mock()
        parser_mock.parse_args.return_value = Mock(command="unknown")

        with patch("voice_mcp.cli.create_parser", return_value=parser_mock):
            with patch("builtins.print") as mock_print:
                result = main(["unknown"])

        assert result == 1
        mock_print.assert_called_with("Unknown command: unknown")

    def test_main_default_argv(self):
        """Test main with default argv (None)."""
        with patch("voice_mcp.cli.create_parser") as mock_create:
            mock_parser = Mock()
            mock_create.return_value = mock_parser
            mock_parser.parse_args.return_value = Mock(command=None)

            result = main(None)

            assert result == 1
            mock_parser.parse_args.assert_called_with(None)

    @patch("voice_mcp.cli.handle_server_command")
    def test_main_server_command_failure(self, mock_handle):
        """Test main with server command that fails."""
        mock_handle.return_value = 1

        result = main(["server"])

        assert result == 1
        mock_handle.assert_called_once()
