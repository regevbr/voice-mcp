# Configuration

Voice MCP Server is configured through environment variables for maximum flexibility.

## TTS Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_MCP_TTS_MODEL` | `tts_models/en/ljspeech/tacotron2-DDC` | Coqui TTS model |
| `VOICE_MCP_TTS_RATE` | `1.0` | Speech rate multiplier |
| `VOICE_MCP_TTS_VOLUME` | `0.9` | Volume level (0.0-1.0) |

## STT Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_MCP_STT_ENABLED` | `true` | Enable STT preloading |
| `VOICE_MCP_STT_MODEL` | `base` | Whisper model size |
| `VOICE_MCP_STT_DEVICE` | `auto` | Processing device |
| `VOICE_MCP_STT_LANGUAGE` | `en` | Default language |
| `VOICE_MCP_STT_SILENCE_THRESHOLD` | `4.0` | Silence detection (seconds) |

## Hotkey Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_MCP_ENABLE_HOTKEY` | `true` | Enable hotkey monitoring |
| `VOICE_MCP_HOTKEY_NAME` | `menu` | Hotkey to monitor |
| `VOICE_MCP_HOTKEY_OUTPUT_MODE` | `typing` | Default output mode |
| `VOICE_MCP_TYPING_ENABLED` | `true` | Enable real-time typing |
| `VOICE_MCP_CLIPBOARD_ENABLED` | `true` | Enable clipboard output |
| `VOICE_MCP_TYPING_DEBOUNCE_DELAY` | `0.1` | Typing delay (seconds) |

## General Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_MCP_LOG_LEVEL` | `INFO` | Logging verbosity |
| `VOICE_MCP_DEBUG` | `false` | Debug mode |

## Example Configuration

Create a `.env` file:

```bash
# TTS Settings
VOICE_MCP_TTS_MODEL=tts_models/en/ljspeech/tacotron2-DDC
VOICE_MCP_TTS_RATE=1.1
VOICE_MCP_TTS_VOLUME=0.8

# STT Settings
VOICE_MCP_STT_MODEL=small
VOICE_MCP_STT_LANGUAGE=en
VOICE_MCP_STT_SILENCE_THRESHOLD=3.0

# Hotkey Settings
VOICE_MCP_HOTKEY_NAME=ctrl+shift+v
VOICE_MCP_HOTKEY_OUTPUT_MODE=clipboard

# General
VOICE_MCP_LOG_LEVEL=DEBUG
```

## Available TTS Models

Popular Coqui TTS models:
- `tts_models/en/ljspeech/tacotron2-DDC` (default)
- `tts_models/en/ljspeech/glow-tts`
- `tts_models/en/ljspeech/speedy-speech`

## Available STT Models

Whisper model sizes:
- `tiny` - Fastest, lowest quality
- `base` - Good balance (default)
- `small` - Better quality
- `medium` - Higher quality
- `large` - Best quality, slowest
