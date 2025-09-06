# Voice MCP Server

A comprehensive Model Context Protocol (MCP) server providing advanced text-to-speech (TTS) and speech-to-text (STT) capabilities with global hotkey monitoring for AI assistants.

[![Tests](https://github.com/voice-mcp/voice-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/voice-mcp/voice-mcp/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## ✨ Features

### 🔊 Text-to-Speech (TTS)
- **Coqui TTS Engine**: High-quality neural text-to-speech with customizable models
- **Voice customization**: Select voices, adjust rate and volume
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
- **Real-time Feedback**: Audio cues (on/off sounds) and live typing
- **Hands-free operation**: Start/stop monitoring via MCP tools
- **Advanced Text Output**: Debounced typing, clipboard integration

### 🏗️ Architecture
- **FastMCP framework**: Modern MCP server implementation
- **Type-safe**: Full type hints and validation with Pydantic
- **Advanced Audio Processing**: NumPy, LibROSA, WebRTC VAD integration
- **Real-time Systems**: Optimized for low-latency voice interactions
- **Production-ready**: Comprehensive error handling, logging, and configuration management
- **Modular Design**: Separate managers for TTS, STT, audio, hotkeys, and text output

## 🚀 Quick Start

### Prerequisites

- Python 3.12+ (required for advanced dependencies)
- Audio hardware (speakers/microphone for full functionality)
- Rust toolchain (for setuptools-rust)

### Installation

```bash
# Install with uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --extra audio --dev

# Or with pip
pip install -e .[audio]
```

### Usage

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

## 🛠️ MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `speak` | Convert text to speech | `text`, `voice`, `rate`, `volume` |
| `start_hotkey_monitoring` | Start global hotkey monitoring | None |
| `stop_hotkey_monitoring` | Stop global hotkey monitoring | None |
| `get_hotkey_status` | Get hotkey monitoring status | None |

## 📚 Documentation

- [Installation Guide](installation.md) - Detailed setup instructions
- [Usage Examples](usage.md) - MCP integration and standalone usage
- [Configuration Options](configuration.md) - Environment variables and settings
- [API Reference](api.md) - Complete API documentation
