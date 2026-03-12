# Chopper AI Agent - Audio Features with API Key Rotation

An AI assistant backend with integrated Speech-to-Text (STT) and Text-to-Speech (TTS) capabilities using **Groq** and **Gemini** APIs with circular API key rotation for high availability.

## 🎵 Audio Features

### Speech-to-Text (STT)
- **Provider**: Groq (Whisper Large V3)
- **Supported Formats**: WAV, MP3, OGG, FLAC, M4A
- **Languages**: English, Tamil, and auto-detection
- **Max Duration**: 5 minutes (configurable)
- **Max File Size**: 10MB (configurable)
- **API Key Rotation**: 5 keys in circular rotation

### Text-to-Speech (TTS)
- **Provider**: Gemini TTS (gemini-2.5-flash-preview-tts)
- **Output Format**: WAV (24kHz, 16-bit, mono)
- **Languages**: English, Tamil (with English voice fallback)
- **Emotions**: None, Happy, Sad
- **Voices**: Bard, Pulcherrima, Nova, Fenix
- **API Key Rotation**: 5 keys in circular rotation

### AI Chat
- **Provider**: Gemini 2.5 Flash
- **API Key Rotation**: 5 keys in circular rotation
- **Total Keys**: 15 keys (5 per service)

## 🔑 API Key Rotation System

The system uses **15 API keys total** with circular rotation:
- **5 Groq keys** for STT (Speech-to-Text)
- **5 Gemini keys** for TTS (Text-to-Speech)  
- **5 Gemini keys** for AI chat responses

Keys rotate using `N % keyCount` pattern to ensure:
- ✅ High availability and load distribution
- ✅ Rate limit avoidance
- ✅ Automatic failover
- ✅ Thread-safe key management

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
# Edit .env with your 15 API keys (5 each for Groq STT, Gemini TTS, Gemini AI)
```

**Required API Keys in .env:**
```env
# Groq STT Keys (5)
GROQ_STT_API_KEY_1=your_groq_key_1
GROQ_STT_API_KEY_2=your_groq_key_2
# ... up to GROQ_STT_API_KEY_5

# Gemini TTS Keys (5)  
GEMINI_TTS_API_KEY_1=your_gemini_key_1
GEMINI_TTS_API_KEY_2=your_gemini_key_2
# ... up to GEMINI_TTS_API_KEY_5

# Gemini AI Keys (5)
GEMINI_AI_API_KEY_1=your_gemini_key_1
GEMINI_AI_API_KEY_2=your_gemini_key_2
# ... up to GEMINI_AI_API_KEY_5
```

### 3. Start Enhanced Server

```bash
python main.py
```

Server starts on `http://localhost:8000` with API key rotation active.

### 4. Test Audio Features

```bash
python audio_client_example.py
```

## 📡 WebSocket API Examples

### Text Query with Gemini TTS Response
```json
{
    "type": "text",
    "query": "What are the admission requirements?",
    "enable_tts": true,
    "tts_language": "en"
}
```

**Response:**
```json
{
    "type": "text_with_audio_response",
    "response": "The admission requirements are...",
    "emotion": "none",
    "audio_data": "base64_wav_audio",
    "audio_format": "wav",
    "audio_duration": 5.2
}
```

### Complete Audio Conversation (Groq → Gemini → Gemini TTS)
```json
{
    "type": "audio_base64",
    "audio_data": "base64_encoded_audio_input",
    "input_language": "auto", 
    "output_language": "en"
}
```

**Response:**
```json
{
    "type": "audio_conversation_response",
    "success": true,
    "input_text": "What is the fee structure?",
    "input_language": "en",
    "response_text": "The fee structure is...",
    "emotion": "none", 
    "audio_data": "base64_wav_response",
    "audio_format": "wav",
    "stt_confidence": 0.95
}
```

## 🏗️ Architecture

```
backend/
├── audio/                     # Audio processing modules
│   ├── stt.py                # Groq STT (Whisper Large V3)
│   ├── tts.py                # Gemini TTS
│   └── manager.py            # Audio coordinator
├── config/
│   ├── settings.py           # Enhanced configuration
│   └── api_keys.py           # 🆕 API Key rotation manager
├── agent/
│   └── gemini_agent.py       # 🔄 Updated with key rotation
├── server/
│   └── websocket_handler.py  # Enhanced WebSocket handler
└── main.py                   # 🔄 Enhanced with rotation monitoring
```

## ⚙️ API Key Rotation

### How It Works
1. **Circular Rotation**: Keys rotate using `(current_index + 1) % total_keys`
2. **Thread Safe**: Uses locks to prevent race conditions
3. **Service Isolation**: Each service (STT/TTS/AI) has independent rotation
4. **Automatic Fallback**: Single key support for development/testing

### Key Management
```python
# Get rotated keys
groq_key = get_groq_stt_key()      # Uses next Groq STT key
gemini_tts_key = get_gemini_tts_key()  # Uses next Gemini TTS key 
gemini_ai_key = get_gemini_ai_key()    # Uses next Gemini AI key
```

### Monitoring
```bash
# Check key rotation status
curl http://localhost:8000/admin/api-keys/status

# Reset rotation to start position
curl -X POST http://localhost:8000/admin/api-keys/reset
```

## 🎯 Performance Optimizations

### Key Rotation Benefits
- **Rate Limit Distribution**: Spreads requests across multiple keys
- **High Availability**: Continues working even if some keys have issues
- **Load Balancing**: Automatic distribution of API calls
- **Cost Management**: Better quota utilization across keys

### Provider Performance
- **Groq STT**: Ultra-fast Whisper Large V3 processing
- **Gemini TTS**: High-quality voice synthesis with emotion support
- **Gemini AI**: Fast, context-aware chat responses

## 🔍 HTTP Endpoints

### Core Endpoints
- `GET /` - Health check with key rotation status
- `GET /audio/info` - Audio capabilities and key status
- `GET /audio/voices/{language}` - Available voices
- `GET /docs` - Interactive API documentation

### Admin Endpoints  
- `GET /admin/api-keys/status` - Detailed key rotation status
- `POST /admin/api-keys/reset` - Reset key rotation counters

## 🎪 Usage Scenarios

1. **High-Volume Applications**: Key rotation prevents rate limiting
2. **Voice Questions**: Users speak questions, get audio responses
3. **Accessibility**: TTS for visually impaired users
4. **Multi-language**: Tamil/English conversations
5. **Emotion-aware**: Happy/sad response tones based on context

## 📊 Configuration

### Environment Variables (.env)
```env
# Enable/disable key rotation
ENABLE_KEY_ROTATION=true
KEY_ROTATION_LOGGING=true

# Audio processing  
STT_LANGUAGE=auto
DEFAULT_VOICE=Bard
DEFAULT_TTS_LANGUAGE=en
MAX_AUDIO_SIZE=10485760
MAX_AUDIO_DURATION=300
```

### Voice Options (Gemini TTS)
- **Bard**: Default, neutral voice
- **Pulcherrima**: Cheerful, expressive (happy emotion)
- **Nova**: Calm, serious (sad emotion)  
- **Fenix**: Deep, authoritative

## 🔧 Troubleshooting

### Key Rotation Issues
```bash
# Check key status
curl http://localhost:8000/admin/api-keys/status

# Look for key validation errors in logs
tail -f logs/app.log | grep "API_KEY_MANAGER"
```

### Common Solutions
1. **No keys loaded**: Check .env file has correct key names
2. **Single key fallback**: Set `GROQ_STT_API_KEY` (no number) for testing
3. **Rate limits**: Ensure all 5 keys per service are valid and active
4. **Audio quality**: Groq Whisper Large V3 provides best STT accuracy

### Debug Mode
```bash
# Enable detailed logging
export ENABLE_AUDIO_LOGGING=true
export KEY_ROTATION_LOGGING=true
python main.py
```

## 🚦 Integration Examples

### Python Client with Key Rotation
```python
import asyncio
import websockets
import json
import base64

async def test_audio_conversation():
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        # Send audio (will use rotated Groq key)
        with open("question.wav", "rb") as f:
            audio_data = base64.b64encode(f.read()).decode()
        
        message = {
            "type": "audio_base64",
            "audio_data": audio_data
        }
        
        await websocket.send(json.dumps(message))
        response = json.loads(await websocket.recv())
        
        # Response generated with rotated Gemini keys
        print(f"STT (Groq): {response['input_text']}")
        print(f"AI (Gemini): {response['response_text']}")
        print(f"TTS (Gemini): {len(response['audio_data'])} bytes")

asyncio.run(test_audio_conversation())
```

### JavaScript Client
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

// All requests automatically use rotated API keys
function sendAudioMessage(audioBlob) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const audioData = btoa(
            new Uint8Array(e.target.result)
                .reduce((data, byte) => data + String.fromCharCode(byte), '')
        );
        
        ws.send(JSON.stringify({
            type: 'audio_base64',
            audio_data: audioData,
            input_language: 'auto',
            output_language: 'en'
        }));
    };
    reader.readAsArrayBuffer(audioBlob);
}
```

## 📈 Monitoring & Analytics

### Key Usage Tracking
The system automatically logs:
- Which key is being used for each request
- Key rotation patterns
- Service-specific key distribution
- API call success/failure rates per key

### Performance Metrics
- **STT Latency**: Groq Whisper processing time
- **TTS Generation**: Gemini synthesis duration  
- **Key Rotation**: Even distribution verification
- **Error Rates**: Per-key failure tracking

## 🔒 Security & Best Practices

### API Key Security
- ✅ Keys stored in environment variables only
- ✅ No keys logged or exposed in responses
- ✅ Rotation prevents key overuse
- ✅ Independent service key pools

### Production Recommendations
1. **Use all 15 keys** for optimal load distribution
2. **Monitor key rotation logs** for even usage
3. **Set up key rotation alerts** for failures
4. **Regular key rotation** (monthly recommended)
5. **Backup key configuration** for disaster recovery

## 📄 License

This enhanced audio system with API key rotation is part of the Chopper AI Agent project.