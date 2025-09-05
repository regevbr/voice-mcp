"""
Configuration management for the Voice MCP server.
"""

import logging
import os
from dataclasses import dataclass


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
    tts_engine: str = "pyttsx3"  # pyttsx3, gtts
    tts_voice: str | None = None
    tts_rate: int = 200
    tts_volume: float = 0.9

    # STT settings
    stt_model: str = "base"  # tiny, base, small, medium, large
    stt_language: str = "en"  # Default language for STT
    stt_silence_threshold: float = 4.0
    stt_server_mode: bool = True  # Enable persistent model server mode
    stt_preload_models: list[str] = (
        None  # Which models to preload (None means use default ["base"])
    )
    stt_model_cache_size: int = 2  # Maximum number of models to keep in memory
    stt_model_timeout: int = 300  # Timeout for unused models (in seconds)
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
    def _parse_model_list(cls, model_str: str) -> list[str]:
        """Parse comma-separated model list from environment variable."""
        if not model_str:
            return ["base"]
        return [model.strip() for model in model_str.split(",") if model.strip()]

    def __post_init__(self):
        """Post-initialization to set default values for None fields."""
        if self.stt_preload_models is None:
            self.stt_preload_models = ["base"]

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv("VOICE_MCP_HOST", "localhost"),
            port=int(os.getenv("VOICE_MCP_PORT", "8000")),
            debug=os.getenv("VOICE_MCP_DEBUG", "false").lower() == "true",
            log_level=os.getenv("VOICE_MCP_LOG_LEVEL", "INFO"),
            transport=os.getenv("VOICE_MCP_TRANSPORT", "stdio"),
            tts_engine=os.getenv("VOICE_MCP_TTS_ENGINE", "pyttsx3"),
            tts_voice=os.getenv("VOICE_MCP_TTS_VOICE"),
            tts_rate=int(os.getenv("VOICE_MCP_TTS_RATE", "200")),
            tts_volume=float(os.getenv("VOICE_MCP_TTS_VOLUME", "0.9")),
            stt_model=os.getenv("VOICE_MCP_STT_MODEL", "base"),
            stt_language=os.getenv("VOICE_MCP_STT_LANGUAGE", "en"),
            stt_silence_threshold=float(
                os.getenv("VOICE_MCP_STT_SILENCE_THRESHOLD", "4.0")
            ),
            stt_server_mode=os.getenv("VOICE_MCP_STT_SERVER_MODE", "false").lower()
            == "true",
            stt_preload_models=cls._parse_model_list(
                os.getenv("VOICE_MCP_STT_PRELOAD_MODELS", "base")
            ),
            stt_model_cache_size=int(os.getenv("VOICE_MCP_STT_MODEL_CACHE_SIZE", "2")),
            stt_model_timeout=int(os.getenv("VOICE_MCP_STT_MODEL_TIMEOUT", "300")),
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
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# Global configuration instance
config = ServerConfig.from_env()
