#!/usr/bin/env python3
"""
Test Token Streaming Implementation
Tests the new Groq token-by-token streaming functionality
"""

import asyncio
import sys
from agent.groq_llama_agent import get_agent_response_streaming

async def test_token_streaming():
    """Test the token streaming functionality"""
    print("🚀 Testing Token Streaming")
    print("=" * 60)
    
    test_query = "What are the hostel facilities available?"
    
    print(f"Query: {test_query}\n")
    print("Streaming response:")
    print("-" * 60)
    
    token_count = 0
    full_response = ""
    
    try:
        async for chunk in get_agent_response_streaming(test_query):
            chunk_type = chunk.get("type")
            
            if chunk_type == "streaming_token":
                token = chunk.get("token", "")
                token_count = chunk.get("token_count", 0)
                full_response += token
                
                # Print token without newline (simulate real-time streaming)
                print(token, end="", flush=True)
                
            elif chunk_type == "streaming_complete":
                print("\n" + "-" * 60)
                print(f"\n✅ Streaming Complete!")
                print(f"   Total tokens: {token_count}")
                print(f"   Response length: {len(full_response)} chars")
                print(f"   Emotion: {chunk.get('emotion', 'none')}")
                print(f"\nFinal parsed response:")
                print(f"   {chunk.get('response', '')[:100]}...")
                
            elif chunk_type == "streaming_error":
                print("\n❌ Streaming Error:", chunk.get("error"))
                
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_token_streaming())
