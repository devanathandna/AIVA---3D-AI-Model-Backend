"""
Enhanced Edge TTS Testing Module
Supports automatic voice playback with manual customization options
Features:
- Multiple voice selections (English, Indian, Tamil accents)
- Speech rate control (0.5x to 2.0x)
- Pitch customization
- Volume control
- Real-time streaming playback
- Audio file saving
- Interactive CLI testing
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np

try:
    import edge_tts
except ImportError:
    print("❌ edge_tts not installed. Install with: pip install edge-tts")
    sys.exit(1)

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    print("⚠️  pygame not installed. Audio playback disabled. Install with: pip install pygame")
    PYGAME_AVAILABLE = False

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    print("⚠️  pydub not installed. Advanced audio processing disabled. Install with: pip install pydub")
    PYDUB_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EdgeTTSCustomizer:
    """Enhanced Edge TTS with manual customization capabilities"""
    
    # Comprehensive voice collection with accents and languages
    AVAILABLE_VOICES = {
        # English - US (Female)
        "en-US-AriaNeural": {
            "name": "Aria (US Female)",
            "language": "en-US",
            "gender": "Female",
            "region": "United States"
        },
        "en-US-AmberNeural": {
            "name": "Amber (US Female)",
            "language": "en-US",
            "gender": "Female",
            "region": "United States"
        },
        "en-US-AshleyNeural": {
            "name": "Ashley (US Female)",
            "language": "en-US",
            "gender": "Female",
            "region": "United States"
        },
        
        # English - US (Male)
        "en-US-GuyNeural": {
            "name": "Guy (US Male)",
            "language": "en-US",
            "gender": "Male",
            "region": "United States"
        },
        "en-US-BrianNeural": {
            "name": "Brian (US Male)",
            "language": "en-US",
            "gender": "Male",
            "region": "United States"
        },
        "en-US-ChristopherNeural": {
            "name": "Christopher (US Male)",
            "language": "en-US",
            "gender": "Male",
            "region": "United States"
        },
        
        # English - India (Female)
        "en-IN-NeerjaNeural": {
            "name": "Neerja (India Female)",
            "language": "en-IN",
            "gender": "Female",
            "region": "India",
            "accent": "Indian"
        },
        
        # English - India (Male)
        "en-IN-PrabhatNeural": {
            "name": "Prabhat (India Male)",
            "language": "en-IN",
            "gender": "Male",
            "region": "India",
            "accent": "Indian"
        },
        
        # English - British
        "en-GB-Amelia-Neural": {
            "name": "Amelia (UK Female)",
            "language": "en-GB",
            "gender": "Female",
            "region": "United Kingdom"
        },
        "en-GB-RyanNeural": {
            "name": "Ryan (UK Male)",
            "language": "en-GB",
            "gender": "Male",
            "region": "United Kingdom"
        },
        
        # Tamil
        "ta-IN-ValluvarNeural": {
            "name": "Valluvar (Tamil Male)",
            "language": "ta-IN",
            "gender": "Male",
            "region": "India",
            "native_language": "Tamil"
        },
        "ta-IN-PallaviNeural": {
            "name": "Pallavi (Tamil Female)",
            "language": "ta-IN",
            "gender": "Female",
            "region": "India",
            "native_language": "Tamil"
        },
        
        # Hindi
        "hi-IN-MadhurNeural": {
            "name": "Madhur (Hindi Male)",
            "language": "hi-IN",
            "gender": "Male",
            "region": "India"
        },
        "hi-IN-SudhaNeural": {
            "name": "Sudha (Hindi Female)",
            "language": "hi-IN",
            "gender": "Female",
            "region": "India"
        },
    }
    
    # Speech rate range: 0.5x to 2.0x
    MIN_RATE = 0.5
    MAX_RATE = 2.0
    DEFAULT_RATE = 1.0
    
    # Pitch range: -50.00 to +50.00 semitones
    MIN_PITCH = -50.0
    MAX_PITCH = 50.0
    DEFAULT_PITCH = 0.0
    
    # Volume range: 0 to 100
    MIN_VOLUME = 0
    MAX_VOLUME = 100
    DEFAULT_VOLUME = 100
    
    def __init__(self):
        """Initialize Edge TTS customizer"""
        self.default_voice = "en-US-AriaNeural"
        self.speech_rate = self.DEFAULT_RATE
        self.pitch = self.DEFAULT_PITCH
        self.volume = self.DEFAULT_VOLUME
        self.output_dir = Path("./audio_output")
        self.output_dir.mkdir(exist_ok=True)
        logger.info("✅ Edge TTS Customizer initialized")
    
    def set_voice(self, voice_id: str) -> bool:
        """Set voice with validation"""
        if voice_id not in self.AVAILABLE_VOICES:
            logger.error(f"❌ Voice '{voice_id}' not found")
            return False
        self.default_voice = voice_id
        logger.info(f"✅ Voice set to: {self.AVAILABLE_VOICES[voice_id]['name']}")
        return True
    
    def set_speech_rate(self, rate: float) -> bool:
        """Set speech rate (0.5 to 2.0)"""
        if not self.MIN_RATE <= rate <= self.MAX_RATE:
            logger.error(f"❌ Speech rate must be between {self.MIN_RATE} and {self.MAX_RATE}")
            return False
        self.speech_rate = rate
        logger.info(f"✅ Speech rate set to: {rate}x")
        return True
    
    def set_pitch(self, pitch: float) -> bool:
        """Set pitch (-50 to +50 semitones)"""
        if not self.MIN_PITCH <= pitch <= self.MAX_PITCH:
            logger.error(f"❌ Pitch must be between {self.MIN_PITCH} and {self.MAX_PITCH}")
            return False
        self.pitch = pitch
        logger.info(f"✅ Pitch set to: {pitch} semitones")
        return True
    
    def set_volume(self, volume: int) -> bool:
        """Set volume (0 to 100)"""
        if not self.MIN_VOLUME <= volume <= self.MAX_VOLUME:
            logger.error(f"❌ Volume must be between {self.MIN_VOLUME} and {self.MAX_VOLUME}")
            return False
        self.volume = volume
        logger.info(f"✅ Volume set to: {volume}%")
        return True
    
    def list_voices(self, filter_by: Optional[str] = None) -> None:
        """List all available voices with optional filtering"""
        print("\n" + "="*80)
        print("🎤 AVAILABLE VOICES")
        print("="*80)
        
        voices_to_show = self.AVAILABLE_VOICES
        
        if filter_by:
            filter_lower = filter_by.lower()
            voices_to_show = {
                k: v for k, v in self.AVAILABLE_VOICES.items()
                if filter_lower in k.lower() or 
                   filter_lower in v.get("name", "").lower() or
                   filter_lower in v.get("region", "").lower()
            }
        
        if not voices_to_show:
            print(f"No voices found matching '{filter_by}'")
            return
        
        current = "→ " if self.default_voice in voices_to_show else "  "
        
        for voice_id, info in sorted(voices_to_show.items()):
            gender_emoji = "👩" if info["gender"] == "Female" else "👨"
            accent = f" ({info.get('accent', info.get('native_language', ''))})" if info.get('accent') or info.get('native_language') else ""
            
            print(f"{current}{gender_emoji} {info['name']}{accent}")
            print(f"   ID: {voice_id} | Region: {info['region']}")
            print()
    
    def get_current_settings(self) -> Dict[str, Any]:
        """Get current TTS settings"""
        return {
            "voice": self.default_voice,
            "voice_name": self.AVAILABLE_VOICES[self.default_voice]["name"],
            "speech_rate": self.speech_rate,
            "pitch": self.pitch,
            "volume": self.volume
        }
    
    def display_settings(self) -> None:
        """Display current settings"""
        settings = self.get_current_settings()
        print("\n" + "="*50)
        print("⚙️  CURRENT TTS SETTINGS")
        print("="*50)
        print(f"🎤 Voice: {settings['voice_name']}")
        print(f"🎵 Speech Rate: {settings['speech_rate']}x")
        print(f"📊 Pitch: {settings['pitch']} semitones")
        print(f"🔊 Volume: {settings['volume']}%")
        print("="*50 + "\n")
    
    async def synthesize_to_file(
        self,
        text: str,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesize and save to file
        
        Args:
            text: Text to synthesize
            filename: Output filename (auto-generated if not provided)
            
        Returns:
            Result dictionary with file path and metadata
        """
        if not text.strip():
            logger.error("❌ Text is empty")
            return {"success": False, "error": "Empty text"}
        
        try:
            # Generate filename if not provided
            if filename is None:
                voice_short = self.default_voice.split("-")[1][:2]
                filename = f"tts_{voice_short}_{self.speech_rate}x_{self.pitch}p.mp3"
            
            filepath = self.output_dir / filename
            
            logger.info(f"🔄 Synthesizing: '{text[:50]}...' to {filepath}")
            
            # Create communicate instance with customization
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.default_voice,
                rate=f"{self.speech_rate:+.0%}",  # Format as percentage
                pitch=f"{self.pitch:+.0f}Hz"  # Format in Hz
            )
            
            # Save to file
            await communicate.save(str(filepath))
            
            file_size = filepath.stat().st_size
            logger.info(f"✅ Saved: {filepath} ({file_size} bytes)")
            
            return {
                "success": True,
                "filepath": str(filepath),
                "filename": filename,
                "file_size": file_size,
                "text": text,
                "voice": self.default_voice,
                "settings": self.get_current_settings()
            }
            
        except Exception as e:
            logger.error(f"❌ Synthesis error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def synthesize_and_play(
        self,
        text: str,
        auto_play: bool = True
    ) -> Dict[str, Any]:
        """
        Synthesize and optionally play audio
        
        Args:
            text: Text to synthesize
            auto_play: Whether to automatically play the audio
            
        Returns:
            Result dictionary
        """
        if not PYGAME_AVAILABLE:
            logger.warning("⚠️  Pygame not available. Saving to file instead...")
            return await self.synthesize_to_file(text)
        
        try:
            logger.info(f"🔄 Synthesizing and preparing playback...")
            
            # Create in-memory audio stream
            submaker = edge_tts.Communicate(
                text=text,
                voice=self.default_voice,
                rate=f"{self.speech_rate:+.0%}",
                pitch=f"{self.pitch:+.0f}Hz"
            )
            
            # Collect audio data
            audio_data = b""
            async for chunk in submaker.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            if not audio_data:
                logger.error("❌ No audio data generated")
                return {"success": False, "error": "No audio data"}
            
            logger.info(f"✅ Audio generated: {len(audio_data)} bytes")
            
            if auto_play:
                self._play_audio(audio_data)
            
            return {
                "success": True,
                "audio_data_size": len(audio_data),
                "text": text,
                "voice": self.default_voice,
                "settings": self.get_current_settings(),
                "played": auto_play
            }
            
        except Exception as e:
            logger.error(f"❌ Error during synthesis/playback: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _play_audio(self, audio_data: bytes) -> None:
        """Play audio using pygame"""
        if not PYGAME_AVAILABLE:
            logger.error("❌ Pygame not available for playback")
            return
        
        try:
            from io import BytesIO
            
            # Initialize mixer
            pygame.mixer.init()
            
            # Create sound from bytes
            sound_file = BytesIO(audio_data)
            sound = pygame.mixer.Sound(sound_file)
            
            # Apply volume
            volume_normalized = self.volume / 100.0
            sound.set_volume(volume_normalized)
            
            logger.info(f"🔊 Playing audio (volume: {self.volume}%)...")
            sound.play()
            
            # Wait for playback to complete
            duration = sound.get_length()
            asyncio.run(asyncio.sleep(duration + 0.5))  # Small buffer
            
            logger.info("✅ Playback completed")
            
        except Exception as e:
            logger.error(f"❌ Playback error: {str(e)}")


async def interactive_testing():
    """Interactive CLI for testing Edge TTS"""
    customizer = EdgeTTSCustomizer()
    customizer.display_settings()
    
    print("\n" + "="*60)
    print("🎵 INTERACTIVE EDGE TTS TESTING")
    print("="*60)
    print("\nAvailable Commands:")
    print("  list [filter]       - List voices (optional filter)")
    print("  voice <voice_id>    - Set voice")
    print("  rate <0.5-2.0>      - Set speech rate")
    print("  pitch <-50 to +50>  - Set pitch")
    print("  volume <0-100>      - Set volume (percent)")
    print("  settings            - Show current settings")
    print("  test <text>         - Synthesize and play text")
    print("  save <text>         - Synthesize and save to file")
    print("  quit                - Exit testing")
    print("="*60)
    
    while True:
        try:
            command = input("\n> ").strip()
            
            if not command:
                continue
            
            parts = command.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else None
            
            if cmd == "quit":
                print("👋 Goodbye!")
                break
            
            elif cmd == "list":
                customizer.list_voices(arg)
            
            elif cmd == "voice":
                if not arg:
                    print("❌ Please provide voice ID")
                else:
                    customizer.set_voice(arg)
            
            elif cmd == "rate":
                if not arg:
                    print("❌ Please provide rate (0.5-2.0)")
                else:
                    try:
                        rate = float(arg)
                        customizer.set_speech_rate(rate)
                    except ValueError:
                        print("❌ Invalid rate value")
            
            elif cmd == "pitch":
                if not arg:
                    print("❌ Please provide pitch (-50 to +50)")
                else:
                    try:
                        pitch = float(arg)
                        customizer.set_pitch(pitch)
                    except ValueError:
                        print("❌ Invalid pitch value")
            
            elif cmd == "volume":
                if not arg:
                    print("❌ Please provide volume (0-100)")
                else:
                    try:
                        volume = int(arg)
                        customizer.set_volume(volume)
                    except ValueError:
                        print("❌ Invalid volume value")
            
            elif cmd == "settings":
                customizer.display_settings()
            
            elif cmd == "test":
                if not arg:
                    print("❌ Please provide text to synthesize")
                else:
                    await customizer.synthesize_and_play(arg, auto_play=True)
                    print("✅ Test completed")
            
            elif cmd == "save":
                if not arg:
                    print("❌ Please provide text to synthesize")
                else:
                    result = await customizer.synthesize_to_file(arg)
                    if result["success"]:
                        print(f"✅ Saved to: {result['filepath']}")
                    else:
                        print(f"❌ Error: {result['error']}")
            
            else:
                print("❌ Unknown command. Try 'list', 'voice', 'rate', 'pitch', 'volume', 'settings', 'test', 'save', or 'quit'")
        
        except KeyboardInterrupt:
            print("\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")


async def demo_all_voices():
    """Demonstrate all available voices"""
    customizer = EdgeTTSCustomizer()
    test_text = "Hello! This is a voice sample."
    
    print("\n" + "="*60)
    print("🎵 VOICE DEMONSTRATION")
    print("="*60)
    
    voices = list(customizer.AVAILABLE_VOICES.keys())[:3]  # Demo first 3 voices
    
    for voice_id in voices:
        customizer.set_voice(voice_id)
        print(f"\n🎤 Testing: {customizer.AVAILABLE_VOICES[voice_id]['name']}")
        result = await customizer.synthesize_to_file(test_text)
        if result["success"]:
            print(f"   ✅ Saved: {result['filename']}")


async def demo_rate_variations():
    """Demonstrate speech rate variations"""
    customizer = EdgeTTSCustomizer()
    test_text = "Rate variations testing. Slow, normal, fast speeds."
    
    print("\n" + "="*60)
    print("📊 SPEECH RATE VARIATIONS")
    print("="*60)
    
    rates = [0.5, 1.0, 1.5, 2.0]
    
    for rate in rates:
        customizer.set_speech_rate(rate)
        result = await customizer.synthesize_to_file(test_text)
        if result["success"]:
            print(f"✅ Rate {rate}x: {result['filename']}")


async def demo_pitch_variations():
    """Demonstrate pitch variations"""
    customizer = EdgeTTSCustomizer()
    test_text = "Pitch variation test. Lower and higher pitch."
    
    print("\n" + "="*60)
    print("🎵 PITCH VARIATIONS")
    print("="*60)
    
    pitches = [-20, -10, 0, 10, 20]
    
    for pitch in pitches:
        customizer.set_pitch(pitch)
        result = await customizer.synthesize_to_file(test_text)
        if result["success"]:
            print(f"✅ Pitch {pitch:+d}: {result['filename']}")


async def demo_multilingual():
    """Demonstrate multilingual support"""
    customizer = EdgeTTSCustomizer()
    
    tests = [
        ("en-US-AriaNeural", "Hello from United States"),
        ("en-IN-PrabhatNeural", "Namaste from India"),
        ("en-GB-RyanNeural", "Hello from United Kingdom"),
        ("ta-IN-ValluvarNeural", "வணக்கம் தமிழ் நாட்டிலிருந்து"),
        ("hi-IN-MadhurNeural", "नमस्ते हिंदी से"),
    ]
    
    print("\n" + "="*60)
    print("🌍 MULTILINGUAL SUPPORT")
    print("="*60)
    
    for voice_id, text in tests:
        customizer.set_voice(voice_id)
        result = await customizer.synthesize_to_file(text)
        if result["success"]:
            print(f"✅ {customizer.AVAILABLE_VOICES[voice_id]['name']}: {result['filename']}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enhanced Edge TTS Testing with Manual Customization"
    )
    parser.add_argument(
        "--mode",
        choices=["interactive", "demo-voices", "demo-rates", "demo-pitches", "demo-multilingual"],
        default="interactive",
        help="Testing mode"
    )
    parser.add_argument(
        "--text",
        type=str,
        help="Text to synthesize (non-interactive mode)"
    )
    parser.add_argument(
        "--voice",
        type=str,
        help="Voice ID to use"
    )
    parser.add_argument(
        "--rate",
        type=float,
        help="Speech rate (0.5-2.0)"
    )
    parser.add_argument(
        "--pitch",
        type=float,
        help="Pitch (-50 to +50)"
    )
    parser.add_argument(
        "--volume",
        type=int,
        help="Volume (0-100)"
    )
    parser.add_argument(
        "--save",
        type=str,
        help="Save to file instead of playing"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == "interactive":
            await interactive_testing()
        
        elif args.mode == "demo-voices":
            await demo_all_voices()
        
        elif args.mode == "demo-rates":
            await demo_rate_variations()
        
        elif args.mode == "demo-pitches":
            await demo_pitch_variations()
        
        elif args.mode == "demo-multilingual":
            await demo_multilingual()
        
        else:
            # Custom synthesis mode
            customizer = EdgeTTSCustomizer()
            
            if args.voice:
                customizer.set_voice(args.voice)
            if args.rate:
                customizer.set_speech_rate(args.rate)
            if args.pitch:
                customizer.set_pitch(args.pitch)
            if args.volume:
                customizer.set_volume(args.volume)
            
            if not args.text:
                print("❌ Please provide text with --text")
                return
            
            customizer.display_settings()
            
            if args.save:
                result = await customizer.synthesize_to_file(args.text, args.save)
                if result["success"]:
                    print(f"✅ Saved to: {result['filepath']}")
                else:
                    print(f"❌ Error: {result['error']}")
            else:
                result = await customizer.synthesize_and_play(args.text)
                if result["success"]:
                    print("✅ Synthesis completed")
                else:
                    print(f"❌ Error: {result['error']}")
    
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
