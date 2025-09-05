# Voice MCP Server

A lightweight Model Context Protocol (MCP) server providing text-to-speech (TTS) capabilities and hotkey monitoring for AI assistants.

[![Tests](https://github.com/voice-mcp/voice-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/voice-mcp/voice-mcp/actions/workflows/test.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## ✨ Features

### 🔊 Text-to-Speech (TTS)
- **Multi-engine support**: pyttsx3 (offline) and gTTS (cloud) with automatic fallback
- **Voice customization**: Select voices, adjust rate and volume
- **Cross-platform**: Works on Linux, Windows, and macOS
- **MCP Integration**: Native `speak` tool and guidance prompts

### ⌨️ Hotkey Monitoring
- **Global hotkey support**: Monitor system-wide keyboard shortcuts
- **Menu key activation**: Configurable hotkey triggers for voice activation
- **Hands-free operation**: Start/stop monitoring via MCP tools

### 🏗️ Architecture
- **FastMCP framework**: Modern MCP server implementation
- **Type-safe**: Full type hints and validation with Pydantic
- **Focused functionality**: Streamlined tool set for core use cases
- **Production-ready**: Error handling, logging, and configuration management

## 🚀 Quick Start

### Prerequisites

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install python3-dev portaudio19-dev
```

**macOS:**
```bash
brew install portaudio
```

**Windows:**
- Install Python 3.11+ from [python.org](https://www.python.org/downloads/)
- Install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/voice-mcp/voice-mcp.git
cd voice-mcp
```

2. **Install with uv (recommended):**
```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project
uv sync --dev
```

3. **Alternative with pip:**
```bash
pip install -e .
```

### Usage

#### 1. MCP Server Mode (Claude Desktop Integration)

Create or update your Claude Desktop configuration:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "voice-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "voice_mcp.server"],
      "env": {
        "VOICE_MCP_TTS_ENGINE": "pyttsx3",
        "VOICE_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### 2. Standalone Server

```bash
# Start with stdio transport (default for MCP clients)
uv run python -m voice_mcp.server

# Start with SSE transport (HTTP-based)
uv run python -m voice_mcp.server --transport sse --port 8000

# Debug mode
uv run python -m voice_mcp.server --debug --log-level DEBUG
```

#### 3. CLI Interface

```bash
# Check version
uv run voice-mcp version

# Test TTS functionality
uv run voice-mcp test --tts --text "Hello, this is a test!"

# Get help
uv run voice-mcp --help
```

## 🛠️ MCP Tools & Prompts

### Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `speak` | Convert text to speech | `text`, `voice`, `rate`, `volume` |
| `start_hotkey_monitoring` | Start global hotkey monitoring | None |
| `stop_hotkey_monitoring` | Stop global hotkey monitoring | None |
| `get_hotkey_status` | Get hotkey monitoring status | None |

### Prompts

| Prompt | Description |
|--------|-------------|
| `speak_guide` | Instructions for using the speak tool |

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

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_MCP_HOST` | `localhost` | Server host |
| `VOICE_MCP_PORT` | `8000` | Server port |
| `VOICE_MCP_DEBUG` | `false` | Enable debug mode |
| `VOICE_MCP_LOG_LEVEL` | `INFO` | Logging level |
| `VOICE_MCP_TTS_ENGINE` | `pyttsx3` | TTS engine (`pyttsx3`, `gtts`) |
| `VOICE_MCP_TTS_RATE` | `200` | Speech rate (words per minute) |
| `VOICE_MCP_TTS_VOLUME` | `0.9` | Volume level (0.0 to 1.0) |
| `VOICE_MCP_ENABLE_HOTKEY` | `true` | Enable hotkey activation |
| `VOICE_MCP_HOTKEY_NAME` | `menu` | Hotkey to monitor |

### Example Configuration

```bash
# .env file
VOICE_MCP_TTS_ENGINE=pyttsx3
VOICE_MCP_TTS_RATE=180
VOICE_MCP_TTS_VOLUME=0.8
VOICE_MCP_ENABLE_HOTKEY=true
VOICE_MCP_HOTKEY_NAME=menu
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
# Format code
uv run black src/ tests/
uv run isort src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
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
```

## 📂 Project Structure

```
voice-mcp/
├── src/voice_mcp/
│   ├── __init__.py
│   ├── server.py          # Main MCP server
│   ├── config.py          # Configuration management
│   ├── tools.py           # MCP tools implementation
│   ├── prompts.py         # MCP prompts
│   ├── cli.py             # Command-line interface
│   └── voice/
│       ├── __init__.py
│       └── tts.py         # TTS engine implementations
├── tests/
│   ├── conftest.py        # Test configuration
│   ├── test_*.py          # Test modules
│   └── integration/       # Integration tests
├── pyproject.toml         # Project configuration
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
git clone https://github.com/voice-mcp/voice-mcp.git
cd voice-mcp
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install

# Run development server
uv run python -m voice_mcp.server --debug
```

## 🔧 Troubleshooting

### Common Issues

**Import Error: No module named 'pyttsx3'**
```bash
# Reinstall dependencies
uv sync --reinstall
```

**Audio playback not working**
```bash
# Linux: Install audio libraries
sudo apt-get install alsa-utils pulseaudio

# macOS: Check audio permissions
# System Preferences > Security & Privacy > Microphone/Camera
```

**TTS engine initialization failed**
```bash
# Check available voices
uv run python -c "
import pyttsx3
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for voice in voices:
    print(f'ID: {voice.id}, Name: {voice.name}')
"
```

**FastMCP errors**
- Ensure you're using Python 3.11+
- Check MCP package version: `uv list | grep mcp`

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://github.com/modelcontextprotocol) - MCP specification and tools
- [whisper-typer-tool](https://github.com/dynamiccreator/whisper-typer-tool) - Inspiration for STT integration
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3) - Cross-platform TTS library
- [gTTS](https://github.com/pndurette/gTTS) - Google Text-to-Speech
- [FastMCP](https://github.com/modelcontextprotocol/python-sdk) - Fast MCP server framework

## 🗺️ Roadmap

- [x] **Phase 1**: MCP server foundation with FastMCP
- [x] **Phase 2**: Text-to-Speech implementation  
- [x] **Phase 3**: Hotkey monitoring and core functionality
- [x] **Phase 4**: Streamlined tool set and focused architecture
- [ ] **Phase 5**: Enhanced voice features and production optimization

---

**Ready to give your AI assistant a voice? 🎉**