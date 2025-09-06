# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice MCP Server is a comprehensive Python implementation of a Model Context Protocol (MCP) server providing advanced text-to-speech (TTS), speech-to-text (STT), and global hotkey monitoring for AI assistants. The project integrates full voice interaction capabilities directly into AI conversations through the standardized MCP interface.

## Current Status

✅ **Completed (Phase 1-6):**
- Complete MCP server foundation using FastMCP framework
- Advanced TTS implementation with Coqui TTS neural models
- TTS model preloading for fast first-call performance
- Full STT implementation with faster-whisper and real-time processing
- Real-time voice activation with global hotkey monitoring
- Advanced text output system (typing, clipboard, return modes)
- Comprehensive audio processing pipeline (NumPy, LibROSA, WebRTC VAD)
- Production-ready configuration management with environment variables
- Rich testing suite covering all voice functionality (92% coverage achieved)
- Enhanced stability with thread-safe operations and robust cleanup
- Security improvements with CodeQL scanning and vulnerability testing
- Performance optimizations (STT silence threshold: 4.0s → 3.0s)
- Updated documentation reflecting latest improvements

## Architecture

### Core Components

```
src/voice_mcp/
├── server.py          # FastMCP server with comprehensive voice tools
├── config.py          # Environment-based configuration with rich settings
├── tools.py           # Complete MCP tool implementations (TTS + STT + Hotkey)
├── prompts.py         # MCP prompt definitions
├── cli.py             # Command-line interface (basic implementation)
└── voice/
    ├── tts.py          # Coqui TTS neural text-to-speech
    ├── stt.py          # faster-whisper STT with real-time processing
    ├── stt_server.py   # STT server implementation
    ├── hotkey.py       # Global hotkey monitoring with voice activation
    ├── audio.py        # Advanced audio I/O with effects and processing
    └── text_output.py  # Real-time typing, clipboard, and output modes
```

### Key Features

1. **MCP Server**: FastMCP-based server with comprehensive voice tool set
2. **TTS System**: Coqui TTS neural models with high-quality speech synthesis
3. **GPU Acceleration**: Optional CUDA GPU support for faster TTS processing
4. **Speech Rate Control**: User-configurable speech rate (speed) control
5. **STT System**: faster-whisper implementation with real-time transcription
6. **Hotkey System**: Global keyboard shortcuts with voice-to-text activation
7. **Real-time Processing**: Live typing during speech recognition with audio feedback
8. **Text Output Modes**: Multiple output options (typing, clipboard, return)
9. **Audio Pipeline**: Advanced processing with VAD, noise filtering, and effects
10. **Configuration**: Rich environment-based configuration system
11. **Testing**: Comprehensive pytest suite covering all voice functionality

## Development Setup

**Required Python**: 3.12+ (due to dependency constraints)

```bash
# Install with uv (recommended) - includes audio extras
uv sync --extra audio --dev --upgrade

# Alternative with pip
pip install -e .[audio]

# Run tests
uv run pytest -v

# Start server
uv run python -m voice_mcp.server --debug
```

## Project Standards

### Code Quality
- **Type hints**: Full typing with mypy compliance
- **Testing**: Focused test suite with essential coverage
- **Formatting**: Black + isort + ruff
- **Documentation**: Comprehensive docstrings

### Development Workflow
1. All changes require tests
2. Tests must pass before commits
3. Follow existing patterns and architecture
4. Use uv for dependency management
5. Environment variables for configuration

## MCP Integration

### Available Tools
- `speak(text, voice?, rate?, volume?)` - Neural text-to-speech with Coqui TTS
- `start_hotkey_monitoring()` - Start global hotkey monitoring for voice activation
- `stop_hotkey_monitoring()` - Stop global hotkey monitoring
- `get_hotkey_status()` - Get comprehensive hotkey and STT status

### Internal STT Functionality (Hotkey-activated)
- Real-time speech-to-text transcription
- Multiple output modes (typing, clipboard, return)
- Silence-based automatic stopping
- Audio feedback with on/off sounds
- Live typing during recognition

### Available Prompts
- `speak` - Instructions for using TTS tools

### Configuration Options
All configurable via environment variables:

**TTS Configuration:**
- `VOICE_MCP_TTS_MODEL` - Coqui TTS model (default: tts_models/en/ljspeech/tacotron2-DDC)
- `VOICE_MCP_TTS_PRELOAD_ENABLED` - Enable TTS preloading on startup (default: true)
- `VOICE_MCP_TTS_GPU_ENABLED` - Enable GPU acceleration for TTS (default: false)
- `VOICE_MCP_TTS_RATE` - Speech rate multiplier (default: 1.0, >1.0 = faster, <1.0 = slower)
- `VOICE_MCP_TTS_VOLUME` - Volume level (default: 0.9)

**STT Configuration:**
- `VOICE_MCP_STT_ENABLED` - Enable STT preloading (default: true)
- `VOICE_MCP_STT_MODEL` - Whisper model size (default: base)
- `VOICE_MCP_STT_DEVICE` - Processing device (default: auto)
- `VOICE_MCP_STT_LANGUAGE` - Default language (default: en)
- `VOICE_MCP_STT_SILENCE_THRESHOLD` - Silence detection (default: 3.0s, previously 4.0s)

**Hotkey & Output Configuration:**
- `VOICE_MCP_ENABLE_HOTKEY` - Enable hotkey monitoring (default: true)
- `VOICE_MCP_HOTKEY_NAME` - Hotkey to monitor (default: menu)
- `VOICE_MCP_HOTKEY_OUTPUT_MODE` - Default output mode (default: typing)
- `VOICE_MCP_TYPING_ENABLED` - Enable real-time typing (default: true)
- `VOICE_MCP_CLIPBOARD_ENABLED` - Enable clipboard output (default: true)
- `VOICE_MCP_TYPING_DEBOUNCE_DELAY` - Typing delay (default: 0.1s)

**General Configuration:**
- `VOICE_MCP_LOG_LEVEL` - Logging verbosity (default: INFO)
- `VOICE_MCP_DEBUG` - Debug mode (default: false)

## Testing Strategy

```bash
# Run all tests
uv run pytest

# Test with coverage
uv run pytest --cov=voice_mcp --cov-report=html

# Test core functionality
uv run pytest tests/test_tools.py tests/test_prompts.py -v

# Skip hardware tests
uv run pytest -m "not voice"
```

## Known Issues & Considerations

1. **Heavy Dependencies**: Coqui TTS and faster-whisper require significant disk space and memory
2. **Startup Time**: TTS/STT preloading increases server startup time (~3-10 seconds) but eliminates first-call delays
3. **Audio Hardware**: Both TTS and STT require functional audio input/output
4. **Build Requirements**: NumPy, PyAudio, and other native dependencies need build tools
5. **GPU Acceleration**: CUDA support available but optional for STT processing
6. **Real-time Performance**: STT with live typing requires low-latency audio pipeline
7. **Hotkey Conflicts**: Global hotkeys may conflict with system shortcuts
8. **Model Downloads**: First-time TTS/STT usage downloads large model files

## Development Commands

```bash
# Server operations
uv run python -m voice_mcp.server --transport sse --port 8000
uv run python -m voice_mcp.server --debug --log-level DEBUG

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

# Test STT system (internal - used by hotkey)
uv run python -c "
from voice_mcp.voice.stt import get_transcription_handler
stt = get_transcription_handler()
print('STT Handler Ready:', stt.preload())
"

# Code quality
uv run black src/ tests/
uv run ruff check src/ tests/
uv run mypy src/
```

## Deployment Notes

- **Claude Desktop**: Add to `claude_desktop_config.json`
- **Standalone**: Run with `--transport sse` for HTTP clients
- **Docker**: Containerization supported (Dockerfile included)
- **CI/CD**: GitHub Actions for testing and releases

The project follows production-ready patterns with comprehensive error handling, logging, and configuration management suitable for both development and production deployment. The full-featured voice system provides complete TTS and STT capabilities with real-time processing, making it suitable for advanced AI assistant voice interactions while maintaining high code quality and reliability.
- always sync uv locally with uv sync --extra audio --dev --upgrade
