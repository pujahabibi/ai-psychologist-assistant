#!/usr/bin/env python3
"""
Therapeutic Capabilities Module for Indonesian Mental Health Support Bot
Implements active listening, CBT techniques, crisis intervention protocols,
cultural trauma-informed approaches, and religious/spiritual integration.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from openai import OpenAI
from dotenv import load_dotenv

from intent_analysis import IntentAnalysisResult, EmotionalState, TherapeuticContext, RiskLevel

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TherapeuticTechnique(Enum):
    """Available therapeutic techniques"""
    ACTIVE_LISTENING = "active_listening"
    CBT_REFRAMING = "cbt_reframing"
    MINDFULNESS = "mindfulness"
    GROUNDING = "grounding"
    BEHAVIORAL_ACTIVATION = "behavioral_activation"
    CRISIS_INTERVENTION = "crisis_intervention"
    CULTURAL_VALIDATION = "cultural_validation"
    SPIRITUAL_INTEGRATION = "spiritual_integration"
    FAMILY_THERAPY = "family_therapy"
    GRIEF_COUNSELING = "grief_counseling"
    ANXIETY_MANAGEMENT = "anxiety_management"
    DEPRESSION_SUPPORT = "depression_support"

class CulturalApproach(Enum):
    """Cultural approaches for Indonesian context"""
    JAVANESE_HARMONY = "javanese_harmony"
    ISLAMIC_COUNSELING = "islamic_counseling"
    FAMILY_CENTERED = "family_centered"
    COMMUNITY_SUPPORT = "community_support"
    TRADITIONAL_HEALING = "traditional_healing"
    COLLECTIVIST_VALUES = "collectivist_values"
    RESPECT_HIERARCHY = "respect_hierarchy"
    SPIRITUAL_WELLNESS = "spiritual_wellness"

@dataclass
class TherapeuticResponse:
    """Response with therapeutic content and metadata"""
    response_text: str
    technique_used: TherapeuticTechnique
    cultural_approach: Optional[CulturalApproach]
    follow_up_questions: List[str]
    safety_notes: List[str]
    crisis_escalation: bool
    session_notes: str
    timestamp: datetime

class TherapeuticCapabilities:
    """
    Main therapeutic capabilities system
    Provides culturally-sensitive therapeutic interventions
    """
    
    def __init__(self, api_key: str = None):
        """Initialize therapeutic capabilities"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Crisis hotlines and resources
        self.crisis_resources = {
            "national_suicide_prevention": "119",
            "mental_health_crisis": "500-454",
            "women_crisis": "021-7270005",
            "child_protection": "129",
            "domestic_violence": "021-3448245",
            "depression_support": "0804-1-500-454"
        }
        
        # Cultural and spiritual resources
        self.cultural_resources = {
            "islamic_counseling": ["Konseling Islam", "Bimbingan Rohani"],
            "traditional_healing": ["Pengobatan Tradisional", "Herbal Medicine"],
            "family_mediation": ["Mediasi Keluarga", "Konseling Keluarga"],
            "community_support": ["Dukungan Komunitas", "Gotong Royong"]
        }
        
        logger.info("Therapeutic Capabilities initialized successfully")
    
    def generate_therapeutic_response(self, 
                                    user_input: str, 
                                    intent_result: IntentAnalysisResult,
                                    conversation_history: List[Dict] = None,
                                    session_id: str = None) -> TherapeuticResponse:
        """
        Generate therapeutic response based on intent analysis
        
        Args:
            user_input: User's input text
            intent_result: Intent analysis result
            conversation_history: Previous conversation
            session_id: Session identifier
            
        Returns:
            TherapeuticResponse with tailored response
        """
        try:
            # Determine primary therapeutic technique
            technique = self._select_therapeutic_technique(intent_result)
            
            # Determine cultural approach
            cultural_approach = self._select_cultural_approach(intent_result)
            
            # Generate response based on technique and context
            response_text = self._generate_technique_response(
                user_input, intent_result, technique, cultural_approach, conversation_history
            )
            
            # Generate follow-up questions
            follow_up_questions = self._generate_follow_up_questions(intent_result, technique)
            
            # Generate safety notes
            safety_notes = self._generate_safety_notes(intent_result)
            
            # Determine if crisis escalation is needed
            crisis_escalation = intent_result.requires_escalation or intent_result.emergency_contact_needed
            
            # Create session notes
            session_notes = self._create_session_notes(intent_result, technique, cultural_approach)
            
            return TherapeuticResponse(
                response_text=response_text,
                technique_used=technique,
                cultural_approach=cultural_approach,
                follow_up_questions=follow_up_questions,
                safety_notes=safety_notes,
                crisis_escalation=crisis_escalation,
                session_notes=session_notes,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error generating therapeutic response: {e}")
            return self._create_safe_response(user_input)
    
    def _select_therapeutic_technique(self, intent_result: IntentAnalysisResult) -> TherapeuticTechnique:
        """Select appropriate therapeutic technique based on intent analysis"""
        
        # Crisis intervention takes priority
        if intent_result.suicide_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return TherapeuticTechnique.CRISIS_INTERVENTION
        
        # Map therapeutic contexts to techniques
        context_technique_map = {
            TherapeuticContext.CRISIS_INTERVENTION: TherapeuticTechnique.CRISIS_INTERVENTION,
            TherapeuticContext.CBT_TECHNIQUES: TherapeuticTechnique.CBT_REFRAMING,
            TherapeuticContext.ACTIVE_LISTENING: TherapeuticTechnique.ACTIVE_LISTENING,
            TherapeuticContext.ANXIETY_MANAGEMENT: TherapeuticTechnique.ANXIETY_MANAGEMENT,
            TherapeuticContext.DEPRESSION_SUPPORT: TherapeuticTechnique.DEPRESSION_SUPPORT,
            TherapeuticContext.GRIEF_COUNSELING: TherapeuticTechnique.GRIEF_COUNSELING,
            TherapeuticContext.CULTURAL_TRAUMA: TherapeuticTechnique.CULTURAL_VALIDATION,
            TherapeuticContext.SPIRITUAL_SUPPORT: TherapeuticTechnique.SPIRITUAL_INTEGRATION,
            TherapeuticContext.FAMILY_DYNAMICS: TherapeuticTechnique.FAMILY_THERAPY
        }
        
        return context_technique_map.get(intent_result.therapeutic_context, TherapeuticTechnique.ACTIVE_LISTENING)
    
    def _select_cultural_approach(self, intent_result: IntentAnalysisResult) -> Optional[CulturalApproach]:
        """Select appropriate cultural approach"""
        
        # Check for spiritual elements
        if intent_result.spiritual_elements:
            if any(elem in ['allah', 'islam', 'doa', 'sholat'] for elem in intent_result.spiritual_elements):
                return CulturalApproach.ISLAMIC_COUNSELING
            return CulturalApproach.SPIRITUAL_WELLNESS
        
        # Check for family factors
        if intent_result.cultural_factors:
            if any(factor in ['keluarga', 'family'] for factor in intent_result.cultural_factors):
                return CulturalApproach.FAMILY_CENTERED
            if any(factor in ['komunitas', 'masyarakat'] for factor in intent_result.cultural_factors):
                return CulturalApproach.COMMUNITY_SUPPORT
        
        # Default to collectivist values for Indonesian context
        return CulturalApproach.COLLECTIVIST_VALUES
    
    def _generate_technique_response(self, 
                                   user_input: str, 
                                   intent_result: IntentAnalysisResult,
                                   technique: TherapeuticTechnique,
                                   cultural_approach: Optional[CulturalApproach],
                                   conversation_history: List[Dict] = None) -> str:
        """Generate response using specific therapeutic technique"""
        
        # Prepare context for GPT
        context = self._prepare_therapeutic_context(
            user_input, intent_result, technique, cultural_approach, conversation_history
        )
        
        # Get technique-specific system prompt
        system_prompt = self._get_technique_system_prompt(technique, cultural_approach)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                max_tokens=400,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating technique response: {e}")
            return self._get_fallback_response(technique)
    
    def _prepare_therapeutic_context(self, 
                                   user_input: str, 
                                   intent_result: IntentAnalysisResult,
                                   technique: TherapeuticTechnique,
                                   cultural_approach: Optional[CulturalApproach],
                                   conversation_history: List[Dict] = None) -> str:
        """Prepare context for therapeutic response generation"""
        
        context = f"""
CURRENT INPUT: {user_input}

INTENT ANALYSIS:
- Primary Emotion: {intent_result.primary_emotion.value}
- Intensity: {intent_result.emotion_intensity:.1%}
- Therapeutic Context: {intent_result.therapeutic_context.value}
- Suicide Risk: {intent_result.suicide_risk.value}
- Cultural Factors: {', '.join(intent_result.cultural_factors)}
- Spiritual Elements: {', '.join(intent_result.spiritual_elements)}
- Suggested Approach: {intent_result.suggested_approach}

TECHNIQUE TO USE: {technique.value}
CULTURAL APPROACH: {cultural_approach.value if cultural_approach else 'general'}

CRISIS INDICATORS: {', '.join(intent_result.crisis_indicators)}
REQUIRES ESCALATION: {intent_result.requires_escalation}
"""
        
        if conversation_history:
            context += "\nRECENT CONVERSATION:\n"
            for msg in conversation_history[-3:]:  # Last 3 messages
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                context += f"{role}: {content}\n"
        
        return context
    
    def _get_technique_system_prompt(self, technique: TherapeuticTechnique, cultural_approach: Optional[CulturalApproach]) -> str:
        """Get system prompt for specific therapeutic technique"""
        
        base_prompt = """Anda adalah Kak Indira, seorang konselor kesehatan mental yang berpengalaman dengan pemahaman mendalam tentang budaya Indonesia. """
        
        technique_prompts = {
            TherapeuticTechnique.ACTIVE_LISTENING: """
Fokus pada ACTIVE LISTENING:
- Validasi perasaan pengguna dengan empati
- Refleksi kembali apa yang dikatakan pengguna
- Gunakan pertanyaan terbuka untuk eksplorasi
- Hindari memberikan solusi langsung
- Tunjukkan bahwa Anda benar-benar mendengarkan
""",
            
            TherapeuticTechnique.CBT_REFRAMING: """
Gunakan teknik CBT REFRAMING:
- Identifikasi pola pikir negatif
- Bantu pengguna melihat perspektif alternatif
- Gunakan pertanyaan Socratic untuk memandu
- Fokus pada bukti yang mendukung vs menentang pikiran
- Tawarkan perspektif yang lebih seimbang
""",
            
            TherapeuticTechnique.CRISIS_INTERVENTION: """
PROTOCOL CRISIS INTERVENTION:
- Lakukan assessment keamanan segera
- Eksplorasi rencana spesifik jika ada
- Berikan nomor hotline krisis: 119 (Pencegahan Bunuh Diri)
- Dorong bantuan profesional segera
- Pastikan pengguna tidak sendirian
- Fokus pada stabilisasi emosi
""",
            
            TherapeuticTechnique.ANXIETY_MANAGEMENT: """
TEKNIK MANAJEMEN KECEMASAN:
- Ajarkan teknik pernapasan (4-7-8)
- Grounding techniques (5-4-3-2-1)
- Progressive muscle relaxation
- Mindfulness sederhana
- Normalisasi perasaan cemas
""",
            
            TherapeuticTechnique.DEPRESSION_SUPPORT: """
DUKUNGAN DEPRESI:
- Behavioral activation (kegiatan kecil yang menyenangkan)
- Mood monitoring dan pola recognition
- Normalisasi perasaan depresi
- Fokus pada self-care sederhana
- Dorong koneksi sosial
""",
            
            TherapeuticTechnique.CULTURAL_VALIDATION: """
VALIDASI BUDAYA:
- Akui dan hormati nilai-nilai budaya
- Validasi pengalaman dalam konteks budaya Indonesia
- Integrasikan nilai-nilai keluarga dan komunitas
- Respek terhadap norma dan tradisi
""",
            
            TherapeuticTechnique.SPIRITUAL_INTEGRATION: """
INTEGRASI SPIRITUAL:
- Hormati keyakinan dan praktik spiritual
- Gunakan referensi religius yang sesuai
- Integrasikan doa dan ibadah sebagai coping
- Hubungkan dengan makna hidup yang lebih besar
""",
            
            TherapeuticTechnique.FAMILY_THERAPY: """
DINAMIKA KELUARGA:
- Eksplorasi peran dalam keluarga
- Pahami hierarki dan ekspektasi keluarga
- Mediasi konflik dengan pendekatan budaya
- Fokus pada harmoni dan keseimbangan
""",
            
            TherapeuticTechnique.GRIEF_COUNSELING: """
KONSELING DUKA:
- Normalisasi proses grief
- Eksplorasi tahapan duka
- Validasi perasaan kehilangan
- Integrasikan ritual budaya dan agama
- Fokus pada meaning-making
"""
        }
        
        cultural_additions = {
            CulturalApproach.ISLAMIC_COUNSELING: """
PENDEKATAN ISLAM:
- Gunakan perspektif Islamic counseling
- Referensi Al-Quran dan Hadis yang relevan
- Integrasikan konsep tawakkal, sabar, dan syukur
- Dorong praktik ibadah sebagai coping mechanism
""",
            
            CulturalApproach.FAMILY_CENTERED: """
PENDEKATAN KELUARGA:
- Respek terhadap otoritas orangtua
- Pertimbangkan implikasi keluarga dari setiap keputusan
- Fokus pada harmoni keluarga
- Integrasikan nilai-nilai gotong royong
""",
            
            CulturalApproach.COMMUNITY_SUPPORT: """
DUKUNGAN KOMUNITAS:
- Dorong koneksi dengan komunitas
- Manfaatkan support system tradisional
- Integrasikan nilai-nilai sosial Indonesia
- Fokus pada collective healing
"""
        }
        
        prompt = base_prompt + technique_prompts.get(technique, "")
        
        if cultural_approach and cultural_approach in cultural_additions:
            prompt += cultural_additions[cultural_approach]
        
        prompt += """
PENTING:
- Respons maksimal 3-4 kalimat
- Gunakan bahasa yang hangat dan tidak menggurui
- Akhiri dengan pertanyaan terbuka
- Jika crisis, berikan nomor hotline 119
- Selalu ingatkan bahwa Anda adalah AI, bukan pengganti terapis profesional
"""
        
        return prompt
    
    def _generate_follow_up_questions(self, intent_result: IntentAnalysisResult, technique: TherapeuticTechnique) -> List[str]:
        """Generate appropriate follow-up questions"""
        
        questions = []
        
        # Technique-specific questions
        if technique == TherapeuticTechnique.ACTIVE_LISTENING:
            questions.extend([
                "Bagaimana perasaan Anda setelah menceritakan ini?",
                "Apa yang paling ingin Anda sampaikan tentang situasi ini?",
                "Bagaimana pengalaman ini mempengaruhi Anda?"
            ])
        
        elif technique == TherapeuticTechnique.CBT_REFRAMING:
            questions.extend([
                "Apa bukti yang mendukung pikiran tersebut?",
                "Bagaimana teman baik Anda akan melihat situasi ini?",
                "Apa kemungkinan lain yang bisa terjadi?"
            ])
        
        elif technique == TherapeuticTechnique.CRISIS_INTERVENTION:
            questions.extend([
                "Apakah Anda memiliki rencana untuk menyakiti diri?",
                "Siapa yang bisa Anda hubungi sekarang?",
                "Apakah ada seseorang yang bisa menemani Anda?"
            ])
        
        # Context-specific questions
        if intent_result.primary_emotion == EmotionalState.ANXIOUS:
            questions.append("Apa yang biasanya membuat Anda merasa lebih tenang?")
        
        if intent_result.cultural_factors:
            questions.append("Bagaimana keluarga biasanya menghadapi situasi seperti ini?")
        
        if intent_result.spiritual_elements:
            questions.append("Bagaimana keyakinan spiritual membantu Anda?")
        
        return questions[:3]  # Return top 3 questions
    
    def _generate_safety_notes(self, intent_result: IntentAnalysisResult) -> List[str]:
        """Generate safety notes based on risk assessment"""
        
        notes = []
        
        if intent_result.suicide_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            notes.extend([
                "TINGGI: Risiko bunuh diri - monitoring ketat diperlukan",
                "Berikan nomor hotline: 119 (Pencegahan Bunuh Diri)",
                "Dorong bantuan profesional segera"
            ])
        
        if intent_result.self_harm_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            notes.append("TINGGI: Risiko self-harm - assess keamanan lingkungan")
        
        if intent_result.crisis_indicators:
            notes.append(f"Crisis indicators: {', '.join(intent_result.crisis_indicators)}")
        
        if intent_result.requires_escalation:
            notes.append("ESCALATION REQUIRED: Rujuk ke profesional")
        
        if intent_result.emergency_contact_needed:
            notes.append("EMERGENCY: Kontak darurat diperlukan")
        
        return notes
    
    def _create_session_notes(self, 
                            intent_result: IntentAnalysisResult,
                            technique: TherapeuticTechnique,
                            cultural_approach: Optional[CulturalApproach]) -> str:
        """Create session notes for documentation"""
        
        notes = f"""
SESSION NOTES:
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Primary Emotion: {intent_result.primary_emotion.value} ({intent_result.emotion_intensity:.1%})
Therapeutic Context: {intent_result.therapeutic_context.value}
Technique Used: {technique.value}
Cultural Approach: {cultural_approach.value if cultural_approach else 'general'}
Risk Assessment: Suicide({intent_result.suicide_risk.value}), Self-harm({intent_result.self_harm_risk.value})
Escalation Required: {intent_result.requires_escalation}
Session Goals: {', '.join(intent_result.session_goals)}
"""
        
        if intent_result.cultural_factors:
            notes += f"Cultural Factors: {', '.join(intent_result.cultural_factors)}\n"
        
        if intent_result.spiritual_elements:
            notes += f"Spiritual Elements: {', '.join(intent_result.spiritual_elements)}\n"
        
        return notes.strip()
    
    def _get_fallback_response(self, technique: TherapeuticTechnique) -> str:
        """Get fallback response when GPT fails"""
        
        fallback_responses = {
            TherapeuticTechnique.ACTIVE_LISTENING: "Saya mendengar bahwa Anda sedang mengalami sesuatu yang sulit. Bisakah Anda ceritakan lebih lanjut tentang perasaan Anda?",
            TherapeuticTechnique.CBT_REFRAMING: "Mari kita coba melihat situasi ini dari perspektif yang berbeda. Apa yang bisa kita pelajari dari pengalaman ini?",
            TherapeuticTechnique.CRISIS_INTERVENTION: "Saya khawatir dengan keamanan Anda. Silakan hubungi 119 untuk bantuan segera. Apakah ada seseorang yang bisa menemani Anda sekarang?",
            TherapeuticTechnique.ANXIETY_MANAGEMENT: "Saat merasa cemas, coba tarik napas dalam-dalam. Hirup selama 4 detik, tahan 7 detik, lalu hembuskan 8 detik. Bagaimana perasaan Anda setelah melakukan ini?",
            TherapeuticTechnique.DEPRESSION_SUPPORT: "Perasaan sedih yang Anda alami sangat wajar. Apa satu hal kecil yang bisa membuat Anda merasa sedikit lebih baik hari ini?"
        }
        
        return fallback_responses.get(technique, "Terima kasih telah berbagi. Saya di sini untuk mendengarkan Anda.")
    
    def _create_safe_response(self, user_input: str) -> TherapeuticResponse:
        """Create safe response when system fails"""
        
        return TherapeuticResponse(
            response_text="Terima kasih telah berbagi. Saya di sini untuk mendengarkan Anda. Bisakah Anda ceritakan lebih lanjut tentang perasaan Anda?",
            technique_used=TherapeuticTechnique.ACTIVE_LISTENING,
            cultural_approach=CulturalApproach.COLLECTIVIST_VALUES,
            follow_up_questions=["Bagaimana perasaan Anda sekarang?", "Apa yang paling ingin Anda sampaikan?"],
            safety_notes=["System fallback - monitor closely"],
            crisis_escalation=False,
            session_notes="System fallback response generated",
            timestamp=datetime.now()
        )
    
    def get_crisis_resources(self) -> Dict[str, str]:
        """Get crisis resources and hotlines"""
        return self.crisis_resources.copy()
    
    def get_cultural_resources(self) -> Dict[str, List[str]]:
        """Get cultural and spiritual resources"""
        return self.cultural_resources.copy()
    
    def assess_session_progress(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Assess therapeutic progress in session"""
        
        if not conversation_history:
            return {"progress": "no_data", "recommendations": []}
        
        # Simple progress assessment
        total_messages = len(conversation_history)
        user_messages = [msg for msg in conversation_history if msg.get('role') == 'user']
        
        progress_metrics = {
            "total_interactions": total_messages,
            "user_engagement": len(user_messages),
            "session_length": "short" if total_messages < 10 else "medium" if total_messages < 20 else "long",
            "emotional_trajectory": "stable",  # Would need more complex analysis
            "therapeutic_alliance": "developing"  # Would need sentiment analysis
        }
        
        recommendations = []
        
        if total_messages > 20:
            recommendations.append("Consider wrapping up session - extended conversation detected")
        
        if len(user_messages) < 3:
            recommendations.append("Encourage more user engagement")
        
        return {
            "progress": progress_metrics,
            "recommendations": recommendations,
            "session_summary": f"Session with {total_messages} interactions, user engagement: {len(user_messages)} messages"
        } 