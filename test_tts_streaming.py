#!/usr/bin/env python3
"""
Test script for sentence-based TTS streaming
"""

import asyncio
import json
from typing import List

def test_sentence_splitting():
    """Test the sentence splitting function"""
    
    # Import the function
    import sys
    sys.path.append('.')
    from server.websocket_handler import split_text_into_sentences
    
    test_cases = [
        "Hello! How are you today? I'm doing great.",
        "The hostel food is very good. It includes rice, dal, and vegetables. The mess timing is from 7 AM to 9 PM.",
        "Mr. Smith visited Dr. Johnson at 3 P.M. They discussed the project etc.",
        "Short sentence. Another one. This is a longer sentence with more content to test chunking.",
        "Single sentence without punctuation",
        "Multiple!! Exclamation marks!! And question marks?? How does it handle this?",
        "Tamil content mixed: Hostel-la saapadu nalla irukku. The food is good. Timing correct-aa irukku.",
    ]
    
    print("🧪 Testing Sentence Splitting Function\n")
    
    for i, text in enumerate(test_cases, 1):
        print(f"Test {i}: Original Text")
        print(f"   Input: '{text}'")
        
        sentences = split_text_into_sentences(text)
        
        print(f"   Output: {len(sentences)} sentences")
        for j, sentence in enumerate(sentences, 1):
            print(f"     {j}. '{sentence}'")
        print()

async def test_tts_streaming_simulation():
    """Simulate TTS streaming workflow"""
    
    print("🎵 Simulating TTS Streaming Workflow\n")
    
    # Sample response text
    response_text = "The hostel facilities are excellent. We have clean rooms, good food, and Wi-Fi. The mess serves breakfast from 7 to 9 AM. Lunch is available from 12 to 2 PM. Dinner is served from 7 to 9 PM."
    
    # Import the function
    import sys
    sys.path.append('.')
    from server.websocket_handler import split_text_into_sentences
    
    sentences = split_text_into_sentences(response_text)
    
    print(f"📝 Original Response: '{response_text}'")
    print(f"🔄 Split into {len(sentences)} sentences for streaming:")
    
    # Simulate streaming each sentence
    total_estimated_time = 0
    
    for i, sentence in enumerate(sentences):
        # Estimate TTS time (roughly 1 second per 10-15 words)
        word_count = len(sentence.split())
        estimated_time = max(0.5, word_count / 12)  # Minimum 0.5s, ~12 words/second
        total_estimated_time += estimated_time
        
        print(f"\n   Chunk {i+1}/{len(sentences)}:")
        print(f"      Text: '{sentence}'")
        print(f"      Words: {word_count}")
        print(f"      Est. TTS Time: {estimated_time:.1f}s")
        print(f"      Stream Available: {sum([max(0.5, len(s.split()) / 12) for s in sentences[:i+1]]):.1f}s")
        
        # Simulate WebSocket message
        websocket_message = {
            "type": "streaming_tts_chunk",
            "chunk_id": i,
            "total_chunks": len(sentences),
            "text_chunk": sentence,
            "audio_data": f"<{len(sentence)*100} bytes base64 audio>",
            "audio_format": "wav",
            "is_final": (i == len(sentences) - 1),
            "chunk_duration": estimated_time
        }
        
        print(f"      WebSocket: {json.dumps({k: v if k != 'audio_data' else '<audio_data>' for k, v in websocket_message.items()}, indent=8)}")
    
    print(f"\n📊 Performance Comparison:")
    print(f"   Traditional TTS: User waits {total_estimated_time:.1f}s for complete audio")
    
    first_chunk_time = max(0.5, len(sentences[0].split()) / 12)
    print(f"   Streaming TTS: User hears audio in {first_chunk_time:.1f}s ({100*(total_estimated_time-first_chunk_time)/total_estimated_time:.0f}% faster)")
    
    print(f"\n🎯 User Experience:")
    print(f"   - Text appears immediately (<1s)")
    print(f"   - Audio starts playing in {first_chunk_time:.1f}s") 
    print(f"   - Continuous audio playback (no gaps)")
    print(f"   - Complete experience in {total_estimated_time:.1f}s")

def test_edge_cases():
    """Test edge cases for sentence splitting"""
    
    print("🔍 Testing Edge Cases\n")
    
    import sys
    sys.path.append('.')
    from server.websocket_handler import split_text_into_sentences
    
    edge_cases = [
        "",  # Empty string
        "No punctuation at all",  # No sentence-ending punctuation
        "Multiple spaces.     Between sentences.",  # Extra spaces
        "Dr. Mr. Mrs. etc. abbreviations.",  # Multiple abbreviations
        "What? Really? Are you sure?",  # Multiple questions
        "Wow! Amazing! Incredible!",  # Multiple exclamations
        "Short. Very short. OK.",  # Very short sentences that should be combined
        "A.",  # Single char sentence
        "This has... ellipsis and -- dashes.",  # Other punctuation
    ]
    
    for case in edge_cases:
        print(f"Input: '{case}'")
        result = split_text_into_sentences(case)
        print(f"Output: {result}")
        print(f"Count: {len(result)} sentences\n")

if __name__ == "__main__":
    print("🚀 Testing Sentence-Based TTS Streaming")
    print("=" * 50)
    
    # Test sentence splitting logic
    test_sentence_splitting()
    print("=" * 50)
    
    # Test streaming simulation  
    asyncio.run(test_tts_streaming_simulation())
    print("=" * 50)
    
    # Test edge cases
    test_edge_cases()
    print("=" * 50)
    
    print("✅ All tests completed!")