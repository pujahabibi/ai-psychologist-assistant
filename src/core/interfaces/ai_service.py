#!/usr/bin/env python3
"""
AI Service Interfaces - Contracts for AI model services
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, AsyncGenerator
from ..entities.therapeutic_response import TherapeuticResponse, ModelValidationResponse


class IAIModelService(ABC):
    """Interface for AI model services"""
    
    @abstractmethod
    async def generate_therapeutic_response(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]],
        session_id: str,
        system_prompt: str
    ) -> TherapeuticResponse:
        """Generate therapeutic response"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if service is available"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get model name"""
        pass


class IGPTService(IAIModelService):
    """Interface for GPT service"""
    
    @abstractmethod
    async def generate_therapeutic_response(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]],
        session_id: str,
        system_prompt: str
    ) -> TherapeuticResponse:
        """Generate therapeutic response using GPT"""
        pass

    @abstractmethod
    async def generate_streaming_therapeutic_response(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]],
        session_id: str,
        system_prompt: str
    ) -> AsyncGenerator[str, None]:
        """Generate streaming therapeutic response using GPT"""
        pass


class IClaudeService(IAIModelService):
    """Interface for Claude service"""
    
    @abstractmethod
    async def generate_therapeutic_response(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]],
        session_id: str,
        system_prompt: str
    ) -> TherapeuticResponse:
        """Generate therapeutic response using Claude"""
        pass


class IAIOrchestrator(ABC):
    """Interface for AI orchestrator that manages multiple AI services"""
    
    @abstractmethod
    async def get_therapeutic_response(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]],
        session_id: str,
        system_prompt: str
    ) -> TherapeuticResponse:
        """Get therapeutic response with fallback logic"""
        pass
    
    @abstractmethod
    async def get_validated_response(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]],
        session_id: str,
        system_prompt: str
    ) -> ModelValidationResponse:
        """Get validated response from multiple models"""
        pass

    @abstractmethod
    async def get_streaming_therapeutic_response(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]],
        session_id: str,
        system_prompt: str
    ) -> AsyncGenerator[str, None]:
        """Get streaming therapeutic response with fallback logic"""
        pass 