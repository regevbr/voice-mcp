#!/usr/bin/env python3
"""
Demo script showing STT usage with simplified implementation.

This script demonstrates how to use the simplified STT functionality
with lazy loading and preloading on server startup.
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from voice_mcp.config import config
from voice_mcp.voice.stt import get_transcription_handler


def main():
    """Main demo function."""
    print("🎤 Voice MCP STT Demo")
    print("=" * 50)

    # Show current configuration
    print("\n📋 Current Configuration:")
    print(f"   STT Enabled: {config.stt_enabled}")
    print(f"   STT Model: {config.stt_model}")
    print(f"   STT Device: {config.stt_device}")
    print(f"   STT Language: {config.stt_language}")
    print(f"   Silence Threshold: {config.stt_silence_threshold}s")

    # Get transcription handler
    stt_handler = get_transcription_handler()

    # Show initial status
    print("\n🔍 STT Status:")
    print(f"   Ready: {stt_handler.is_ready()}")

    if not stt_handler.is_ready():
        print("\n🔧 STT Not Ready - Demonstrating Enable...")
        success = stt_handler.enable()
        print(f"   Enable Result: {success}")
        if success:
            print(f"   Device: {stt_handler.device}")
            print(f"   Compute Type: {stt_handler.compute_type}")
        print(f"   Now Ready: {stt_handler.is_ready()}")
    else:
        print(f"   Device: {stt_handler.device}")
        print(f"   Compute Type: {stt_handler.compute_type}")

    # Demonstrate preloading (if not already loaded)
    if config.stt_enabled:
        print("\n🚀 STT Preloading Demo:")
        print("   Note: STT is configured to preload on server startup")
        print("   This means the model is ready immediately when needed")

        if stt_handler.is_ready():
            print("   ✅ Model is already preloaded and ready!")
        else:
            print("   Loading model now...")
            success = stt_handler.preload()
            print(f"   Preload Result: {success}")
    else:
        print("\n⚠️  STT Preloading Disabled:")
        print("   Set VOICE_MCP_STT_ENABLED=true to preload on startup")
        print("   Models will be loaded on first use instead")

    # Demonstrate transcription
    print("\n🎙️  Transcription Demo:")
    print("   Note: This demo uses mock STT for safety")
    print("   In real usage, this would capture audio from your microphone")

    try:
        # This would normally prompt for audio input
        print("   Simulating transcription request...")

        # For demo purposes, we'll show what would happen
        if stt_handler.is_ready():
            print("   ✅ STT ready - would start audio capture")
            print("   ✅ Audio processing would use preloaded model")
            print("   ✅ Fast response due to no model loading delay")
        else:
            print("   📊 STT not ready - would auto-enable on request")
            print("   📊 First request would load model, subsequent ones fast")

        # In a real scenario:
        # transcription_result = VoiceTools.listen(duration=5.0)
        # print(f"   Transcription: {transcription_result.get('transcription', '')}")

    except Exception as e:
        print(f"   Demo error: {e}")

    # Demonstrate configuration benefits
    print("\n💡 Configuration Benefits:")
    print("   📈 Performance:")
    if config.stt_enabled:
        print("      - Model preloaded on startup = instant first transcription")
        print("      - No loading delays during usage")
        print("      - Consistent performance")
    else:
        print("      - Model loaded on first request = initial delay")
        print("      - Subsequent requests fast (model stays loaded)")
        print("      - Memory efficient (no preload)")

    print("\n   🎛️  Device Selection:")
    print(f"      - Device: {config.stt_device}")
    if config.stt_device == "auto":
        print("      - Automatic CUDA/CPU detection")
        print("      - Optimal performance selection")
    else:
        print(f"      - Fixed device: {config.stt_device}")

    print("\n   🔧 Simplified Architecture:")
    print("      - Single model instance (singleton pattern)")
    print("      - No complex server management")
    print("      - Lazy loading with smart enable/disable")
    print("      - Automatic cleanup on shutdown")

    # Show usage examples
    print("\n📚 Usage Examples:")
    print("   Environment Variables:")
    print("      export VOICE_MCP_STT_ENABLED=true     # Preload on startup")
    print("      export VOICE_MCP_STT_MODEL=small      # Use small model")
    print("      export VOICE_MCP_STT_DEVICE=cuda      # Force CUDA")
    print("      export VOICE_MCP_STT_LANGUAGE=es      # Spanish language")

    print("\n   Python Usage:")
    print("      from voice_mcp.voice.stt import get_transcription_handler")
    print("      handler = get_transcription_handler()")
    print("      result = handler.transcribe_once()")

    print("\n✅ Demo completed!")
    print("\n🎯 Key Improvements:")
    print("   - ~500 lines of complex server code removed")
    print("   - Single, predictable code path")
    print("   - No threading complexity")
    print("   - Model ready immediately if preloaded")
    print("   - Simple enable/disable behavior")
    print("   - Much easier to maintain and debug")


if __name__ == "__main__":
    main()
