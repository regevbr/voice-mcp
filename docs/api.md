# API Reference

This document provides a comprehensive reference for the Voice MCP Server API, including MCP tools, core modules, and configuration options.

## MCP Tools

### VoiceTools

The main interface for voice functionality in the MCP server.

#### speak(text, voice=None, rate=None, volume=None)

Convert text to speech using the configured TTS engine.

**Parameters:**
- `text` (str): The text to convert to speech (required)
- `voice` (str, optional): Voice to use (system-dependent)
- `rate` (float, optional): Speech rate multiplier (1.0 = normal, >1.0 = faster, <1.0 = slower, default: config.tts_rate)
- `volume` (float, optional): Volume level 0.0-1.0 (default: config.tts_volume)

**Features:**
- **GPU Acceleration**: Automatically uses CUDA GPU if available and enabled
- **High-Quality Rate Control**: Speed adjustment maintains natural pitch
- **Model Preloading**: Optimized for instant first-call performance

**Returns:**
- `str`: Status message indicating success or failure

**Example:**
```python
result = VoiceTools.speak("Hello from Voice MCP!")
# Returns: "✅ Successfully spoke: 'Hello from Voice MCP!'"

# With speed control
result = VoiceTools.speak("Faster speech", rate=1.3)  # 30% faster
result = VoiceTools.speak("Slower speech", rate=0.8)  # 20% slower

# With custom parameters
result = VoiceTools.speak("Custom message", rate=1.2, volume=0.8)
```

#### start_hotkey_monitoring()

Start global hotkey monitoring for voice activation.

**Returns:**
- `str`: Status message indicating success or failure

**Example:**
```python
result = VoiceTools.start_hotkey_monitoring()
# Returns: "✅ Hotkey monitoring started (menu)"
```

#### stop_hotkey_monitoring()

Stop global hotkey monitoring and cleanup resources.

**Returns:**
- `str`: Status message indicating success or failure

**Example:**
```python
result = VoiceTools.stop_hotkey_monitoring()
# Returns: "✅ Hotkey monitoring stopped"
```

#### get_hotkey_status()

Get current hotkey monitoring status and configuration details.

**Returns:**
- `dict`: Dictionary containing hotkey status, configuration, and error conditions

**Example:**
```python
status = VoiceTools.get_hotkey_status()
# Returns: {
#   "active": True,
#   "hotkey_name": "menu",
#   "description": "Menu key",
#   "configuration": {
#     "enabled": True,
#     "hotkey_name": "menu",
#     "output_mode": "typing",
#     "language": "en"
#   }
# }
```

## Core Modules

### TTS Module (voice_mcp.voice.tts)

#### TTSManager

High-quality neural text-to-speech using Coqui TTS.

**Key Methods:**
- `speak(text, voice=None, rate=None, volume=None)`: Convert text to speech
- `get_available_models()`: List available TTS models
- `cleanup()`: Clean up TTS resources

**Configuration:**
- Model: `VOICE_MCP_TTS_MODEL`
- Rate: `VOICE_MCP_TTS_RATE`
- Volume: `VOICE_MCP_TTS_VOLUME`

### STT Module (voice_mcp.voice.stt)

#### TranscriptionHandler

Real-time speech-to-text using faster-whisper.

**Key Methods:**
- `transcribe_once(duration=None, language="en")`: Single transcription
- `transcribe_with_realtime_output(text_output_controller, duration=None, language="en")`: Real-time typing transcription
- `preload()`: Preload STT model
- `cleanup()`: Clean up STT resources

**Configuration:**
- Model: `VOICE_MCP_STT_MODEL`
- Device: `VOICE_MCP_STT_DEVICE`
- Language: `VOICE_MCP_STT_LANGUAGE`
- Silence Threshold: `VOICE_MCP_STT_SILENCE_THRESHOLD`

### Hotkey Module (voice_mcp.voice.hotkey)

#### HotkeyManager

Global hotkey monitoring for voice activation.

**Key Methods:**
- `start_monitoring(hotkey_name)`: Start monitoring specified hotkey
- `stop_monitoring()`: Stop hotkey monitoring
- `get_status()`: Get current monitoring status
- `is_active()`: Check if monitoring is active

**Configuration:**
- Enable: `VOICE_MCP_ENABLE_HOTKEY`
- Hotkey: `VOICE_MCP_HOTKEY_NAME`
- Output Mode: `VOICE_MCP_HOTKEY_OUTPUT_MODE`

### Audio Module (voice_mcp.voice.audio)

#### AudioManager

Advanced audio I/O and effects management.

**Key Methods:**
- `play_on_sound()`: Play recording start sound
- `play_off_sound()`: Play recording stop sound
- `is_available`: Check if audio hardware is available
- `get_input_devices()`: List available input devices
- `get_output_devices()`: List available output devices

**Features:**
- WebRTC VAD (Voice Activity Detection)
- NumPy/LibROSA audio processing
- Cross-platform audio support

### Text Output Module (voice_mcp.voice.text_output)

#### TextOutputController

Real-time typing, clipboard, and text output management.

**Key Methods:**
- `output_text(text, mode)`: Output text using specified mode
- `type_text_realtime(text, debounce_delay=0.1)`: Real-time typing
- `copy_to_clipboard(text)`: Copy text to clipboard

**Output Modes:**
- `typing`: Real-time typing during speech recognition
- `clipboard`: Copy final text to clipboard
- `return`: Return text to calling application

**Configuration:**
- Typing Enabled: `VOICE_MCP_TYPING_ENABLED`
- Clipboard Enabled: `VOICE_MCP_CLIPBOARD_ENABLED`
- Debounce Delay: `VOICE_MCP_TYPING_DEBOUNCE_DELAY`

## Configuration Module (voice_mcp.config)

### VoiceMCPConfig

Environment-based configuration management using Pydantic.

**Server Settings:**
- `host`: Server host (default: "localhost")
- `port`: Server port (default: 8000)
- `transport`: Transport type (default: "stdio")
- `debug`: Debug mode (default: False)
- `log_level`: Logging level (default: "INFO")

**TTS Settings:**
- `tts_model`: Coqui TTS model (default: "tts_models/en/ljspeech/tacotron2-DDC")
- `tts_rate`: Speech rate multiplier (default: 1.0)
- `tts_volume`: Volume level (default: 0.9)

**STT Settings:**
- `stt_enabled`: Enable STT preloading (default: True)
- `stt_model`: Whisper model size (default: "base")
- `stt_device`: Processing device (default: "auto")
- `stt_language`: Default language (default: "en")
- `stt_silence_threshold`: Silence detection threshold (default: 4.0)

**Hotkey Settings:**
- `enable_hotkey`: Enable hotkey monitoring (default: True)
- `hotkey_name`: Hotkey to monitor (default: "menu")
- `hotkey_output_mode`: Default output mode (default: "typing")
- `typing_enabled`: Enable real-time typing (default: True)
- `clipboard_enabled`: Enable clipboard output (default: True)
- `typing_debounce_delay`: Typing debounce delay (default: 0.1)

## Error Handling

All API methods include comprehensive error handling:

- **TTS Errors**: Model loading, audio playback, configuration issues
- **STT Errors**: Microphone access, model loading, transcription failures
- **Hotkey Errors**: Permission issues, invalid hotkey names, system conflicts
- **Audio Errors**: Hardware unavailable, device conflicts, permission denied

Error responses include descriptive messages and are logged appropriately for debugging.

## Type Hints

The Voice MCP Server is fully typed using Python type hints:

```python
from typing import Any, Optional, Dict, List
from voice_mcp.tools import VoiceTools

# All methods have proper type annotations
result: str = VoiceTools.speak("Hello")
status: Dict[str, Any] = VoiceTools.get_hotkey_status()
```

## Thread Safety

- **TTSManager**: Thread-safe singleton instance
- **STT Operations**: Single-threaded per transcription session
- **HotkeyManager**: Uses system-level global hooks
- **AudioManager**: Thread-safe audio device access

## Resource Management

All managers implement proper resource cleanup:

```python
# Automatic cleanup on server shutdown
atexit.register(cleanup_resources)

# Manual cleanup if needed
tts_manager.cleanup()
stt_handler.cleanup()
hotkey_manager.stop_monitoring()
```
