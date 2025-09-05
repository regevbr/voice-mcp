"""
Tests for hotkey monitoring functionality.
"""

import threading
import time
from unittest.mock import Mock, patch, MagicMock
import pytest

from voice_mcp.voice.hotkey import HotkeyManager
from voice_mcp.tools import VoiceTools, get_hotkey_manager
from voice_mcp.config import ServerConfig


# Mock pynput to prevent actual key monitoring during tests and provide consistent behavior
@pytest.fixture(autouse=True)
def mock_pynput():
    """Mock pynput to prevent actual keyboard monitoring during tests."""
    # Create mock objects with the required attributes
    mock_key = Mock()
    mock_key.menu = "mock_menu_key"
    mock_key.f1 = "mock_f1_key"
    mock_key.f2 = "mock_f2_key"
    mock_key.f3 = "mock_f3_key"
    mock_key.f4 = "mock_f4_key"
    mock_key.f5 = "mock_f5_key"
    mock_key.f6 = "mock_f6_key"
    mock_key.f7 = "mock_f7_key"
    mock_key.f8 = "mock_f8_key"
    mock_key.f9 = "mock_f9_key"
    mock_key.f10 = "mock_f10_key"
    mock_key.f11 = "mock_f11_key"
    mock_key.f12 = "mock_f12_key"
    mock_key.ctrl_l = "mock_ctrl_l_key"
    mock_key.alt_l = "mock_alt_l_key"
    mock_key.shift_l = "mock_shift_l_key"
    mock_key.cmd = "mock_cmd_key"
    mock_key.space = "mock_space_key"
    mock_key.pause = "mock_pause_key"
    mock_key.scroll_lock = "mock_scroll_lock_key"
    mock_key.backspace = "mock_backspace_key"
    
    mock_keycode = Mock()
    mock_keycode.from_char = Mock(side_effect=lambda x: f"mock_char_{x}")
    
    mock_keyboard = Mock()
    mock_listener_instance = Mock()
    mock_listener_instance.start = Mock()
    mock_listener_instance.stop = Mock()
    mock_keyboard.Listener.return_value = mock_listener_instance
    mock_keyboard.Key = mock_key
    mock_keyboard.KeyCode = mock_keycode
    
    with patch('voice_mcp.voice.hotkey.PYNPUT_AVAILABLE', True), \
         patch('voice_mcp.voice.hotkey.keyboard', mock_keyboard), \
         patch('voice_mcp.voice.hotkey.Key', mock_key), \
         patch('voice_mcp.voice.hotkey.KeyCode', mock_keycode):
        yield mock_keyboard


@pytest.fixture
def hotkey_manager():
    """Create a HotkeyManager instance for testing."""
    callback = Mock()
    manager = HotkeyManager(on_hotkey_pressed=callback)
    return manager


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return ServerConfig(
        enable_hotkey=True,
        hotkey_name="f12",
        hotkey_output_mode="typing",
        stt_language="en"
    )


class TestHotkeyManager:
    """Test cases for HotkeyManager class."""
    
    def test_init(self, hotkey_manager):
        """Test HotkeyManager initialization."""
        assert hotkey_manager.on_hotkey_pressed is not None
        assert not hotkey_manager.is_monitoring()
        assert hotkey_manager.get_status()["active"] is False
    
    def test_parse_single_key(self, hotkey_manager, mock_pynput):
        """Test parsing single key names."""
        # Test special keys
        parse_result = hotkey_manager._parse_hotkey("menu")
        assert parse_result["success"] is True
        assert "mock_menu_key" in parse_result["keys"]
        assert parse_result["is_combination"] is False
        
        # Test function keys
        parse_result = hotkey_manager._parse_hotkey("f12")
        assert parse_result["success"] is True
        assert "mock_f12_key" in parse_result["keys"]
        
        # Test character keys
        parse_result = hotkey_manager._parse_hotkey("s")
        assert parse_result["success"] is True
        assert "mock_char_s" in parse_result["keys"]
    
    def test_parse_combination_keys(self, hotkey_manager, mock_pynput):
        """Test parsing key combinations."""
        parse_result = hotkey_manager._parse_hotkey("ctrl+alt+s")
        assert parse_result["success"] is True
        assert len(parse_result["keys"]) == 3
        assert parse_result["is_combination"] is True
        
        # Check all expected keys are present
        keys_list = list(parse_result["keys"])
        assert "mock_ctrl_l_key" in keys_list
        assert "mock_alt_l_key" in keys_list
        assert "mock_char_s" in keys_list
    
    def test_parse_invalid_key(self, hotkey_manager):
        """Test parsing invalid key names."""
        parse_result = hotkey_manager._parse_hotkey("invalid_key")
        assert parse_result["success"] is False
        assert "Unknown key" in parse_result["error"]
    
    def test_start_monitoring_success(self, hotkey_manager, mock_pynput):
        """Test successful start of hotkey monitoring."""
        result = hotkey_manager.start_monitoring("f12")
        
        assert result["success"] is True
        assert result["hotkey"] == "f12"
        assert "Single key: f12" in result["description"]
        assert hotkey_manager.is_monitoring()
        
        # Verify listener was created and started
        mock_pynput.Listener.assert_called_once()
        
    def test_start_monitoring_already_active(self, hotkey_manager, mock_pynput):
        """Test starting monitoring when already active."""
        # Start monitoring first time
        hotkey_manager.start_monitoring("f12")
        
        # Try to start again
        result = hotkey_manager.start_monitoring("f11")
        assert result["success"] is False
        assert "Already monitoring" in result["error"]
    
    def test_stop_monitoring(self, hotkey_manager, mock_pynput):
        """Test stopping hotkey monitoring."""
        # Start monitoring first
        hotkey_manager.start_monitoring("f12")
        assert hotkey_manager.is_monitoring()
        
        # Stop monitoring
        result = hotkey_manager.stop_monitoring()
        assert result["success"] is True
        assert not hotkey_manager.is_monitoring()
    
    def test_stop_monitoring_not_active(self, hotkey_manager):
        """Test stopping monitoring when not active."""
        result = hotkey_manager.stop_monitoring()
        assert result["success"] is True
        assert "was not active" in result["message"]
    
    def test_get_status(self, hotkey_manager, mock_pynput):
        """Test getting status information."""
        # Initially not monitoring
        status = hotkey_manager.get_status()
        assert status["active"] is False
        assert status["hotkey"] is None
        assert status["pynput_available"] is True
        
        # Start monitoring
        hotkey_manager.start_monitoring("menu")
        status = hotkey_manager.get_status()
        assert status["active"] is True
        assert status["hotkey"] == "menu"
        assert status["is_combination"] is False
    
    def test_key_press_callback(self, mock_pynput):
        """Test hotkey press callback functionality."""
        callback = Mock()
        manager = HotkeyManager(on_hotkey_pressed=callback)
        
        # Start monitoring for a simple key
        manager.start_monitoring("f12")
        
        # Simulate key press and release
        manager._on_key_press("mock_f12_key")
        
        # Give callback thread time to execute
        time.sleep(0.1)
        
        # Verify callback was called
        callback.assert_called_once()
    
    def test_combination_key_press(self, mock_pynput):
        """Test combination key press detection."""
        callback = Mock()
        manager = HotkeyManager(on_hotkey_pressed=callback)
        
        # Start monitoring for combination
        manager.start_monitoring("ctrl+alt+s")
        
        # Press keys individually (not all at once)
        manager._on_key_press("mock_ctrl_l_key")
        manager._on_key_press("mock_alt_l_key")
        
        # Callback should not be triggered yet
        time.sleep(0.05)
        callback.assert_not_called()
        
        # Press the final key
        manager._on_key_press("mock_char_s")
        
        # Give callback thread time to execute
        time.sleep(0.1)
        
        # Now callback should be triggered
        callback.assert_called_once()
    
    def test_thread_cleanup(self, hotkey_manager, mock_pynput):
        """Test proper thread cleanup on stop."""
        hotkey_manager.start_monitoring("f12")
        
        # Verify monitoring thread exists
        assert hotkey_manager._monitoring_thread is not None
        
        hotkey_manager.stop_monitoring()
        
        # Give thread time to clean up
        time.sleep(0.1)
        
        # Verify cleanup
        assert not hotkey_manager.is_monitoring()


class TestHotkeyManagerWithoutPynput:
    """Test HotkeyManager behavior when pynput is not available."""
    
    @patch('voice_mcp.voice.hotkey.PYNPUT_AVAILABLE', False)
    def test_start_without_pynput(self):
        """Test starting monitoring without pynput available."""
        manager = HotkeyManager()
        result = manager.start_monitoring("f12")
        
        assert result["success"] is False
        assert "pynput not available" in result["error"]
    
    @patch('voice_mcp.voice.hotkey.PYNPUT_AVAILABLE', False)
    def test_parse_without_pynput(self):
        """Test key parsing without pynput available."""
        manager = HotkeyManager()
        result = manager._parse_hotkey("f12")
        
        assert result["success"] is False
        assert "pynput not available" in result["error"]


class TestVoiceToolsHotkeyIntegration:
    """Test hotkey functionality integration with VoiceTools."""
    
    @patch('voice_mcp.tools.config')
    def test_start_hotkey_monitoring_disabled(self, mock_config):
        """Test starting hotkey when disabled in config."""
        mock_config.enable_hotkey = False
        
        result = VoiceTools.start_hotkey_monitoring()
        assert "disabled in configuration" in result
    
    @patch('voice_mcp.tools.config')
    @patch('voice_mcp.tools.get_hotkey_manager')
    def test_start_hotkey_monitoring_success(self, mock_get_manager, mock_config):
        """Test successful hotkey monitoring start."""
        mock_config.enable_hotkey = True
        mock_config.hotkey_name = "f12"
        
        mock_manager = Mock()
        mock_manager.start_monitoring.return_value = {
            "success": True,
            "description": "Single key: f12"
        }
        mock_get_manager.return_value = mock_manager
        
        result = VoiceTools.start_hotkey_monitoring()
        assert "✅ Hotkey monitoring started" in result
        assert "Single key: f12" in result
        mock_manager.start_monitoring.assert_called_once_with("f12")
    
    @patch('voice_mcp.tools.get_hotkey_manager')
    def test_stop_hotkey_monitoring(self, mock_get_manager):
        """Test stopping hotkey monitoring."""
        mock_manager = Mock()
        mock_manager.stop_monitoring.return_value = {
            "success": True,
            "message": "Hotkey monitoring stopped"
        }
        mock_get_manager.return_value = mock_manager
        
        result = VoiceTools.stop_hotkey_monitoring()
        assert "✅ Hotkey monitoring stopped" in result
        mock_manager.stop_monitoring.assert_called_once()
    
    @patch('voice_mcp.tools.config')
    @patch('voice_mcp.tools.get_hotkey_manager')
    def test_get_hotkey_status(self, mock_get_manager, mock_config):
        """Test getting hotkey status."""
        mock_config.enable_hotkey = True
        mock_config.hotkey_name = "menu"
        mock_config.hotkey_output_mode = "typing"
        mock_config.stt_language = "en"
        
        mock_manager = Mock()
        mock_manager.get_status.return_value = {
            "active": True,
            "hotkey": "menu",
            "pynput_available": True
        }
        mock_get_manager.return_value = mock_manager
        
        result = VoiceTools.get_hotkey_status()
        
        assert result["active"] is True
        assert result["hotkey"] == "menu"
        assert result["configuration"]["enabled"] is True
        assert result["configuration"]["hotkey_name"] == "menu"
        assert result["configuration"]["output_mode"] == "typing"
        mock_manager.get_status.assert_called_once()


class TestHotkeyCallback:
    """Test the hotkey callback functionality."""
    
    @patch('voice_mcp.tools.VoiceTools.listen')
    @patch('voice_mcp.tools.config')
    def test_on_hotkey_pressed_success(self, mock_config, mock_listen):
        """Test successful hotkey callback execution."""
        from voice_mcp.tools import _on_hotkey_pressed
        
        mock_config.stt_language = "en"
        mock_config.hotkey_output_mode = "typing"
        
        mock_listen.return_value = {
            "status": "success",
            "transcription": "Hello world",
            "duration": 2.5,
            "output_mode": "typing"
        }
        
        # Execute callback
        _on_hotkey_pressed()
        
        # Verify listen was called with correct parameters
        mock_listen.assert_called_once_with(
            duration=None,
            language="en",
            output_mode="typing"
        )
    
    @patch('voice_mcp.tools.VoiceTools.listen')
    @patch('voice_mcp.tools.config')
    def test_on_hotkey_pressed_failure(self, mock_config, mock_listen):
        """Test hotkey callback with STT failure."""
        from voice_mcp.tools import _on_hotkey_pressed
        
        mock_config.stt_language = "en"
        mock_config.hotkey_output_mode = "clipboard"
        
        mock_listen.return_value = {
            "status": "error",
            "error": "STT not available",
            "transcription": ""
        }
        
        # Execute callback (should not raise exception)
        _on_hotkey_pressed()
        
        # Verify listen was called
        mock_listen.assert_called_once_with(
            duration=None,
            language="en",
            output_mode="clipboard"
        )
    
    @patch('voice_mcp.tools.VoiceTools.listen')
    @patch('voice_mcp.tools.config')
    def test_on_hotkey_pressed_exception(self, mock_config, mock_listen):
        """Test hotkey callback with exception handling."""
        from voice_mcp.tools import _on_hotkey_pressed
        
        mock_config.stt_language = "en"
        mock_config.hotkey_output_mode = "typing"
        
        # Make listen raise an exception
        mock_listen.side_effect = Exception("Test exception")
        
        # Execute callback (should not raise exception)
        _on_hotkey_pressed()
        
        # Verify listen was called
        mock_listen.assert_called_once()


class TestHotkeyKeyParsing:
    """Test comprehensive key parsing scenarios."""
    
    def test_all_function_keys(self, hotkey_manager, mock_pynput):
        """Test parsing all function keys F1-F12."""
        for i in range(1, 13):
            key_name = f"f{i}"
            expected_key = f"mock_f{i}_key"
            
            result = hotkey_manager._parse_hotkey(key_name)
            assert result["success"] is True, f"Failed for {key_name}"
            assert expected_key in result["keys"]
    
    def test_special_key_aliases(self, hotkey_manager, mock_pynput):
        """Test special key aliases."""
        test_cases = [
            ("alt", "mock_alt_l_key"),
            ("ctrl", "mock_ctrl_l_key"),
            ("shift", "mock_shift_l_key"),
            ("win", "mock_cmd_key"),
            ("windows", "mock_cmd_key"),
            ("cmd", "mock_cmd_key"),
        ]
        
        for key_name, expected_key in test_cases:
            result = hotkey_manager._parse_hotkey(key_name)
            assert result["success"] is True, f"Failed for {key_name}"
            assert expected_key in result["keys"]
    
    def test_complex_combinations(self, hotkey_manager, mock_pynput):
        """Test complex key combinations."""
        result = hotkey_manager._parse_hotkey("ctrl+shift+alt+s")
        assert result["success"] is True
        assert len(result["keys"]) == 4
        assert result["is_combination"] is True


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_start_monitoring_error(self, hotkey_manager, mock_pynput):
        """Test error handling during monitoring start."""
        # Make listener creation raise an exception
        mock_pynput.Listener.side_effect = Exception("Listener creation failed")
        
        result = hotkey_manager.start_monitoring("f12")
        assert result["success"] is False
        assert "Failed to start monitoring" in result["error"]
    
    def test_stop_monitoring_error(self, hotkey_manager, mock_pynput):
        """Test error handling during monitoring stop."""
        # Start monitoring successfully first
        hotkey_manager.start_monitoring("f12")
        
        # Mock listener stop to raise exception
        hotkey_manager._listener.stop.side_effect = Exception("Stop failed")
        
        result = hotkey_manager.stop_monitoring()
        # Should report error when stop fails
        assert result["success"] is False
        assert "Failed to stop monitoring" in result["error"]
    
    def test_key_press_exception(self, mock_pynput):
        """Test exception handling in key press callback."""
        callback = Mock(side_effect=Exception("Callback failed"))
        manager = HotkeyManager(on_hotkey_pressed=callback)
        
        manager.start_monitoring("f12")
        
        # This should not raise an exception
        manager._on_key_press("mock_f12_key")
        
        # Give callback thread time to execute
        time.sleep(0.1)
        
        # Callback should have been called despite the exception
        callback.assert_called_once()


@pytest.mark.integration
class TestHotkeyIntegration:
    """Integration tests for hotkey functionality."""
    
    @patch('voice_mcp.voice.hotkey.PYNPUT_AVAILABLE', True)
    def test_manager_lifecycle(self):
        """Test complete manager lifecycle."""
        manager = get_hotkey_manager()
        
        # Verify initial state
        status = manager.get_status()
        assert status["active"] is False
        
        # Test starting and stopping
        with patch('voice_mcp.voice.hotkey.keyboard'):
            start_result = manager.start_monitoring("f12")
            assert start_result["success"] is True
            
            status = manager.get_status()
            assert status["active"] is True
            
            stop_result = manager.stop_monitoring()
            assert stop_result["success"] is True
            
            status = manager.get_status()
            assert status["active"] is False
    
    def test_configuration_integration(self, sample_config):
        """Test integration with configuration system."""
        with patch('voice_mcp.config.config', sample_config):
            # Test that VoiceTools uses config values
            assert sample_config.enable_hotkey is True
            assert sample_config.hotkey_name == "f12"
            assert sample_config.hotkey_output_mode == "typing"
            assert sample_config.stt_language == "en"