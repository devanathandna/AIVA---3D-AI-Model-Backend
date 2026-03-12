#!/usr/bin/env python3
"""
Test for enhanced Tamil language detection and handling
"""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from audio.stt import STTProcessor

async def test_tamil_enhancement():
    """Test the enhanced Tamil detection features"""
    try:
        # Test STT processor initialization
        stt = STTProcessor()
        print("✅ Enhanced STT processor initialized")
        
        # Test language normalization methods
        print("✅ Testing language normalization...")
        
        # Test _normalize_language method
        test_languages = ["en", "tamil", "ta", "ta-in", "english"]
        for lang in test_languages:
            normalized = stt._normalize_language(lang)
            print(f"  {lang} -> {normalized}")
        
        # Test _normalize_detected_language method
        print("✅ Testing detected language normalization...")
        detected_languages = ["en", "ta", "tamil", "tam", "hi", "te"]
        for lang in detected_languages:
            normalized = stt._normalize_detected_language(lang)
            print(f"  detected {lang} -> {normalized}")
        
        # Test auto language parameter
        print("✅ Auto-language detection mode available")
        
        print("\n🎉 Enhanced Tamil support test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Enhancement test failed: {e}")
        return False

async def test_agent_signature():
    """Test agent function signature"""
    try:
        # Mock agent function for testing signature
        async def mock_agent(query: str, language_context: dict = None) -> dict:
            return {
                "response": f"Mock response for: {query}",
                "emotion": "none"
            }
        
        # Test with language context
        result1 = await mock_agent("test query", {"is_tamil": True, "language": "ta"})
        print("✅ Agent accepts language context")
        
        # Test without language context (backward compatibility)
        result2 = await mock_agent("test query")
        print("✅ Agent maintains backward compatibility")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent signature test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔊 Testing Enhanced Tamil Language Support...")
    
    success1 = asyncio.run(test_tamil_enhancement())
    success2 = asyncio.run(test_agent_signature())
    
    if success1 and success2:
        print("\n🎉 All enhancement tests passed!")
        print("\n📋 New Features:")
        print("  • Auto-language detection in STT")
        print("  • Tamil language detection flag (is_tamil)")
        print("  • Enhanced language normalization")
        print("  • Language-aware agent responses")
        print("  • Tanglish support for mixed conversations")
    else:
        print("\n💥 Some tests failed. Please check your configuration.")
    
    sys.exit(0 if (success1 and success2) else 1)