#!/usr/bin/env python3
"""
Demo script showing STT Server mode usage.

This script demonstrates how to use the STT server mode functionality
for improved performance with persistent model loading.
"""

import sys
import os
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from voice_mcp.tools import VoiceTools
from voice_mcp.config import config


def main():
    """Main demo function."""
    print("🎤 Voice MCP STT Server Demo")
    print("=" * 50)
    
    # Show current configuration
    print("\n📋 Current Configuration:")
    print(f"   STT Model: {config.stt_model}")
    print(f"   Server Mode: {config.stt_server_mode}")
    print(f"   Preload Models: {config.stt_preload_models}")
    print(f"   Cache Size: {config.stt_model_cache_size}")
    print(f"   Model Timeout: {config.stt_model_timeout}s")
    
    # Get initial STT status
    print("\n🔍 Initial STT Status:")
    stt_info = VoiceTools.get_stt_info()
    print(f"   Available: {stt_info.get('available', False)}")
    if stt_info.get('server_mode'):
        server_status = stt_info['server_mode'].get('server_status')
        if server_status:
            print(f"   Server Active: {server_status.get('active', False)}")
    
    # Demonstrate server management
    print("\n🚀 Starting STT Server...")
    result = VoiceTools.start_stt_server()
    print(f"   Result: {result}")
    
    time.sleep(1)  # Give server time to start
    
    # Get server status
    print("\n📊 Server Status:")
    status = VoiceTools.get_stt_server_status()
    if status.get("active"):
        print(f"   Active: {status['active']}")
        print(f"   Loaded Models: {status.get('model_count', 0)}")
        if status.get('loaded_models'):
            for model in status['loaded_models']:
                print(f"     - {model['name']} ({model['device']})")
        print(f"   Memory Usage: {status.get('total_model_memory', 0) / 1024 / 1024:.1f} MB")
    else:
        print(f"   Status: {status.get('status', 'unknown')}")
        if 'error' in status:
            print(f"   Error: {status['error']}")
    
    # Demonstrate model management
    if status.get("active"):
        print("\n🔧 Model Management Demo:")
        
        # Preload a model
        print("   Preloading 'small' model...")
        result = VoiceTools.preload_stt_model("small")
        print(f"   Result: {result}")
        
        time.sleep(1)
        
        # Get updated status
        status = VoiceTools.get_stt_server_status()
        print(f"   Updated model count: {status.get('model_count', 0)}")
        
        # Warm up a model
        print("   Warming up 'base' model...")
        result = VoiceTools.warm_stt_model("base")
        print(f"   Result: {result}")
        
        # Demonstrate transcription (would work with real audio)
        print("\n🎙️  Transcription Demo:")
        print("   Note: This demo uses mock STT - in real usage, this would")
        print("   use the persistent models for faster performance!")
        
        try:
            # This would normally prompt for audio input
            transcription_result = VoiceTools.listen(duration=0.1)  # Very short for demo
            print(f"   Transcription Status: {transcription_result.get('status')}")
            if transcription_result.get('transcription'):
                print(f"   Text: {transcription_result['transcription']}")
        except Exception as e:
            print(f"   Transcription skipped: {e}")
        
        # Clean up - unload a model
        print("\n🧹 Cleanup Demo:")
        print("   Unloading 'small' model...")
        result = VoiceTools.unload_stt_model("small")
        print(f"   Result: {result}")
    
    # Stop the server
    print("\n🛑 Stopping STT Server...")
    result = VoiceTools.stop_stt_server()
    print(f"   Result: {result}")
    
    # Final status check
    print("\n📊 Final Status:")
    status = VoiceTools.get_stt_server_status()
    print(f"   Active: {status.get('active', False)}")
    
    print("\n✅ Demo completed!")
    print("\n💡 Usage Tips:")
    print("   - Set VOICE_MCP_STT_SERVER_MODE=true to enable server mode")
    print("   - Set VOICE_MCP_STT_PRELOAD_MODELS=base,small to preload multiple models")
    print("   - Set VOICE_MCP_STT_MODEL_CACHE_SIZE=3 to cache more models")
    print("   - Server mode provides faster transcription by avoiding model reloading")
    print("   - Use model warming for best performance on first use")


if __name__ == "__main__":
    main()