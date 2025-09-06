"""
Voice MCP Server - Simplified version with only essential tools.
"""

import argparse
import atexit
import signal
import sys
from typing import Any

import structlog
from fastmcp import FastMCP

from .config import config, setup_logging
from .prompts import VoicePrompts
from .tools import VoiceTools
from .voice.stt import get_transcription_handler

logger = structlog.get_logger(__name__)

# Initialize MCP app with server info
mcp = FastMCP(
    name="Voice MCP Server",
    instructions="A Model Context Protocol server providing text-to-speech (TTS) capabilities and hotkey monitoring for AI assistants.",
    version="3.0.0",
)


# Cleanup function for hotkey monitoring and STT
def cleanup_resources():
    """Cleanup resources on server shutdown."""
    logger.info("Cleaning up server resources...")

    try:
        # Stop hotkey monitoring first
        if config.enable_hotkey:
            logger.debug("Stopping hotkey monitoring...")
            result = VoiceTools.stop_hotkey_monitoring()
            logger.debug(f"Hotkey stop result: {result}")

        # Cleanup STT resources
        logger.debug("Cleaning up STT resources...")
        stt_handler = get_transcription_handler()
        stt_handler.cleanup()

        # Additional cleanup for any module-level instances
        from .tools import _hotkey_manager, _text_output_controller

        if _hotkey_manager:
            logger.debug("Force cleanup hotkey manager...")
            _hotkey_manager.stop_monitoring()

        if _text_output_controller:
            logger.debug("Cleanup text output controller...")
            # No explicit cleanup needed for text output controller
            pass

        logger.info("Resource cleanup completed")

    except Exception as e:
        # Log the error but don't raise to avoid hanging during shutdown
        logger.warning(f"Error during resource cleanup: {e}")
        pass


# Register voice tools
@mcp.tool()
def speak(
    text: str,
    voice: str | None = None,
    rate: int | None = None,
    volume: float | None = None,
) -> str:
    """
    Convert text to speech using the configured TTS engine.

    Args:
        text: The text to convert to speech
        voice: Optional voice to use (system-dependent)
        rate: Optional speech rate (words per minute)
        volume: Optional volume level (0.0 to 1.0)

    Returns:
        Status message indicating success or failure
    """
    return VoiceTools.speak(text, voice, rate, volume)


# Register voice prompts
@mcp.prompt(name="speak")
def speak_guide() -> str:
    """Guide for using the speak tool effectively."""
    return VoicePrompts.speak_prompt()


# Hotkey management tools
@mcp.tool()
def start_hotkey_monitoring() -> str:
    """
    Start global hotkey monitoring for voice activation.

    Returns:
        Status message indicating success or failure of hotkey setup
    """
    return VoiceTools.start_hotkey_monitoring()


@mcp.tool()
def stop_hotkey_monitoring() -> str:
    """
    Stop global hotkey monitoring and cleanup resources.

    Returns:
        Status message indicating success or failure of hotkey cleanup
    """
    return VoiceTools.stop_hotkey_monitoring()


@mcp.tool()
def get_hotkey_status() -> dict[str, Any]:
    """
    Get current hotkey monitoring status and configuration details.

    Returns:
        Dictionary containing hotkey monitoring state, configured key combination,
        output mode settings, and any error conditions for debugging purposes.
    """
    return VoiceTools.get_hotkey_status()


# Setup cleanup on exit
atexit.register(cleanup_resources)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Voice MCP Server")

    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default=config.transport,
        help=f"Transport type (default: {config.transport})",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=config.port,
        help=f"Port to bind to (default: {config.port})",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=config.log_level,
        help=f"Log level (default: {config.log_level})",
    )

    parser.add_argument(
        "--debug", action="store_true", default=config.debug, help="Enable debug mode"
    )

    return parser.parse_args()


def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""

    def signal_handler(signum, _frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        cleanup_resources()
        sys.exit(0)

    # Handle termination signals
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

    # On Unix systems, also handle SIGHUP
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, signal_handler)


def main():
    """Main entry point for the MCP server."""
    args = parse_args()

    # Setup logging based on arguments
    setup_logging(args.log_level)

    # Setup signal handlers for graceful shutdown
    setup_signal_handlers()

    logger.info("Starting Voice MCP Server...")
    logger.info(f"Transport: {args.transport}")
    logger.info(f"Debug mode: {args.debug}")

    # Preload STT model if enabled
    if config.stt_enabled:
        logger.info("Preloading STT model on startup...")
        stt_handler = get_transcription_handler()
        if stt_handler.preload():
            logger.info("STT model preloaded successfully")
        else:
            logger.warning("STT model preload failed, will load on first use")

    # Start hotkey monitoring if enabled
    if config.enable_hotkey:
        logger.info("Starting hotkey monitoring on startup...")
        result = VoiceTools.start_hotkey_monitoring()
        logger.info(f"Hotkey startup: {result}")

    try:
        if args.transport == "stdio":
            mcp.run(transport="stdio")
        elif args.transport == "sse":
            mcp.run(transport="sse", host="localhost", port=args.port)
        else:
            logger.error(f"Unsupported transport: {args.transport}")
            cleanup_resources()
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        cleanup_resources()
    except Exception as e:
        logger.error(f"Server error: {e}")
        cleanup_resources()
        if args.debug:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
