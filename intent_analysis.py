#!/usr/bin/env python3
"""
Intent Analysis Module for Indonesian Mental Health Support Bot
Provides emotional state detection, therapeutic context understanding,
and safety mechanisms using OpenAI GPT-4.1-mini API.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmotionalState(Enum):
    """Emotional states that can be detected"""
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

class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TherapeuticContext(Enum):
    """Types of therapeutic contexts"""
    GENERAL_SUPPORT = "general_support"
    CRISIS_INTERVENTION = "crisis_intervention"
    CBT_TECHNIQUES = "cbt_techniques"
    ACTIVE_LISTENING = "active_listening"
    CULTURAL_TRAUMA = "cultural_trauma"
    SPIRITUAL_SUPPORT = "spiritual_support"
    FAMILY_DYNAMICS = "family_dynamics"
    GRIEF_COUNSELING = "grief_counseling"
    ANXIETY_MANAGEMENT = "anxiety_management"
    DEPRESSION_SUPPORT = "depression_support"
    RELATIONSHIP_ISSUES = "relationship_issues"
    WORKPLACE_STRESS = "workplace_stress"
    ACADEMIC_PRESSURE = "academic_pressure"

@dataclass
class IntentAnalysisResult:
    """Result of intent analysis"""
    # Emotional state detection
    primary_emotion: EmotionalState
    secondary_emotions: List[EmotionalState]
    emotion_intensity: float  # 0.0 to 1.0
    
    # Therapeutic context
    therapeutic_context: TherapeuticContext
    suggested_approach: str
    
    # Safety assessment
    suicide_risk: RiskLevel
    self_harm_risk: RiskLevel
    crisis_indicators: List[str]
    
    # Cultural context
    cultural_factors: List[str]
    spiritual_elements: List[str]
    
    # Therapeutic recommendations
    cbt_techniques: List[str]
    intervention_priority: str
    session_goals: List[str]
    
    # Metadata
    confidence_score: float  # 0.0 to 1.0
    requires_escalation: bool
    emergency_contact_needed: bool
    
    timestamp: datetime

class IntentAnalyzer:
    """
    Intent Analysis system for therapeutic conversations
    Uses OpenAI GPT-4.1-mini for sophisticated analysis
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the intent analyzer"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Crisis keywords for quick detection
        self.crisis_keywords = {
            'suicide': ['bunuh diri', 'ingin mati', 'mengakhiri hidup', 'tidak ingin hidup', 'suicide', 'kill myself'],
            'self_harm': ['melukai diri', 'menyakiti diri', 'self harm', 'cutting', 'memotong', 'menyilet'],
            'violence': ['menyakiti orang', 'membunuh', 'kekerasan', 'melukai'],
            'substance': ['obat-obatan', 'alkohol', 'narkoba', 'mabuk', 'overdosis'],
            'crisis': ['darurat', 'emergency', 'bantuan segera', 'tidak tahan lagi', 'putus asa']
        }
        
        # Cultural context indicators
        self.cultural_indicators = {
            'family': ['keluarga', 'orangtua', 'anak', 'suami', 'istri', 'kakak', 'adik', 'mertua'],
            'religion': ['allah', 'tuhan', 'doa', 'sholat', 'puasa', 'haji', 'umrah', 'masjid', 'gereja'],
            'social': ['masyarakat', 'tetangga', 'teman', 'sosial', 'komunitas', 'lingkungan'],
            'work': ['kerja', 'kantor', 'boss', 'atasan', 'gaji', 'pegawai', 'bisnis', 'usaha'],
            'education': ['sekolah', 'kuliah', 'ujian', 'nilai', 'guru', 'dosen', 'mahasiswa']
        }
        
        logger.info("Intent Analyzer initialized successfully")
    
    def analyze_intent(self, user_input: str, conversation_history: List[Dict] = None) -> IntentAnalysisResult:
        """
        Analyze user input for emotional state, therapeutic context, and safety
        
        Args:
            user_input: User's text input
            conversation_history: Previous conversation context
            
        Returns:
            IntentAnalysisResult with comprehensive analysis
        """
        try:
            # Quick crisis detection
            crisis_detected = self._quick_crisis_detection(user_input)
            
            # Prepare context for analysis
            context = self._prepare_analysis_context(user_input, conversation_history)
            
            # Get comprehensive analysis from GPT-4.1-mini
            analysis_result = self._get_gpt_analysis(context)
            
            # Process and structure the result
            intent_result = self._process_analysis_result(analysis_result, crisis_detected)
            
            logger.info(f"Intent analysis completed - Primary emotion: {intent_result.primary_emotion.value}, "
                       f"Context: {intent_result.therapeutic_context.value}, "
                       f"Risk level: {intent_result.suicide_risk.value}")
            
            return intent_result
            
        except Exception as e:
            logger.error(f"Error in intent analysis: {e}")
            # Return safe default result
            return self._create_safe_default_result()
    
    def _quick_crisis_detection(self, text: str) -> bool:
        """Quick keyword-based crisis detection"""
        text_lower = text.lower()
        
        for category, keywords in self.crisis_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    logger.warning(f"Crisis keyword detected: {keyword} in category {category}")
                    return True
        return False
    
    def _prepare_analysis_context(self, user_input: str, conversation_history: List[Dict] = None) -> str:
        """Prepare context for GPT analysis"""
        context = f"User Input: {user_input}\n\n"
        
        if conversation_history:
            context += "Recent Conversation:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                context += f"{role}: {content}\n"
        
        return context
    
    def _get_gpt_analysis(self, context: str) -> Dict:
        """Get analysis from GPT-4.1-mini"""
        system_prompt = """Anda adalah seorang psikolog klinis yang ahli dalam analisis emosi dan konteks terapeutik untuk budaya Indonesia. Analisis teks yang diberikan dan berikan hasil dalam format JSON yang mencakup:

1. EMOTIONAL STATE ANALYSIS:
   - primary_emotion: emosi utama (pilih dari: neutral, happy, sad, angry, anxious, depressed, fearful, frustrated, hopeful, overwhelmed, lonely, confused, guilty, ashamed, grieving)
   - secondary_emotions: emosi sekunder (array)
   - emotion_intensity: intensitas emosi (0.0-1.0)

2. THERAPEUTIC CONTEXT:
   - therapeutic_context: konteks terapeutik (pilih dari: general_support, crisis_intervention, cbt_techniques, active_listening, cultural_trauma, spiritual_support, family_dynamics, grief_counseling, anxiety_management, depression_support, relationship_issues, workplace_stress, academic_pressure)
   - suggested_approach: pendekatan yang disarankan

3. SAFETY ASSESSMENT:
   - suicide_risk: risiko bunuh diri (low, medium, high, critical)
   - self_harm_risk: risiko menyakiti diri (low, medium, high, critical)
   - crisis_indicators: indikator krisis (array)

4. CULTURAL CONTEXT:
   - cultural_factors: faktor budaya yang relevan (array)
   - spiritual_elements: elemen spiritual/religius (array)

5. THERAPEUTIC RECOMMENDATIONS:
   - cbt_techniques: teknik CBT yang cocok (array)
   - intervention_priority: prioritas intervensi (immediate, urgent, routine, low)
   - session_goals: tujuan sesi (array)

6. METADATA:
   - confidence_score: skor kepercayaan analisis (0.0-1.0)
   - requires_escalation: perlu eskalasi (true/false)
   - emergency_contact_needed: perlu kontak darurat (true/false)

Berikan analisis yang akurat, sensitif budaya, dan mempertimbangkan konteks Indonesia."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                max_tokens=1000,
                temperature=0.2  # Lower temperature for more consistent analysis
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                return json.loads(analysis_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, create structured response
                return self._parse_text_response(analysis_text)
                
        except Exception as e:
            logger.error(f"Error in GPT analysis: {e}")
            return self._create_fallback_analysis()
    
    def _parse_text_response(self, text: str) -> Dict:
        """Parse text response if JSON parsing fails"""
        # Basic parsing fallback
        return {
            "primary_emotion": "neutral",
            "secondary_emotions": [],
            "emotion_intensity": 0.5,
            "therapeutic_context": "general_support",
            "suggested_approach": "Active listening and empathetic response",
            "suicide_risk": "low",
            "self_harm_risk": "low",
            "crisis_indicators": [],
            "cultural_factors": [],
            "spiritual_elements": [],
            "cbt_techniques": [],
            "intervention_priority": "routine",
            "session_goals": ["Provide emotional support"],
            "confidence_score": 0.3,
            "requires_escalation": False,
            "emergency_contact_needed": False
        }
    
    def _create_fallback_analysis(self) -> Dict:
        """Create fallback analysis when GPT fails"""
        return {
            "primary_emotion": "neutral",
            "secondary_emotions": [],
            "emotion_intensity": 0.5,
            "therapeutic_context": "general_support",
            "suggested_approach": "Active listening and empathetic response",
            "suicide_risk": "low",
            "self_harm_risk": "low",
            "crisis_indicators": [],
            "cultural_factors": [],
            "spiritual_elements": [],
            "cbt_techniques": [],
            "intervention_priority": "routine",
            "session_goals": ["Provide emotional support"],
            "confidence_score": 0.1,
            "requires_escalation": False,
            "emergency_contact_needed": False
        }
    
    def _process_analysis_result(self, analysis: Dict, crisis_detected: bool = False) -> IntentAnalysisResult:
        """Process and validate analysis result"""
        try:
            # Handle enum conversions safely
            primary_emotion = EmotionalState(analysis.get("primary_emotion", "neutral"))
            secondary_emotions = [EmotionalState(e) for e in analysis.get("secondary_emotions", [])
                                if e in [state.value for state in EmotionalState]]
            
            therapeutic_context = TherapeuticContext(analysis.get("therapeutic_context", "general_support"))
            
            suicide_risk = RiskLevel(analysis.get("suicide_risk", "low"))
            self_harm_risk = RiskLevel(analysis.get("self_harm_risk", "low"))
            
            # Override risk levels if crisis detected
            if crisis_detected:
                suicide_risk = RiskLevel.HIGH
                self_harm_risk = RiskLevel.HIGH
            
            # Determine escalation needs
            requires_escalation = (
                crisis_detected or 
                suicide_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL] or
                self_harm_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL] or
                analysis.get("requires_escalation", False)
            )
            
            emergency_contact_needed = (
                suicide_risk == RiskLevel.CRITICAL or
                self_harm_risk == RiskLevel.CRITICAL or
                analysis.get("emergency_contact_needed", False)
            )
            
            return IntentAnalysisResult(
                primary_emotion=primary_emotion,
                secondary_emotions=secondary_emotions,
                emotion_intensity=max(0.0, min(1.0, analysis.get("emotion_intensity", 0.5))),
                therapeutic_context=therapeutic_context,
                suggested_approach=analysis.get("suggested_approach", "Active listening and empathetic response"),
                suicide_risk=suicide_risk,
                self_harm_risk=self_harm_risk,
                crisis_indicators=analysis.get("crisis_indicators", []),
                cultural_factors=analysis.get("cultural_factors", []),
                spiritual_elements=analysis.get("spiritual_elements", []),
                cbt_techniques=analysis.get("cbt_techniques", []),
                intervention_priority=analysis.get("intervention_priority", "routine"),
                session_goals=analysis.get("session_goals", ["Provide emotional support"]),
                confidence_score=max(0.0, min(1.0, analysis.get("confidence_score", 0.5))),
                requires_escalation=requires_escalation,
                emergency_contact_needed=emergency_contact_needed,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error processing analysis result: {e}")
            return self._create_safe_default_result()
    
    def _create_safe_default_result(self) -> IntentAnalysisResult:
        """Create safe default result for error cases"""
        return IntentAnalysisResult(
            primary_emotion=EmotionalState.NEUTRAL,
            secondary_emotions=[],
            emotion_intensity=0.5,
            therapeutic_context=TherapeuticContext.GENERAL_SUPPORT,
            suggested_approach="Active listening and empathetic response",
            suicide_risk=RiskLevel.LOW,
            self_harm_risk=RiskLevel.LOW,
            crisis_indicators=[],
            cultural_factors=[],
            spiritual_elements=[],
            cbt_techniques=[],
            intervention_priority="routine",
            session_goals=["Provide emotional support"],
            confidence_score=0.1,
            requires_escalation=False,
            emergency_contact_needed=False,
            timestamp=datetime.now()
        )
    
    def get_therapeutic_recommendations(self, intent_result: IntentAnalysisResult) -> Dict[str, Any]:
        """Get specific therapeutic recommendations based on analysis"""
        recommendations = {
            "immediate_actions": [],
            "therapeutic_techniques": [],
            "cultural_considerations": [],
            "safety_measures": [],
            "follow_up_actions": []
        }
        
        # Immediate actions based on risk level
        if intent_result.suicide_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations["immediate_actions"].extend([
                "Assess immediate safety",
                "Ask about specific suicide plans",
                "Provide crisis hotline numbers",
                "Encourage professional help"
            ])
        
        if intent_result.emergency_contact_needed:
            recommendations["immediate_actions"].append("Contact emergency services if immediate danger")
        
        # Therapeutic techniques based on context
        context_techniques = {
            TherapeuticContext.ANXIETY_MANAGEMENT: ["Deep breathing exercises", "Progressive muscle relaxation", "Grounding techniques"],
            TherapeuticContext.DEPRESSION_SUPPORT: ["Behavioral activation", "Mood monitoring", "Pleasant activity scheduling"],
            TherapeuticContext.CBT_TECHNIQUES: ["Thought challenging", "Cognitive restructuring", "Behavioral experiments"],
            TherapeuticContext.GRIEF_COUNSELING: ["Normalize grief process", "Memory preservation", "Meaning-making activities"],
            TherapeuticContext.CULTURAL_TRAUMA: ["Cultural validation", "Community connection", "Traditional healing integration"]
        }
        
        recommendations["therapeutic_techniques"] = context_techniques.get(intent_result.therapeutic_context, [])
        
        # Cultural considerations
        if intent_result.cultural_factors:
            recommendations["cultural_considerations"] = [
                "Respect family dynamics",
                "Consider religious/spiritual beliefs",
                "Understand cultural stigma around mental health",
                "Integrate traditional values with modern therapy"
            ]
        
        # Safety measures
        if intent_result.requires_escalation:
            recommendations["safety_measures"] = [
                "Regular check-ins",
                "Safety planning",
                "Professional referral",
                "Crisis contact information"
            ]
        
        return recommendations
    
    def format_analysis_summary(self, intent_result: IntentAnalysisResult) -> str:
        """Format analysis result into readable summary"""
        summary = f"""
🔍 ANALISIS INTENT:
• Emosi Utama: {intent_result.primary_emotion.value.title()} ({intent_result.emotion_intensity:.1%} intensitas)
• Konteks Terapeutik: {intent_result.therapeutic_context.value.replace('_', ' ').title()}
• Risiko Bunuh Diri: {intent_result.suicide_risk.value.upper()}
• Pendekatan Disarankan: {intent_result.suggested_approach}

🎯 REKOMENDASI:
• Prioritas: {intent_result.intervention_priority.upper()}
• Tujuan Sesi: {', '.join(intent_result.session_goals)}
• Teknik CBT: {', '.join(intent_result.cbt_techniques) if intent_result.cbt_techniques else 'Tidak diperlukan'}

⚠️ KEAMANAN:
• Perlu Eskalasi: {'YA' if intent_result.requires_escalation else 'TIDAK'}
• Kontak Darurat: {'YA' if intent_result.emergency_contact_needed else 'TIDAK'}
"""
        
        if intent_result.cultural_factors:
            summary += f"\n🌍 FAKTOR BUDAYA: {', '.join(intent_result.cultural_factors)}"
        
        if intent_result.spiritual_elements:
            summary += f"\n🕊️ ELEMEN SPIRITUAL: {', '.join(intent_result.spiritual_elements)}"
        
        return summary.strip() 