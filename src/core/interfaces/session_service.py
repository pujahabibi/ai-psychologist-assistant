#!/usr/bin/env python3
"""
Session Service Interfaces - Contracts for session management
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from ..entities.therapeutic_session import TherapeuticSession


class ISessionManager(ABC):
    """Interface for session management"""
    
    @abstractmethod
    def create_session(self, session_id: Optional[str] = None) -> TherapeuticSession:
        """Create a new session"""
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[TherapeuticSession]:
        """Get session by ID"""
        pass
    
    @abstractmethod
    def update_session(self, session: TherapeuticSession) -> bool:
        """Update session"""
        pass
    
    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        pass
    
    @abstractmethod
    def list_sessions(self) -> List[str]:
        """List all session IDs"""
        pass
    
    @abstractmethod
    def get_session_analysis(self, session_id: str) -> Dict[str, Any]:
        """Get session analysis"""
        pass
    
    @abstractmethod
    def cleanup_inactive_sessions(self, timeout_minutes: int = 30) -> int:
        """Clean up inactive sessions"""
        pass


class ISessionStorage(ABC):
    """Interface for session storage"""
    
    @abstractmethod
    def store_session(self, session: TherapeuticSession) -> bool:
        """Store session"""
        pass
    
    @abstractmethod
    def retrieve_session(self, session_id: str) -> Optional[TherapeuticSession]:
        """Retrieve session"""
        pass
    
    @abstractmethod
    def remove_session(self, session_id: str) -> bool:
        """Remove session"""
        pass
    
    @abstractmethod
    def list_all_sessions(self) -> List[str]:
        """List all stored sessions"""
        pass


class IConsentManager(ABC):
    """Interface for consent management"""
    
    @abstractmethod
    def record_consent(
        self,
        session_id: str,
        ip_address: str,
        consent_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record user consent"""
        pass
    
    @abstractmethod
    def get_consent_record(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get consent record"""
        pass
    
    @abstractmethod
    def is_consent_valid(self, session_id: str) -> bool:
        """Check if consent is valid"""
        pass 