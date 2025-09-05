"""
Enhanced speech-to-text functionality with proper error handling and configuration.
"""

import contextlib
from typing import Optional, Dict, Any, Callable, Tuple
import structlog
import torch
from RealtimeSTT import AudioToTextRecorder

from ..config import config
from .stt_server import get_stt_server

logger = structlog.get_logger(__name__)


class TranscriptionHandler:
    """Enhanced Whisper model configuration and transcription setup with proper error handling."""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        silence_threshold: Optional[float] = None,
        language: str = "en"
    ):
        """
        Initialize the transcription handler.
        
        Args:
            model_name: Whisper model name (tiny, base, small, medium, large)
            silence_threshold: Seconds of silence before stopping recording
            language: Language code for transcription
        """
        self.model_name = model_name or config.stt_model
        self.silence_threshold = silence_threshold or config.stt_silence_threshold
        self.language = language
        self.device: Optional[str] = None
        self.compute_type: Optional[str] = None
        self._recorder: Optional[AudioToTextRecorder] = None
        self._is_initialized = False
        
        logger.info(
            "TranscriptionHandler initialized",
            model=self.model_name,
            silence_threshold=self.silence_threshold,
            language=self.language
        )

    def _get_optimal_device(self) -> Tuple[str, str]:
        """Detect optimal device for Whisper inference with error handling."""
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
    
    def initialize(self) -> bool:
        """
        Initialize the transcription handler with device detection.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self._is_initialized:
            return True

        try:
            self.device, self.compute_type = self._get_optimal_device()
            self._is_initialized = True
            logger.info(
                "TranscriptionHandler initialized successfully",
                device=self.device,
                compute_type=self.compute_type
            )
            return True
        except Exception as e:
            logger.error("Failed to initialize TranscriptionHandler", error=str(e))
            return False
    
    def create_recorder(
        self,
        on_realtime_transcription_callback: Optional[Callable[[str], None]] = None,
        on_recording_stop_callback: Optional[Callable[[str], None]] = None,
        language: Optional[str] = None
    ) -> Optional[AudioToTextRecorder]:
        """
        Create and configure AudioToTextRecorder with optimized settings.
        
        Uses server mode if enabled and available, otherwise falls back to one-off mode.
        
        Args:
            on_realtime_transcription_callback: Callback for real-time transcription updates
            on_recording_stop_callback: Callback when recording stops
            language: Language override for this session
            
        Returns:
            Configured AudioToTextRecorder instance or None if creation failed
        """
        # Try server mode first if enabled
        if config.stt_server_mode:
            server_recorder = self._create_server_recorder(
                on_realtime_transcription_callback,
                on_recording_stop_callback,
                language
            )
            if server_recorder:
                return server_recorder
            else:
                logger.warning("Server mode failed, falling back to one-off mode")
        
        # Fall back to one-off mode
        return self._create_oneoff_recorder(
            on_realtime_transcription_callback,
            on_recording_stop_callback,
            language
        )
    
    def _create_server_recorder(
        self,
        on_realtime_transcription_callback: Optional[Callable[[str], None]] = None,
        on_recording_stop_callback: Optional[Callable[[str], None]] = None,
        language: Optional[str] = None
    ) -> Optional[AudioToTextRecorder]:
        """
        Create recorder using server mode (persistent models).
        
        Returns:
            AudioToTextRecorder from server or None if server unavailable
        """
        try:
            server = get_stt_server()
            if not server or not server._is_running:
                logger.debug("STT server not available or not running")
                return None
            
            # Get recorder from server
            recorder = server.get_model_recorder(self.model_name)
            if not recorder:
                logger.warning("Failed to get recorder from STT server", model=self.model_name)
                return None
            
            # Configure callbacks if provided
            # Note: This is a simplified approach. In practice, you might need to
            # create a wrapper or configure the recorder differently for callbacks
            if on_recording_stop_callback or on_realtime_transcription_callback:
                logger.debug("Configuring callbacks for server recorder")
                # In a real implementation, you would configure the callbacks here
                # This depends on the RealtimeSTT API for runtime callback configuration
            
            logger.info(
                "Using server recorder",
                model=self.model_name,
                language=language or self.language
            )
            
            return recorder
            
        except Exception as e:
            logger.error("Error creating server recorder", error=str(e))
            return None
    
    def _create_oneoff_recorder(
        self,
        on_realtime_transcription_callback: Optional[Callable[[str], None]] = None,
        on_recording_stop_callback: Optional[Callable[[str], None]] = None,
        language: Optional[str] = None
    ) -> Optional[AudioToTextRecorder]:
        """
        Create recorder using one-off mode (load model each time).
        
        Returns:
            Fresh AudioToTextRecorder instance or None if creation failed
        """
        if not self.initialize():
            logger.error("Cannot create recorder - initialization failed")
            return None

        use_language = language or self.language
        
        try:
            recorder_config = {
                # Model configuration
                "model": self.model_name,
                "language": use_language,
                "device": self.device,
                "compute_type": self.compute_type,
                
                # VAD Configuration for better speech detection
                "silero_sensitivity": 0.4,  # Silero VAD sensitivity (0.0-1.0)
                "webrtc_sensitivity": 2,    # WebRTC VAD aggressiveness (0-3)
                
                # Recording behavior
                "post_speech_silence_duration": self.silence_threshold,
                "min_length_of_recording": 0.5,  # Minimum recording duration
                
                # Real-time transcription settings
                "enable_realtime_transcription": True,
                "realtime_processing_pause": 0.1,  # Update every 100ms
                "realtime_model_type": self.model_name,
                
                # Performance settings
                "use_microphone": True,
                "no_log_file": True,
                "spinner": False,  # Disable spinner for cleaner output
                "early_transcription_on_silence": 1,  # Faster transcription
            }
            
            # Add callbacks if provided
            if on_recording_stop_callback:
                recorder_config["on_recording_stop"] = on_recording_stop_callback
            if on_realtime_transcription_callback:
                recorder_config["on_realtime_transcription_stabilized"] = on_realtime_transcription_callback
            
            self._recorder = AudioToTextRecorder(**recorder_config)
            
            logger.info(
                "AudioToTextRecorder created successfully (one-off mode)",
                model=self.model_name,
                language=use_language,
                device=self.device
            )
            
            return self._recorder
            
        except Exception as e:
            logger.error("Failed to create AudioToTextRecorder", error=str(e))
            return None
    
    def transcribe_once(
        self,
        duration: Optional[float] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform a single transcription session.
        
        Args:
            duration: Maximum recording duration (None for silence-based stopping)
            language: Language override for this session
            
        Returns:
            Dictionary with transcription results and metadata
        """
        if not self.initialize():
            return {
                "success": False,
                "error": "STT initialization failed - dependencies not available",
                "transcription": "",
                "duration": 0.0
            }
        
        import time
        
        transcription_result = ""
        start_time = time.time()
        
        def on_transcription_update(text: str) -> None:
            nonlocal transcription_result
            transcription_result = text
            logger.debug("Transcription update", text=text[:50] + "..." if len(text) > 50 else text)
        
        def on_recording_stop(text: str) -> None:
            nonlocal transcription_result
            transcription_result = text
            logger.info("Recording stopped", final_text=text)
        
        try:
            recorder = self.create_recorder(
                on_realtime_transcription_callback=on_transcription_update,
                on_recording_stop_callback=on_recording_stop,
                language=language
            )
            
            if not recorder:
                return {
                    "success": False,
                    "error": "Failed to create audio recorder",
                    "transcription": "",
                    "duration": 0.0
                }
            
            logger.info("Starting transcription session", max_duration=duration)
            
            # Start recording
            if duration:
                # Record for specified duration
                with self._timeout_context(duration):
                    recorder.listen()
            else:
                # Record until silence
                recorder.listen()
            
            end_time = time.time()
            actual_duration = end_time - start_time
            
            logger.info(
                "Transcription completed",
                duration=actual_duration,
                text_length=len(transcription_result)
            )
            
            return {
                "success": True,
                "transcription": transcription_result.strip(),
                "duration": actual_duration,
                "language": language or self.language,
                "model": self.model_name
            }
            
        except Exception as e:
            end_time = time.time()
            logger.error("Transcription failed", error=str(e), duration=end_time - start_time)
            return {
                "success": False,
                "error": f"Transcription error: {str(e)}",
                "transcription": transcription_result.strip(),
                "duration": end_time - start_time
            }
    
    @contextlib.contextmanager
    def _timeout_context(self, duration: float):
        """Context manager for handling recording timeout."""
        import signal

        class TimeoutError(Exception):
            pass
        
        def timeout_handler(signum, frame):
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
                if hasattr(self._recorder, 'cleanup'):
                    self._recorder.cleanup()
                logger.debug("TranscriptionHandler cleaned up")
            except Exception as e:
                logger.warning("Error during cleanup", error=str(e))
            finally:
                self._recorder = None
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
