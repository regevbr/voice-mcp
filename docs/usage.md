# Usage

## MCP Server

Start the MCP server:

```bash
voice-mcp
```

Or with debug logging:

```bash
voice-mcp --debug
```

## Available Tools

### Text-to-Speech

```python
from voice_mcp.tools import VoiceTools

# Basic TTS
result = VoiceTools.speak("Hello from Voice MCP!")

# With options
result = VoiceTools.speak(
    "Custom voice message",
    voice="default",
    rate=1.2,
    volume=0.8
)
```

### Hotkey Monitoring

```python
# Start monitoring for voice activation
VoiceTools.start_hotkey_monitoring()

# Check status
status = VoiceTools.get_hotkey_status()
print(f"Active: {status['active']}")

# Stop monitoring
VoiceTools.stop_hotkey_monitoring()
```

## Configuration

Configure via environment variables:

```bash
export VOICE_MCP_TTS_MODEL="tts_models/en/ljspeech/tacotron2-DDC"
export VOICE_MCP_STT_MODEL="base"
export VOICE_MCP_HOTKEY_NAME="menu"
export VOICE_MCP_LOG_LEVEL="INFO"
```

## Integration with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "voice-mcp": {
      "command": "voice-mcp",
      "env": {
        "VOICE_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```
