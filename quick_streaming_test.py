"""
Quick Streaming Test - Test immediate response functionality
=========================================================

Simple test to verify immediate streaming responses.

Usage:
    python quick_streaming_test.py
"""

import asyncio
import websockets
import json
import time

async def test_immediate_response():
    """Test immediate response functionality"""
    try:
        # Connect to WebSocket
        print("🔌 Connecting to ws://localhost:8000/ws...")
        websocket = await websockets.connect("ws://localhost:8000/ws")
        print("✅ Connected!")
        
        # Send test message
        test_message = {
            "type": "test_immediate",
            "message": "Testing immediate response"
        }
        
        start_time = time.time()
        print(f"📤 Sending test at {start_time}")
        await websocket.send(json.dumps(test_message))
        
        # Listen for immediate responses
        response_count = 0
        while response_count < 5:  # Expect: immediate + 3 progress + final
            response = await websocket.recv()
            receive_time = time.time()
            delay = (receive_time - start_time) * 1000  # ms
            
            data = json.loads(response)
            response_type = data.get("type")
            message = data.get("message", "")
            
            print(f"📥 [{delay:6.1f}ms] {response_type}: {message}")
            
            response_count += 1
            
            if response_type == "test_final_response":
                break
        
        await websocket.close()
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🧪 Quick Streaming Test")
    print("=" * 40)
    asyncio.run(test_immediate_response())