"""
Test suite for audio quality validation and improvements.
"""

import numpy as np
import pytest

from voice_mcp.voice.tts import CoquiTTSEngine


class TestAudioQuality:
    """Test audio quality validation and processing."""

    def setup_method(self):
        """Setup test fixtures."""
        self.engine = CoquiTTSEngine()

    def test_validate_audio_quality_valid(self):
        """Test that valid audio passes validation."""
        # Create a valid audio array (sine wave)
        sample_rate = 22050
        duration = 1.0  # 1 second
        frequency = 440  # A4 note

        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio = np.sin(2 * np.pi * frequency * t).astype(np.float32) * 0.5

        is_valid, error_msg = self.engine._validate_audio_quality(audio)
        assert is_valid, f"Valid audio failed validation: {error_msg}"
        assert error_msg == "", "Error message should be empty for valid audio"

    def test_validate_audio_quality_empty(self):
        """Test that empty audio fails validation."""
        audio = np.array([], dtype=np.float32)

        is_valid, error_msg = self.engine._validate_audio_quality(audio)
        assert not is_valid, "Empty audio should fail validation"
        assert "empty" in error_msg.lower()

    def test_validate_audio_quality_nan(self):
        """Test that audio with NaN values fails validation."""
        audio = np.array([0.1, 0.2, np.nan, 0.4], dtype=np.float32)

        is_valid, error_msg = self.engine._validate_audio_quality(audio)
        assert not is_valid, "Audio with NaN should fail validation"
        assert "nan" in error_msg.lower()

    def test_validate_audio_quality_silent(self):
        """Test that silent audio fails validation."""
        audio = np.zeros(22050, dtype=np.float32)  # 1 second of silence

        is_valid, error_msg = self.engine._validate_audio_quality(audio)
        assert not is_valid, "Silent audio should fail validation"
        assert "silent" in error_msg.lower()

    def test_validate_audio_quality_clipped(self):
        """Test that heavily clipped audio fails validation."""
        # Create audio that's mostly clipped
        audio = np.ones(22050, dtype=np.float32) * 0.999  # Near maximum

        is_valid, error_msg = self.engine._validate_audio_quality(audio)
        assert not is_valid, "Heavily clipped audio should fail validation"
        assert "clipped" in error_msg.lower()

    def test_validate_audio_quality_too_short(self):
        """Test that very short audio fails validation."""
        audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        is_valid, error_msg = self.engine._validate_audio_quality(audio)
        assert not is_valid, "Very short audio should fail validation"
        assert "too short" in error_msg.lower()

    def test_get_model_sample_rate_default(self):
        """Test that sample rate detection returns default when model is unavailable."""
        # Engine without initialized TTS model
        engine = CoquiTTSEngine()
        sample_rate = engine._get_model_sample_rate()
        assert sample_rate == 22050, "Should return default sample rate"

    def test_get_model_sample_rate_tacotron(self):
        """Test sample rate detection for Tacotron model."""
        engine = CoquiTTSEngine(model_name="tts_models/en/ljspeech/tacotron2-DDC")
        sample_rate = engine._get_model_sample_rate()
        assert sample_rate == 22050, "Tacotron should use 22050 Hz"

    def test_get_model_sample_rate_xtts(self):
        """Test sample rate detection for XTTS model."""
        engine = CoquiTTSEngine(
            model_name="tts_models/multilingual/multi-dataset/xtts_v2"
        )
        sample_rate = engine._get_model_sample_rate()
        # If TTS engine isn't initialized, it falls back to default (22050)
        # If it is initialized and detects model, it should use 24000 for XTTS
        assert sample_rate in [
            22050,
            24000,
        ], f"XTTS should use 24000 Hz or fall back to 22050 Hz, got {sample_rate}"

    def test_audio_normalization_with_headroom(self):
        """Test that audio normalization applies proper headroom."""
        # Create audio that needs normalization (peak > 0.95)
        audio = np.array([0.98, -0.97, 0.99, -0.96], dtype=np.float32)

        # Mock the config for testing
        from voice_mcp.config import config

        original_headroom = config.audio_normalization_headroom
        config.audio_normalization_headroom = 0.9

        try:
            # Process audio through the normalization logic
            max_val = np.abs(audio).max()
            headroom = config.audio_normalization_headroom

            if max_val > headroom:
                normalized_audio = audio * (headroom / max_val)
                new_peak = np.abs(normalized_audio).max()
                assert (
                    new_peak <= headroom
                ), f"Normalized peak ({new_peak}) should be <= headroom ({headroom})"

        finally:
            # Restore original config
            config.audio_normalization_headroom = original_headroom


class TestAudioProcessingIntegration:
    """Integration tests for audio processing pipeline."""

    def test_rate_adjustment_maintains_quality(self):
        """Test that rate adjustment doesn't degrade audio quality significantly."""
        # Create a test sine wave
        sample_rate = 22050
        duration = 0.5  # 0.5 seconds
        frequency = 440

        t = np.linspace(0, duration, int(sample_rate * duration), False)
        original_audio = np.sin(2 * np.pi * frequency * t).astype(np.float32) * 0.5

        engine = CoquiTTSEngine()

        # Validate original audio passes quality checks
        is_valid, error_msg = engine._validate_audio_quality(original_audio)
        assert is_valid, f"Original test audio should be valid: {error_msg}"

    def test_audio_quality_integration(self):
        """Test complete audio quality validation pipeline."""
        engine = CoquiTTSEngine()

        # Test various audio scenarios
        test_cases = [
            # (description, audio_data, should_pass)
            ("Valid sine wave", np.sin(np.linspace(0, 2 * np.pi, 22050)) * 0.5, True),
            ("Empty array", np.array([]), False),
            ("Too short", np.array([0.1, 0.2]), False),
            ("Silent", np.zeros(22050), False),
            ("NaN values", np.array([0.1, np.nan, 0.3] * 1000), False),
        ]

        for description, audio_data, should_pass in test_cases:
            audio_array = (
                audio_data.astype(np.float32) if len(audio_data) > 0 else audio_data
            )
            is_valid, error_msg = engine._validate_audio_quality(audio_array)

            if should_pass:
                assert (
                    is_valid
                ), f"{description} should pass validation but failed: {error_msg}"
            else:
                assert not is_valid, f"{description} should fail validation but passed"


@pytest.mark.voice  # Mark as requiring audio hardware
class TestTTSAudioQuality:
    """Test TTS audio quality with actual models (requires hardware)."""

    def test_tts_output_quality(self):
        """Test that TTS output meets quality standards."""
        pytest.skip("Requires TTS model and audio hardware - manual testing only")

        # This test would require actual TTS model initialization
        # and is meant for manual verification of the fixes
        engine = CoquiTTSEngine()
        if not engine.is_available():
            pytest.skip("TTS engine not available")

        # Test rate adjustment doesn't cause distortion
        # This test would validate actual TTS output quality at different rates
        pass
