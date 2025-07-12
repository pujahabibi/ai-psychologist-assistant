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
        
        # Convert response to speech using parallel processing
        response_length = len(ai_response)
        if response_length < 100:
            audio_response = bot.text_to_speech(ai_response)
        else:
            audio_response = await bot.text_to_speech_parallel(ai_response)
        
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
    """Convert text to speech using OpenAI TTS with parallel processing"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        start_time = time.time()
        
        # Choose TTS method based on text length
        text_length = len(request.text)
        
        if text_length < 100:
            # Use regular TTS for short texts
            audio_data = bot.text_to_speech(request.text)
            method_used = "synchronous"
        elif text_length < 1000:
            # Use parallel TTS for medium texts
            audio_data = await bot.text_to_speech_parallel(request.text)
            method_used = "parallel"
        else:
            # Use parallel TTS with more workers for long texts
            audio_data = await bot.text_to_speech_parallel(request.text, max_workers=8)
            method_used = "parallel_extended"
        
        if not audio_data:
            raise HTTPException(status_code=500, detail="Could not generate audio")
        
        # Save audio to file
        audio_filename = f"tts_output_{uuid.uuid4().hex}.mp3"
        audio_path = static_dir / audio_filename
        
        async with aiofiles.open(audio_path, "wb") as f:
            await f.write(audio_data)
        
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

@app.post("/text-to-speech-streaming")
async def text_to_speech_streaming_endpoint(request: TextRequest):
    """Stream text-to-speech audio chunks as they become available"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        from fastapi.responses import StreamingResponse
        import json
        
        async def generate_audio_stream():
            """Generate streaming audio chunks"""
            chunk_count = 0
            
            # Send initial metadata
            metadata = {
                "type": "metadata",
                "text": request.text,
                "text_length": len(request.text),
                "estimated_chunks": len(bot._split_text_into_sentences(request.text))
            }
            yield f"data: {json.dumps(metadata)}\n\n"
            
            # Stream audio chunks
            async for chunk_data in bot.text_to_speech_streaming(request.text):
                chunk_count += 1
                
                # Save chunk to file
                audio_filename = f"tts_chunk_{uuid.uuid4().hex}.mp3"
                audio_path = static_dir / audio_filename
                
                async with aiofiles.open(audio_path, "wb") as f:
                    await f.write(chunk_data["audio"])
                
                # Send chunk information
                chunk_info = {
                    "type": "audio_chunk",
                    "chunk_id": chunk_data["chunk_id"],
                    "audio_url": f"/static/{audio_filename}",
                    "text": chunk_data["text"],
                    "total_chunks": chunk_data["total_chunks"],
                    "progress": round((chunk_data["chunk_id"] + 1) / chunk_data["total_chunks"] * 100, 2)
                }
                yield f"data: {json.dumps(chunk_info)}\n\n"
            
            # Send completion signal
            completion = {
                "type": "complete",
                "total_chunks_processed": chunk_count,
                "message": "TTS streaming completed"
            }
            yield f"data: {json.dumps(completion)}\n\n"
        
        return StreamingResponse(
            generate_audio_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        logger.error(f"Error in streaming TTS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tts-performance-stats")
async def get_tts_performance_stats():
    """Get TTS performance statistics and recommendations"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        return bot.get_tts_performance_stats()
    except Exception as e:
        logger.error(f"Error getting TTS stats: {e}")
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

@app.get("/session-analysis/{session_id}")
async def get_session_analysis(session_id: str):
    """Get comprehensive session analysis including intent and safety assessment"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        analysis = bot.get_session_analysis(session_id)
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
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
    """Create session consent record for data protection compliance"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        consent_data = {
            "consent_given": consent_given,
            "recording_consent": recording_consent,
            "data_sharing_consent": data_sharing_consent,
            "anonymization_level": anonymization_level,
            "retention_period": retention_period
        }
        
        result = bot.create_session_consent(session_id, ip_address, consent_data)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        logger.error(f"Error creating session consent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crisis-resources")
async def get_crisis_resources():
    """Get crisis resources and emergency contacts"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        resources = bot.get_crisis_resources()
        return resources
    except Exception as e:
        logger.error(f"Error getting crisis resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/intent-analysis")
async def analyze_intent(request: TextRequest):
    """Analyze user input for emotional state and therapeutic context"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    if not bot.intent_analyzer:
        raise HTTPException(status_code=503, detail="Intent analyzer not available")
    
    try:
        session_id = request.session_id or str(uuid.uuid4())
        conversation_history = bot.conversations.get(session_id, [])
        
        intent_result = bot.intent_analyzer.analyze_intent(request.text, conversation_history)
        
        # Format the result for JSON response
        result = {
            "primary_emotion": intent_result.primary_emotion.value,
            "secondary_emotions": [emotion.value for emotion in intent_result.secondary_emotions],
            "emotion_intensity": intent_result.emotion_intensity,
            "therapeutic_context": intent_result.therapeutic_context.value,
            "suggested_approach": intent_result.suggested_approach,
            "suicide_risk": intent_result.suicide_risk.value,
            "self_harm_risk": intent_result.self_harm_risk.value,
            "crisis_indicators": intent_result.crisis_indicators,
            "cultural_factors": intent_result.cultural_factors,
            "spiritual_elements": intent_result.spiritual_elements,
            "cbt_techniques": intent_result.cbt_techniques,
            "intervention_priority": intent_result.intervention_priority,
            "session_goals": intent_result.session_goals,
            "confidence_score": intent_result.confidence_score,
            "requires_escalation": intent_result.requires_escalation,
            "emergency_contact_needed": intent_result.emergency_contact_needed,
            "timestamp": intent_result.timestamp.isoformat(),
            "session_id": session_id
        }
        
        return result
    except Exception as e:
        logger.error(f"Error in intent analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/safety-assessment")
async def assess_safety(request: TextRequest):
    """Perform safety assessment for user input"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    if not bot.safety_mechanisms or not bot.intent_analyzer:
        raise HTTPException(status_code=503, detail="Safety mechanisms not available")
    
    try:
        session_id = request.session_id or str(uuid.uuid4())
        conversation_history = bot.conversations.get(session_id, [])
        
        # First get intent analysis
        intent_result = bot.intent_analyzer.analyze_intent(request.text, conversation_history)
        
        # Then perform safety assessment
        safety_assessment = bot.safety_mechanisms.assess_safety(
            request.text, intent_result, conversation_history, session_id
        )
        
        # Format the result for JSON response
        result = {
            "alert_level": safety_assessment.alert_level.value,
            "risk_factors": safety_assessment.risk_factors,
            "protective_factors": safety_assessment.protective_factors,
            "immediate_actions": safety_assessment.immediate_actions,
            "referral_needed": safety_assessment.referral_needed,
            "referral_triggers": [trigger.value for trigger in safety_assessment.referral_triggers],
            "emergency_contact": safety_assessment.emergency_contact,
            "session_monitoring": safety_assessment.session_monitoring,
            "data_protection_notes": safety_assessment.data_protection_notes,
            "timestamp": safety_assessment.timestamp.isoformat(),
            "session_id": session_id
        }
        
        # Add emergency response plan if needed
        if safety_assessment.alert_level.value in ["orange", "red"]:
            emergency_plan = bot.safety_mechanisms.get_emergency_response_plan(safety_assessment)
            result["emergency_response_plan"] = emergency_plan
        
        return result
    except Exception as e:
        logger.error(f"Error in safety assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/therapeutic-response")
async def get_therapeutic_response_enhanced(request: TextRequest):
    """Get therapeutic response with full analysis and safety features"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get therapeutic response (this will include all analysis internally)
        ai_response = bot._get_therapeutic_response(request.text, session_id)
        
        # Get session analysis if available
        session_analysis = {}
        if session_id in bot.session_metadata:
            session_analysis = bot.get_session_analysis(session_id)
        
        return {
            "response": ai_response,
            "session_id": session_id,
            "session_analysis": session_analysis
        }
        
    except Exception as e:
        logger.error(f"Error getting therapeutic response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 