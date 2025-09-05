# Hotkey Monitoring Usage Guide

The voice-mcp server includes global hotkey monitoring functionality that allows you to activate speech-to-text (STT) by pressing configurable hotkeys anywhere in your system.

## Quick Start

1. **Install voice dependencies:**
   ```bash
   pip install 'voice-mcp[voice]'
   ```

2. **Enable hotkey monitoring:**
   ```bash
   export VOICE_MCP_ENABLE_HOTKEY=true
   export VOICE_MCP_HOTKEY_NAME="f12"  # Optional: default is "menu"
   export VOICE_MCP_HOTKEY_OUTPUT_MODE="typing"  # Optional: default is "typing"
   ```

3. **Start the server and enable monitoring:**
   ```python
   from voice_mcp.tools import VoiceTools
   
   # Start hotkey monitoring
   result = VoiceTools.start_hotkey_monitoring()
   print(result)  # "✅ Hotkey monitoring started (Single key: f12)"
   
   # Now press F12 anywhere to activate STT!
   ```

## Configuration

### Environment Variables

- `VOICE_MCP_ENABLE_HOTKEY`: Enable/disable hotkey monitoring (default: `false`)
- `VOICE_MCP_HOTKEY_NAME`: Which key to use (default: `"menu"`)
- `VOICE_MCP_HOTKEY_OUTPUT_MODE`: Output mode when hotkey is pressed (default: `"typing"`)

### Supported Hotkeys

#### Single Keys
```
# Function keys
f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, f12

# Special keys  
menu, pause, scroll_lock, caps_lock, num_lock
space, enter, return, esc, escape, tab, backspace, delete
insert, home, end, page_up, page_down
up, down, left, right

# Character keys
a, b, c, ..., z
1, 2, 3, ..., 0
```

#### Key Combinations
```
# Common combinations
ctrl+alt+s
ctrl+shift+l
alt+space
win+r

# Modifier aliases
alt = alt_l
ctrl = ctrl_l  
shift = shift_l
win = windows = cmd
```

## MCP Tools

The hotkey functionality provides three MCP tools:

### `start_hotkey_monitoring()`
Starts global hotkey monitoring using the configured hotkey.

**Returns:** Status message
```
"✅ Hotkey monitoring started (Single key: f12)"
"⚠️  Hotkey monitoring is disabled in configuration"
"❌ Failed to start hotkey monitoring: pynput not available"
```

### `stop_hotkey_monitoring()`
Stops global hotkey monitoring.

**Returns:** Status message
```
"✅ Hotkey monitoring stopped"
```

### `get_hotkey_status()`
Gets current hotkey monitoring status and configuration.

**Returns:** Dictionary with status information
```json
{
  "active": true,
  "hotkey": "f12", 
  "is_combination": false,
  "pynput_available": true,
  "thread_alive": true,
  "configuration": {
    "enabled": true,
    "hotkey_name": "f12",
    "output_mode": "typing",
    "language": "en"
  }
}
```

## Output Modes

When a hotkey is pressed, the transcribed text can be output in different ways:

- **`"typing"`**: Types the text into the currently active window
- **`"clipboard"`**: Copies the text to the system clipboard
- **`"return"`**: Returns the text only (no automatic output)

## Audio Feedback

When hotkey monitoring is active:
- **On sound**: Plays when recording starts (hotkey pressed)
- **Off sound**: Plays when recording stops (silence detected or manual stop)

## Error Handling

The hotkey system includes comprehensive error handling:

### Graceful Degradation
- Works even when `pynput` is not installed (with helpful error messages)
- Continues working if audio feedback fails
- Proper cleanup of threads and resources

### Common Issues

#### "pynput not available"
**Solution:** Install voice dependencies
```bash
pip install 'voice-mcp[voice]'
```

#### "Hotkey monitoring is disabled in configuration"
**Solution:** Enable in configuration
```bash
export VOICE_MCP_ENABLE_HOTKEY=true
```

#### Global hotkeys not working
- **Linux**: May require running with appropriate permissions
- **macOS**: May require accessibility permissions for the terminal/application
- **Windows**: Usually works without special permissions

## Examples

### Basic Usage
```python
from voice_mcp.tools import VoiceTools

# Check if hotkeys are available
status = VoiceTools.get_hotkey_status()
if not status["pynput_available"]:
    print("Install pynput: pip install 'voice-mcp[voice]'")
    
# Start monitoring
if status["configuration"]["enabled"]:
    result = VoiceTools.start_hotkey_monitoring()
    print(f"Monitoring result: {result}")
    
    # Press the configured hotkey to activate STT
    # ...
    
    # Stop when done
    VoiceTools.stop_hotkey_monitoring()
```

### Custom Configuration
```python
from voice_mcp.config import ServerConfig

# Create custom config
config = ServerConfig(
    enable_hotkey=True,
    hotkey_name="ctrl+alt+s",
    hotkey_output_mode="clipboard",
    stt_language="es"  # Spanish
)

# Use with environment variables
import os
os.environ["VOICE_MCP_ENABLE_HOTKEY"] = "true"
os.environ["VOICE_MCP_HOTKEY_NAME"] = "f11"
os.environ["VOICE_MCP_HOTKEY_OUTPUT_MODE"] = "clipboard"
```

### Demonstration Script
Run the included demonstration:
```bash
python examples/hotkey_demo.py
```

## Thread Safety

The hotkey system is designed to be thread-safe:
- Background monitoring runs in daemon threads
- Proper synchronization prevents race conditions
- Clean shutdown and resource cleanup
- Safe callback execution in separate threads

## Troubleshooting

### Debug Logging
Enable debug logging to see hotkey events:
```bash
export VOICE_MCP_LOG_LEVEL=DEBUG
```

### Test Hotkey Parsing
```python
from voice_mcp.voice.hotkey import HotkeyManager

manager = HotkeyManager()
result = manager._parse_hotkey("ctrl+alt+s")
print(result)
```

### Manual Testing
Use the demonstration script to test your configuration:
```bash
python examples/hotkey_demo.py --keys  # Show supported keys
python examples/hotkey_demo.py         # Full demo
```