# Configuration

Voice MCP Server is configured through environment variables for maximum flexibility and deployment compatibility.

## Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_MCP_HOST` | `localhost` | Server host for SSE transport |
| `VOICE_MCP_PORT` | `8000` | Server port for SSE transport |
| `VOICE_MCP_TRANSPORT` | `stdio` | Transport type (`stdio`, `sse`) |
| `VOICE_MCP_DEBUG` | `false` | Enable debug mode |
| `VOICE_MCP_LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

## Text-to-Speech Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_MCP_TTS_MODEL` | `tts_models/en/ljspeech/tacotron2-DDC` | Coqui TTS model |
| `VOICE_MCP_TTS_RATE` | `1.0` | Speech rate multiplier |
| `VOICE_MCP_TTS_VOLUME` | `0.9` | Volume level (0.0 to 1.0) |

### Available TTS Models

Popular Coqui TTS models:
- `tts_models/en/ljspeech/tacotron2-DDC` (default, balanced quality/speed)
- `tts_models/en/ljspeech/glow-tts` (faster inference)
- `tts_models/en/ljspeech/speedy-speech` (fastest)
- `tts_models/en/ljspeech/fast_pitch` (high quality)
- `tts_models/en/vctk/vits` (multiple speakers)

## Speech-to-Text Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_MCP_STT_ENABLED` | `true`  | Enable STT preloading on startup |
| `VOICE_MCP_STT_MODEL` | `base`  | Whisper model size |
| `VOICE_MCP_STT_DEVICE` | `auto`  | Processing device (`auto`, `cuda`, `cpu`) |
| `VOICE_MCP_STT_LANGUAGE` | `en`    | Default STT language |
| `VOICE_MCP_STT_SILENCE_THRESHOLD` | `3.0`   | Silence detection threshold (seconds)


### Available STT Models

Whisper model sizes (faster-whisper):
- `tiny` - Fastest, ~2 GB VRAM, lowest quality
- `base` - Good balance, ~1 GB VRAM (default)
- `small` - Better quality, ~2 GB VRAM
- `medium` - Higher quality, ~5 GB VRAM
- `large` - Best quality, ~10 GB VRAM, slowest
- `large-v2` - Latest large model
- `large-v3` - Most recent large model

### Supported STT Languages

Common language codes:
- `en` - English (default)
- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `ja` - Japanese
- `ko` - Korean
- `zh` - Chinese
- `ru` - Russian
- `pt` - Portuguese

## Hotkey & Voice Activation Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_MCP_ENABLE_HOTKEY` | `true` | Enable global hotkey monitoring |
| `VOICE_MCP_HOTKEY_NAME` | `menu` | Hotkey to monitor |
| `VOICE_MCP_HOTKEY_OUTPUT_MODE` | `typing` | Default output mode |
| `VOICE_MCP_TYPING_ENABLED` | `true` | Enable real-time typing output |
| `VOICE_MCP_CLIPBOARD_ENABLED` | `true` | Enable clipboard output |
| `VOICE_MCP_TYPING_DEBOUNCE_DELAY` | `0.1` | Typing debounce delay (seconds) |

### Available Hotkeys

Common hotkey names:
- `menu` - Menu key (default)
- `f1`, `f2`, ..., `f12` - Function keys
- `ctrl+shift+v` - Key combinations
- `alt+space` - Alt + Space
- `shift+f10` - Shift + F10
- `insert` - Insert key
- `pause` - Pause/Break key

### Output Modes

- **`typing`**: Text appears in real-time as you speak (recommended for interactive use)
- **`clipboard`**: Text is copied to clipboard after recording (good for batch processing)
- **`return`**: Text is returned to the calling application (internal use)

## Example Configurations

### Development Configuration

Create a `.env` file:

```bash
# Server Settings
VOICE_MCP_DEBUG=true
VOICE_MCP_LOG_LEVEL=DEBUG
VOICE_MCP_TRANSPORT=stdio

# TTS Settings - High Quality
VOICE_MCP_TTS_MODEL=tts_models/en/ljspeech/fast_pitch
VOICE_MCP_TTS_RATE=1.0
VOICE_MCP_TTS_VOLUME=0.9

# STT Settings - Balanced Performance
VOICE_MCP_STT_ENABLED=true
VOICE_MCP_STT_MODEL=base
VOICE_MCP_STT_DEVICE=auto
VOICE_MCP_STT_LANGUAGE=en
VOICE_MCP_STT_SILENCE_THRESHOLD=3.0

# Hotkey Settings - Real-time Typing
VOICE_MCP_ENABLE_HOTKEY=true
VOICE_MCP_HOTKEY_NAME=menu
VOICE_MCP_HOTKEY_OUTPUT_MODE=typing
VOICE_MCP_TYPING_ENABLED=true
VOICE_MCP_TYPING_DEBOUNCE_DELAY=0.05
```

### Production Configuration

```bash
# Server Settings
VOICE_MCP_DEBUG=false
VOICE_MCP_LOG_LEVEL=INFO
VOICE_MCP_TRANSPORT=stdio

# TTS Settings - Optimized for Speed
VOICE_MCP_TTS_MODEL=tts_models/en/ljspeech/speedy-speech
VOICE_MCP_TTS_RATE=1.0
VOICE_MCP_TTS_VOLUME=0.8

# STT Settings - Small Model for Speed
VOICE_MCP_STT_ENABLED=true
VOICE_MCP_STT_MODEL=small
VOICE_MCP_STT_DEVICE=cuda
VOICE_MCP_STT_LANGUAGE=en
VOICE_MCP_STT_SILENCE_THRESHOLD=2.5

# Hotkey Settings - Clipboard Mode
VOICE_MCP_ENABLE_HOTKEY=true
VOICE_MCP_HOTKEY_NAME=ctrl+shift+v
VOICE_MCP_HOTKEY_OUTPUT_MODE=clipboard
VOICE_MCP_TYPING_ENABLED=false
```

### Multi-Language Configuration

```bash
# STT Settings - Multi-language Support
VOICE_MCP_STT_MODEL=medium
VOICE_MCP_STT_LANGUAGE=auto  # Auto-detect language
VOICE_MCP_STT_DEVICE=cuda
VOICE_MCP_STT_SILENCE_THRESHOLD=3.0

# TTS Settings - Multi-speaker Model
VOICE_MCP_TTS_MODEL=tts_models/en/vctk/vits
VOICE_MCP_TTS_RATE=0.9
VOICE_MCP_TTS_VOLUME=0.85
```

### CI/CD Configuration

```bash
# Minimal Configuration for Testing
VOICE_MCP_DEBUG=false
VOICE_MCP_LOG_LEVEL=WARNING
VOICE_MCP_STT_ENABLED=false  # Disable STT in CI
VOICE_MCP_ENABLE_HOTKEY=false  # Disable hotkey in CI
VOICE_MCP_TTS_MODEL=tts_models/en/ljspeech/speedy-speech  # Fastest model
```

## Claude Desktop Configuration

For Claude Desktop integration, add environment variables to the MCP server configuration:

```json
{
  "mcpServers": {
    "voice-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "voice_mcp.server"],
      "env": {
        "VOICE_MCP_TTS_MODEL": "tts_models/en/ljspeech/tacotron2-DDC",
        "VOICE_MCP_TTS_RATE": "1.0",
        "VOICE_MCP_TTS_VOLUME": "0.9",
        "VOICE_MCP_STT_ENABLED": "true",
        "VOICE_MCP_STT_MODEL": "base",
        "VOICE_MCP_STT_LANGUAGE": "en",
        "VOICE_MCP_ENABLE_HOTKEY": "true",
        "VOICE_MCP_HOTKEY_NAME": "menu",
        "VOICE_MCP_HOTKEY_OUTPUT_MODE": "typing",
        "VOICE_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Performance Tuning

### For Maximum Quality
- STT Model: `large-v3`
- TTS Model: `tts_models/en/ljspeech/fast_pitch`
- Device: `cuda`
- Silence Threshold: `5.0`

### For Maximum Speed
- STT Model: `tiny`
- TTS Model: `tts_models/en/ljspeech/speedy-speech`
- Device: `cpu` (if no CUDA)
- Silence Threshold: `2.0`

### For Balanced Performance
- STT Model: `base` or `small`
- TTS Model: `tts_models/en/ljspeech/tacotron2-DDC`
- Device: `auto`
- Silence Threshold: `3.0`
