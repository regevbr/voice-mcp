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
- **Multi-Model Support**: Dynamic sample rate detection for different TTS models (Tacotron2, XTTS)
- **Voice Customization**: Select voices, adjust rate and volume with distortion-free output
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

## 📚 Documentation

For detailed documentation, API reference, and examples, visit our [GitHub repository](https://github.com/regevbr/voice-mcp).

## 🚀 Quick Start

### Prerequisites

**Python Requirements:**
- Python 3.12+ (required for advanced dependencies)
- Rust toolchain (for setuptools-rust)

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install python3-dev portaudio19-dev libasound2-dev
sudo apt-get install build-essential cmake
# For audio processing
sudo apt-get install ffmpeg libsndfile1
```

**macOS:**
```bash
brew install portaudio ffmpeg libsndfile
# Install Rust if not present
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

**Windows:**
- Install Python 3.12+ from [python.org](https://www.python.org/downloads/)
- Install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- Install [Rust toolchain](https://rustup.rs/)
- Install [FFmpeg](https://ffmpeg.org/download.html) and add to PATH

### Installation

#### Option 1: Install from PyPI (Recommended)

```bash
# Install with uv (recommended)
uv add voice-mcp[audio]

# Alternative with pip
pip install voice-mcp[audio]
```

> **⚠️ Important**: Use `[audio]` extras to get full audio hardware support (PyAudio, RealtimeSTT). Without it, you'll get TTS functionality but may encounter audio I/O issues.

#### Option 2: Development Installation

1. **Clone the repository:**
```bash
git clone https://github.com/regevbr/voice-mcp.git
cd voice-mcp
```

2. **Install with uv:**
```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project with all audio dependencies
uv sync --extra audio --dev
```

3. **Alternative with pip:**
```bash
pip install -e .[audio]
```

### Usage

#### 1. Claude Desktop Integration

Create or update your Claude Desktop configuration:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**For PyPI Installation (Recommended):**
```json
{
  "mcpServers": {
    "voice-mcp": {
      "command": "voice-mcp",
      "env": {
        "VOICE_MCP_TTS_MODEL": "tts_models/en/ljspeech/tacotron2-DDC",
        "VOICE_MCP_TTS_PRELOAD_ENABLED": "true",
        "VOICE_MCP_STT_ENABLED": "true",
        "VOICE_MCP_ENABLE_HOTKEY": "true",
        "VOICE_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**For Development Installation:**
```json
{
  "mcpServers": {
    "voice-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "voice_mcp.server"],
      "env": {
        "VOICE_MCP_TTS_MODEL": "tts_models/en/ljspeech/tacotron2-DDC",
        "VOICE_MCP_TTS_PRELOAD_ENABLED": "true",
        "VOICE_MCP_STT_ENABLED": "true",
        "VOICE_MCP_ENABLE_HOTKEY": "true",
        "VOICE_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### 2. Claude Code Integration

**Option A: Using Claude Code CLI (Recommended):**
```bash
# Add MCP server using Claude Code CLI
claude add-mcp voice-mcp

# Or with specific configuration
claude add-mcp voice-mcp \
  --env VOICE_MCP_TTS_MODEL=tts_models/en/ljspeech/tacotron2-DDC \
  --env VOICE_MCP_TTS_PRELOAD_ENABLED=true \
  --env VOICE_MCP_STT_ENABLED=true \
  --env VOICE_MCP_ENABLE_HOTKEY=true \
  --env VOICE_MCP_LOG_LEVEL=INFO
```

**Option B: Manual Configuration File:**

Create or update `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "voice-mcp": {
      "command": "voice-mcp",
      "env": {
        "VOICE_MCP_TTS_MODEL": "tts_models/en/ljspeech/tacotron2-DDC",
        "VOICE_MCP_TTS_PRELOAD_ENABLED": "true",
        "VOICE_MCP_STT_ENABLED": "true",
        "VOICE_MCP_ENABLE_HOTKEY": "true",
        "VOICE_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### 3. Standalone Server

**For PyPI Installation:**
```bash
# Start with stdio transport (default for MCP clients)
voice-mcp

# Start with SSE transport (HTTP-based)
voice-mcp --transport sse --port 8000

# Debug mode
voice-mcp --debug --log-level DEBUG
```

**For Development Installation:**
```bash
# Start with stdio transport (default for MCP clients)
uv run python -m voice_mcp.server

# Start with SSE transport (HTTP-based)
uv run python -m voice_mcp.server --transport sse --port 8000

# Debug mode
uv run python -m voice_mcp.server --debug --log-level DEBUG
```

#### 3. Direct Testing

```bash
# Test TTS functionality directly
uv run python -c "
from voice_mcp.tools import VoiceTools
result = VoiceTools.speak('Hello from Voice MCP!')
print('TTS Result:', result)
"

# Test hotkey status
uv run python -c "
from voice_mcp.tools import VoiceTools
status = VoiceTools.get_hotkey_status()
print('Hotkey Status:', status['active'])
"

# Test background loading status
uv run python -c "
from voice_mcp.tools import VoiceTools
status = VoiceTools.get_loading_status()
print('Loading Status:', status['summary'])
"
```

## 🛠️ MCP Tools & Prompts

### Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `speak` | Convert text to speech | `text`, `voice`, `rate`, `volume` |
| `start_hotkey_monitoring` | Start global hotkey monitoring | None |
| `stop_hotkey_monitoring` | Stop global hotkey monitoring | None |
| `get_hotkey_status` | Get hotkey monitoring status | None |
| `get_loading_status` | Get background loading status for all components | None |

### Prompts

| Prompt | Description |
|--------|-------------|
| `speak` | Instructions for using the speak tool |

### Example Usage in Claude

**Text-to-Speech:**
```
Human: Please speak this message: "Hello! The voice MCP server is working perfectly."

Claude: I'll use the speak tool to convert your message to speech.

*Uses speak tool with text: "Hello! The voice MCP server is working perfectly."*

✅ Successfully spoke: 'Hello! The voice MCP server is working perfectly...'
```

**Hotkey Management:**
```
Human: Start monitoring the hotkey for voice activation.

Claude: I'll start the global hotkey monitoring for you.

*Uses start_hotkey_monitoring tool*

✅ Hotkey monitoring started (menu key)
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default                                | Description |
|----------|----------------------------------------|-------------|
| `VOICE_MCP_HOST` | `localhost`                            | Server host |
| `VOICE_MCP_PORT` | `8000`                                 | Server port |
| `VOICE_MCP_DEBUG` | `false`                                | Enable debug mode |
| `VOICE_MCP_LOG_LEVEL` | `INFO`                                 | Logging level |
| `VOICE_MCP_TTS_MODEL` | `tts_models/en/ljspeech/tacotron2-DDC` | Coqui TTS model |
| `VOICE_MCP_TTS_PRELOAD_ENABLED` | `true`                                 | Enable TTS model preloading on startup |
| `VOICE_MCP_TTS_GPU_ENABLED` | `false`                                | Enable GPU acceleration for TTS |
| `VOICE_MCP_TTS_RATE` | `1.0`                                  | Speech rate multiplier (>1.0 = faster, <1.0 = slower) |
| `VOICE_MCP_TTS_VOLUME` | `0.9`                                  | Volume level (0.0 to 1.0) |
| `VOICE_MCP_STT_ENABLED` | `true`                                 | Enable STT preloading on startup |
| `VOICE_MCP_STT_MODEL` | `base`                                 | Whisper model (`tiny`, `base`, `small`, `medium`, `large`) |
| `VOICE_MCP_STT_DEVICE` | `auto`                                 | Processing device (`auto`, `cuda`, `cpu`) |
| `VOICE_MCP_STT_LANGUAGE` | `en`                                   | Default STT language |
| `VOICE_MCP_STT_SILENCE_THRESHOLD` | `2.0`                                  | Silence detection threshold (seconds, reduced from 3.0s) |
| `VOICE_MCP_ENABLE_HOTKEY` | `true`                                 | Enable hotkey activation |
| `VOICE_MCP_HOTKEY_NAME` | `menu`                                 | Hotkey to monitor |
| `VOICE_MCP_HOTKEY_OUTPUT_MODE` | `typing`                               | Default hotkey output mode (`typing`, `clipboard`, `return`) |
| `VOICE_MCP_TYPING_ENABLED` | `true`                                 | Enable real-time typing output |
| `VOICE_MCP_CLIPBOARD_ENABLED` | `true`                                 | Enable clipboard output |
| `VOICE_MCP_TYPING_DEBOUNCE_DELAY` | `0.1`                                  | Typing debounce delay (seconds) |
| **Hotkey Lock Configuration** | | |
| `VOICE_MCP_HOTKEY_LOCK_ENABLED` | `true` | Enable cross-process hotkey locking |
| `VOICE_MCP_HOTKEY_LOCK_DIRECTORY` | `auto` | Custom lock directory (auto-detect if not set) |
| `VOICE_MCP_HOTKEY_LOCK_FALLBACK_SEMAPHORE` | `true` | Allow semaphore fallback if file locks fail |
| **Audio Quality Configuration** | | |
| `VOICE_MCP_AUDIO_QUALITY_VALIDATION_ENABLED` | `true` | Enable audio quality validation |
| `VOICE_MCP_AUDIO_QUALITY_MODE` | `balanced` | Audio quality mode (fast, balanced, high_quality) |
| `VOICE_MCP_AUDIO_NORMALIZATION_HEADROOM` | `0.95` | Normalization headroom (0.0-1.0) |

### Example Configuration

```bash
# .env file
# TTS Configuration
VOICE_MCP_TTS_MODEL=tts_models/en/ljspeech/tacotron2-DDC
VOICE_MCP_TTS_PRELOAD_ENABLED=true
VOICE_MCP_TTS_GPU_ENABLED=false
VOICE_MCP_TTS_RATE=1.0
VOICE_MCP_TTS_VOLUME=0.8

# STT Configuration
VOICE_MCP_STT_ENABLED=true
VOICE_MCP_STT_MODEL=base
VOICE_MCP_STT_DEVICE=auto
VOICE_MCP_STT_SILENCE_THRESHOLD=2.0

# Hotkey Configuration
VOICE_MCP_ENABLE_HOTKEY=true
VOICE_MCP_HOTKEY_NAME=menu
VOICE_MCP_HOTKEY_OUTPUT_MODE=typing
VOICE_MCP_HOTKEY_LOCK_ENABLED=true

# Audio Quality Configuration
VOICE_MCP_AUDIO_QUALITY_VALIDATION_ENABLED=true
VOICE_MCP_AUDIO_QUALITY_MODE=balanced
VOICE_MCP_AUDIO_NORMALIZATION_HEADROOM=0.95

# General Configuration
VOICE_MCP_LOG_LEVEL=DEBUG
```

## 🧪 Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=voice_mcp --cov-report=html

# Run specific test categories
uv run pytest -m "not voice"  # Skip hardware-dependent tests
uv run pytest tests/test_tts.py -v  # TTS tests only
```

### Code Quality

```bash
# Format code (recommended single command)
./scripts/format.sh

# Lint code
./scripts/lint.sh

# Type checking
./scripts/typecheck.sh

# Run all quality checks
./scripts/check-all.sh

# Alternative individual commands
uv run ruff format src/ tests/  # Primary formatter
uv run isort src/ tests/        # Import sorting
uv run ruff check src/ tests/   # Linting
uv run mypy src/               # Type checking
```

### Testing Core Functionality

```bash
# Test TTS functionality directly
uv run python -c "
from voice_mcp.tools import VoiceTools
result = VoiceTools.speak('Hello from Voice MCP!')
print('TTS Result:', result)
"

# Test hotkey monitoring
uv run python -c "
from voice_mcp.tools import VoiceTools
status = VoiceTools.get_hotkey_status()
print('Hotkey Status:', status)
"

# Test background loading coordination
uv run python -c "
from voice_mcp.tools import VoiceTools
status = VoiceTools.get_loading_status()
print('All components ready:', status['summary']['all_ready'])
print('Loading details:', status)
"
```

## 📂 Project Structure

```
voice-mcp/
├── src/voice_mcp/
│   ├── __init__.py
│   ├── server.py          # Main MCP server with FastMCP
│   ├── config.py          # Configuration management
│   ├── tools.py           # MCP tools implementation
│   ├── prompts.py         # MCP prompts
│   ├── loading.py         # Background loading state management
│   ├── cli.py             # Command-line interface (partial)
│   └── voice/
│       ├── __init__.py
│       ├── audio.py       # Audio I/O and effects management
│       ├── hotkey.py      # Global hotkey monitoring
│       ├── hotkey_lock.py # Cross-platform hotkey locking system
│       ├── stt.py         # Speech-to-text with faster-whisper
│       ├── stt_server.py  # STT server implementation
│       ├── text_output.py # Real-time typing and clipboard
│       └── tts.py         # Coqui TTS engine with audio quality pipeline
├── tests/
│   ├── conftest.py        # Test configuration
│   ├── test_*.py          # Comprehensive test suite (82% coverage)
│   ├── test_hotkey_lock.py # Cross-platform locking tests
│   ├── test_audio_quality.py # Audio quality validation tests
│   ├── integration/       # Integration tests
│   └── unit/              # Unit tests
├── examples/
│   ├── hotkey_demo.py     # Hotkey usage examples
│   └── stt_server_demo.py # STT server examples
├── scripts/
│   ├── format.sh          # Code formatting with Ruff
│   ├── lint.sh            # Linting with Ruff
│   ├── typecheck.sh       # Type checking with mypy
│   ├── test.sh            # Test execution
│   └── check-all.sh       # All quality checks
├── pyproject.toml         # Project configuration
├── CHANGELOG.md           # Version history
└── README.md
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the test suite (`uv run pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Clone and setup
git clone https://github.com/regevbr/voice-mcp.git
cd voice-mcp
uv sync --extra audio --dev

# Install pre-commit hooks (if available)
uv run pre-commit install

# Run development server
uv run python -m voice_mcp.server --debug
```

## 🔧 Troubleshooting

### Common Issues

**PyPI Installation Issues**

If you get limited functionality or audio errors after `pip install voice-mcp`:
```bash
# Reinstall with audio extras (recommended)
pip uninstall voice-mcp
pip install voice-mcp[audio]

# Or with uv
uv remove voice-mcp
uv add voice-mcp[audio]
```

**Import Error: No module named 'TTS', 'faster_whisper', or 'pyaudio'**
```bash
# For PyPI installation
pip install voice-mcp[audio]

# For development installation
uv sync --extra audio --reinstall

# On Linux, ensure build dependencies
sudo apt-get install build-essential cmake
```

**Audio Extras vs Base Installation**

| Installation | TTS | STT | Audio I/O | Hotkeys | Use Case |
|--------------|-----|-----|-----------|---------|----------|
| `voice-mcp` | ✅ | ✅ | ⚠️ Limited | ✅ | Basic TTS, may have audio issues |
| `voice-mcp[audio]` | ✅ | ✅ | ✅ Full | ✅ | Complete functionality (recommended) |

> **Recommendation**: Always use `voice-mcp[audio]` for full functionality

**Audio playback not working**
```bash
# Linux: Install audio libraries
sudo apt-get install alsa-utils pulseaudio

# macOS: Check audio permissions
# System Preferences > Security & Privacy > Microphone/Camera
```

**TTS engine initialization failed**
```bash
# Check Coqui TTS installation and models
uv run python -c "
from TTS.api import TTS
print('Available models:')
for model in TTS.list_models():
    print(f'- {model}')
"

# Test TTS functionality
uv run python -c "
from voice_mcp.tools import VoiceTools
result = VoiceTools.speak('Test message')
print(result)
"
```

**FastMCP errors**
- Ensure you're using Python 3.12+
- Check MCP package version: `uv list | grep mcp`

**STT/Audio Issues**
```bash
# Test microphone access
uv run python -c "
import pyaudio
p = pyaudio.PyAudio()
print(f'Available audio devices: {p.get_device_count()}')
p.terminate()
"

# Check faster-whisper installation
uv run python -c "
from faster_whisper import WhisperModel
model = WhisperModel('base')
print('Faster-whisper working!')
"
```

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [whisper-typer-tool](https://github.com/dynamiccreator/whisper-typer-tool) - Inspiration for STT integration patterns
- [mcp-voice-hooks](https://github.com/johnmatthewtennant/mcp-voice-hooks) - Inspiration for TTS integration patterns
- [FastMCP](https://github.com/jlowin/fastmcp) - Modern MCP server framework
- [Coqui TTS](https://github.com/coqui-ai/TTS) - High-quality neural text-to-speech

---

**Ready to give your AI assistant a voice? 🎉**
