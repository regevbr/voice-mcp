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
    
    def test_get_text_diff(self):
        """Test text difference calculation."""
        controller = TextOutputController()
        
        # Test no changes
        result = controller.get_text_diff("hello", "hello")
        # When text is identical, it might return no-op or similar
        assert "type" in result
        
        # Test append
        result = controller.get_text_diff("hello", "hello world")
        assert result["type"] == "append"
        assert result["text"] == " world"
        
        # Test replace (when difference is significant)
        result = controller.get_text_diff("hello", "goodbye")
        assert result["type"] == "replace_all"
        assert result["text"] == "goodbye"
    
    @patch('voice_mcp.voice.text_output.time')
    def test_output_text_clipboard_mode(self, mock_time):
        """Test text output in clipboard mode."""
        mock_time.time.return_value = 100.0
        controller = TextOutputController()
        
        with patch.object(controller, '_copy_to_clipboard', return_value={"success": True}) as mock_copy:
            result = controller.output_text("Hello World", mode="clipboard")
            
            assert result["success"] is True
            mock_copy.assert_called_once_with("Hello World")
    
    @patch('voice_mcp.voice.text_output.time')  
    def test_output_text_typing_mode(self, mock_time):
        """Test text output in typing mode."""
        mock_time.time.return_value = 100.0
        controller = TextOutputController()
        
        with patch.object(controller, '_type_text_realtime', return_value={"success": True}) as mock_type:
            result = controller.output_text("Hello", mode="typing")
            
            assert result["success"] is True
            mock_type.assert_called_once_with("Hello")
    
    def test_output_text_invalid_mode(self):
        """Test text output with invalid mode."""
        controller = TextOutputController()
        
        result = controller.output_text("Hello", mode="invalid")
        
        assert result["success"] is False
        assert "Unknown output mode" in result["error"]
    
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
    
    def test_copy_to_clipboard_success(self):
        """Test successful clipboard operation."""
        controller = TextOutputController()
        
        with patch('voice_mcp.voice.text_output.pyperclip') as mock_pyperclip:
            result = controller._copy_to_clipboard("Hello World")
            
            assert result["success"] is True
            assert result["text"] == "Hello World"
            mock_pyperclip.copy.assert_called_once_with("Hello World")
    
    def test_copy_to_clipboard_exception(self):
        """Test clipboard operation with exception."""
        controller = TextOutputController()
        
        with patch('voice_mcp.voice.text_output.pyperclip') as mock_pyperclip:
            mock_pyperclip.copy.side_effect = Exception("Clipboard error")
            
            result = controller._copy_to_clipboard("Hello")
            
            assert result["success"] is False
            assert "Clipboard error" in result["error"]
    
    def test_type_text_realtime_no_keyboard(self):
        """Test typing when keyboard controller unavailable."""
        controller = TextOutputController()
        controller._keyboard_controller = None
        
        with patch.object(controller, '_get_keyboard_controller', return_value=None):
            result = controller._type_text_realtime("Hello")
            
            assert result["success"] is False
            assert "Typing functionality not available" in result["error"]


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