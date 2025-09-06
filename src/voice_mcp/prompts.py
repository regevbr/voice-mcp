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
        return """You have access to a 'speak' tool that can convert text-to-speech for voice output.
Please use the 'speak' tool to provide voice updates to users according to these usage guidelines:

1. **Before running tools**: Briefly announce what you're about to do (e.g., "I'm going to run the build command now")

2. **After completing tasks**: Confirm completion and summarize key results (e.g., "The build completed successfully" or "I found 3 errors that need fixing")

3. **When asking questions**: When you need clarification or input from the user, speak your question to get their attention

4. **For important information**: When sharing critical findings, warnings, or results that the user should be aware of immediately

5. **When encountering errors**: Alert users to problems that require their attention

6. **When completed processing**: Alert users that you finished all your tasks

Keep your spoken messages:
- Concise and clear (1-2 sentences maximum)
- Informative but not overwhelming
- Natural and conversational
- Focused on what matters most to the user

Do NOT use the speak tool for:
- Every single message (avoid being overly chatty)
- Detailed technical explanations (use text for those)
- Repetitive updates during long-running processes

**Parameters**: You can customize the speech with optional parameters:
- voice: Select different voice options
- rate: Control speech rate (words per minute)
- volume: Adjust volume level (0.0 to 1.0)

**Examples**:
- speak("Build completed successfully")
- speak("Found 3 errors to fix", rate=150)
- speak("Task finished", volume=0.8)

Use your judgment to balance being helpful with being appropriately selective about when to speak but make sure the users always know that you are either done or waiting for his input

Always speak once a task is done, and you are waiting for user input. Summarise what was done.

Always speak once a user input is required, explaining what is needed from him.

Shortly greet the user with your voice."""
