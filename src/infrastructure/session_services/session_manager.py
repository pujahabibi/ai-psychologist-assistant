#!/usr/bin/env python3
"""
Session Manager Implementation - In-memory session management
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ...core.interfaces.session_service import ISessionManager, IConsentManager
from ...core.entities.therapeutic_session import TherapeuticSession
from ...infrastructure.config.settings import settings


class SessionManager(ISessionManager):
    """Session manager implementation using in-memory storage"""
    
    def __init__(self):
        self.sessions: Dict[str, TherapeuticSession] = {}
        self.consent_manager = ConsentManager()
        
    def create_session(self, session_id: Optional[str] = None) -> TherapeuticSession:
        """Create a new session"""
        session = TherapeuticSession(
            session_id=session_id,
            max_conversation_length=settings.session_config.max_conversation_length,
            trim_to_length=settings.session_config.trim_to_length
        )
        
        self.sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[TherapeuticSession]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def update_session(self, session: TherapeuticSession) -> bool:
        """Update session"""
        try:
            self.sessions[session.session_id] = session
            return True
        except Exception as e:
            print(f"Error updating session {session.session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
    
    def list_sessions(self) -> List[str]:
        """List all session IDs"""
        return list(self.sessions.keys())
    
    def get_session_analysis(self, session_id: str) -> Dict[str, Any]:
        """Get session analysis"""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "duration_minutes": session.get_session_duration() / 60,
            "total_messages": session.get_conversation_count(),
            "user_messages": session.get_user_messages_count(),
            "assistant_messages": session.get_assistant_messages_count(),
            "is_active": session.is_active(settings.session_config.session_timeout_minutes),
            "conversation_history": session.get_conversation_context(),
            "metadata": session.metadata
        }
    
    def cleanup_inactive_sessions(self, timeout_minutes: int = 30) -> int:
        """Clean up inactive sessions"""
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
        inactive_sessions = []
        
        for session_id, session in self.sessions.items():
            if session.last_activity < cutoff_time:
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            del self.sessions[session_id]
        
        return len(inactive_sessions)
    
    def get_consent_manager(self) -> IConsentManager:
        """Get consent manager"""
        return self.consent_manager


class ConsentManager(IConsentManager):
    """Consent manager implementation"""
    
    def __init__(self):
        self.consent_records: Dict[str, Dict[str, Any]] = {}
    
    def record_consent(
        self,
        session_id: str,
        ip_address: str,
        consent_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record user consent"""
        consent_record = {
            "session_id": session_id,
            "ip_address": ip_address,
            "timestamp": datetime.now().isoformat(),
            "consent_given": consent_data.get("consent_given", True),
            "recording_consent": consent_data.get("recording_consent", False),
            "data_sharing_consent": consent_data.get("data_sharing_consent", False),
            "anonymization_level": consent_data.get("anonymization_level", "high"),
            "retention_period": consent_data.get("retention_period", 30)
        }
        
        self.consent_records[session_id] = consent_record
        return consent_record
    
    def get_consent_record(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get consent record"""
        return self.consent_records.get(session_id)
    
    def is_consent_valid(self, session_id: str) -> bool:
        """Check if consent is valid"""
        consent_record = self.consent_records.get(session_id)
        if not consent_record:
            return False
        
        # Check if consent was given
        if not consent_record.get("consent_given", False):
            return False
        
        # Check if consent is still within retention period
        consent_time = datetime.fromisoformat(consent_record["timestamp"])
        retention_days = consent_record.get("retention_period", 30)
        expiry_time = consent_time + timedelta(days=retention_days)
        
        return datetime.now() < expiry_time 