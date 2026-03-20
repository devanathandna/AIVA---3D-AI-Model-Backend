"""
Groq Llama-4 Scout AI Agent - Clean single-pass language handling
Minimal, fast, no redundant regeneration
"""

import os
import json
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from groq import Groq
from rag_faiss.retriever import retrieve as query_knowledge_base

logger = logging.getLogger(__name__)

EMOTION_OPTIONS = {"Acknowledging", "Talking", "Talking2", "HeadNodYes"}
DEFAULT_EMOTION = "Talking"

# Language instructions - SINGLE PASS based on frontend selection
LANGUAGE_TEMPLATES = {
    "ta": "CRITICAL: You MUST respond entirely in pure native Tamil script (தமிழ் எழுத்துக்கள்). Do NOT use English letters or Tanglish.",
    "hi": "CRITICAL: You MUST respond entirely in pure native Hindi script (देवनागरी). Do NOT use English letters or Hinglish.",
    "en": "Respond in clear English only."
}

SYSTEM_PROMPT = """You are AIVA, helpful AI assistant for Sri Eshwar College students.

KNOWLEDGE BASE TOPICS:
- Hostel facilities, mess timings, accommodation options, room types, charges
- Academic programs, departments, courses, specializations, curriculum
- Campus facilities: library, labs, sports, health center, cafeteria
- Fee structure, scholarships, payment options, financial aid
- Admission process, eligibility, cutoff marks by category and department
- College policies, rules, procedures, important dates
- Student services, placement information, internships

LANGUAGE INSTRUCTION: {LANGUAGE_TEMPLATE}

RESPONSE FORMAT - STRICT JSON ONLY:
{{
    "response": "Your answer here with specific details from context",
    "emotion": "One of: Acknowledging, Talking, Talking2, HeadNodYes"
}}

RULES:
- Always respond in JSON format above
- Use provided context for accurate details
- Do not use symbols like ₹
- STRICT LENGTH RULE: Your 'response' text MUST be exactly between 200 and 400 characters long. Not more, not less!
- Never break JSON format
"""

def _normalize_emotion(emotion: Any) -> str:
    """Normalize emotion to supported avatar animations - minimal version."""
    if isinstance(emotion, list):
        for item in emotion:
            n = _normalize_emotion(item)
            if n in EMOTION_OPTIONS:
                return n
        return DEFAULT_EMOTION
    
    if not isinstance(emotion, str):
        return DEFAULT_EMOTION
    
    cleaned = emotion.strip().lower().replace('"', '').replace("'", '')
    
    mapping = {
        "acknowledging": "Acknowledging", "talking": "Talking", "talking2": "Talking2",
        "headnodyes": "HeadNodYes", "head_nod_yes": "HeadNodYes", "head nod yes": "HeadNodYes",
    }
    
    return mapping.get(cleaned, DEFAULT_EMOTION)


def _get_groq_client() -> Groq:
    """Get Groq client using rotating keys."""
    from config.settings import get_rotating_key
    
    api_key = get_rotating_key("GROQ_STT_API_KEY")
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
        
    if not api_key:
        raise Exception("GROQ_STT_API_KEY or GROQ_API_KEY not found")
        
    return Groq(api_key=api_key)


TRANSFORMER_PROMPT = """You are a Query Transformer for AIVA, the AI assistant of Sri Eshwar College.
Analyze the user input.
1. If it is ALREADY about Sri Eshwar College, education, or you (AIVA), just fix any obvious STT typos/jargon (e.g. 'Three Eshwar' -> 'Sri Eshwar') and output it as is.
2. If it is COMPLETELY UNRELATED (e.g. asking about sports cars, general knowledge, recipes, etc.), creatively ALTER or pivot the question so that it explicitly asks about how that topic relates to Sri Eshwar College (e.g., 'What is the fastest car?' -> 'Does Sri Eshwar college have a racing team or automotive club?'). Do NOT reject any queries.
RESPOND STRICTLY IN JSON format with a single key 'query'.
Example: {"query": "Does Sri Eshwar college teach culinary arts?"}
"""

async def sanitize_query(user_query: str) -> str:
    """Transform irrelevant queries into Sri Eshwar College related queries."""
    try:
        import asyncio
        client = _get_groq_client()
        
        def _run_transformer():
            return client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": TRANSFORMER_PROMPT},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.1,
                max_tokens=150,
                response_format={"type": "json_object"}
            )
            
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(loop.run_in_executor(None, _run_transformer), timeout=3.0)
        
        text = response.choices[0].message.content.strip()
        parsed = json.loads(text)
        new_query = parsed.get("query", user_query)
        logger.info(f"🔄 Transformer: '{user_query}' -> '{new_query}'")
        return new_query
    except Exception as e:
        logger.warning(f"Transformer failed: {e}")
        return user_query



async def get_agent_response(
    user_query: str,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """
    Single-pass LLM response. Language parameter from frontend.
    """
    try:
        language = kwargs.get("language")
        if not language and args:
            ctx = args[0]
            if isinstance(ctx, dict):
                language = ctx.get("language")
            elif isinstance(ctx, str):
                language = ctx

        # Validate language parameter from frontend
        language = language if language in {"ta", "hi", "en"} else "en"
        lang_instruction = LANGUAGE_TEMPLATES.get(language)
        
        # Transform user query
        user_query = await sanitize_query(user_query)
        
        # Get RAG context with timeout
        try:
            import asyncio
            rag_results = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, query_knowledge_base, user_query),
                timeout=6.0
            )
            context = rag_results.get("context", "") if isinstance(rag_results, dict) else ""
            context = context.strip() if context.strip() else "No specific context available."
        except Exception as e:
            logger.warning(f"RAG error: {e}")
            context = "Using general knowledge."
        
        # SINGLE LLM CALL - language embedded in prompt template
        client = _get_groq_client()
        
        # Dynamic prompt with language template substitution
        prompt = SYSTEM_PROMPT.format(LANGUAGE_TEMPLATE=lang_instruction) + f"""
CONTEXT FROM KNOWLEDGE BASE:
{context}

USER QUERY:
{user_query}

RESPOND IN JSON FORMAT:"""
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.65,
            max_tokens=250,
            top_p=0.95
        )
        
        text = response.choices[0].message.content.strip()
        
        # Clean JSON
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            # Fallback: extract response field
            if '"response"' in text:
                start = text.find('"response"') + 11
                end = text.find('"', start)
                parsed = {
                    "response": text[start:end] if end > start else "Check college website",
                    "emotion": DEFAULT_EMOTION
                }
            else:
                parsed = {"response": text[:150], "emotion": DEFAULT_EMOTION}
        
        response_text = parsed.get("response", "I couldn't process that.")
        emotion = _normalize_emotion(parsed.get("emotion", DEFAULT_EMOTION))
        
        logger.info(f"[{language}] {len(response_text)} chars, emotion: {emotion}")
        
        return {
            "response": response_text,
            "emotion": emotion,
            "language": language,
            "success": True
        }
        
    except Exception as error:
        logger.error(f"Agent error: {error}")
        return {
            "response": "Technical difficulty. Try again.",
            "emotion": DEFAULT_EMOTION,
            "language": language if 'language' in locals() else "en",
            "success": False,
            "error": str(error)
        }


async def get_agent_response_streaming(
    user_query: str,
    *args,
    **kwargs
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Streaming LLM response - same single-pass logic.
    """
    try:
        language = kwargs.get("language")
        if not language and args:
            ctx = args[0]
            if isinstance(ctx, dict):
                language = ctx.get("language")
            elif isinstance(ctx, str):
                language = ctx

        # Validate language
        language = language if language in {"ta", "hi", "en"} else "en"
        lang_instruction = LANGUAGE_TEMPLATES.get(language)
        
        # Transform user query
        user_query = await sanitize_query(user_query)
        
        # Get RAG context
        try:
            import asyncio
            rag_results = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, query_knowledge_base, user_query),
                timeout=6.0
            )
            context = rag_results.get("context", "") if isinstance(rag_results, dict) else ""
            context = context.strip() if context.strip() else "No specific context available."
        except Exception as e:
            logger.warning(f"RAG error: {e}")
            context = "Using general knowledge."
        
        client = _get_groq_client()
        
        # Dynamic prompt with language template substitution
        prompt = SYSTEM_PROMPT.format(LANGUAGE_TEMPLATE=lang_instruction) + f"""
CONTEXT FROM KNOWLEDGE BASE:
{context}

USER QUERY:
{user_query}

RESPOND IN JSON FORMAT:"""
        
        stream = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.65,
            max_tokens=250,
            top_p=0.95,
            stream=True
        )
        
        full_text = ""
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_text += token
                yield {
                    "type": "token",
                    "token": token,
                    "language": language
                }
        
        # Parse final response
        text = full_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            if '"response"' in text:
                start = text.find('"response"') + 11
                end = text.find('"', start)
                parsed = {
                    "response": text[start:end] if end > start else "Check college website",
                    "emotion": DEFAULT_EMOTION
                }
            else:
                parsed = {"response": text[:150], "emotion": DEFAULT_EMOTION}
        
        response_text = parsed.get("response", "Processing complete.")
        emotion = _normalize_emotion(parsed.get("emotion", DEFAULT_EMOTION))
        
        logger.info(f"[{language}] Streaming complete: {len(response_text)} chars, emotion: {emotion}")
        
        yield {
            "type": "complete",
            "response": response_text,
            "emotion": emotion,
            "language": language,
            "full_text": full_text
        }
        
    except Exception as error:
        logger.error(f"Streaming error: {error}")
        yield {
            "type": "error",
            "error": str(error),
            "response": "Technical difficulty.",
            "emotion": DEFAULT_EMOTION,
            "language": language if 'language' in locals() else "en"
        }
        
    except Exception as error:
        logger.error(f"Streaming error: {error}")
        yield {
            "type": "error",
            "error": str(error),
            "response": "Technical difficulty.",
            "emotion": DEFAULT_EMOTION,
            "language": language if 'language' in locals() else "en"
        }