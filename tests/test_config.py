"""
Tests for configuration management.
"""

from voice_mcp.config import ServerConfig


def test_default_config():
    """Test default configuration values."""
    config = ServerConfig()

    assert config.host == "localhost"
    assert config.port == 8000
    assert config.debug is False
    assert config.log_level == "INFO"
    assert config.tts_model == "tts_models/en/ljspeech/tacotron2-DDC"
    assert config.tts_rate == 1.0
    assert config.tts_volume == 0.9
    assert config.stt_model == "base"
    assert config.stt_language == "en"
    assert config.stt_silence_threshold == 3.0
    assert config.typing_enabled is True
    assert config.clipboard_enabled is True
    assert config.enable_hotkey is True  # Default is now True
    assert config.hotkey_name == "menu"
    assert config.hotkey_output_mode == "typing"
    assert config.sample_rate == 16000
    assert config.chunk_size == 1024


def test_config_from_env(monkeypatch):
    """Test configuration from environment variables."""
    # Set environment variables
    monkeypatch.setenv("VOICE_MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("VOICE_MCP_PORT", "9000")
    monkeypatch.setenv("VOICE_MCP_DEBUG", "true")
    monkeypatch.setenv("VOICE_MCP_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("VOICE_MCP_TTS_MODEL", "some_model")
    monkeypatch.setenv("VOICE_MCP_TTS_RATE", "1.5")
    monkeypatch.setenv("VOICE_MCP_TTS_VOLUME", "0.7")
    monkeypatch.setenv("VOICE_MCP_STT_MODEL", "base")
    monkeypatch.setenv("VOICE_MCP_STT_SILENCE_THRESHOLD", "2.0")
    monkeypatch.setenv("VOICE_MCP_ENABLE_HOTKEY", "true")  # Enable for this test
    monkeypatch.setenv("VOICE_MCP_HOTKEY_NAME", "f11")
    monkeypatch.setenv("VOICE_MCP_HOTKEY_OUTPUT_MODE", "clipboard")

    config = ServerConfig.from_env()

    assert config.host == "0.0.0.0"
    assert config.port == 9000
    assert config.debug is True
    assert config.log_level == "DEBUG"
    assert config.tts_model == "some_model"
    assert config.tts_rate == 1.5
    assert config.tts_volume == 0.7
    assert config.stt_model == "base"
    assert config.stt_silence_threshold == 2.0
    assert config.enable_hotkey is True  # Should be True from env var
    assert config.hotkey_name == "f11"
    assert config.hotkey_output_mode == "clipboard"


def test_config_validation():
    """Test configuration parameter validation."""
    # Test invalid values
    config = ServerConfig()

    # Port should be within valid range
    assert 1 <= config.port <= 65535

    # Volume should be between 0 and 1
    assert 0.0 <= config.tts_volume <= 1.0

    # Sample rate should be positive
    assert config.sample_rate > 0

    # Chunk size should be positive
    assert config.chunk_size > 0

    # Silence threshold should be positive
    assert config.stt_silence_threshold > 0


def test_config_boolean_parsing(monkeypatch):
    """Test boolean environment variable parsing."""
    test_cases = [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("1", False),  # Only "true" (case-insensitive) should be True
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("0", False),
        ("", False),
        ("invalid", False),
    ]

    for env_value, expected in test_cases:
        monkeypatch.setenv("VOICE_MCP_DEBUG", env_value)
        config = ServerConfig.from_env()
        assert config.debug == expected, f"Failed for env value: {env_value}"
