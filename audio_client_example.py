"""
Example client for testing Deepgram STT and Gemini TTS functionality
"""
import asyncio
import websockets
import json
import base64
import pyaudio
import wave
import tempfile
import os
from typing import Optional

class AudioClient:
    def __init__(self, server_url: str = "ws://localhost:8000/ws"):
        self.server_url = server_url
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        
    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.server_url) 
            print("✅ Connected to Chopper AI Agent (Deepgram + Gemini)")
            
            # Get server info
            info = await self.get_audio_info()
            if info.get("type") == "audio_info_response":
                capabilities = info["info"]
                print(f"📋 STT Provider: {capabilities['stt']['provider']}")
                print(f"📋 TTS Provider: {capabilities['tts']['provider']}")
                print(f"🔑 API Key Rotation: {capabilities['conversation_flow'].get('api_key_rotation', False)}")
            
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the server"""
        if self.websocket:
            await self.websocket.close()
            print("👋 Disconnected from server")
    
    async def send_text_query(self, text: str, enable_tts: bool = False, tts_language: str = "en"):
        """Send text query to server with Gemini AI and optional Gemini TTS"""
        message = {
            "type": "text",
            "query": text,
            "enable_tts": enable_tts,
            "tts_language": tts_language
        }
        
        await self.websocket.send(json.dumps(message))
        response = await self.websocket.recv()
        return json.loads(response)
    
    async def send_audio_file(self, audio_file_path: str, input_language: str = "auto", output_language: str = "en"):
        """Send audio file to server for Deepgram STT processing"""
        try:
            # Read audio file
            with open(audio_file_path, 'rb') as f:
                audio_data = f.read()
            
            # Encode to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            message = {
                "type": "audio_base64",
                "audio_data": audio_base64,
                "input_language": input_language,
                "output_language": output_language
            }
            
            await self.websocket.send(json.dumps(message))
            response = await self.websocket.recv()
            return json.loads(response)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def record_and_send_audio(self, duration: int = 5, input_language: str = "auto", output_language: str = "en"):
        """Record audio from microphone and send to server"""
        try:
            print(f"🎤 Recording for {duration} seconds (Deepgram STT → Gemini AI → Gemini TTS)...")
            
            # Audio configuration
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000
            
            # Initialize PyAudio
            p = pyaudio.PyAudio()
            
            # Create stream
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            frames = []
            
            # Record audio
            for i in range(0, int(RATE / CHUNK * duration)):
                data = stream.read(CHUNK)
                frames.append(data)
            
            # Clean up
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            print("📝 Recording finished, processing with rotated API keys...")
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
                
                wf = wave.open(temp_path, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
                wf.close()
            
            # Send audio file
            result = await self.send_audio_file(temp_path, input_language, output_language)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_audio_info(self):
        """Get supported audio formats and capabilities"""
        message = {"type": "get_audio_info"}
        await self.websocket.send(json.dumps(message))
        response = await self.websocket.recv()
        return json.loads(response)
    
    async def get_voices(self, language: str = "en"):
        """Get available Gemini TTS voices"""
        message = {"type": "get_voices", "language": language}
        await self.websocket.send(json.dumps(message))
        response = await self.websocket.recv()
        return json.loads(response)
    
    def save_audio_response(self, response: dict, output_path: str = "response.wav"):
        """Save WAV audio response to file"""
        if response.get("success") and response.get("audio_data"):
            try:
                audio_data = base64.b64decode(response["audio_data"])
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                print(f"💾 Audio saved to {output_path} (Gemini TTS WAV format)")
                return True
            except Exception as e:
                print(f"❌ Failed to save audio: {e}")
                return False
        return False

async def demo_text_with_gemini_tts():
    """Demo: Text query with Gemini TTS response"""
    client = AudioClient()
    
    if not await client.connect():
        return
    
    try:
        print("\n=== Text Query with Gemini TTS Demo ===")
        
        # Send text query with TTS enabled
        response = await client.send_text_query(
            "What is the admission process for your college?",
            enable_tts=True,
            tts_language="en"
        )
        
        print(f"📄 Text Response: {response.get('response', 'No response')}")
        print(f"😊 Emotion: {response.get('emotion', 'none')}")
        
        if response.get('type') == 'text_with_audio_response':
            print("🔊 Gemini TTS audio response available")
            client.save_audio_response(response, "gemini_tts_response.wav")
            print("▶️  Play gemini_tts_response.wav to hear the response")
        
    finally:
        await client.disconnect()

async def demo_full_audio_pipeline():
    """Demo: Full audio pipeline (Deepgram STT → Gemini AI → Gemini TTS)"""
    client = AudioClient()
    
    if not await client.connect():
        return
    
    try:
        print("\n=== Full Audio Pipeline Demo ===")
        print("Pipeline: Deepgram Nova-2 → Gemini 2.5 Flash → Gemini TTS")
        print("This demo requires a microphone")
        
        # Get audio capabilities
        info = await client.get_audio_info()
        if info.get("type") == "audio_info_response":
            print(f"📋 Audio Pipeline Info:")
            capabilities = info["info"]
            print(f"   - STT: {capabilities['stt']['provider']}")
            print(f"   - TTS: {capabilities['tts']['provider']}")
            print(f"   - API Key Rotation: {capabilities['conversation_flow'].get('api_key_rotation', False)}")
        
        # Get available voices
        voices_response = await client.get_voices("en")
        if voices_response.get("type") == "voices_response":
            voices = voices_response["voices"]["voices"]
            print(f"🎵 Available Gemini TTS voices: {[v['name'] for v in voices]}")
        
        # Record and process audio
        input("Press Enter to start recording...")
        response = await client.record_and_send_audio(
            duration=5,
            input_language="auto",
            output_language="en"
        )
        
        if response.get("success"):
            print(f"🎤 STT (Deepgram): {response.get('input_text', 'N/A')}")
            print(f"📄 AI (Gemini): {response.get('response_text', 'N/A')}")
            print(f"😊 Emotion: {response.get('emotion', 'none')}")
            print(f"🎯 STT Confidence: {response.get('stt_confidence', 0):.2f}")
            
            if response.get("audio_data"):
                client.save_audio_response(response, "full_pipeline_response.wav")
                print("🔊 Complete pipeline response saved as full_pipeline_response.wav")
                print("▶️  Play the file to hear Gemini TTS output")
        else:
            print(f"❌ Pipeline Error: {response.get('error', 'Unknown error')}")
        
    finally:
        await client.disconnect()

async def demo_api_key_rotation():
    """Demo: Monitor API key rotation"""
    import aiohttp
    
    print("\n=== API Key Rotation Demo ===")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Check API key status
            async with session.get("http://localhost:8000/admin/api-keys/status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print("🔑 API Key Rotation Status:")
                    for service, status in data["key_status"].items():
                        print(f"   - {service}: {status['current_index']}/{status['total_keys']} keys")
                else:
                    print("❌ Could not connect to server")
                    
    except Exception as e:
        print(f"❌ Error checking key rotation: {e}")
        print("💡 Make sure the server is running: python main.py")

async def demo_voice_options():
    """Demo: Show Gemini TTS voice options and emotions"""
    client = AudioClient()
    
    if not await client.connect():
        return
    
    try:
        print("\n=== Gemini TTS Voice Options Demo ===")
        
        # Test different voices and emotions
        test_cases = [
            ("Hello, I'm using the default Bard voice.", "en", "none"),
            ("I'm feeling happy today!", "en", "happy"),  # Uses Pulcherrima
            ("This is a sad message.", "en", "sad")       # Uses Nova
        ]
        
        for i, (text, language, emotion) in enumerate(test_cases, 1):
            print(f"\n🎵 Test {i}: {emotion} emotion")
            response = await client.send_text_query(
                text,
                enable_tts=True,
                tts_language=language
            )
            
            if response.get('type') == 'text_with_audio_response':
                filename = f"voice_demo_{emotion}.wav"
                client.save_audio_response(response, filename)
                print(f"💾 Saved as {filename}")
            
    finally:
        await client.disconnect()

async def main():
    """Main demo function"""
    print("🎵 Chopper AI Agent - Audio Client Demo")
    print("Features: Deepgram STT + Gemini AI + Gemini TTS")
    print("\nChoose a demo:")
    print("1. Text query with Gemini TTS")
    print("2. Full audio pipeline (STT→AI→TTS)")
    print("3. API key rotation monitoring")
    print("4. Gemini TTS voice options")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        await demo_text_with_gemini_tts()
    elif choice == "2":
        await demo_full_audio_pipeline() 
    elif choice == "3":
        await demo_api_key_rotation()
    elif choice == "4":
        await demo_voice_options()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    # Install required packages for client:
    # pip install websockets pyaudio wave aiohttp
    
    print("🚀 Starting Chopper AI Agent Audio Client")
    print("Requirements: websockets, pyaudio, wave, aiohttp")
    
    asyncio.run(main())