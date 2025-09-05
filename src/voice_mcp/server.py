"""
Voice MCP Server - Simplified version with only essential tools.
"""

import sys
import time
import argparse
import atexit
from typing import Dict, Any, Optional, Union, Literal

import structlog
from fastmcp import FastMCP

from .tools import VoiceTools
from .prompts import VoicePrompts
from .config import config, setup_logging

logger = structlog.get_logger(__name__)

# Initialize MCP app with server info
mcp = FastMCP(
    name="Voice MCP Server",
    instructions="A Model Context Protocol server providing text-to-speech (TTS) capabilities and hotkey monitoring for AI assistants.",
    version="3.0.0"
)


# Cleanup function for hotkey monitoring
def cleanup_hotkey_monitoring():
    """Cleanup hotkey monitoring on server shutdown."""
    try:
        if config.enable_hotkey:
            logger.info("Cleaning up hotkey monitoring...")
            result = VoiceTools.stop_hotkey_monitoring()
            logger.info(f"Hotkey cleanup: {result}")
    except Exception as e:
        logger.debug(f"Error during cleanup: {e}")


# Register voice tools
@mcp.tool()
def speak(
    text: str, 
    voice: Optional[str] = None, 
    rate: Optional[int] = None, 
    volume: Optional[float] = None
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
@mcp.prompt()
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
def get_hotkey_status() -> Dict[str, Any]:
    """
    Get current hotkey monitoring status and configuration details.
    
    Returns:
        Dictionary containing hotkey monitoring state, configured key combination,
        output mode settings, and any error conditions for debugging purposes.
    """
    return VoiceTools.get_hotkey_status()


# Setup cleanup on exit
atexit.register(cleanup_hotkey_monitoring)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Voice MCP Server")
    
    parser.add_argument(
        "--transport", 
        choices=["stdio", "sse"],
        default=config.transport,
        help=f"Transport type (default: {config.transport})"
    )
    
    parser.add_argument(
        "--port", 
        type=int,
        default=config.port,
        help=f"Port to bind to (default: {config.port})"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=config.log_level,
        help=f"Log level (default: {config.log_level})"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true", 
        default=config.debug,
        help="Enable debug mode"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the MCP server."""
    args = parse_args()
    
    # Setup logging based on arguments
    setup_logging(args.log_level)
    
    logger.info("Starting Voice MCP Server...")
    logger.info(f"Transport: {args.transport}")
    logger.info(f"Debug mode: {args.debug}")
    
    try:
        if args.transport == "stdio":
            mcp.run(transport="stdio")
        elif args.transport == "sse":
            mcp.run(transport="sse", host="localhost", port=args.port)
        else:
            logger.error(f"Unsupported transport: {args.transport}")
            cleanup_hotkey_monitoring()
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        cleanup_hotkey_monitoring()
    except Exception as e:
        logger.error(f"Server error: {e}")
        cleanup_hotkey_monitoring()
        if args.debug:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()