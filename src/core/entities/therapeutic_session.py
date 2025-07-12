#!/usr/bin/env python3
"""
TherapeuticSession Entity - Domain model for therapy sessions
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4


@dataclass
class ConversationEntry:
    """Represents a single conversation entry"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TherapeuticSession:
    """
    Domain entity representing a therapeutic session
    """
    session_id: str = field(default_factory=lambda: str(uuid4()))
    conversation_history: List[ConversationEntry] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    max_conversation_length: int = 20
    trim_to_length: int = 15
    
    def add_conversation_entry(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add a new conversation entry"""
        entry = ConversationEntry(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.conversation_history.append(entry)
        self.last_activity = datetime.now()
        
        # Trim conversation if too long
        if len(self.conversation_history) > self.max_conversation_length:
            self.conversation_history = self.conversation_history[-self.trim_to_length:]
    
    def get_conversation_context(self) -> List[Dict[str, str]]:
        """Get conversation history formatted for AI models"""
        return [
            {"role": entry.role, "content": entry.content}
            for entry in self.conversation_history
        ]
    
    def get_session_duration(self) -> float:
        """Get session duration in seconds"""
        return (self.last_activity - self.created_at).total_seconds()
    
    def is_active(self, timeout_minutes: int = 30) -> bool:
        """Check if session is still active"""
        timeout_seconds = timeout_minutes * 60
        return (datetime.now() - self.last_activity).total_seconds() < timeout_seconds
    
    def get_conversation_count(self) -> int:
        """Get total number of conversation entries"""
        return len(self.conversation_history)
    
    def get_user_messages_count(self) -> int:
        """Get number of user messages"""
        return sum(1 for entry in self.conversation_history if entry.role == 'user')
    
    def get_assistant_messages_count(self) -> int:
        """Get number of assistant messages"""
        return sum(1 for entry in self.conversation_history if entry.role == 'assistant') 