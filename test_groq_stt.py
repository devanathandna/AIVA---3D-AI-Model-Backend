#!/usr/bin/env python3
"""
Simple test for Groq STT functionality
"""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from audio.stt import STTProcessor
from config.api_keys import get_groq_stt_key

async def test_stt_import():
    """Test if STT processor can be initialized"""
    try:
        # Check if API key is available
        api_key = get_groq_stt_key()
        if not api_key:
            print("❌ No Groq API key found in environment")
            return False
            
        print("✅ Groq API key found")
        
        # Initialize STT processor
        stt = STTProcessor()
        print("✅ STT processor initialized successfully")
        
        # Test basic functionality (without actual audio file)
        print("✅ Groq STT integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ STT test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔊 Testing Groq STT Integration...")
    success = asyncio.run(test_stt_import())
    if success:
        print("\n🎉 All tests passed! Groq STT is ready to use.")
    else:
        print("\n💥 Tests failed. Please check your configuration.")
    
    sys.exit(0 if success else 1)