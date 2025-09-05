"""
MCP prompts for voice functionality.
"""


class VoicePrompts:
    """Container for voice-related MCP prompts."""
    
    @staticmethod
    def speak_prompt() -> str:
        """
        Prompt to guide AI usage of the speak tool.
        
        Returns:
            A prompt that instructs the AI how to use the speak tool effectively.
        """
        return """You have access to a 'speak' tool that can convert text to speech. Use this tool when:

1. The user explicitly requests text-to-speech or asks you to "speak" something
2. You want to provide audio output for accessibility
3. The user asks for voice output or audio feedback

Usage guidelines:
- Use clear, natural language that sounds good when spoken
- Keep spoken text concise and well-structured
- Consider the user's context and preferences
- Use appropriate voice settings if specified

Example usage:
- speak("Hello! I'm ready to help you with voice interactions.")
- speak("Here's the summary of your document: [brief summary]")

The tool accepts optional parameters:
- voice: specify a particular voice if available
- rate: adjust speech speed (words per minute)
- volume: set volume level (0.0 to 1.0)

Additional TTS Management Tools:
- get_tts_info(): Get detailed information about TTS engine, available voices, and configuration
- stop_speech(): Immediately stop any current speech output
- server_status(): Get comprehensive server status and configuration details"""
    
