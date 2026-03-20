"""Speech-to-Text module using Groq."""

import asyncio
import logging
from typing import Any, Dict
import io

from groq import Groq

from config.api_keys import get_groq_stt_key

logger = logging.getLogger(__name__)


class STTProcessor:
    _SUPPORTED_LANGUAGES = {"en", "ta", "hi"}

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

    async def transcribe_audio(self, audio_data: bytes, language: str = "en") -> Dict[str, Any]:
        """Transcribe audio using a single STT API call based on preferred language."""
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, self._transcribe_bytes, audio_data, language)
            
            return {
                "success": True,
                "text": result["text"].strip(),
                "language": result["language"],
                "confidence": result.get("confidence", 0.0),
                "provider": "groq",
                "is_tamil": result.get("is_tamil", False),
                "is_hindi": result.get("is_hindi", False),
                "detected_language": result.get("detected_language", "en"),
                "requested_language": result.get("requested_language", "en"),
            }
        except Exception as error:
            logger.error(f"Groq STT transcription error: {error}")
            return {
                "success": False,
                "error": str(error),
                "text": "",
                "language": "en",
                "confidence": 0.0,
                "provider": "groq",
                "is_tamil": False,
                "is_hindi": False,
            }

    def _normalize_language(self, language: str) -> str:
        """Normalize app language aliases to the codes expected by downstream services."""
        if not language:
            return "en"

        normalized = language.strip().lower()
        if normalized in self._SUPPORTED_LANGUAGES or normalized == "auto":
            return normalized
        return "en"

    def _transcribe_bytes(self, audio_data: bytes, language: str = "auto") -> Dict[str, Any]:
        """Transcribe audio in a single pass with optional language targeting."""
        try:
            client = self._get_client()
            normalized_language = self._normalize_language(language)
            
            # Create a file-like object from audio bytes
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"

            request_kwargs = {
                "file": audio_file,
                "model": "whisper-large-v3-turbo",
                "response_format": "verbose_json",
                "temperature": 0.0,
            }

            if normalized_language != "auto":
                request_kwargs["language"] = normalized_language
                logger.info(f"Transcribing with user-selected language='{normalized_language}'")
            else:
                logger.info("Transcribing with auto language detection")

            transcript_response = client.audio.transcriptions.create(**request_kwargs)

            transcript_text = transcript_response.text or ""
            detected_language = getattr(transcript_response, "language", None) or normalized_language
            if detected_language == "auto":
                detected_language = "en"

            is_tamil_input = detected_language == "ta"
            is_hindi_input = detected_language == "hi"

            logger.info(
                "Final STT Result - requested=%s detected=%s tamil=%s hindi=%s text='%s...'",
                normalized_language,
                detected_language,
                is_tamil_input,
                is_hindi_input,
                transcript_text[:50],
            )
            
            return {
                "text": transcript_text,
                "confidence": 0.92,
                "language": detected_language,
                "is_tamil": is_tamil_input,
                "is_hindi": is_hindi_input,
                "detected_language": detected_language,
                "requested_language": normalized_language,
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