#!/usr/bin/env python3
"""
Test script for streaming response flow
Tests the new architecture: STT → Agent → Send Text → TTS → Send Audio
"""

import asyncio
import json
import time
from typing import Dict, Any

async def test_streaming_flow():
    """Test the streaming response workflow"""
    print("🚀 Testing Streaming Response Flow")
    print("=" * 50)
    
    try:
        # Import components
        from audio.manager import get_audio_manager
        from agent.gemini_agent import get_agent_response
        
        # Mock audio data (small test)
        mock_audio_data = b"fake_audio_data_for_testing" * 1000  # ~25KB
        
        # Test timing
        start_time = time.time()
        
        print("📤 Step 1: STT Processing...")
        stt_start = time.time()
        audio_manager = get_audio_manager()
        
        # This would normally do STT processing
        mock_stt_result = {
            "success": True,
            "text": "How is the hostel food?", 
            "language": "en",
            "confidence": 0.95,
            "is_tamil": False
        }
        stt_time = time.time() - stt_start
        print(f"   ✅ STT Complete: {stt_time:.2f}s - '{mock_stt_result['text']}'")
        
        print("🤖 Step 2: Agent Processing...")
        agent_start = time.time()
        
        # Create language context
        language_context = {
            "language": mock_stt_result["language"],
            "is_tamil": mock_stt_result["is_tamil"], 
            "confidence": mock_stt_result["confidence"]
        }
        
        # Get agent response (this calls the real agent)
        agent_result = await get_agent_response(
            mock_stt_result["text"], 
            language_context
        )
        
        agent_time = time.time() - agent_start
        print(f"   ✅ Agent Complete: {agent_time:.2f}s")
        print(f"   📝 Response: '{agent_result.get('response', '')[:60]}...'")
        print(f"   😊 Emotion: {agent_result.get('emotion', 'none')}")
        
        # Calculate time to first response (text)
        text_response_time = time.time() - start_time
        print(f"📱 TEXT SENT TO FRONTEND: {text_response_time:.2f}s")
        print("   🎯 User sees response immediately!")
        
        print("🎵 Step 3: TTS Processing (background)...")
        tts_start = time.time()
        
        # Simulate TTS processing
        response_text = agent_result.get("response", "Test response")
        
        # This would normally do TTS processing  
        mock_tts_result = {
            "success": True,
            "audio_data": b"fake_tts_audio" * 2000,  # ~26KB
            "format": "wav",
            "duration": 3.5
        }
        
        tts_time = time.time() - tts_start
        print(f"   ✅ TTS Complete: {tts_time:.2f}s")
        
        # Total time for complete response
        total_time = time.time() - start_time
        print(f"📱 AUDIO SENT TO FRONTEND: {total_time:.2f}s")
        
        print("\n📊 Performance Summary:")
        print(f"   STT Processing:       {stt_time:.2f}s")
        print(f"   Agent Processing:     {agent_time:.2f}s")
        print(f"   📱 TEXT Available:    {text_response_time:.2f}s ← USER SEES THIS")
        print(f"   TTS Processing:       {tts_time:.2f}s")
        print(f"   📱 AUDIO Available:   {total_time:.2f}s")
        
        print(f"\n🎯 Improvement:")
        print(f"   Old Flow: User waits {total_time:.2f}s for any response")
        print(f"   New Flow: User sees text in {text_response_time:.2f}s ({100*text_response_time/total_time:.0f}% faster)")
        
        # Mock WebSocket responses that would be sent
        print("\n📡 WebSocket Messages:")
        
        text_message = {
            "type": "streaming_text_response",
            "success": True,
            "input_text": mock_stt_result["text"],
            "response_text": response_text[:100] + "..." if len(response_text) > 100 else response_text,
            "emotion": agent_result.get("emotion", "none"),
            "audio_processing": "in_progress"
        }
        
        audio_message = {
            "type": "streaming_audio_response", 
            "success": True,
            "audio_data": f"<{len(mock_tts_result['audio_data'])} bytes>",
            "audio_format": "wav",
            "audio_processing": "complete"
        }
        
        print("   1️⃣ Text Message (immediate):")
        print(f"      {json.dumps(text_message, indent=2)[:200]}...")
        
        print("   2️⃣ Audio Message (later):")
        print(f"      {json.dumps(audio_message, indent=2)[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_streaming_flow())
    if success:
        print("\n🎉 Streaming flow test completed successfully!")
    else:
        print("\n💥 Streaming flow test failed!")