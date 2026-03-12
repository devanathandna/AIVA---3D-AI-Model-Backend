"""Speech-to-Text module using Groq."""

import asyncio
import logging
from typing import Any, Dict
import io

from groq import Groq

from config.api_keys import get_groq_stt_key
from .stt_post_processor import get_stt_post_processor

logger = logging.getLogger(__name__)


class STTProcessor:
    _SUPPORTED_LANGUAGES = {"en", "ta"}

    def __init__(self):
        """Initialize the STT processor."""
        self._client = None

    def _get_client(self) -> Groq:
        """Create or reuse a Groq client bound to the configured API key."""
        api_key = get_groq_stt_key()
        if not api_key:
            raise Exception("No Groq API key available")

        if self._client is None:
            self._client = Groq(api_key=api_key)
        return self._client

    async def transcribe_audio(self, audio_data: bytes, language: str = "auto") -> Dict[str, Any]:
        """Transcribe audio - translate Tamil to English, force other languages to English."""
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, self._transcribe_bytes, audio_data, language)
            
            return {
                "success": True,
                "text": result["text"].strip(),  # Always English text (Tamil translated to English)
                "language": result["language"],  # Always "en"
                "confidence": result.get("confidence", 0.0),
                "provider": "groq",
                "is_tamil": result.get("is_tamil", False),  # Tamil input detection flag
                "detected_language": result.get("detected_language", "unknown"),
            }
        except Exception as error:
            logger.error(f"Groq STT transcription error: {error}")
            return {
                "success": False,
                "error": str(error),
                "text": "",
                "language": "unknown",
                "confidence": 0.0,
                "provider": "groq",
                "is_tamil": False,
            }

    def _normalize_language(self, language: str) -> str:
        """Normalize app language aliases to the codes expected by downstream services."""
        if not language:
            return "en"

        normalized = language.strip().lower().replace("_", "-")
        aliases = {
            "en": "en",
            "en-us": "en",
            "en-in": "en",
            "english": "en",
            "ta": "ta",
            "ta-in": "ta",
            "tamil": "ta",
        }
        normalized = aliases.get(normalized, normalized)
        if normalized in self._SUPPORTED_LANGUAGES:
            return normalized
        return "en"

    def _transcribe_bytes(self, audio_data: bytes, language: str = "en") -> Dict[str, Any]:
        """Force English transcription first, then check for Tamil and re-transcribe if needed."""
        try:
            client = self._get_client()
            
            # Create a file-like object from audio bytes
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"
            
            # Step 1: Always force English transcription first (avoid auto-detection issues)
            logger.info("Force transcribing in English (no auto-detection)...")
            transcript_response = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3-turbo",
                response_format="verbose_json",
                language="en",  # Force English - no auto detection to avoid Hindi/other languages
                temperature=0.0
            )
            
            english_transcript = transcript_response.text or ""
            logger.info(f"English forced transcription: '{english_transcript[:50]}...'")
            
            # Step 2: Check for Tamil indicators in the English transcription
            # Common Tamil words that appear even in English transcription
            tamil_word_patterns = [
                'saapadu', 'saapatu', 'eppadi', 'epadi', 'irukkum', 'irukum', 'iruku',
                'enna', 'ena', 'vandhu', 'vanthu', 'podu', 'poidu', 'poitu', 
                'solluga', 'soluga', 'keluga', 'kekura', 'pannu', 'panu',
                'hostel', 'college', 'school', 'veetla', 'vetla', 'anga', 'enga'
            ]
            
            english_lower = english_transcript.lower().replace("'", "").replace(",", " ")
            has_tamil_words = any(pattern in english_lower for pattern in tamil_word_patterns)
            has_tamil_chars = any('\u0b80' <= char <= '\u0bff' for char in english_transcript)
            
            # Step 3: If Tamil indicators found, re-transcribe in Tamil
            if has_tamil_words or has_tamil_chars:
                logger.info("Tamil patterns detected, re-transcribing with Tamil language...")
                audio_file.seek(0)  # Reset file pointer for re-transcription
                
                tamil_transcript_response = client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3-turbo",
                    response_format="verbose_json",
                    language="ta",  # Force Tamil transcription
                    temperature=0.0
                )
                
                tamil_transcript = tamil_transcript_response.text or ""
                logger.info(f"Tamil transcription result: '{tamil_transcript[:50]}...'")
                
                # Use Tamil transcription if it's different and non-empty
                if tamil_transcript.strip() and tamil_transcript != english_transcript:
                    final_transcript = tamil_transcript
                    final_language = "ta"
                    is_tamil_input = True
                    confidence = 0.90
                    logger.info("Using Tamil transcription")
                else:
                    # Fall back to English if Tamil transcription failed
                    final_transcript = english_transcript
                    final_language = "en"
                    is_tamil_input = True  # Still Tamil input, but keeping English transcription
                    confidence = 0.85
                    logger.info("Falling back to English transcription for Tamil input")
            else:
                # Pure English - use English transcription
                final_transcript = english_transcript
                final_language = "en"
                is_tamil_input = False
                confidence = 0.95
                logger.info("Using English transcription for English input")
            
            logger.info(f"Final STT Result - Language: {final_language}, Tamil Input: {is_tamil_input}, Text: '{final_transcript[:50]}...'")
            
            return {
                "text": final_transcript,
                "confidence": confidence,
                "language": final_language,  # "ta" or "en" 
                "is_tamil": is_tamil_input,  # Flag indicating Tamil was spoken
                "detected_language": final_language,
            }
            
        except Exception as error:
            logger.error(f"Groq transcription failed: {error}")
            raise

    async def validate_audio_format(self, audio_data: bytes) -> Dict[str, Any]:
        """Validate whether the input looks like supported audio data."""
        try:
            if len(audio_data) < 1000:
                return {
                    "valid": False,
                    "error": "Audio data too small",
                }

            headers = {
                b"RIFF": "wav",
                b"\xff\xfb": "mp3",
                b"\xff\xf3": "mp3",
                b"\xff\xf2": "mp3",
                b"OggS": "ogg",
                b"fLaC": "flac",
                b"ftypM4A": "m4a",
            }

            audio_format = "unknown"
            for header, fmt in headers.items():
                if audio_data.startswith(header):
                    audio_format = fmt
                    break

            return {
                "valid": True,
                "format": audio_format,
                "size": len(audio_data),
            }
        except Exception as error:
            return {
                "valid": False,
                "error": str(error),
            }


_stt_processor = None


def get_stt_processor() -> STTProcessor:
    """Get the global STT processor instance."""
    global _stt_processor
    if _stt_processor is None:
        _stt_processor = STTProcessor()
    return _stt_processor