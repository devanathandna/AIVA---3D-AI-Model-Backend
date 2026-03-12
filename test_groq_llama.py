#!/usr/bin/env python3
"""
Test script for new Groq Llama agent and STT post-processing
"""

import asyncio
import os

async def test_groq_llama_agent():
    """Test the new Groq Llama agent"""
    print("🤖 Testing Groq Llama Agent")
    print("=" * 40)
    
    try:
        # Set test environment variables if not set
        if not os.getenv("GROQ_API_KEY"):
            print("⚠️  GROQ_API_KEY not set in environment")
            return False
        
        from agent.groq_llama_agent import get_agent_response
        
        test_queries = [
            "How is the hostel food?", 
            "What are the mess timings?",
            "Tell me about CSE department"
        ]
        
        for query in test_queries:
            print(f"\n📝 Query: {query}")
            result = await get_agent_response(query)
            
            print(f"✅ Response: {result.get('response', 'No response')[:100]}...")
            print(f"😊 Emotion: {result.get('emotion', 'none')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Groq Llama agent test failed: {e}")
        return False


async def test_stt_post_processor():
    """Test STT post-processing corrections"""
    print("\n🔧 Testing STT Post-Processor")
    print("=" * 40)
    
    try:
        # Set test environment variable if not set
        if not os.getenv("GROQ_STT_Processor"):
            print("⚠️  GROQ_STT_Processor key not set, testing rule-based corrections only")
        
        from audio.stt_post_processor import get_stt_post_processor
        
        post_processor = get_stt_post_processor()
        
        # Test correction examples
        test_cases = [
            "I'm in PC category and study CIC",
            "St EShwar college mess timing is 7 AM to 9 PM",
            "Internal exam in CCE department next week",
            "The hostel dormitory has good facilities"
        ]
        
        for original_text in test_cases:
            print(f"\n📝 Original: {original_text}")
            
            # Test quick corrections (rule-based)
            quick_corrected = post_processor.apply_quick_corrections(original_text)
            print(f"⚡ Quick: {quick_corrected}")
            
            # Test smart corrections (Llama) if API key available
            if os.getenv("GROQ_STT_Processor"):
                result = await post_processor.process_stt_corrections(original_text, "college")
                if result["success"]:
                    print(f"🤖 Smart: {result['corrected_text']}")
                    print(f"✅ Applied: {result['corrections_applied']}")
                else:
                    print(f"❌ Smart correction failed: {result.get('error')}")
            
        return True
        
    except Exception as e:
        print(f"❌ STT post-processor test failed: {e}")
        return False


async def test_sentence_streaming():
    """Test sentence-based TTS streaming"""
    print("\n🎵 Testing Sentence TTS Streaming")
    print("=" * 40)
    
    try:
        from audio.tts import get_tts_processor
        
        tts_processor = get_tts_processor()
        
        test_text = "The hostel food is very good. It includes rice, dal, and vegetables. The mess timing is from 7:00 AM to 9:00 PM."
        
        print(f"📝 Test text: {test_text}")
        
        # Test sentence splitting
        sentences = tts_processor.split_into_sentences(test_text)
        print(f"✂️  Split into {len(sentences)} sentences:")
        for i, sentence in enumerate(sentences, 1):
            print(f"   {i}. {sentence}")
        
        # Test streaming (mock - no actual TTS)
        print(f"🎵 TTS streaming simulation:")
        for i, sentence in enumerate(sentences, 1):
            print(f"   📡 Chunk {i}/{len(sentences)}: '{sentence}' → [Audio data would be sent]")
        
        return True
        
    except Exception as e:
        print(f"❌ TTS streaming test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Testing New Groq Llama Implementation")
    print("=" * 60)
    
    success_count = 0
    total_tests = 3
    
    # Test 1: Groq Llama Agent
    if await test_groq_llama_agent():
        success_count += 1
    
    # Test 2: STT Post-Processor 
    if await test_stt_post_processor():
        success_count += 1
    
    # Test 3: Sentence TTS Streaming
    if await test_sentence_streaming():
        success_count += 1
    
    print(f"\n📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! Ready to use Groq Llama implementation.")
    else:
        print("⚠️  Some tests failed. Check API keys and dependencies.")
        
        # Environment check
        print("\n🔑 Environment Check:")
        print(f"   GROQ_API_KEY: {'✅ Set' if os.getenv('GROQ_API_KEY') else '❌ Missing'}")
        print(f"   GROQ_STT_Processor: {'✅ Set' if os.getenv('GROQ_STT_Processor') else '❌ Missing'}")


if __name__ == "__main__":
    asyncio.run(main())