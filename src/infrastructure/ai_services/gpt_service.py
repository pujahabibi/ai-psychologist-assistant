#!/usr/bin/env python3
"""
GPT Service Implementation - OpenAI API integration for therapeutic responses
"""

import time
from typing import List, Dict, Optional
from openai import OpenAI
from ...core.interfaces.ai_service import IGPTService
from ...core.entities.therapeutic_response import TherapeuticResponse, EmotionType, EmotionAnalysis, SafetyAssessment, AlertLevel
from ...infrastructure.config.settings import settings


class GPTService(IGPTService):
    """GPT service implementation using OpenAI API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.model_name = settings.model_config.primary_model
        
    async def generate_therapeutic_response(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]],
        session_id: str,
        system_prompt: str
    ) -> TherapeuticResponse:
        """Generate therapeutic response using GPT"""
        start_time = time.time()
        
        try:
            # Prepare messages with system prompt
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)
            
            # Make API call with original hyperparameters
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=settings.model_config.max_tokens,
                temperature=settings.model_config.temperature,
                presence_penalty=settings.model_config.presence_penalty,
                frequency_penalty=settings.model_config.frequency_penalty
            )
            
            ai_response = response.choices[0].message.content.strip()
            processing_time = time.time() - start_time
            
            # Create basic emotion analysis (simplified implementation)
            emotion_analysis = self._analyze_emotion(user_input)
            
            # Create safety assessment
            safety_assessment = self._assess_safety(user_input, ai_response)
            
            return TherapeuticResponse(
                content=ai_response,
                session_id=session_id,
                user_input=user_input,
                model_used=self.model_name,
                emotion_analysis=emotion_analysis,
                safety_assessment=safety_assessment,
                processing_time=processing_time
            )
            
        except Exception as e:
            print(f"Error in GPT response generation: {e}")
            return TherapeuticResponse(
                content="Maaf, saya sedang mengalami gangguan teknis. Bisakah Anda ulangi yang tadi?",
                session_id=session_id,
                user_input=user_input,
                model_used="error",
                processing_time=time.time() - start_time
            )
    
    def _analyze_emotion(self, user_input: str) -> EmotionAnalysis:
        """Simplified emotion analysis based on keywords"""
        # Convert to lowercase for analysis
        text = user_input.lower()
        
        # Basic emotion detection (simplified)
        if any(word in text for word in ['sedih', 'sad', 'depress', 'terpuruk', 'down']):
            return EmotionAnalysis(
                primary_emotion=EmotionType.SAD,
                intensity=0.7,
                confidence=0.6
            )
        elif any(word in text for word in ['cemas', 'anxious', 'worry', 'takut', 'nervous']):
            return EmotionAnalysis(
                primary_emotion=EmotionType.ANXIOUS,
                intensity=0.6,
                confidence=0.6
            )
        elif any(word in text for word in ['marah', 'angry', 'kesal', 'frustrated']):
            return EmotionAnalysis(
                primary_emotion=EmotionType.ANGRY,
                intensity=0.6,
                confidence=0.6
            )
        elif any(word in text for word in ['bingung', 'confused', 'overwhelmed']):
            return EmotionAnalysis(
                primary_emotion=EmotionType.CONFUSED,
                intensity=0.5,
                confidence=0.5
            )
        else:
            return EmotionAnalysis(
                primary_emotion=EmotionType.NEUTRAL,
                intensity=0.3,
                confidence=0.4
            )
    
    def _assess_safety(self, user_input: str, ai_response: str) -> SafetyAssessment:
        """Assess safety based on keywords and patterns"""
        text = user_input.lower()
        
        # High risk patterns
        high_risk_keywords = [
            'ingin mati', 'bunuh diri', 'mengakhiri hidup', 'tidak ingin hidup lagi',
            'suicide', 'kill myself', 'end my life', 'want to die',
            'menyerah total', 'tak sanggup bertahan', 'lebih baik mati', 'life is pointless'
        ]
        
        # Medium risk patterns
        medium_risk_keywords = [
            'tidak tahan lagi', 'putus asa', 'hopeless', 'tidak ada harapan',
            'lelah hidup', 'tired of living', 'give up', 'kehilangan arah',
            'merasa hampa', 'meaningless', 'tidak berguna', 'hidup terasa berat'
        ]
        
        # Self-harm patterns
        self_harm_keywords = [
            'melukai diri', 'menyakiti diri', 'cutting', 'self harm',
            'memotong', 'menyilet', 'hurt myself', 'mencederai tubuh'
        ]
        
        detected_keywords = []
        alert_level = AlertLevel.GREEN
        requires_intervention = False
        requires_referral = False
        
        # Check for high risk
        for keyword in high_risk_keywords:
            if keyword in text:
                detected_keywords.append(keyword)
                alert_level = AlertLevel.RED
                requires_intervention = True
                requires_referral = True
                break
        
        # Check for self-harm if not already high risk
        if alert_level != AlertLevel.RED:
            for keyword in self_harm_keywords:
                if keyword in text:
                    detected_keywords.append(keyword)
                    alert_level = AlertLevel.RED
                    requires_intervention = True
                    requires_referral = True
                    break
        
        # Check for medium risk if not already high risk
        if alert_level == AlertLevel.GREEN:
            for keyword in medium_risk_keywords:
                if keyword in text:
                    detected_keywords.append(keyword)
                    alert_level = AlertLevel.ORANGE
                    requires_referral = True
                    break
        
        return SafetyAssessment(
            alert_level=alert_level,
            keywords_detected=detected_keywords,
            requires_intervention=requires_intervention,
            requires_referral=requires_referral
        )
    
    def is_available(self) -> bool:
        """Check if GPT service is available"""
        return bool(self.api_key)
    
    def get_model_name(self) -> str:
        """Get model name"""
        return self.model_name 