# Bilingual Tamil + English TTS Guide

## Overview
When Tamil language is selected by the user, the system now generates responses in **both Tamil and English combined** (Tanglish format), providing a better user experience for bilingual users.

## Features

### 1. Response Format
When `output_language` is set to `"ta"` (Tamil):

**Text Response includes:**
- `response`: Combined text with both Tamil and English
- `tamil_response`: Pure Tamil/Tanglish version
- `english_response`: Pure English version
- `bilingual`: Boolean flag indicating bilingual output
- `language`: Language code ("ta")

### 2. Audio Output
- TTS uses **Tamil Pallavi** voice (natural Tamil female voice)
- Audio synthesizes the combined response (Tamil + English mixed)
- Speech rate adapts based on emotion

### 3. Default Language
- **Default language is now Tamil ("ta")**
- All handlers default to Tamil for both input and output
- Can be overridden by client

## Frontend Implementation

### Basic Usage - Text Query with TTS

```json
{
  "type": "text",
  "query": "hostel fees structure",
  "enable_tts": true,
  "tts_language": "ta",
  "output_language": "ta",
  "input_language": "ta"
}
```

### Response Format

```json
{
  "type": "text_with_audio_response",
  "response": "Hostel fees structure is ... The annual hostel fee is ...",
  "tamil_response": "Hostel fees structure uh ... annual fee ...",
  "english_response": "Hostel fees structure is ... The annual fee is ...",
  "emotion": "Talking",
  "bilingual": true,
  "language": "ta",
  "audio_data": "base64_encoded_audio_data",
  "audio_format": "wav",
  "audio_duration": 4.5
}
```

### Audio-to-Text-to-Speech Flow

```json
{
  "type": "audio_base64_streaming_tokens",
  "audio_data": "base64_encoded_audio",
  "input_language": "ta",
  "output_language": "ta",
  "response_style": "tanglish"
}
```

## Frontend Display Recommendations

### Option 1: Show Combined Response
Display the `response` field which contains both Tamil and English mixed naturally.

### Option 2: Show Both Versions
Display both `tamil_response` and `english_response` side-by-side for clarity:

```
---  தமிழ் (Tamil)  ---
Hostel fees structure uh ... annual fee ...

---  English  ---
Hostel fees structure is ... The annual fee is ...
```

### Option 3: Toggle Between Versions
Add a toggle button to switch between Tamil and English views.

## Language Codes

| Language | Code | Voice | Notes |
|----------|------|-------|-------|
| English | `en` | Aria (US Female) | Default for English |
| Tamil | `ta` | Pallavi (Tamil Female) | **New Default** |
| Hindi | `hi` | Sudha (Hindi Female) | For Hindi-speaking users |

## Payload Parameters

### For Text Queries
```json
{
  "type": "text",
  "query": "your question",
  "enable_tts": true,           // Enable TTS
  "tts_language": "ta",         // Voice language
  "output_language": "ta",      // Response language
  "input_language": "ta",       // For normalization
  "response_style": "tanglish"  // Optional: explicit style
}
```

### For Audio Queries
```json
{
  "type": "audio_base64_streaming_tokens",
  "audio_data": "base64_audio",
  "input_language": "ta",       // STT language
  "output_language": "ta",      // Response language
  "response_style": "tanglish"  // Optional
}
```

## Emotion Support

Emotions affect speech delivery (via speech rate):
- `"none"`: Normal speed (1.0x)
- `"happy"`: Faster speed (1.25x)
- `"sad"`: Slower speed (0.75x)

## Backend Response Handling

### Bilingual Field
- `bilingual: true` - Both Tamil and English versions generated
- `bilingual: false` - Only one version available (fallback case)

### Language Field
Always check `language` field in response:
- `"ta"` - Tamil output
- `"en"` - English output
- `"hi"` - Hindi output

## Error Handling

If TTS fails:
```json
{
  "type": "text_response",
  "response": "The answer text",
  "tts_error": "TTS processing failed"
}
```

Text will still be available even if audio generation fails.

## Performance Tips

1. **Batching**: For better performance, combine text and audio requests
2. **Streaming**: Use token-streaming for faster perceived response
3. **Caching**: Cache frequently asked questions with their audio

## Migration Guide for Existing Frontend

### Old Implementation (English Default)
```json
{
  "type": "text",
  "query": "question",
  "tts_language": "en"
}
```

### New Implementation (Tamil Default)
```json
{
  "type": "text",
  "query": "question",
  "tts_language": "ta",
  "output_language": "ta"
}
```

For backward compatibility, explicitly specify `"output_language": "en"` if English-only response is needed.

## Examples

### Example 1: Tamil User - Text Query
**Request:**
```json
{
  "type": "text",
  "query": "hostel fees",
  "enable_tts": true,
  "tts_language": "ta",
  "output_language": "ta"
}
```

**Response:**
```json
{
  "type": "text_with_audio_response",
  "response": "Hostel fees structure ah nalla clear pannachu. Annual fee 30,000 rupees, monthly uh 2,500 per month.",
  "tamil_response": "Hostel fees structure nalla clear. Annual fee 30,000 rupees...",
  "english_response": "Hostel fees structure is clear. Annual fee is 30,000 rupees per year...",
  "emotion": "Talking",
  "bilingual": true,
  "audio_data": "...",
  "audio_duration": 3.2
}
```

### Example 2: Audio Input with Streaming
**Request:**
```json
{
  "type": "audio_base64_streaming_tokens",
  "audio_data": "base64_tamil_audio",
  "input_language": "ta",
  "output_language": "ta"
}
```

**Response (Streamed tokens, then final audio):**
- Tokens stream in: "Hostel", "fees", "annual", "30000", ...
- Final audio response with Tamil Pallavi voice

## Testing Checklist

- [ ] Text query with Tamil output
- [ ] Audio input with Tamil output
- [ ] Both tamil_response and english_response generated
- [ ] TTS audio plays correctly
- [ ] Emotion affects speech rate
- [ ] Bilingual flag correctly set
- [ ] Fallback to English if Tamil generation fails
- [ ] Combined response sounds natural in Tamil Pallavi voice

