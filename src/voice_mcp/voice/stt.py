"""
Simplified speech-to-text functionality with singleton pattern and preloading.
"""

import contextlib
from typing import TYPE_CHECKING, Any

import structlog
import torch

from ..config import config

# Fix for tqdm compatibility issue with huggingface_hub
try:
    from contextlib import nullcontext

    import tqdm  # type: ignore
    import tqdm.contrib.concurrent  # type: ignore
    import tqdm.std  # type: ignore

    # Patch the tqdm class to handle disabled_tqdm properly
    original_tqdm_new = tqdm.std.tqdm.__new__

    def patched_tqdm_new(cls, *args, **kwargs):
        """Patched __new__ that handles get_lock properly."""
        try:
            # Get the lock with proper error handling
            lock = cls.get_lock()
            if lock is None:
                # If get_lock returns None, create a proper lock
                import threading

                cls._lock = threading.RLock()
        except (AttributeError, TypeError):
            # If there's any issue with locking, create a proper lock
            import threading

            cls._lock = threading.RLock()

        return original_tqdm_new(cls, *args, **kwargs)

    # Apply the tqdm patch
    tqdm.std.tqdm.__new__ = staticmethod(patched_tqdm_new)

    # Patch the ensure_lock function to handle disabled_tqdm properly
    original_ensure_lock = tqdm.contrib.concurrent.ensure_lock

    def patched_ensure_lock(tqdm_class, lock_name=""):
        """Patched ensure_lock that handles disabled_tqdm properly."""
        try:
            # Check if the class has the _lock attribute before trying to access it
            if not hasattr(tqdm_class, "_lock"):
                # For disabled_tqdm or other classes without _lock, return nullcontext
                return nullcontext()
            return original_ensure_lock(tqdm_class, lock_name)
        except AttributeError as e:
            if "_lock" in str(e) or "disabled_tqdm" in str(e):
                # Create a no-op context manager for disabled_tqdm
                return nullcontext()
            raise

    # Apply the patch globally before any imports that might use huggingface_hub
    tqdm.contrib.concurrent.ensure_lock = patched_ensure_lock

    # Also patch directly in tqdm.contrib.concurrent module for safety
    if hasattr(tqdm.contrib.concurrent, "_executor_map"):
        original_executor_map = tqdm.contrib.concurrent._executor_map

        def patched_executor_map(executor_class, fn, *iterables, **kwargs):
            """Patched _executor_map that handles disabled_tqdm properly."""
            try:
                return original_executor_map(executor_class, fn, *iterables, **kwargs)
            except (AttributeError, TypeError) as e:
                if "_lock" in str(e) or "context manager" in str(e):
                    # If we encounter lock/context manager issues, fall back to simpler execution
                    with executor_class() as executor:
                        return list(executor.map(fn, *iterables))
                raise

        tqdm.contrib.concurrent._executor_map = patched_executor_map

except ImportError:
    pass

if TYPE_CHECKING:
    from .text_output import TextOutputController

# Check if RealtimeSTT is available
try:
    from RealtimeSTT import AudioToTextRecorder

    REALTIMESTT_AVAILABLE = True
except ImportError:
    REALTIMESTT_AVAILABLE = False

    # Create a placeholder type for type checking
    class AudioToTextRecorder:  # type: ignore
        pass


logger = structlog.get_logger(__name__)


class TranscriptionHandler:
    """Simplified transcription handler with singleton pattern and preloading."""

    _instance: "TranscriptionHandler | None" = None
    _recorder: AudioToTextRecorder | None = None
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

        try:
            logger.info("Using preloaded STT model for transcription")
            recorder_to_use = self._recorder

            if recorder_to_use is None:
                raise RuntimeError("Recorder not initialized")

            # Configure callbacks by directly setting the instance attributes
            logger.debug("Setting recorder callbacks for single transcription")
            recorder_to_use.on_realtime_transcription_stabilized = (
                on_transcription_update
            )

            logger.info("Starting transcription session", max_duration=duration)

            # Start recording
            if duration:
                # Record for specified duration
                with self._timeout_context(duration):
                    recorder_to_use.start()  # type: ignore
                    transcription_result = recorder_to_use.text()  # type: ignore
            else:
                # Record until silence
                recorder_to_use.start()  # type: ignore
                transcription_result = recorder_to_use.text()  # type: ignore

            recorder_to_use.shutdown()

            logger.info("Recording stopped", final_text=transcription_result)

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
            logger.debug(
                "Real-time transcription update",
                text_length=len(text),
                text_preview=text[:50] + "..." if len(text) > 50 else text,
            )

            # Output text in real-time using the typing mode with force_update
            try:
                result = text_output_controller.output_text(
                    text, "typing", force_update=True
                )
                if result["success"]:
                    logger.debug(
                        "Real-time typing successful",
                        operation=result.get("operation", ""),
                    )
                else:
                    logger.warning(
                        "Real-time typing failed",
                        error=result.get("error"),
                        text_length=len(text),
                    )
            except Exception as e:
                logger.error(
                    "Real-time typing error",
                    error=str(e),
                    text_length=len(text),
                    exc_info=True,
                )

        try:
            logger.info("Using preloaded STT model for real-time transcription")
            recorder_to_use = self._recorder

            if recorder_to_use is None:
                raise RuntimeError("Recorder not initialized")

            # Configure callbacks by directly setting the instance attributes
            logger.debug("Setting up recorder callbacks for real-time transcription")
            recorder_to_use.on_realtime_transcription_stabilized = (
                on_realtime_transcription_update
            )
            logger.debug("Real-time transcription callbacks configured")

            logger.info(
                "Starting real-time transcription session", max_duration=duration
            )

            text_output_controller.reset()

            # Start recording
            if duration:
                with self._timeout_context(duration):
                    recorder_to_use.start()  # type: ignore
                    transcription_result = recorder_to_use.text()  # type: ignore
            else:
                recorder_to_use.start()  # type: ignore
                transcription_result = recorder_to_use.text()  # type: ignore

            recorder_to_use.shutdown()
            logger.info(
                "Recording stopped with final text",
                final_text=(
                    transcription_result[:100] + "..."
                    if len(transcription_result) > 100
                    else transcription_result
                ),
                text_length=len(transcription_result),
            )

            # Final output to ensure we have the complete text
            try:
                result = text_output_controller.output_text(
                    transcription_result, "typing", force_update=True
                )
                if result["success"]:
                    logger.info(
                        "Final typing successful", operation=result.get("operation", "")
                    )
                else:
                    logger.error(
                        "Final typing failed",
                        error=result.get("error"),
                        text_length=len(transcription_result),
                    )
            except Exception as e:
                logger.error(
                    "Final typing error",
                    error=str(e),
                    text_length=len(transcription_result),
                    exc_info=True,
                )

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
        import platform
        import signal
        import threading
        import time

        class RecordingTimeoutError(Exception):
            pass

        if platform.system() == "Windows":
            # Use threading-based timeout for Windows
            timeout_occurred = False

            def timeout_handler():
                nonlocal timeout_occurred
                time.sleep(duration)
                timeout_occurred = True

            timer = threading.Timer(duration, timeout_handler)
            timer.start()

            try:
                yield
            finally:
                timer.cancel()
                if timeout_occurred:
                    logger.info("Recording stopped due to timeout", duration=duration)
        else:
            # Use signal-based timeout for Unix systems
            def signal_timeout_handler(_signum, _frame):
                raise RecordingTimeoutError(
                    f"Recording timeout after {duration} seconds"
                )

            # Set the signal handler
            old_handler = signal.signal(signal.SIGALRM, signal_timeout_handler)
            signal.alarm(int(duration))

            try:
                yield
            except RecordingTimeoutError:
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
