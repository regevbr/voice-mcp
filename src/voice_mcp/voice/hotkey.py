"""
Hotkey monitoring functionality for voice-mcp with configurable global hotkeys.
"""

import threading
import time
from typing import Optional, Dict, Any, Callable, Set, List
import structlog
from pynput import keyboard
from pynput.keyboard import Key, KeyCode

logger = structlog.get_logger(__name__)


class HotkeyManager:
    """Manages global hotkey monitoring for STT activation."""
    
    def __init__(self, on_hotkey_pressed: Optional[Callable[[], None]] = None):
        """
        Initialize the hotkey manager.
        
        Args:
            on_hotkey_pressed: Callback function to call when hotkey is pressed
        """
        self.on_hotkey_pressed = on_hotkey_pressed
        self._listener: Optional[Any] = None
        self._is_monitoring = False
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Current hotkey configuration
        self._hotkey_name = ""
        self._hotkey_keys: Set[Any] = set()
        self._is_combination = False
        self._pressed_keys: Set[Any] = set()
        
        # Thread safety
        self._lock = threading.RLock()
        
        logger.info(
            "HotkeyManager initialized",
        )
    
    def _parse_hotkey(self, hotkey_name: str) -> Dict[str, Any]:
        """
        Parse hotkey name into keyboard keys.
        
        Args:
            hotkey_name: Name like "menu", "f12", "ctrl+alt+s", etc.
            
        Returns:
            Dictionary with parsed hotkey information
        """

        hotkey_name = hotkey_name.lower().strip()
        
        try:
            # Handle combination keys
            if "+" in hotkey_name:
                parts = [part.strip() for part in hotkey_name.split("+")]
                keys = set()
                
                for part in parts:
                    key = self._parse_single_key(part)
                    if key is None:
                        return {
                            "success": False,
                            "error": f"Unknown key: {part}"
                        }
                    keys.add(key)
                
                return {
                    "success": True,
                    "keys": keys,
                    "is_combination": True,
                    "description": f"Combination: {hotkey_name}"
                }
            
            # Handle single keys
            else:
                key = self._parse_single_key(hotkey_name)
                if key is None:
                    return {
                        "success": False,
                        "error": f"Unknown key: {hotkey_name}"
                    }
                
                return {
                    "success": True,
                    "keys": {key},
                    "is_combination": False,
                    "description": f"Single key: {hotkey_name}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error parsing hotkey '{hotkey_name}': {str(e)}"
            }
    
    def _parse_single_key(self, key_name: str) -> Optional[Any]:
        """
        Parse a single key name into a pynput key.
        
        Args:
            key_name: Single key name like "menu", "f12", "ctrl", etc.
            
        Returns:
            pynput Key or KeyCode, or None if unknown
        """
        key_name = key_name.lower()
        
        # Special keys
        special_keys = {
            "menu": Key.menu,
            "alt": Key.alt_l,
            "alt_l": Key.alt_l,
            "alt_r": Key.alt_r,
            "ctrl": Key.ctrl_l,
            "ctrl_l": Key.ctrl_l,
            "ctrl_r": Key.ctrl_r,
            "shift": Key.shift_l,
            "shift_l": Key.shift_l,
            "shift_r": Key.shift_r,
            "cmd": Key.cmd,
            "win": Key.cmd,
            "windows": Key.cmd,
            "space": Key.space,
            "enter": Key.enter,
            "return": Key.enter,
            "esc": Key.esc,
            "escape": Key.esc,
            "tab": Key.tab,
            "backspace": Key.backspace,
            "delete": Key.delete,
            "insert": Key.insert,
            "home": Key.home,
            "end": Key.end,
            "page_up": Key.page_up,
            "page_down": Key.page_down,
            "up": Key.up,
            "down": Key.down,
            "left": Key.left,
            "right": Key.right,
            "pause": Key.pause,
            "scroll_lock": Key.scroll_lock,
            "caps_lock": Key.caps_lock,
            "num_lock": Key.num_lock,
        }
        
        if key_name in special_keys:
            return special_keys[key_name]
        
        # Function keys
        if key_name.startswith("f") and key_name[1:].isdigit():
            f_number = int(key_name[1:])
            if 1 <= f_number <= 12:
                f_keys = {
                    1: Key.f1, 2: Key.f2, 3: Key.f3, 4: Key.f4,
                    5: Key.f5, 6: Key.f6, 7: Key.f7, 8: Key.f8,
                    9: Key.f9, 10: Key.f10, 11: Key.f11, 12: Key.f12
                }
                return f_keys[f_number]
        
        # Single character keys (a-z, 0-9)
        if len(key_name) == 1:
            if key_name.isalnum():
                return KeyCode.from_char(key_name)
        
        # Unknown key
        return None
    
    def _on_key_press(self, key: Any) -> None:
        """Handle key press events."""
        with self._lock:
            self._pressed_keys.add(key)
            
            # Check if all required keys are pressed
            if self._hotkey_keys and self._hotkey_keys.issubset(self._pressed_keys):
                logger.debug("Hotkey detected", keys=self._hotkey_keys)
                
                # Call the callback in a separate thread to avoid blocking
                if self.on_hotkey_pressed:
                    callback_thread = threading.Thread(
                        target=self.on_hotkey_pressed,
                        daemon=True
                    )
                    callback_thread.start()
    
    def _on_key_release(self, key: Any) -> None:
        """Handle key release events."""
        with self._lock:
            self._pressed_keys.discard(key)
    
    def start_monitoring(self, hotkey_name: str) -> Dict[str, Any]:
        """
        Start hotkey monitoring.
        
        Args:
            hotkey_name: Hotkey to monitor (e.g., "menu", "f12", "ctrl+alt+s")
            
        Returns:
            Dictionary with operation results
        """

        with self._lock:
            if self._is_monitoring:
                return {
                    "success": False,
                    "error": f"Already monitoring hotkey: {self._hotkey_name}"
                }
            
            # Parse the hotkey
            parse_result = self._parse_hotkey(hotkey_name)
            if not parse_result["success"]:
                return parse_result
            
            try:
                # Set up hotkey configuration
                self._hotkey_name = hotkey_name
                self._hotkey_keys = parse_result["keys"]
                self._is_combination = parse_result["is_combination"]
                self._pressed_keys.clear()
                
                # Reset stop event
                self._stop_event.clear()
                
                # Start keyboard listener
                self._listener = keyboard.Listener(
                    on_press=self._on_key_press,
                    on_release=self._on_key_release
                )
                
                # Start listener in background thread
                self._monitoring_thread = threading.Thread(
                    target=self._run_listener,
                    daemon=True
                )
                self._monitoring_thread.start()
                
                # Give the listener a moment to start
                time.sleep(0.1)
                
                self._is_monitoring = True
                
                logger.info(
                    "Hotkey monitoring started",
                    hotkey=hotkey_name,
                    description=parse_result["description"]
                )
                
                return {
                    "success": True,
                    "hotkey": hotkey_name,
                    "description": parse_result["description"],
                    "message": f"Hotkey monitoring started ({parse_result['description']})"
                }
                
            except Exception as e:
                logger.error("Failed to start hotkey monitoring", error=str(e))
                return {
                    "success": False,
                    "error": f"Failed to start monitoring: {str(e)}"
                }
    
    def _run_listener(self) -> None:
        """Run the keyboard listener in a background thread."""
        try:
            if self._listener:
                self._listener.start()
                
                # Keep the listener running until stop is requested
                while not self._stop_event.is_set():
                    time.sleep(0.1)
                
                self._listener.stop()
                
        except Exception as e:
            logger.error("Keyboard listener error", error=str(e))
        finally:
            with self._lock:
                self._is_monitoring = False
                logger.debug("Keyboard listener stopped")
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """
        Stop hotkey monitoring.
        
        Returns:
            Dictionary with operation results
        """
        with self._lock:
            if not self._is_monitoring:
                return {
                    "success": True,
                    "message": "Hotkey monitoring was not active"
                }
            
            try:
                # Signal stop
                self._stop_event.set()
                
                # Stop the listener
                if self._listener:
                    self._listener.stop()
                    self._listener = None
                
                # Wait for monitoring thread to finish
                if self._monitoring_thread and self._monitoring_thread.is_alive():
                    self._monitoring_thread.join(timeout=2.0)
                    if self._monitoring_thread.is_alive():
                        logger.warning("Monitoring thread did not stop gracefully")
                
                self._is_monitoring = False
                self._monitoring_thread = None
                
                # Clear state
                previous_hotkey = self._hotkey_name
                self._hotkey_name = ""
                self._hotkey_keys.clear()
                self._pressed_keys.clear()
                
                logger.info("Hotkey monitoring stopped", previous_hotkey=previous_hotkey)
                
                return {
                    "success": True,
                    "message": f"Hotkey monitoring stopped (was: {previous_hotkey})"
                }
                
            except Exception as e:
                logger.error("Failed to stop hotkey monitoring", error=str(e))
                return {
                    "success": False,
                    "error": f"Failed to stop monitoring: {str(e)}"
                }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current hotkey monitoring status.
        
        Returns:
            Dictionary with current status
        """
        with self._lock:
            return {
                "active": self._is_monitoring,
                "hotkey": self._hotkey_name if self._is_monitoring else None,
                "is_combination": self._is_combination if self._is_monitoring else None,
                "thread_alive": (
                    self._monitoring_thread.is_alive() 
                    if self._monitoring_thread else False
                )
            }
    
    def is_monitoring(self) -> bool:
        """Check if currently monitoring hotkeys."""
        with self._lock:
            return self._is_monitoring
    
    def __del__(self):
        """Cleanup resources when object is destroyed."""
        try:
            self.stop_monitoring()
        except Exception:
            pass  # Ignore cleanup errors