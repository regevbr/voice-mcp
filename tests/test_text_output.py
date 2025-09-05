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
        assert result["chars_to_delete"] == 6
        assert result["text"] == " there"

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
                                mock_pyperclip.copy.assert_any_call("Goodbye")
                                mock_pyperclip.copy.assert_any_call(
                                    "original"
                                )  # Restore

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
        with patch(
            "voice_mcp.voice.text_output.keyboard", create=True
        ) as mock_keyboard:
            result = _get_keyboard_module()
            assert result == mock_keyboard

    def test_get_keyboard_module_import_error(self):
        """Test keyboard module import error."""
        with patch("builtins.__import__", side_effect=ImportError("No module")):
            result = _get_keyboard_module()
            assert result is None


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
