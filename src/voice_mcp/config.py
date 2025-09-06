"""
Configuration management for the Voice MCP server.
"""

import logging
import os
from dataclasses import dataclass

import structlog


@dataclass
class ServerConfig:
    """Configuration settings for the MCP server."""

    # Server settings
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"
    transport: str = "stdio"

    # TTS settings
    tts_model: str = "tts_models/en/ljspeech/tacotron2-DDC"  # Coqui TTS model to use
    tts_rate: float = 1.0  # Speed multiplier (not implemented yet)
    tts_volume: float = 0.9  # Volume level (not implemented yet)

    # STT settings
    stt_enabled: bool = True  # Enable STT preloading on startup
    stt_model: str = "base"  # tiny, base, small, medium, large
    stt_device: str = "auto"  # auto, cuda, cpu
    stt_language: str = "en"  # Default language for STT
    stt_silence_threshold: float = 3.0
    enable_hotkey: bool = True  # Enable/disable hotkey monitoring
    hotkey_name: str = "menu"  # Which key to use (menu, f12, ctrl+alt+s, etc.)
    hotkey_output_mode: str = "typing"  # Default output mode when hotkey is used

    # Text output settings
    typing_enabled: bool = True
    clipboard_enabled: bool = True
    typing_debounce_delay: float = 0.1

    # Audio settings
    sample_rate: int = 16000
    chunk_size: int = 1024

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv("VOICE_MCP_HOST", "localhost"),
            port=int(os.getenv("VOICE_MCP_PORT", "8000")),
            debug=os.getenv("VOICE_MCP_DEBUG", "false").lower() == "true",
            log_level=os.getenv("VOICE_MCP_LOG_LEVEL", "INFO"),
            transport=os.getenv("VOICE_MCP_TRANSPORT", "stdio"),
            tts_model=os.getenv(
                "VOICE_MCP_TTS_MODEL", "tts_models/en/ljspeech/tacotron2-DDC"
            ),
            tts_rate=float(os.getenv("VOICE_MCP_TTS_RATE", "1.0")),
            tts_volume=float(os.getenv("VOICE_MCP_TTS_VOLUME", "0.9")),
            stt_enabled=os.getenv("VOICE_MCP_STT_ENABLED", "true").lower() == "true",
            stt_model=os.getenv("VOICE_MCP_STT_MODEL", "base"),
            stt_device=os.getenv("VOICE_MCP_STT_DEVICE", "auto"),
            stt_language=os.getenv("VOICE_MCP_STT_LANGUAGE", "en"),
            stt_silence_threshold=float(
                os.getenv("VOICE_MCP_STT_SILENCE_THRESHOLD", "3.0")
            ),
            enable_hotkey=os.getenv("VOICE_MCP_ENABLE_HOTKEY", "true").lower()
            == "true",
            hotkey_name=os.getenv("VOICE_MCP_HOTKEY_NAME", "menu"),
            hotkey_output_mode=os.getenv("VOICE_MCP_HOTKEY_OUTPUT_MODE", "typing"),
            typing_enabled=os.getenv("VOICE_MCP_TYPING_ENABLED", "true").lower()
            == "true",
            clipboard_enabled=os.getenv("VOICE_MCP_CLIPBOARD_ENABLED", "true").lower()
            == "true",
            typing_debounce_delay=float(
                os.getenv("VOICE_MCP_TYPING_DEBOUNCE_DELAY", "0.1")
            ),
            sample_rate=int(os.getenv("VOICE_MCP_SAMPLE_RATE", "16000")),
            chunk_size=int(os.getenv("VOICE_MCP_CHUNK_SIZE", "1024")),
        )


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration."""
    # Configure Python's standard logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure structlog to use Python's standard logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Set the root logger level to ensure structlog respects it
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))


# Global configuration instance
config = ServerConfig.from_env()
