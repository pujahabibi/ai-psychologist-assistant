#!/usr/bin/env python3
"""
AI Orchestrator - Manages multiple AI services with fallback logic
"""

from typing import List, Dict, Optional, AsyncGenerator
from ...core.interfaces.ai_service import IAIOrchestrator
from ...core.entities.therapeutic_response import TherapeuticResponse, ModelValidationResponse
from .gpt_service import GPTService
from .claude_service import ClaudeService
from ...infrastructure.config.settings import settings


class AIOrchestrator(IAIOrchestrator):
    """AI orchestrator that manages multiple AI services"""
    
    def __init__(self):
        # Initialize services
        self.gpt_service = GPTService(settings.api_config.openai_api_key)
        self.claude_service = ClaudeService(settings.api_config.anthropic_api_key)
        
        print("🧠 AI Orchestrator initialized")
        if self.gpt_service.is_available():
            print(f"✅ GPT ({settings.model_config.primary_model}) available")
        else:
            print("❌ GPT service not available")
        
        if self.claude_service.is_available():
            print(f"✅ Claude ({settings.model_config.fallback_model}) available")
        else:
            print("❌ Claude service not available")
    
    async def get_therapeutic_response(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]],
        session_id: str,
        system_prompt: str
    ) -> TherapeuticResponse:
        """Get therapeutic response with fallback logic"""
        # Try GPT first
        if self.gpt_service.is_available():
            try:
                response = await self.gpt_service.generate_therapeutic_response(
                    user_input, conversation_history, session_id, system_prompt
                )
                
                # Check if GPT response was successful
                if response.model_used != "error":
                    print(f"✅ GPT-4.1 response generated for session {session_id}")
                    return response
                else:
                    print(f"⚠️ GPT-4.1 failed for session {session_id}")
                    
            except Exception as e:
                print(f"⚠️ GPT-4.1 error for session {session_id}: {e}")
        
        # Fallback to Claude
        if self.claude_service.is_available():
            try:
                print(f"🔄 Falling back to Claude 3.5 Sonnet for session {session_id}")
                response = await self.claude_service.generate_therapeutic_response(
                    user_input, conversation_history, session_id, system_prompt
                )
                
                if response.model_used != "error":
                    print(f"✅ Claude 3.5 Sonnet response generated for session {session_id}")
                    return response
                else:
                    print(f"❌ Claude fallback also failed for session {session_id}")
                    
            except Exception as e:
                print(f"❌ Claude fallback error for session {session_id}: {e}")
        
        # If both failed, return error response
        print(f"❌ All AI services failed for session {session_id}")
        return TherapeuticResponse(
            content="Maaf, saya sedang mengalami gangguan teknis. Bisakah Anda ulangi yang tadi?",
            session_id=session_id,
            user_input=user_input,
            model_used="error"
        )

    async def get_streaming_therapeutic_response(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]],
        session_id: str,
        system_prompt: str
    ) -> AsyncGenerator[str, None]:
        """Get streaming therapeutic response with fallback logic"""
        # Try GPT first for streaming
        if self.gpt_service.is_available():
            try:
                print(f"🔄 Starting streaming GPT-4.1 response for session {session_id}")
                async for chunk in self.gpt_service.generate_streaming_therapeutic_response(
                    user_input, conversation_history, session_id, system_prompt
                ):
                    yield chunk
                
                print(f"✅ Streaming GPT-4.1 response completed for session {session_id}")
                return
                
            except Exception as e:
                print(f"⚠️ Streaming GPT-4.1 error for session {session_id}: {e}")
        
        # Fallback to Claude (non-streaming for now)
        if self.claude_service.is_available():
            try:
                print(f"🔄 Falling back to Claude 3.5 Sonnet (non-streaming) for session {session_id}")
                response = await self.claude_service.generate_therapeutic_response(
                    user_input, conversation_history, session_id, system_prompt
                )
                
                if response.model_used != "error":
                    print(f"✅ Claude 3.5 Sonnet response generated for session {session_id}")
                    yield response.content
                else:
                    print(f"❌ Claude fallback also failed for session {session_id}")
                    yield "Maaf, saya sedang mengalami gangguan teknis. Bisakah Anda ulangi yang tadi?"
                    
            except Exception as e:
                print(f"❌ Claude fallback error for session {session_id}: {e}")
                yield "Maaf, saya sedang mengalami gangguan teknis. Bisakah Anda ulangi yang tadi?"
        else:
            # If both failed, return error response
            print(f"❌ All AI services failed for session {session_id}")
            yield "Maaf, saya sedang mengalami gangguan teknis. Bisakah Anda ulangi yang tadi?"
    
    async def get_validated_response(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]],
        session_id: str,
        system_prompt: str
    ) -> ModelValidationResponse:
        """Get validated response from both models"""
        gpt_response = None
        claude_response = None
        
        # Try GPT
        if self.gpt_service.is_available():
            try:
                gpt_response = await self.gpt_service.generate_therapeutic_response(
                    user_input, conversation_history, session_id, system_prompt
                )
            except Exception as e:
                print(f"Error getting GPT response: {e}")
        
        # Try Claude
        if self.claude_service.is_available():
            try:
                claude_response = await self.claude_service.generate_therapeutic_response(
                    user_input, conversation_history, session_id, system_prompt
                )
            except Exception as e:
                print(f"Error getting Claude response: {e}")
        
        # Determine primary response
        primary_response = None
        if gpt_response and gpt_response.model_used != "error":
            primary_response = gpt_response
        elif claude_response and claude_response.model_used != "error":
            primary_response = claude_response
        
        return ModelValidationResponse(
            gpt_response=gpt_response,
            claude_response=claude_response,
            primary_response=primary_response,
            consensus_reached=self._check_consensus(gpt_response, claude_response)
        )
    
    def _check_consensus(self, gpt_response: TherapeuticResponse, claude_response: TherapeuticResponse) -> bool:
        """Check if both models reached consensus"""
        if not gpt_response or not claude_response:
            return False
        
        if gpt_response.model_used == "error" or claude_response.model_used == "error":
            return False
        
        # Simple consensus check based on response length similarity
        gpt_length = len(gpt_response.content.split())
        claude_length = len(claude_response.content.split())
        
        # Consider consensus if responses are within 50% length difference
        length_ratio = min(gpt_length, claude_length) / max(gpt_length, claude_length)
        return length_ratio > 0.5
    
    def get_service_status(self) -> Dict[str, bool]:
        """Get status of all services"""
        return {
            "gpt_available": self.gpt_service.is_available(),
            "claude_available": self.claude_service.is_available(),
            "gpt_model": self.gpt_service.get_model_name(),
            "claude_model": self.claude_service.get_model_name()
        } 