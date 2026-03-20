import json
import traceback
import base64
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from agent.groq_llama_agent import get_agent_response, get_agent_response_streaming  # Changed to Groq Llama
from audio.manager import get_audio_manager

router = APIRouter()
audio_manager = get_audio_manager()


def normalize_response_style(style: str, fallback_language: str = "en") -> str:
    """Normalize response style from frontend settings or infer from language."""
    if style:
        normalized = style.strip().lower()
        aliases = {
            "en": "english",
            "english": "english",
            "ta": "tanglish",
            "tamil": "tanglish",
            "tanglish": "tanglish",
            "hi": "hindi-english",
            "hindi": "hindi-english",
            "hinglish": "hindi-english",
            "hindi-english": "hindi-english",
        }
        return aliases.get(normalized, "english")

    lang = (fallback_language or "en").strip().lower()
    if lang == "ta":
        return "tanglish"
    if lang == "hi":
        return "hindi-english"
    return "english"


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    print("[WS] Client connected")
    try:
        while True:
            # Try to receive either text or binary data
            try:
                data = await ws.receive_text()
                await handle_text_message(ws, data)
            except:
                # If text receive fails, try binary
                try:
                    binary_data = await ws.receive_bytes()
                    await handle_binary_message(ws, binary_data)
                except:
                    # If both fail, try JSON message
                    message = await ws.receive_json()
                    await handle_json_message(ws, message)

    except WebSocketDisconnect:
        print("[WS] Client disconnected")
    except Exception as e:
        traceback.print_exc()
        try:
            await ws.send_json({
                "type": "error",
                "response": f"Server error: {str(e)}", 
                "emotion": "sad"
            })
        except Exception:
            pass


async def handle_text_message(ws: WebSocket, data: str):
    """Handle plain text messages (legacy support)"""
    try:
        payload = json.loads(data)
        await handle_json_message(ws, payload)
    except json.JSONDecodeError:
        # Plain text query
        query = data.strip()
        if not query:
            await ws.send_json({
                "type": "text_response",
                "response": "Please send a valid query.", 
                "emotion": "none"
            })
            return

        print(f"[WS] Text Query: {query}")
        result = await get_agent_response(query)
        result["type"] = "text_response"
        print(f"[WS] Text Response: {result}")
        await ws.send_json(result)


async def handle_json_message(ws: WebSocket, payload: dict):
    """Handle structured JSON messages"""
    message_type = payload.get("type", "text")
    
    # Debug: Print what the frontend sent (hiding huge base64 strings)
    debug_payload = {k: f"<base64 data {len(v)} chars>" if k in ("audio_data", "audio") and isinstance(v, str) and len(v) > 50 else v for k, v in payload.items()}
    print(f"\n[WS FRONTEND IN] << {message_type.upper()}: {debug_payload}")
    
    if message_type == "text":
        await handle_text_query(ws, payload)
    elif message_type == "audio":
        await handle_audio_query(ws, payload)
    elif message_type == "audio_base64":
        await handle_audio_base64_query(ws, payload)
    elif message_type == "get_audio_info":
        await handle_audio_info_request(ws)
    elif message_type == "get_voices":
        await handle_voices_request(ws, payload)
    elif message_type == "audio_base64_streaming":
        await handle_audio_base64_streaming(ws, payload)
    elif message_type == "audio_base64_streaming_tokens":
        # NEW: Token-by-token streaming for audio
        await handle_audio_base64_streaming_with_tokens(ws, payload)
    elif message_type == "audio_streaming":
        # Alternative endpoint for non-base64 streaming
        await handle_audio_streaming(ws, payload)
    elif message_type == "audio_tts_streaming":
        # TTS-only streaming for text input
        await handle_tts_streaming(ws, payload)
    elif message_type == "test_immediate":
        # Test immediate response - bypass all processing
        await handle_test_immediate(ws, payload)
    else:
        await ws.send_json({
            "type": "error",
            "response": f"Unknown message type: {message_type}",
            "emotion": "sad"
        })


async def handle_text_query(ws: WebSocket, payload: dict):
    """Handle text-based queries"""
    query = payload.get("query", "").strip()
    if not query:
        await ws.send_json({
            "type": "text_response",
            "response": "Please send a valid query.", 
            "emotion": "none"
        })
        return

    print(f"[WS] JSON Text Query: {query}")
    
    # Check if TTS is requested
    enable_tts = payload.get("enable_tts", False)
    tts_language = payload.get("tts_language", "en")
    input_language = payload.get("language", payload.get("input_language", "en"))
    response_style = normalize_response_style(
        payload.get("response_style", ""),
        input_language,
    )
    
    # Get agent response
    result = await get_agent_response(query, language=input_language, response_style=response_style)
    print(f"[WS] Emotion: {result.get('emotion', 'none')}")
    
    if enable_tts and result.get("response"):
        # First send the text response immediately so UI updates
        await ws.send_json({
            "type": "text_response",
            "response": result["response"],
            "emotion": result.get("emotion", "none")
        })
        
        # Then stream the audio directly from Edge TTS to avoid 20-second blocking timeouts
        try:
            print("[WS] 🚀 Starting Edge TTS Binary Stream for Text Query...")
            await ws.send_json({
                "type": "audio_stream_start"
            })
            
            tts_processor = audio_manager.tts_processor
            chunk_count = 0
            async for audio_chunk in tts_processor.synthesize_speech_stream(
                text=result["response"],
                language=tts_language,
                emotion=result.get("emotion", "none")
            ):
                await ws.send_bytes(audio_chunk)
                chunk_count += 1
                
            await ws.send_json({
                "type": "audio_stream_end"
            })
            print(f"[WS] 🎉 Edge TTS Binary Stream generated {chunk_count} chunks successfully!")
        except Exception as tts_error:
            print(f"[WS] Edge TTS streaming error: {tts_error}")
            await ws.send_json({
                "type": "error",
                "response": "TTS backend failed",
                "emotion": "sad"
            })
    else:
        # Just text response
        result["type"] = "text_response"
        print(f"[WS] JSON Text Response: {result.get('response', '')[:100]}...")
        await ws.send_json(result)


async def handle_binary_message(ws: WebSocket, binary_data: bytes):
    """Handle raw binary audio data"""
    print(f"[WS] Received binary audio: {len(binary_data)} bytes")
    
    # Process audio through complete conversation flow
    conversation_result = await audio_manager.process_audio_conversation(
        binary_data,
        get_agent_response,
        input_language="en",
        output_language="en",
        response_style="english",
    )
    
    if conversation_result["success"]:
        # Encode response audio to base64
        audio_base64 = base64.b64encode(conversation_result["audio_data"]).decode('utf-8')
        
        response = {
            "type": "audio_conversation_response",
            "success": True,
            "input_text": conversation_result["input_text"],
            "response_text": conversation_result["response_text"],
            "emotion": conversation_result["response_emotion"],
            "audio_data": audio_base64,
            "audio_format": conversation_result["audio_format"],
            "audio_duration": conversation_result["audio_duration"],
            "stt_confidence": conversation_result["stt_confidence"]
        }
    else:
        response = {
            "type": "audio_conversation_response", 
            "success": False,
            "error": conversation_result["error"],
            "input_text": conversation_result.get("input_text", ""),
            "response_text": "",
            "audio_data": "",
            "stt_confidence": conversation_result.get("stt_confidence", 0.0)
        }
    
    print(f"[WS] Audio Conversation Response: {response.get('success', False)}")
    await ws.send_json(response)


async def handle_audio_base64_query(ws: WebSocket, payload: dict):
    """Handle base64 encoded audio data"""
    try:
        audio_base64 = payload.get("audio_data", "")
        if not audio_base64:
            await ws.send_json({
                "type": "error",
                "response": "No audio data provided",
                "emotion": "sad"
            })
            return
        
        # Decode base64 audio
        audio_data = base64.b64decode(audio_base64)
        
        # Get processing options
        input_language = payload.get("language", payload.get("input_language", "auto"))
        output_language = payload.get("output_language", "en")
        response_style = normalize_response_style(payload.get("response_style", ""), input_language)
        
        print(f"[WS] Received base64 audio: {len(audio_data)} bytes")
        
        # Process through conversation flow
        conversation_result = await audio_manager.process_audio_conversation(
            audio_data,
            get_agent_response,
            input_language=input_language,
            output_language=output_language,
            response_style=response_style,
        )
        
        if conversation_result["success"]:
            # Encode response audio to base64
            response_audio_base64 = base64.b64encode(conversation_result["audio_data"]).decode('utf-8')
            
            response = {
                "type": "audio_conversation_response",
                "success": True,
                "input_text": conversation_result["input_text"],
                "input_language": conversation_result["input_language"],
                "response_style": conversation_result.get("response_style", response_style),
                "response_text": conversation_result["response_text"],
                "emotion": conversation_result["response_emotion"],
                "audio_data": response_audio_base64,
                "audio_format": conversation_result["audio_format"],
                "audio_duration": conversation_result["audio_duration"],
                "stt_confidence": conversation_result["stt_confidence"]
            }
        else:
            response = {
                "type": "audio_conversation_response",
                "success": False,
                "error": conversation_result["error"],
                "input_text": conversation_result.get("input_text", ""),
                "response_text": "",
                "audio_data": "",
                "stt_confidence": conversation_result.get("stt_confidence", 0.0)
            }
        
        print(f"[WS] Base64 Audio Response: {response.get('success', False)}")
        await ws.send_json(response)
        
    except Exception as e:
        await ws.send_json({
            "type": "error",
            "response": f"Audio processing error: {str(e)}",
            "emotion": "sad"
        })


async def handle_audio_query(ws: WebSocket, payload: dict):
    """Handle non-base64 audio payloads by delegating to the base64 path."""
    await handle_audio_base64_query(ws, payload)


async def handle_audio_streaming(ws: WebSocket, payload: dict):
    """Handle raw audio data with streaming response"""
    try:
        audio_data = payload.get("audio_data", b"")
        if not audio_data:
            await ws.send_json({
                "type": "error", 
                "response": "No audio data provided",
                "emotion": "sad"
            })
            return
            
        # Process with streaming approach
        input_language = payload.get("input_language", "auto")
        output_language = payload.get("output_language", "en")
        response_style = payload.get("response_style", "")
        
        # Use the same streaming logic as base64 handler
        await handle_audio_base64_streaming(ws, {
            "audio_data": base64.b64encode(audio_data).decode('utf-8'),
            "input_language": input_language,
            "output_language": output_language,
            "response_style": response_style,
        })
        
    except Exception as e:
        await ws.send_json({
            "type": "streaming_error",
            "error": f"Audio streaming error: {str(e)}",
            "stage": "general"
        })


async def handle_audio_base64_streaming(ws: WebSocket, payload: dict):
    """Handle base64 audio with streaming response (text first, audio later)"""
    try:
        audio_base64 = payload.get("audio_data", "")
        if not audio_base64:
            await ws.send_json({
                "type": "error",
                "response": "No audio data provided",
                "emotion": "sad"
            })
            return
        
        # Decode base64 audio
        audio_data = base64.b64decode(audio_base64)
        input_language = payload.get("language", payload.get("input_language", "auto"))
        output_language = payload.get("output_language", "en")
        response_style = normalize_response_style(payload.get("response_style", ""), input_language)
        
        print(f"[WS] Streaming audio: {len(audio_data)} bytes")
        
        # Get audio manager
        audio_manager = get_audio_manager()
        
        # Step 1: STT Processing - Get text quickly
        stt_start = time.time()
        stt_result = await audio_manager.process_audio_to_text(audio_data, input_language)
        stt_duration = (time.time() - stt_start) * 1000
        print(f"[WS] ⏱️ STT took {stt_duration:.1f}ms")
        
        if not stt_result["success"]:
            await ws.send_json({
                "type": "streaming_error", 
                "error": stt_result.get("error", "STT failed"),
                "stage": "stt"
            })
            return
            
        input_text = stt_result["text"]
        detected_language = stt_result.get("language", "unknown")
        is_tamil = stt_result.get("is_tamil", False)
        is_hindi = stt_result.get("is_hindi", False)
        
        # Create language context
        language_context = {
            "language": detected_language,
            "is_tamil": is_tamil,
            "is_hindi": is_hindi,
            "confidence": stt_result["confidence"]
        }
        
        print(f"[WS] STT Complete: '{input_text}' (detected: {detected_language})")
        
        # Step 2: Send immediate acknowledgment that we're processing
        await ws.send_json({
            "type": "streaming_status", 
            "stage": "processing",
            "input_text": input_text,
            "message": "Processing your query..."
        })
        
        # Step 3: Agent Processing - Get response text
        agent_start = time.time()
        agent_result = await get_agent_response(
            input_text,
            language_context,
            language=input_language if input_language != "auto" else detected_language,
            response_style=response_style,
        )
        agent_duration = (time.time() - agent_start) * 1000
        print(f"[WS] ⏱️ Agent took {agent_duration:.1f}ms")
        
        if not isinstance(agent_result, dict):
            await ws.send_json({
                "type": "streaming_error",
                "error": "Invalid agent response", 
                "stage": "agent"
            })
            return
            
        response_text = agent_result.get("response", "")
        response_emotion = agent_result.get("emotion", "none")
        
        print(f"[WS] Agent Complete: '{response_text[:50]}...'")
        print(f"[WS] Emotion: {response_emotion}")
        
        # Step 4: Send TEXT IMMEDIATELY to frontend
        await ws.send_json({
            "type": "streaming_text_response",
            "success": True,
            "input_text": input_text,
            "input_language": detected_language,
            "response_text": response_text,
            "emotion": response_emotion,
            "stt_confidence": stt_result["confidence"],
            "is_tamil": is_tamil,
            "is_hindi": is_hindi,
            "response_style": response_style,
            "audio_processing": "in_progress"  # Indicates audio is being generated
        })
        
        print(f"[WS] ✅ Text response sent immediately")
        
        # Step 4: TTS Processing - Generate audio with a single full-response call
        resolved_output_language = output_language if output_language in {"en", "ta", "hi"} else "en"
        
        try:
            print("[WS] Generating single TTS response...")

            tts_result = await audio_manager.process_text_to_audio(
                text=response_text,
                language=resolved_output_language,
                emotion=response_emotion,
            )

            if tts_result["success"]:
                audio_base64 = base64.b64encode(tts_result["audio_data"]).decode('utf-8')

                await ws.send_json({
                    "type": "streaming_audio_response",
                    "success": True,
                    "audio_data": audio_base64,
                    "audio_format": tts_result.get("format", "wav"),
                    "audio_duration": tts_result.get("duration", 0.0),
                    "output_language": resolved_output_language,
                    "audio_processing": "complete"
                })
            else:
                await ws.send_json({
                    "type": "streaming_audio_error",
                    "error": f"TTS failed: {tts_result.get('error', 'Unknown error')}",
                    "audio_processing": "failed"
                })

        except Exception as tts_error:
            print(f"[WS] TTS failed: {tts_error}")
            await ws.send_json({
                "type": "streaming_audio_error",
                "error": f"TTS failed: {str(tts_error)}",
                "audio_processing": "failed"
            })
            
    except Exception as e:
        await ws.send_json({
            "type": "streaming_error",
            "error": f"Streaming processing error: {str(e)}",
            "stage": "general"
        })


async def handle_audio_base64_streaming_with_tokens(ws: WebSocket, payload: dict):
    """Handle base64 audio with token-by-token streaming response"""
    try:
        audio_base64 = payload.get("audio_data", "")
        if not audio_base64:
            await ws.send_json({
                "type": "error",
                "response": "No audio data provided",
                "emotion": "sad"
            })
            return
        
        # Decode base64 audio
        audio_data = base64.b64decode(audio_base64)
        input_language = payload.get("language", payload.get("input_language", "auto"))
        output_language = payload.get("output_language", "en")
        response_style = normalize_response_style(payload.get("response_style", ""), input_language)
        
        print(f"[WS] Token streaming audio: {len(audio_data)} bytes")
        
        # Get audio manager
        audio_manager = get_audio_manager()
        
        # Step 1: STT Processing - Get text quickly
        stt_start = time.time()
        stt_result = await audio_manager.process_audio_to_text(audio_data, input_language)
        stt_duration = (time.time() - stt_start) * 1000
        print(f"[WS] ⏱️ STT took {stt_duration:.1f}ms")
        
        if not stt_result["success"]:
            await ws.send_json({
                "type": "streaming_error", 
                "error": stt_result.get("error", "STT failed"),
                "stage": "stt"
            })
            return
            
        input_text = stt_result["text"]
        detected_language = stt_result.get("language", "unknown")
        is_tamil = stt_result.get("is_tamil", False)
        is_hindi = stt_result.get("is_hindi", False)
        
        # Create language context
        language_context = {
            "language": detected_language,
            "is_tamil": is_tamil,
            "is_hindi": is_hindi,
            "confidence": stt_result["confidence"]
        }
        
        print(f"[WS] STT Complete: '{input_text}' (detected: {detected_language})")
        
        # Step 2: Send STT result immediately
        await ws.send_json({
            "type": "streaming_stt_complete", 
            "input_text": input_text,
            "input_language": detected_language,
            "is_tamil": is_tamil,
            "is_hindi": is_hindi,
            "stt_confidence": stt_result["confidence"]
        })
        
        # Step 3: Agent Processing with TOKEN STREAMING (Wait for full response)
        agent_start = time.time()
        print(f"[WS] 🚀 Starting token streaming...")
        
        full_response = ""
        response_emotion = "none"
        token_count = 0
        resolved_output_language = output_language if output_language in {"en", "ta", "hi"} else "en"
        
        # Stream tokens from Groq as they arrive
        async for stream_chunk in get_agent_response_streaming(
            input_text,
            language_context,
            language=input_language if input_language != "auto" else detected_language,
            response_style=response_style,
        ):
            chunk_type = stream_chunk.get("type")
            
            if chunk_type == "token":
                token = stream_chunk.get("token", "")
                if "token_count" in stream_chunk:
                    token_count = stream_chunk.get("token_count", 0)
                else:
                    token_count += 1
                
                full_response += token
                
                await ws.send_json({
                    "type": "streaming_token",
                    "token": token,
                    "token_count": token_count
                })
                
            elif chunk_type == "complete":
                full_response = stream_chunk.get("response", full_response)
                response_emotion = stream_chunk.get("emotion", "none")
                
                await ws.send_json({
                    "type": "streaming_text_complete",
                    "response_text": full_response,
                    "emotion": response_emotion,
                    "response_style": response_style,
                    "token_count": token_count
                })
                
            elif chunk_type == "error":
                await ws.send_json({
                    "type": "streaming_error",
                    "error": stream_chunk.get("error", "Agent streaming failed"),
                    "stage": "agent"
                })
                return
                
        print(f"[WS] ✅ LLM streaming complete: '{full_response[:50]}...'")
        
        # Step 4: Edge TTS Binary Streaming (Single API Call)
        try:
            print("[WS] 🚀 Starting Edge TTS Binary Stream...")
            
            # Send start signal to let frontend know binary audio is coming
            await ws.send_json({
                "type": "audio_stream_start"
            })
            
            audio_manager = get_audio_manager()
            tts_processor = audio_manager.tts_processor
            
            # Stream binary MP3 chunks directly from Microsoft Edge TTS to the websocket!
            chunk_count = 0
            async for audio_chunk in tts_processor.synthesize_speech_stream(
                text=full_response,
                language=resolved_output_language,
                emotion=response_emotion
            ):
                await ws.send_bytes(audio_chunk)
                chunk_count += 1
                
            # Send end signal to let frontend play the merged audio
            await ws.send_json({
                "type": "audio_stream_end"
            })
            
            print(f"[WS] 🎉 Edge TTS Binary Stream generated {chunk_count} chunks successfully!")
            
        except Exception as tts_error:
            print(f"[WS] Edge TTS streaming error: {tts_error}")
            await ws.send_json({
                "type": "streaming_audio_error",
                "error": f"TTS error: {str(tts_error)}",
                "stage": "tts"
            })
            
    except Exception as e:
        print(f"[WS] Token streaming error: {e}")
        import traceback
        traceback.print_exc()
        await ws.send_json({
            "type": "streaming_error",
            "error": f"Token streaming error: {str(e)}",
            "stage": "general"
        })


async def handle_tts_streaming(ws: WebSocket, payload: dict):
    """Handle text-to-speech generation with a single request."""
    try:
        text = payload.get("text", "").strip()
        if not text:
            await ws.send_json({
                "type": "error",
                "response": "No text provided for TTS",
                "emotion": "sad"
            })
            return
            
        language = payload.get("language", "en")
        emotion = payload.get("emotion", "none")
        
        print(f"[WS] TTS Single Call: '{text[:50]}...' (lang: {language})")

        audio_manager = get_audio_manager()
        tts_result = await audio_manager.process_text_to_audio(
            text=text,
            language=language,
            emotion=emotion,
        )

        if tts_result["success"]:
            audio_base64 = base64.b64encode(tts_result["audio_data"]).decode('utf-8')
            await ws.send_json({
                "type": "streaming_tts_complete",
                "audio_data": audio_base64,
                "audio_format": tts_result.get("format", "wav"),
                "chunk_duration": tts_result.get("duration", 0.0),
                "total_chunks_processed": 1,
                "is_final": True
            })
            print("🎵 Single TTS response generated")
        else:
            await ws.send_json({
                "type": "streaming_tts_error",
                "error": tts_result.get("error", "TTS failed"),
            })
        
    except Exception as e:
        await ws.send_json({
            "type": "streaming_error",
            "error": f"TTS streaming error: {str(e)}",
            "stage": "tts_streaming"
        })


def split_text_into_sentences(text: str) -> list[str]:
    """Split text into complete sentences for streaming TTS"""
    import re
    
    # Handle common abbreviations to avoid false splits
    text = text.replace("Mr.", "Mr").replace("Dr.", "Dr")
    text = text.replace("A.M.", "AM").replace("P.M.", "PM")
    text = text.replace("etc.", "etc")
    
    # Split by sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    # Clean and process sentences
    processed_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Restore abbreviations 
        sentence = sentence.replace("Mr", "Mr.").replace("Dr", "Dr.")
        sentence = sentence.replace("AM", "A.M.").replace("PM", "P.M.")
        sentence = sentence.replace("etc", "etc.")
        
        # Combine very short sentences (less than 4 words) with the previous one
        if len(sentence.split()) < 4 and processed_sentences:
            processed_sentences[-1] += " " + sentence
        else:
            processed_sentences.append(sentence)
    
    # Ensure we have at least one sentence
    if not processed_sentences:
        processed_sentences = [text]
        
    return processed_sentences


async def handle_test_immediate(ws: WebSocket, payload: dict):
    """Test immediate response functionality - bypass all processing"""
    import time
    import asyncio
    
    test_message = payload.get("message", "Test message")
    
    # Send immediate response
    await ws.send_json({
        "type": "test_immediate_response",
        "message": f"Immediate: {test_message}",
        "timestamp": time.time(),
        "status": "immediate_sent"
    })
    
    print(f"[WS] ✅ Test immediate response sent")
    
    # Simulate some processing time
    for i in range(3):
        await asyncio.sleep(1)
        await ws.send_json({
            "type": "test_progress",
            "step": i + 1,
            "message": f"Processing step {i + 1}/3",
            "timestamp": time.time()
        })
        print(f"[WS] Test progress step {i + 1}/3 sent")
    
    # Send final response
    await ws.send_json({
        "type": "test_final_response", 
        "message": f"Final response for: {test_message}",
        "timestamp": time.time(),
        "status": "complete"
    })
    
    print(f"[WS] ✅ Test final response sent")


async def handle_audio_info_request(ws: WebSocket):
    """Handle request for audio capabilities info"""
    info = audio_manager.get_supported_formats()
    await ws.send_json({
        "type": "audio_info_response",
        "info": info
    })


async def handle_voices_request(ws: WebSocket, payload: dict):
    """Handle request for available voices"""
    language = payload.get("language", "en")
    voices = await audio_manager.get_voice_options(language)
    await ws.send_json({
        "type": "voices_response",
        "voices": voices
    })
