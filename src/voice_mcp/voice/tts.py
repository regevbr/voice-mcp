"""
Text-to-Speech engine implementation with multiple backends.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Voice:
    """Represents a TTS voice."""
    id: str
    name: str
    language: str
    gender: Optional[str] = None
    age: Optional[str] = None


class TTSEngine(ABC):
    """Abstract base class for TTS engines."""
    
    @abstractmethod
    def speak(self, text: str, voice: Optional[str] = None, rate: Optional[int] = None, 
             volume: Optional[float] = None) -> bool:
        """
        Convert text to speech.
        
        Args:
            text: Text to convert to speech
            voice: Voice ID to use
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_voices(self) -> List[Voice]:
        """Get available voices."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the TTS engine is available."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop current speech."""
        pass


class Pyttsx3Engine(TTSEngine):
    """pyttsx3-based TTS engine for offline speech synthesis."""
    
    def __init__(self):
        self._engine = None
        self._initialized = False
        self._init_engine()
    
    def _init_engine(self) -> None:
        """Initialize the pyttsx3 engine."""
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._initialized = True
            logger.info("pyttsx3 engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3 engine: {e}")
            self._engine = None
            self._initialized = False
    
    def speak(self, text: str, voice: Optional[str] = None, rate: Optional[int] = None, 
             volume: Optional[float] = None) -> bool:
        """Convert text to speech using pyttsx3."""
        if not self.is_available():
            logger.error("pyttsx3 engine not available")
            return False
        
        try:
            # Set voice if specified
            if voice:
                voices = self._engine.getProperty('voices')
                for v in voices:
                    if v.id == voice or v.name == voice:
                        self._engine.setProperty('voice', v.id)
                        break
            
            # Set rate if specified
            if rate:
                self._engine.setProperty('rate', rate)
            
            # Set volume if specified  
            if volume is not None:
                self._engine.setProperty('volume', max(0.0, min(1.0, volume)))
            
            # Speak the text
            self._engine.say(text)
            self._engine.runAndWait()
            
            logger.debug(f"Successfully spoke text: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error during speech synthesis: {e}")
            return False
    
    def get_voices(self) -> List[Voice]:
        """Get available voices from pyttsx3."""
        if not self.is_available():
            return []
        
        try:
            voices = self._engine.getProperty('voices')
            return [
                Voice(
                    id=voice.id,
                    name=voice.name,
                    language=getattr(voice, 'languages', ['unknown'])[0] if hasattr(voice, 'languages') else 'unknown',
                    gender=getattr(voice, 'gender', None),
                    age=getattr(voice, 'age', None)
                )
                for voice in voices if voice is not None
            ]
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if pyttsx3 engine is available."""
        return self._initialized and self._engine is not None
    
    def stop(self) -> None:
        """Stop current speech."""
        if self.is_available():
            try:
                self._engine.stop()
            except Exception as e:
                logger.error(f"Error stopping speech: {e}")


class GTTSEngine(TTSEngine):
    """gTTS-based TTS engine for cloud-based speech synthesis."""
    
    def __init__(self):
        self._available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if gTTS is available."""
        try:
            import gtts
            import pygame  # For audio playback
            return True
        except ImportError as e:
            logger.warning(f"gTTS not available: {e}")
            return False
    
    def speak(self, text: str, voice: Optional[str] = None, rate: Optional[int] = None, 
             volume: Optional[float] = None) -> bool:
        """Convert text to speech using gTTS."""
        if not self.is_available():
            logger.error("gTTS engine not available")
            return False
        
        try:
            from gtts import gTTS
            import pygame
            import tempfile
            import os
            
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                temp_path = tmp_file.name
            
            try:
                # Generate speech with gTTS
                language = voice if voice in ['en', 'es', 'fr', 'de', 'it'] else 'en'
                tts = gTTS(text=text, lang=language, slow=False)
                tts.save(temp_path)
                
                # Play audio with pygame
                pygame.mixer.init()
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                
                # Wait for playback to complete
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                
                logger.debug(f"Successfully spoke text with gTTS: {text[:50]}...")
                return True
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error during gTTS synthesis: {e}")
            return False
    
    def get_voices(self) -> List[Voice]:
        """Get available languages for gTTS."""
        if not self.is_available():
            return []
        
        # gTTS supports many languages, but we'll return common ones
        return [
            Voice(id='en', name='English', language='en'),
            Voice(id='es', name='Spanish', language='es'), 
            Voice(id='fr', name='French', language='fr'),
            Voice(id='de', name='German', language='de'),
            Voice(id='it', name='Italian', language='it'),
        ]
    
    def is_available(self) -> bool:
        """Check if gTTS engine is available."""
        return self._available
    
    def stop(self) -> None:
        """Stop current speech."""
        try:
            import pygame
            pygame.mixer.music.stop()
        except:
            pass


class TTSManager:
    """Manages multiple TTS engines with fallback support."""
    
    def __init__(self, preferred_engine: str = "pyttsx3"):
        self.engines: Dict[str, TTSEngine] = {
            "pyttsx3": Pyttsx3Engine(),
            "gtts": GTTSEngine(),
        }
        
        self.preferred_engine = preferred_engine
        self._current_engine = None
        self._select_engine()
    
    def _select_engine(self) -> None:
        """Select the best available engine."""
        # Try preferred engine first
        if self.preferred_engine in self.engines and self.engines[self.preferred_engine].is_available():
            self._current_engine = self.engines[self.preferred_engine]
            logger.info(f"Using {self.preferred_engine} TTS engine")
            return
        
        # Fallback to any available engine
        for name, engine in self.engines.items():
            if engine.is_available():
                self._current_engine = engine
                logger.info(f"Falling back to {name} TTS engine")
                return
        
        logger.error("No TTS engines available")
        self._current_engine = None
    
    def speak(self, text: str, voice: Optional[str] = None, rate: Optional[int] = None, 
             volume: Optional[float] = None) -> str:
        """
        Convert text to speech using the current engine.
        
        Returns:
            Status message
        """
        if not self._current_engine:
            return "❌ No TTS engines available"
        
        if not text or not text.strip():
            return "❌ No text provided to speak"
        
        # Truncate very long text
        if len(text) > 1000:
            text = text[:1000] + "... (truncated)"
            logger.warning("Text truncated to 1000 characters for TTS")
        
        try:
            success = self._current_engine.speak(text, voice, rate, volume)
            if success:
                return f"✅ Successfully spoke: '{text[:50]}...'"
            else:
                return f"❌ Failed to speak text"
                
        except Exception as e:
            logger.error(f"Error in TTS speak: {e}")
            return f"❌ TTS error: {str(e)}"
    
    def get_voices(self) -> List[Voice]:
        """Get available voices from current engine."""
        if not self._current_engine:
            return []
        
        return self._current_engine.get_voices()
    
    def get_voice_info(self) -> Dict[str, Any]:
        """Get information about current TTS setup."""
        if not self._current_engine:
            return {"status": "no_engine", "voices": []}
        
        voices = self.get_voices()
        return {
            "status": "available",
            "engine": type(self._current_engine).__name__,
            "voice_count": len(voices),
            "voices": [{"id": v.id, "name": v.name, "language": v.language} for v in voices[:5]]  # Limit to 5 for brevity
        }
    
    def stop(self) -> None:
        """Stop current speech."""
        if self._current_engine:
            self._current_engine.stop()
    
    def is_available(self) -> bool:
        """Check if any TTS engine is available."""
        return self._current_engine is not None