# Installation

## Prerequisites

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

## Installation Methods

### 1. PyPI Installation (Recommended)

```bash
# Install with uv (recommended)
uv add voice-mcp[audio]

# Alternative with pip
pip install voice-mcp[audio]
```

> **⚠️ Important**: Use `[audio]` extras to get full audio hardware support (PyAudio, RealtimeSTT). Without it, you'll get TTS functionality but may encounter audio I/O issues.

**Audio Extras vs Base Installation**

| Installation | TTS | STT | Audio I/O | Hotkeys | Use Case |
|--------------|-----|-----|-----------|---------|----------|
| `voice-mcp` | ✅ | ✅ | ⚠️ Limited | ✅ | Basic TTS, may have audio issues |
| `voice-mcp[audio]` | ✅ | ✅ | ✅ Full | ✅ | Complete functionality (recommended) |

### 2. Development Installation

```bash
# Clone the repository
git clone https://github.com/voice-mcp/voice-mcp.git
cd voice-mcp

# Install with uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --extra audio --dev
```

### 3. Alternative Package Installation

```bash
# Full installation with audio dependencies (development mode)
pip install -e .[audio]

# Direct git installation
pip install git+https://github.com/voice-mcp/voice-mcp.git[audio]
```

### 4. Docker Installation

```bash
# Build and run with Docker
docker build -t voice-mcp .
docker run --rm -p 8000:8000 voice-mcp
```

## MCP Client Configuration

### Claude Desktop Integration

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
        "VOICE_MCP_STT_ENABLED": "true",
        "VOICE_MCP_ENABLE_HOTKEY": "true",
        "VOICE_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Claude Code Integration

**Option A: Using Claude Code CLI (Recommended):**
```bash
# Add MCP server using Claude Code CLI
claude add-mcp voice-mcp

# Or with specific configuration
claude add-mcp voice-mcp \
  --env VOICE_MCP_TTS_MODEL=tts_models/en/ljspeech/tacotron2-DDC \
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
        "VOICE_MCP_STT_ENABLED": "true",
        "VOICE_MCP_ENABLE_HOTKEY": "true",
        "VOICE_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Standalone Server

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

## Verification

### Test Core Functionality

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
```

### Test Dependencies

```bash
# Check Coqui TTS installation
uv run python -c "
from TTS.api import TTS
print('✅ Coqui TTS working')
"

# Check faster-whisper installation
uv run python -c "
from faster_whisper import WhisperModel
model = WhisperModel('base')
print('✅ Faster-whisper working')
"

# Check audio access
uv run python -c "
import pyaudio
p = pyaudio.PyAudio()
print(f'✅ Audio devices available: {p.get_device_count()}')
p.terminate()
"
```

## Troubleshooting

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
python -c "
from TTS.api import TTS
print('Available models:')
for model in TTS.list_models():
    print(f'- {model}')
"
```

**FastMCP errors**
- Ensure you're using Python 3.12+
- Check MCP package version: `pip list | grep mcp`

**Build failures on Windows**
- Install Microsoft Visual C++ Build Tools
- Install Rust toolchain
- Use Python 3.12 from python.org (not Microsoft Store)

### Installation Comparison

| Method | TTS | STT | Audio I/O | Hotkeys | Installation Command |
|--------|-----|-----|-----------|---------|---------------------|
| **PyPI (Recommended)** | ✅ | ✅ | ✅ Full | ✅ | `pip install voice-mcp[audio]` |
| **PyPI Basic** | ✅ | ✅ | ⚠️ Limited | ✅ | `pip install voice-mcp` |
| **Development** | ✅ | ✅ | ✅ Full | ✅ | `git clone` + `uv sync --extra audio` |
| **Git Direct** | ✅ | ✅ | ✅ Full | ✅ | `pip install git+https://...` |

> **Recommendation**: Always use `voice-mcp[audio]` for complete functionality.
