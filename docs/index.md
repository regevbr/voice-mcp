# Voice MCP Server

A comprehensive Model Context Protocol (MCP) server providing advanced text-to-speech (TTS), speech-to-text (STT), and global hotkey monitoring capabilities for AI assistants. Built with Python 3.12+ using FastMCP framework for optimal performance and reliability.

[![Tests](https://github.com/regevbr/voice-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/regevbr/voice-mcp/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## ✨ Features

### 🔊 Text-to-Speech (TTS)
- **Coqui TTS Engine**: High-quality neural text-to-speech with customizable models
- **GPU Acceleration**: Optional CUDA GPU support for faster TTS processing
- **Advanced Speech Rate Control**: High-quality time-stretching with natural pitch preservation
- **Audio Quality Pipeline**: Comprehensive validation, normalization, and dynamic range processing
- **Voice customization**: Select voices, adjust rate and volume with distortion-free output
- **Cross-platform**: Works on Linux, Windows, and macOS
- **MCP Integration**: Native `speak` tool and guidance prompts

### 🎤 Speech-to-Text (STT)
- **Faster-Whisper Engine**: Optimized Whisper implementation for real-time transcription
- **Real-time Processing**: Live typing during speech recognition
- **Multiple Output Modes**: Direct return, clipboard, or real-time typing
- **Language Support**: Multi-language speech recognition
- **Silence Detection**: Automatic stopping based on speech patterns

### ⌨️ Hotkey Monitoring & Voice Activation
- **Global hotkey support**: Monitor system-wide keyboard shortcuts
- **Menu key activation**: Configurable hotkey triggers for voice-to-text
- **Multi-Instance Coordination**: Cross-platform hotkey locking prevents conflicts between server instances
- **Real-time Feedback**: Audio cues (on/off sounds) and live typing
- **Hands-free operation**: Start/stop monitoring via MCP tools
- **Advanced Text Output**: Debounced typing, clipboard integration
- **Exclusive Processing**: Automatic lock acquisition ensures only one server processes each keystroke

### 🏗️ Architecture
- **FastMCP framework**: Modern MCP server implementation
- **Background Loading System**: Intelligent component preloading for fast startup and reduced latency
- **Type-safe**: Full type hints and validation with Pydantic
- **Advanced Audio Processing**: NumPy, LibROSA, WebRTC VAD integration with quality validation
- **Real-time Systems**: Optimized for low-latency voice interactions
- **Production-ready**: Comprehensive error handling, logging, and configuration management
- **Modular Design**: Separate managers for TTS, STT, audio, hotkeys, text output, and background loading
- **Cross-Process Coordination**: File-based and semaphore locking for multi-instance safety

## 🚀 Quick Start

### Prerequisites

- Python 3.12+ (required for advanced dependencies)
- Audio hardware (speakers/microphone for full functionality)
- Rust toolchain (for setuptools-rust)

### Installation

**Option 1: Install from PyPI (Recommended)**
```bash
# Install with uv (recommended)
uv add voice-mcp[audio]

# Or with pip
pip install voice-mcp[audio]
```

**Option 2: Development Installation**
```bash
# Clone and install
git clone https://github.com/regevbr/voice-mcp.git
cd voice-mcp
uv sync --extra audio --dev
```

> **⚠️ Important**: Use `[audio]` extras for full audio hardware support

### Usage

**For PyPI Installation:**
```bash
# Start MCP server
voice-mcp

# Test TTS functionality
python -c "
from voice_mcp.tools import VoiceTools
result = VoiceTools.speak('Hello from Voice MCP!')
print('TTS Result:', result)
"
```

**For Development Installation:**
```bash
# Start MCP server
uv run python -m voice_mcp.server

# Test TTS functionality
uv run python -c "
from voice_mcp.tools import VoiceTools
result = VoiceTools.speak('Hello from Voice MCP!')
print('TTS Result:', result)
"
```

### Claude Integration

**Claude Code CLI:**
```bash
claude add-mcp voice-mcp
```

**Claude Desktop JSON:**
```json
{
  "mcpServers": {
    "voice-mcp": {
      "command": "voice-mcp"
    }
  }
}
```

## 🛠️ MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `speak` | Convert text to speech | `text`, `voice`, `rate`, `volume` |
| `start_hotkey_monitoring` | Start global hotkey monitoring | None |
| `stop_hotkey_monitoring` | Stop global hotkey monitoring | None |
| `get_hotkey_status` | Get hotkey monitoring status | None |
| `get_loading_status` | Get background loading status for all components | None |

## 📚 Documentation

- [Installation Guide](installation.md) - Detailed setup instructions
- [Usage Examples](usage.md) - MCP integration and standalone usage
- [Configuration Options](configuration.md) - Environment variables and settings
- [API Reference](api.md) - Complete API documentation
