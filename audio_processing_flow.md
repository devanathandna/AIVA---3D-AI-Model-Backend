# Audio Processing Pipeline - Chopper AI Agent

This diagram shows the complete audio processing flow for the Chopper AI Agent system.

```mermaid
graph TD
    A[Frontend Audio Input] -->|WebSocket| B[Websocket Handler]
    B --> C[Audio Manager]
    
    C --> D[STT Processing - Groq]
    D --> E{Auto Language Detection}
    E -->|Hindi/Other Languages| F[Force English Transcription]
    E -->|Tamil Detected| G[Re-transcribe in Tamil]
    E -->|English| H[Keep English Transcription]
    
    F --> I[English Text Output]
    G --> J[Tamil Text Output]  
    H --> I
    
    I --> K[Create Language Context]
    J --> L[Create Tamil Context]
    
    K --> M[Gemini Agent Processing]
    L --> N[Gemini Agent - Tamil Mode]
    
    M --> O{JSON Response Valid?}
    N --> P{JSON Response Valid?}
    
    O -->|Yes| Q[Extract Response Text]
    O -->|No| R[JSON Error Recovery]
    P -->|Yes| S[Extract Tamil Response]
    P -->|No| T[JSON Error Recovery - Tamil]
    
    R --> U[Fallback Response Text]
    T --> V[Tamil Fallback Response]
    Q --> W[Response Text Ready]
    S --> X[Tamil Response Ready]
    U --> W
    V --> X
    
    W -->|Stream Text First| Y[Send Text to Frontend]
    X -->|Stream Text First| Z[Send Tamil Text to Frontend]
    
    Y --> AA[TTS Processing - Gemini]
    Z --> BB[Tamil TTS Processing]
    
    AA --> CC{TTS Success?}
    BB --> DD{Tamil TTS Success?}
    
    CC -->|Yes| EE[Audio Data Generated]
    CC -->|No| FF[TTS Error Fallback]
    DD -->|Yes| GG[Tamil Audio Data]
    DD -->|No| HH[Tamil TTS Error]
    
    EE -->|Stream Audio Later| II[Send Audio to Frontend]
    GG -->|Stream Audio Later| JJ[Send Tamil Audio to Frontend]
    FF --> KK[Error Response]
    HH --> LL[Tamil Error Response]
    
    II --> MM[Complete Response]
    JJ --> NN[Complete Tamil Response]
    KK --> OO[Error Handled]
    LL --> PP[Tamil Error Handled]
    
    subgraph "API Key Rotation"
        QQ[Groq Keys Pool<br/>5 Keys]
        RR[Gemini AI Keys<br/>5 Keys] 
        SS[Gemini TTS Keys<br/>5 Keys]
        D -.->|Rotates| QQ
        M -.->|Rotates| RR
        N -.->|Rotates| RR
        AA -.->|Rotates| SS
        BB -.->|Rotates| SS
    end
    
    subgraph "RAG System"
        TT[FAISS Index<br/>TOP_K=3]
        UU[Knowledge Base<br/>Embeddings]
        M --> TT
        N --> TT
        TT --> UU
        UU --> M
        UU --> N
    end
    
    subgraph "Error Recovery"
        VV[STT Fallback:<br/>Force English]
        WW[Agent Fallback:<br/>Extract from JSON]
        XX[TTS Fallback:<br/>Simple Response]
        E -.->|Detection Fails| VV
        O -.->|JSON Invalid| WW  
        P -.->|JSON Invalid| WW
        CC -.->|TTS Fails| XX
        DD -.->|TTS Fails| XX
    end

    style A fill:#e1f5fe
    style D fill:#f3e5f5
    style M fill:#e8f5e8
    style N fill:#e8f5e8
    style AA fill:#fff3e0
    style BB fill:#fff3e0
    style Y fill:#f1f8e9
    style Z fill:#f1f8e9
```

## Key Components

### Main Processing Flow
1. **Frontend Audio Input**: User speaks into microphone
2. **WebSocket Handler**: Receives audio data via WebSocket connection
3. **Audio Manager**: Orchestrates the complete audio processing pipeline
4. **STT Processing**: Groq Whisper transcribes speech to text
5. **Language Detection**: Identifies Tamil vs English vs other languages
6. **Agent Processing**: Gemini generates contextual responses
7. **TTS Processing**: Gemini converts response text back to speech
8. **Streaming Response**: Text sent first, audio sent separately

### System Architecture

#### API Key Rotation System
- **Groq STT**: 5 API keys for speech-to-text processing
- **Gemini AI**: 5 API keys for agent response generation  
- **Gemini TTS**: 5 API keys for text-to-speech synthesis
- Keys rotate automatically to prevent rate limiting

#### RAG (Retrieval Augmented Generation)
- **FAISS Index**: Vector database for knowledge retrieval
- **TOP_K=3**: Optimized for faster retrieval (reduced from 5)
- **Knowledge Base**: Embeddings for contextual information

#### Error Recovery Mechanisms
- **STT Fallback**: Force English transcription if detection fails
- **Agent Fallback**: Extract partial responses from malformed JSON
- **TTS Fallback**: Provide simple responses if synthesis fails

### Current Issues & Solutions

#### Language Detection Problem
- **Issue**: Tamil speech detected as Hindi/other languages
- **Current**: "hostel saapatu eppadi irukkum" → detected as Hindi → incorrect translation
- **Solution**: Force English transcription, then re-check for Tamil characters

#### JSON Response Errors  
- **Issue**: Gemini returns incomplete JSON: `{"response": "Hostel-la, students snacks, beverages, and'`
- **Solution**: Enhanced error recovery with text extraction from partial JSON

#### Streaming Architecture
- **Requirement**: Send text to frontend immediately, audio follows later
- **Implementation**: Separate WebSocket messages for text and audio data

## File Structure Reference

```
backend/
├── audio/
│   ├── stt.py          # Groq STT processing
│   ├── tts.py          # Gemini TTS processing  
│   └── manager.py      # Audio pipeline orchestration
├── agent/
│   └── gemini_agent.py # AI response generation
├── server/
│   └── websocket_handler.py # WebSocket communication
├── rag_faiss/
│   └── config.py       # RAG configuration (TOP_K=3)
└── config/
    ├── api_keys.py     # API key rotation management
    └── settings.py     # System configuration
```