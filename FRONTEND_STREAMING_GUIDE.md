# Frontend Implementation Guide for Streaming Features

This guide explains how to implement the streaming features in your frontend application.

---

## 🎯 Overview

Your backend now supports **two streaming modes**:

1. **Standard Streaming** (`audio_base64_streaming`) - Text sent immediately, then audio chunks
2. **Token Streaming** (`audio_base64_streaming_tokens`) - Token-by-token text + audio chunks

---

## 📡 WebSocket Message Types

### **Messages SENT to Backend**

#### 1. Standard Streaming Request
```javascript
{
  "type": "audio_base64_streaming",
  "audio_data": "base64EncodedAudioData...",
  "input_language": "auto",  // "auto" | "en" | "ta" | "hi"
  "output_language": "en",   // "en" | "ta" | "hi"
  "response_style": "english" // "english" | "tanglish" | "hindi-english"
}
```

#### 2. Token Streaming Request (NEW!)
```javascript
{
  "type": "audio_base64_streaming_tokens",
  "audio_data": "base64EncodedAudioData...",
  "input_language": "auto",  // "auto" | "en" | "ta" | "hi"
  "output_language": "en",   // "en" | "ta" | "hi"
  "response_style": "english" // "english" | "tanglish" | "hindi-english"
}
```

---

### **Messages RECEIVED from Backend**

#### Standard Streaming Flow:

1. **`streaming_status`** - Processing started
```javascript
{
  "type": "streaming_status",
  "stage": "processing",
  "input_text": "what you said",
  "message": "Processing your query..."
}
```

2. **`streaming_text_response`** - Complete text immediately
```javascript
{
  "type": "streaming_text_response",
  "success": true,
  "input_text": "what you said",
  "input_language": "en",
  "response_text": "Here is the complete answer...",
  "emotion": "happy",
  "stt_confidence": 0.95,
  "is_tamil": false,
  "audio_processing": "in_progress"
}
```

3. **`streaming_audio_chunk`** - Audio chunks as generated
```javascript
{
  "type": "streaming_audio_chunk",
  "chunk_id": 0,
  "total_chunks": 3,
  "text_chunk": "First sentence.",
  "audio_data": "base64AudioData...",
  "audio_format": "wav",
  "audio_duration": 1.5,
  "output_language": "en",
  "is_final": false,
  "audio_processing": "streaming"
}
```

---

#### Token Streaming Flow (NEW!):

1. **`streaming_stt_complete`** - STT finished
```javascript
{
  "type": "streaming_stt_complete",
  "input_text": "what you said",
  "input_language": "en",
  "is_tamil": false,
  "is_hindi": false,
  "stt_confidence": 0.95
}
```

2. **`streaming_token`** - Each token as generated ⚡
```javascript
{
  "type": "streaming_token",
  "token": "Hello",  // Single word/token
  "token_count": 1
}
```

3. **`streaming_text_complete`** - Text generation finished
```javascript
{
  "type": "streaming_text_complete",
  "response_text": "Complete response text",
  "emotion": "happy",
  "response_style": "english",
  "token_count": 45
}
```

4. **`streaming_audio_chunk`** - Audio chunks (same as above)

5. **`streaming_complete`** - Everything finished
```javascript
{
  "type": "streaming_complete",
  "total_audio_chunks": 3,
  "message": "Streaming complete"
}
```

---

## 💻 Frontend Implementation Examples

### **React Example with Token Streaming**

```javascript
import React, { useState, useRef, useEffect } from 'react';

function StreamingChat() {
  const [inputText, setInputText] = useState('');
  const [responseText, setResponseText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [audioChunks, setAudioChunks] = useState([]);
  const wsRef = useRef(null);
  const audioQueueRef = useRef([]);
  const isPlayingRef = useRef(false);
  const [selectedLanguage, setSelectedLanguage] = useState('en');

  const responseStyleByLanguage = {
    en: 'english',
    ta: 'tanglish',
    hi: 'hindi-english'
  };

  useEffect(() => {
    // Initialize WebSocket
    wsRef.current = new WebSocket('ws://localhost:8000/ws');
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleMessage(data);
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleMessage = (data) => {
    switch (data.type) {
      case 'streaming_stt_complete':
        setInputText(data.input_text);
        console.log('You said:', data.input_text);
        break;

      case 'streaming_token':
        // Append each token as it arrives (like ChatGPT)
        setResponseText(prev => prev + data.token);
        break;

      case 'streaming_text_complete':
        // Text generation complete
        setResponseText(data.response_text);
        console.log('Text complete:', data.token_count, 'tokens');
        break;

      case 'streaming_audio_chunk':
        // Queue audio chunk for playback
        queueAudioChunk(data);
        break;

      case 'streaming_complete':
        setIsProcessing(false);
        console.log('All streaming complete!');
        break;

      case 'streaming_error':
        console.error('Error:', data.error);
        setIsProcessing(false);
        break;

      default:
        console.log('Unknown message:', data.type);
    }
  };

  const queueAudioChunk = (chunk) => {
    const audioBlob = base64ToBlob(chunk.audio_data, 'audio/wav');
    const audioUrl = URL.createObjectURL(audioBlob);
    
    audioQueueRef.current.push({
      url: audioUrl,
      chunk_id: chunk.chunk_id,
      is_final: chunk.is_final
    });

    // Start playing if not already playing
    if (!isPlayingRef.current) {
      playNextAudioChunk();
    }
  };

  const playNextAudioChunk = () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      return;
    }

    isPlayingRef.current = true;
    const chunk = audioQueueRef.current.shift();
    
    const audio = new Audio(chunk.url);
    audio.onended = () => {
      URL.revokeObjectURL(chunk.url);
      playNextAudioChunk();
    };
    audio.onerror = () => {
      console.error('Audio playback error');
      playNextAudioChunk();
    };
    audio.play();
  };

  const sendAudio = async (audioBlob) => {
    setIsProcessing(true);
    setResponseText('');
    
    // Convert audio to base64
    const reader = new FileReader();
    reader.onload = () => {
      const base64Audio = reader.result.split(',')[1];
      
      // Send with token streaming
      wsRef.current.send(JSON.stringify({
        type: 'audio_base64_streaming_tokens',
        audio_data: base64Audio,
        input_language: selectedLanguage, // from button: en | ta | hi
        output_language: selectedLanguage,
        response_style: responseStyleByLanguage[selectedLanguage]
      }));
    };
    reader.readAsDataURL(audioBlob);
  };
  const base64ToBlob = (base64, mimeType) => {
    const byteCharacters = atob(base64);
    const byteArray = new Uint8Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteArray[i] = byteCharacters.charCodeAt(i);
    }
    return new Blob([byteArray], { type: mimeType });
  };

  return (
    <div className="streaming-chat">
      <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
        <button onClick={() => setSelectedLanguage('en')}>English</button>
        <button onClick={() => setSelectedLanguage('ta')}>Tamil</button>
        <button onClick={() => setSelectedLanguage('hi')}>Hindi</button>
      </div>

      <div className="input-display">
        {inputText && <p><strong>You:</strong> {inputText}</p>}
      </div>
      
      <div className="response-display">
        {responseText && (
          <p>
            <strong>AI:</strong> {responseText}
            {isProcessing && <span className="cursor-blink">▊</span>}
          </p>
        )}
      </div>

      <button onClick={() => {/* Start recording */}}>
        {isProcessing ? 'Processing...' : 'Start Recording'}
      </button>
    </div>
  );
}
```

### Language Button Behavior

- `English` button sends: `input_language: "en"`, `response_style: "english"`
- `Tamil` button sends: `input_language: "ta"`, `response_style: "tanglish"`
- `Hindi` button sends: `input_language: "hi"`, `response_style: "hindi-english"`
- If you want backend auto-detection, send `input_language: "auto"` and still set `response_style` explicitly.

---

### **Vanilla JavaScript Example**

```javascript
class StreamingClient {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.responseElement = document.getElementById('response');
    this.audioQueue = [];
    this.isPlaying = false;
    
    this.ws.onmessage = this.handleMessage.bind(this);
  }

  handleMessage(event) {
    const data = JSON.parse(event.data);
    
    switch (data.type) {
      case 'streaming_stt_complete':
        this.displayInput(data.input_text);
        break;

      case 'streaming_token':
        // Append token immediately (real-time effect)
        this.responseElement.textContent += data.token;
        this.scrollToBottom();
        break;

      case 'streaming_text_complete':
        // Ensure complete text is displayed
        this.responseElement.textContent = data.response_text;
        break;

      case 'streaming_audio_chunk':
        this.queueAudioChunk(data);
        break;

      case 'streaming_complete':
        console.log('✅ Streaming complete');
        break;
    }
  }

  displayInput(text) {
    const inputDiv = document.getElementById('user-input');
    inputDiv.textContent = `You: ${text}`;
  }

  queueAudioChunk(chunk) {
    const audioBlob = this.base64ToBlob(chunk.audio_data, 'audio/wav');
    const audioUrl = URL.createObjectURL(audioBlob);
    
    this.audioQueue.push(audioUrl);
    
    if (!this.isPlaying) {
      this.playNextAudio();
    }
  }

  playNextAudio() {
    if (this.audioQueue.length === 0) {
      this.isPlaying = false;
      return;
    }

    this.isPlaying = true;
    const audioUrl = this.audioQueue.shift();
    
    const audio = new Audio(audioUrl);
    audio.onended = () => {
      URL.revokeObjectURL(audioUrl);
      this.playNextAudio();
    };
    audio.play();
  }

  sendAudio(audioBlob) {
    const reader = new FileReader();
    reader.onload = () => {
      const base64Audio = reader.result.split(',')[1];
      
      this.ws.send(JSON.stringify({
        type: 'audio_base64_streaming_tokens',
        audio_data: base64Audio,
        input_language: 'hi',
        output_language: 'hi',
        response_style: 'hindi-english'
      }));
    };
    reader.readAsDataURL(audioBlob);
  }

  base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64);
    const byteArray = new Uint8Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteArray[i] = byteCharacters.charCodeAt(i);
    }
    return new Blob([byteArray], { type: mimeType });
  }

  scrollToBottom() {
    this.responseElement.scrollTop = this.responseElement.scrollHeight;
  }
}

// Usage
const client = new StreamingClient('ws://localhost:8000/ws');
```

---

### **HTML + CSS for Visual Feedback**

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    .response-container {
      font-family: 'Arial', sans-serif;
      padding: 20px;
      max-width: 600px;
    }

    .input-text {
      color: #2196F3;
      margin-bottom: 15px;
    }

    .response-text {
      color: #333;
      line-height: 1.6;
      position: relative;
    }

    /* Blinking cursor for streaming effect */
    .cursor-blink {
      display: inline-block;
      width: 2px;
      height: 1em;
      background: #333;
      animation: blink 1s step-end infinite;
      margin-left: 2px;
    }

    @keyframes blink {
      50% { opacity: 0; }
    }

    /* Audio loading indicator */
    .audio-processing {
      color: #FF9800;
      font-size: 0.9em;
      margin-top: 10px;
    }

    .audio-playing {
      color: #4CAF50;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .audio-wave {
      display: inline-block;
      width: 4px;
      height: 16px;
      background: #4CAF50;
      margin: 0 2px;
      animation: wave 0.6s ease-in-out infinite;
    }

    .audio-wave:nth-child(2) { animation-delay: 0.1s; }
    .audio-wave:nth-child(3) { animation-delay: 0.2s; }

    @keyframes wave {
      0%, 100% { height: 10px; }
      50% { height: 20px; }
    }
  </style>
</head>
<body>
  <div class="response-container">
    <div id="user-input" class="input-text"></div>
    <div id="response" class="response-text"></div>
    <span id="cursor" class="cursor-blink" style="display:none;">▊</span>
    <div id="audio-status"></div>
  </div>

  <script>
    // Show cursor during streaming
    function showStreamingCursor() {
      document.getElementById('cursor').style.display = 'inline-block';
    }

    function hideStreamingCursor() {
      document.getElementById('cursor').style.display = 'none';
    }

    function showAudioStatus(message) {
      const status = document.getElementById('audio-status');
      status.innerHTML = `
        <div class="audio-playing">
          <span class="audio-wave"></span>
          <span class="audio-wave"></span>
          <span class="audio-wave"></span>
          ${message}
        </div>
      `;
    }
  </script>
</body>
</html>
```

---

## 🎬 Comparison: Standard vs Token Streaming

| Feature | Standard Streaming | Token Streaming |
|---------|-------------------|-----------------|
| **Text display** | Complete text at once | Token-by-token (ChatGPT style) |
| **User sees text** | After ~2-4 seconds | Starts in ~0.5-1 second |
| **Visual effect** | Instant full text | Typing effect |
| **Audio** | Sentence chunks | Sentence chunks |
| **Message type** | `audio_base64_streaming` | `audio_base64_streaming_tokens` |
| **Best for** | Simple implementations | Engaging user experience |

---

## ⚡ Performance Characteristics

**Token Streaming Timeline:**
```
0.0s  - Audio sent to backend
0.5s  - STT complete (streaming_stt_complete)
0.6s  - First token arrives (streaming_token)
0.7s  - More tokens... user sees text appearing
2.0s  - All tokens received (streaming_text_complete)
2.5s  - First audio chunk (streaming_audio_chunk)
3.0s  - Second audio chunk
4.0s  - Complete (streaming_complete)
```

---

## 🚀 Quick Start Checklist

- [ ] Update WebSocket message handler to support new message types
- [ ] Implement token streaming display (append tokens as received)
- [ ] Implement audio chunk queue and sequential playback
- [ ] Add visual indicators (cursor blink, audio wave animation)
- [ ] Handle error cases (`streaming_error`)
- [ ] Test with real audio input
- [ ] Optimize for smooth animation (use requestAnimationFrame if needed)

---

## 🐛 Debugging Tips

1. **Console log all messages:**
   ```javascript
   ws.onmessage = (event) => {
     const data = JSON.parse(event.data);
     console.log('Received:', data.type, data);
     // ... handle message
   };
   ```

2. **Track streaming stages:**
   ```javascript
   const stages = {
     stt: false,
     tokens: false,
     audio: false
   };
   
   // Update stages as messages arrive
   ```

3. **Monitor audio queue:**
   ```javascript
   console.log('Audio queue length:', audioQueue.length);
   console.log('Currently playing:', isPlaying);
   ```

---

## 📚 Additional Resources

- WebSocket API: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
- Web Audio API: https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API
- MediaRecorder API: https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder

---

**Need help?** Check the backend test scripts:
- `test_token_streaming.py` - Test token streaming
- `test_streaming_flow.py` - Test complete flow
