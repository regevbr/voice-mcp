#!/usr/bin/env python3
"""
Command line interface for Voice MCP server management.
"""

import argparse
import sys
from typing import List, Optional

from .server import main as server_main


def create_parser() -> argparse.ArgumentParser:
    """Create the main CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="voice-mcp",
        description="Voice MCP Server - Management CLI"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start the MCP server")
    server_parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport type (default: stdio)"
    )
    server_parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind to (default: localhost)"
    )
    server_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    server_parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)"
    )
    server_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test voice functionality")
    test_parser.add_argument(
        "--tts",
        action="store_true",
        help="Test text-to-speech"
    )
    test_parser.add_argument(
        "--stt",
        action="store_true",
        help="Test speech-to-text"
    )
    test_parser.add_argument(
        "--text",
        default="Hello, this is a test of the voice MCP server.",
        help="Text to speak for TTS test"
    )
    
    return parser


def handle_server_command(args: argparse.Namespace) -> int:
    """Handle the server command."""
    # Modify sys.argv to pass arguments to server_main
    original_argv = sys.argv[:]
    sys.argv = ["voice-mcp"]
    
    if args.transport:
        sys.argv.extend(["--transport", args.transport])
    if args.host:
        sys.argv.extend(["--host", args.host])
    if args.port:
        sys.argv.extend(["--port", str(args.port)])
    if args.log_level:
        sys.argv.extend(["--log-level", args.log_level])
    if args.debug:
        sys.argv.append("--debug")
    
    try:
        server_main()
        return 0
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1
    finally:
        sys.argv = original_argv


def handle_version_command(args: argparse.Namespace) -> int:
    """Handle the version command."""
    from . import __version__
    print(f"Voice MCP Server v{__version__}")
    return 0


def handle_test_command(args: argparse.Namespace) -> int:
    """Handle the test command."""
    print("Voice MCP Test Suite")
    print("=" * 40)
    
    if args.tts or (not args.tts and not args.stt):
        print("\n🔊 Testing Text-to-Speech...")
        try:
            from .tools import VoiceTools
            result = VoiceTools.speak(args.text)
            print(f"TTS Result: {result}")
        except Exception as e:
            print(f"TTS Error: {e}")
    
    if args.stt or (not args.tts and not args.stt):
        print("\n🎤 Testing Speech-to-Text...")
        try:
            from .tools import VoiceTools
            result = VoiceTools.listen(5.0)  # 5 second test
            print(f"STT Result: {result}")
        except Exception as e:
            print(f"STT Error: {e}")
    
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == "server":
        return handle_server_command(args)
    elif args.command == "version":
        return handle_version_command(args)
    elif args.command == "test":
        return handle_test_command(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())