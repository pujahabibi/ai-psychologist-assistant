#!/usr/bin/env python3
"""
FastAPI Backend for Indonesian Mental Health Support Chatbot
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

# Import our mental health bot
from infer import IndonesianMentalHealthBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global bot instance
bot = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    global bot
    
    # Startup
    try:
        logger.info("🧠 Starting Indonesian Mental Health Support Bot Server")
        logger.info("💚 Server Bot Dukungan Kesehatan Mental Indonesia")
        logger.info("🌐 Access the therapy interface at: http://localhost:8000")
        logger.info("📚 API Documentation available at: http://localhost:8000/docs")
        
        bot = IndonesianMentalHealthBot()
        logger.info("🧠 Indonesian Mental Health Support Bot initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize bot: {e}")
        raise
    
    yield
    
    # Shutdown
    if bot:
        try:
            bot.cleanup()
            logger.info("🧹 Bot cleanup completed")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")

app = FastAPI(
    title="Indonesian Mental Health Support Bot",
    description="Voice-based therapeutic chatbot with cultural sensitivity for Indonesian users",
    version="1.0.0",
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

@app.get("/")
async def root():
    """Serve the main therapy interface"""
    return FileResponse("templates/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "indonesian-mental-health-bot"}

@app.post("/voice-therapy", response_model=TherapyResponse)
async def voice_therapy(
    audio_file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    Complete voice therapy interaction
    Processes audio input and returns therapeutic response with audio
    """
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    start_time = time.time()
    
    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Read uploaded audio file
        audio_data = await audio_file.read()
        
        # Convert speech to text
        user_text = bot.speech_to_text(audio_data)
        
        if not user_text:
            return TherapyResponse(
                success=False,
                error="Maaf, saya tidak dapat mendengar suara Anda dengan jelas. Silakan coba lagi.",
                session_id=session_id
            )
        
        # Get therapeutic response
        ai_response = bot._get_therapeutic_response(user_text, session_id)
        
        # Convert response to speech
        audio_response = bot.text_to_speech(ai_response)
        
        # Save audio response to file
        audio_url = None
        if audio_response:
            audio_filename = f"therapy_response_{uuid.uuid4().hex}.mp3"
            audio_path = static_dir / audio_filename
            
            async with aiofiles.open(audio_path, "wb") as f:
                await f.write(audio_response)
            
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

@app.post("/speech-to-text")
async def speech_to_text_endpoint(audio_file: UploadFile = File(...)):
    """Convert speech to text using Whisper"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        audio_data = await audio_file.read()
        text = bot.speech_to_text(audio_data)
        
        if not text:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")
        
        return {"text": text}
        
    except Exception as e:
        logger.error(f"Error in speech-to-text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get-therapy-response")
async def get_therapy_response(request: TextRequest):
    """Get therapeutic response from text input"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        session_id = request.session_id or str(uuid.uuid4())
        response = bot._get_therapeutic_response(request.text, session_id)
        
        return {
            "response": response,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error getting therapy response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/text-to-speech")
async def text_to_speech_endpoint(request: TextRequest):
    """Convert text to speech using OpenAI TTS"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        audio_data = bot.text_to_speech(request.text)
        
        if not audio_data:
            raise HTTPException(status_code=500, detail="Could not generate audio")
        
        # Save audio to file
        audio_filename = f"tts_output_{uuid.uuid4().hex}.mp3"
        audio_path = static_dir / audio_filename
        
        async with aiofiles.open(audio_path, "wb") as f:
            await f.write(audio_data)
        
        return {
            "audio_url": f"/static/{audio_filename}",
            "text": request.text
        }
        
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session-info/{session_id}")
async def get_session_info(session_id: str):
    """Get session information"""
    if not bot or session_id not in bot.conversations:
        raise HTTPException(status_code=404, detail="Session not found")
    
    conversation = bot.conversations[session_id]
    return {
        "session_id": session_id,
        "message_count": len(conversation),
        "last_activity": "recent"  # You might want to add timestamp tracking
    }

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a specific session"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    if session_id in bot.conversations:
        del bot.conversations[session_id]
        return {"message": f"Session {session_id} cleared"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    return {
        "active_sessions": list(bot.conversations.keys()),
        "total_sessions": len(bot.conversations)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 