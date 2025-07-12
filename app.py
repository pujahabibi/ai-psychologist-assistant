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
from typing import Dict, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, FileResponse
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
    Complete voice therapy interaction using clean architecture
    """
    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Read uploaded audio file
        audio_bytes = await audio_file.read()
        
        # Create AudioData entity
        audio_data = AudioData(
            audio_bytes=audio_bytes,
            format=settings.audio_config.default_format
        )
        
        # Use clean architecture use case
        therapy_use_case = clean_app.get_therapy_use_case()
        result = await therapy_use_case.process_voice_therapy(audio_data, session_id)
        
        if not result["success"]:
            return TherapyResponse(
                success=False,
                error=result["error"],
                session_id=session_id
            )
        
        # Save audio response to file
        audio_url = None
        if result["audio_data"] and result["audio_data"].audio_bytes:
            audio_filename = f"therapy_response_{uuid.uuid4().hex}.{settings.audio_config.default_format}"
            audio_path = static_dir / audio_filename
            
            async with aiofiles.open(audio_path, "wb") as f:
                await f.write(result["audio_data"].audio_bytes)
            
            audio_url = f"/static/{audio_filename}"
        
        return TherapyResponse(
            success=True,
            user_text=result["user_text"],
            ai_response=result["ai_response"],
            audio_url=audio_url,
            session_id=session_id,
            latency=result["latency"],
            model_used=result["response_metrics"]["model_used"],
            alert_level=result["response_metrics"]["alert_level"]
        )
        
    except Exception as e:
        logger.error(f"Error in voice therapy: {e}")
        return TherapyResponse(
            success=False,
            error=f"Terjadi kesalahan dalam memproses permintaan Anda: {str(e)}",
            session_id=session_id
        )


@app.post("/speech-to-text")
async def speech_to_text_endpoint(audio_file: UploadFile = File(...)):
    """Convert speech to text using clean architecture"""
    try:
        audio_bytes = await audio_file.read()
        
        # Create AudioData entity
        audio_data = AudioData(
            audio_bytes=audio_bytes,
            format=settings.audio_config.default_format
        )
        
        # Use clean architecture use case
        therapy_use_case = clean_app.get_therapy_use_case()
        text = await therapy_use_case.convert_speech_to_text(audio_data)
        
        if not text:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")
        
        return {"text": text}
        
    except Exception as e:
        logger.error(f"Error in speech-to-text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/get-therapy-response")
async def get_therapy_response(request: TextRequest):
    """Get therapeutic response from text input using clean architecture"""
    try:
        # Use clean architecture use case
        therapy_use_case = clean_app.get_therapy_use_case()
        result = await therapy_use_case.process_text_therapy(
            request.text, 
            request.session_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "response": result["response"],
            "session_id": result["session_id"],
            "model_used": result["response_metrics"]["model_used"],
            "alert_level": result["response_metrics"]["alert_level"]
        }
        
    except Exception as e:
        logger.error(f"Error getting therapy response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/text-to-speech")
async def text_to_speech_endpoint(request: TextRequest):
    """Convert text to speech using clean architecture with parallel processing"""
    try:
        start_time = time.time()
        
        # Use clean architecture use case (always parallel per user preference)
        therapy_use_case = clean_app.get_therapy_use_case()
        audio_data = await therapy_use_case.convert_text_to_speech(request.text)
        
        if not audio_data.audio_bytes:
            raise HTTPException(status_code=500, detail="Could not generate audio")
        
        # Save audio to file
        audio_filename = f"tts_output_{uuid.uuid4().hex}.{settings.audio_config.default_format}"
        audio_path = static_dir / audio_filename
        
        async with aiofiles.open(audio_path, "wb") as f:
            await f.write(audio_data.audio_bytes)
        
        processing_time = time.time() - start_time
        
        return {
            "audio_url": f"/static/{audio_filename}",
            "text": request.text,
            "processing_time": processing_time,
            "method_used": "parallel_clean_architecture",
            "format": settings.audio_config.default_format
        }
        
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tts-performance-stats")
async def get_tts_performance_stats():
    """Get TTS performance statistics from clean architecture"""
    try:
        audio_service = clean_app.get_audio_service()
        return audio_service.get_performance_stats()
    except Exception as e:
        logger.error(f"Error getting TTS stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session-info/{session_id}")
async def get_session_info(session_id: str):
    """Get session information using clean architecture"""
    try:
        therapy_use_case = clean_app.get_therapy_use_case()
        session_info = therapy_use_case.get_session_info(session_id)
        
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session_info
        
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear session using clean architecture"""
    try:
        therapy_use_case = clean_app.get_therapy_use_case()
        success = therapy_use_case.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions")
async def list_sessions():
    """List all sessions using clean architecture"""
    try:
        therapy_use_case = clean_app.get_therapy_use_case()
        sessions = therapy_use_case.list_sessions()
        
        return {"sessions": sessions}
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session-analysis/{session_id}")
async def get_session_analysis(session_id: str):
    """Get session analysis using clean architecture"""
    try:
        therapy_use_case = clean_app.get_therapy_use_case()
        analysis = therapy_use_case.get_session_analysis(session_id)
        
        return analysis
        
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
    """Create session consent using clean architecture"""
    try:
        session_manager = clean_app.get_session_manager()
        consent_manager = session_manager.get_consent_manager()
        
        consent_data = {
            "consent_given": consent_given,
            "recording_consent": recording_consent,
            "data_sharing_consent": data_sharing_consent,
            "anonymization_level": anonymization_level,
            "retention_period": retention_period
        }
        
        consent_record = consent_manager.record_consent(
            session_id, ip_address, consent_data
        )
        
        return consent_record
        
    except Exception as e:
        logger.error(f"Error creating session consent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/crisis-resources")
async def get_crisis_resources():
    """Get crisis resources from clean architecture"""
    try:
        return clean_app.get_crisis_resources()
    except Exception as e:
        logger.error(f"Error getting crisis resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    """Get Claude status from clean architecture"""
    try:
        ai_orchestrator = clean_app.get_ai_orchestrator()
        service_status = ai_orchestrator.get_service_status()
        
        return {
            "claude_available": service_status["claude_available"],
            "claude_model": service_status["claude_model"],
            "gpt_available": service_status["gpt_available"],
            "gpt_model": service_status["gpt_model"]
        }
        
    except Exception as e:
        logger.error(f"Error getting Claude status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 