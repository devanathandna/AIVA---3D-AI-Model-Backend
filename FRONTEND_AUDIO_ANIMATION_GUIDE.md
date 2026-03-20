# Frontend Audio Playback & Animation Guide

## Overview
This guide explains how to properly handle TTS audio playback on the frontend and trigger avatar animations during speech.

## Audio Format
- **Format**: MP3 (MPEG Audio Layer III)
- **Encoding**: Base64-encoded in JSON responses
- **Duration**: Provided in response for animation timing

## Response Structure

### Text with Audio Response
```json
{
  "type": "text_with_audio_response",
  "response": "Complete response text...",
  "emotion": "Talking",
  "tts_enabled": true,
  "tts_status": "ready",
  "animation_trigger": "start",
  "audio_data": "//NExAAyAIIADQAA8...base64_encoded_mp3",
  "audio_format": "mp3",
  "audio_duration": 4.5,
  "voice": "ta-IN-PallaviNeural"
}
```

### Key Fields Explained

| Field | Type | Description |
|-------|------|-------------|
| `audio_data` | string (base64) | Encoded MP3 audio bytes |
| `audio_format` | string | Always "mp3" for Edge TTS |
| `audio_duration` | number | Duration in seconds (for timing animations) |
| `tts_enabled` | boolean | Whether TTS was generated |
| `tts_status` | string | "ready" = audio is ready to play |
| `animation_trigger` | string | "start" = begin avatar animation |
| `emotion` | string | Avatar emotion (should sync with audio) |

## Frontend Implementation

### Step 1: Decode and Create Audio URL

```javascript
// Assuming response from WebSocket
const response = JSON.parse(message);

if (response.audio_data && response.audio_format === 'mp3') {
    // Decode base64 to binary
    const binaryString = atob(response.audio_data);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    
    // Create blob and audio URL
    const audioBlob = new Blob([bytes], { type: 'audio/mpeg' });
    const audioUrl = URL.createObjectURL(audioBlob);
    
    return audioUrl;
}
```

### Step 2: Create Audio Element

```javascript
function setupAudioPlayback(response) {
    // Create or get audio element
    const audioElement = document.getElementById('avatar-audio') || 
                        new Audio();
    audioElement.id = 'avatar-audio';
    
    // Decode and set source
    const audioUrl = decodeAudio(response.audio_data);
    audioElement.src = audioUrl;
    
    return audioElement;
}
```

### Step 3: Trigger Animation During Playback

```javascript
async function playAudioWithAnimation(response, avatarElement) {
    if (!response.tts_enabled) {
        console.log('TTS not enabled, skipping audio');
        return;
    }
    
    const audioElement = setupAudioPlayback(response);
    const duration = response.audio_duration;
    
    // Start animation BEFORE audio plays
    if (response.animation_trigger === 'start') {
        startTalkingAnimation(avatarElement, response.emotion);
    }
    
    // Play audio
    console.log(`Starting audio playback (${duration.toFixed(1)}s)`);
    audioElement.play().catch(err => {
        console.error('Audio playback failed:', err);
        stopTalkingAnimation(avatarElement);
    });
    
    // Stop animation when audio ends
    audioElement.onended = () => {
        console.log('Audio playback completed');
        stopTalkingAnimation(avatarElement);
    };
    
    // Safety timeout in case onended doesn't fire
    setTimeout(() => {
        stopTalkingAnimation(avatarElement);
    }, (duration + 0.5) * 1000);
}

function startTalkingAnimation(element, emotion = 'Talking') {
    // Play avatar talking animation
    element.classList.add('animating', `emotion-${emotion}`);
    console.log(`Starting animation: ${emotion}`);
}

function stopTalkingAnimation(element) {
    // Stop avatar animation
    element.classList.remove('animating');
    console.log('Animation stopped');
}
```

### Step 4: Complete Integration Example

```javascript
class AvatarTTSHandler {
    constructor(avatarElement, audioContainerId = 'audio-container') {
        this.avatar = avatarElement;
        this.audioContainer = document.getElementById(audioContainerId) || 
                            document.body;
        this.currentAudio = null;
        this.isPlaying = false;
    }
    
    async handleResponse(response) {
        // Check if audio is enabled
        if (!response.tts_enabled || !response.audio_data) {
            console.log('No audio data in response');
            return false;
        }
        
        try {
            // Kill previous audio if still playing
            if (this.currentAudio?.playing) {
                this.currentAudio.pause();
                this.currentAudio = null;
            }
            
            // Setup and play new audio
            const audioElement = this.setupAudioElement(response);
            this.currentAudio = audioElement;
            this.isPlaying = true;
            
            // Setup animation sync
            this.syncAnimation(response);
            
            // Play audio
            await audioElement.play();
            
            console.log(`Playing TTS audio: ${response.audio_duration.toFixed(1)}s`);
            return true;
            
        } catch (error) {
            console.error('TTS playback error:', error);
            this.stopAnimation();
            return false;
        }
    }
    
    setupAudioElement(response) {
        const audioElement = new Audio();
        
        // Decode base64 MP3
        const binaryString = atob(response.audio_data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        const audioBlob = new Blob([bytes], { type: 'audio/mpeg' });
        const audioUrl = URL.createObjectURL(audioBlob);
        audioElement.src = audioUrl;
        
        // Setup event handlers
        audioElement.onended = () => this.handleAudioEnd();
        audioElement.onerror = (e) => this.handleAudioError(e);
        
        // Cleanup URL after loading
        audioElement.onloadstart = () => {
            // Audio has started loading
        };
        
        return audioElement;
    }
    
    syncAnimation(response) {
        const emotion = response.emotion || 'Talking';
        const duration = response.audio_duration || 5;
        
        // Start talking animation
        this.startAnimation(emotion);
        
        // Safety stop after duration + buffer
        this.animationTimeout = setTimeout(
            () => this.stopAnimation(),
            (duration + 0.5) * 1000
        );
    }
    
    startAnimation(emotion) {
        this.avatar.classList.add('talking', `emotion-${emotion}`);
        this.avatar.setAttribute('data-emotion', emotion);
        console.log(`Avatar animation: ${emotion}`);
    }
    
    stopAnimation() {
        this.avatar.classList.remove('talking');
        this.isPlaying = false;
        if (this.animationTimeout) {
            clearTimeout(this.animationTimeout);
        }
    }
    
    handleAudioEnd() {
        console.log('Audio playback ended');
        this.stopAnimation();
    }
    
    handleAudioError(error) {
        console.error('Audio playback error:', error);
        this.stopAnimation();
    }
}

// Usage
const ttHandler = new AvatarTTSHandler(
    document.getElementById('avatar'),
    'audio-container'
);

// When receiving WebSocket message
webSocket.onmessage = async (event) => {
    const response = JSON.parse(event.data);
    
    if (response.type === 'text_with_audio_response') {
        // Display text
        document.getElementById('response-text').textContent = response.response;
        
        // Play audio and animate
        await ttHandler.handleResponse(response);
    }
};
```

## CSS for Animation

```css
.avatar {
    transition: all 0.3s ease;
}

.avatar.talking {
    animation: talking 0.4s infinite;
}

@keyframes talking {
    0%, 100% {
        transform: translateY(0);
    }
    50% {
        transform: translateY(-3px);
    }
}

/* Emotion-specific animations */
.avatar.emotion-Talking {
    filter: brightness(1);
}

.avatar.emotion-Acknowledging {
    animation: nodding 0.6s infinite;
}

@keyframes nodding {
    0%, 100% {
        transform: rotateX(0deg);
    }
    50% {
        transform: rotateX(-5deg);
    }
}

.avatar.emotion-Talking2 {
    animation: talking2 0.5s infinite;
}

@keyframes talking2 {
    0%, 100% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.02);
    }
}
```

## Debug Logging

```javascript
function enableDebugLogging(response) {
    console.group('TTS Response Debug Info');
    console.log('TTS Enabled:', response.tts_enabled);
    console.log('Audio Format:', response.audio_format);
    console.log('Duration:', response.audio_duration, 'seconds');
    console.log('Status:', response.tts_status);
    console.log('Animation Trigger:', response.animation_trigger);
    console.log('Emotion:', response.emotion);
    console.log('Audio Data Length:', response.audio_data?.length || 0, 'chars');
    console.log('Voice:', response.voice);
    console.groupEnd();
}

// Usage in response handler
webSocket.onmessage = (event) => {
    const response = JSON.parse(event.data);
    enableDebugLogging(response);
    // ... rest of handler
};
```

## Troubleshooting

### Audio Not Playing
1. Check `audio_data` is not empty/null
2. Verify `audio_format` is "mp3"
3. Ensure base64 decoding is correct
4. Check browser console for CORS or permission errors
5. Test with simple Audio() element first

### Animation Not Syncing
1. Verify `audio_duration` is accurate
2. Check animation classes are being added
3. Monitor `onended` event firing
4. Use timeout as backup (duration + buffer)
5. Ensure CSS animation is applied

### Timing Issues
- Add 0.5s buffer after duration for safety
- Use both `onended` event AND timeout
- Log animation start/stop times
- Check for multiple audio elements interfering

## Response Handling Checklist

- [ ] Check `tts_enabled` before playing audio
- [ ] Decode base64 audio data correctly
- [ ] Create Audio element properly
- [ ] Handle audio playback errors
- [ ] Start animation before audio plays
- [ ] Use both onended AND timeout for stopping
- [ ] Clean up audio URLs with revokeObjectURL
- [ ] Log debug info in development
- [ ] Test with different durations
- [ ] Test with different emotions
- [ ] Verify MP3 codec support in target browsers

