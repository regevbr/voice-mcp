"""
Tests for text output functionality.
"""

from unittest.mock import Mock, patch

from voice_mcp.voice.text_output import TextOutputController, _get_keyboard_module


class TestTextOutputController:
    """Test suite for TextOutputController class."""

    def test_initialization_default(self):
        """Test TextOutputController initialization with defaults."""
        with patch("voice_mcp.voice.text_output.config") as mock_config:
            mock_config.typing_debounce_delay = 0.2

            controller = TextOutputController()

            assert controller.debounce_delay == 0.2
            assert controller.last_typed_text == ""
            assert controller.last_update_time == 0
            assert controller._keyboard_controller is None

    def test_initialization_custom(self):
        """Test TextOutputController initialization with custom values."""
        controller = TextOutputController(debounce_delay=0.5)

        assert controller.debounce_delay == 0.5
        assert controller.last_typed_text == ""

    def test_get_text_diff_empty_old(self):
        """Test text diff with empty old text."""
        controller = TextOutputController()
        result = controller.get_text_diff("", "hello")
        assert result["type"] == "append"
        assert result["text"] == "hello"

    def test_get_text_diff_empty_new(self):
        """Test text diff with empty new text."""
        controller = TextOutputController()
        result = controller.get_text_diff("hello", "")
        assert result["type"] == "delete_all"
        assert result["chars_to_delete"] == 5

    def test_get_text_diff_identical(self):
        """Test text diff with identical text."""
        controller = TextOutputController()
        result = controller.get_text_diff("hello", "hello")
        assert result["type"] == "append"
        assert result["text"] == ""

    def test_get_text_diff_append(self):
        """Test text diff append case."""
        controller = TextOutputController()
        result = controller.get_text_diff("hello", "hello world")
        assert result["type"] == "append"
        assert result["text"] == " world"

    def test_get_text_diff_delete_suffix(self):
        """Test text diff delete suffix case."""
        controller = TextOutputController()
        result = controller.get_text_diff("hello world", "hello")
        assert result["type"] == "delete_suffix"
        assert result["chars_to_delete"] == 6

    def test_get_text_diff_replace_suffix(self):
        """Test text diff replace suffix case."""
        controller = TextOutputController()
        result = controller.get_text_diff("hello world", "hello there")
        assert result["type"] == "replace_suffix"
        assert result["chars_to_delete"] == 5
        assert result["text"] == "there"

    def test_get_text_diff_replace_all(self):
        """Test text diff replace all case."""
        controller = TextOutputController()
        result = controller.get_text_diff("hello", "goodbye")
        assert result["type"] == "replace_all"
        assert result["chars_to_delete"] == 5
        assert result["text"] == "goodbye"

    def test_get_text_diff_no_common_prefix(self):
        """Test text diff with no common prefix."""
        controller = TextOutputController()
        result = controller.get_text_diff("abc", "xyz")
        assert result["type"] == "replace_all"
        assert result["chars_to_delete"] == 3
        assert result["text"] == "xyz"

    @patch("voice_mcp.voice.text_output.time")
    def test_output_text_clipboard_mode(self, mock_time):
        """Test text output in clipboard mode."""
        mock_time.time.return_value = 100.0
        controller = TextOutputController()

        with patch.object(
            controller, "_copy_to_clipboard", return_value={"success": True}
        ) as mock_copy:
            result = controller.output_text("Hello World", mode="clipboard")

            assert result["success"] is True
            mock_copy.assert_called_once_with("Hello World")

    @patch("voice_mcp.voice.text_output.time")
    def test_output_text_typing_mode(self, mock_time):
        """Test text output in typing mode."""
        mock_time.time.return_value = 100.0
        controller = TextOutputController()

        with patch.object(
            controller, "_type_text_realtime", return_value={"success": True}
        ) as mock_type:
            result = controller.output_text("Hello", mode="typing")

            assert result["success"] is True
            mock_type.assert_called_once_with("Hello")

    def test_output_text_return_mode(self):
        """Test text output in return mode."""
        controller = TextOutputController()

        result = controller.output_text("Hello World", mode="return")

        assert result["success"] is True
        assert result["mode"] == "return"
        assert result["text"] == "Hello World"
        assert "returned successfully" in result["message"]

    def test_output_text_empty_text(self):
        """Test text output with empty text."""
        controller = TextOutputController()

        result = controller.output_text("", mode="return")

        assert result["success"] is True
        assert result["text"] == ""
        assert "No text to output" in result["message"]

    def test_output_text_whitespace_only(self):
        """Test text output with whitespace-only text."""
        controller = TextOutputController()

        result = controller.output_text("   ", mode="return")

        assert result["success"] is True
        assert result["text"] == ""  # Should be stripped

    @patch("voice_mcp.voice.text_output.time")
    def test_output_text_debouncing(self, mock_time):
        """Test debouncing in typing mode."""
        mock_time.time.side_effect = [100.0, 100.05]  # Within debounce window
        controller = TextOutputController(debounce_delay=0.1)

        # First call
        with patch.object(
            controller, "_type_text_realtime", return_value={"success": True}
        ):
            result1 = controller.output_text("Hello", mode="typing")
            assert result1["success"] is True

        # Second call within debounce window
        result2 = controller.output_text("Hello there", mode="typing")
        assert result2["success"] is True
        assert "Debounced" in result2["message"]

    @patch("voice_mcp.voice.text_output.time")
    def test_output_text_force_update_skips_debounce(self, mock_time):
        """Test that force_update skips debouncing."""
        mock_time.time.side_effect = [100.0, 100.05]  # Within debounce window
        controller = TextOutputController(debounce_delay=0.1)

        with patch.object(
            controller, "_type_text_realtime", return_value={"success": True}
        ) as mock_type:
            # First call
            result1 = controller.output_text("Hello", mode="typing")
            assert result1["success"] is True

            # Second call with force_update=True should not be debounced
            result2 = controller.output_text(
                "Hello there", mode="typing", force_update=True
            )
            assert result2["success"] is True
            assert mock_type.call_count == 2

    @patch("voice_mcp.voice.text_output.time")
    def test_output_text_same_text_skip(self, mock_time):
        """Test skipping output when text is unchanged."""
        mock_time.time.return_value = 100.0
        controller = TextOutputController()
        controller.last_typed_text = "Hello"

        result = controller.output_text("Hello", mode="typing")

        assert result["success"] is True
        assert "unchanged" in result["message"]

    def test_output_text_invalid_mode(self):
        """Test text output with invalid mode."""
        controller = TextOutputController()

        result = controller.output_text("Hello", mode="invalid")

        assert result["success"] is False
        assert "Unknown output mode" in result["error"]

    def test_output_text_exception_handling(self):
        """Test exception handling in output_text."""
        controller = TextOutputController()

        with patch.object(
            controller, "_type_text_realtime", side_effect=Exception("Test error")
        ):
            result = controller.output_text("Hello", mode="typing")

            assert result["success"] is False
            assert "Output error" in result["error"]

    def test_reset(self):
        """Test reset functionality."""
        controller = TextOutputController()
        controller.last_typed_text = "some text"
        controller.last_update_time = 123.45

        controller.reset()

        assert controller.last_typed_text == ""
        assert controller.last_update_time == 0


class TestTextOutputControllerPrivateMethods:
    """Test private methods of TextOutputController."""

    def test_get_keyboard_controller_success(self):
        """Test successful keyboard controller creation."""
        controller = TextOutputController()

        with patch("voice_mcp.voice.text_output._get_keyboard_module") as mock_get_kb:
            mock_keyboard = Mock()
            mock_controller = Mock()
            mock_keyboard.Controller.return_value = mock_controller
            mock_get_kb.return_value = mock_keyboard

            result = controller._get_keyboard_controller()

            assert result == mock_controller
            assert controller._keyboard_controller == mock_controller

    def test_get_keyboard_controller_no_keyboard_module(self):
        """Test keyboard controller when module unavailable."""
        controller = TextOutputController()

        with patch(
            "voice_mcp.voice.text_output._get_keyboard_module", return_value=None
        ):
            result = controller._get_keyboard_controller()

            assert result is None

    def test_get_keyboard_controller_exception(self):
        """Test keyboard controller creation exception."""
        controller = TextOutputController()

        with patch("voice_mcp.voice.text_output._get_keyboard_module") as mock_get_kb:
            mock_keyboard = Mock()
            mock_keyboard.Controller.side_effect = Exception("Controller error")
            mock_get_kb.return_value = mock_keyboard

            result = controller._get_keyboard_controller()

            assert result is None

    def test_get_keyboard_controller_cached(self):
        """Test that keyboard controller is cached."""
        controller = TextOutputController()
        mock_controller = Mock()
        controller._keyboard_controller = mock_controller

        result = controller._get_keyboard_controller()

        assert result == mock_controller

    def test_check_typing_availability_true(self):
        """Test typing availability check when available."""
        controller = TextOutputController()

        with patch.object(controller, "_get_keyboard_controller", return_value=Mock()):
            result = controller._check_typing_availability()
            assert result is True

    def test_check_typing_availability_false(self):
        """Test typing availability check when unavailable."""
        controller = TextOutputController()

        with patch.object(controller, "_get_keyboard_controller", return_value=None):
            result = controller._check_typing_availability()
            assert result is False

    def test_check_clipboard_availability_true(self):
        """Test clipboard availability check when available."""
        controller = TextOutputController()

        with patch("voice_mcp.voice.text_output.pyperclip.paste", return_value="test"):
            result = controller._check_clipboard_availability()
            assert result is True

    def test_check_clipboard_availability_false(self):
        """Test clipboard availability check when unavailable."""
        controller = TextOutputController()

        with patch(
            "voice_mcp.voice.text_output.pyperclip.paste",
            side_effect=Exception("No clipboard"),
        ):
            result = controller._check_clipboard_availability()
            assert result is False

    def test_copy_to_clipboard_success(self):
        """Test successful clipboard operation."""
        controller = TextOutputController()

        with patch("voice_mcp.voice.text_output.pyperclip") as mock_pyperclip:
            with patch.object(
                controller, "_check_clipboard_availability", return_value=True
            ):
                result = controller._copy_to_clipboard("Hello World")

                assert result["success"] is True
                assert result["text"] == "Hello World"
                assert "copied to clipboard" in result["message"]
                mock_pyperclip.copy.assert_called_once_with("Hello World")

    def test_copy_to_clipboard_not_available(self):
        """Test clipboard operation when not available."""
        controller = TextOutputController()

        with patch.object(
            controller, "_check_clipboard_availability", return_value=False
        ):
            result = controller._copy_to_clipboard("Hello")

            assert result["success"] is False
            assert "not available" in result["error"]

    def test_copy_to_clipboard_exception(self):
        """Test clipboard operation with exception."""
        controller = TextOutputController()

        with patch("voice_mcp.voice.text_output.pyperclip") as mock_pyperclip:
            with patch.object(
                controller, "_check_clipboard_availability", return_value=True
            ):
                mock_pyperclip.copy.side_effect = Exception("Clipboard error")

                result = controller._copy_to_clipboard("Hello")

                assert result["success"] is False
                assert "Clipboard error" in result["error"]

    def test_type_text_realtime_not_available(self):
        """Test typing when not available."""
        controller = TextOutputController()

        with patch.object(controller, "_check_typing_availability", return_value=False):
            result = controller._type_text_realtime("Hello")

            assert result["success"] is False
            assert "not available" in result["error"]

    def test_type_text_realtime_no_keyboard_controller(self):
        """Test typing when keyboard controller unavailable."""
        controller = TextOutputController()

        with patch.object(controller, "_check_typing_availability", return_value=True):
            with patch.object(
                controller, "_get_keyboard_controller", return_value=None
            ):
                result = controller._type_text_realtime("Hello")

                assert result["success"] is False
                assert "Failed to get keyboard controller" in result["error"]

    def test_type_text_realtime_no_keyboard_module(self):
        """Test typing when keyboard module unavailable."""
        controller = TextOutputController()
        mock_kb_controller = Mock()

        with patch.object(controller, "_check_typing_availability", return_value=True):
            with patch.object(
                controller, "_get_keyboard_controller", return_value=mock_kb_controller
            ):
                with patch(
                    "voice_mcp.voice.text_output._get_keyboard_module",
                    return_value=None,
                ):
                    result = controller._type_text_realtime("Hello")

                    assert result["success"] is False
                    assert "keyboard module not available" in result["error"]

    def test_type_text_realtime_append_operation(self):
        """Test typing with append operation."""
        controller = TextOutputController()
        controller.last_typed_text = "Hello"

        mock_kb_controller = Mock()
        mock_kb_controller.pressed.return_value.__enter__ = Mock(return_value=None)
        mock_kb_controller.pressed.return_value.__exit__ = Mock(return_value=None)
        mock_keyboard = Mock()
        mock_keyboard.Key = Mock()
        mock_keyboard.Controller = Mock()

        with patch.object(controller, "_check_typing_availability", return_value=True):
            with patch.object(
                controller, "_get_keyboard_controller", return_value=mock_kb_controller
            ):
                with patch(
                    "voice_mcp.voice.text_output._get_keyboard_module",
                    return_value=mock_keyboard,
                ):
                    with patch.object(
                        controller, "_check_clipboard_availability", return_value=True
                    ):
                        with patch(
                            "voice_mcp.voice.text_output.pyperclip"
                        ) as mock_pyperclip:
                            mock_pyperclip.paste.return_value = "original"
                            with patch("time.sleep"):
                                result = controller._type_text_realtime("Hello World")

                                assert result["success"] is True
                                assert "Appending" in result["operation"]
                                assert controller.last_typed_text == "Hello World"

    def test_type_text_realtime_delete_all_operation(self):
        """Test typing with delete all operation."""
        controller = TextOutputController()
        controller.last_typed_text = "Hello"

        mock_kb_controller = Mock()
        mock_keyboard = Mock()
        mock_keyboard.Key = Mock()
        mock_keyboard.Key.backspace = Mock()

        with patch.object(controller, "_check_typing_availability", return_value=True):
            with patch.object(
                controller, "_get_keyboard_controller", return_value=mock_kb_controller
            ):
                with patch(
                    "voice_mcp.voice.text_output._get_keyboard_module",
                    return_value=mock_keyboard,
                ):
                    with patch("time.sleep"):
                        result = controller._type_text_realtime("")

                        assert result["success"] is True
                        assert "Deleting all" in result["operation"]
                        assert (
                            mock_kb_controller.press.call_count == 5
                        )  # 5 characters in "Hello"
                        assert controller.last_typed_text == ""

    def test_type_text_realtime_replace_operation_with_clipboard(self):
        """Test typing with replace operation using clipboard."""
        controller = TextOutputController()
        controller.last_typed_text = "Hello"

        mock_kb_controller = Mock()
        mock_kb_controller.pressed.return_value.__enter__ = Mock(return_value=None)
        mock_kb_controller.pressed.return_value.__exit__ = Mock(return_value=None)
        mock_keyboard = Mock()
        mock_keyboard.Key = Mock()
        mock_keyboard.Key.backspace = Mock()
        mock_keyboard.Key.ctrl = Mock()

        with patch.object(controller, "_check_typing_availability", return_value=True):
            with patch.object(
                controller, "_get_keyboard_controller", return_value=mock_kb_controller
            ):
                with patch(
                    "voice_mcp.voice.text_output._get_keyboard_module",
                    return_value=mock_keyboard,
                ):
                    with patch.object(
                        controller, "_check_clipboard_availability", return_value=True
                    ):
                        with patch(
                            "voice_mcp.voice.text_output.pyperclip"
                        ) as mock_pyperclip:
                            mock_pyperclip.paste.return_value = "original"
                            with patch("time.sleep"):
                                result = controller._type_text_realtime("Goodbye")

                                assert result["success"] is True
                                assert "Replacing" in result["operation"]
                                mock_pyperclip.copy.assert_called_once_with("Goodbye")
                                # Current implementation doesn't restore clipboard

    def test_type_text_realtime_replace_operation_without_clipboard(self):
        """Test typing with replace operation without clipboard."""
        controller = TextOutputController()
        controller.last_typed_text = "Hello"

        mock_kb_controller = Mock()
        mock_keyboard = Mock()
        mock_keyboard.Key = Mock()
        mock_keyboard.Key.backspace = Mock()

        with patch.object(controller, "_check_typing_availability", return_value=True):
            with patch.object(
                controller, "_get_keyboard_controller", return_value=mock_kb_controller
            ):
                with patch(
                    "voice_mcp.voice.text_output._get_keyboard_module",
                    return_value=mock_keyboard,
                ):
                    with patch.object(
                        controller, "_check_clipboard_availability", return_value=False
                    ):
                        with patch("time.sleep"):
                            result = controller._type_text_realtime("Goodbye")

                            assert result["success"] is True
                            mock_kb_controller.type.assert_called_with("Goodbye")

    def test_type_text_realtime_typing_exception(self):
        """Test typing with exception during operation."""
        controller = TextOutputController()

        mock_kb_controller = Mock()
        mock_keyboard = Mock()
        mock_kb_controller.type.side_effect = Exception("Typing error")

        with patch.object(controller, "_check_typing_availability", return_value=True):
            with patch.object(
                controller, "_get_keyboard_controller", return_value=mock_kb_controller
            ):
                with patch(
                    "voice_mcp.voice.text_output._get_keyboard_module",
                    return_value=mock_keyboard,
                ):
                    with patch.object(
                        controller, "_check_clipboard_availability", return_value=False
                    ):
                        result = controller._type_text_realtime("Hello")

                        assert result["success"] is False
                        assert "Typing failed" in result["error"]


class TestGetKeyboardModule:
    """Test the _get_keyboard_module function."""

    def test_get_keyboard_module_success(self):
        """Test successful keyboard module import."""
        mock_keyboard = Mock()

        def mock_import(name, *args, **kwargs):
            if name == "pynput":
                mock_pynput = Mock()
                mock_pynput.keyboard = mock_keyboard
                return mock_pynput
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = _get_keyboard_module()
            assert result == mock_keyboard

    def test_get_keyboard_module_import_error(self):
        """Test keyboard module import error."""
        with patch("voice_mcp.voice.text_output.logger") as mock_logger:
            with patch("builtins.__import__", side_effect=ImportError("No module")):
                result = _get_keyboard_module()
                assert result is None
                mock_logger.warning.assert_called_once()


class TestTextOutputControllerIntegration:
    """Integration tests for TextOutputController."""

    def test_complete_workflow(self):
        """Test complete text output workflow."""
        controller = TextOutputController()

        # Test basic functionality
        assert controller.debounce_delay >= 0
        assert controller.last_typed_text == ""

        # Test reset
        controller.reset()
        assert controller.last_typed_text == ""


class TestTextOutputControllerSessionLifecycle:
    """Test session lifecycle and clipboard restoration functionality."""

    def test_session_initialization(self):
        """Test session state is properly initialized."""
        controller = TextOutputController()

        assert controller._session_active is False
        assert controller._original_clipboard_content is None
        assert controller._clipboard_was_modified is False

    def test_start_session_success(self):
        """Test successful session start with clipboard backup."""
        controller = TextOutputController()

        with (
            patch.object(
                controller, "_check_clipboard_availability", return_value=True
            ),
            patch(
                "voice_mcp.voice.text_output.pyperclip.paste",
                return_value="original content",
            ),
        ):
            result = controller.start_session()

            assert result["success"] is True
            assert result["clipboard_backed_up"] is True
            assert controller._session_active is True
            assert controller._original_clipboard_content == "original content"
            assert controller._clipboard_was_modified is False

    def test_start_session_no_clipboard(self):
        """Test session start when clipboard is not available."""
        controller = TextOutputController()

        with patch.object(
            controller, "_check_clipboard_availability", return_value=False
        ):
            result = controller.start_session()

            assert result["success"] is True
            assert result["clipboard_backed_up"] is False
            assert controller._session_active is True
            assert controller._original_clipboard_content is None

    def test_start_session_clipboard_error(self):
        """Test session start with clipboard access error."""
        controller = TextOutputController()

        with (
            patch.object(
                controller, "_check_clipboard_availability", return_value=True
            ),
            patch(
                "voice_mcp.voice.text_output.pyperclip.paste",
                side_effect=Exception("Clipboard error"),
            ),
        ):
            result = controller.start_session()

            assert result["success"] is True
            assert result["clipboard_backed_up"] is False
            assert controller._session_active is True
            assert controller._original_clipboard_content is None

    def test_start_session_already_active(self):
        """Test starting session when one is already active."""
        controller = TextOutputController()

        with (
            patch.object(
                controller, "_check_clipboard_availability", return_value=True
            ),
            patch(
                "voice_mcp.voice.text_output.pyperclip.paste", return_value="content1"
            ),
            patch.object(controller, "end_session") as mock_end,
        ):
            # Start first session
            controller.start_session()

            # Start second session - should end first
            with patch(
                "voice_mcp.voice.text_output.pyperclip.paste", return_value="content2"
            ):
                controller.start_session()

            mock_end.assert_called_once()
            assert controller._original_clipboard_content == "content2"

    def test_end_session_no_active_session(self):
        """Test ending session when none is active."""
        controller = TextOutputController()

        result = controller.end_session()

        assert result["success"] is True
        assert result["clipboard_restored"] is False
        assert "No active session" in result["message"]

    def test_end_session_with_clipboard_restoration(self):
        """Test ending session with clipboard restoration."""
        controller = TextOutputController()

        # Setup session with clipboard backup
        controller._session_active = True
        controller._original_clipboard_content = "original content"
        controller._clipboard_was_modified = True

        with (
            patch.object(
                controller, "_check_clipboard_availability", return_value=True
            ),
            patch("voice_mcp.voice.text_output.pyperclip.copy") as mock_copy,
            patch.object(controller, "reset") as mock_reset,
        ):
            result = controller.end_session()

            assert result["success"] is True
            assert result["clipboard_restored"] is True
            mock_copy.assert_called_once_with("original content")
            mock_reset.assert_called_once()

            # Verify session state is reset
            assert controller._session_active is False
            assert controller._original_clipboard_content is None
            assert controller._clipboard_was_modified is False

    def test_end_session_no_clipboard_modification(self):
        """Test ending session when clipboard was not modified."""
        controller = TextOutputController()

        # Setup session but no clipboard modification
        controller._session_active = True
        controller._original_clipboard_content = "original content"
        controller._clipboard_was_modified = False

        with (
            patch("voice_mcp.voice.text_output.pyperclip.copy") as mock_copy,
            patch.object(controller, "reset") as mock_reset,
        ):
            result = controller.end_session()

            assert result["success"] is True
            assert result["clipboard_restored"] is False
            mock_copy.assert_not_called()
            mock_reset.assert_called_once()

    def test_end_session_clipboard_restore_error(self):
        """Test ending session with clipboard restoration error."""
        controller = TextOutputController()

        controller._session_active = True
        controller._original_clipboard_content = "original content"
        controller._clipboard_was_modified = True

        with (
            patch.object(
                controller, "_check_clipboard_availability", return_value=True
            ),
            patch(
                "voice_mcp.voice.text_output.pyperclip.copy",
                side_effect=Exception("Restore error"),
            ),
            patch.object(controller, "reset") as mock_reset,
        ):
            result = controller.end_session()

            assert result["success"] is True
            assert result["clipboard_restored"] is False
            mock_reset.assert_called_once()

            # Session state should still be reset despite error
            assert controller._session_active is False

    def test_clipboard_modification_tracking(self):
        """Test that clipboard modifications are properly tracked."""
        controller = TextOutputController()

        # Start session
        controller._session_active = True
        controller._clipboard_was_modified = False

        with (
            patch.object(controller, "_check_typing_availability", return_value=True),
            patch.object(controller, "_get_keyboard_controller") as mock_kb,
            patch.object(
                controller, "_check_clipboard_availability", return_value=True
            ),
            patch("voice_mcp.voice.text_output.pyperclip.copy"),
            patch(
                "voice_mcp.voice.text_output._get_keyboard_module"
            ) as mock_keyboard_module,
        ):
            # Setup mocks with context manager support
            mock_controller = Mock()
            mock_controller.pressed = Mock()
            mock_controller.pressed.return_value.__enter__ = Mock()
            mock_controller.pressed.return_value.__exit__ = Mock()
            mock_controller.press = Mock()
            mock_controller.release = Mock()
            mock_kb.return_value = mock_controller

            mock_keyboard_module.return_value = Mock()
            mock_keyboard_module.return_value.Key = Mock()
            mock_keyboard_module.return_value.Key.ctrl = Mock()

            # Type some text
            result = controller._type_text_realtime("hello")

            assert result["success"] is True
            assert controller._clipboard_was_modified is True

    def test_clipboard_modification_tracking_no_session(self):
        """Test clipboard modification tracking when no session is active."""
        controller = TextOutputController()

        # No active session
        controller._session_active = False
        controller._clipboard_was_modified = False

        with (
            patch.object(controller, "_check_typing_availability", return_value=True),
            patch.object(controller, "_get_keyboard_controller") as mock_kb,
            patch.object(
                controller, "_check_clipboard_availability", return_value=True
            ),
            patch("voice_mcp.voice.text_output.pyperclip.copy"),
            patch(
                "voice_mcp.voice.text_output._get_keyboard_module"
            ) as mock_keyboard_module,
        ):
            # Setup mocks with context manager support
            mock_controller = Mock()
            mock_controller.pressed = Mock()
            mock_controller.pressed.return_value.__enter__ = Mock()
            mock_controller.pressed.return_value.__exit__ = Mock()
            mock_controller.press = Mock()
            mock_controller.release = Mock()
            mock_kb.return_value = mock_controller

            mock_keyboard_module.return_value = Mock()
            mock_keyboard_module.return_value.Key = Mock()
            mock_keyboard_module.return_value.Key.ctrl = Mock()

            # Type some text
            result = controller._type_text_realtime("hello")

            assert result["success"] is True
            # Should not track modification when no session
            assert controller._clipboard_was_modified is False

    def test_session_context_manager_pattern(self):
        """Test session lifecycle using context manager pattern."""
        controller = TextOutputController()

        try:
            # Start session
            with (
                patch.object(
                    controller, "_check_clipboard_availability", return_value=True
                ),
                patch(
                    "voice_mcp.voice.text_output.pyperclip.paste",
                    return_value="original",
                ),
            ):
                start_result = controller.start_session()
                assert start_result["success"] is True
                assert controller._session_active is True

                # Simulate some work that modifies clipboard
                controller._clipboard_was_modified = True

                # Simulate error
                raise Exception("Test error")

        except Exception:
            pass
        finally:
            # Ensure cleanup happens
            with (
                patch.object(
                    controller, "_check_clipboard_availability", return_value=True
                ),
                patch("voice_mcp.voice.text_output.pyperclip.copy") as mock_copy,
            ):
                end_result = controller.end_session()
                assert end_result["success"] is True
                mock_copy.assert_called_once_with("original")
