#!/usr/bin/env python3
"""
FastAPI Backend for Indonesian Mental Health Support Chatbot (Clean Architecture)
Provides voice-based therapeutic conversations with cultural sensitivity
"""

import io
import os
import time
import uuid
import tempfile
import json
from typing import Dict, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import aiofiles
from pathlib import Path
import logging

# Import clean architecture components
from src.main.app import app as clean_app
from src.core.entities.audio_data import AudioData
from src.infrastructure.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    
    # Startup
    try:
        logger.info("🧠 Starting Indonesian Mental Health Support Bot Server (Clean Architecture)")
        logger.info("💚 Server Bot Dukungan Kesehatan Mental Indonesia (Arsitektur Bersih)")
        logger.info("🌐 Access the therapy interface at: http://localhost:8000")
        logger.info("📚 API Documentation available at: http://localhost:8000/docs")
        
        # Clean architecture app is already initialized
        logger.info("✅ Clean architecture application initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        clean_app.cleanup()
        logger.info("🧹 Application cleanup completed")
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")


app = FastAPI(
    title="Indonesian Mental Health Support Bot (Clean Architecture)",
    description="Voice-based therapeutic chatbot with cultural sensitivity for Indonesian users",
    version="2.0.0",
    lifespan=lifespan
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")

# Create static directory if it doesn't exist
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models
class TextRequest(BaseModel):
    text: str
    session_id: Optional[str] = None

class TherapyResponse(BaseModel):
    success: bool
    user_text: Optional[str] = None
    ai_response: Optional[str] = None
    audio_url: Optional[str] = None
    session_id: Optional[str] = None
    error: Optional[str] = None
    latency: Optional[float] = None
    model_used: Optional[str] = None
    alert_level: Optional[str] = None


@app.get("/")
async def root():
    """Serve the main therapy interface"""
    return FileResponse("templates/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint with clean architecture info"""
    return {
        "status": "healthy", 
        "service": "indonesian-mental-health-bot",
        "architecture": "clean",
        "version": "2.0.0"
    }


@app.get("/service-status")
async def service_status():
    """Get service status from clean architecture"""
    return clean_app.get_service_status()


@app.post("/voice-therapy", response_model=TherapyResponse)
async def voice_therapy(
    audio_file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    Complete voice therapy interaction
    Processes audio input and returns therapeutic response with audio
    """
    start_time = time.time()
    
    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Read uploaded audio file
        audio_data = await audio_file.read()
        
        # Create AudioData entity for clean architecture
        audio_entity = AudioData(
            audio_bytes=audio_data,
            format=settings.audio_config.default_format
        )
        
        # Convert speech to text using clean architecture
        therapy_use_case = clean_app.get_therapy_use_case()
        audio_service = clean_app.get_audio_service()
        
        # Speech to text
        processed_audio = await audio_service.speech_to_text(audio_entity)
        user_text = processed_audio.transcription
        
        if not user_text:
            return TherapyResponse(
                success=False,
                error="Maaf, saya tidak dapat mendengar suara Anda dengan jelas. Silakan coba lagi.",
                session_id=session_id
            )
        
        # Get therapeutic response
        therapy_result = await therapy_use_case.process_text_therapy(user_text, session_id)
        ai_response = therapy_result["response"]
        
        # Convert response to speech using parallel processing
        response_length = len(ai_response)
        # Use parallel processing with smart worker allocation (RESTORED ORIGINAL LOGIC)
        if response_length <= 150:
            audio_response_data = await audio_service.text_to_speech_parallel(ai_response)
        else:
            audio_response_data = await audio_service.text_to_speech_parallel(ai_response, max_workers=8)
        
        # Save audio response to file
        audio_url = None
        if audio_response_data and audio_response_data.audio_bytes:
            audio_filename = f"therapy_response_{uuid.uuid4().hex}.mp3"
            audio_path = static_dir / audio_filename
            
            async with aiofiles.open(audio_path, "wb") as f:
                await f.write(audio_response_data.audio_bytes)
            
            audio_url = f"/static/{audio_filename}"
        
        # Calculate latency
        latency = time.time() - start_time
        
        return TherapyResponse(
            success=True,
            user_text=user_text,
            ai_response=ai_response,
            audio_url=audio_url,
            session_id=session_id,
            latency=latency
        )
        
    except Exception as e:
        logger.error(f"Error in voice therapy: {e}")
        return TherapyResponse(
            success=False,
            error=f"Terjadi kesalahan dalam memproses permintaan Anda: {str(e)}",
            session_id=session_id
        )


@app.post("/streaming-therapy")
async def streaming_therapy(request: TextRequest):
    """
    Streaming therapy interaction with parallel TTS processing
    Provides real-time response streaming with chunked audio generation
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Use clean architecture streaming use case
        therapy_use_case = clean_app.get_therapy_use_case()
        
        async def generate_streaming_response():
            """Generate streaming response with individual audio chunks"""
            async for chunk in therapy_use_case.process_streaming_therapy(
                request.text, 
                session_id
            ):
                # Handle different chunk types
                if chunk.get("type") == "complete_response":
                    # Final response (no merged audio)
                    final_response = {
                        "type": "complete_response",
                        "content": chunk.get("content", ""),
                        "session_id": chunk.get("session_id"),
                        "latency": chunk.get("latency", 0),
                        "sentences_processed": chunk.get("sentences_processed", 0),
                        "success": chunk.get("success", True)
                    }
                    
                    yield f"data: {json.dumps(final_response)}\n\n"
                    
                elif chunk.get("type") == "audio_chunk":
                    # Individual audio chunk - save and send immediately
                    audio_url = None
                    if chunk.get("audio_data") and chunk["audio_data"].audio_bytes:
                        # Save individual audio chunk to file
                        audio_filename = f"audio_chunk_{session_id}_{chunk.get('chunk_id', 0)}.mp3"
                        audio_path = static_dir / audio_filename
                        
                        async with aiofiles.open(audio_path, "wb") as f:
                            await f.write(chunk["audio_data"].audio_bytes)
                        
                        audio_url = f"/static/{audio_filename}"
                    
                    # Send audio chunk immediately
                    audio_response = {
                        "type": "audio_chunk",
                        "content": chunk.get("content", ""),
                        "session_id": chunk.get("session_id"),
                        "chunk_id": chunk.get("chunk_id", 0),
                        "audio_url": audio_url,
                        "partial_response": chunk.get("partial_response", "")
                    }
                    
                    yield f"data: {json.dumps(audio_response)}\n\n"
                    
                elif chunk.get("type") == "text_chunk":
                    # Individual sentence processed
                    sentence_response = {
                        "type": "text_chunk",
                        "content": chunk.get("content", ""),
                        "session_id": chunk.get("session_id"),
                        "chunk_id": chunk.get("chunk_id", 0),
                        "partial_response": chunk.get("partial_response", "")
                    }
                    
                    yield f"data: {json.dumps(sentence_response)}\n\n"
                    
                elif chunk.get("type") == "streaming_chunk":
                    # Real-time streaming content
                    streaming_response = {
                        "type": "streaming_chunk",
                        "content": chunk.get("content", ""),
                        "session_id": chunk.get("session_id"),
                        "partial_response": chunk.get("partial_response", "")
                    }
                    
                    yield f"data: {json.dumps(streaming_response)}\n\n"
                    
                elif chunk.get("type") == "error":
                    # Error response
                    error_response = {
                        "type": "error",
                        "error": chunk.get("error", "Unknown error"),
                        "session_id": chunk.get("session_id"),
                        "success": False
                    }
                    
                    yield f"data: {json.dumps(error_response)}\n\n"
                    break
        
        # Return streaming response
        return StreamingResponse(
            generate_streaming_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in streaming therapy: {e}")
        error_response = {
            "type": "error",
            "error": f"Terjadi kesalahan dalam memproses permintaan Anda: {str(e)}",
            "session_id": request.session_id,
            "success": False
        }
        
        async def error_stream():
            yield f"data: {json.dumps(error_response)}\n\n"
        
        return StreamingResponse(
            error_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )


@app.post("/speech-to-text")
async def speech_to_text_endpoint(audio_file: UploadFile = File(...)):
    """Convert speech to text using Whisper"""
    try:
        audio_data = await audio_file.read()
        
        # Create AudioData entity for clean architecture
        audio_entity = AudioData(
            audio_bytes=audio_data,
            format=settings.audio_config.default_format
        )
        
        # Use audio service directly
        audio_service = clean_app.get_audio_service()
        processed_audio = await audio_service.speech_to_text(audio_entity)
        text = processed_audio.transcription
        
        if not text:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")
        
        return {"text": text}
        
    except Exception as e:
        logger.error(f"Error in speech-to-text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/get-therapy-response")
async def get_therapy_response(request: TextRequest):
    """Get therapeutic response from text input"""
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Use clean architecture use case
        therapy_use_case = clean_app.get_therapy_use_case()
        result = await therapy_use_case.process_text_therapy(
            request.text, 
            session_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "response": result["response"],
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error getting therapy response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/text-to-speech")
async def text_to_speech_endpoint(request: TextRequest):
    """Convert text to speech using OpenAI TTS with parallel processing"""
    try:
        start_time = time.time()
        
        # Always use parallel processing regardless of text length
        text_length = len(request.text)
        
        # Use clean architecture audio service
        audio_service = clean_app.get_audio_service()
        
        if text_length <= 150:
            # Use parallel TTS for texts 150 characters or less
            audio_data = await audio_service.text_to_speech_parallel(request.text)
            method_used = "parallel"
        else:
            # Use parallel TTS with more workers for texts over 150 characters (PERFORMANCE RESTORED)
            audio_data = await audio_service.text_to_speech_parallel(request.text, max_workers=8)
            method_used = "parallel_extended"
        
        if not audio_data.audio_bytes:
            raise HTTPException(status_code=500, detail="Could not generate audio")
        
        # Save audio to file
        audio_filename = f"tts_output_{uuid.uuid4().hex}.mp3"
        audio_path = static_dir / audio_filename
        
        async with aiofiles.open(audio_path, "wb") as f:
            await f.write(audio_data.audio_bytes)
        
        processing_time = time.time() - start_time
        
        return {
            "audio_url": f"/static/{audio_filename}",
            "text": request.text,
            "processing_time": round(processing_time, 2),
            "method_used": method_used,
            "text_length": text_length,
            "performance_gain": f"{round(text_length / processing_time, 2)} chars/sec"
        }
        
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tts-performance-stats")
async def get_tts_performance_stats():
    """Get TTS performance statistics"""
    try:
        audio_service = clean_app.get_audio_service()
        return audio_service.get_performance_stats()
    except Exception as e:
        logger.error(f"Error getting TTS performance stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session-info/{session_id}")
async def get_session_info(session_id: str):
    """Get session information"""
    try:
        therapy_use_case = clean_app.get_therapy_use_case()
        session_info = therapy_use_case.get_session_info(session_id)
        
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a specific session"""
    try:
        therapy_use_case = clean_app.get_therapy_use_case()
        success = therapy_use_case.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": f"Session {session_id} cleared successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    try:
        therapy_use_case = clean_app.get_therapy_use_case()
        sessions = therapy_use_case.list_sessions()
        
        return {
            "sessions": sessions,
            "total_sessions": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session-analysis/{session_id}")
async def get_session_analysis(session_id: str):
    """Get session analysis with metrics"""
    try:
        therapy_use_case = clean_app.get_therapy_use_case()
        analysis = therapy_use_case.get_session_analysis(session_id)
        
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/session-consent")
async def create_session_consent(
    session_id: str = Form(...),
    ip_address: str = Form(...),
    consent_given: bool = Form(True),
    recording_consent: bool = Form(False),
    data_sharing_consent: bool = Form(False),
    anonymization_level: str = Form("high"),
    retention_period: int = Form(30)
):
    """Create session consent record"""
    try:
        # Create consent record
        consent_record = {
            "session_id": session_id,
            "ip_address": ip_address,
            "consent_given": consent_given,
            "recording_consent": recording_consent,
            "data_sharing_consent": data_sharing_consent,
            "anonymization_level": anonymization_level,
            "retention_period": retention_period,
            "timestamp": time.time()
        }
        
        # Store consent (this would typically go to a database)
        logger.info(f"Session consent recorded for {session_id}")
        
        return {
            "message": "Consent recorded successfully",
            "session_id": session_id,
            "consent_record": consent_record
        }
        
    except Exception as e:
        logger.error(f"Error creating session consent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/crisis-resources")
async def get_crisis_resources():
    """Get crisis intervention resources"""
    return {
        "emergency_hotlines": [
            {"name": "Pencegahan Bunuh Diri", "number": "119"},
            {"name": "Gawat Darurat", "number": "118"},
            {"name": "Kepolisian", "number": "110"},
            {"name": "Mental Health Crisis", "number": "500-454"}
        ],
        "online_resources": [
            {"name": "Crisis Chat", "url": "https://krisispsikologi.com"},
            {"name": "Mental Health Indonesia", "url": "https://mentalhealth.id"}
        ]
    }


@app.post("/therapeutic-response-validation")
async def get_therapeutic_response_with_validation(request: TextRequest):
    """Get validated response from both models using clean architecture"""
    try:
        therapy_use_case = clean_app.get_therapy_use_case()
        validation_result = await therapy_use_case.get_validated_response(
            request.text, 
            request.session_id
        )
        
        return {
            "user_input": request.text,
            "session_id": request.session_id,
            "gpt_response": validation_result.gpt_response.content if validation_result.gpt_response else None,
            "claude_response": validation_result.claude_response.content if validation_result.claude_response else None,
            "primary_response": validation_result.get_primary_or_fallback().content,
            "primary_model": validation_result.get_primary_or_fallback().model_used,
            "has_claude_fallback": validation_result.has_claude_fallback(),
            "consensus_reached": validation_result.consensus_reached
        }
        
    except Exception as e:
        logger.error(f"Error in therapeutic response validation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/claude-status")
async def get_claude_status():
    """Get Claude service status"""
    try:
        ai_orchestrator = clean_app.get_ai_orchestrator()
        claude_service = ai_orchestrator.claude_service
        
        return {
            "claude_available": claude_service.is_available(),
            "model_name": claude_service.get_model_name(),
            "service_status": "available" if claude_service.is_available() else "unavailable"
        }
        
    except Exception as e:
        logger.error(f"Error getting Claude status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 