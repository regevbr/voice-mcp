"""
AudioManager for handling audio playback with pre-initialization and non-blocking operations.

This module provides a production-ready AudioManager class that handles audio feedback
with proper error handling, logging, and graceful degradation when audio hardware
is not available.
"""

import threading
import wave
from pathlib import Path
from typing import Dict, Any, Optional, Union
import structlog

logger = structlog.get_logger(__name__)

# Check if PyAudio is available
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None


class AudioManager:
    """
    Manages audio playback with pre-initialization and non-blocking operations.
    
    Features:
    - Pre-loads audio files into memory for fast playback
    - Non-blocking audio playback using threading
    - Graceful degradation when audio hardware is unavailable
    - Context manager support for proper resource cleanup
    - Production-ready error handling and logging
    """
    
    def __init__(self, assets_path: Optional[Union[str, Path]] = None) -> None:
        """
        Initialize the AudioManager.
        
        Args:
            assets_path: Path to directory containing audio files.
                        If None, uses the default assets directory.
        """
        self.audio: Optional[pyaudio.PyAudio] = None
        self.audio_data: Dict[str, Dict[str, Any]] = {}
        self._assets_path = self._resolve_assets_path(assets_path)
        self._available = False
        
        logger.info("Initializing AudioManager", assets_path=str(self._assets_path))
        
        self._init_audio_system()
        if self._available:
            self._preload_audio_files()
    
    def __enter__(self) -> "AudioManager":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Context manager exit with cleanup."""
        self.cleanup()
        return False
    
    @property
    def is_available(self) -> bool:
        """Check if audio system is available and functioning."""
        return self._available
    
    def _resolve_assets_path(self, assets_path: Optional[Union[str, Path]]) -> Path:
        """
        Resolve the assets directory path.
        
        Args:
            assets_path: Custom assets path or None for default
            
        Returns:
            Resolved Path object to assets directory
        """
        if assets_path is not None:
            return Path(assets_path)
        
        # Default to assets directory relative to this module
        current_dir = Path(__file__).parent.parent
        return current_dir / "assets"
    
    def _init_audio_system(self) -> None:
        """Initialize PyAudio once at startup."""
        try:
            self.audio = pyaudio.PyAudio()
            self._available = True
            logger.info("Audio system initialized successfully")
        except Exception as e:
            logger.warning(
                "Could not initialize audio system - audio feedback disabled",
                error=str(e),
                recommendation="Check audio hardware and PyAudio installation"
            )
            self.audio = None
    
    def _preload_audio_files(self) -> None:
        """Preload audio files into memory for fast playback."""
        if not self._available:
            return
        
        audio_files = ["on.wav", "off.wav"]
        loaded_count = 0
        
        for filename in audio_files:
            file_path = self._assets_path / filename
            
            if not file_path.exists():
                logger.warning(
                    "Audio file not found",
                    filename=filename,
                    path=str(file_path),
                    recommendation=f"Ensure {filename} exists in assets directory"
                )
                continue
            
            try:
                with wave.open(str(file_path), 'rb') as wf:
                    self.audio_data[filename] = {
                        'frames': wf.readframes(wf.getnframes()),
                        'format': self.audio.get_format_from_width(wf.getsampwidth()),
                        'channels': wf.getnchannels(),
                        'rate': wf.getframerate(),
                        'frames_count': wf.getnframes(),
                        'duration': wf.getnframes() / wf.getframerate()
                    }
                    loaded_count += 1
                    logger.debug(
                        "Audio file preloaded",
                        filename=filename,
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        duration=f"{wf.getnframes() / wf.getframerate():.2f}s"
                    )
            except Exception as e:
                logger.error(
                    "Could not preload audio file",
                    filename=filename,
                    path=str(file_path),
                    error=str(e)
                )
        
        logger.info(
            "Audio preloading complete",
            loaded_files=loaded_count,
            total_files=len(audio_files)
        )
    
    def play_audio_file(self, filename: str) -> bool:
        """
        Play audio file non-blocking using threading.
        
        Args:
            filename: Name of the audio file to play (e.g., "on.wav", "off.wav")
            
        Returns:
            True if playback was initiated successfully, False otherwise
        """
        if not self._available:
            logger.debug("Audio playback skipped - system not available", filename=filename)
            return False
        
        if filename not in self.audio_data:
            logger.warning(
                "Audio file not found in preloaded data",
                filename=filename,
                available_files=list(self.audio_data.keys())
            )
            return False
        
        # Start playback in a separate thread to avoid blocking
        try:
            thread = threading.Thread(
                target=self._play_audio_thread,
                args=(filename,),
                daemon=True,
                name=f"AudioPlayback-{filename}"
            )
            thread.start()
            logger.debug("Audio playback initiated", filename=filename)
            return True
        except Exception as e:
            logger.error(
                "Could not start audio playback thread",
                filename=filename,
                error=str(e)
            )
            return False
    
    def _play_audio_thread(self, filename: str) -> None:
        """
        Internal method to play audio in a separate thread.
        
        Args:
            filename: Name of the audio file to play
        """
        if not self._available or not self.audio:
            return
        
        try:
            audio_info = self.audio_data[filename]
            
            stream = self.audio.open(
                format=audio_info['format'],
                channels=audio_info['channels'],
                rate=audio_info['rate'],
                output=True
            )
            
            # Play the preloaded audio data
            stream.write(audio_info['frames'])
            
            stream.stop_stream()
            stream.close()
            
            logger.debug(
                "Audio playback completed",
                filename=filename,
                duration=f"{audio_info['duration']:.2f}s"
            )
            
        except Exception as e:
            logger.error(
                "Error during audio playback",
                filename=filename,
                error=str(e)
            )
    
    def play_on_sound(self) -> bool:
        """
        Play the 'on' audio feedback sound.
        
        Returns:
            True if playback was initiated successfully, False otherwise
        """
        return self.play_audio_file("on.wav")
    
    def play_off_sound(self) -> bool:
        """
        Play the 'off' audio feedback sound.
        
        Returns:
            True if playback was initiated successfully, False otherwise
        """
        return self.play_audio_file("off.wav")

    def cleanup(self) -> None:
        """Clean up audio resources."""
        if self.audio:
            try:
                self.audio.terminate()
                logger.debug("Audio system cleanup completed")
            except Exception as e:
                logger.warning("Error during audio system cleanup", error=str(e))
            finally:
                self.audio = None
                self._available = False
        
        # Clear preloaded audio data
        self.audio_data.clear()