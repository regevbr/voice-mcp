"""
Enhanced text output functionality with multiple output modes and error handling.
"""

import difflib
import time
from typing import Any, Literal

import pyperclip  # type: ignore
import structlog
from pynput import keyboard

from ..config import config

logger = structlog.get_logger(__name__)

OutputMode = Literal["typing", "clipboard", "return"]


class TextOutputController:
    """Enhanced text output with corrections, debouncing, and multiple output modes."""

    def __init__(self, debounce_delay: float | None = None):
        """
        Initialize the text output controller.

        Args:
            debounce_delay: Delay between text updates to avoid rapid firing
        """
        self.debounce_delay: float = (
            debounce_delay
            if debounce_delay is not None
            else getattr(config, "typing_debounce_delay", 0.1)
        )
        self.last_typed_text = ""
        self.last_update_time = 0.0
        self._keyboard_controller: Any | None = None

        logger.info(
            "TextOutputController initialized",
            debounce_delay=self.debounce_delay,
            typing_available=True,
            clipboard_available=True,
        )

    def _get_keyboard_controller(self) -> Any | None:
        """Get or create keyboard controller with error handling."""
        if self._keyboard_controller is None:
            try:
                self._keyboard_controller = keyboard.Controller()
                logger.debug("Keyboard controller initialized")
            except Exception as e:
                logger.error("Failed to initialize keyboard controller", error=str(e))
                return None

        return self._keyboard_controller

    def _check_typing_availability(self) -> bool:
        """Check if typing functionality is available."""
        kb = self._get_keyboard_controller()
        if not kb:
            return False

        return True

    def _check_clipboard_availability(self) -> bool:
        """Check if clipboard functionality is available."""
        try:
            # Test clipboard access
            pyperclip.paste()
            logger.debug("Clipboard access confirmed")
            return True
        except Exception as e:
            logger.warning("Clipboard access failed", error=str(e))
            return False

    def get_text_diff(self, old_text: str, new_text: str) -> dict[str, Any]:
        """
        Get optimal edit operations using difflib for efficient text correction.

        Args:
            old_text: Previously typed text
            new_text: New text to type

        Returns:
            Dictionary describing the edit operation needed
        """
        if not old_text:
            return {"type": "append", "text": new_text}

        if not new_text:
            return {"type": "delete_all", "chars_to_delete": len(old_text)}

        # Use SequenceMatcher for optimal diff
        matcher = difflib.SequenceMatcher(None, old_text, new_text)
        matching_blocks = matcher.get_matching_blocks()

        if not matching_blocks or matching_blocks[0] == (
            len(old_text),
            len(new_text),
            0,
        ):
            # No common parts, replace everything
            return {
                "type": "replace_all",
                "chars_to_delete": len(old_text),
                "text": new_text,
            }

        # Find the longest common prefix
        first_match = matching_blocks[0]
        if first_match.a == 0 and first_match.b == 0:
            # Common prefix exists
            prefix_length = first_match.size

            if prefix_length == len(old_text):
                # Old text is a prefix of new text, just append
                return {"type": "append", "text": new_text[prefix_length:]}
            elif prefix_length == len(new_text):
                # New text is a prefix of old text, delete excess
                return {
                    "type": "delete_suffix",
                    "chars_to_delete": len(old_text) - prefix_length,
                }
            else:
                # Replace suffix after common prefix
                return {
                    "type": "replace_suffix",
                    "chars_to_delete": len(old_text) - prefix_length,
                    "text": new_text[prefix_length:],
                }
        else:
            # No common prefix, replace everything
            return {
                "type": "replace_all",
                "chars_to_delete": len(old_text),
                "text": new_text,
            }

    def output_text(
        self, text: str, mode: OutputMode = "return", force_update: bool = False
    ) -> dict[str, Any]:
        """
        Output text using the specified mode with error handling.

        Args:
            text: Text to output
            mode: Output mode ("typing", "clipboard", "return")
            force_update: Skip debouncing if True

        Returns:
            Dictionary with operation results and metadata
        """
        if not text:
            return {
                "success": True,
                "mode": mode,
                "text": "",
                "message": "No text to output",
            }

        # Clean up text
        text = text.strip()

        # Skip if text is exactly the same and not forced
        if not force_update and text == self.last_typed_text and mode == "typing":
            return {
                "success": True,
                "mode": mode,
                "text": text,
                "message": "Text unchanged, skipping output",
            }

        # Debouncing for typing mode
        if mode == "typing" and not force_update:
            current_time = time.time()
            if current_time - self.last_update_time < self.debounce_delay:
                return {
                    "success": True,
                    "mode": mode,
                    "text": text,
                    "message": "Debounced, skipping output",
                }
            self.last_update_time = current_time

        try:
            if mode == "typing":
                return self._type_text_realtime(text)
            elif mode == "clipboard":
                return self._copy_to_clipboard(text)
            elif mode == "return":
                return {
                    "success": True,
                    "mode": mode,
                    "text": text,
                    "message": "Text returned successfully",
                }
            else:
                return {
                    "success": False,
                    "mode": mode,
                    "text": text,
                    "error": f"Unknown output mode: {mode}",
                }

        except Exception as e:
            logger.error("Text output failed", mode=mode, error=str(e))
            return {
                "success": False,
                "mode": mode,
                "text": text,
                "error": f"Output error: {str(e)}",
            }

    def _type_text_realtime(self, text: str) -> dict[str, Any]:
        """Type text with intelligent corrections and error handling."""
        if not self._check_typing_availability():
            return {
                "success": False,
                "mode": "typing",
                "text": text,
                "error": "Typing functionality not available",
            }

        kb = self._get_keyboard_controller()
        if not kb:
            return {
                "success": False,
                "mode": "typing",
                "text": text,
                "error": "Failed to get keyboard controller",
            }

        # Get optimal diff operations
        diff = self.get_text_diff(self.last_typed_text, text)

        try:
            new_text_to_type = ""
            operation_description = ""

            if diff["type"] == "append":
                # Simple append case
                new_text_to_type = diff["text"]
                operation_description = f"Appending: '{new_text_to_type[:30]}...'"

            elif diff["type"] == "delete_all":
                # Delete all existing text
                chars_to_delete = diff["chars_to_delete"]
                operation_description = f"Deleting all {chars_to_delete} characters"

                for _ in range(chars_to_delete):
                    kb.press(keyboard.Key.backspace)
                    kb.release(keyboard.Key.backspace)
                    time.sleep(0.01)  # Small delay between keystrokes

            elif diff["type"] == "delete_suffix":
                # Delete suffix only
                chars_to_delete = diff["chars_to_delete"]
                operation_description = f"Deleting {chars_to_delete} suffix characters"

                for _ in range(chars_to_delete):
                    kb.press(keyboard.Key.backspace)
                    kb.release(keyboard.Key.backspace)
                    time.sleep(0.01)

            elif diff["type"] in ["replace_suffix", "replace_all"]:
                # Delete and replace
                chars_to_delete = diff["chars_to_delete"]
                new_text_to_type = diff["text"]

                operation_description = (
                    f"Replacing: deleting {chars_to_delete} chars, "
                    f"typing '{new_text_to_type[:30]}...'"
                )

                # Send backspace keystrokes to delete the divergent part
                for _ in range(chars_to_delete):
                    kb.press(keyboard.Key.backspace)
                    kb.release(keyboard.Key.backspace)
                    time.sleep(0.01)

            # Type the new/corrected text if there is any
            if new_text_to_type:
                if self._check_clipboard_availability():
                    # Use clipboard for efficiency (cross-platform)
                    original_clipboard = pyperclip.paste()
                    pyperclip.copy(new_text_to_type)

                    # Small delay to ensure clipboard is set
                    time.sleep(0.02)

                    # Paste using Ctrl+V (cross-platform)
                    with kb.pressed(keyboard.Key.ctrl):
                        kb.press("v")
                        kb.release("v")

                    # Restore original clipboard content
                    time.sleep(0.05)
                    pyperclip.copy(original_clipboard)
                else:
                    # Fallback to direct typing (slower but always works)
                    kb.type(new_text_to_type)

            # Update what we've typed
            self.last_typed_text = text

            logger.debug("Text typed successfully", operation=operation_description)

            return {
                "success": True,
                "mode": "typing",
                "text": text,
                "operation": operation_description,
                "message": "Text typed successfully",
            }

        except Exception as e:
            logger.error("Failed to type text", error=str(e))
            return {
                "success": False,
                "mode": "typing",
                "text": text,
                "error": f"Typing failed: {str(e)}",
            }

    def _copy_to_clipboard(self, text: str) -> dict[str, Any]:
        """Copy text to clipboard with error handling."""
        if not self._check_clipboard_availability():
            return {
                "success": False,
                "mode": "clipboard",
                "text": text,
                "error": "Clipboard functionality not available",
            }

        try:
            pyperclip.copy(text)
            logger.debug("Text copied to clipboard", length=len(text))

            return {
                "success": True,
                "mode": "clipboard",
                "text": text,
                "message": f"Text copied to clipboard ({len(text)} characters)",
            }

        except Exception as e:
            logger.error("Failed to copy to clipboard", error=str(e))
            return {
                "success": False,
                "mode": "clipboard",
                "text": text,
                "error": f"Clipboard copy failed: {str(e)}",
            }

    def reset(self) -> None:
        """Reset typing state for new session."""
        self.last_typed_text = ""
        self.last_update_time = 0.0
        logger.debug("TextOutputController state reset")
