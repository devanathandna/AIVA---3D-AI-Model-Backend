"""
Test Groq Llama Agent with RAG Integration
========================================

Test if the agent now properly uses RAG context for specific queries.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agent.groq_llama_agent import get_agent_response

async def test_cutoff_query():
    """Test the specific cutoff query that was failing"""
    query = "What is the cut-off for CSE department BC category?"
    
    print(f"🔍 Testing query: {query}")
    print("=" * 60)
    
    try:
        result = await get_agent_response(query)
        
        print(f"📥 Agent Response:")
        print(f"   Response: {result.get('response', 'No response')}")
        print(f"   Emotion: {result.get('emotion', 'none')}")
        
        # Check if it contains specific cutoff information
        response_text = result.get('response', '').lower()
        if '192' in response_text or 'bc' in response_text and 'cse' in response_text:
            print("✅ SUCCESS: Agent used specific RAG context!")
        else:
            print("❌ FAILURE: Agent gave generic response")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_cutoff_query())