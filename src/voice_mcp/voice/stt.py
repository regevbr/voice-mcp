"""
Simplified speech-to-text functionality with singleton pattern and preloading.
"""

import contextlib
from typing import TYPE_CHECKING, Any

import structlog
import torch

from ..config import config

if TYPE_CHECKING:
    from .text_output import TextOutputController

# Check if RealtimeSTT is available
try:
    from RealtimeSTT import AudioToTextRecorder  # type: ignore

    REALTIMESTT_AVAILABLE = True
except ImportError:
    REALTIMESTT_AVAILABLE = False
    AudioToTextRecorder = None

logger = structlog.get_logger(__name__)


class TranscriptionHandler:
    """Simplified transcription handler with singleton pattern and preloading."""

    _instance: "TranscriptionHandler | None" = None
    _recorder: Any = None  # AudioToTextRecorder when available, None when not
    _is_initialized = False

    def __new__(cls) -> "TranscriptionHandler":
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the transcription handler (called only once due to singleton)."""
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self.device: str | None = None
        self.compute_type: str | None = None

        logger.info(
            "TranscriptionHandler initialized (singleton)",
            model=config.stt_model,
            silence_threshold=config.stt_silence_threshold,
            language=config.stt_language,
        )

    def _get_optimal_device(self) -> tuple[str, str]:
        """Detect optimal device for Whisper inference with error handling."""
        if config.stt_device != "auto":
            # Use specified device
            if config.stt_device == "cuda":
                return "cuda", "float16"
            else:
                return "cpu", "int8"

        if not torch:
            logger.warning("PyTorch not available, defaulting to CPU")
            return "cpu", "int8"

        try:
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name()
                logger.info("CUDA detected", device=device_name)
                return "cuda", "float16"
            else:
                logger.info("CUDA not available, using CPU with int8 quantization")
                return "cpu", "int8"
        except Exception as e:
            logger.warning("Error detecting CUDA, falling back to CPU", error=str(e))
            return "cpu", "int8"

    def preload(self) -> bool:
        """
        Preload the STT model on server startup.

        Returns:
            True if preloading successful, False otherwise
        """
        if not REALTIMESTT_AVAILABLE:
            logger.warning("RealtimeSTT not available - STT functionality disabled")
            return False

        if self._is_initialized:
            logger.debug("STT model already preloaded")
            return True

        try:
            self.device, self.compute_type = self._get_optimal_device()

            logger.info(
                "Preloading STT model", model=config.stt_model, device=self.device
            )

            recorder_config = {
                # Model configuration
                "model": config.stt_model,
                "language": config.stt_language,
                "device": self.device,
                "compute_type": self.compute_type,
                # VAD Configuration for better speech detection
                "silero_sensitivity": 0.4,  # Silero VAD sensitivity (0.0-1.0)
                "webrtc_sensitivity": 2,  # WebRTC VAD aggressiveness (0-3)
                # Recording behavior
                "post_speech_silence_duration": config.stt_silence_threshold,
                "min_length_of_recording": 0.5,  # Minimum recording duration
                # Real-time transcription settings
                "enable_realtime_transcription": True,
                "realtime_processing_pause": 0.1,  # Update every 100ms
                "realtime_model_type": config.stt_model,
                # Performance settings
                "use_microphone": True,
                "no_log_file": True,
                "spinner": False,  # Disable spinner for cleaner output
                "early_transcription_on_silence": 1,  # Faster transcription
            }

            self._recorder = AudioToTextRecorder(**recorder_config)
            self._is_initialized = True

            logger.info(
                "STT model preloaded successfully",
                model=config.stt_model,
                device=self.device,
                compute_type=self.compute_type,
            )
            return True

        except Exception as e:
            logger.error("Failed to preload STT model", error=str(e))
            return False

    def is_ready(self) -> bool:
        """Check if STT model is ready for use."""
        return (
            REALTIMESTT_AVAILABLE
            and self._is_initialized
            and self._recorder is not None
        )

    def is_available(self) -> bool:
        """Check if STT functionality is available (RealtimeSTT installed)."""
        return REALTIMESTT_AVAILABLE

    def enable(self) -> bool:
        """Enable STT by loading model if not already loaded."""
        if self.is_ready():
            return True
        return self.preload()

    def transcribe_once(
        self, duration: float | None = None, language: str | None = None
    ) -> dict[str, Any]:
        """
        Perform a single transcription session.

        Args:
            duration: Maximum recording duration (None for silence-based stopping)
            language: Language override for this session

        Returns:
            Dictionary with transcription results and metadata
        """
        # Auto-enable if not ready
        if not self.is_ready():
            if not self.enable():
                return {
                    "success": False,
                    "error": "STT not available - failed to load model",
                    "transcription": "",
                    "duration": 0.0,
                }

        import time

        transcription_result = ""
        start_time = time.time()
        use_language = language or config.stt_language

        def on_transcription_update(text: str) -> None:
            nonlocal transcription_result
            transcription_result = text
            logger.debug(
                "Transcription update",
                text=text[:50] + "..." if len(text) > 50 else text,
            )

        def on_recording_stop(text: str) -> None:
            nonlocal transcription_result
            transcription_result = text
            logger.info("Recording stopped", final_text=text)

        try:
            logger.info("Using preloaded STT model for transcription")
            recorder_to_use = self._recorder

            # Configure callbacks for this session on the preloaded recorder
            # Note: RealtimeSTT allows dynamic callback configuration
            if hasattr(recorder_to_use, "set_on_recording_stop"):
                recorder_to_use.set_on_recording_stop(on_recording_stop)  # type: ignore
            if hasattr(recorder_to_use, "set_on_realtime_transcription_stabilized"):
                recorder_to_use.set_on_realtime_transcription_stabilized(  # type: ignore
                    on_transcription_update
                )

            logger.info("Starting transcription session", max_duration=duration)

            # Start recording
            if duration:
                # Record for specified duration
                with self._timeout_context(duration):
                    recorder_to_use.listen()  # type: ignore
            else:
                # Record until silence
                recorder_to_use.listen()  # type: ignore

            end_time = time.time()
            actual_duration = end_time - start_time

            logger.info(
                "Transcription completed",
                duration=actual_duration,
                text_length=len(transcription_result),
            )

            return {
                "success": True,
                "transcription": transcription_result.strip(),
                "duration": actual_duration,
                "language": use_language,
                "model": config.stt_model,
            }

        except Exception as e:
            end_time = time.time()
            logger.error(
                "Transcription failed", error=str(e), duration=end_time - start_time
            )
            return {
                "success": False,
                "error": f"Transcription error: {str(e)}",
                "transcription": transcription_result.strip(),
                "duration": end_time - start_time,
            }

    def transcribe_with_realtime_output(
        self,
        text_output_controller: "TextOutputController",
        duration: float | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        """
        Perform transcription with real-time text output for hotkey usage.

        Args:
            text_output_controller: TextOutputController for real-time typing
            duration: Maximum recording duration (None for silence-based stopping)
            language: Language override for this session

        Returns:
            Dictionary with transcription results and metadata
        """
        # Auto-enable if not ready
        if not self.is_ready():
            if not self.enable():
                return {
                    "success": False,
                    "error": "STT not available - failed to load model",
                    "transcription": "",
                    "duration": 0.0,
                }

        import time

        transcription_result = ""
        start_time = time.time()
        use_language = language or config.stt_language

        def on_realtime_transcription_update(text: str) -> None:
            nonlocal transcription_result
            transcription_result = text
            logger.debug("Real-time transcription update", text_length=len(text))

            # Output text in real-time using the typing mode
            try:
                result = text_output_controller.output_text(text, "typing")
                if not result["success"]:
                    logger.warning("Real-time typing failed", error=result.get("error"))
            except Exception as e:
                logger.warning("Real-time typing error", error=str(e))

        def on_recording_stop(text: str) -> None:
            nonlocal transcription_result
            transcription_result = text
            logger.info("Recording stopped with final text", final_text=text)

            # Final output to ensure we have the complete text
            try:
                result = text_output_controller.output_text(
                    text, "typing", force_update=True
                )
                if not result["success"]:
                    logger.warning("Final typing failed", error=result.get("error"))
            except Exception as e:
                logger.warning("Final typing error", error=str(e))

        try:
            logger.info("Using preloaded STT model for real-time transcription")
            recorder_to_use = self._recorder

            # Configure callbacks for real-time output
            if hasattr(recorder_to_use, "set_on_recording_stop"):
                recorder_to_use.set_on_recording_stop(on_recording_stop)  # type: ignore
            if hasattr(recorder_to_use, "set_on_realtime_transcription_stabilized"):
                recorder_to_use.set_on_realtime_transcription_stabilized(  # type: ignore
                    on_realtime_transcription_update
                )

            logger.info(
                "Starting real-time transcription session", max_duration=duration
            )

            # Start recording
            if duration:
                with self._timeout_context(duration):
                    recorder_to_use.listen()  # type: ignore
            else:
                recorder_to_use.listen()  # type: ignore

            end_time = time.time()
            actual_duration = end_time - start_time

            logger.info(
                "Real-time transcription completed",
                duration=actual_duration,
                text_length=len(transcription_result),
            )

            return {
                "success": True,
                "transcription": transcription_result.strip(),
                "duration": actual_duration,
                "language": use_language,
                "model": config.stt_model,
            }

        except Exception as e:
            end_time = time.time()
            logger.error(
                "Real-time transcription failed",
                error=str(e),
                duration=end_time - start_time,
            )
            return {
                "success": False,
                "error": f"Transcription error: {str(e)}",
                "transcription": transcription_result.strip(),
                "duration": end_time - start_time,
            }

    @contextlib.contextmanager
    def _timeout_context(self, duration: float):
        """Context manager for handling recording timeout."""
        import signal

        class TimeoutError(Exception):
            pass

        def timeout_handler(_signum, _frame):
            raise TimeoutError(f"Recording timeout after {duration} seconds")

        # Set the signal handler
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(duration))

        try:
            yield
        except TimeoutError:
            logger.info("Recording stopped due to timeout", duration=duration)
        finally:
            # Restore the old signal handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._recorder:
            try:
                # Clean up recorder resources if available
                if hasattr(self._recorder, "cleanup"):
                    self._recorder.cleanup()
                logger.debug("TranscriptionHandler cleaned up")
            except Exception as e:
                logger.warning("Error during cleanup", error=str(e))
            finally:
                self._recorder = None

        # Always reset initialization state
        self._is_initialized = False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()


# Global singleton instance
transcription_handler = TranscriptionHandler()


def get_transcription_handler() -> TranscriptionHandler:
    """Get the global transcription handler instance."""
    return transcription_handler
