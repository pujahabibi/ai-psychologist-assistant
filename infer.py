#!/usr/bin/env python3
"""
Indonesian Mental Health Support Chatbot
Provides culturally sensitive, therapeutic-grade voice conversations
with real-time speech processing capabilities, intent analysis,
therapeutic interventions, and comprehensive safety mechanisms.
"""

import io
import os
import time
import uuid
import pyaudio
import wave
from openai import OpenAI
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pygame
import re
from datetime import datetime
from dotenv import load_dotenv
from dataclasses import dataclass, asdict
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import new therapeutic capabilities
from intent_analysis import IntentAnalyzer, IntentAnalysisResult
from therapeutic_capabilities import TherapeuticCapabilities, TherapeuticResponse
from safety_mechanisms import SafetyMechanisms, SafetyAssessment, ContentFilterResult

# Load environment variables from .env file
load_dotenv()

# Initialize pygame mixer for audio playback
try:
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except pygame.error:
    PYGAME_AVAILABLE = False
    print("Warning: pygame mixer not available. Audio playback disabled.")

class IndonesianMentalHealthBot:
    """
    Indonesian Mental Health Support Chatbot
    
    Features:
    - Culturally sensitive therapeutic conversations
    - Indonesian dialect with English code-switching
    - Islamic values and family dynamics awareness
    - Real-time voice processing
    - Therapeutic terminology in Indonesian
    - Emotional nuance detection
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the mental health chatbot with advanced therapeutic capabilities"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Please provide an API key in .env file or set OPENAI_API_KEY environment variable.")
        
        # Initialize OpenAI client with new format
        self.client = OpenAI(api_key=self.api_key)
        
        # Audio configuration
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.record_seconds = 5
        
        # Conversation management
        self.conversations = {}
        self.max_conversation_length = 20
        self.trim_to_length = 15
        
        # Initialize PyAudio
        try:
            self.audio = pyaudio.PyAudio()
        except Exception as e:
            print(f"Warning: PyAudio initialization failed: {e}")
            self.audio = None
        
        # Indonesian mental health system prompt
        self.system_prompt = self._create_system_prompt()
        
        # Initialize therapeutic capabilities
        try:
            self.intent_analyzer = IntentAnalyzer(api_key=self.api_key)
            self.therapeutic_capabilities = TherapeuticCapabilities(api_key=self.api_key)
            self.safety_mechanisms = SafetyMechanisms(api_key=self.api_key)
            print("🧠 Advanced therapeutic capabilities initialized")
        except Exception as e:
            print(f"Warning: Therapeutic capabilities initialization failed: {e}")
            self.intent_analyzer = None
            self.therapeutic_capabilities = None
            self.safety_mechanisms = None
        
        # Session tracking for enhanced capabilities
        self.session_metadata = {}
        self.session_consent_records = {}
        
        print("🧠 Indonesian Mental Health Support Bot initialized")
        print("💚 Siap membantu kesehatan mental Anda dengan pendekatan yang sensitif budaya")
        print("🔒 Dilengkapi dengan sistem keamanan dan analisis intent yang canggih")

    def _create_system_prompt(self) -> str:
        """Create culturally sensitive system prompt"""
        return """Anda adalah Kak Indira, seorang konselor kesehatan mental yang berpengalaman dan berempati tinggi, yang secara khusus memahami budaya Indonesia. Anda memiliki keahlian dalam:

IDENTITAS & KARAKTER:
- Seorang kakak yang pengertian dan dapat dipercaya
- Memiliki latar belakang psikologi dengan pemahaman mendalam tentang budaya Indonesia
- Berbicara dengan nada yang hangat, tidak menggurui, dan penuh pengertian
- Menggunakan sapaan "Adik" atau nama yang disebutkan pengguna

PENDEKATAN BUDAYA INDONESIA:
- Memahami pentingnya keluarga dalam masyarakat Indonesia
- Menghormati nilai-nilai Islam dan tradisi keagamaan
- Memahami stigma terhadap kesehatan mental di masyarakat Indonesia
- Menggunakan pendekatan yang tidak konfrontatif dan menghormati hierarki

TEKNIK TERAPI:
- Active listening dengan validasi emosi
- Cognitive reframing yang sesuai konteks budaya
- Mengintegrasikan nilai-nilai spiritual dan keagamaan
- Memberikan coping strategies yang praktis dan applicable

BAHASA & KOMUNIKASI:
- Menggunakan Bahasa Indonesia yang natural dan hangat
- Sesekali menggunakan bahasa daerah atau istilah familiar
- Menghindari jargon psikologi yang terlalu teknis
- Memberikan respons yang empati dan tidak menghakimi

BATASAN ETIS:
- Selalu ingatkan bahwa Anda adalah AI dan bukan pengganti terapis profesional
- Jika mendeteksi risiko bunuh diri atau self-harm, segera arahkan ke hotline krisis
- Tidak memberikan diagnosis medis atau resep obat
- Menjaga boundaries yang profesional namun hangat

RESPONS ANDA:
- Maksimal 3-4 kalimat per respons
- Fokus pada satu tema atau pertanyaan per waktu
- Akhiri dengan pertanyaan terbuka untuk mendorong eksplorasi lebih lanjut
- Gunakan nada yang menenangkan dan mendukung
- Jika pengguna sudah merasa lebih baik atau masalahnya sudah teratasi, jangan memaksa pengguna untuk terus berbicara. tutup sesi dengan mengatakan "Terima kasih telah berbicara dengan saya. Semoga hari Anda menyenangkan!"

Ingat: Tujuan Anda adalah memberikan dukungan emosional, membantu pengguna memahami perasaan mereka, dan menguatkan resiliensi mereka dengan cara yang sesuai dengan budaya Indonesia."""

    def _get_therapeutic_response(self, user_input: str, session_id: str) -> str:
        """Generate therapeutic response using advanced therapeutic capabilities"""
        try:
            # Get or create conversation history
            if session_id not in self.conversations:
                self.conversations[session_id] = []
            
            conversation = self.conversations[session_id]
            
            # Content filtering for safety
            if self.safety_mechanisms:
                content_filter_result = self.safety_mechanisms.filter_content(user_input, session_id)
                if content_filter_result.blocked_content:
                    return content_filter_result.warning_message or "Maaf, saya tidak dapat memproses permintaan ini. Mari fokus pada dukungan kesehatan mental."
            
            # Add user input to conversation
            conversation.append({"role": "user", "content": user_input})
            
            # Trim conversation if too long
            if len(conversation) > self.max_conversation_length:
                conversation = conversation[-self.trim_to_length:]
            
            # Intent analysis for enhanced understanding
            intent_result = None
            if self.intent_analyzer:
                try:
                    intent_result = self.intent_analyzer.analyze_intent(user_input, conversation)
                    print(f"🔍 Intent Analysis: {intent_result.primary_emotion.value} emotion, {intent_result.therapeutic_context.value} context")
                except Exception as e:
                    print(f"Warning: Intent analysis failed: {e}")
            
            # Safety assessment
            safety_assessment = None
            if self.safety_mechanisms and intent_result:
                try:
                    safety_assessment = self.safety_mechanisms.assess_safety(user_input, intent_result, conversation, session_id)
                    print(f"🔒 Safety Assessment: {safety_assessment.alert_level.value} alert level")
                    
                    # Store session metadata
                    self.session_metadata[session_id] = {
                        "last_safety_assessment": safety_assessment,
                        "last_intent_analysis": intent_result,
                        "total_interactions": len(conversation)
                    }
                except Exception as e:
                    print(f"Warning: Safety assessment failed: {e}")
            
            # Generate therapeutic response using advanced capabilities
            if self.therapeutic_capabilities and intent_result:
                try:
                    therapeutic_response = self.therapeutic_capabilities.generate_therapeutic_response(
                        user_input, intent_result, conversation, session_id
                    )
                    
                    # Add AI response to conversation
                    conversation.append({"role": "assistant", "content": therapeutic_response.response_text})
                    
                    # Update conversation history
                    self.conversations[session_id] = conversation
                    
                    # Handle crisis escalation
                    if therapeutic_response.crisis_escalation and safety_assessment:
                        crisis_message = self._handle_crisis_escalation(safety_assessment)
                        if crisis_message:
                            return f"{therapeutic_response.response_text}\n\n{crisis_message}"
                    
                    return therapeutic_response.response_text
                    
                except Exception as e:
                    print(f"Warning: Therapeutic response generation failed: {e}")
                    # Fall back to basic response
                    return self._generate_basic_response(user_input, conversation)
            
            # Fallback to basic response if advanced capabilities unavailable
            return self._generate_basic_response(user_input, conversation)
            
        except Exception as e:
            print(f"Error in therapeutic response: {e}")
            return "Maaf, saya sedang mengalami gangguan teknis. Bisakah Anda ulangi yang tadi?"

    def speech_to_text(self, audio_data: bytes) -> str:
        """Convert speech to text using Whisper API with new client format"""
        try:
            # Create a temporary file-like object
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "temp_audio.wav"
            
            # Transcribe using Whisper with new client format
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                prompt="",
                language="id"  # Indonesian language code
            )
            
            return transcript.text.strip()
            
        except Exception as e:
            print(f"Error in speech-to-text: {e}")
            return ""
    
    def text_to_speech(self, text: str) -> bytes:
        """Convert text to speech using OpenAI TTS API with new client format"""
        try:
            response = self.client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",  # Works well for Indonesian
                input=text,
                response_format="mp3",
            )
            
            return response.content
            
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
            return b""
    
    def record_audio(self, duration: int = None) -> bytes:
        """Record audio from microphone"""
        if not self.audio:
            raise RuntimeError("PyAudio not available for recording")
            
        if duration is None:
            duration = self.record_seconds
        
        print(f"🎤 Merekam selama {duration} detik...")
        
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        frames = []
        for i in range(0, int(self.rate / self.chunk * duration)):
            data = stream.read(self.chunk)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        # Convert to WAV format
        audio_buffer = io.BytesIO()
        with wave.open(audio_buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
        
        return audio_buffer.getvalue()
    
    def play_audio(self, audio_data: bytes) -> bool:
        """Play audio using pygame"""
        if not PYGAME_AVAILABLE:
            print("Audio playback not available")
            return False
        
        try:
            # Create temporary file
            temp_file = f"temp_audio_{uuid.uuid4().hex}.mp3"
            
            with open(temp_file, 'wb') as f:
                f.write(audio_data)
            
            # Play audio
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # Clean up
            os.remove(temp_file)
            
            return True
            
        except Exception as e:
            print(f"Error playing audio: {e}")
            return False
    
    def listen_and_respond(self, session_id: str = None) -> Dict:
        """Complete voice interaction cycle"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        try:
            # Record audio
            print("🎤 Silakan berbicara... (tekan Enter untuk berhenti merekam)")
            audio_data = self.record_audio()
            
            # Convert to text
            print("🔄 Memproses suara Anda...")
            user_text = self.speech_to_text(audio_data)
            
            if not user_text:
                return {
                    "success": False,
                    "error": "Maaf, saya tidak dapat mendengar suara Anda dengan jelas. Silakan coba lagi."
                }
            
            print(f"👤 Anda: {user_text}")
            
            # Generate therapeutic response
            print("🧠 Memproses respons terapeutik...")
            ai_response = self._get_therapeutic_response(user_text, session_id)
            print(f"🤖 Kak Indira: {ai_response}")
            
            # Convert to speech
            print("🔊 Menghasilkan audio respons...")
            audio_response = self.text_to_speech(ai_response)
            
            # Play audio
            if audio_response:
                print("📢 Memainkan respons audio...")
                self.play_audio(audio_response)
            
            return {
                "success": True,
                "user_text": user_text,
                "ai_response": ai_response,
                "audio_response": audio_response,
                "session_id": session_id
            }
            
        except Exception as e:
            error_msg = f"Terjadi kesalahan: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "session_id": session_id
            }

    def _generate_basic_response(self, user_input: str, conversation: List[Dict]) -> str:
        """Generate basic therapeutic response as fallback"""
        try:
            # Prepare messages for API
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(conversation)
            
            # Generate response using new client format
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
                max_tokens=250,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error in basic response generation: {e}")
            return "Saya mendengar Anda. Bisakah Anda ceritakan lebih lanjut tentang perasaan Anda?"
    
    def _handle_crisis_escalation(self, safety_assessment: SafetyAssessment) -> Optional[str]:
        """Handle crisis escalation based on safety assessment"""
        if not safety_assessment.emergency_contact:
            return None
        
        crisis_message = "\n⚠️ PENTING - BANTUAN DARURAT:"
        
        if safety_assessment.alert_level.value == "red":
            crisis_message += "\n🚨 Hubungi segera: 119 (Pencegahan Bunuh Diri)"
            crisis_message += "\n🏥 Atau: 118 (Gawat Darurat)"
            crisis_message += "\n👮 Jika dalam bahaya: 110 (Polisi)"
        elif safety_assessment.alert_level.value == "orange":
            crisis_message += "\n📞 Hubungi: 500-454 (Crisis Mental Health)"
            crisis_message += "\n🆘 Atau: 119 (Pencegahan Bunuh Diri)"
        
        crisis_message += "\n\n💙 Anda tidak sendirian. Bantuan tersedia 24/7."
        
        return crisis_message
    
    def get_session_analysis(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session analysis"""
        if session_id not in self.session_metadata:
            return {"error": "Session not found"}
        
        metadata = self.session_metadata[session_id]
        analysis = {
            "session_id": session_id,
            "total_interactions": metadata.get("total_interactions", 0),
            "last_update": datetime.now().isoformat()
        }
        
        # Add safety assessment info
        if "last_safety_assessment" in metadata:
            safety = metadata["last_safety_assessment"]
            analysis["safety_status"] = {
                "alert_level": safety.alert_level.value,
                "risk_factors_count": len(safety.risk_factors),
                "requires_escalation": safety.referral_needed,
                "emergency_contact": safety.emergency_contact
            }
        
        # Add intent analysis info
        if "last_intent_analysis" in metadata:
            intent = metadata["last_intent_analysis"]
            analysis["intent_status"] = {
                "primary_emotion": intent.primary_emotion.value,
                "therapeutic_context": intent.therapeutic_context.value,
                "emotion_intensity": intent.emotion_intensity,
                "confidence_score": intent.confidence_score
            }
        
        return analysis
    
    def create_session_consent(self, session_id: str, ip_address: str, consent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create session consent record"""
        if not self.safety_mechanisms:
            return {"error": "Safety mechanisms not available"}
        
        try:
            consent_record = self.safety_mechanisms.create_session_consent(session_id, ip_address, consent_data)
            self.session_consent_records[session_id] = consent_record
            return {
                "success": True,
                "session_id": session_id,
                "consent_timestamp": consent_record.consent_timestamp.isoformat(),
                "retention_period": consent_record.retention_period
            }
        except Exception as e:
            return {"error": f"Failed to create consent record: {e}"}
    
    def get_crisis_resources(self) -> Dict[str, Any]:
        """Get crisis resources and emergency contacts"""
        resources = {
            "emergency_contacts": {
                "suicide_prevention": "119",
                "medical_emergency": "118",
                "police": "110",
                "mental_health_crisis": "500-454",
                "women_crisis": "021-7270005",
                "child_protection": "129"
            },
            "professional_resources": {
                "psychiatrist": "Dokter Spesialis Jiwa",
                "psychologist": "Psikolog Klinis",
                "counselor": "Konselor Berlisensi",
                "community_health": "Puskesmas"
            },
            "online_resources": [
                "https://www.sehatjiwa.id",
                "https://www.halodoc.com (Konsultasi Online)",
                "https://www.alodokter.com (Psikologi Online)"
            ]
        }
        
        # Add resources from safety mechanisms if available
        if self.safety_mechanisms:
            resources["detailed_emergency"] = self.safety_mechanisms.get_crisis_resources()
            resources["cultural_resources"] = self.safety_mechanisms.get_cultural_resources()
        
        return resources

    def cleanup(self):
        """Clean up resources"""
        if self.audio:
            self.audio.terminate()
        
        if PYGAME_AVAILABLE:
            pygame.mixer.quit()

    async def optimized_therapeutic_response(self, user_input: str, session_id: str) -> str:
        """Parallel processing for faster response"""
        
        # Start multiple tasks concurrently
        tasks = []
        
        # Task 1: Intent Analysis (can start immediately)
        intent_task = asyncio.create_task(
            self._async_intent_analysis(user_input, session_id)
        )
        
        # Task 2: Quick safety patterns (lightweight, immediate)
        safety_patterns_task = asyncio.create_task(
            self._quick_safety_patterns(user_input)
        )
        
        # Wait for quick results
        quick_safety = await safety_patterns_task
        
        # If immediate crisis detected, skip full analysis
        if quick_safety.get('immediate_crisis'):
            return self._generate_crisis_response(quick_safety)
        
        # Continue with full analysis
        intent_result = await intent_task
        
        # Parallel: Safety Assessment + Response Generation
        safety_task = asyncio.create_task(
            self._async_safety_assessment(user_input, intent_result, session_id)
        )
        
        response_task = asyncio.create_task(
            self._async_therapeutic_response(user_input, intent_result, session_id)
        )
        
        # Wait for both
        safety_result, therapeutic_response = await asyncio.gather(
            safety_task, response_task
        )
        
        # Handle crisis escalation if needed
        if safety_result.emergency_contact_needed:
            return self._add_crisis_info(therapeutic_response, safety_result)
        
        return therapeutic_response

    async def stream_therapeutic_response(self, user_input: str, intent_result: IntentAnalysisResult):
        """Stream response as it's generated"""
        
        response = await self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=self._prepare_messages(user_input, intent_result),
            max_tokens=200,  # Reduced for speed
            temperature=0.7,
            stream=True  # Enable streaming
        )
        
        full_response = ""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                chunk_text = chunk.choices[0].delta.content
                full_response += chunk_text
                
                # Send partial response to frontend
                yield {
                    "type": "partial_response",
                    "content": chunk_text,
                    "full_so_far": full_response
                }
        
        # Send final response
        yield {
            "type": "final_response", 
            "content": full_response,
            "start_tts": True  # Signal to start TTS
        }

    async def progressive_tts(self, text_stream):
        """Generate TTS for complete sentences as they arrive"""
        
        sentence_buffer = ""
        sentence_endings = ['.', '!', '?', '\n']
        
        async for chunk in text_stream:
            sentence_buffer += chunk
            
            # Check if we have a complete sentence
            if any(ending in sentence_buffer for ending in sentence_endings):
                sentences = self._split_sentences(sentence_buffer)
                
                for complete_sentence in sentences[:-1]:  # All but last
                    # Generate TTS for complete sentence
                    audio_chunk = await self._quick_tts(complete_sentence)
                    yield {
                        "type": "audio_chunk",
                        "audio": audio_chunk,
                        "text": complete_sentence
                    }
                
                # Keep incomplete sentence in buffer
                sentence_buffer = sentences[-1] if sentences else ""

    async def voice_therapy_optimized(self, audio_data: bytes, session_id: str):
        """Optimized voice therapy with parallel processing"""
        
        # Step 1: Speech-to-Text (must be first)
        user_text = await self._async_speech_to_text(audio_data)
        
        # Step 2: Start response generation
        response_task = asyncio.create_task(
            self.optimized_therapeutic_response(user_text, session_id)
        )
        
        # Step 3: Get response text
        ai_response = await response_task
        
        # Step 4: Start TTS immediately (don't wait for UI update)
        tts_task = asyncio.create_task(
            self._async_text_to_speech(ai_response)
        )
        
        # Return text immediately, audio will follow
        return {
            "user_text": user_text,
            "ai_response": ai_response,
            "audio_task": tts_task  # Let frontend handle this
        }

class ResponseCache:
    def __init__(self):
        self.intent_cache = {}
        self.response_templates = {}
        self.common_patterns = self._load_common_patterns()
    
    def _load_common_patterns(self):
        return {
            "greeting": {
                "patterns": ["halo", "hai", "selamat", "assalamualaikum"],
                "response": "Halo! Saya Kak Indira. Apa yang ingin Anda ceritakan hari ini?",
                "intent": {"emotion": "neutral", "context": "general_support"}
            },
            "anxiety_light": {
                "patterns": ["cemas", "khawatir", "takut", "nervous"],
                "response_template": "anxiety_management_basic",
                "intent": {"emotion": "anxious", "context": "anxiety_management"}
            },
            "gratitude": {
                "patterns": ["terima kasih", "thanks", "syukur"],
                "response": "Sama-sama. Saya senang bisa membantu Anda.",
                "intent": {"emotion": "grateful", "context": "general_support"}
            }
        }
    
    async def quick_response_check(self, user_input: str) -> Optional[dict]:
        """Check for common patterns that don't need full analysis"""
        user_lower = user_input.lower()
        
        for pattern_name, pattern_data in self.common_patterns.items():
            for pattern in pattern_data["patterns"]:
                if pattern in user_lower:
                    return {
                        "response": pattern_data["response"],
                        "intent": pattern_data["intent"],
                        "cached": True,
                        "pattern": pattern_name
                    }
        return None

def main():
    """Main function for testing"""
    try:
        bot = IndonesianMentalHealthBot()
        
        print("\n🌟 Selamat datang di Layanan Dukungan Kesehatan Mental Indonesia!")
        print("🗣️  Berbicara dengan Kak Indira - Konselor Digital Anda")
        print("📱 Tekan Ctrl+C untuk berhenti\n")
        
        session_id = str(uuid.uuid4())
        
        while True:
            try:
                result = bot.listen_and_respond(session_id)
                
                if not result["success"]:
                    print(f"❌ {result['error']}")
                
                print("\n" + "="*50 + "\n")
                
            except KeyboardInterrupt:
                print("\n🙏 Terima kasih telah menggunakan layanan kami!")
                print("💚 Semoga hari Anda menyenangkan!")
                break
                
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        
    finally:
        if 'bot' in locals():
            bot.cleanup()

if __name__ == "__main__":
    main()
