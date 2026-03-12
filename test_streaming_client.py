"""
WebSocket Test Client - Test immediate streaming functionality
===========================================================

Test client to verify immediate content delivery from the backend.

Usage:
    python test_streaming_client.py
"""

import asyncio
import json
import websockets
import time
from typing import Dict, Any

class StreamingTestClient:
    def __init__(self, url: str = "ws://localhost:8000/ws"):
        self.url = url
        self.websocket = None

    async def connect(self):
        """Connect to WebSocket server"""
        try:
            print(f"🔌 Connecting to {self.url}...")
            self.websocket = await websockets.connect(self.url)
            print("✅ Connected successfully!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    async def send_message(self, message: Dict[str, Any]):
        """Send message and log timing"""
        if not self.websocket:
            print("❌ Not connected")
            return

        send_time = time.time()
        print(f"\n📤 Sending: {json.dumps(message, indent=2)}")
        print(f"⏰ Send time: {send_time}")
        
        await self.websocket.send(json.dumps(message))
        print("✅ Message sent")

    async def listen_for_responses(self, timeout: float = 30.0):
        """Listen for responses and track timing"""
        if not self.websocket:
            print("❌ Not connected")
            return

        start_time = time.time()
        response_count = 0
        first_response_time = None

        print(f"\n👂 Listening for responses (timeout: {timeout}s)...")
        print("-" * 60)

        try:
            while True:
                try:
                    # Wait for response with timeout
                    response = await asyncio.wait_for(
                        self.websocket.recv(), 
                        timeout=timeout
                    )
                    
                    receive_time = time.time()
                    response_count += 1
                    
                    if first_response_time is None:
                        first_response_time = receive_time
                        first_response_delay = receive_time - start_time
                        print(f"⚡ First response in {first_response_delay:.3f}s")

                    # Parse and display response
                    try:
                        data = json.loads(response)
                        response_type = data.get("type", "unknown")
                        
                        print(f"\n📥 Response #{response_count} [{response_type}]")
                        print(f"   ⏱️  Delay: {receive_time - start_time:.3f}s")
                        
                        # Show key content based on response type
                        if response_type == "streaming_status":
                            print(f"   📋 Status: {data.get('stage')} - {data.get('message')}")
                            print(f"   💭 Input: {data.get('input_text', 'N/A')}")
                            
                        elif response_type == "streaming_text_response":
                            print(f"   💬 Text Response: {data.get('response_text', 'N/A')[:100]}...")
                            print(f"   🎭 Emotion: {data.get('emotion', 'none')}")
                            print(f"   🔊 Audio Status: {data.get('audio_processing', 'unknown')}")
                            
                        elif response_type == "streaming_audio_chunk":
                            chunk_id = data.get('chunk_id', 0)
                            total_chunks = data.get('total_chunks', 1)
                            text_chunk = data.get('text_chunk', '')
                            print(f"   🎵 Audio Chunk {chunk_id+1}/{total_chunks}: {text_chunk[:50]}...")
                            
                        elif response_type == "test_immediate_response":
                            print(f"   🧪 Test Response: {data.get('message', 'N/A')}")
                            
                        elif response_type == "test_progress":
                            print(f"   ⏳ Progress: {data.get('message', 'N/A')}")
                            
                        elif response_type.endswith("_error"):
                            print(f"   ❌ Error: {data.get('error', 'Unknown error')}")
                            
                        else:
                            print(f"   📄 Data: {json.dumps(data, indent=6)[:200]}...")
                            
                    except json.JSONDecodeError:
                        print(f"   📄 Raw: {response[:200]}...")
                    
                except asyncio.TimeoutError:
                    print(f"\n⏰ Timeout after {timeout}s")
                    break
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"\n🔌 Connection closed")
        except Exception as e:
            print(f"\n❌ Error during listening: {e}")

        print(f"\n📊 Summary:")
        print(f"   • Total responses: {response_count}")
        if first_response_time:
            print(f"   • First response: {first_response_time - start_time:.3f}s")
        print(f"   • Total time: {time.time() - start_time:.3f}s")

    async def test_immediate_functionality(self):
        """Test the immediate response functionality"""
        print("\n🧪 Testing immediate response functionality...")
        
        # Test 1: Simple immediate test
        await self.send_message({
            "type": "test_immediate",
            "message": "Hello immediate test!"
        })
        
        await self.listen_for_responses(timeout=10.0)

    async def test_streaming_audio(self):
        """Test streaming audio functionality with sample data"""
        print("\n🎵 Testing streaming audio functionality...")
        
        # Create a simple audio message (empty base64 for testing)
        import base64
        
        # Use a small dummy audio data
        dummy_audio = b"dummy_audio_data_for_testing"
        audio_base64 = base64.b64encode(dummy_audio).decode('utf-8')
        
        await self.send_message({
            "type": "audio_base64_streaming",
            "audio_data": audio_base64,
            "input_language": "en",
            "output_language": "en"
        })
        
        await self.listen_for_responses(timeout=20.0)

    async def test_text_streaming(self):
        """Test TTS streaming functionality"""
        print("\n📝 Testing TTS streaming functionality...")
        
        await self.send_message({
            "type": "audio_tts_streaming",
            "text": "This is a test message for streaming TTS. It should be split into multiple sentences.",
            "language": "en",
            "emotion": "none"
        })
        
        await self.listen_for_responses(timeout=15.0)

    async def close(self):
        """Close the connection"""
        if self.websocket:
            await self.websocket.close()
            print("🔌 Connection closed")

async def main():
    """Main test function"""
    print("=" * 60)
    print("    🧪 WebSocket Streaming Test Client")
    print("=" * 60)
    
    client = StreamingTestClient()
    
    try:
        # Connect to server
        if not await client.connect():
            return 1
        
        # Run tests
        while True:
            print("\n🔧 Test Options:")
            print("1. Test immediate response")
            print("2. Test streaming audio (dummy)")
            print("3. Test TTS streaming")
            print("4. Exit")
            
            choice = input("\nEnter choice (1-4): ").strip()
            
            if choice == "1":
                await client.test_immediate_functionality()
            elif choice == "2":
                await client.test_streaming_audio()
            elif choice == "3":
                await client.test_text_streaming()
            elif choice == "4":
                break
            else:
                print("Invalid choice!")
                
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"❌ Test error: {e}")
    finally:
        await client.close()
    
    return 0

if __name__ == "__main__":
    asyncio.run(main())