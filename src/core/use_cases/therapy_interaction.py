#!/usr/bin/env python3
"""
Therapy Interaction Use Cases - Business logic for therapeutic interactions
"""

import time
from typing import Dict, Optional, Any
from uuid import uuid4

from ..entities.therapeutic_session import TherapeuticSession
from ..entities.audio_data import AudioData
from ..entities.therapeutic_response import TherapeuticResponse, ModelValidationResponse
from ..interfaces.ai_service import IAIOrchestrator
from ..interfaces.audio_service import IAudioService
from ..interfaces.session_service import ISessionManager


class TherapyInteractionUseCase:
    """Use case for handling therapy interactions"""
    
    def __init__(
        self,
        ai_orchestrator: IAIOrchestrator,
        audio_service: IAudioService,
        session_manager: ISessionManager,
        system_prompt: str
    ):
        self.ai_orchestrator = ai_orchestrator
        self.audio_service = audio_service
        self.session_manager = session_manager
        self.system_prompt = system_prompt
    
    async def process_voice_therapy(
        self,
        audio_data: AudioData,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process complete voice therapy interaction"""
        start_time = time.time()
        
        try:
            # Get or create session
            if not session_id:
                session_id = str(uuid4())
            
            session = self.session_manager.get_session(session_id)
            if not session:
                session = self.session_manager.create_session(session_id)
            
            # Convert speech to text
            processed_audio = await self.audio_service.speech_to_text(audio_data)
            
            if not processed_audio.transcription:
                return {
                    "success": False,
                    "error": "Maaf, saya tidak dapat mendengar suara Anda dengan jelas. Silakan coba lagi.",
                    "session_id": session_id
                }
            
            # Add user input to session
            session.add_conversation_entry("user", processed_audio.transcription)
            
            # Get therapeutic response
            response = await self.ai_orchestrator.get_therapeutic_response(
                processed_audio.transcription,
                session.get_conversation_context(),
                session_id,
                self.system_prompt
            )
            
            # Add AI response to session
            session.add_conversation_entry("assistant", response.content)
            
            # Convert response to speech (always use parallel processing per user preference)
            response_audio = await self.audio_service.text_to_speech(response.content)
            
            # Update session
            self.session_manager.update_session(session)
            
            # Calculate latency
            latency = time.time() - start_time
            
            return {
                "success": True,
                "user_text": processed_audio.transcription,
                "ai_response": response.content,
                "audio_data": response_audio,
                "session_id": session_id,
                "latency": latency,
                "response_metrics": response.get_response_metrics()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Terjadi kesalahan dalam memproses permintaan Anda: {str(e)}",
                "session_id": session_id
            }
    
    async def process_text_therapy(
        self,
        user_input: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process text-based therapy interaction"""
        try:
            # Get or create session
            if not session_id:
                session_id = str(uuid4())
            
            session = self.session_manager.get_session(session_id)
            if not session:
                session = self.session_manager.create_session(session_id)
            
            # Add user input to session
            session.add_conversation_entry("user", user_input)
            
            # Get therapeutic response
            response = await self.ai_orchestrator.get_therapeutic_response(
                user_input,
                session.get_conversation_context(),
                session_id,
                self.system_prompt
            )
            
            # Add AI response to session
            session.add_conversation_entry("assistant", response.content)
            
            # Update session
            self.session_manager.update_session(session)
            
            return {
                "success": True,
                "response": response.content,
                "session_id": session_id,
                "response_metrics": response.get_response_metrics()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Terjadi kesalahan dalam memproses permintaan Anda: {str(e)}",
                "session_id": session_id
            }
    
    async def get_validated_response(
        self,
        user_input: str,
        session_id: Optional[str] = None
    ) -> ModelValidationResponse:
        """Get validated response from multiple models"""
        if not session_id:
            session_id = str(uuid4())
        
        session = self.session_manager.get_session(session_id)
        if not session:
            session = self.session_manager.create_session(session_id)
        
        return await self.ai_orchestrator.get_validated_response(
            user_input,
            session.get_conversation_context(),
            session_id,
            self.system_prompt
        )
    
    async def convert_text_to_speech(
        self,
        text: str,
        use_parallel: bool = True  # Always use parallel per user preference
    ) -> AudioData:
        """Convert text to speech with parallel processing"""
        return await self.audio_service.text_to_speech(text)
    
    async def convert_speech_to_text(
        self,
        audio_data: AudioData
    ) -> str:
        """Convert speech to text"""
        processed = await self.audio_service.speech_to_text(audio_data)
        return processed.transcription
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        session = self.session_manager.get_session(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "conversation_count": session.get_conversation_count(),
            "user_messages": session.get_user_messages_count(),
            "assistant_messages": session.get_assistant_messages_count(),
            "duration": session.get_session_duration(),
            "is_active": session.is_active(),
            "metadata": session.metadata
        }
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        return self.session_manager.delete_session(session_id)
    
    def list_sessions(self) -> list:
        """List all sessions"""
        return self.session_manager.list_sessions()
    
    def get_session_analysis(self, session_id: str) -> Dict[str, Any]:
        """Get session analysis"""
        return self.session_manager.get_session_analysis(session_id) 