"""
Groq Llama-4 Scout AI Agent (Replacing Gemini)
Handles conversational responses with RAG integration
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from groq import Groq

from rag_faiss.retriever import retrieve as query_knowledge_base

logger = logging.getLogger(__name__)

# System prompt for Groq Llama agent
SYSTEM_PROMPT = """You are a helpful AI assistant for Sri Eshwar College students. You provide accurate, specific answers using the provided context about:

- Hostel facilities, mess timings, and accommodation
- Academic programs, departments, and courses  
- Campus facilities and student services
- Fee structure and admission information
- College policies and procedures and marks
- Cutoff marks for different departments and categories
- General information about Sri Eshwar College

IMPORTANT: When context is provided, use it to give specific, detailed answers with exact numbers, marks, or information. Don't give vague responses when you have specific data.

RESPONSE FORMAT: Always respond in JSON format:
{
    "response": "Your helpful answer with specific details from context",
    "emotion": "none" or "happy" or "sad"
}

GUIDELINES:
- Be conversational and friendly
- Use proper Indian English  
- When you have specific context, provide exact details (numbers, marks, etc.)
- If asking about cutoffs/marks, give the exact values from context
- If you don't know something, say so honestly
- For Tamil queries, respond in Tanglish"""


def _get_groq_client() -> Groq:
    """Get Groq client for Llama agent"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise Exception("GROQ_API_KEY not found in environment")
    return Groq(api_key=api_key)


async def get_agent_response(user_query: str, language_context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Get response from Groq Llama-4 Scout agent with RAG integration
    
    Args:
        user_query: User's question
        language_context: Optional language detection info
        
    Returns:
        Response with text and emotion
    """
    try:
        # Determine language instruction
        if language_context and language_context.get("is_tamil", False):
            language_instruction = "User asked in Tamil. Respond in English with some Tamil phrases mixed in naturally."
        else:
            language_instruction = "User asked in English. Respond in clear English."
        
        # Get relevant context from knowledge base (with timeout)
        try:
            import asyncio
            # Add timeout to RAG retrieval to prevent delays
            rag_results = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, query_knowledge_base, user_query),
                timeout=2.0  # Maximum 2 seconds for RAG
            )
            
            # Extract context properly from RAG results dictionary
            if rag_results and isinstance(rag_results, dict):
                context = rag_results.get("context", "")
                sources = rag_results.get("sources", [])
                logger.info(f"RAG retrieved {len(sources)} sources: {sources}")
                context = context if context else "No specific context found."
            else:
                context = "No specific context found."
                logger.warning(f"RAG returned unexpected format: {type(rag_results)}")
                
        except asyncio.TimeoutError:
            logger.warning(f"RAG retrieval timeout for query: {user_query}")
            context = "Knowledge base timeout - using general knowledge."
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            context = "Knowledge base temporarily unavailable."
        
        # Build prompt
        prompt = f"""{SYSTEM_PROMPT}

LANGUAGE INSTRUCTION: {language_instruction}

Context from knowledge base: {context}

User Question: {user_query}

Response (in JSON format):"""

        # Debug logging
        logger.info(f"Context length: {len(context)} chars")
        logger.debug(f"Full context: {context[:200]}...")
        logger.debug(f"Prompt length: {len(prompt)} chars")

        # Get Groq Llama client
        client = _get_groq_client()
        
        # Generate response with optimized settings for speed
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Fastest Groq model for immediate responses
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Lower temperature for faster, more focused responses
            max_tokens=300,   # Reduced tokens for faster generation
            top_p=0.9,        # Slightly lower top_p for speed
            stream=False
        )
        
        text = response.choices[0].message.content.strip()
        
        logger.info(f"Groq Llama raw response: '{text[:100]}...'")
        
        # Clean up response format
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        try:
            # Parse JSON response
            parsed = json.loads(text)
            
            # Validate required keys
            if "response" not in parsed or "emotion" not in parsed:
                raise json.JSONDecodeError("Missing required keys", text, 0)
                
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON from Groq Llama (length={len(text)}): {e}")
            logger.debug(f"Raw response: '{text[:100]}...'")
            
            # Enhanced error recovery
            partial_response = ""
            
            if '"response"' in text:
                try:
                    # Extract response content
                    start_patterns = ['"response": "', '"response":"', ': "']
                    for pattern in start_patterns:
                        start_idx = text.find(pattern)
                        if start_idx >= 0:
                            start_idx += len(pattern)
                            remaining = text[start_idx:]
                            
                            # Find natural end points
                            end_patterns = ['",', '"', '\\n', "'}"]
                            min_end = len(remaining)
                            
                            for end_pattern in end_patterns:
                                end_pos = remaining.find(end_pattern)
                                if end_pos >= 0 and end_pos < min_end:
                                    min_end = end_pos
                            
                            if min_end < len(remaining):
                                partial_response = remaining[:min_end].strip()
                                break
                    
                    # Clean extracted response
                    if partial_response:
                        partial_response = partial_response.replace('\\"', '"')
                        partial_response = partial_response.replace('\\n', ' ')
                        partial_response = partial_response.strip()
                        
                except Exception as extraction_error:
                    logger.debug(f"Response extraction failed: {extraction_error}")
            
            # Final fallback
            if not partial_response or len(partial_response.strip()) < 3:
                partial_response = "I apologize, but I'm having trouble processing your request right now."
            
            parsed = {
                "response": partial_response,
                "emotion": "none"
            }
            
            logger.info(f"Recovered Groq response: '{partial_response[:50]}...'")
        
        # Ensure required keys exist with valid values
        if "response" not in parsed:
            parsed["response"] = text if text else "I don't have that information."
        if "emotion" not in parsed or parsed["emotion"] not in ("happy", "sad", "none"):
            parsed["emotion"] = "none"
        
        logger.info(f"Groq Llama response: '{parsed['response'][:50]}...' (emotion: {parsed['emotion']})")
        
        return parsed
        
    except Exception as error:
        logger.error(f"Groq Llama agent error: {error}")
        return {
            "response": "I apologize, but I'm experiencing technical difficulties. Please try again.",
            "emotion": "sad"
        }