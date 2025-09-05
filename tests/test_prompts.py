"""
Tests for Voice MCP prompts.
"""

from voice_mcp.prompts import VoicePrompts


class TestVoicePrompts:
    """Test suite for VoicePrompts class."""

    def test_speak_prompt(self):
        """Test speak prompt generation."""
        prompt = VoicePrompts.speak_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be a substantial prompt
        assert "speak" in prompt.lower()
        assert "tool" in prompt.lower()
        assert "text-to-speech" in prompt.lower()

        # Should contain usage guidelines
        assert "usage" in prompt.lower() or "guidelines" in prompt.lower()

        # Should contain examples
        assert "example" in prompt.lower()

        # Should mention parameters
        assert "voice" in prompt.lower()
        assert "rate" in prompt.lower()
        assert "volume" in prompt.lower()

    def test_prompt_consistency(self):
        """Test that prompts are consistent across calls."""
        # Prompts should be deterministic
        prompt1 = VoicePrompts.speak_prompt()
        prompt2 = VoicePrompts.speak_prompt()
        assert prompt1 == prompt2

    def test_prompt_content_quality(self):
        """Test the quality and completeness of prompt content."""
        speak_prompt = VoicePrompts.speak_prompt()

        # Should provide clear instructions
        assert "when:" in speak_prompt.lower() or "use" in speak_prompt.lower()

        # Should be helpful for AI understanding
        assert any(
            word in speak_prompt.lower()
            for word in ["accessibility", "audio", "voice", "spoken"]
        )

    def test_prompt_structure(self):
        """Test that prompts have good structure."""
        speak_prompt = VoicePrompts.speak_prompt()

        # Should have multiple paragraphs/sections
        assert "\n" in speak_prompt

        # Should have examples section
        assert "example" in speak_prompt.lower()

        # Should have parameters section
        assert "parameter" in speak_prompt.lower()
