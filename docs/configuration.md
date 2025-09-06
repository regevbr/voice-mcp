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
| `VOICE_MCP_TTS_PRELOAD_ENABLED` | `true` | Enable TTS model preloading on startup |
| `VOICE_MCP_TTS_GPU_ENABLED` | `false` | Enable GPU acceleration for TTS (requires CUDA) |
| `VOICE_MCP_TTS_RATE` | `1.0` | Speech rate multiplier (>1.0 = faster, <1.0 = slower, uses time-stretching) |
| `VOICE_MCP_TTS_VOLUME` | `0.9` | Volume level (0.0 to 1.0) |

## Audio Quality Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_MCP_AUDIO_QUALITY_VALIDATION_ENABLED` | `true` | Enable audio quality validation |
| `VOICE_MCP_AUDIO_QUALITY_MODE` | `balanced` | Quality mode (`fast`, `balanced`, `high_quality`) |
| `VOICE_MCP_AUDIO_NORMALIZATION_HEADROOM` | `0.95` | Headroom for audio normalization (0.0-1.0) |

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
VOICE_MCP_TTS_PRELOAD_ENABLED=true
VOICE_MCP_TTS_GPU_ENABLED=false
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

# Audio Quality Settings
VOICE_MCP_AUDIO_QUALITY_VALIDATION_ENABLED=true
VOICE_MCP_AUDIO_QUALITY_MODE=balanced
VOICE_MCP_AUDIO_NORMALIZATION_HEADROOM=0.95
```

### Production Configuration

```bash
# Server Settings
VOICE_MCP_DEBUG=false
VOICE_MCP_LOG_LEVEL=INFO
VOICE_MCP_TRANSPORT=stdio

# TTS Settings - Optimized for Speed
VOICE_MCP_TTS_MODEL=tts_models/en/ljspeech/speedy-speech
VOICE_MCP_TTS_PRELOAD_ENABLED=true
VOICE_MCP_TTS_GPU_ENABLED=true
VOICE_MCP_TTS_RATE=1.2
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

# Audio Quality Settings - High Performance
VOICE_MCP_AUDIO_QUALITY_VALIDATION_ENABLED=true
VOICE_MCP_AUDIO_QUALITY_MODE=high_quality
VOICE_MCP_AUDIO_NORMALIZATION_HEADROOM=0.90
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
VOICE_MCP_TTS_PRELOAD_ENABLED=true
VOICE_MCP_TTS_GPU_ENABLED=true
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
        "VOICE_MCP_TTS_PRELOAD_ENABLED": "true",
        "VOICE_MCP_TTS_GPU_ENABLED": "false",
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

### GPU Acceleration Setup

For optimal performance with GPU acceleration:

```bash
# Enable GPU for TTS (requires CUDA)
VOICE_MCP_TTS_GPU_ENABLED=true

# Enable GPU for STT
VOICE_MCP_STT_DEVICE=cuda

# Preload models for instant first-call performance
VOICE_MCP_TTS_PRELOAD_ENABLED=true
VOICE_MCP_STT_ENABLED=true
```

**GPU Requirements:**
- NVIDIA GPU with CUDA support
- PyTorch with CUDA installation
- 4GB+ VRAM recommended for TTS + STT

### Performance Profiles

### For Maximum Quality + GPU
- STT Model: `large-v3`
- STT Device: `cuda`
- TTS Model: `tts_models/en/ljspeech/fast_pitch`
- TTS GPU: `true`
- TTS Rate: `1.0`
- Silence Threshold: `5.0`

### For Maximum Speed + GPU
- STT Model: `tiny` or `base`
- STT Device: `cuda`
- TTS Model: `tts_models/en/ljspeech/speedy-speech`
- TTS GPU: `true`
- TTS Rate: `1.3` (30% faster speech)
- Silence Threshold: `2.0`

### For Balanced Performance (CPU Fallback)
- STT Model: `base` or `small`
- STT Device: `auto`
- TTS Model: `tts_models/en/ljspeech/tacotron2-DDC`
- TTS GPU: `false`
- TTS Rate: `1.0`
- Silence Threshold: `3.0`

### Speech Rate Control

Fine-tune speech speed using high-quality time-stretching that maintains natural pitch:

```bash
# Presentations (clear and slow)
VOICE_MCP_TTS_RATE=0.8

# Normal conversation
VOICE_MCP_TTS_RATE=1.0

# Quick updates (faster speech)
VOICE_MCP_TTS_RATE=1.3

# Very fast notifications
VOICE_MCP_TTS_RATE=1.5
```

**Rate Guidelines:**
- `0.7-0.9`: Slower, clearer speech for presentations
- `1.0`: Normal speech rate (default)
- `1.1-1.3`: Slightly faster for efficiency
- `1.4-1.6`: Fast speech for quick notifications
- `>1.6`: May sound unnatural depending on model

**Technical Details:**
- Uses librosa time-stretching for pitch-preserving speed adjustment
- No audio distortion or "chipmunk effect"
- Maintains natural speech characteristics at all rates
