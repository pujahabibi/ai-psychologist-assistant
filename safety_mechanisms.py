#!/usr/bin/env python3
"""
Safety Mechanisms Module for Indonesian Mental Health Support Bot
Implements suicide risk assessment, harmful content detection, professional referral triggers,
session recording consent, data protection, and emergency contact integration.
"""

import os
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from openai import OpenAI
from dotenv import load_dotenv

from intent_analysis import IntentAnalysisResult, RiskLevel

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert levels for safety mechanisms"""
    GREEN = "green"      # Normal operation
    YELLOW = "yellow"    # Monitor closely
    ORANGE = "orange"    # Elevated concern
    RED = "red"         # Immediate intervention needed

class ContentType(Enum):
    """Types of harmful content"""
    SUICIDE_IDEATION = "suicide_ideation"
    SELF_HARM = "self_harm"
    VIOLENCE_THREAT = "violence_threat"
    SUBSTANCE_ABUSE = "substance_abuse"
    CHILD_ABUSE = "child_abuse"
    DOMESTIC_VIOLENCE = "domestic_violence"
    SEXUAL_CONTENT = "sexual_content"
    HATE_SPEECH = "hate_speech"
    SPAM = "spam"
    INAPPROPRIATE = "inappropriate"

class ReferralTrigger(Enum):
    """Triggers for professional referral"""
    PERSISTENT_SUICIDAL_IDEATION = "persistent_suicidal_ideation"
    ACTIVE_PSYCHOSIS = "active_psychosis"
    SEVERE_DEPRESSION = "severe_depression"
    SUBSTANCE_DEPENDENCY = "substance_dependency"
    DOMESTIC_VIOLENCE = "domestic_violence"
    CHILD_ENDANGERMENT = "child_endangerment"
    EATING_DISORDER = "eating_disorder"
    TRAUMA_RESPONSE = "trauma_response"
    MEDICATION_CONCERNS = "medication_concerns"
    BEYOND_AI_SCOPE = "beyond_ai_scope"

@dataclass
class SafetyAssessment:
    """Safety assessment result"""
    alert_level: AlertLevel
    risk_factors: List[str]
    protective_factors: List[str]
    immediate_actions: List[str]
    referral_needed: bool
    referral_triggers: List[ReferralTrigger]
    emergency_contact: bool
    session_monitoring: bool
    data_protection_notes: List[str]
    timestamp: datetime

@dataclass
class ContentFilterResult:
    """Result of content filtering"""
    is_harmful: bool
    content_types: List[ContentType]
    severity_score: float  # 0.0 to 1.0
    blocked_content: bool
    warning_message: Optional[str]
    escalation_required: bool
    timestamp: datetime

@dataclass
class SessionConsent:
    """Session consent and data protection"""
    consent_given: bool
    recording_consent: bool
    data_sharing_consent: bool
    anonymization_level: str
    retention_period: int  # days
    consent_timestamp: datetime
    ip_hash: str
    session_id: str

class SafetyMechanisms:
    """
    Comprehensive safety mechanisms for therapeutic conversations
    """
    
    def __init__(self, api_key: str = None):
        """Initialize safety mechanisms"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Emergency contacts and resources
        self.emergency_contacts = {
            "police": "110",
            "medical_emergency": "118",
            "fire_department": "113",
            "suicide_prevention": "119",
            "mental_health_crisis": "500-454",
            "women_crisis": "021-7270005",
            "child_protection": "129",
            "domestic_violence": "021-3448245",
            "substance_abuse": "021-7256526"
        }
        
        # Professional referral resources
        self.referral_resources = {
            "psychiatrist": "Dokter Spesialis Jiwa",
            "psychologist": "Psikolog Klinis",
            "counselor": "Konselor Berlisensi",
            "social_worker": "Pekerja Sosial",
            "hospital_emergency": "Unit Gawat Darurat Rumah Sakit",
            "mental_health_clinic": "Klinik Kesehatan Mental",
            "community_health": "Puskesmas"
        }
        
        # Risk assessment patterns
        self.risk_patterns = {
            "high_risk": [
                "ingin mati", "bunuh diri", "mengakhiri hidup", "tidak ingin hidup lagi",
                "suicide", "kill myself", "end my life", "want to die",
                "menyerah total", "tak sanggup bertahan", "lebih baik mati", "life is pointless",
                "ingin mengakhiri semuanya", "tidak mau hidup", "hidup tak berarti", "mati saja",
                "tidak ada gunanya hidup", "suicidal thoughts", "death wish", "better off dead",
                "no reason to live", "can't go on anymore"
            ],
            "medium_risk": [
                "tidak tahan lagi", "putus asa", "hopeless", "tidak ada harapan",
                "lelah hidup", "tired of living", "give up",
                "kehilangan arah", "merasa hampa", "meaningless", "tidak berguna",
                "hidup terasa berat", "tidak ada jalan keluar", "semua sia-sia", "tertekan berat",
                "tidak berdaya", "overwhelmed", "no way out", "life is too hard",
                "can't see a future", "everything is pointless"
            ],
            "self_harm": [
                "melukai diri", "menyakiti diri", "cutting", "self harm",
                "memotong", "menyilet", "hurt myself",
                "mencederai tubuh", "self-injury", "merusak diri", "menyayat",
                "menggores kulit", "membakar diri", "menyiksa diri", "memar sengaja",
                "melukai tubuh sendiri", "self-mutilation", "burning myself", "hitting myself",
                "intentional injury", "harming my body"
            ],
            "violence": [
                "menyakiti orang", "membunuh", "kekerasan", "melukai",
                "hurt someone", "kill", "violence", "harm others",
                "menyerang", "mengancam", "assault", "menghancurkan",
                "memukul orang", "menyiksa", "ingin melukai", "membuat orang menderita",
                "dendam kesumat", "physical attack", "threatening others", "causing pain",
                "violent thoughts", "destructive urges"
            ]
        }
        
        # Content filtering patterns
        self.harmful_patterns = {
            "explicit_sexual": [
                "pornografi", "seks eksplisit", "organ intim", "hubungan seksual detail",
                "cabul", "mesum", "telanjang", "vulgar", "bercinta", "birahi",
                "nafsu", "porno", "bugil", "intim", "sensual"
            ],
            "hate_speech": [
                "benci", "diskriminasi", "rasisme", "hate", "discrimination",
                "menghina", "merendahkan", "menyudutkan", "rasis", "stereotip",
                "prasangka", "xenofobia", "intoleran", "menghasut", "memfitnah"
            ],
            "spam": [
                "promo", "diskon", "gratis", "menang", "hadiah",
                "investasi", "kaya", "cepat", "untung", "bonus",
                "penawaran", "terbatas", "eksklusif", "murah", "kesempatan"
            ]
        }
        
        logger.info("Safety Mechanisms initialized successfully")
    
    def assess_safety(self, 
                     user_input: str, 
                     intent_result: IntentAnalysisResult,
                     conversation_history: List[Dict] = None,
                     session_id: str = None) -> SafetyAssessment:
        """
        Comprehensive safety assessment
        
        Args:
            user_input: User's input text
            intent_result: Intent analysis result
            conversation_history: Previous conversation
            session_id: Session identifier
            
        Returns:
            SafetyAssessment with risk evaluation
        """
        try:
            # Determine alert level
            alert_level = self._determine_alert_level(intent_result)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(user_input, intent_result, conversation_history)
            
            # Identify protective factors
            protective_factors = self._identify_protective_factors(user_input, intent_result, conversation_history)
            
            # Determine immediate actions
            immediate_actions = self._determine_immediate_actions(alert_level, risk_factors)
            
            # Assess referral needs
            referral_needed, referral_triggers = self._assess_referral_needs(intent_result, risk_factors)
            
            # Emergency contact determination
            emergency_contact = self._needs_emergency_contact(alert_level, risk_factors)
            
            # Session monitoring needs
            session_monitoring = self._needs_session_monitoring(alert_level, risk_factors)
            
            # Data protection considerations
            data_protection_notes = self._get_data_protection_notes(alert_level, risk_factors)
            
            return SafetyAssessment(
                alert_level=alert_level,
                risk_factors=risk_factors,
                protective_factors=protective_factors,
                immediate_actions=immediate_actions,
                referral_needed=referral_needed,
                referral_triggers=referral_triggers,
                emergency_contact=emergency_contact,
                session_monitoring=session_monitoring,
                data_protection_notes=data_protection_notes,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in safety assessment: {e}")
            return self._create_safe_assessment()
    
    def filter_content(self, user_input: str, session_id: str = None) -> ContentFilterResult:
        """
        Filter content for harmful material
        
        Args:
            user_input: User's input text
            session_id: Session identifier
            
        Returns:
            ContentFilterResult with filtering decision
        """
        try:
            # Quick pattern matching
            is_harmful, content_types, severity_score = self._quick_content_check(user_input)
            
            # Advanced content analysis using GPT
            if severity_score > 0.3:  # Threshold for advanced analysis
                advanced_result = self._advanced_content_analysis(user_input)
                if advanced_result:
                    is_harmful = advanced_result.get("is_harmful", is_harmful)
                    severity_score = max(severity_score, advanced_result.get("severity", 0))
            
            # Determine if content should be blocked
            blocked_content = is_harmful and severity_score > 0.7
            
            # Generate warning message
            warning_message = self._generate_warning_message(content_types) if is_harmful else None
            
            # Determine escalation needs
            escalation_required = severity_score > 0.8 or ContentType.VIOLENCE_THREAT in content_types
            
            # Log harmful content
            if is_harmful:
                logger.warning(f"Harmful content detected: {content_types}, severity: {severity_score:.2f}")
            
            return ContentFilterResult(
                is_harmful=is_harmful,
                content_types=content_types,
                severity_score=severity_score,
                blocked_content=blocked_content,
                warning_message=warning_message,
                escalation_required=escalation_required,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in content filtering: {e}")
            return self._create_safe_filter_result()
    
    def create_session_consent(self, 
                              session_id: str, 
                              ip_address: str,
                              consent_data: Dict[str, Any]) -> SessionConsent:
        """
        Create session consent record
        
        Args:
            session_id: Session identifier
            ip_address: User's IP address
            consent_data: Consent preferences
            
        Returns:
            SessionConsent record
        """
        try:
            # Hash IP address for privacy
            ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16]
            
            # Default consent settings
            consent_given = consent_data.get("consent_given", False)
            recording_consent = consent_data.get("recording_consent", False)
            data_sharing_consent = consent_data.get("data_sharing_consent", False)
            anonymization_level = consent_data.get("anonymization_level", "high")
            retention_period = consent_data.get("retention_period", 30)  # 30 days default
            
            consent_record = SessionConsent(
                consent_given=consent_given,
                recording_consent=recording_consent,
                data_sharing_consent=data_sharing_consent,
                anonymization_level=anonymization_level,
                retention_period=retention_period,
                consent_timestamp=datetime.now(),
                ip_hash=ip_hash,
                session_id=session_id
            )
            
            logger.info(f"Session consent created for {session_id}")
            return consent_record
            
        except Exception as e:
            logger.error(f"Error creating session consent: {e}")
            return self._create_default_consent(session_id)
    
    def check_data_retention(self, consent_record: SessionConsent) -> Dict[str, Any]:
        """
        Check data retention compliance
        
        Args:
            consent_record: Session consent record
            
        Returns:
            Retention status and actions
        """
        try:
            now = datetime.now()
            session_age = (now - consent_record.consent_timestamp).days
            
            retention_status = {
                "session_age_days": session_age,
                "retention_limit_days": consent_record.retention_period,
                "within_retention": session_age <= consent_record.retention_period,
                "action_required": False,
                "recommended_action": "none"
            }
            
            if session_age > consent_record.retention_period:
                retention_status["action_required"] = True
                retention_status["recommended_action"] = "delete_or_anonymize"
            elif session_age > (consent_record.retention_period * 0.8):
                retention_status["action_required"] = True
                retention_status["recommended_action"] = "notify_expiration"
            
            return retention_status
            
        except Exception as e:
            logger.error(f"Error checking data retention: {e}")
            return {"error": "retention_check_failed"}
    
    def get_emergency_response_plan(self, safety_assessment: SafetyAssessment) -> Dict[str, Any]:
        """
        Get emergency response plan based on safety assessment
        
        Args:
            safety_assessment: Safety assessment result
            
        Returns:
            Emergency response plan
        """
        response_plan = {
            "immediate_actions": safety_assessment.immediate_actions,
            "emergency_contacts": [],
            "referral_resources": [],
            "follow_up_schedule": [],
            "documentation_needs": []
        }
        
        # Emergency contacts based on alert level
        if safety_assessment.alert_level == AlertLevel.RED:
            response_plan["emergency_contacts"] = [
                {"name": "Pencegahan Bunuh Diri", "number": "119", "priority": "high"},
                {"name": "Gawat Darurat", "number": "118", "priority": "high"},
                {"name": "Polisi", "number": "110", "priority": "medium"}
            ]
        elif safety_assessment.alert_level == AlertLevel.ORANGE:
            response_plan["emergency_contacts"] = [
                {"name": "Crisis Mental Health", "number": "500-454", "priority": "high"},
                {"name": "Pencegahan Bunuh Diri", "number": "119", "priority": "medium"}
            ]
        
        # Referral resources based on triggers
        for trigger in safety_assessment.referral_triggers:
            if trigger == ReferralTrigger.PERSISTENT_SUICIDAL_IDEATION:
                response_plan["referral_resources"].append(
                    {"type": "psychiatrist", "urgency": "immediate", "notes": "Suicidal ideation assessment"}
                )
            elif trigger == ReferralTrigger.SEVERE_DEPRESSION:
                response_plan["referral_resources"].append(
                    {"type": "psychologist", "urgency": "urgent", "notes": "Depression evaluation"}
                )
            elif trigger == ReferralTrigger.SUBSTANCE_DEPENDENCY:
                response_plan["referral_resources"].append(
                    {"type": "addiction_counselor", "urgency": "routine", "notes": "Substance abuse treatment"}
                )
        
        # Follow-up schedule
        if safety_assessment.session_monitoring:
            response_plan["follow_up_schedule"] = [
                {"interval": "24_hours", "method": "automated_check"},
                {"interval": "72_hours", "method": "human_review"},
                {"interval": "1_week", "method": "progress_assessment"}
            ]
        
        # Documentation requirements
        if safety_assessment.alert_level in [AlertLevel.ORANGE, AlertLevel.RED]:
            response_plan["documentation_needs"] = [
                "detailed_session_notes",
                "risk_assessment_form",
                "safety_plan_creation",
                "referral_documentation"
            ]
        
        return response_plan
    
    def _determine_alert_level(self, intent_result: IntentAnalysisResult) -> AlertLevel:
        """Determine alert level based on intent analysis"""
        
        if intent_result.suicide_risk == RiskLevel.CRITICAL or intent_result.emergency_contact_needed:
            return AlertLevel.RED
        elif intent_result.suicide_risk == RiskLevel.HIGH or intent_result.requires_escalation:
            return AlertLevel.ORANGE
        elif intent_result.suicide_risk == RiskLevel.MEDIUM or intent_result.self_harm_risk == RiskLevel.HIGH:
            return AlertLevel.YELLOW
        else:
            return AlertLevel.GREEN
    
    def _identify_risk_factors(self, 
                             user_input: str, 
                             intent_result: IntentAnalysisResult,
                             conversation_history: List[Dict] = None) -> List[str]:
        """Identify risk factors from input and context"""
        
        risk_factors = []
        
        # Risk factors from intent analysis
        if intent_result.suicide_risk != RiskLevel.LOW:
            risk_factors.append(f"Suicide risk: {intent_result.suicide_risk.value}")
        
        if intent_result.self_harm_risk != RiskLevel.LOW:
            risk_factors.append(f"Self-harm risk: {intent_result.self_harm_risk.value}")
        
        if intent_result.crisis_indicators:
            risk_factors.extend([f"Crisis indicator: {indicator}" for indicator in intent_result.crisis_indicators])
        
        # Pattern-based risk factors
        text_lower = user_input.lower()
        
        for category, patterns in self.risk_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    risk_factors.append(f"Risk pattern detected: {category}")
                    break
        
        # Emotional state risk factors
        if intent_result.primary_emotion.value in ["depressed", "hopeless", "overwhelmed"]:
            risk_factors.append(f"High-risk emotional state: {intent_result.primary_emotion.value}")
        
        if intent_result.emotion_intensity > 0.8:
            risk_factors.append(f"High emotional intensity: {intent_result.emotion_intensity:.1%}")
        
        # Conversation pattern risk factors
        if conversation_history:
            user_messages = [msg for msg in conversation_history if msg.get('role') == 'user']
            if len(user_messages) > 5:
                # Check for persistent negative themes
                negative_count = sum(1 for msg in user_messages[-5:] 
                                   if any(word in msg.get('content', '').lower() 
                                         for word in ['sedih', 'putus asa', 'lelah', 'tidak tahan']))
                if negative_count >= 3:
                    risk_factors.append("Persistent negative themes in conversation")
        
        return risk_factors
    
    def _identify_protective_factors(self, 
                                   user_input: str, 
                                   intent_result: IntentAnalysisResult,
                                   conversation_history: List[Dict] = None) -> List[str]:
        """Identify protective factors"""
        
        protective_factors = []
        
        # Spiritual/religious factors
        if intent_result.spiritual_elements:
            protective_factors.append("Spiritual/religious connection")
        
        # Cultural/family factors
        if intent_result.cultural_factors:
            if any(factor in ['keluarga', 'family'] for factor in intent_result.cultural_factors):
                protective_factors.append("Family support system")
            if any(factor in ['komunitas', 'teman'] for factor in intent_result.cultural_factors):
                protective_factors.append("Social support network")
        
        # Help-seeking behavior
        if "bantuan" in user_input.lower() or "help" in user_input.lower():
            protective_factors.append("Help-seeking behavior")
        
        # Positive emotional states
        if intent_result.primary_emotion.value in ["hopeful", "happy"]:
            protective_factors.append(f"Positive emotional state: {intent_result.primary_emotion.value}")
        
        # Engagement with therapy
        if conversation_history and len(conversation_history) > 2:
            protective_factors.append("Engaged in therapeutic conversation")
        
        # Future-oriented thinking
        future_words = ["besok", "nanti", "akan", "rencana", "harapan", "future", "tomorrow", "plan"]
        if any(word in user_input.lower() for word in future_words):
            protective_factors.append("Future-oriented thinking")
        
        return protective_factors
    
    def _determine_immediate_actions(self, alert_level: AlertLevel, risk_factors: List[str]) -> List[str]:
        """Determine immediate actions based on alert level and risk factors"""
        
        actions = []
        
        if alert_level == AlertLevel.RED:
            actions.extend([
                "Immediate safety assessment required",
                "Provide emergency contact numbers",
                "Encourage immediate professional help",
                "Do not leave user alone",
                "Consider emergency services contact"
            ])
        elif alert_level == AlertLevel.ORANGE:
            actions.extend([
                "Enhanced monitoring required",
                "Provide crisis hotline numbers",
                "Encourage professional consultation",
                "Create safety plan",
                "Schedule follow-up within 24 hours"
            ])
        elif alert_level == AlertLevel.YELLOW:
            actions.extend([
                "Increased attention to safety",
                "Provide mental health resources",
                "Monitor for escalation",
                "Consider professional referral"
            ])
        
        # Risk-specific actions
        if any("suicide" in rf.lower() for rf in risk_factors):
            actions.append("Specific suicide risk protocol")
        
        if any("self-harm" in rf.lower() for rf in risk_factors):
            actions.append("Self-harm intervention protocol")
        
        return actions
    
    def _assess_referral_needs(self, intent_result: IntentAnalysisResult, risk_factors: List[str]) -> Tuple[bool, List[ReferralTrigger]]:
        """Assess if professional referral is needed"""
        
        referral_needed = False
        triggers = []
        
        # High-risk situations require referral
        if intent_result.suicide_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            referral_needed = True
            triggers.append(ReferralTrigger.PERSISTENT_SUICIDAL_IDEATION)
        
        if intent_result.self_harm_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            referral_needed = True
            triggers.append(ReferralTrigger.TRAUMA_RESPONSE)
        
        # Context-specific referrals
        if intent_result.primary_emotion.value == "depressed" and intent_result.emotion_intensity > 0.8:
            referral_needed = True
            triggers.append(ReferralTrigger.SEVERE_DEPRESSION)
        
        # Risk factor based referrals
        if any("substance" in rf.lower() for rf in risk_factors):
            referral_needed = True
            triggers.append(ReferralTrigger.SUBSTANCE_DEPENDENCY)
        
        if any("violence" in rf.lower() for rf in risk_factors):
            referral_needed = True
            triggers.append(ReferralTrigger.DOMESTIC_VIOLENCE)
        
        # Complex issues beyond AI scope
        if len(risk_factors) > 5:
            referral_needed = True
            triggers.append(ReferralTrigger.BEYOND_AI_SCOPE)
        
        return referral_needed, triggers
    
    def _needs_emergency_contact(self, alert_level: AlertLevel, risk_factors: List[str]) -> bool:
        """Determine if emergency contact is needed"""
        
        return (alert_level == AlertLevel.RED or 
                any("critical" in rf.lower() for rf in risk_factors) or
                any("immediate danger" in rf.lower() for rf in risk_factors))
    
    def _needs_session_monitoring(self, alert_level: AlertLevel, risk_factors: List[str]) -> bool:
        """Determine if enhanced session monitoring is needed"""
        
        return alert_level in [AlertLevel.ORANGE, AlertLevel.RED] or len(risk_factors) > 3
    
    def _get_data_protection_notes(self, alert_level: AlertLevel, risk_factors: List[str]) -> List[str]:
        """Get data protection considerations"""
        
        notes = []
        
        if alert_level in [AlertLevel.ORANGE, AlertLevel.RED]:
            notes.append("High-risk session - enhanced data protection required")
            notes.append("Consider anonymization of sensitive details")
        
        if any("violence" in rf.lower() for rf in risk_factors):
            notes.append("Violence indicators - legal reporting obligations may apply")
        
        if any("child" in rf.lower() for rf in risk_factors):
            notes.append("Child protection concerns - mandatory reporting may be required")
        
        return notes
    
    def _quick_content_check(self, text: str) -> Tuple[bool, List[ContentType], float]:
        """Quick pattern-based content check"""
        
        is_harmful = False
        content_types = []
        severity_score = 0.0
        
        text_lower = text.lower()
        
        # Check for various harmful content types
        for category, patterns in self.harmful_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    is_harmful = True
                    severity_score = max(severity_score, 0.6)
                    
                    if category == "explicit_sexual":
                        content_types.append(ContentType.SEXUAL_CONTENT)
                    elif category == "hate_speech":
                        content_types.append(ContentType.HATE_SPEECH)
                    elif category == "spam":
                        content_types.append(ContentType.SPAM)
        
        # Check for high-risk patterns
        for category, patterns in self.risk_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    is_harmful = True
                    severity_score = max(severity_score, 0.8)
                    
                    if category == "high_risk":
                        content_types.append(ContentType.SUICIDE_IDEATION)
                    elif category == "self_harm":
                        content_types.append(ContentType.SELF_HARM)
                    elif category == "violence":
                        content_types.append(ContentType.VIOLENCE_THREAT)
        
        return is_harmful, content_types, severity_score
    
    def _advanced_content_analysis(self, text: str) -> Optional[Dict]:
        """Advanced content analysis using GPT"""
        
        try:
            system_prompt = """Anda adalah sistem keamanan konten yang menganalisis teks untuk konten berbahaya. 
            Analisis teks dan berikan hasil dalam format JSON dengan:
            - is_harmful: boolean
            - severity: float (0.0-1.0)
            - content_types: array of harmful content types
            - explanation: penjelasan singkat
            
            Fokus pada: konten seksual eksplisit, kekerasan, ujaran kebencian, ancaman, dan konten yang tidak pantas untuk konseling."""
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            return json.loads(result_text)
            
        except Exception as e:
            logger.error(f"Error in advanced content analysis: {e}")
            return None
    
    def _generate_warning_message(self, content_types: List[ContentType]) -> str:
        """Generate warning message for harmful content"""
        
        if ContentType.SUICIDE_IDEATION in content_types:
            return "Saya khawatir dengan keselamatan Anda. Silakan hubungi 119 untuk bantuan segera."
        
        if ContentType.VIOLENCE_THREAT in content_types:
            return "Konten yang mengandung ancaman kekerasan tidak dapat diproses. Silakan hubungi 110 jika dalam bahaya."
        
        if ContentType.SELF_HARM in content_types:
            return "Saya khawatir dengan keinginan Anda untuk menyakiti diri. Mari bicarakan tentang cara yang lebih aman."
        
        if ContentType.SEXUAL_CONTENT in content_types:
            return "Konten yang tidak pantas terdeteksi. Mari fokus pada dukungan kesehatan mental."
        
        return "Konten yang tidak sesuai terdeteksi. Mari kembali ke topik dukungan kesehatan mental."
    
    def _create_safe_assessment(self) -> SafetyAssessment:
        """Create safe default assessment"""
        
        return SafetyAssessment(
            alert_level=AlertLevel.YELLOW,
            risk_factors=["System error - defaulting to cautious assessment"],
            protective_factors=["User seeking help"],
            immediate_actions=["Monitor closely", "Provide support"],
            referral_needed=True,
            referral_triggers=[ReferralTrigger.BEYOND_AI_SCOPE],
            emergency_contact=False,
            session_monitoring=True,
            data_protection_notes=["System error - enhanced protection applied"],
            timestamp=datetime.now()
        )
    
    def _create_safe_filter_result(self) -> ContentFilterResult:
        """Create safe default filter result"""
        
        return ContentFilterResult(
            is_harmful=False,
            content_types=[],
            severity_score=0.0,
            blocked_content=False,
            warning_message=None,
            escalation_required=False,
            timestamp=datetime.now()
        )
    
    def _create_default_consent(self, session_id: str) -> SessionConsent:
        """Create default consent record"""
        
        return SessionConsent(
            consent_given=True,
            recording_consent=False,
            data_sharing_consent=False,
            anonymization_level="high",
            retention_period=7,  # Short retention for safety
            consent_timestamp=datetime.now(),
            ip_hash="anonymous",
            session_id=session_id
        ) 