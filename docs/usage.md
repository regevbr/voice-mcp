# Usage

## MCP Server

### Standalone Mode

Start the MCP server:

```bash
# Start with stdio transport (default for MCP clients)
uv run python -m voice_mcp.server

# Start with SSE transport (HTTP-based)
uv run python -m voice_mcp.server --transport sse --port 8000

# Debug mode with verbose logging
uv run python -m voice_mcp.server --debug --log-level DEBUG
```

### Claude Desktop Integration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "voice-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "voice_mcp.server"],
      "env": {
        "VOICE_MCP_TTS_MODEL": "tts_models/en/ljspeech/tacotron2-DDC",
        "VOICE_MCP_STT_ENABLED": "true",
        "VOICE_MCP_ENABLE_HOTKEY": "true",
        "VOICE_MCP_HOTKEY_NAME": "menu",
        "VOICE_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## MCP Tools Usage

### Text-to-Speech (`speak`)

Convert text to speech with optional voice, rate, and volume parameters.

**In Claude Conversation:**
```
Human: Please speak this message: "Hello! The voice MCP server is working perfectly."

Claude: I'll use the speak tool to convert your message to speech.

*Uses speak tool with text: "Hello! The voice MCP server is working perfectly."*

✅ Successfully spoke: 'Hello! The voice MCP server is working perfectly...'
```

**Direct Python Usage:**
```python
from voice_mcp.tools import VoiceTools

# Basic TTS
result = VoiceTools.speak("Hello from Voice MCP!")

# With custom parameters
result = VoiceTools.speak(
    "Custom voice message",
    voice="default",
    rate=1.2,
    volume=0.8
)
print(result)  # ✅ Successfully spoke: 'Custom voice message'
```

### Hotkey Monitoring (`start_hotkey_monitoring`, `stop_hotkey_monitoring`, `get_hotkey_status`)

Enable global hotkey shortcuts for voice-to-text activation.

**In Claude Conversation:**
```
Human: Start monitoring the hotkey for voice activation.

Claude: I'll start the global hotkey monitoring for you.

*Uses start_hotkey_monitoring tool*

✅ Hotkey monitoring started (menu key)
```

**Direct Python Usage:**
```python
from voice_mcp.tools import VoiceTools

# Start monitoring for voice activation
result = VoiceTools.start_hotkey_monitoring()
print(result)  # ✅ Hotkey monitoring started (menu)

# Check current status
status = VoiceTools.get_hotkey_status()
print(f"Active: {status['active']}")
print(f"Hotkey: {status['configuration']['hotkey_name']}")
print(f"Output Mode: {status['configuration']['output_mode']}")

# Stop monitoring
result = VoiceTools.stop_hotkey_monitoring()
print(result)  # ✅ Hotkey monitoring stopped
```

## Voice-to-Text with Hotkeys

When hotkey monitoring is active, press the configured hotkey (default: `menu` key) to:

1. **Start Voice Recording**: Audio feedback plays ("on" sound)
2. **Real-time Transcription**: Spoken words appear as you speak
3. **Automatic Stopping**: Stops after silence threshold (default: 4 seconds)
4. **Audio Feedback**: "Off" sound plays when recording stops

### Output Modes

- **`typing`**: Text appears in real-time as you speak
- **`clipboard`**: Text is copied to clipboard after recording
- **`return`**: Text is returned to the calling application

## Environment Configuration

Configure via environment variables or `.env` file:

```bash
# TTS Settings
VOICE_MCP_TTS_MODEL=tts_models/en/ljspeech/tacotron2-DDC
VOICE_MCP_TTS_RATE=1.1
VOICE_MCP_TTS_VOLUME=0.8

# STT Settings
VOICE_MCP_STT_ENABLED=true
VOICE_MCP_STT_MODEL=base
VOICE_MCP_STT_LANGUAGE=en
VOICE_MCP_STT_SILENCE_THRESHOLD=3.0

# Hotkey Settings
VOICE_MCP_ENABLE_HOTKEY=true
VOICE_MCP_HOTKEY_NAME=menu
VOICE_MCP_HOTKEY_OUTPUT_MODE=typing

# General Settings
VOICE_MCP_LOG_LEVEL=INFO
VOICE_MCP_DEBUG=false
```

## Testing Commands

### Test Core Functionality

```bash
# Test TTS functionality
uv run python -c "
from voice_mcp.tools import VoiceTools
result = VoiceTools.speak('Hello from Voice MCP!')
print('TTS Result:', result)
"

# Test hotkey system
uv run python -c "
from voice_mcp.tools import VoiceTools
status = VoiceTools.get_hotkey_status()
print('Hotkey Active:', status['active'])
print('Configuration:', status['configuration'])
"
```

### Test STT System (Internal)

```bash
# Test STT handler (used internally by hotkey system)
uv run python -c "
from voice_mcp.voice.stt import get_transcription_handler
stt = get_transcription_handler()
print('STT Handler Ready:', stt.preload())
"
```

## Development Usage

### Running Tests

```bash
# Run all tests
uv run pytest

# Test with coverage
uv run pytest --cov=voice_mcp --cov-report=html

# Test core functionality (skip hardware tests)
uv run pytest -m "not voice" -v
```

### Code Quality Commands

```bash
# Format code
uv run black src/ tests/
uv run isort src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```
