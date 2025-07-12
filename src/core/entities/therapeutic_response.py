#!/usr/bin/env python3
"""
TherapeuticResponse Entity - Domain model for therapeutic responses
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4
from enum import Enum


class AlertLevel(Enum):
    """Safety alert levels"""
    GREEN = "green"      # Normal operation
    YELLOW = "yellow"    # Monitor closely
    ORANGE = "orange"    # Elevated concern
    RED = "red"         # Immediate intervention


class EmotionType(Enum):
    """Detected emotion types"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    ANXIOUS = "anxious"
    DEPRESSED = "depressed"
    FEARFUL = "fearful"
    FRUSTRATED = "frustrated"
    HOPEFUL = "hopeful"
    OVERWHELMED = "overwhelmed"
    LONELY = "lonely"
    CONFUSED = "confused"
    GUILTY = "guilty"
    ASHAMED = "ashamed"
    GRIEVING = "grieving"


@dataclass
class EmotionAnalysis:
    """Analysis of detected emotions"""
    primary_emotion: EmotionType
    intensity: float  # 0.0 to 1.0
    secondary_emotions: List[EmotionType] = field(default_factory=list)
    confidence: float = 0.0
    
    def is_high_intensity(self, threshold: float = 0.7) -> bool:
        """Check if emotion has high intensity"""
        return self.intensity >= threshold
    
    def get_all_emotions(self) -> List[EmotionType]:
        """Get all detected emotions"""
        return [self.primary_emotion] + self.secondary_emotions


@dataclass
class SafetyAssessment:
    """Safety assessment results"""
    alert_level: AlertLevel
    risk_factors: List[str] = field(default_factory=list)
    protective_factors: List[str] = field(default_factory=list)
    keywords_detected: List[str] = field(default_factory=list)
    requires_intervention: bool = False
    requires_referral: bool = False
    
    def is_crisis_level(self) -> bool:
        """Check if this is a crisis level situation"""
        return self.alert_level == AlertLevel.RED
    
    def needs_monitoring(self) -> bool:
        """Check if situation needs monitoring"""
        return self.alert_level in [AlertLevel.YELLOW, AlertLevel.ORANGE, AlertLevel.RED]


@dataclass
class TherapeuticResponse:
    """
    Domain entity representing a therapeutic response from AI
    """
    response_id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    session_id: str = ""
    user_input: str = ""
    model_used: str = "gpt-4.1-nano"  # Preserving original model name
    emotion_analysis: Optional[EmotionAnalysis] = None
    safety_assessment: Optional[SafetyAssessment] = None
    processing_time: float = 0.0
    therapeutic_techniques: List[str] = field(default_factory=list)
    cultural_approaches: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_safe_response(self) -> bool:
        """Check if response is safe"""
        if not self.safety_assessment:
            return True
        return not self.safety_assessment.requires_intervention
    
    def requires_professional_help(self) -> bool:
        """Check if professional help is required"""
        if not self.safety_assessment:
            return False
        return self.safety_assessment.requires_referral
    
    def get_primary_emotion(self) -> Optional[EmotionType]:
        """Get primary detected emotion"""
        if self.emotion_analysis:
            return self.emotion_analysis.primary_emotion
        return None
    
    def get_emotion_intensity(self) -> float:
        """Get emotion intensity"""
        if self.emotion_analysis:
            return self.emotion_analysis.intensity
        return 0.0
    
    def add_therapeutic_technique(self, technique: str):
        """Add a therapeutic technique used"""
        if technique not in self.therapeutic_techniques:
            self.therapeutic_techniques.append(technique)
    
    def add_cultural_approach(self, approach: str):
        """Add a cultural approach used"""
        if approach not in self.cultural_approaches:
            self.cultural_approaches.append(approach)
    
    def get_response_metrics(self) -> Dict[str, Any]:
        """Get response metrics"""
        return {
            "response_id": self.response_id,
            "session_id": self.session_id,
            "model_used": self.model_used,
            "content_length": len(self.content),
            "processing_time": self.processing_time,
            "alert_level": self.safety_assessment.alert_level.value if self.safety_assessment else "unknown",
            "primary_emotion": self.get_primary_emotion().value if self.get_primary_emotion() else "unknown",
            "emotion_intensity": self.get_emotion_intensity(),
            "therapeutic_techniques": self.therapeutic_techniques,
            "cultural_approaches": self.cultural_approaches,
            "requires_intervention": self.safety_assessment.requires_intervention if self.safety_assessment else False,
            "requires_referral": self.safety_assessment.requires_referral if self.safety_assessment else False,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class ModelValidationResponse:
    """
    Domain entity for model validation responses (GPT vs Claude)
    """
    gpt_response: TherapeuticResponse
    claude_response: Optional[TherapeuticResponse] = None
    primary_response: Optional[TherapeuticResponse] = None
    validation_score: float = 0.0
    consensus_reached: bool = False
    discrepancies: List[str] = field(default_factory=list)
    
    def get_primary_or_fallback(self) -> TherapeuticResponse:
        """Get primary response or fallback"""
        if self.primary_response:
            return self.primary_response
        return self.gpt_response
    
    def has_claude_fallback(self) -> bool:
        """Check if Claude fallback is available"""
        return self.claude_response is not None 