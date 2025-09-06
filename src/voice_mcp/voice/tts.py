"""
Text-to-Speech engine implementation using Coqui TTS.
"""

import logging
import threading
from dataclasses import dataclass
from typing import Any

from ..config import config
from .audio import AudioManager

logger = logging.getLogger(__name__)


@dataclass
class Voice:
    """Represents a TTS voice/model."""

    id: str
    name: str
    language: str
    description: str | None = None


class CoquiTTSEngine:
    """Coqui TTS engine for high-quality speech synthesis."""

    def __init__(
        self,
        model_name: str = "tts_models/en/ljspeech/tacotron2-DDC",
        gpu_enabled: bool = False,
    ):
        self._model_name = model_name
        self._gpu_enabled = gpu_enabled
        self._tts = None
        self._initialized = False
        self._audio_manager = AudioManager()
        self._init_lock = threading.RLock()  # Thread safety for initialization
        self._init_engine()

    def _init_engine(self) -> None:
        """Initialize the Coqui TTS engine with thread safety."""
        # Return early if already initialized (fast path)
        if self._initialized:
            return

        with self._init_lock:
            # Double-check after acquiring lock
            if self._initialized:
                return

            try:
                from TTS.api import TTS  # type: ignore

                # Determine GPU usage
                use_gpu = False
                if self._gpu_enabled:
                    try:
                        import torch

                        use_gpu = torch.cuda.is_available()
                        if use_gpu:
                            logger.info(
                                "CUDA available, enabling GPU acceleration for TTS"
                            )
                        else:
                            logger.warning(
                                "GPU requested but CUDA not available, falling back to CPU"
                            )
                    except ImportError:
                        logger.warning(
                            "GPU requested but PyTorch not available, falling back to CPU"
                        )

                logger.info(
                    f"Initializing Coqui TTS with model: {self._model_name}, GPU: {use_gpu}"
                )
                self._tts = TTS(self._model_name, progress_bar=False, gpu=use_gpu)
                self._initialized = True
                logger.info("Coqui TTS engine initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Coqui TTS engine: {e}")
                self._tts = None
                self._initialized = False

    def speak(
        self,
        text: str,
        voice: str | None = None,  # noqa: ARG002
        rate: float | None = None,
        volume: float | None = None,  # noqa: ARG002
    ) -> bool:
        """Convert text to speech using Coqui TTS."""
        # Ensure initialization (thread-safe)
        self._init_engine()

        if not self.is_available():
            logger.error("Coqui TTS engine not available")
            return False

        if self._tts is None:
            logger.error("TTS engine not initialized")
            return False

        try:
            # Use the direct tts() method that returns audio data
            logger.debug("Using direct TTS audio generation (no temp file)")
            audio_data = self._tts.tts(text=text)

            # Convert to bytes if needed and play directly with rate adjustment
            if self._play_audio_data_directly(audio_data, rate):
                logger.debug(
                    f"Successfully spoke text using direct method: {text[:50]}..."
                )
                return True
            else:
                # Fallback to file method if direct playback failed
                logger.warning(
                    "Direct audio playback failed, falling back to file method"
                )

        except Exception as e:
            logger.error(f"Error during speech synthesis: {e}")
            return False

    def _play_audio_data_directly(
        self, audio_data: Any, rate: float | None = None
    ) -> bool:
        """
        Play audio data directly without saving to file.

        Args:
            audio_data: Audio data from Coqui TTS (typically numpy array or torch tensor)
            rate: Speed multiplier (1.0 = normal, >1.0 = faster, <1.0 = slower)

        Returns:
            True if playback was successful, False otherwise
        """
        try:
            import numpy as np

            # Convert audio data to the right format
            if hasattr(audio_data, "cpu"):
                # PyTorch tensor
                audio_array = audio_data.cpu().numpy()
            elif hasattr(audio_data, "numpy"):
                # TensorFlow tensor or similar
                audio_array = audio_data.numpy()
            else:
                # Assume it's already a numpy array
                audio_array = np.array(audio_data)

            # Ensure it's the right data type and range for audio playback
            if audio_array.dtype != np.float32:
                audio_array = audio_array.astype(np.float32)

            # Validate audio quality before processing (if enabled)
            if config.audio_quality_validation_enabled:
                is_valid, error_msg = self._validate_audio_quality(audio_array)
                if not is_valid:
                    logger.error(f"Audio quality validation failed: {error_msg}")
                    return False

            # Apply time-stretching for rate adjustment if specified
            if rate is not None and rate != 1.0 and rate > 0:
                logger.debug(f"Applying time-stretching rate adjustment: {rate}x")
                try:
                    import librosa

                    # Use librosa for high-quality time-stretching that maintains pitch
                    audio_array = librosa.effects.time_stretch(audio_array, rate=rate)
                    logger.debug("Time-stretching completed successfully")
                except ImportError:
                    logger.warning(
                        "librosa not available for time-stretching, skipping rate adjustment"
                    )
                except Exception as e:
                    logger.error(f"Time-stretching failed: {e}, using original audio")

            # Coqui TTS usually outputs float32 in range [-1, 1]
            # Convert to 16-bit PCM with proper normalization and headroom
            if audio_array.dtype == np.float32:
                # Validate audio range and apply normalization with configurable headroom
                max_val = np.abs(audio_array).max()
                if max_val > 0:
                    headroom = config.audio_normalization_headroom
                    if max_val > headroom:
                        audio_array = audio_array * (headroom / max_val)
                        logger.debug(
                            f"Applied normalization: peak reduced from {max_val:.3f} to {headroom}"
                        )

                # Scale to 16-bit range with configured headroom
                audio_array = (
                    audio_array * 32767 * config.audio_normalization_headroom
                ).astype(np.int16)
            elif audio_array.dtype != np.int16:
                # Ensure it's int16
                audio_array = audio_array.astype(np.int16)

            # Convert to bytes
            audio_bytes = audio_array.tobytes()

            # Detect actual sample rate from TTS model (fallback to 22050)
            sample_rate = self._get_model_sample_rate()
            logger.debug(f"Using sample rate: {sample_rate} Hz")

            success = self._audio_manager.play_audio_data(
                audio_data=audio_bytes,
                sample_rate=sample_rate,
                channels=1,  # mono
                sample_width=2,  # 16-bit = 2 bytes
            )

            return success

        except Exception as e:
            logger.error(f"Error playing audio data directly: {e}")
            return False

    def _get_model_sample_rate(self) -> int:
        """
        Detect the sample rate of the current TTS model.

        Returns:
            Sample rate in Hz, defaults to 22050 if detection fails
        """
        if self._tts is None:
            logger.warning("TTS engine not initialized, using default sample rate")
            return 22050

        try:
            # Try to get sample rate from model configuration
            if hasattr(self._tts, "synthesizer") and hasattr(
                self._tts.synthesizer, "output_sample_rate"
            ):
                sample_rate = self._tts.synthesizer.output_sample_rate
                logger.debug(f"Detected sample rate from synthesizer: {sample_rate} Hz")
                return int(sample_rate)

            # Try to get from model config
            if hasattr(self._tts, "config") and hasattr(self._tts.config, "audio"):
                if hasattr(self._tts.config.audio, "sample_rate"):
                    sample_rate = self._tts.config.audio.sample_rate
                    logger.debug(f"Detected sample rate from config: {sample_rate} Hz")
                    return int(sample_rate)

            # Model-specific defaults based on model name
            model_sample_rates = {
                "tacotron2": 22050,
                "glow-tts": 22050,
                "speedy-speech": 22050,
                "fast_pitch": 22050,
                "xtts": 24000,
                "multi-dataset": 24000,  # XTTS models often contain this
                "vits": 22050,
                "bark": 24000,
            }

            for model_key, default_rate in model_sample_rates.items():
                if model_key in self._model_name.lower():
                    logger.debug(
                        f"Using model-specific sample rate for {model_key}: {default_rate} Hz"
                    )
                    return default_rate

        except Exception as e:
            logger.warning(f"Error detecting sample rate from model: {e}")

        # Default fallback
        logger.debug("Using default sample rate: 22050 Hz")
        return 22050

    def _validate_audio_quality(self, audio_array: Any) -> tuple[bool, str]:
        """
        Validate audio data quality and detect potential issues.

        Args:
            audio_array: Audio data array to validate

        Returns:
            Tuple of (is_valid, error_message). error_message is empty if valid.
        """
        try:
            import numpy as np

            # Ensure it's a numpy array
            if not isinstance(audio_array, np.ndarray):
                return False, "Audio data is not a numpy array"

            # Check if audio is empty
            if audio_array.size == 0:
                return False, "Audio array is empty"

            # Check for NaN or infinite values
            if np.any(np.isnan(audio_array)) or np.any(np.isinf(audio_array)):
                return False, "Audio contains NaN or infinite values"

            # Check for silence (all zeros or very low amplitude)
            max_amplitude = np.abs(audio_array).max()
            if max_amplitude < 1e-6:
                return False, f"Audio is silent (max amplitude: {max_amplitude:.2e})"

            # Check for clipping (values at or very close to digital maximum)
            if audio_array.dtype == np.float32:
                clip_threshold = 0.99
                clipped_samples = np.sum(np.abs(audio_array) > clip_threshold)
                if clipped_samples > len(audio_array) * 0.01:  # More than 1% clipped
                    return (
                        False,
                        f"Audio is heavily clipped ({clipped_samples} samples > {clip_threshold})",
                    )

            # Check audio duration (too short might indicate generation issues)
            if len(audio_array) < 1000:  # Less than ~45ms at 22kHz
                return (
                    False,
                    f"Audio too short ({len(audio_array)} samples, likely generation error)",
                )

            # Calculate quality metrics
            rms = np.sqrt(np.mean(audio_array**2))
            peak = np.abs(audio_array).max()
            dynamic_range = 20 * np.log10(peak / (rms + 1e-10)) if rms > 0 else 0

            logger.debug(
                f"Audio quality metrics - Peak: {peak:.3f}, RMS: {rms:.3f}, Dynamic Range: {dynamic_range:.1f} dB"
            )

            # Warn about potential quality issues
            if dynamic_range < 6:  # Less than 6dB dynamic range
                logger.warning(f"Low dynamic range detected: {dynamic_range:.1f} dB")
            if peak > 0.95:  # Very high peak levels
                logger.warning(f"High peak levels detected: {peak:.3f}")

            return True, ""

        except Exception as e:
            return False, f"Audio validation error: {str(e)}"

    def get_voices(self) -> list[Voice]:
        """Get available Coqui TTS models."""
        # Ensure initialization (thread-safe)
        self._init_engine()

        if not self.is_available():
            return []

        try:
            # Return some common Coqui TTS models
            # In a real implementation, you might query the TTS API for available models
            return [
                Voice(
                    id="tts_models/en/ljspeech/tacotron2-DDC",
                    name="LJSpeech Tacotron2",
                    language="en",
                    description="English female voice (LJSpeech dataset)",
                ),
                Voice(
                    id="tts_models/en/ljspeech/fast_pitch",
                    name="LJSpeech FastPitch",
                    language="en",
                    description="English female voice (FastPitch model)",
                ),
                Voice(
                    id="tts_models/multilingual/multi-dataset/xtts_v2",
                    name="XTTS v2 Multilingual",
                    language="multilingual",
                    description="High-quality multilingual voice",
                ),
            ]
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return []

    def is_available(self) -> bool:
        """Check if Coqui TTS engine is available."""
        return self._initialized and self._tts is not None

    def stop(self) -> None:
        """Stop current speech."""
        # Note: With the current AudioManager implementation using PyAudio streams,
        # stopping playback mid-stream is not easily supported since each playback
        # runs in its own thread and stream. This is a limitation we inherit.
        logger.warning("Stop functionality not implemented for current audio backend")


class TTSManager:
    """Manages Coqui TTS engine."""

    def __init__(
        self,
        model_name: str = "tts_models/en/ljspeech/tacotron2-DDC",
        gpu_enabled: bool = False,
    ):
        self._engine = CoquiTTSEngine(model_name, gpu_enabled)

    def speak(
        self,
        text: str,
        voice: str | None = None,
        rate: float | None = None,
        volume: float | None = None,
    ) -> str:
        """
        Convert text to speech using Coqui TTS.

        Returns:
            Status message
        """
        if not self._engine.is_available():
            return "❌ Coqui TTS engine not available"

        if not text or not text.strip():
            return "❌ No text provided to speak"

        # Truncate very long text
        if len(text) > 1000:
            text = text[:1000] + "... (truncated)"
            logger.warning("Text truncated to 1000 characters for TTS")

        try:
            success = self._engine.speak(text, voice, rate, volume)
            if success:
                return f"✅ Successfully spoke: '{text[:50]}...'"
            else:
                return "❌ Failed to speak text"

        except Exception as e:
            logger.error(f"Error in TTS speak: {e}")
            return f"❌ TTS error: {str(e)}"

    def get_voices(self) -> list[Voice]:
        """Get available voices from Coqui TTS."""
        return self._engine.get_voices()

    def get_voice_info(self) -> dict[str, Any]:
        """Get information about current TTS setup."""
        if not self._engine.is_available():
            return {"status": "no_engine", "voices": []}

        voices = self.get_voices()
        return {
            "status": "available",
            "engine": "CoquiTTS",
            "model": self._engine._model_name,
            "voice_count": len(voices),
            "voices": [
                {
                    "id": v.id,
                    "name": v.name,
                    "language": v.language,
                    "description": v.description,
                }
                for v in voices[:5]
            ],  # Limit to 5 for brevity
        }

    def stop(self) -> None:
        """Stop current speech."""
        self._engine.stop()

    def is_available(self) -> bool:
        """Check if TTS engine is available."""
        return self._engine.is_available()
