# Installation

## Requirements

- Python 3.12 or higher
- Audio hardware (speakers/microphone for full functionality)

## Basic Installation

For basic MCP server functionality without audio hardware:

```bash
pip install voice-mcp
```

## Full Audio Installation

For complete voice functionality including TTS and STT:

```bash
pip install voice-mcp[audio]
```

This includes:
- PyAudio for audio I/O
- RealtimeSTT for speech recognition
- All audio processing dependencies

## Development Installation

For development with all tools:

```bash
git clone https://github.com/regevbr/voice-mcp.git
cd voice-mcp
uv sync --dev
```

## System Dependencies

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install portaudio19-dev python3-dev
```

### macOS
```bash
brew install portaudio
```

### Windows
Audio dependencies are included in the wheel packages.

## Verification

Test the installation:

```bash
python -c "from voice_mcp.tools import VoiceTools; print('✅ Installation successful')"
```
