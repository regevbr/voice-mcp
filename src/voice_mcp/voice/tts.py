"""
Text-to-Speech engine implementation using Coqui TTS.
"""

import logging
import threading
from dataclasses import dataclass
from typing import Any

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

            # Apply rate adjustment if specified
            if rate is not None and rate != 1.0 and rate > 0:
                # Rate adjustment is handled by modifying the sample rate
                # passed to the audio manager rather than resampling the audio data
                # This is more efficient and maintains quality
                logger.debug(f"Applying rate adjustment: {rate}x")

            # Coqui TTS usually outputs float32 in range [-1, 1]
            # Convert to 16-bit PCM (typical for WAV files)
            if audio_array.dtype == np.float32 and np.abs(audio_array).max() <= 1.0:
                # Scale to 16-bit range
                audio_array = (audio_array * 32767).astype(np.int16)
            elif audio_array.dtype != np.int16:
                # Ensure it's int16
                audio_array = audio_array.astype(np.int16)

            # Convert to bytes
            audio_bytes = audio_array.tobytes()

            # Play using AudioManager with typical TTS parameters
            # Most TTS models output at 22050 Hz, mono, 16-bit
            base_sample_rate = 22050

            # Adjust sample rate for rate control (higher sample rate = faster playback)
            if rate is not None and rate > 0:
                adjusted_sample_rate = int(base_sample_rate * rate)
                logger.debug(
                    f"Adjusted sample rate: {adjusted_sample_rate} Hz (rate: {rate}x)"
                )
            else:
                adjusted_sample_rate = base_sample_rate

            success = self._audio_manager.play_audio_data(
                audio_data=audio_bytes,
                sample_rate=adjusted_sample_rate,
                channels=1,  # mono
                sample_width=2,  # 16-bit = 2 bytes
            )

            return success

        except Exception as e:
            logger.error(f"Error playing audio data directly: {e}")
            return False

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
