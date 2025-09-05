# Voice MCP Server

Voice MCP Server is a comprehensive Python implementation of a Model Context Protocol (MCP) server providing advanced text-to-speech (TTS), speech-to-text (STT), and global hotkey monitoring for AI assistants.

## Features

- **Text-to-Speech (TTS)**: High-quality neural speech synthesis using Coqui TTS
- **Speech-to-Text (STT)**: Real-time transcription with faster-whisper
- **Global Hotkey Monitoring**: Voice activation through keyboard shortcuts
- **MCP Integration**: Seamless integration with Claude and other AI assistants
- **Production Ready**: Comprehensive error handling, logging, and configuration

## Quick Start

```bash
pip install voice-mcp[audio]
voice-mcp
```

See the [Installation](installation.md) guide for detailed setup instructions.

## Architecture

The server is built on the FastMCP framework and provides:

- Complete MCP tool implementations for voice functionality
- Real-time audio processing pipeline
- Environment-based configuration management
- Optional audio dependencies for CI environments

## Documentation

- [Installation Guide](installation.md)
- [Usage Examples](usage.md)
- [Configuration Options](configuration.md)
- [API Reference](api.md)
