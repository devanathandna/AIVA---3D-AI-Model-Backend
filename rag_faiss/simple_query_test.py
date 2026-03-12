"""
Simple Query Test - Quick vector embedding testing
================================================

Minimal script for fast query testing without interactive mode.

Usage:
    python simple_query_test.py "your query here"
    python simple_query_test.py  # for predefined test queries
"""

import os
import sys
import time

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from rag_faiss.retriever import retrieve
except ImportError:
    from retriever import retrieve

def test_query(query: str, show_context: bool = True):
    """Test a single query and show results."""
    print(f"\n🔍 Query: {query}")
    print("-" * 50)
    
    start_time = time.perf_counter()
    result = retrieve(query)
    elapsed = (time.perf_counter() - start_time) * 1000
    
    print(f"⚡ Response time: {elapsed:.1f}ms")
    print(f"📚 Sources: {', '.join(result['sources'])}")
    print(f"📝 Context length: {len(result['context'])} characters")
    
    if show_context:
        print(f"\n📖 Retrieved Context:")
        print(result['context'][:800] + ("..." if len(result['context']) > 800 else ""))
    
    return result

def main():
    if len(sys.argv) > 1:
        # Query provided as command line argument
        query = " ".join(sys.argv[1:])
        test_query(query)
    else:
        # Run predefined test queries
        test_queries = [
            "CSE department cutoff marks",
            "student achievements and awards", 
            "hostel facilities",
            "fee structure",
            "placement companies"
        ]
        
        print("🧪 Running quick test queries...")
        for query in test_queries:
            test_query(query, show_context=False)

if __name__ == "__main__":
    main()