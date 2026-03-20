# 🎵 Edge TTS Enhanced Testing Guide

## Overview

The `test_edge_tts_enhanced.py` module provides a feature-rich testing environment for Microsoft Edge Text-to-Speech (TTS) with comprehensive customization options.

## Features

✅ **Multiple Voice Options**
- US English (4 voices)
- Indian English (2 voices)
- British English (2 voices)
- Tamil (2 voices)
- Hindi (2 voices)

✅ **Customization Controls**
- Speech Rate: 0.5x to 2.0x
- Pitch: -50 to +50 semitones
- Volume: 0-100%
- Language/Regional Support

✅ **Playback Modes**
- Real-time audio playback with pygame
- File-based synthesis and saving
- In-memory streaming
- Automatic volume control

✅ **Testing Modes**
- Interactive CLI testing
- Voice demonstrations
- Speech rate variations
- Pitch variations
- Multilingual samples

## Installation

### 1. Install Required Packages

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install edge-tts pygame pydub
```

### 2. Optional: Install FFmpeg (for pydub advanced features)

**Windows:**
```bash
choco install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

## Quick Start

### Interactive Mode (Default)

```bash
python test_edge_tts_enhanced.py
```

This launches an interactive CLI where you can:
- List available voices
- Change voice, rate, pitch, volume
- Test synthesis with automatic playback
- Save audio files

### Interactive Commands

```
list [filter]       - List all voices (optional regex filter)
voice <voice_id>    - Set the voice
rate <0.5-2.0>      - Set speech rate (0.5x = slower, 2.0x = faster)
pitch <-50 to +50>  - Set pitch in semitones
volume <0-100>      - Set volume as percentage
settings            - Display current settings
test <text>         - Synthesize text and play automatically
save <text>         - Synthesize text and save to file
quit                - Exit
```

### Example Interactive Session

```bash
$ python test_edge_tts_enhanced.py

> list          # Show all voices
> voice en-IN-PrabhatNeural
✅ Voice set to: Prabhat (India Male)

> rate 1.5
✅ Speech rate set to: 1.5x

> pitch 10
✅ Pitch set to: 10 semitones

> test Hello from India with faster speech and higher pitch
🔊 Playing audio (volume: 100%)...
✅ Playback completed

> save This is saved to file
✅ Saved to: audio_output/tts_IN_1.5x_+10p.mp3

> quit
👋 Goodbye!
```

## Demo Modes

### Demo All Voices

```bash
python test_edge_tts_enhanced.py --mode demo-voices
```

Demonstrates the first 3 available voices and saves samples.

### Demo Speech Rates

```bash
python test_edge_tts_enhanced.py --mode demo-rates
```

Synthesizes the same text at different speech rates (0.5x, 1.0x, 1.5x, 2.0x).

### Demo Pitch Variations

```bash
python test_edge_tts_enhanced.py --mode demo-pitches
```

Generates audio samples at different pitch levels (-20, -10, 0, +10, +20).

### Demo Multilingual

```bash
python test_edge_tts_enhanced.py --mode demo-multilingual
```

Demonstrates support for English (US, India, UK), Tamil, and Hindi with native text samples.

## Command-Line Options

```bash
python test_edge_tts_enhanced.py [OPTIONS]

OPTIONS:
  --mode {interactive|demo-voices|demo-rates|demo-pitches|demo-multilingual}
         Default: interactive

  --text TEXT              Text to synthesize
  --voice VOICE_ID         Voice to use (e.g., en-US-AriaNeural)
  --rate RATE              Speech rate (0.5-2.0)
  --pitch PITCH            Pitch (-50 to +50)
  --volume VOLUME          Volume (0-100)
  --save FILENAME          Save to file instead of playing
```

## Usage Examples

### Example 1: Quick Synthesis with Playback

```bash
python test_edge_tts_enhanced.py --text "Hello World" --voice en-US-AriaNeural --rate 1.2
```

### Example 2: Indian English with Higher Pitch

```bash
python test_edge_tts_enhanced.py --text "Namaste from India" --voice en-IN-PrabhatNeural --pitch 15 --rate 0.9
```

### Example 3: Save with Custom Settings

```bash
python test_edge_tts_enhanced.py \
  --text "This is stored in a file" \
  --voice ta-IN-ValluvarNeural \
  --pitch 10 \
  --rate 1.3 \
  --save tamil_sample.mp3
```

### Example 4: Low Volume, Slow Speech

```bash
python test_edge_tts_enhanced.py \
  --text "Speaking slowly and quietly" \
  --rate 0.6 \
  --volume 50
```

## Available Voices

### English - United States
- `en-US-AriaNeural` - Aria (Female) ⭐ Default
- `en-US-AmberNeural` - Amber (Female)
- `en-US-AshleyNeural` - Ashley (Female)
- `en-US-GuyNeural` - Guy (Male)
- `en-US-BrianNeural` - Brian (Male)
- `en-US-ChristopherNeural` - Christopher (Male)

### English - India (Indian Accent)
- `en-IN-NeerjaNeural` - Neerja (Female)
- `en-IN-PrabhatNeural` - Prabhat (Male)

### English - United Kingdom
- `en-GB-Amelia-Neural` - Amelia (Female)
- `en-GB-RyanNeural` - Ryan (Male)

### Tamil
- `ta-IN-ValluvarNeural` - Valluvar (Male)
- `ta-IN-PallaviNeural` - Pallavi (Female)

### Hindi
- `hi-IN-MadhurNeural` - Madhur (Male)
- `hi-IN-SudhaNeural` - Sudha (Female)

## Customization Details

### Speech Rate
- **Range:** 0.5x to 2.0x
- **Default:** 1.0x (normal speed)
- **Examples:**
  - 0.5x: Very slow, clear pronunciation
  - 0.75x: Slower than normal
  - 1.0x: Normal speed
  - 1.5x: Faster speech
  - 2.0x: Maximum speed

### Pitch
- **Range:** -50 to +50 semitones
- **Default:** 0 (original pitch)
- **Examples:**
  - -20: Noticeably lower pitch (deeper voice)
  - 0: Original pitch
  - +20: Noticeably higher pitch (lighter voice)

### Volume
- **Range:** 0 to 100%
- **Default:** 100%
- **Examples:**
  - 0%: Silent
  - 30%: Very quiet
  - 50%: Medium
  - 100%: Maximum volume

## Output Directory

All saved files go to: `./audio_output/`

Naming convention: `tts_{VOICE}_{RATE}x_{PITCH}p.mp3`

Example: `tts_US_1.5x_+10p.mp3`

## Troubleshooting

### Issue: "pygame not installed. Audio playback disabled."

**Solution:** Install pygame
```bash
pip install pygame
```

### Issue: "pydub not installed. Advanced audio processing disabled."

**Solution:** Install pydub and ffmpeg
```bash
pip install pydub
```

### Issue: Audio not playing

**Possible causes:**
1. pygame not installed - see above
2. System audio issues - check system volume
3. Use `--save` to save to file instead and test with a media player

### Issue: No output audio but process completes

**Solution:** Check the `audio_output/` directory for generated files

## Integration with Existing Code

### Using EdgeTTSCustomizer in Your Code

```python
from test_edge_tts_enhanced import EdgeTTSCustomizer
import asyncio

async def custom_tts():
    customizer = EdgeTTSCustomizer()
    
    # Configure
    customizer.set_voice("en-IN-PrabhatNeural")
    customizer.set_speech_rate(1.2)
    customizer.set_pitch(5)
    customizer.set_volume(80)
    
    # Synthesize and play
    result = await customizer.synthesize_and_play("Your text here")
    
    # Or save to file
    result = await customizer.synthesize_to_file("Your text here")
    
    return result

# Run
asyncio.run(custom_tts())
```

### Integration with FastAPI

```python
from fastapi import FastAPI
from fastapi.responses import FileResponse
from test_edge_tts_enhanced import EdgeTTSCustomizer
import asyncio

app = FastAPI()
customizer = EdgeTTSCustomizer()

@app.get("/tts")
async def tts_endpoint(
    text: str,
    voice: str = "en-US-AriaNeural",
    rate: float = 1.0,
    pitch: float = 0,
    volume: int = 100
):
    customizer.set_voice(voice)
    customizer.set_speech_rate(rate)
    customizer.set_pitch(pitch)
    customizer.set_volume(volume)
    
    result = await customizer.synthesize_to_file(text)
    
    if result["success"]:
        return FileResponse(result["filepath"])
    return {"error": result["error"]}
```

## Performance Notes

- **First synthesis:** ~2-3 seconds (network latency)
- **Subsequent calls:** ~1-2 seconds
- **Playback:** Real-time
- **File size:** ~10-50 KB per minute of audio

## API Rate Limits

Edge TTS has generous rate limits for personal/development use. For production, consider:
- Caching synthesized audio
- Batch processing requests
- Using the groq_llama_agent for local fallback

## License & Attribution

Uses Microsoft Edge TTS service via the `edge-tts` Python library.
- GitHub: https://github.com/rany2/edge-tts

## Related Files

- Main agent: `agent/groq_llama_agent.py`
- Existing TTS: `audio/tts.py`
- Server: `server/websocket_handler.py`
- Audio manager: `audio/manager.py`

## Questions?

Check the logs for detailed debugging:
- Interactive mode shows real-time logs
- All operations logged to console
- Errors include specific error messages and suggestions
