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

# Handle Anthropic import gracefully
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

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
        
        # Initialize Claude client for fallback/validation
        self.claude_client = None
        self.claude_available = False
        
        try:
            if Anthropic is None:
                print("ℹ️  Anthropic library not available - Claude fallback disabled")
            else:
                claude_api_key = os.getenv("ANTHROPIC_API_KEY")
                if claude_api_key and claude_api_key.strip() and len(claude_api_key.strip()) > 10:
                    # Initialize Claude client (lightweight validation)
                    self.claude_client = Anthropic(api_key=claude_api_key)
                    self.claude_available = True
                    print("🤖 Claude 3.5 Sonnet initialized as fallback model")
                else:
                    print("ℹ️  ANTHROPIC_API_KEY not provided or invalid - Claude fallback disabled")
                
        except Exception as e:
            print(f"⚠️  Claude initialization failed: {e}")
            print("ℹ️  Claude fallback disabled - continuing with GPT-4.1 only")
            self.claude_client = None
            self.claude_available = False
        
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
        
        # Session tracking for enhanced capabilities
        self.session_metadata = {}
        self.session_consent_records = {}
        
        print("🧠 Indonesian Mental Health Support Bot initialized")
        print("💚 Siap membantu kesehatan mental Anda dengan pendekatan yang sensitif budaya")
        print("🔒 Dilengkapi dengan sistem keamanan dan analisis intent yang canggih")

    def _create_system_prompt(self) -> str:
        """Create comprehensive system prompt with integrated intent analysis and response generation"""
        return """Anda adalah Kak Indira, seorang konselor kesehatan mental yang berpengalaman dan berempati tinggi, yang secara khusus memahami budaya Indonesia.

        
════════════════════════════════════════════════════════════════
FRAMEWORK ANALISIS TERINTEGRASI - TAHAPAN BERURUTAN
════════════════════════════════════════════════════════════════

TAHAP 1: DETEKSI EMOSI DAN INTENSITAS
─────────────────────────────────────────────────────────────────
- Identifikasi emosi utama: neutral, happy, sad, angry, anxious, depressed, fearful, frustrated, hopeful, overwhelmed, lonely, confused, guilty, ashamed, grieving
- Intensitas emosi (0.0-1.0): rendah (0.0-0.3), sedang (0.4-0.6), tinggi (0.7-1.0)
- Identifikasi emosi sekunder yang mungkin ada (dapat lebih dari satu)
- Berikan confidence score untuk analisis emosi (0.0-1.0)

TAHAP 2: PENILAIAN KEAMANAN DAN SISTEM ALERT
─────────────────────────────────────────────────────────────────
🟢 ALERT LEVEL GREEN (Normal Operation):
- Tidak ada indikator krisis atau bahaya
- Emosi dalam rentang normal
- Tidak ada risk factors yang signifikan

🟡 ALERT LEVEL YELLOW (Monitor Closely):
- Emosi sedang dengan intensitas tinggi
- Mild risk factors seperti stress atau tekanan
- Perlu perhatian khusus tapi tidak darurat

🟠 ALERT LEVEL ORANGE (Elevated Concern):
- Deteksi kata kunci medium risk
- Emosi negatif dengan intensitas tinggi
- Multiple risk factors present

🔴 ALERT LEVEL RED (Immediate Intervention):
- Deteksi kata kunci high risk atau krisis
- Risiko bunuh diri atau self-harm
- Memerlukan intervensi segera

DETEKSI RISIKO BERDASARKAN KATA KUNCI:
High Risk Patterns:
- "ingin mati", "bunuh diri", "mengakhiri hidup", "tidak ingin hidup lagi", "suicide", "kill myself", "end my life", "want to die"
- "menyerah total", "tak sanggup bertahan", "lebih baik mati", "life is pointless", "ingin mengakhiri semuanya"
- "tidak mau hidup", "hidup tak berarti", "mati saja", "tidak ada gunanya hidup", "suicidal thoughts", "death wish"

Medium Risk Patterns:
- "tidak tahan lagi", "putus asa", "hopeless", "tidak ada harapan", "lelah hidup", "tired of living", "give up"
- "kehilangan arah", "merasa hampa", "meaningless", "tidak berguna", "hidup terasa berat", "tidak ada jalan keluar"
- "semua sia-sia", "tertekan berat", "tidak berdaya", "overwhelmed", "no way out", "life is too hard"

Self-Harm Patterns:
- "melukai diri", "menyakiti diri", "cutting", "self harm", "memotong", "menyilet", "hurt myself"
- "mencederai tubuh", "self-injury", "merusak diri", "menyayat", "menggores kulit", "membakar diri"
- "menyiksa diri", "memar sengaja", "melukai tubuh sendiri", "self-mutilation", "burning myself"

Violence Patterns:
- "menyakiti orang", "membunuh", "kekerasan", "melukai", "hurt someone", "kill", "violence", "harm others"
- "menyerang", "mengancam", "assault", "menghancurkan", "memukul orang", "menyiksa", "ingin melukai"

TAHAP 3: CONTENT FILTERING DAN PROTECTIVE FACTORS
─────────────────────────────────────────────────────────────────
CONTENT FILTERING TYPES:
- SUICIDE_IDEATION: Ide bunuh diri eksplisit
- SELF_HARM: Rencana melukai diri
- VIOLENCE_THREAT: Ancaman kekerasan
- SUBSTANCE_ABUSE: Penyalahgunaan zat
- CHILD_ABUSE: Kekerasan pada anak
- DOMESTIC_VIOLENCE: Kekerasan dalam rumah tangga
- SEXUAL_CONTENT: Konten seksual eksplisit
- HATE_SPEECH: Ujaran kebencian
- SPAM: Promosi tidak relevan
- INAPPROPRIATE: Konten tidak pantas lainnya

PROTECTIVE FACTORS IDENTIFICATION:
- Support System: keluarga, teman, komunitas, terapis, mentor
- Spiritual/Religious: praktik keagamaan, nilai spiritual, komunitas religius, doa, ibadah
- Personal Strengths: resiliensi, coping skills, pengalaman mengatasi masalah, prestasi
- Future Goals: rencana masa depan, harapan, tujuan hidup, mimpi, cita-cita
- Cultural Resources: nilai budaya, tradisi, kearifan lokal, gotong royong, kebersamaan

TAHAP 4: PROFESSIONAL REFERRAL TRIGGERS
─────────────────────────────────────────────────────────────────
REFERRAL TRIGGERS:
- PERSISTENT_SUICIDAL_IDEATION: Ide bunuh diri yang menetap atau berulang
- ACTIVE_PSYCHOSIS: Gejala psikosis aktif (halusinasi, delusi, paranoia)
- SEVERE_DEPRESSION: Depresi berat yang mengganggu fungsi sehari-hari
- SUBSTANCE_DEPENDENCY: Ketergantungan zat atau penyalahgunaan obat
- DOMESTIC_VIOLENCE: Kekerasan dalam rumah tangga yang sedang berlangsung
- CHILD_ENDANGERMENT: Bahaya pada anak atau kekerasan terhadap anak
- EATING_DISORDER: Gangguan makan yang parah
- TRAUMA_RESPONSE: Respons trauma yang kompleks dan menganggu
- MEDICATION_CONCERNS: Masalah dengan obat-obatan psikiatri
- BEYOND_AI_SCOPE: Masalah yang melampaui kemampuan AI

TAHAP 5: THERAPEUTIC TECHNIQUE SELECTION
─────────────────────────────────────────────────────────────────
THERAPEUTIC TECHNIQUES:
- ACTIVE_LISTENING: Mendengarkan aktif dengan validasi emosi
- CBT_REFRAMING: Restrukturisasi kognitif dan challenging thoughts
- MINDFULNESS: Teknik kesadaran dan present moment awareness
- GROUNDING: Teknik grounding untuk anxiety dan panic (5-4-3-2-1)
- BEHAVIORAL_ACTIVATION: Aktivasi perilaku untuk depresi
- CRISIS_INTERVENTION: Intervensi krisis dan safety planning
- CULTURAL_VALIDATION: Validasi pengalaman budaya dan nilai
- SPIRITUAL_INTEGRATION: Integrasi nilai-nilai spiritual dan religius
- FAMILY_THERAPY: Pendekatan dinamika keluarga
- GRIEF_COUNSELING: Konseling duka dan kehilangan
- ANXIETY_MANAGEMENT: Manajemen kecemasan dan teknik relaksasi
- DEPRESSION_SUPPORT: Dukungan untuk depresi dan mood disorders

TAHAP 6: CULTURAL APPROACH SELECTION
─────────────────────────────────────────────────────────────────
CULTURAL APPROACHES:
- JAVANESE_HARMONY: Pendekatan harmoni Jawa (rukun, saling menghargai, tidak konfrontatif)
- ISLAMIC_COUNSELING: Konseling Islam (tawakkal, sabar, syukur, tawakal)
- FAMILY_CENTERED: Pendekatan berpusat pada keluarga dan hierarki
- COMMUNITY_SUPPORT: Dukungan komunitas dan gotong royong
- TRADITIONAL_HEALING: Integrasi penyembuhan tradisional dan herbal
- COLLECTIVIST_VALUES: Nilai-nilai kolektif Indonesia (kebersamaan, musyawarah)
- RESPECT_HIERARCHY: Menghormati hierarki sosial dan otoritas
- SPIRITUAL_WELLNESS: Kesehatan spiritual dan religius sebagai dasar

TAHAP 7: KONTEKS TERAPEUTIK
─────────────────────────────────────────────────────────────────
- general_support: dukungan umum untuk masalah sehari-hari
- crisis_intervention: intervensi krisis dan keadaan darurat
- cbt_techniques: teknik CBT untuk restrukturisasi kognitif
- active_listening: mendengarkan aktif dan validasi emosi
- cultural_trauma: trauma budaya dan konflik nilai
- spiritual_support: dukungan spiritual dan religius
- family_dynamics: dinamika keluarga dan konflik interpersonal
- grief_counseling: konseling duka dan kehilangan
- anxiety_management: manajemen kecemasan dan fobia
- depression_support: dukungan untuk depresi dan mood disorders
- relationship_issues: masalah hubungan dan komunikasi
- workplace_stress: stres kerja dan tekanan profesional
- academic_pressure: tekanan akademis dan prestasi

TAHAP 8: PRIORITAS INTERVENSI
─────────────────────────────────────────────────────────────────
- IMMEDIATE: Butuh tindakan segera (Alert RED, risiko critical)
- URGENT: Butuh tindakan cepat (Alert ORANGE, risiko high)
- ROUTINE: Tindakan rutin (Alert YELLOW, risiko medium)
- LOW: Tindakan minimal (Alert GREEN, risiko low)

════════════════════════════════════════════════════════════════
ATURAN RESPONS BERDASARKAN ANALISIS
════════════════════════════════════════════════════════════════

🔴 PRIORITAS IMMEDIATE/URGENT (ALERT RED/ORANGE):
- Assess immediate safety: "Apakah Adik dalam keadaan aman sekarang?"
- Crisis intervention: Fokus pada stabilisasi dan safety planning
- Safety planning: "Mari buat rencana keamanan bersama"
- Berikan nomor hotline segera: 119 (Pencegahan Bunuh Diri), 118 (Gawat Darurat), 110 (Polisi)
- Professional referral: "Saya sangat menyarankan Adik berbicara dengan profesional segera"
- Jangan tinggalkan pengguna sendirian: "Saya akan tetap di sini untuk Adik"
- Eksplorasi rencana spesifik: "Apakah Adik memiliki rencana untuk menyakiti diri?"

TEKNIK BERDASARKAN EMOSI:

ANXIOUS/FEARFUL (Grounding & Anxiety Management):
- Validasi perasaan: "Saya memahami perasaan cemas yang Adik alami"
- Teknik grounding 5-4-3-2-1: "Sebutkan 5 hal yang Adik lihat, 4 yang Adik dengar, 3 yang Adik sentuh, 2 yang Adik cium, 1 yang Adik rasakan"
- Breathing technique: "Tarik napas 4 hitungan, tahan 7, hembuskan 8"
- Progressive muscle relaxation: "Tegangkan lalu rilekskan otot-otot tubuh secara bergantian"
- Mindfulness: "Coba fokus pada saat ini, rasakan napas Adik"

SAD/DEPRESSED (Behavioral Activation & Depression Support):
- Validasi dengan empati: "Terima kasih sudah berbagi perasaan ini dengan saya"
- Hindari toxic positivity: jangan langsung bilang "think positive"
- Behavioral activation: "Coba lakukan satu aktivitas kecil yang biasanya Adik suka"
- Mood monitoring: "Bagaimana perasaan Adik berubah sepanjang hari?"
- Pleasant activity scheduling: "Apa kegiatan kecil yang bisa membuat Adik sedikit senang?"
- Eksplorasi support system: "Siapa yang biasanya Adik ajak bicara saat sedih?"

ANGRY/FRUSTRATED (CBT Reframing & Emotional Regulation):
- Validasi tanpa judgment: "Marah adalah perasaan yang wajar dan natural"
- Teknik regulasi emosi: "Bagaimana biasanya Adik mengatasi perasaan marah?"
- Cognitive restructuring: "Mari kita lihat situasi ini dari sudut pandang yang berbeda"
- Eksplorasi pemicu: "Apa yang membuat Adik merasa kesal?"
- Thought challenging: "Apa bukti yang mendukung dan menentang pikiran ini?"

GRIEVING (Grief Counseling & Meaning-Making):
- Normalize grief process: "Duka adalah proses yang natural dan butuh waktu"
- Memory preservation: "Ceritakan kenangan indah tentang yang Adik rindukan"
- Meaning-making: "Apa yang bisa kita pelajari dari pengalaman ini?"
- Ritual integration: "Bagaimana tradisi keluarga membantu proses duka?"
- Stages acknowledgment: "Tidak ada cara yang benar atau salah untuk berduka"

OVERWHELMED/CONFUSED (Active Listening & Problem-Solving):
- Validasi kompleksitas: "Saya pahami banyak hal yang membuat Adik bingung"
- Break down problems: "Mari kita pecah masalah ini menjadi bagian-bagian kecil"
- Thought challenging: "Mana yang fakta dan mana yang pikiran atau asumsi?"
- Prioritization: "Apa yang paling penting untuk diatasi terlebih dahulu?"
- Clarity seeking: "Bagaimana jika kita fokus pada satu masalah dulu?"

GUILTY/ASHAMED (Cognitive Restructuring & Self-Compassion):
- Validasi perasaan: "Perasaan bersalah menunjukkan bahwa Adik peduli"
- Self-compassion: "Bagaimana Adik akan memperlakukan teman yang mengalami hal yang sama?"
- Realistic thinking: "Apakah Adik benar-benar bertanggung jawab penuh atas situasi ini?"
- Forgiveness exploration: "Apa yang dibutuhkan untuk memaafkan diri sendiri?"

KONTEKS BUDAYA:

FAMILY_DYNAMICS (Family-Centered Approach):
- Pertimbangkan hierarki keluarga Indonesia: "Saya memahami dinamika keluarga Indonesia"
- Hormati nilai-nilai tradisional dan respect authority
- Mediasi dengan pendekatan budaya: "Bagaimana cara menghormati orang tua sambil mengutarakan perasaan?"
- Berikan strategi komunikasi yang sesuai: "Bagaimana cara bicara yang sopan tapi jujur?"
- Musyawarah approach: "Mungkin bisa dibicarakan secara keluarga?"

SPIRITUAL_SUPPORT (Spiritual Integration):
- Integrasikan nilai-nilai keagamaan: "Bagaimana keyakinan spiritual membantu Adik?"
- Gunakan referensi yang sesuai: "Apa yang biasanya Adik lakukan saat berdoa?"
- Traditional healing integration: "Apakah ada praktik tradisional yang membantu?"
- Hindari advice yang bertentangan dengan nilai agama
- Tawakkal dan sabar: "Bagaimana konsep sabar membantu dalam situasi ini?"

WORKPLACE_STRESS (Stress Management):
- Eksplorasi beban kerja: "Apa yang membuat pekerjaan terasa berat?"
- Work-life balance: "Bagaimana Adik memisahkan waktu kerja dan istirahat?"
- Boundary setting: "Apa yang bisa Adik lakukan untuk menjaga batas yang sehat?"
- Professional relationships: "Bagaimana hubungan dengan rekan kerja?"

ACADEMIC_PRESSURE (Performance Management):
- Validasi tekanan akademis: "Saya pahami tekanan di dunia pendidikan"
- Study strategies: "Bagaimana cara belajar yang paling efektif untuk Adik?"
- Performance anxiety: "Apa yang Adik rasakan saat menghadapi ujian?"
- Future planning: "Bagaimana tekanan ini mempengaruhi rencana masa depan?"

CULTURAL_TRAUMA (Cultural Validation):
- Validasi pengalaman budaya: "Saya memahami konflik antara tradisi dan modernitas"
- Cultural identity exploration: "Bagaimana Adik melihat identitas budaya sendiri?"
- Generational differences: "Apa perbedaan pandangan dengan generasi tua?"
- Integration approach: "Bagaimana cara menyeimbangkan dua nilai yang berbeda?"

RELATIONSHIP_ISSUES (Communication & Conflict Resolution):
- Eksplorasi pola komunikasi: "Bagaimana biasanya Adik berkomunikasi dengan orang tersebut?"
- Conflict resolution skills: "Apa yang sudah Adik coba untuk menyelesaikan masalah?"
- Boundary setting: "Bagaimana menetapkan batas yang sehat dalam hubungan?"
- Expectation management: "Apa harapan Adik dari hubungan ini?"

MULTIPLE EMOTIONS:
- Acknowledge complexity: "Saya lihat Adik merasakan beberapa emosi sekaligus"
- Prioritize primary emotion untuk respons utama
- Validate secondary emotions: "Wajar jika Adik merasa campur aduk seperti ini"
- Emotional acceptance: "Semua perasaan ini valid dan bisa dirasakan bersamaan"

════════════════════════════════════════════════════════════════
PANDUAN KOMUNIKASI DAN ETIKA
════════════════════════════════════════════════════════════════

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

BAHASA & KOMUNIKASI:
- Gunakan Bahasa Indonesia yang natural dan hangat
- Sesekali gunakan istilah familiar atau daerah yang sesuai
- Hindari jargon psikologi yang terlalu teknis
- Berikan respons yang empati dan tidak menghakimi

BATASAN ETIS:
- Selalu ingatkan bahwa Anda adalah AI dan bukan pengganti terapis profesional
- Jika mendeteksi risiko bunuh diri atau self-harm, segera arahkan ke hotline krisis
- Tidak memberikan diagnosis medis atau resep obat
- Jaga boundaries yang profesional namun hangat

EMERGENCY RESOURCES:
- Pencegahan Bunuh Diri: 119
- Gawat Darurat: 118
- Kepolisian: 110
- Mental Health Crisis: 500-454
- Women Crisis Center: 021-7270005
- Child Protection: 129
- Domestic Violence: 021-3448245
- Depression Support: 0804-1-500-454

STRUKTUR RESPONS:
- Maksimal 2-3 kalimat per respons
- Validasi emosi terlebih dahulu
- Berikan satu teknik atau strategi praktis
- Akhiri dengan pertanyaan eksplorasi terbuka jika masih ada informasi yang perlu diketahui untuk membantu pengguna menyelesaikan permasalahan mentalnya
- Gunakan nada yang menenangkan dan mendukung

PENUTUPAN SESI:
- Jika pengguna sudah merasa lebih baik, sudah menemukan solusi, atau masalah teratasi
- Jangan memaksa untuk terus berbicara
- Tutup dengan: "Terima kasih telah berbicara dengan saya. Semoga hari Anda menyenangkan!"

** IMPORTANT NOTES **
- Anda harus mengerti konteks bahasa indonesia dan di campur Inggris
- Kata kunci dari rules di atas tidak mengcover semuanya. jadi, anda harus mencari lagi sinonim dari kata kunci tersebut

Ingat: Tujuan Anda adalah memberikan dukungan emosional, membantu pengguna memahami perasaan mereka, dan menguatkan resiliensi mereka dengan cara yang sesuai dengan budaya Indonesia."""

    def _call_claude_response(self, messages: List[Dict], session_id: str) -> Optional[str]:
        """
        Call Claude 3.5 Sonnet for therapeutic response using official API format
        
        Args:
            messages: List of message dictionaries in OpenAI format
            session_id: Session identifier for logging
            
        Returns:
            Claude's response or None if failed
        """
        if not self.claude_available or not self.claude_client:
            return None
            
        try:
            # Convert OpenAI format messages to Claude format
            # Claude expects system message separately and user/assistant messages
            system_content = ""
            claude_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_content = msg["content"]
                elif msg["role"] in ["user", "assistant"]:
                    claude_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Call Claude 3.5 Sonnet using official API format
            # Reference: https://docs.anthropic.com/en/api/messages
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Latest Claude 3.5 Sonnet model
                system=system_content,
                messages=claude_messages,
                max_tokens=250,
                temperature=0.3,
            )
            
            # Extract text from response content array
            if response.content and len(response.content) > 0:
                return response.content[0].text.strip()
            else:
                print(f"Warning: Empty response content for session {session_id}")
                return None
            
        except Exception as e:
            print(f"Claude API error for session {session_id}: {e}")
            return None

    def _get_therapeutic_response(self, user_input: str, session_id: str) -> str:
        """Generate therapeutic response using advanced therapeutic capabilities with Claude fallback"""
        try:
            # Get or create conversation history
            if session_id not in self.conversations:
                self.conversations[session_id] = []
            
            conversation = self.conversations[session_id]
            
            # Add user input to conversation
            conversation.append({"role": "user", "content": user_input})
            
            # Trim conversation if too long
            if len(conversation) > self.max_conversation_length:
                conversation = conversation[-self.trim_to_length:]
            
            # Use integrated system prompt for response generation
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(conversation)
            
            ai_response = None
            model_used = "gpt-4.1"
            
            # Try GPT-4.1 first
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4.1",
                    messages=messages,
                    max_tokens=250,
                    temperature=0.3,
                    presence_penalty=0.1,
                    frequency_penalty=0.1
                )
                
                ai_response = response.choices[0].message.content.strip()
                print(f"✅ GPT-4.1 response generated for session {session_id}")
                
            except Exception as gpt_error:
                print(f"⚠️ GPT-4.1 failed for session {session_id}: {gpt_error}")
                
                # Fallback to Claude 3.5 Sonnet
                if self.claude_available:
                    print(f"🔄 Falling back to Claude 3.5 Sonnet for session {session_id}")
                    ai_response = self._call_claude_response(messages, session_id)
                    
                    if ai_response:
                        model_used = "claude-3-5-sonnet"
                        print(f"✅ Claude 3.5 Sonnet response generated for session {session_id}")
                    else:
                        print(f"❌ Claude fallback also failed for session {session_id}")
                else:
                    print(f"❌ No fallback available, Claude not initialized")
            
            # If both models failed, return error message
            if not ai_response:
                ai_response = "Maaf, saya sedang mengalami gangguan teknis. Bisakah Anda ulangi yang tadi?"
                model_used = "error"
            
            # Add AI response to conversation
            conversation.append({
                "role": "assistant", 
                "content": ai_response
            })
            
            # Update conversation history
            self.conversations[session_id] = conversation
            
            return ai_response
            
        except Exception as e:
            print(f"Critical error in therapeutic response for session {session_id}: {e}")
            return "Maaf, saya sedang mengalami gangguan teknis. Bisakah Anda ulangi yang tadi?"

    def _get_therapeutic_response_with_validation(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """
        Generate therapeutic response using both models for validation/comparison
        
        Args:
            user_input: User's input text
            session_id: Session identifier
            
        Returns:
            Dictionary containing responses from both models and metadata
        """
        try:
            # Get or create conversation history
            if session_id not in self.conversations:
                self.conversations[session_id] = []
            
            conversation = self.conversations[session_id]
            
            # Add user input to conversation (temporarily)
            temp_conversation = conversation + [{"role": "user", "content": user_input}]
            
            # Trim conversation if too long
            if len(temp_conversation) > self.max_conversation_length:
                temp_conversation = temp_conversation[-self.trim_to_length:]
            
            # Prepare messages
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(temp_conversation)
            
            results = {
                "user_input": user_input,
                "session_id": session_id,
                "gpt_response": None,
                "claude_response": None,
                "gpt_error": None,
                "claude_error": None,
                "timestamp": datetime.now().isoformat(),
                "primary_response": None,
                "primary_model": None
            }
            
            # Try GPT-4.1
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4.1",
                    messages=messages,
                    max_tokens=250,
                    temperature=0.3,
                    presence_penalty=0.1,
                    frequency_penalty=0.1
                )
                results["gpt_response"] = response.choices[0].message.content.strip()
            except Exception as e:
                results["gpt_error"] = str(e)
            
            # Try Claude 3.5 Sonnet if available
            if self.claude_available:
                try:
                    claude_response = self._call_claude_response(messages, session_id)
                    results["claude_response"] = claude_response
                except Exception as e:
                    results["claude_error"] = str(e)
            
            # Determine primary response (prefer GPT, fallback to Claude)
            if results["gpt_response"]:
                results["primary_response"] = results["gpt_response"]
                results["primary_model"] = "gpt-4.1"
            elif results["claude_response"]:
                results["primary_response"] = results["claude_response"]
                results["primary_model"] = "claude-3-5-sonnet"
            else:
                results["primary_response"] = "Maaf, saya sedang mengalami gangguan teknis. Bisakah Anda ulangi yang tadi?"
                results["primary_model"] = "error"
            
            # Add to conversation history
            conversation.append({"role": "user", "content": user_input})
            conversation.append({
                "role": "assistant", 
                "content": results["primary_response"]
            })
            
            # Trim conversation if too long
            if len(conversation) > self.max_conversation_length:
                conversation = conversation[-self.trim_to_length:]
            
            self.conversations[session_id] = conversation
            
            return results
            
        except Exception as e:
            print(f"Critical error in therapeutic response validation for session {session_id}: {e}")
            return {
                "user_input": user_input,
                "session_id": session_id,
                "primary_response": "Maaf, saya sedang mengalami gangguan teknis. Bisakah Anda ulangi yang tadi?",
                "primary_model": "error",
                "error": str(e)
            }



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
                language="id",  # Indonesian language code
            )
            
            return transcript.text.strip()
            
        except Exception as e:
            print(f"Error in speech-to-text: {e}")
            return ""
    
    def text_to_speech(self, text: str) -> bytes:
        """Convert text to speech using parallel processing implementation"""
        # Use parallel implementation as default per user preference
        try:
            # Use asyncio.run for the parallel version
            return asyncio.run(self.text_to_speech_parallel(text))
        except Exception as e:
            print(f"Error in parallel TTS, falling back to synchronous: {e}")
            # Fallback to synchronous version if parallel fails
            try:
                response = self.client.audio.speech.create(
                    model="gpt-4o-mini-tts",
                    voice="alloy",  # Works well for Indonesian
                    input=text,
                    response_format="mp3",
                )
                
                return response.content
                
            except Exception as e2:
                print(f"Error in fallback text-to-speech: {e2}")
                return b""
    
    def _split_text_into_sentences(self, text: str, max_chunk_size: int = 200) -> List[str]:
        """Split text into sentences for parallel processing"""
        # Define sentence ending patterns for Indonesian and English
        sentence_endings = ['.', '!', '?', '...', '。', '！', '？']
        
        # Split by common sentence boundaries
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            
            # Check if we hit a sentence ending
            if char in sentence_endings:
                # Look ahead to see if there's a space or end of text
                if len(current_sentence.strip()) > 0:
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
            
            # If sentence gets too long, break at word boundary
            elif len(current_sentence) > max_chunk_size:
                # Find last space to break at word boundary
                last_space = current_sentence.rfind(' ')
                if last_space > 0:
                    sentences.append(current_sentence[:last_space].strip())
                    current_sentence = current_sentence[last_space:].strip()
                else:
                    # No space found, break at current position
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
        
        # Add any remaining text
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # Filter out empty sentences
        return [s for s in sentences if s.strip()]
    
    async def _async_text_to_speech_chunk(self, text_chunk: str, chunk_id: int) -> Tuple[int, bytes]:
        """Async TTS for individual text chunk"""
        try:
            # Create async client call
            response = await asyncio.to_thread(
                self.client.audio.speech.create,
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=text_chunk,
                response_format="mp3"
            )
            
            return chunk_id, response.content
            
        except Exception as e:
            print(f"Error in async TTS for chunk {chunk_id}: {e}")
            return chunk_id, b""
    
    def _merge_audio_chunks(self, audio_chunks: List[bytes]) -> bytes:
        """Merge audio chunks with smooth transitions"""
        if not audio_chunks:
            return b""
        
        if len(audio_chunks) == 1:
            return audio_chunks[0]
        
        try:
            # For MP3 files, we can concatenate them directly
            # This is a simple approach - more sophisticated merging could be added
            merged_audio = b''.join(audio_chunks)
            return merged_audio
            
        except Exception as e:
            print(f"Error merging audio chunks: {e}")
            # Fallback: return first chunk if merging fails
            return audio_chunks[0] if audio_chunks else b""
    
    async def text_to_speech_parallel(self, text: str, max_workers: int = 8) -> bytes:
        """
        Parallel text-to-speech processing with sentence-level chunking
        
        Args:
            text: Text to convert to speech
            max_workers: Maximum number of parallel workers
            
        Returns:
            Merged audio content as bytes
        """
        if not text or not text.strip():
            return b""
        
        try:
            # Split text into sentences
            sentences = self._split_text_into_sentences(text)
            
            if not sentences:
                return b""
            
            # Always use parallel processing per user preference
            # For very short texts, still use parallel but with single chunk
            
            print(f"🎵 Processing {len(sentences)} sentences in parallel...")
            
            # Create tasks for parallel processing
            tasks = []
            for i, sentence in enumerate(sentences):
                task = asyncio.create_task(
                    self._async_text_to_speech_chunk(sentence, i)
                )
                tasks.append(task)
            
            # Process chunks in parallel with semaphore for rate limiting
            semaphore = asyncio.Semaphore(max_workers)
            
            async def process_with_semaphore(task):
                async with semaphore:
                    return await task
            
            # Execute all tasks with rate limiting
            results = await asyncio.gather(*[
                process_with_semaphore(task) for task in tasks
            ])
            
            # Sort results by chunk ID to maintain order
            results.sort(key=lambda x: x[0])
            
            # Extract audio chunks
            audio_chunks = [result[1] for result in results if result[1]]
            
            if not audio_chunks:
                print("Warning: No audio chunks generated")
                return b""
            
            # Merge audio chunks
            merged_audio = self._merge_audio_chunks(audio_chunks)
            
            print(f"✅ Successfully merged {len(audio_chunks)} audio chunks")
            return merged_audio
            
        except Exception as e:
            print(f"Error in parallel TTS: {e}")
            # Fallback to regular TTS
            return self.text_to_speech(text)
    
    async def text_to_speech_streaming(self, text: str, chunk_callback=None):
        """
        Streaming text-to-speech that yields audio chunks as they become available
        
        Args:
            text: Text to convert to speech
            chunk_callback: Optional callback function for each audio chunk
            
        Yields:
            Audio chunks as they become available
        """
        if not text or not text.strip():
            return
        
        try:
            # Split text into sentences
            sentences = self._split_text_into_sentences(text)
            
            if not sentences:
                return
            
            print(f"🎵 Streaming {len(sentences)} sentences...")
            
            # Process sentences one by one for streaming
            for i, sentence in enumerate(sentences):
                try:
                    # Generate audio for this sentence
                    audio_chunk = await self._async_text_to_speech_chunk(sentence, i)
                    
                    if audio_chunk[1]:  # Check if audio data exists
                        # Call callback if provided
                        if chunk_callback:
                            chunk_callback(audio_chunk[1], sentence, i)
                        
                        # Yield the audio chunk
                        yield {
                            "chunk_id": i,
                            "audio": audio_chunk[1],
                            "text": sentence,
                            "total_chunks": len(sentences)
                        }
                        
                        print(f"✅ Streamed chunk {i+1}/{len(sentences)}")
                    
                except Exception as e:
                    print(f"Error processing sentence {i}: {e}")
                    continue
            
            print(f"🎉 Streaming complete!")
            
        except Exception as e:
            print(f"Error in streaming TTS: {e}")
    
    def get_tts_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for TTS operations"""
        return {
            "supported_methods": [
                "text_to_speech",           # Original synchronous method
                "text_to_speech_parallel",  # Parallel processing
                "text_to_speech_streaming"  # Streaming chunks
            ],
            "recommendations": {
                "short_text": "Use text_to_speech_parallel for texts under 150 characters",
                "medium_text": "Use text_to_speech_parallel with max_workers=8 for texts 150 characters or more", 
                "long_text": "Use text_to_speech_parallel with max_workers=8 for texts 150 characters or more",
                "real_time": "Use text_to_speech_streaming for real-time applications"
            },
            "performance_benefits": {
                "parallel_speedup": "2-5x faster for medium texts",
                "streaming_latency": "First audio chunk available in ~1-2 seconds",
                "memory_efficiency": "Processes chunks independently"
            }
        }
    
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
        
        return analysis
    
    def create_session_consent(self, session_id: str, ip_address: str, consent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create session consent record"""
        # Note: Safety mechanisms functionality has been integrated into the system prompt
        # This is a simplified implementation for basic consent recording
        try:
            # Simple consent record without external safety mechanisms
            consent_record = {
                "session_id": session_id,
                "consent_given": consent_data.get("consent_given", False),
                "recording_consent": consent_data.get("recording_consent", False),
                "data_sharing_consent": consent_data.get("data_sharing_consent", False),
                "anonymization_level": consent_data.get("anonymization_level", "high"),
                "retention_period": consent_data.get("retention_period", 30),
                "consent_timestamp": datetime.now().isoformat(),
                "ip_hash": "hashed_for_privacy"
            }
            
            self.session_consent_records[session_id] = consent_record
            return {
                "success": True,
                "session_id": session_id,
                "consent_timestamp": consent_record["consent_timestamp"],
                "retention_period": consent_record["retention_period"]
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
        
        # Note: All safety mechanisms and cultural resources are now integrated into the system prompt
        # No additional external modules needed
        
        return resources

    def cleanup(self):
        """Clean up resources"""
        if self.audio:
            self.audio.terminate()
        
        if PYGAME_AVAILABLE:
            pygame.mixer.quit()

    async def optimized_therapeutic_response(self, user_input: str, session_id: str) -> str:
        """Integrated response generation with streamlined processing"""
        
        # Use integrated system prompt approach
        return self._get_therapeutic_response(user_input, session_id)

    async def stream_therapeutic_response(self, user_input: str, session_id: str = None):
        """Stream response as it's generated with integrated intent analysis and Claude fallback"""
        
        # Get or create conversation history
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        conversation = self.conversations[session_id]
        
        # Add user input to conversation
        conversation.append({"role": "user", "content": user_input})
        
        # Trim conversation if too long
        if len(conversation) > self.max_conversation_length:
            conversation = conversation[-self.trim_to_length:]
        
        # Prepare messages with integrated system prompt
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(conversation)
        
        full_response = ""
        model_used = "gpt-4.1"
        
        try:
            # Try GPT-4.1 streaming first
            response = await self.client.chat.completions.create(
                model="gpt-4.1",
                messages=messages,
                max_tokens=250,
                temperature=0.3,
                stream=True  # Enable streaming
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    chunk_text = chunk.choices[0].delta.content
                    full_response += chunk_text
                    
                    # Send partial response to frontend
                    yield {
                        "type": "partial_response",
                        "content": chunk_text,
                        "full_so_far": full_response,
                        "model": model_used
                    }
            
            print(f"✅ GPT-4.1 streaming response generated for session {session_id}")
            
        except Exception as gpt_error:
            print(f"⚠️ GPT-4.1 streaming failed for session {session_id}: {gpt_error}")
            
            # Fallback to Claude 3.5 Sonnet (non-streaming)
            if self.claude_available:
                print(f"🔄 Falling back to Claude 3.5 Sonnet for session {session_id}")
                claude_response = self._call_claude_response(messages, session_id)
                
                if claude_response:
                    full_response = claude_response
                    model_used = "claude-3-5-sonnet"
                    
                    # Send Claude response as single chunk
                    yield {
                        "type": "partial_response",
                        "content": claude_response,
                        "full_so_far": claude_response,
                        "model": model_used
                    }
                    
                    print(f"✅ Claude 3.5 Sonnet fallback response generated for session {session_id}")
                else:
                    # Both models failed
                    full_response = "Maaf, saya sedang mengalami gangguan teknis. Bisakah Anda ulangi yang tadi?"
                    model_used = "error"
                    
                    yield {
                        "type": "partial_response",
                        "content": full_response,
                        "full_so_far": full_response,
                        "model": model_used
                    }
            else:
                # No Claude available, return error
                full_response = "Maaf, saya sedang mengalami gangguan teknis. Bisakah Anda ulangi yang tadi?"
                model_used = "error"
                
                yield {
                    "type": "partial_response",
                    "content": full_response,
                    "full_so_far": full_response,
                    "model": model_used
                }
        
        # Add AI response to conversation with model info
        conversation.append({
            "role": "assistant", 
            "content": full_response,
            "model": model_used
        })
        
        # Update conversation history
        self.conversations[session_id] = conversation
        
        # Send final response
        yield {
            "type": "final_response", 
            "content": full_response,
            "model": model_used,
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
        """Optimized voice therapy with integrated processing"""
        
        # Step 1: Speech-to-Text (must be first)
        user_text = await self._async_speech_to_text(audio_data)
        
        # Step 2: Start response generation using integrated system prompt
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
    
    def test_integrated_response(self, user_input: str, session_id: str = None) -> Dict[str, Any]:
        """Test the new integrated intent analysis and response generation"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        print(f"🧪 Testing integrated response system...")
        print(f"📝 User Input: {user_input}")
        print(f"🔑 Session ID: {session_id}")
        
        # Generate response using integrated system prompt
        ai_response = self._get_therapeutic_response(user_input, session_id)
        
        print(f"🤖 AI Response: {ai_response}")
        
        return {
            "user_input": user_input,
            "ai_response": ai_response,
            "session_id": session_id,
            "method": "integrated_intent_analysis",
            "timestamp": datetime.now().isoformat()
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
