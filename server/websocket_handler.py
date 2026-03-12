import json
import traceback
import base64
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from agent.groq_llama_agent import get_agent_response  # Changed to Groq Llama
from audio.manager import get_audio_manager

router = APIRouter()
audio_manager = get_audio_manager()


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
    
    # Get agent response
    result = await get_agent_response(query)
    
    if enable_tts and result.get("response"):
        # Generate audio for the response
        tts_result = await audio_manager.process_text_to_audio(
            result["response"],
            tts_language,
            result.get("emotion", "none")
        )
        
        if tts_result["success"]:
            # Encode audio data to base64 for JSON transport
            audio_base64 = base64.b64encode(tts_result["audio_data"]).decode('utf-8')
            result.update({
                "type": "text_with_audio_response",
                "audio_data": audio_base64,
                "audio_format": tts_result["format"],
                "audio_duration": tts_result["duration"]
            })
        else:
            result["type"] = "text_response"
            result["tts_error"] = tts_result.get("error", "TTS failed")
    else:
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
        output_language="en"
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
        input_language = payload.get("input_language", "en")
        output_language = payload.get("output_language", "en")
        
        print(f"[WS] Received base64 audio: {len(audio_data)} bytes")
        
        # Process through conversation flow
        conversation_result = await audio_manager.process_audio_conversation(
            audio_data,
            get_agent_response,
            input_language=input_language,
            output_language=output_language
        )
        
        if conversation_result["success"]:
            # Encode response audio to base64
            response_audio_base64 = base64.b64encode(conversation_result["audio_data"]).decode('utf-8')
            
            response = {
                "type": "audio_conversation_response",
                "success": True,
                "input_text": conversation_result["input_text"],
                "input_language": conversation_result["input_language"],
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
        
        # Use the same streaming logic as base64 handler
        await handle_audio_base64_streaming(ws, {
            "audio_data": base64.b64encode(audio_data).decode('utf-8'),
            "input_language": input_language,
            "output_language": output_language
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
        input_language = payload.get("input_language", "auto")
        output_language = payload.get("output_language", "en")
        
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
        
        # Create language context
        language_context = {
            "language": detected_language,
            "is_tamil": is_tamil,
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
        agent_result = await get_agent_response(input_text, language_context)
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
            "audio_processing": "in_progress"  # Indicates audio is being generated
        })
        
        print(f"[WS] ✅ Text response sent immediately")
        
        # Step 4: TTS Processing - Generate audio with sentence streaming
        resolved_output_language = output_language if output_language in {"en", "ta"} else "en"
        
        try:
            # Use sentence-based streaming for TTS
            sentences = split_text_into_sentences(response_text)
            print(f"[WS] Streaming TTS for {len(sentences)} sentences...")
            
            for i, sentence in enumerate(sentences):
                print(f"   🎵 TTS Sentence {i+1}: '{sentence}'")
                
                tts_result = await audio_manager.process_text_to_audio(
                    text=sentence,
                    language=resolved_output_language, 
                    emotion=response_emotion
                )
                
                if tts_result["success"]:
                    # Encode audio to base64
                    audio_base64 = base64.b64encode(tts_result["audio_data"]).decode('utf-8')
                    
                    # Stream each sentence's audio immediately
                    await ws.send_json({
                        "type": "streaming_audio_chunk",
                        "chunk_id": i,
                        "total_chunks": len(sentences),
                        "text_chunk": sentence,
                        "audio_data": audio_base64,
                        "audio_format": tts_result.get("format", "wav"),
                        "audio_duration": tts_result.get("duration", 0.0),
                        "output_language": resolved_output_language,
                        "is_final": (i == len(sentences) - 1),
                        "audio_processing": "streaming" if i < len(sentences) - 1 else "complete"
                    })
                    
                    print(f"   ✅ Streamed audio chunk {i+1}/{len(sentences)}")
                    
                else:
                    # Send error for this chunk but continue with others
                    await ws.send_json({
                        "type": "streaming_audio_error", 
                        "error": tts_result.get("error", "TTS failed"),
                        "chunk_id": i,
                        "text_chunk": sentence,
                        "audio_processing": "failed"
                    })
                    
        except Exception as tts_error:
            # Fallback to non-streaming TTS if sentence streaming fails
            print(f"[WS] Sentence streaming failed, using fallback TTS: {tts_error}")
            
            tts_result = await audio_manager.process_text_to_audio(
                response_text,
                resolved_output_language, 
                response_emotion
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
                    "error": f"TTS fallback failed: {tts_result.get('error', 'Unknown error')}",
                    "audio_processing": "failed"
                })
            
    except Exception as e:
        await ws.send_json({
            "type": "streaming_error",
            "error": f"Streaming processing error: {str(e)}",
            "stage": "general"
        })


async def handle_tts_streaming(ws: WebSocket, payload: dict):
    """Handle text-to-speech streaming by sentences"""
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
        
        print(f"[WS] TTS Streaming: '{text[:50]}...' (lang: {language})")
        
        # Split text into sentences
        sentences = split_text_into_sentences(text)
        
        print(f"[WS] Streaming {len(sentences)} sentences...")
        
        # Get audio manager
        audio_manager = get_audio_manager()
        
        # Process each sentence separately
        for i, sentence in enumerate(sentences):
            print(f"   📝 Sentence {i+1}: '{sentence}'")
            
            try:
                # Generate TTS for this sentence
                tts_result = await audio_manager.process_text_to_audio(
                    text=sentence,
                    language=language,
                    emotion=emotion
                )
                
                if tts_result["success"]:
                    # Convert to base64
                    audio_base64 = base64.b64encode(tts_result["audio_data"]).decode('utf-8')
                    
                    # Stream this sentence's audio immediately
                    await ws.send_json({
                        "type": "streaming_tts_chunk",
                        "chunk_id": i,
                        "total_chunks": len(sentences),
                        "text_chunk": sentence,
                        "audio_data": audio_base64,
                        "audio_format": tts_result.get("format", "wav"),
                        "is_final": (i == len(sentences) - 1),
                        "chunk_duration": tts_result.get("duration", 0.0)
                    })
                    
                    print(f"   ✅ Streamed sentence {i+1}/{len(sentences)}")
                    
                else:
                    print(f"   ❌ TTS failed for sentence {i+1}: {tts_result.get('error')}")
                    await ws.send_json({
                        "type": "streaming_tts_error",
                        "chunk_id": i,
                        "error": tts_result.get("error", "TTS failed"),
                        "text_chunk": sentence
                    })
                    
            except Exception as sentence_error:
                print(f"   ❌ Error processing sentence {i+1}: {sentence_error}")
                await ws.send_json({
                    "type": "streaming_tts_error",
                    "chunk_id": i,
                    "error": str(sentence_error),
                    "text_chunk": sentence
                })
        
        # Send completion signal
        await ws.send_json({
            "type": "streaming_tts_complete",
            "total_chunks_processed": len(sentences)
        })
        
        print("🎵 All sentences streamed!")
        
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
