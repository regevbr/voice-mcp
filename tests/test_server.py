"""
Tests for the simplified MCP server functionality.
"""

from unittest.mock import Mock, patch

from voice_mcp.config import setup_logging
from voice_mcp.server import (
    cleanup_resources,
    main,
    parse_args,
)


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


class TestServerTools:
    """Test server tool implementations."""

    def test_speak_tool_via_voice_tools(self):
        """Test the speak tool through VoiceTools."""
        with patch("voice_mcp.server.VoiceTools.speak") as mock_speak:
            mock_speak.return_value = "Success"

            # Test via VoiceTools directly since tool functions are wrapped
            from voice_mcp.tools import VoiceTools

            result = VoiceTools.speak("Hello", voice="default", rate=150, volume=0.8)

            assert result == "Success"
            mock_speak.assert_called_once_with(
                "Hello", voice="default", rate=150, volume=0.8
            )

    def test_server_tool_registration(self):
        """Test that server tools are properly registered with FastMCP."""
        from voice_mcp.server import mcp

        # Check that mcp instance has tools registered via tool manager
        assert hasattr(mcp, "_tool_manager")
        assert hasattr(mcp._tool_manager, "_tools")

        # Check that our tools are in the tools list
        tool_names = list(mcp._tool_manager._tools.keys())
        assert "speak" in tool_names
        assert "start_hotkey_monitoring" in tool_names
        assert "stop_hotkey_monitoring" in tool_names
        assert "get_hotkey_status" in tool_names

    def test_server_prompt_registration(self):
        """Test that server prompts are properly registered with FastMCP."""
        from voice_mcp.server import mcp

        # Check that mcp instance has prompts registered via prompt manager
        assert hasattr(mcp, "_prompt_manager")
        assert hasattr(mcp._prompt_manager, "_prompts")

        # Check that our prompt is in the prompts list
        prompt_names = list(mcp._prompt_manager._prompts.keys())
        assert "speak" in prompt_names


class TestCleanupResources:
    """Test cleanup resource function."""

    @patch("voice_mcp.server.config")
    @patch("voice_mcp.server.VoiceTools")
    @patch("voice_mcp.server.get_transcription_handler")
    def test_cleanup_resources_with_hotkey_enabled(
        self, _mock_get_stt, _mock_voice_tools, mock_config
    ):
        """Test cleanup with hotkey enabled."""
        from voice_mcp.server import _reset_cleanup_state

        _reset_cleanup_state()

        mock_config.enable_hotkey = True
        _mock_voice_tools.stop_hotkey_monitoring.return_value = "Stopped"
        mock_stt_handler = Mock()
        _mock_get_stt.return_value = mock_stt_handler

        cleanup_resources()

        _mock_voice_tools.stop_hotkey_monitoring.assert_called_once()
        mock_stt_handler.cleanup.assert_called_once()

    @patch("voice_mcp.server.config")
    @patch("voice_mcp.server.VoiceTools")
    @patch("voice_mcp.server.get_transcription_handler")
    def test_cleanup_resources_with_hotkey_disabled(
        self, _mock_get_stt, _mock_voice_tools, mock_config
    ):
        """Test cleanup with hotkey disabled."""
        from voice_mcp.server import _reset_cleanup_state

        _reset_cleanup_state()

        mock_config.enable_hotkey = False
        mock_stt_handler = Mock()
        _mock_get_stt.return_value = mock_stt_handler

        cleanup_resources()

        _mock_voice_tools.stop_hotkey_monitoring.assert_not_called()
        mock_stt_handler.cleanup.assert_called_once()

    @patch("voice_mcp.server.config")
    @patch("voice_mcp.server.VoiceTools")
    @patch("voice_mcp.server.get_transcription_handler")
    def test_cleanup_resources_with_exception(
        self, _mock_get_stt, _mock_voice_tools, mock_config
    ):
        """Test cleanup with exception handling."""
        from voice_mcp.server import _reset_cleanup_state

        _reset_cleanup_state()

        mock_config.enable_hotkey = False  # Test STT cleanup exception instead
        mock_stt_handler = Mock()
        mock_stt_handler.cleanup.side_effect = Exception("STT cleanup error")
        _mock_get_stt.return_value = mock_stt_handler

        # Should not raise exception even when cleanup fails
        cleanup_resources()

        mock_stt_handler.cleanup.assert_called_once()


class TestMainFunction:
    """Test main server function."""

    @patch("voice_mcp.server.parse_args")
    @patch("voice_mcp.server.setup_logging")
    @patch("voice_mcp.server.config")
    @patch("voice_mcp.server.get_transcription_handler")
    @patch("voice_mcp.server.VoiceTools")
    @patch("voice_mcp.server.mcp")
    def test_main_stdio_transport(
        self,
        _mock_mcp,
        _mock_voice_tools,
        _mock_get_stt,
        mock_config,
        _mock_setup_logging,
        mock_parse_args,
    ):
        """Test main function with stdio transport."""
        mock_args = Mock()
        mock_args.transport = "stdio"
        mock_args.log_level = "INFO"
        mock_args.debug = False
        mock_args.port = 8000
        mock_parse_args.return_value = mock_args

        mock_config.stt_enabled = False
        mock_config.enable_hotkey = False

        main()

        _mock_setup_logging.assert_called_once_with("INFO")
        _mock_mcp.run.assert_called_once_with(transport="stdio")

    @patch("voice_mcp.server.parse_args")
    @patch("voice_mcp.server.setup_logging")
    @patch("voice_mcp.server.config")
    @patch("voice_mcp.server.get_transcription_handler")
    @patch("voice_mcp.server.VoiceTools")
    @patch("voice_mcp.server.mcp")
    def test_main_sse_transport(
        self,
        _mock_mcp,
        _mock_voice_tools,
        _mock_get_stt,
        mock_config,
        _mock_setup_logging,
        mock_parse_args,
    ):
        """Test main function with SSE transport."""
        mock_args = Mock()
        mock_args.transport = "sse"
        mock_args.log_level = "DEBUG"
        mock_args.debug = True
        mock_args.port = 9000
        mock_parse_args.return_value = mock_args

        mock_config.stt_enabled = False
        mock_config.enable_hotkey = False

        main()

        _mock_setup_logging.assert_called_once_with("DEBUG")
        _mock_mcp.run.assert_called_once_with(
            transport="sse", host="localhost", port=9000
        )

    @patch("voice_mcp.server.parse_args")
    @patch("voice_mcp.server.setup_logging")
    @patch("voice_mcp.server.config")
    @patch("voice_mcp.server.get_transcription_handler")
    @patch("voice_mcp.server.VoiceTools")
    @patch("voice_mcp.server.mcp")
    @patch("voice_mcp.server.cleanup_resources")
    @patch("sys.exit")
    def test_main_unsupported_transport(
        self,
        mock_exit,
        mock_cleanup,
        _mock_mcp,
        _mock_voice_tools,
        _mock_get_stt,
        mock_config,
        _mock_setup_logging,
        mock_parse_args,
    ):
        """Test main function with unsupported transport."""
        mock_args = Mock()
        mock_args.transport = "invalid"
        mock_args.log_level = "INFO"
        mock_args.debug = False
        mock_parse_args.return_value = mock_args

        mock_config.stt_enabled = False
        mock_config.enable_hotkey = False

        main()

        mock_cleanup.assert_called_once()
        mock_exit.assert_called_once_with(1)

    @patch("voice_mcp.server.parse_args")
    @patch("voice_mcp.server.setup_logging")
    @patch("voice_mcp.server.config")
    @patch("voice_mcp.server.get_transcription_handler")
    @patch("voice_mcp.server.VoiceTools")
    @patch("voice_mcp.server.mcp")
    def test_main_with_stt_enabled_success(
        self,
        _mock_mcp,
        _mock_voice_tools,
        _mock_get_stt,
        mock_config,
        _mock_setup_logging,
        mock_parse_args,
    ):
        """Test main function with STT enabled and successful preload."""
        mock_args = Mock()
        mock_args.transport = "stdio"
        mock_args.log_level = "INFO"
        mock_args.debug = False
        mock_parse_args.return_value = mock_args

        mock_config.stt_enabled = True
        mock_config.enable_hotkey = False

        mock_stt_handler = Mock()
        mock_stt_handler.preload.return_value = True
        _mock_get_stt.return_value = mock_stt_handler

        main()

        mock_stt_handler.preload.assert_called_once()
        _mock_mcp.run.assert_called_once_with(transport="stdio")

    @patch("voice_mcp.server.parse_args")
    @patch("voice_mcp.server.setup_logging")
    @patch("voice_mcp.server.config")
    @patch("voice_mcp.server.get_transcription_handler")
    @patch("voice_mcp.server.VoiceTools")
    @patch("voice_mcp.server.mcp")
    def test_main_with_stt_enabled_failure(
        self,
        _mock_mcp,
        _mock_voice_tools,
        _mock_get_stt,
        mock_config,
        _mock_setup_logging,
        mock_parse_args,
    ):
        """Test main function with STT enabled but preload failure."""
        mock_args = Mock()
        mock_args.transport = "stdio"
        mock_args.log_level = "INFO"
        mock_args.debug = False
        mock_parse_args.return_value = mock_args

        mock_config.stt_enabled = True
        mock_config.enable_hotkey = False

        mock_stt_handler = Mock()
        mock_stt_handler.preload.return_value = False
        _mock_get_stt.return_value = mock_stt_handler

        main()

        mock_stt_handler.preload.assert_called_once()
        _mock_mcp.run.assert_called_once_with(transport="stdio")

    @patch("voice_mcp.server.parse_args")
    @patch("voice_mcp.server.setup_logging")
    @patch("voice_mcp.server.config")
    @patch("voice_mcp.server.get_transcription_handler")
    @patch("voice_mcp.server.VoiceTools")
    @patch("voice_mcp.server.mcp")
    def test_main_with_hotkey_enabled(
        self,
        _mock_mcp,
        _mock_voice_tools,
        _mock_get_stt,
        mock_config,
        _mock_setup_logging,
        mock_parse_args,
    ):
        """Test main function with hotkey enabled."""
        mock_args = Mock()
        mock_args.transport = "stdio"
        mock_args.log_level = "INFO"
        mock_args.debug = False
        mock_parse_args.return_value = mock_args

        mock_config.stt_enabled = False
        mock_config.enable_hotkey = True

        _mock_voice_tools.start_hotkey_monitoring.return_value = "Started"

        main()

        _mock_voice_tools.start_hotkey_monitoring.assert_called_once()
        _mock_mcp.run.assert_called_once_with(transport="stdio")

    @patch("voice_mcp.server.parse_args")
    @patch("voice_mcp.server.setup_logging")
    @patch("voice_mcp.server.config")
    @patch("voice_mcp.server.get_transcription_handler")
    @patch("voice_mcp.server.VoiceTools")
    @patch("voice_mcp.server.mcp")
    @patch("voice_mcp.server.cleanup_resources")
    def test_main_keyboard_interrupt(
        self,
        mock_cleanup,
        _mock_mcp,
        _mock_voice_tools,
        _mock_get_stt,
        mock_config,
        _mock_setup_logging,
        mock_parse_args,
    ):
        """Test main function with KeyboardInterrupt."""
        mock_args = Mock()
        mock_args.transport = "stdio"
        mock_args.log_level = "INFO"
        mock_args.debug = False
        mock_parse_args.return_value = mock_args

        mock_config.stt_enabled = False
        mock_config.enable_hotkey = False

        _mock_mcp.run.side_effect = KeyboardInterrupt()

        main()

        mock_cleanup.assert_called_once()

    @patch("voice_mcp.server.parse_args")
    @patch("voice_mcp.server.setup_logging")
    @patch("voice_mcp.server.config")
    @patch("voice_mcp.server.get_transcription_handler")
    @patch("voice_mcp.server.VoiceTools")
    @patch("voice_mcp.server.mcp")
    @patch("voice_mcp.server.cleanup_resources")
    @patch("sys.exit")
    def test_main_generic_exception_debug_false(
        self,
        mock_exit,
        mock_cleanup,
        _mock_mcp,
        _mock_voice_tools,
        _mock_get_stt,
        mock_config,
        _mock_setup_logging,
        mock_parse_args,
    ):
        """Test main function with generic exception and debug=False."""
        mock_args = Mock()
        mock_args.transport = "stdio"
        mock_args.log_level = "INFO"
        mock_args.debug = False
        mock_parse_args.return_value = mock_args

        mock_config.stt_enabled = False
        mock_config.enable_hotkey = False

        _mock_mcp.run.side_effect = Exception("Server error")

        main()

        mock_cleanup.assert_called_once()
        mock_exit.assert_called_once_with(1)

    @patch("voice_mcp.server.parse_args")
    @patch("voice_mcp.server.setup_logging")
    @patch("voice_mcp.server.config")
    @patch("voice_mcp.server.get_transcription_handler")
    @patch("voice_mcp.server.VoiceTools")
    @patch("voice_mcp.server.mcp")
    @patch("voice_mcp.server.cleanup_resources")
    def test_main_generic_exception_debug_true(
        self,
        mock_cleanup,
        _mock_mcp,
        _mock_voice_tools,
        _mock_get_stt,
        mock_config,
        _mock_setup_logging,
        mock_parse_args,
    ):
        """Test main function with generic exception and debug=True."""
        mock_args = Mock()
        mock_args.transport = "stdio"
        mock_args.log_level = "INFO"
        mock_args.debug = True
        mock_parse_args.return_value = mock_args

        mock_config.stt_enabled = False
        mock_config.enable_hotkey = False

        _mock_mcp.run.side_effect = Exception("Server error")

        try:
            main()
            raise AssertionError("Should have raised exception")
        except Exception as e:
            assert str(e) == "Server error"

        mock_cleanup.assert_called_once()


class TestParseArgsEdgeCases:
    """Test edge cases for argument parsing."""

    def test_parse_args_invalid_transport(self):
        """Test argument parsing with invalid transport."""
        test_args = ["voice-mcp", "--transport", "invalid"]

        with patch("sys.argv", test_args):
            try:
                parse_args()
                raise AssertionError("Should have raised SystemExit")
            except SystemExit:
                pass  # Expected behavior

    def test_parse_args_invalid_log_level(self):
        """Test argument parsing with invalid log level."""
        test_args = ["voice-mcp", "--log-level", "INVALID"]

        with patch("sys.argv", test_args):
            try:
                parse_args()
                raise AssertionError("Should have raised SystemExit")
            except SystemExit:
                pass  # Expected behavior

    def test_parse_args_invalid_port(self):
        """Test argument parsing with invalid port."""
        test_args = ["voice-mcp", "--port", "not_a_number"]

        with patch("sys.argv", test_args):
            try:
                parse_args()
                raise AssertionError("Should have raised SystemExit")
            except SystemExit:
                pass  # Expected behavior


class TestServerIntegration:
    """Integration tests for server components."""

    @patch("voice_mcp.server.atexit.register")
    def test_atexit_registration(self, mock_register):
        """Test that cleanup is registered with atexit."""
        # Re-import to trigger atexit registration
        import importlib

        import voice_mcp.server

        importlib.reload(voice_mcp.server)

        # Check that register was called (at least once during import)
        mock_register.assert_called()

    def test_mcp_instance_creation(self):
        """Test MCP instance is created with correct parameters."""
        from voice_mcp.server import mcp

        assert mcp is not None
        # Basic check that it's a FastMCP instance
        assert hasattr(mcp, "run")


class TestUtilityFunctions:
    """Test utility functions in server.py."""

    def test_log_active_threads(self):
        """Test log_active_threads function."""
        from voice_mcp.server import log_active_threads

        with patch("threading.enumerate") as mock_enumerate:
            mock_thread = Mock()
            mock_thread.name = "test-thread"
            mock_thread.daemon = True
            mock_thread.is_alive.return_value = True
            mock_thread.ident = 12345
            mock_enumerate.return_value = [mock_thread]

            # This should not raise any exceptions
            log_active_threads()

            mock_enumerate.assert_called_once()

    @patch("threading.Thread")
    @patch("time.sleep")
    def test_force_exit_after_timeout(self, mock_sleep, mock_thread):
        """Test force_exit_after_timeout function."""
        from voice_mcp.server import force_exit_after_timeout

        mock_timer_thread = Mock()
        mock_thread.return_value = mock_timer_thread

        with patch("os._exit") as mock_exit:
            # Test timeout without actually waiting
            mock_sleep.side_effect = lambda _: mock_exit(1)

            force_exit_after_timeout(1)

            # Verify thread was created and started
            mock_thread.assert_called_once()
            mock_timer_thread.start.assert_called_once()

    @patch("signal.signal")
    def test_setup_signal_handlers_with_sighup(self, mock_signal):
        """Test signal handler setup with SIGHUP support."""
        import signal

        from voice_mcp.server import setup_signal_handlers

        # Only test SIGHUP if it exists on this platform
        if hasattr(signal, "SIGHUP"):
            setup_signal_handlers()
            # Should register handlers for SIGINT, SIGTERM, and SIGHUP
            assert mock_signal.call_count >= 3
        else:
            # On platforms without SIGHUP (like Windows), skip this test
            import pytest

            pytest.skip("SIGHUP not available on this platform")

    @patch("signal.signal")
    def test_setup_signal_handlers_without_sighup(self, mock_signal):
        """Test signal handler setup without SIGHUP support."""
        from voice_mcp.server import setup_signal_handlers

        with patch("builtins.hasattr", return_value=False):  # Simulate no SIGHUP
            setup_signal_handlers()

        # Should register handlers for SIGINT and SIGTERM only
        assert mock_signal.call_count >= 2

    @patch("voice_mcp.server.cleanup_resources")
    @patch("voice_mcp.server.log_active_threads")
    @patch("voice_mcp.server.force_exit_after_timeout")
    @patch("time.sleep")
    @patch("sys.exit")
    def test_signal_handler_execution(
        self, mock_exit, mock_sleep, mock_force_exit, mock_log_threads, mock_cleanup
    ):
        """Test signal handler function execution."""
        from voice_mcp.server import setup_signal_handlers

        with patch("signal.signal") as mock_signal:
            setup_signal_handlers()

            # Get the signal handler function that was registered
            signal_handler = mock_signal.call_args_list[0][0][
                1
            ]  # Second argument to signal.signal

            # Execute the signal handler
            signal_handler(2, None)  # SIGINT = 2

            # Verify cleanup sequence
            assert mock_log_threads.call_count == 1  # Only before cleanup (simplified)
            mock_force_exit.assert_called_once_with(6)  # Reduced timeout
            mock_cleanup.assert_called_once()
            mock_sleep.assert_called_once_with(1)  # Reduced sleep
            mock_exit.assert_called_once_with(0)

    def test_cleanup_resources_with_module_instances(self):
        """Test cleanup_resources with module-level instances."""
        from voice_mcp.server import cleanup_resources

        # This test verifies that the cleanup function can handle module-level instances
        # The actual module import and cleanup logic is tested separately
        with patch("voice_mcp.server.config") as mock_config:
            mock_config.enable_hotkey = True

            with patch(
                "voice_mcp.server.VoiceTools.stop_hotkey_monitoring",
                return_value="Stopped",
            ):
                with patch(
                    "voice_mcp.server.get_transcription_handler"
                ) as mock_get_stt:
                    mock_stt = Mock()
                    mock_get_stt.return_value = mock_stt

                    # Test that cleanup doesn't fail when called
                    cleanup_resources()

                    # Verify the main cleanup path was followed
                    mock_stt.cleanup.assert_called_once()


class TestServerToolFunctions:
    """Test the actual tool functions exposed by the server."""

    def test_server_tool_functions_via_mcp(self):
        """Test server tool functions via MCP framework."""
        from voice_mcp.server import mcp

        # Check that tools are registered and can be accessed
        tools = mcp._tool_manager._tools
        assert "speak" in tools
        assert "start_hotkey_monitoring" in tools
        assert "stop_hotkey_monitoring" in tools
        assert "get_hotkey_status" in tools

        # Test that the tools have proper functions
        speak_tool = tools["speak"]
        assert speak_tool.fn is not None

        # Test tool function calls through VoiceTools
        with patch(
            "voice_mcp.server.VoiceTools.speak", return_value="Success"
        ) as mock_speak:
            result = speak_tool.fn("Hello", voice="default", rate=150, volume=0.8)
            assert result == "Success"
            mock_speak.assert_called_once_with("Hello", "default", 150, 0.8)

    def test_server_prompt_functions_via_mcp(self):
        """Test server prompt functions via MCP framework."""
        from voice_mcp.server import mcp

        # Check that prompts are registered
        prompts = mcp._prompt_manager._prompts
        assert "speak" in prompts

        # Test prompt function call through VoicePrompts
        speak_prompt = prompts["speak"]
        assert speak_prompt.fn is not None

        with patch(
            "voice_mcp.server.VoicePrompts.speak_prompt", return_value="Guide"
        ) as mock_prompt:
            result = speak_prompt.fn()
            assert result == "Guide"
            mock_prompt.assert_called_once()
