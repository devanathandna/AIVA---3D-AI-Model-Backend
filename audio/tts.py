"""
Text-to-Speech module using Gemini TTS with API key rotation
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

from google import genai
from google.genai import types
from config.api_keys import get_gemini_tts_key

logger = logging.getLogger(__name__)

class TTSProcessor:
    def __init__(self):
        """
        Initialize TTS processor with Gemini TTS
        """
        self._client = None
        
        # Gemini TTS voice mapping - using Pulcherrima for all
        self.voice_mapping = {
            ("en", "none"): "Pulcherrima",
            ("en", "happy"): "Pulcherrima", 
            ("en", "sad"): "Pulcherrima",
            ("ta", "none"): "Pulcherrima",
            ("ta", "happy"): "Pulcherrima",
            ("ta", "sad"): "Pulcherrima"
        }
        
    def _get_client(self):
        """Get Gemini client with rotated API key"""
        api_key = get_gemini_tts_key()
        if not api_key:
            raise Exception("No Gemini TTS API key available")
        
        return genai.Client(api_key=api_key)
        
    async def synthesize_speech(
        self, 
        text: str, 
        language: str = "en", 
        voice: Optional[str] = None,
        emotion: str = "none"
    ) -> Dict[str, Any]:
        """
        Convert text to speech using Gemini TTS
        
        Args:
            text: Text to synthesize
            language: Language code ("en", "ta", etc.)
            voice: Specific voice name (optional)
            emotion: Emotion for speech ("happy", "sad", "none")
            
        Returns:
            Dict with audio data and metadata
        """
        try:
            # Get Gemini client
            client = self._get_client()
            
            # Select voice based on language and emotion
            selected_voice = voice or self.voice_mapping.get((language, emotion), "Pulcherrima")
            
            logger.info(f"Synthesizing with Gemini TTS: voice={selected_voice}, emotion={emotion}")
            
            # Run synthesis in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._synthesize_with_gemini,
                text,
                selected_voice
            )
            
            return {
                "success": True,
                "audio_data": result["audio_data"],
                "format": "wav",
                "voice": selected_voice,
                "language": language,
                "duration": result["duration"],
                "size": len(result["audio_data"]),
                "provider": "gemini_tts"
            }
            
        except Exception as e:
            logger.error(f"Gemini TTS synthesis error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "audio_data": b"",
                "format": "wav",
                "provider": "gemini_tts"
            }

    def _synthesize_with_gemini(self, text: str, voice_name: str) -> Dict[str, Any]:
        """Synchronous Gemini TTS synthesis for thread execution"""
        try:
            # Get client with API key
            client = self._get_client()
            
            # Generate content with TTS configuration
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name
                            )
                        )
                    ),
                ),
            )
            
            # Extract raw PCM bytes with proper error handling
            if not response.candidates or len(response.candidates) == 0:
                raise Exception("No candidates in TTS response")
            
            candidate = response.candidates[0]
            if not candidate or not candidate.content:
                raise Exception("No content in TTS response candidate")
            
            if not candidate.content.parts or len(candidate.content.parts) == 0:
                raise Exception("No parts in TTS response content")
                
            part = candidate.content.parts[0]
            if not part or not hasattr(part, 'inline_data') or not part.inline_data:
                raise Exception("No inline_data in TTS response part")
            
            audio_bytes = part.inline_data.data
            if not audio_bytes:
                raise Exception("No audio data in TTS response")
            
            # Convert PCM to proper WAV format
            wav_data = self._pcm_to_wav(audio_bytes)
            
            # Estimate duration
            duration = self._estimate_duration_from_audio(audio_bytes)
            
            logger.info(f"Gemini TTS synthesis successful: {len(wav_data)} bytes, {duration:.2f}s")
            
            return {
                "audio_data": wav_data,
                "duration": duration
            }
            
        except Exception as e:
            logger.error(f"Gemini TTS generation failed: {str(e)}")
            raise

    def _pcm_to_wav(self, pcm_data: bytes) -> bytes:
        """Convert raw PCM data to WAV format"""
        try:
            # Create WAV file in memory
            wav_buffer = BytesIO()
            
            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(1)      # Mono
                wf.setsampwidth(2)      # 16-bit
                wf.setframerate(24000)  # 24kHz sample rate (Gemini TTS default)
                wf.writeframes(pcm_data)
            
            wav_data = wav_buffer.getvalue()
            wav_buffer.close()
            
            return wav_data
            
        except Exception as e:
            logger.error(f"PCM to WAV conversion failed: {str(e)}")
            # Return raw PCM data as fallback
            return pcm_data

    def _estimate_duration_from_audio(self, audio_data: bytes) -> float:
        """Estimate audio duration from PCM data"""
        try:
            # For 16-bit mono at 24kHz: 2 bytes per sample, 24000 samples per second
            bytes_per_second = 24000 * 2
            duration = len(audio_data) / bytes_per_second
            return max(0.1, duration)  # Minimum 0.1 seconds
        except:
            # Fallback estimation based on text length
            return len(audio_data) / 48000  # Rough estimate

    def _estimate_duration(self, text: str) -> float:
        """Estimate audio duration based on text length"""
        # Rough estimate: ~150 words per minute
        words = len(text.split())
        return max(0.5, (words / 150) * 60)

    def get_available_voices(self, language: str = "en") -> Dict[str, Any]:
        """Get list of available voices for language"""
        # Gemini TTS available voices - using only Pulcherrima
        gemini_voices = {
            "en": [
                {"name": "Pulcherrima", "gender": "Female", "description": "Cheerful, expressive"}
            ],
            "ta": [
                {"name": "Pulcherrima", "gender": "Female", "description": "Expressive (English fallback)"}
            ]
        }
        
        return {
            "provider": "gemini_tts",
            "language": language,
            "voices": gemini_voices.get(language, gemini_voices["en"])
        }

    def validate_text_input(self, text: str) -> Dict[str, Any]:
        """Validate text input for TTS"""
        try:
            if not text or not text.strip():
                return {
                    "valid": False,
                    "error": "Empty text provided"
                }
            
            # Check text length (Gemini TTS has limits)
            if len(text) > 5000:  # Conservative limit
                return {
                    "valid": False,
                    "error": f"Text too long: {len(text)} characters (max: 5000)"
                }
            
            return {
                "valid": True,
                "length": len(text),
                "word_count": len(text.split()),
                "estimated_duration": self._estimate_duration(text)
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
    
    async def synthesize_sentences_streaming(self, text: str, language: str = "en", 
                                           voice: str = None, emotion: str = "none") -> List[Dict[str, Any]]:
        """Synthesize text as streaming sentence chunks"""
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
                    # Synthesize each sentence
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
                            "is_final": (i == len(sentences) - 1)
                        })
                        
                        logger.info(f"TTS chunk {i+1}/{len(sentences)} complete: '{sentence[:40]}...'")
                    else:
                        logger.error(f"TTS failed for sentence {i+1}: {result.get('error')}")
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