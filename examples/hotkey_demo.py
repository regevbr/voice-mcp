#!/usr/bin/env python3
"""
Demonstration script for hotkey functionality in voice-mcp.

This script shows how to use the hotkey monitoring functionality
to activate speech-to-text with global hotkeys.
"""

import time
import sys
from voice_mcp.tools import VoiceTools
from voice_mcp.config import ServerConfig

def demonstrate_hotkey_functionality():
    """Demonstrate the hotkey functionality."""
    print("🎤 Voice MCP Hotkey Demonstration")
    print("=" * 40)
    
    # Show current configuration
    config = ServerConfig()
    print(f"📋 Configuration:")
    print(f"   - Hotkey enabled: {config.enable_hotkey}")
    print(f"   - Hotkey name: {config.hotkey_name}")
    print(f"   - Output mode: {config.hotkey_output_mode}")
    print(f"   - STT language: {config.stt_language}")
    print()
    
    # Get hotkey status
    status = VoiceTools.get_hotkey_status()
    print(f"🔧 Hotkey Status:")
    print(f"   - Active: {status['active']}")
    print(f"   - PyInput available: {status['pynput_available']}")
    print(f"   - Configuration enabled: {status['configuration']['enabled']}")
    print()
    
    if not status['pynput_available']:
        print("⚠️  pynput is not available!")
        print("   Install with: pip install 'voice-mcp[voice]'")
        print("   This is required for global hotkey monitoring.")
        return
    
    if not config.enable_hotkey:
        print("⚠️  Hotkey monitoring is disabled in configuration.")
        print("   Set VOICE_MCP_ENABLE_HOTKEY=true to enable it.")
        return
    
    # Demonstrate starting/stopping monitoring
    print("🚀 Starting hotkey monitoring...")
    start_result = VoiceTools.start_hotkey_monitoring()
    print(f"   Result: {start_result}")
    
    if "✅" in start_result:
        print(f"🎯 Press the {config.hotkey_name} key to activate STT!")
        print("   (This demo will run for 10 seconds)")
        
        try:
            # Let it run for a bit to demonstrate
            time.sleep(10)
        except KeyboardInterrupt:
            print("\n⏹️  Interrupted by user")
        
        print("🛑 Stopping hotkey monitoring...")
        stop_result = VoiceTools.stop_hotkey_monitoring()
        print(f"   Result: {stop_result}")
    
    print("\n✅ Demonstration complete!")

def show_available_keys():
    """Show examples of supported key names."""
    print("\n🔑 Supported Key Examples:")
    print("=" * 30)
    print("Single keys:")
    print("  - Function keys: f1, f2, ..., f12")
    print("  - Special keys: menu, pause, scroll_lock")
    print("  - Character keys: a, b, c, ..., 1, 2, 3, ...")
    print()
    print("Key combinations:")
    print("  - ctrl+alt+s")
    print("  - ctrl+shift+l")
    print("  - alt+space")
    print()
    print("Modifier aliases:")
    print("  - alt, ctrl, shift")
    print("  - win, windows, cmd (for Windows/Cmd key)")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--keys":
        show_available_keys()
    else:
        demonstrate_hotkey_functionality()
        show_available_keys()