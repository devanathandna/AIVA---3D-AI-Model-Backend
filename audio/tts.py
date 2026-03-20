"""
Text-to-Speech module using Edge TTS with language-based voice selection
"""
import os
import asyncio
import tempfile
import logging
import wave
import re
from typing import Optional, Dict, Any, Union, List
from io import BytesIO
import json

try:
    import edge_tts
except ImportError:
    raise ImportError("edge_tts not installed. Install with: pip install edge-tts")

logger = logging.getLogger(__name__)

class TTSProcessor:
    def __init__(self):
        """
        Initialize TTS processor with Edge TTS
        """
        # Edge TTS voice mapping by language - Tamil Pallavi as default
        self.voice_mapping = {
            "en": "en-US-AriaNeural",      # English - US Female
            "ta": "ta-IN-PallaviNeural",   # Tamil - Pallavi (Female) - DEFAULT
            "hi": "hi-IN-SudhaNeural",     # Hindi - Female
            "default": "ta-IN-PallaviNeural"  # Default voice (Tamil Pallavi)
        }
        
        # Emotion mapping for Edge TTS (speech rate adjustments)
        self.emotion_rate_map = {
            "happy": 1.25,    # Faster speech
            "sad": 0.75,      # Slower speech
            "none": 1.0       # Normal speed
        }
        
    async def synthesize_speech(
        self, 
        text: str, 
        language: str = "ta",  # Tamil as default
        voice: Optional[str] = None,
        emotion: str = "none"
    ) -> Dict[str, Any]:
        """
        Convert text to speech using Edge TTS
        
        Args:
            text: Text to synthesize
            language: Language code ("en", "ta", "hi", etc.)
            voice: Specific voice name (optional, overrides language selection)
            emotion: Emotion for speech ("happy", "sad", "none")
            
        Returns:
            Dict with audio data and metadata
        """
        try:
            # Select voice based on language or use provided voice
            if voice:
                selected_voice = voice
            else:
                # Use language-mapped voice, or Tamil Pallavi if language not found
                selected_voice = self.voice_mapping.get(language, self.voice_mapping["default"])
            
            # Get speech rate based on emotion
            rate = self.emotion_rate_map.get(emotion, 1.0)
            
            logger.info(f"Synthesizing with Edge TTS: voice={selected_voice}, emotion={emotion}, rate={rate}")
            
            # Directly call async synthesis (don't use executor)
            result = await self._synthesize_with_edge_tts_async(text, selected_voice, rate)
            
            return {
                "success": True,
                "audio_data": result["audio_data"],
                "format": result.get("format", "mp3"),
                "voice": selected_voice,
                "language": language,
                "emotion": emotion,
                "duration": result["duration"],
                "size": len(result["audio_data"]),
                "provider": "edge_tts"
            }
            
        except Exception as e:
            logger.error(f"Edge TTS synthesis error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "audio_data": b"",
                "format": "mp3",
                "provider": "edge_tts"
            }

    async def _synthesize_with_edge_tts_async(self, text: str, voice_name: str, rate: float = 1.0) -> Dict[str, Any]:
        """Async Edge TTS synthesis"""
        try:
            # Rate is formatted as percentage: +10.00% for 10% faster, -10.00% for 10% slower
            rate_percent = f"{(rate - 1.0) * 100:+.0f}%"
            
            # Call async Edge TTS
            audio_data = await self._async_synthesize_edge_tts(text, voice_name, rate_percent)
            
            # Estimate duration
            duration = self._estimate_duration_from_text(text)
            
            logger.info(f"Edge TTS synthesis successful: {len(audio_data)} bytes, {duration:.2f}s")
            
            return {
                "audio_data": audio_data,
                "duration": duration,
                "format": "mp3"
            }
            
        except Exception as e:
            logger.error(f"Edge TTS generation failed: {str(e)}")
            raise


    def _synthesize_with_edge_tts(self, text: str, voice_name: str, rate: float = 1.0) -> Dict[str, Any]:
        """Synchronous Edge TTS synthesis for thread execution"""
        try:
            # Create communicate instance with voice and rate settings
            # Rate is formatted as percentage: +10.00% for 10% faster, -10.00% for 10% slower
            rate_percent = f"{(rate - 1.0) * 100:+.0f}%"
            
            # Subtle pitch adjustment makes it sound less artificial and more humanic
            pitch_adjust = "+2Hz"
            volume_adjust = "+10%"
            
            # Create event loop for async execution
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run async function with proper event loop handling
            audio_data = loop.run_until_complete(
                self._async_synthesize_edge_tts(text, voice_name, rate_percent, pitch_adjust, volume_adjust)
            )
            
            # Edge TTS returns MP3 - keep it as MP3 for compatibility
            # MP3 is more efficient and widely supported
            duration = self._estimate_duration_from_text(text)
            
            logger.info(f"Edge TTS synthesis successful: {len(audio_data)} bytes, {duration:.2f}s")
            
            return {
                "audio_data": audio_data,
                "duration": duration,
                "format": "mp3"
            }
            
        except Exception as e:
            logger.error(f"Edge TTS generation failed: {str(e)}")
            raise

    async def _async_synthesize_edge_tts(self, text: str, voice_name: str, rate_percent: str, pitch: str = "+0Hz", volume: str = "+0%") -> bytes:
        """Async Edge TTS synthesis"""
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice_name,
                rate=rate_percent,
                pitch=pitch,
                volume=volume
            )
            
            audio_buffer = BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])
            
            audio_buffer.seek(0)
            return audio_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Edge TTS async synthesis failed: {str(e)}")
            raise

    async def synthesize_speech_stream(
        self, 
        text: str, 
        language: str = "ta",
        voice: Optional[str] = None,
        emotion: str = "none"
    ):
        """
        Convert text to speech and yield audio byte chunks directly from Edge TTS
        """
        try:
            if voice:
                selected_voice = voice
            else:
                selected_voice = self.voice_mapping.get(language, self.voice_mapping["default"])
            
            rate = self.emotion_rate_map.get(emotion, 1.0)
            rate_percent = f"{(rate - 1.0) * 100:+.0f}%"
            
            pitch_adjust = "+2Hz"
            volume_adjust = "+10%"
            
            logger.info(f"Streaming with Edge TTS: voice={selected_voice}, emotion={emotion}, rate={rate}")
            
            communicate = edge_tts.Communicate(
                text=text,
                voice=selected_voice,
                rate=rate_percent,
                pitch=pitch_adjust,
                volume=volume_adjust
            )
            
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
                    
        except Exception as e:
            logger.error(f"Edge TTS synthesis streaming error: {str(e)}")
            raise

    def _estimate_duration_from_text(self, text: str) -> float:
        """Estimate duration based on text length"""
        # Average speaking rate: ~150 words per minute
        words = len(text.split())
        # Each word takes approximately 0.4 seconds
        duration = words * 0.4
        # Add minimum 0.5 seconds
        return max(0.5, duration)

    def get_available_voices(self, language: str = "ta") -> Dict[str, Any]:
        """Get list of available voices for language"""
        # Edge TTS available voices by language
        edge_voices = {
            "en": [
                {"name": "en-US-AriaNeural", "gender": "Female", "description": "US Female"},
            ],
            "ta": [
                {"name": "ta-IN-PallaviNeural", "gender": "Female", "description": "Tamil Pallavi (Default)"},
            ],
            "hi": [
                {"name": "hi-IN-SudhaNeural", "gender": "Female", "description": "Hindi Female"},
            ]
        }
        
        return {
            "provider": "edge_tts",
            "language": language,
            "default_language": "ta",
            "default_voice": "ta-IN-PallaviNeural",
            "voices": edge_voices.get(language, edge_voices.get("ta", []))
        }

    def validate_text_input(self, text: str) -> Dict[str, Any]:
        """Validate text input for TTS"""
        try:
            if not text or not text.strip():
                return {
                    "valid": False,
                    "error": "Empty text provided"
                }
            
            # Check text length (Edge TTS has limits)
            if len(text) > 10000:  # Edge TTS can handle longer text than Gemini
                return {
                    "valid": False,
                    "error": f"Text too long: {len(text)} characters (max: 10000)"
                }
            
            return {
                "valid": True,
                "length": len(text),
                "word_count": len(text.split()),
                "estimated_duration": self._estimate_duration_from_text(text)
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into complete sentences for streaming TTS"""
        if not text or not text.strip():
            return []
        
        # Handle common abbreviations to avoid false splits
        text = text.replace("Mr.", "Mr").replace("Dr.", "Dr").replace("Ms.", "Ms")
        text = text.replace("A.M.", "AM").replace("P.M.", "PM")
        text = text.replace("a.m.", "am").replace("p.m.", "pm")
        
        # Split by sentence-ending punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        clean_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 3:  # Avoid very short fragments
                # Ensure sentence ends with punctuation
                if not sentence[-1] in '.!?':
                    sentence += '.'
                clean_sentences.append(sentence)
        
        return clean_sentences
    
    async def synthesize_sentences_streaming(self, text: str, language: str = "ta", 
                                           voice: str = None, emotion: str = "none") -> List[Dict[str, Any]]:
        """Synthesize text as streaming sentence chunks with Edge TTS and Tamil Pallavi as default"""
        try:
            sentences = self.split_into_sentences(text)
            
            if not sentences:
                return [{
                    "success": False,
                    "error": "No valid sentences to synthesize",
                    "chunk_id": 0,
                    "text_chunk": "",
                    "audio_data": b""
                }]
            
            logger.info(f"TTS streaming {len(sentences)} sentences: {[s[:30]+'...' for s in sentences]}")
            
            results = []
            
            for i, sentence in enumerate(sentences):
                try:
                    # Synthesize each sentence with Edge TTS
                    result = await self.synthesize_speech(sentence, language, voice, emotion)
                    
                    if result["success"]:
                        results.append({
                            "success": True,
                            "chunk_id": i,
                            "total_chunks": len(sentences),
                            "text_chunk": sentence,
                            "audio_data": result["audio_data"],
                            "format": result["format"],
                            "size": result["size"],
                            "duration": result.get("duration", 0.0),
                            "voice": result.get("voice", "ta-IN-PallaviNeural"),
                            "is_final": (i == len(sentences) - 1)
                        })
                    else:
                        results.append({
                            "success": False,
                            "chunk_id": i,
                            "total_chunks": len(sentences),
                            "text_chunk": sentence,
                            "error": result.get("error", "TTS failed"),
                            "audio_data": b"",
                            "is_final": (i == len(sentences) - 1)
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing sentence {i+1}: {e}")
                    results.append({
                        "success": False,
                        "chunk_id": i,
                        "total_chunks": len(sentences),
                        "text_chunk": sentence,
                        "error": str(e),
                        "audio_data": b"",
                        "is_final": (i == len(sentences) - 1)
                    })
            
            logger.info(f"TTS streaming complete: {len(results)} chunks processed")
            return results
            
        except Exception as error:
            logger.error(f"TTS streaming error: {error}")
            return [{
                "success": False,
                "error": str(error),
                "chunk_id": 0,
                "text_chunk": text[:50] + "..." if len(text) > 50 else text,
                "audio_data": b""
            }]

# Global TTS processor instance
_tts_processor = None

def get_tts_processor() -> TTSProcessor:
    """Get global TTS processor instance"""
    global _tts_processor
    if _tts_processor is None:
        _tts_processor = TTSProcessor()
    return _tts_processor