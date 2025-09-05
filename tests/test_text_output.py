"""
Tests for text output functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from voice_mcp.voice.text_output import TextOutputController


class TestTextOutputController:
    """Test suite for TextOutputController class."""
    
    def test_initialization_default(self):
        """Test TextOutputController initialization with defaults."""
        with patch('voice_mcp.voice.text_output.config') as mock_config:
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
    
    @patch('voice_mcp.voice.text_output.PYNPUT_AVAILABLE', True)
    @patch('voice_mcp.voice.text_output.keyboard')
    def test_get_keyboard_controller_success(self, mock_keyboard):
        """Test keyboard controller creation success."""
        mock_kb = Mock()
        mock_keyboard.Controller.return_value = mock_kb
        
        controller = TextOutputController()
        kb = controller._get_keyboard_controller()
        
        assert kb is mock_kb
        assert controller._keyboard_controller is mock_kb
        
        # Second call should return cached instance
        kb2 = controller._get_keyboard_controller()
        assert kb2 is mock_kb
        assert mock_keyboard.Controller.call_count == 1
    
    @patch('voice_mcp.voice.text_output.PYNPUT_AVAILABLE', False)
    def test_get_keyboard_controller_unavailable(self):
        """Test keyboard controller when pynput unavailable."""
        controller = TextOutputController()
        kb = controller._get_keyboard_controller()
        
        assert kb is None
    
    @patch('voice_mcp.voice.text_output.PYNPUT_AVAILABLE', True)
    @patch('voice_mcp.voice.text_output.keyboard')
    def test_get_keyboard_controller_exception(self, mock_keyboard):
        """Test keyboard controller creation exception."""
        mock_keyboard.Controller.side_effect = Exception("Keyboard error")
        
        controller = TextOutputController()
        kb = controller._get_keyboard_controller()
        
        assert kb is None
    
    @patch('voice_mcp.voice.text_output.PYNPUT_AVAILABLE', True)
    def test_check_typing_availability_success(self):
        """Test typing availability check success."""
        controller = TextOutputController()
        
        with patch.object(controller, '_get_keyboard_controller', return_value=Mock()):
            result = controller._check_typing_availability()
            
            assert result is True
    
    @patch('voice_mcp.voice.text_output.PYNPUT_AVAILABLE', False)
    def test_check_typing_availability_no_pynput(self):
        """Test typing availability when pynput unavailable."""
        controller = TextOutputController()
        result = controller._check_typing_availability()
        
        assert result is False
    
    def test_check_typing_availability_no_controller(self):
        """Test typing availability when controller creation fails."""
        controller = TextOutputController()
        
        with patch.object(controller, '_get_keyboard_controller', return_value=None):
            result = controller._check_typing_availability()
            
            assert result is False
    
    @patch('voice_mcp.voice.text_output.PYPERCLIP_AVAILABLE', True)
    @patch('voice_mcp.voice.text_output.pyperclip')
    def test_check_clipboard_availability_success(self, mock_pyperclip):
        """Test clipboard availability check success."""
        mock_pyperclip.paste.return_value = "test"
        
        controller = TextOutputController()
        result = controller._check_clipboard_availability()
        
        assert result is True
        mock_pyperclip.paste.assert_called_once()
    
    @patch('voice_mcp.voice.text_output.PYPERCLIP_AVAILABLE', False)
    def test_check_clipboard_availability_no_pyperclip(self):
        """Test clipboard availability when pyperclip unavailable."""
        controller = TextOutputController()
        result = controller._check_clipboard_availability()
        
        assert result is False
    
    @patch('voice_mcp.voice.text_output.PYPERCLIP_AVAILABLE', True)
    @patch('voice_mcp.voice.text_output.pyperclip')
    def test_check_clipboard_availability_exception(self, mock_pyperclip):
        """Test clipboard availability when exception occurs."""
        mock_pyperclip.paste.side_effect = Exception("Clipboard error")
        
        controller = TextOutputController()
        result = controller._check_clipboard_availability()
        
        assert result is False
    
    def test_get_text_diff_append(self):
        """Test text diff for simple append operation."""
        controller = TextOutputController()
        
        diff = controller.get_text_diff("Hello", "Hello world")
        
        assert diff["type"] == "append"
        assert diff["text"] == " world"
    
    def test_get_text_diff_delete_all(self):
        """Test text diff for delete all operation."""
        controller = TextOutputController()
        
        diff = controller.get_text_diff("Hello world", "")
        
        assert diff["type"] == "delete_all"
        assert diff["chars_to_delete"] == 11
    
    def test_get_text_diff_delete_suffix(self):
        """Test text diff for delete suffix operation."""
        controller = TextOutputController()
        
        diff = controller.get_text_diff("Hello world", "Hello")
        
        assert diff["type"] == "delete_suffix"
        assert diff["chars_to_delete"] == 6  # " world" is 6 characters
    
    def test_get_text_diff_replace_suffix(self):
        """Test text diff for replace suffix operation."""
        controller = TextOutputController()
        
        diff = controller.get_text_diff("Hello world", "Hello universe")
        
        assert diff["type"] == "replace_suffix"
        assert diff["chars_to_delete"] == 5  # " world" is 5 characters
        assert diff["text"] == "universe"
    
    def test_get_text_diff_replace_all(self):
        """Test text diff for replace all operation."""
        controller = TextOutputController()
        
        diff = controller.get_text_diff("Hello", "Goodbye")
        
        assert diff["type"] == "replace_all"
        assert diff["chars_to_delete"] == 5
        assert diff["text"] == "Goodbye"
    
    def test_get_text_diff_empty_old_text(self):
        """Test text diff when old text is empty."""
        controller = TextOutputController()
        
        diff = controller.get_text_diff("", "Hello")
        
        assert diff["type"] == "append"
        assert diff["text"] == "Hello"
    
    def test_output_text_return_mode(self):
        """Test output_text with return mode."""
        controller = TextOutputController()
        
        result = controller.output_text("Hello world", mode="return")
        
        assert result["success"] is True
        assert result["mode"] == "return"
        assert result["text"] == "Hello world"
        assert "returned successfully" in result["message"]
    
    def test_output_text_empty_text(self):
        """Test output_text with empty text."""
        controller = TextOutputController()
        
        result = controller.output_text("", mode="return")
        
        assert result["success"] is True
        assert result["text"] == ""
        assert "No text to output" in result["message"]
    
    def test_output_text_unknown_mode(self):
        """Test output_text with unknown mode."""
        controller = TextOutputController()
        
        result = controller.output_text("Hello", mode="unknown")
        
        assert result["success"] is False
        assert "Unknown output mode" in result["error"]
    
    @patch('voice_mcp.voice.text_output.time.time')
    def test_output_text_debouncing(self, mock_time):
        """Test output_text debouncing in typing mode."""
        mock_time.side_effect = [100.0, 100.05]  # 0.05 seconds apart
        
        controller = TextOutputController(debounce_delay=0.1)
        controller.last_typed_text = "Hello"
        controller.last_update_time = 100.0
        
        with patch.object(controller, '_check_typing_availability', return_value=True):
            result = controller.output_text("Hello world", mode="typing")
            
            assert result["success"] is True
            assert "Debounced" in result["message"]
    
    def test_output_text_unchanged_text_typing(self):
        """Test output_text with unchanged text in typing mode."""
        controller = TextOutputController()
        controller.last_typed_text = "Hello world"
        
        result = controller.output_text("Hello world", mode="typing")
        
        assert result["success"] is True
        assert "unchanged" in result["message"]
    
    def test_output_text_force_update(self):
        """Test output_text with force_update flag."""
        controller = TextOutputController()
        controller.last_typed_text = "Hello world"
        
        with patch.object(controller, '_type_text_realtime') as mock_type:
            mock_type.return_value = {"success": True, "mode": "typing", "text": "Hello world"}
            
            result = controller.output_text("Hello world", mode="typing", force_update=True)
            
            mock_type.assert_called_once_with("Hello world")
    
    def test_output_text_exception(self):
        """Test output_text when exception occurs."""
        controller = TextOutputController()
        
        with patch.object(controller, '_copy_to_clipboard', side_effect=Exception("Copy error")):
            result = controller.output_text("Hello", mode="clipboard")
            
            assert result["success"] is False
            assert "Copy error" in result["error"]
    
    @patch('voice_mcp.voice.text_output.time.time')
    @patch('voice_mcp.voice.text_output.time.sleep')
    def test_type_text_realtime_append(self, mock_sleep, mock_time):
        """Test typing with append operation."""
        controller = TextOutputController()
        controller.last_typed_text = "Hello"
        
        # Create mock keyboard controller with all necessary attributes
        mock_kb = Mock()
        
        # Mock the pressed method to return a context manager
        mock_context_manager = Mock()
        mock_context_manager.__enter__ = Mock(return_value=mock_context_manager)
        mock_context_manager.__exit__ = Mock(return_value=None)
        mock_kb.pressed = Mock(return_value=mock_context_manager)
        
        mock_kb.press = Mock()
        mock_kb.release = Mock()
        mock_kb.type = Mock()
        
        with patch.object(controller, '_check_typing_availability', return_value=True), \
             patch.object(controller, '_get_keyboard_controller', return_value=mock_kb), \
             patch.object(controller, '_check_clipboard_availability', return_value=True), \
             patch('voice_mcp.voice.text_output.pyperclip') as mock_pyperclip, \
             patch('voice_mcp.voice.text_output.keyboard') as mock_keyboard:
            
            # Mock keyboard.Key
            mock_keyboard.Key = Mock()
            mock_keyboard.Key.ctrl = Mock()
            
            mock_pyperclip.paste.return_value = "original"
            
            result = controller._type_text_realtime("Hello world")
            
            assert result["success"] is True
            assert result["mode"] == "typing"
            assert "Appending" in result["operation"]
            
            # Verify clipboard operations
            mock_pyperclip.copy.assert_any_call(" world")
            mock_pyperclip.copy.assert_any_call("original")
    
    def test_type_text_realtime_not_available(self):
        """Test typing when typing not available."""
        controller = TextOutputController()
        
        with patch.object(controller, '_check_typing_availability', return_value=False):
            result = controller._type_text_realtime("Hello")
            
            assert result["success"] is False
            assert "not available" in result["error"]
    
    def test_type_text_realtime_no_controller(self):
        """Test typing when keyboard controller unavailable."""
        controller = TextOutputController()
        
        with patch.object(controller, '_check_typing_availability', return_value=True), \
             patch.object(controller, '_get_keyboard_controller', return_value=None):
            
            result = controller._type_text_realtime("Hello")
            
            assert result["success"] is False
            assert "Failed to get keyboard controller" in result["error"]
    
    @patch('voice_mcp.voice.text_output.time.sleep')
    def test_type_text_realtime_delete_all(self, mock_sleep):
        """Test typing with delete all operation."""
        controller = TextOutputController()
        controller.last_typed_text = "Hello world"
        
        # Create mock keyboard controller with all necessary attributes
        mock_kb = Mock()
        
        # Mock the pressed method to return a context manager
        mock_context_manager = Mock()
        mock_context_manager.__enter__ = Mock(return_value=mock_context_manager)
        mock_context_manager.__exit__ = Mock(return_value=None)
        mock_kb.pressed = Mock(return_value=mock_context_manager)
        
        mock_kb.press = Mock()
        mock_kb.release = Mock()
        mock_kb.type = Mock()
        
        with patch.object(controller, '_check_typing_availability', return_value=True), \
             patch.object(controller, '_get_keyboard_controller', return_value=mock_kb), \
             patch.object(controller, 'get_text_diff') as mock_diff, \
             patch('voice_mcp.voice.text_output.keyboard') as mock_keyboard:
            
            # Mock keyboard.Key
            mock_keyboard.Key = Mock()
            mock_keyboard.Key.backspace = Mock()
            
            mock_diff.return_value = {"type": "delete_all", "chars_to_delete": 11}
            
            result = controller._type_text_realtime("")
            
            assert result["success"] is True
            assert "Deleting all 11 characters" in result["operation"]
            
            # Verify backspace was pressed 11 times
            assert mock_kb.press.call_count == 11
            assert mock_kb.release.call_count == 11
    
    def test_type_text_realtime_fallback_typing(self):
        """Test typing fallback when clipboard unavailable."""
        controller = TextOutputController()
        controller.last_typed_text = ""
        
        # Create mock keyboard controller with all necessary attributes
        mock_kb = Mock()
        
        # Mock the pressed method to return a context manager
        mock_context_manager = Mock()
        mock_context_manager.__enter__ = Mock(return_value=mock_context_manager)
        mock_context_manager.__exit__ = Mock(return_value=None)
        mock_kb.pressed = Mock(return_value=mock_context_manager)
        
        mock_kb.press = Mock()
        mock_kb.release = Mock()
        mock_kb.type = Mock()
        
        with patch.object(controller, '_check_typing_availability', return_value=True), \
             patch.object(controller, '_get_keyboard_controller', return_value=mock_kb), \
             patch.object(controller, '_check_clipboard_availability', return_value=False), \
             patch.object(controller, 'get_text_diff') as mock_diff:
            
            mock_diff.return_value = {"type": "append", "text": "Hello"}
            
            result = controller._type_text_realtime("Hello")
            
            assert result["success"] is True
            mock_kb.type.assert_called_once_with("Hello")
    
    def test_type_text_realtime_exception(self):
        """Test typing when exception occurs."""
        controller = TextOutputController()
        
        with patch.object(controller, '_check_typing_availability', return_value=True), \
             patch.object(controller, '_get_keyboard_controller', return_value=None):
            
            result = controller._type_text_realtime("Hello")
            
            assert result["success"] is False
            assert "Failed to get keyboard controller" in result["error"]
    
    @patch('voice_mcp.voice.text_output.pyperclip')
    def test_copy_to_clipboard_success(self, mock_pyperclip):
        """Test successful clipboard copy."""
        controller = TextOutputController()
        
        with patch.object(controller, '_check_clipboard_availability', return_value=True):
            result = controller._copy_to_clipboard("Hello world")
            
            assert result["success"] is True
            assert result["mode"] == "clipboard"
            assert result["text"] == "Hello world"
            assert "copied to clipboard" in result["message"]
            mock_pyperclip.copy.assert_called_once_with("Hello world")
    
    def test_copy_to_clipboard_not_available(self):
        """Test clipboard copy when unavailable."""
        controller = TextOutputController()
        
        with patch.object(controller, '_check_clipboard_availability', return_value=False):
            result = controller._copy_to_clipboard("Hello")
            
            assert result["success"] is False
            assert "not available" in result["error"]
    
    @patch('voice_mcp.voice.text_output.pyperclip')
    def test_copy_to_clipboard_exception(self, mock_pyperclip):
        """Test clipboard copy when exception occurs."""
        controller = TextOutputController()
        mock_pyperclip.copy.side_effect = Exception("Clipboard error")
        
        with patch.object(controller, '_check_clipboard_availability', return_value=True):
            result = controller._copy_to_clipboard("Hello")
            
            assert result["success"] is False
            assert "Clipboard error" in result["error"]
    
    def test_reset(self):
        """Test reset functionality."""
        controller = TextOutputController()
        controller.last_typed_text = "Hello"
        controller.last_update_time = 100.0
        
        controller.reset()
        
        assert controller.last_typed_text == ""
        assert controller.last_update_time == 0
    
    def test_get_status(self):
        """Test get_status method."""
        controller = TextOutputController(debounce_delay=0.3)
        controller.last_typed_text = "Hello world"
        
        with patch.object(controller, '_check_typing_availability', return_value=True), \
             patch.object(controller, '_check_clipboard_availability', return_value=False), \
             patch('voice_mcp.voice.text_output.PYNPUT_AVAILABLE', True), \
             patch('voice_mcp.voice.text_output.PYPERCLIP_AVAILABLE', False):
            
            status = controller.get_status()
            
            assert status["typing_available"] is True
            assert status["clipboard_available"] is False
            assert status["debounce_delay"] == 0.3
            assert status["last_text_length"] == 11
            assert status["pynput_available"] is True
            assert status["pyperclip_available"] is False


class TestTextOutputControllerIntegration:
    """Integration tests for TextOutputController with comprehensive scenarios."""
    
    @patch('voice_mcp.voice.text_output.time.sleep')
    @patch('voice_mcp.voice.text_output.pyperclip')
    @patch('voice_mcp.voice.text_output.PYNPUT_AVAILABLE', True)
    @patch('voice_mcp.voice.text_output.PYPERCLIP_AVAILABLE', True)
    def test_complete_typing_workflow(self, mock_pyperclip, mock_sleep):
        """Test complete typing workflow with real-time corrections."""
        controller = TextOutputController()
        
        # Create mock keyboard controller with all necessary attributes
        mock_kb = Mock()
        
        # Mock the pressed method to return a context manager
        mock_context_manager = Mock()
        mock_context_manager.__enter__ = Mock(return_value=mock_context_manager)
        mock_context_manager.__exit__ = Mock(return_value=None)
        mock_kb.pressed = Mock(return_value=mock_context_manager)
        
        mock_kb.press = Mock() 
        mock_kb.release = Mock()
        mock_kb.type = Mock()
        
        with patch.object(controller, '_get_keyboard_controller', return_value=mock_kb), \
             patch('voice_mcp.voice.text_output.keyboard') as mock_keyboard:
            
            # Mock keyboard.Key
            mock_keyboard.Key = Mock()
            mock_keyboard.Key.ctrl = Mock()
            
            mock_pyperclip.paste.return_value = "original_clipboard"
            
            # First output - simple append
            result1 = controller.output_text("Hello", mode="typing")
            assert result1["success"] is True
            
            # Second output - append more text
            result2 = controller.output_text("Hello world", mode="typing", force_update=True)
            assert result2["success"] is True
            
            # Verify clipboard was used for pasting
            mock_pyperclip.copy.assert_called()
    
    @patch('voice_mcp.voice.text_output.PYNPUT_AVAILABLE', False)
    @patch('voice_mcp.voice.text_output.PYPERCLIP_AVAILABLE', False)
    def test_graceful_degradation_no_dependencies(self):
        """Test graceful behavior when all dependencies are missing."""
        controller = TextOutputController()
        
        # Test typing mode - should fail gracefully
        result1 = controller.output_text("Hello", mode="typing")
        assert result1["success"] is False
        assert "not available" in result1["error"]
        
        # Test clipboard mode - should fail gracefully
        result2 = controller.output_text("Hello", mode="clipboard")
        assert result2["success"] is False
        assert "not available" in result2["error"]
        
        # Test return mode - should always work
        result3 = controller.output_text("Hello", mode="return")
        assert result3["success"] is True
        
        # Test status
        status = controller.get_status()
        assert status["typing_available"] is False
        assert status["clipboard_available"] is False
        assert status["pynput_available"] is False
        assert status["pyperclip_available"] is False
    
    @pytest.mark.parametrize("old_text,new_text,expected_type", [
        ("", "Hello", "append"),
        ("Hello", "Hello world", "append"),
        ("Hello world", "Hello", "delete_suffix"),
        ("Hello world", "", "delete_all"),
        ("Hello", "Goodbye", "replace_all"),
        ("Hello world", "Hello universe", "replace_suffix"),
    ])
    def test_text_diff_scenarios(self, old_text, new_text, expected_type):
        """Test various text diff scenarios."""
        controller = TextOutputController()
        
        diff = controller.get_text_diff(old_text, new_text)
        
        assert diff["type"] == expected_type
        
        if expected_type in ["delete_all", "delete_suffix", "replace_suffix", "replace_all"]:
            assert "chars_to_delete" in diff
            assert diff["chars_to_delete"] > 0
        
        if expected_type in ["append", "replace_suffix", "replace_all"]:
            assert "text" in diff
            assert len(diff["text"]) > 0
    
    @pytest.mark.parametrize("mode,should_succeed", [
        ("return", True),
        ("typing", False),  # Will fail due to mocked unavailability
        ("clipboard", False),  # Will fail due to mocked unavailability
        ("invalid", False),
    ])
    def test_output_modes(self, mode, should_succeed):
        """Test different output modes."""
        controller = TextOutputController()
        
        with patch.object(controller, '_check_typing_availability', return_value=False), \
             patch.object(controller, '_check_clipboard_availability', return_value=False):
            
            result = controller.output_text("Test text", mode=mode)
            
            assert result["success"] == should_succeed
            assert result["mode"] == mode