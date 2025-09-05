# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice MCP Server is a streamlined Python implementation of a Model Context Protocol (MCP) server providing text-to-speech (TTS) capabilities and hotkey monitoring for AI assistants. The project integrates essential voice functionality directly into AI interactions through the standardized MCP interface.

## Current Status

✅ **Completed (Phase 1-4):**
- Complete MCP server foundation using FastMCP framework
- Full TTS implementation with multi-engine support (pyttsx3 + gTTS)
- Hotkey monitoring system with global shortcuts
- Streamlined tool set focused on core functionality
- Comprehensive testing suite for essential features
- Production-ready configuration management
- CLI interface and server modes
- Updated documentation (README.md)

## Architecture

### Core Components

```
src/voice_mcp/
├── server.py          # Simplified MCP server with essential tools
├── config.py          # Environment-based configuration 
├── tools.py           # Core MCP tool implementations
├── prompts.py         # MCP prompt definitions
├── cli.py             # Command-line interface
└── voice/
    ├── tts.py          # TTS engine implementations
    ├── hotkey.py       # Global hotkey monitoring
    ├── audio.py        # Audio I/O management
    ├── stt.py          # Speech-to-text (internal use)
    └── text_output.py  # Text output handling
```

### Key Features

1. **MCP Server**: FastMCP-based server with streamlined tool set
2. **TTS System**: Multi-engine (pyttsx3, gTTS) with automatic fallback
3. **Hotkey Monitoring**: Global keyboard shortcuts for voice activation
4. **Configuration**: Environment variables with defaults
5. **Testing**: Focused pytest suite for essential functionality
6. **CLI**: Management interface for server operations

## Development Setup

**Required Python**: 3.11+ (due to dependency constraints)

```bash
# Install with uv (recommended)
uv sync --dev

# Alternative with pip
pip install -e .

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
- `speak(text, voice?, rate?, volume?)` - Text-to-speech conversion
- `start_hotkey_monitoring()` - Start global hotkey monitoring
- `stop_hotkey_monitoring()` - Stop global hotkey monitoring  
- `get_hotkey_status()` - Get hotkey monitoring status

### Available Prompts  
- `speak_guide` - Instructions for using TTS tools

### Configuration Options
All configurable via environment variables:
- `VOICE_MCP_TTS_ENGINE` - Engine selection (pyttsx3/gtts)
- `VOICE_MCP_TTS_RATE` - Speech rate (WPM)
- `VOICE_MCP_TTS_VOLUME` - Volume level (0.0-1.0)
- `VOICE_MCP_ENABLE_HOTKEY` - Enable hotkey monitoring
- `VOICE_MCP_HOTKEY_NAME` - Hotkey to monitor (default: menu)
- `VOICE_MCP_LOG_LEVEL` - Logging verbosity

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

1. **Dependencies**: Audio libraries may have platform-specific requirements
2. **Audio Hardware**: TTS requires system audio libraries
3. **Platform Differences**: Voice engines vary by OS
4. **Hotkey Conflicts**: Global hotkeys may conflict with system shortcuts

## Development Commands

```bash
# Server operations
uv run python -m voice_mcp.server --transport sse --port 8000
uv run python -m voice_mcp.server --debug --log-level DEBUG

# Testing core functionality directly
uv run python -c "
from voice_mcp.tools import VoiceTools
result = VoiceTools.speak('Hello from Voice MCP!')
print('TTS Result:', result)
status = VoiceTools.get_hotkey_status()
print('Hotkey Status:', status['active'])
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

The project follows production-ready patterns with comprehensive error handling, logging, and configuration management suitable for both development and production deployment. The streamlined tool set focuses on essential voice functionality while maintaining high code quality and reliability.