"""
MCP tools for voice functionality.
"""

from typing import Any

import structlog

from .config import config
from .voice.audio import AudioManager
from .voice.hotkey import HotkeyManager
from .voice.stt import get_transcription_handler
from .voice.text_output import OutputMode, TextOutputController
from .voice.tts import TTSManager

logger = structlog.get_logger(__name__)

# Initialize managers
_tts_manager = None
_audio_manager = None
_text_output_controller = None
_hotkey_manager = None


def get_tts_manager() -> TTSManager:
    """Get or create TTS manager instance."""
    global _tts_manager
    if _tts_manager is None:
        _tts_manager = TTSManager(
            model_name=config.tts_model, gpu_enabled=config.tts_gpu_enabled
        )
    return _tts_manager


def get_audio_manager() -> AudioManager:
    """Get or create AudioManager instance."""
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManager()
    return _audio_manager


def get_text_output_controller() -> TextOutputController:
    """Get or create text output controller instance."""
    global _text_output_controller
    if _text_output_controller is None:
        _text_output_controller = TextOutputController(
            debounce_delay=config.typing_debounce_delay
        )
    return _text_output_controller


def get_hotkey_manager() -> HotkeyManager:
    """Get or create hotkey manager instance."""
    global _hotkey_manager
    if _hotkey_manager is None:
        _hotkey_manager = HotkeyManager(on_hotkey_pressed=_on_hotkey_pressed)
    return _hotkey_manager


def _on_hotkey_pressed() -> None:
    """Callback function when hotkey is pressed."""
    try:
        logger.info("Hotkey activated, starting real-time STT")

        # Use typing mode for real-time display during hotkey usage
        if config.hotkey_output_mode == "typing":
            # Use real-time transcription with live typing
            stt_handler = get_transcription_handler()
            text_controller = get_text_output_controller()

            # Reset text controller state for new session
            text_controller.reset()

            # Play "on" sound to indicate recording start
            audio_manager = get_audio_manager()
            if audio_manager.is_available:
                audio_manager.play_on_sound()

            # Perform real-time transcription with live typing
            result = stt_handler.transcribe_with_realtime_output(
                text_output_controller=text_controller,
                duration=None,  # Use silence-based stopping
                language=config.stt_language,
            )

            # Play "off" sound to indicate recording stop
            if audio_manager.is_available:
                audio_manager.play_off_sound()

            # Log the result
            if result.get("success"):
                logger.info(
                    "Hotkey real-time STT completed successfully",
                    text_length=len(result.get("transcription", "")),
                    duration=result.get("duration", 0),
                )
            else:
                logger.warning(
                    "Hotkey real-time STT failed",
                    error=result.get("error"),
                )
        else:
            # Fallback to standard listen mode for non-typing output modes
            result = VoiceTools.listen(
                duration=None,  # Use silence-based stopping
                language=config.stt_language,
                output_mode=config.hotkey_output_mode,  # type: ignore
            )

            # Log the result for debugging
            if result.get("status") == "success":
                text = result.get("transcription", "")
                logger.info(
                    "Hotkey STT completed successfully",
                    text_length=len(text),
                    duration=result.get("duration", 0),
                    output_mode=result.get("output_mode"),
                )
            else:
                logger.warning(
                    "Hotkey STT failed",
                    error=result.get("error"),
                    status=result.get("status"),
                )

    except Exception as e:
        logger.error("Hotkey callback error", error=str(e), exc_info=True)


class VoiceTools:
    """Container for voice-related MCP tools."""

    @staticmethod
    def speak(
        text: str,
        voice: str | None = None,
        rate: float | None = None,
        volume: float | None = None,
    ) -> str:
        """
        Convert text to speech using the configured TTS engine.

        Args:
            text: The text to convert to speech
            voice: Optional voice to use (system-dependent)
            rate: Optional speech rate (words per minute)
            volume: Optional volume level (0.0 to 1.0)

        Returns:
            Status message indicating success or failure
        """
        if not text or not text.strip():
            return "❌ No text provided to speak"

        logger.info(f"TTS request: {text[:50]}...")

        try:
            tts = get_tts_manager()

            # Use configuration defaults if not specified
            if rate is None:
                rate = config.tts_rate
            if volume is None:
                volume = config.tts_volume

            result = tts.speak(text, voice, rate, volume)
            logger.info(f"TTS result: {result}")
            return result

        except Exception as e:
            error_msg = f"❌ TTS error: {str(e)}"
            logger.error(error_msg)
            return error_msg

    @staticmethod
    def listen(
        duration: float | None = None,
        language: str = "en",
        output_mode: OutputMode = "return",
    ) -> dict[str, Any]:
        """
        Listen for speech input and convert to text with various output modes.

        NOTE: This method is kept internal for hotkey functionality support.

        Args:
            duration: Maximum duration to listen (seconds, None for silence-based stopping)
            language: Language for speech recognition
            output_mode: How to output the text ("typing", "clipboard", "return")

        Returns:
            Dictionary with transcription results and metadata
        """
        logger.info(
            "STT request started",
            duration=duration,
            language=language,
            output_mode=output_mode,
        )

        try:
            # Get the singleton transcription handler
            stt_handler = get_transcription_handler()

            # Play "on" sound to indicate recording start
            audio_manager = get_audio_manager()
            if audio_manager.is_available:
                audio_manager.play_on_sound()

            # Perform transcription using the simplified handler
            result = stt_handler.transcribe_once(duration=duration, language=language)

            # Play "off" sound to indicate recording stop
            if audio_manager.is_available:
                audio_manager.play_off_sound()

            if not result["success"]:
                logger.error("Transcription failed", error=result.get("error"))
                return {
                    "transcription": result.get("transcription", ""),
                    "status": "error",
                    "error": result.get("error", "Unknown transcription error"),
                    "duration": result.get("duration", 0.0),
                    "language": language,
                    "output_mode": output_mode,
                }

            transcribed_text = result["transcription"]

            # Handle output mode
            if output_mode != "return" and transcribed_text:
                text_controller = get_text_output_controller()
                output_result = text_controller.output_text(
                    transcribed_text, output_mode
                )

                if not output_result["success"]:
                    logger.warning(
                        "Text output failed", error=output_result.get("error")
                    )
                    # Still return the transcription even if output failed
                    return {
                        "transcription": transcribed_text,
                        "status": "partial_success",
                        "warning": f"Transcription successful but output failed: {output_result.get('error')}",
                        "duration": result["duration"],
                        "language": result.get("language", language),
                        "output_mode": output_mode,
                    }
                else:
                    logger.debug("Text output successful", mode=output_mode)

            logger.info(
                "STT request completed successfully",
                text_length=len(transcribed_text),
                duration=result["duration"],
                output_mode=output_mode,
            )

            return {
                "transcription": transcribed_text,
                "status": "success",
                "duration": result["duration"],
                "language": result.get("language", language),
                "output_mode": output_mode,
                "model": result.get("model", config.stt_model),
            }

        except Exception as e:
            error_msg = f"STT error: {str(e)}"
            logger.error(error_msg, exc_info=True)

            # Try to play "off" sound even on error
            try:
                audio_manager = get_audio_manager()
                if audio_manager.is_available:
                    audio_manager.play_off_sound()
            except Exception:
                pass

            return {
                "transcription": "",
                "status": "error",
                "error": error_msg,
                "duration": 0.0,
                "language": language,
                "output_mode": output_mode,
            }

    @staticmethod
    def start_hotkey_monitoring() -> str:
        """
        Start global hotkey monitoring for STT activation.

        Returns:
            Status message indicating success or failure
        """
        if not config.enable_hotkey:
            return "⚠️  Hotkey monitoring is disabled in configuration"

        try:
            hotkey_manager = get_hotkey_manager()
            result = hotkey_manager.start_monitoring(config.hotkey_name)

            if result["success"]:
                logger.info(
                    "Hotkey monitoring started via tools", hotkey=config.hotkey_name
                )
                return f"✅ Hotkey monitoring started ({result.get('description', config.hotkey_name)})"
            else:
                error_msg = f"❌ Failed to start hotkey monitoring: {result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"❌ Error starting hotkey monitoring: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    @staticmethod
    def stop_hotkey_monitoring() -> str:
        """
        Stop global hotkey monitoring.

        Returns:
            Status message indicating success or failure
        """
        try:
            hotkey_manager = get_hotkey_manager()
            result = hotkey_manager.stop_monitoring()

            if result["success"]:
                logger.info("Hotkey monitoring stopped via tools")
                return f"✅ {result.get('message', 'Hotkey monitoring stopped')}"
            else:
                error_msg = f"❌ Failed to stop hotkey monitoring: {result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"❌ Error stopping hotkey monitoring: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    @staticmethod
    def get_hotkey_status() -> dict[str, Any]:
        """
        Get current hotkey monitoring status.

        Returns:
            Dictionary with hotkey status and configuration
        """
        try:
            hotkey_manager = get_hotkey_manager()
            status = hotkey_manager.get_status()

            # Add configuration information
            status.update(
                {
                    "configuration": {
                        "enabled": config.enable_hotkey,
                        "hotkey_name": config.hotkey_name,
                        "output_mode": config.hotkey_output_mode,
                        "language": config.stt_language,
                    }
                }
            )

            logger.debug("Hotkey status requested", status=status)
            return status

        except Exception as e:
            error_info = {
                "status": "error",
                "error": str(e),
                "active": False,
                "configuration": {
                    "enabled": config.enable_hotkey,
                    "hotkey_name": config.hotkey_name,
                    "output_mode": config.hotkey_output_mode,
                    "language": config.stt_language,
                },
            }
            logger.error("Error getting hotkey status", error=str(e))
            return error_info
