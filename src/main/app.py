#!/usr/bin/env python3
"""
Main Application Composition Root - Dependency Injection Setup
"""

from typing import Dict, Any
from ..core.use_cases.therapy_interaction import TherapyInteractionUseCase
from ..infrastructure.ai_services.ai_orchestrator import AIOrchestrator
from ..infrastructure.audio_services.audio_service import AudioService
from ..infrastructure.session_services.session_manager import SessionManager
from ..infrastructure.config.settings import settings


class Application:
    """Main application composition root"""
    
    def __init__(self):
        self._initialize_dependencies()
        self._create_use_cases()
        
    def _initialize_dependencies(self):
        """Initialize all dependencies with dependency injection"""
        print("🚀 Initializing Indonesian Mental Health Support Bot (Clean Architecture)")
        print("💚 Menginisialisasi Bot Dukungan Kesehatan Mental Indonesia (Arsitektur Bersih)")
        
        # Initialize infrastructure services
        self.ai_orchestrator = AIOrchestrator()
        self.audio_service = AudioService(settings.api_config.openai_api_key)
        self.session_manager = SessionManager()
        
        # Validate API keys
        api_status = settings.validate_api_keys()
        if not api_status["openai_available"]:
            raise ValueError("OpenAI API key is required. Please set OPENAI_API_KEY environment variable.")
        
        if api_status["anthropic_available"]:
            print("✅ Both OpenAI and Anthropic API keys available")
        else:
            print("⚠️  Only OpenAI API key available - Claude fallback disabled")
    
    def _create_use_cases(self):
        """Create use cases with injected dependencies"""
        self.therapy_interaction_use_case = TherapyInteractionUseCase(
            ai_orchestrator=self.ai_orchestrator,
            audio_service=self.audio_service,
            session_manager=self.session_manager,
            system_prompt=settings.system_prompt
        )
        
        print("🧠 Therapy interaction use case initialized")
        print("💚 Use case interaksi terapi diinisialisasi")
    
    def get_therapy_use_case(self) -> TherapyInteractionUseCase:
        """Get therapy interaction use case"""
        return self.therapy_interaction_use_case
    
    def get_ai_orchestrator(self) -> AIOrchestrator:
        """Get AI orchestrator"""
        return self.ai_orchestrator
    
    def get_audio_service(self) -> AudioService:
        """Get audio service"""
        return self.audio_service
    
    def get_session_manager(self) -> SessionManager:
        """Get session manager"""
        return self.session_manager
    
    def get_system_prompt(self) -> str:
        """Get system prompt"""
        return settings.system_prompt
    
    def get_crisis_resources(self) -> Dict[str, Any]:
        """Get crisis resources"""
        return settings.get_crisis_resources()
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "ai_services": self.ai_orchestrator.get_service_status(),
            "audio_service": self.audio_service.is_available(),
            "session_manager": len(self.session_manager.list_sessions()),
            "api_keys": settings.validate_api_keys(),
            "model_config": {
                "primary_model": settings.model_config.primary_model,
                "fallback_model": settings.model_config.fallback_model,
                "temperature": settings.model_config.temperature,
                "max_tokens": settings.model_config.max_tokens
            },
            "audio_config": {
                "default_format": settings.audio_config.default_format,
                "use_parallel_tts": settings.audio_config.use_parallel_tts,
                "max_workers": settings.audio_config.max_workers
            }
        }
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            # Cleanup inactive sessions
            cleaned_sessions = self.session_manager.cleanup_inactive_sessions(
                settings.session_config.session_timeout_minutes
            )
            
            if cleaned_sessions > 0:
                print(f"🧹 Cleaned up {cleaned_sessions} inactive sessions")
            
            print("✅ Application cleanup completed")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")


# Global application instance
app = Application() 