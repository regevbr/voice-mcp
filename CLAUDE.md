# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice MCP Server is a comprehensive Python implementation of a Model Context Protocol (MCP) server providing advanced text-to-speech (TTS), speech-to-text (STT), and global hotkey monitoring for AI assistants. Built with Python 3.12+ using FastMCP framework, the project integrates full voice interaction capabilities directly into AI conversations through the standardized MCP interface with production-ready reliability and performance optimizations.

## Current Status

✅ **Completed (Phase 1-7):**
- Complete MCP server foundation using FastMCP framework
- Advanced TTS implementation with Coqui TTS neural models and high-quality time-stretching
- TTS model preloading for fast first-call performance
- Full STT implementation with faster-whisper and real-time processing
- Real-time voice activation with global hotkey monitoring
- Cross-platform hotkey locking system preventing multi-instance conflicts
- Background loading system for intelligent component preloading
- Advanced text output system (typing, clipboard, return modes)
- Comprehensive audio processing pipeline with quality validation and normalization
- Production-ready configuration management with environment variables
- Rich testing suite covering all voice functionality (82% coverage achieved)
- Enhanced stability with thread-safe operations and robust cleanup
- Security improvements with CodeQL scanning and vulnerability testing
- Performance optimizations (STT silence threshold: 4.0s → 3.0s)
- Audio quality pipeline preventing distortion and "chipmunk effect"
- Comprehensive code formatting with single formatter (Ruff) for CI/CD consistency

## Architecture

### Core Components

```
src/voice_mcp/
├── server.py          # FastMCP server with comprehensive voice tools
├── config.py          # Environment-based configuration with rich settings
├── tools.py           # Complete MCP tool implementations (TTS + STT + Hotkey + Loading)
├── prompts.py         # MCP prompt definitions
├── loading.py         # Background loading state management system
├── cli.py             # Command-line interface (basic implementation)
└── voice/
    ├── tts.py          # Coqui TTS with audio quality pipeline and time-stretching
    ├── stt.py          # faster-whisper STT with real-time processing
    ├── stt_server.py   # STT server implementation
    ├── hotkey.py       # Global hotkey monitoring with voice activation
    ├── hotkey_lock.py  # Cross-platform hotkey locking system
    ├── audio.py        # Advanced audio I/O with effects and processing
    └── text_output.py  # Real-time typing, clipboard, and output modes
```

### Key Features

1. **MCP Server**: FastMCP-based server with comprehensive voice tool set
2. **TTS System**: Coqui TTS neural models with high-quality speech synthesis
3. **GPU Acceleration**: Optional CUDA GPU support for faster TTS processing
4. **Advanced Speech Rate Control**: High-quality time-stretching with natural pitch preservation (eliminates "chipmunk effect")
5. **Audio Quality Pipeline**: Comprehensive validation, normalization, and dynamic range processing
6. **STT System**: faster-whisper implementation with real-time transcription
7. **Hotkey System**: Global keyboard shortcuts with voice-to-text activation
8. **Multi-Instance Coordination**: Cross-process locking prevents hotkey conflicts between server instances
9. **Background Loading System**: Intelligent component preloading for fast startup and reduced latency
10. **Real-time Processing**: Live typing during speech recognition with audio feedback
11. **Text Output Modes**: Multiple output options (typing, clipboard, return)
12. **Audio Pipeline**: Advanced processing with VAD, noise filtering, quality validation, and effects
13. **Configuration**: Rich environment-based configuration system with comprehensive audio settings
14. **Testing**: Comprehensive pytest suite covering all voice functionality (82% coverage)
15. **Cross-Platform Compatibility**: Full support for Windows, macOS, and Linux with platform-specific optimizations

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
- **Testing**: Focused test suite with essential coverage (82% coverage achieved)
- **Formatting**: Ruff (primary) + isort for consistent CI/CD compatibility
- **Documentation**: Comprehensive docstrings and inline documentation
- **Linting**: Comprehensive Ruff linting with security-focused rules
- **Quality Scripts**: Automated quality checks via ./scripts/ directory

### Development Workflow
1. All changes require tests to maintain 82%+ coverage
2. Tests must pass before commits
3. Follow existing patterns and architecture
4. Use uv for dependency management and execution
5. Environment variables for all configuration
6. Use provided scripts for quality checks: ./scripts/check-all.sh
7. Maintain thread-safe patterns for all managers and singletons

## MCP Integration

### Available Tools
- `speak(text, voice?, rate?, volume?)` - Neural text-to-speech with Coqui TTS and audio quality pipeline
- `start_hotkey_monitoring()` - Start global hotkey monitoring for voice activation
- `stop_hotkey_monitoring()` - Stop global hotkey monitoring
- `get_hotkey_status()` - Get comprehensive hotkey and STT status with lock coordination info
- `get_loading_status()` - Get background loading status for all voice components

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
- `VOICE_MCP_TTS_RATE` - Speech rate multiplier with time-stretching (default: 1.0, >1.0 = faster, <1.0 = slower)
- `VOICE_MCP_TTS_VOLUME` - Volume level (default: 0.9)

**STT Configuration:**
- `VOICE_MCP_STT_ENABLED` - Enable STT preloading (default: true)
- `VOICE_MCP_STT_MODEL` - Whisper model size (default: base)
- `VOICE_MCP_STT_DEVICE` - Processing device (default: auto)
- `VOICE_MCP_STT_LANGUAGE` - Default language (default: en)
- `VOICE_MCP_STT_SILENCE_THRESHOLD` - Silence detection (default: 3.0s, reduced from 4.0s for faster response)

**Hotkey & Output Configuration:**
- `VOICE_MCP_ENABLE_HOTKEY` - Enable hotkey monitoring (default: true)
- `VOICE_MCP_HOTKEY_NAME` - Hotkey to monitor (default: menu)
- `VOICE_MCP_HOTKEY_OUTPUT_MODE` - Default output mode (default: typing)
- `VOICE_MCP_TYPING_ENABLED` - Enable real-time typing (default: true)
- `VOICE_MCP_CLIPBOARD_ENABLED` - Enable clipboard output (default: true)
- `VOICE_MCP_TYPING_DEBOUNCE_DELAY` - Typing delay (default: 0.1s)
- `VOICE_MCP_CLIPBOARD_RESTORE_ENABLED` - Restore original clipboard after STT sessions (default: true)
- `VOICE_MCP_CLIPBOARD_RESTORE_DELAY` - Delay before clipboard restoration in seconds (default: 3.0)

**Hotkey Lock Configuration:**
- `VOICE_MCP_HOTKEY_LOCK_ENABLED` - Enable cross-process hotkey locking (default: true)
- `VOICE_MCP_HOTKEY_LOCK_TIMEOUT` - Lock timeout (default: 1.0s, not used for immediate forfeit)
- `VOICE_MCP_HOTKEY_LOCK_DIRECTORY` - Custom lock directory (default: auto-detect)
- `VOICE_MCP_HOTKEY_LOCK_FALLBACK_SEMAPHORE` - Allow semaphore fallback (default: true)

**Audio Quality Configuration:**
- `VOICE_MCP_AUDIO_QUALITY_VALIDATION_ENABLED` - Enable audio quality validation (default: true)
- `VOICE_MCP_AUDIO_QUALITY_MODE` - Audio processing mode (default: balanced, options: fast/balanced/high_quality)
- `VOICE_MCP_AUDIO_NORMALIZATION_HEADROOM` - Normalization headroom to prevent clipping (default: 0.95)

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
2. **Startup Time**: TTS/STT preloading increases server startup time (~3-10 seconds) but eliminates first-call delays via background loading
3. **Audio Hardware**: Both TTS and STT require functional audio input/output
4. **Build Requirements**: NumPy, PyAudio, and other native dependencies need build tools
5. **GPU Acceleration**: CUDA support available but optional for TTS processing
6. **Real-time Performance**: STT with live typing requires low-latency audio pipeline
7. **Hotkey Conflicts**: Resolved with cross-platform hotkey locking system (file-based with semaphore fallback)
8. **Model Downloads**: First-time TTS/STT usage downloads large model files (managed by background loading)
9. **Multi-Instance Coordination**: Complete solution with cross-process locking prevents conflicts between multiple server instances
10. **Audio Quality**: Comprehensive validation and normalization prevents distortion, clipping, and "chipmunk effect"
11. **CI/CD Formatting**: Single formatter (Ruff) ensures consistent code style across development and CI environments

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

# Test background loading status
uv run python -c "
from voice_mcp.tools import VoiceTools
status = VoiceTools.get_loading_status()
print('All components ready:', status['summary']['all_ready'])
print('Component details:', status)
"

# Test STT system (internal - used by hotkey)
uv run python -c "
from voice_mcp.voice.stt import get_transcription_handler
stt = get_transcription_handler()
print('STT Handler Ready:', stt.preload())
"

# Code quality (using single formatter for consistency)
uv run ruff format src/ tests/  # Primary formatter
uv run isort src/ tests/        # Import sorting
uv run ruff check src/ tests/    # Linting
uv run mypy src/                 # Type checking

# Or use scripts
./scripts/format.sh     # Format with Ruff + isort
./scripts/lint.sh       # Lint with Ruff
./scripts/typecheck.sh  # Type check with mypy
./scripts/check-all.sh  # All quality checks
```

## Deployment Notes

- **Claude Desktop**: Add to `claude_desktop_config.json` with voice-mcp command
- **Claude Code**: Use `claude add-mcp voice-mcp` or manual configuration
- **Standalone**: Run with `--transport sse` for HTTP clients
- **Docker**: Containerization supported (basic Dockerfile available)
- **CI/CD**: GitHub Actions for testing, linting, and releases
- **PyPI**: Available as `voice-mcp[audio]` package for easy installation

## Installation & Setup Summary

```bash
# Quick installation (recommended)
pip install voice-mcp[audio]

# Development setup
git clone https://github.com/regevbr/voice-mcp.git
cd voice-mcp
uv sync --extra audio --dev --upgrade

# Quality checks
./scripts/check-all.sh

# Start server
uv run python -m voice_mcp.server --debug
```

The project follows production-ready patterns with comprehensive error handling, logging, and configuration management suitable for both development and production deployment. The full-featured voice system provides complete TTS and STT capabilities with real-time processing, making it suitable for advanced AI assistant voice interactions while maintaining high code quality and reliability.
