#!/usr/bin/env python3
"""
Audio Service Interfaces - Contracts for audio processing services
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from ..entities.audio_data import AudioData, ProcessedAudioData


class IAudioService(ABC):
    """Interface for audio processing services"""
    
    @abstractmethod
    async def speech_to_text(self, audio_data: AudioData) -> ProcessedAudioData:
        """Convert speech to text"""
        pass
    
    @abstractmethod
    async def text_to_speech(self, text: str) -> AudioData:
        """Convert text to speech"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if service is available"""
        pass


class ISpeechToTextService(ABC):
    """Interface for speech-to-text service"""
    
    @abstractmethod
    async def transcribe(self, audio_data: AudioData) -> ProcessedAudioData:
        """Transcribe audio to text"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> list:
        """Get supported audio formats"""
        pass


class ITextToSpeechService(ABC):
    """Interface for text-to-speech service"""
    
    @abstractmethod
    async def synthesize(self, text: str, voice: str = "alloy") -> AudioData:
        """Synthesize text to speech"""
        pass
    
    @abstractmethod
    async def synthesize_parallel(self, text: str, max_workers: int = 8) -> AudioData:
        """Synthesize text to speech using parallel processing"""
        pass
    
    @abstractmethod
    def get_available_voices(self) -> list:
        """Get available voices"""
        pass
    
    @abstractmethod
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get TTS performance statistics"""
        pass


class IAudioProcessor(ABC):
    """Interface for audio processing utilities"""
    
    @abstractmethod
    def validate_audio(self, audio_data: AudioData) -> bool:
        """Validate audio data"""
        pass
    
    @abstractmethod
    def merge_audio_chunks(self, audio_chunks: list) -> AudioData:
        """Merge multiple audio chunks"""
        pass
    
    @abstractmethod
    def split_text_for_tts(self, text: str, max_chunk_size: int = 200) -> list:
        """Split text into chunks for TTS processing"""
        pass 