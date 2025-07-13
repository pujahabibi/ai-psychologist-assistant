#!/usr/bin/env python3
"""
AudioData Entity - Domain model for audio processing
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Any
from uuid import uuid4


@dataclass
class AudioData:
    """
    Domain entity representing audio data and processing metadata
    """
    audio_id: str = field(default_factory=lambda: str(uuid4()))
    audio_bytes: bytes = field(default_factory=bytes)
    format: str = "wav"  # Following user preference for wav format
    duration: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    file_size: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and set additional properties after initialization"""
        if self.audio_bytes:
            self.file_size = len(self.audio_bytes)
            self.metadata["original_size"] = self.file_size
    
    def is_valid(self) -> bool:
        """Check if audio data is valid"""
        return (
            len(self.audio_bytes) > 0 and
            self.format in ["wav", "mp3", "m4a", "ogg"] and
            self.file_size is not None and
            self.file_size > 100  # Minimum file size check
        )
    
    def get_duration_seconds(self) -> float:
        """Get duration in seconds"""
        return self.duration or 0.0
    
    def get_file_size_mb(self) -> float:
        """Get file size in MB"""
        return (self.file_size or 0) / (1024 * 1024)
    
    def update_metadata(self, key: str, value: Any):
        """Update metadata"""
        self.metadata[key] = value
    
    def get_processing_metrics(self) -> Dict[str, Any]:
        """Get processing metrics"""
        return {
            "audio_id": self.audio_id,
            "format": self.format,
            "duration": self.duration,
            "file_size_mb": self.get_file_size_mb(),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "created_at": self.created_at.isoformat(),
            "is_valid": self.is_valid()
        }


@dataclass
class ProcessedAudioData:
    """
    Domain entity representing processed audio data (e.g., transcription results)
    """
    audio_id: str
    transcription: str
    confidence: float = 0.0
    processing_time: float = 0.0
    language: str = "id"  # Indonesian by default
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if transcription has high confidence"""
        return self.confidence >= threshold
    
    def get_word_count(self) -> int:
        """Get word count of transcription"""
        return len(self.transcription.split()) if self.transcription else 0
    
    def get_processing_metrics(self) -> Dict[str, Any]:
        """Get processing metrics"""
        return {
            "audio_id": self.audio_id,
            "transcription_length": len(self.transcription),
            "word_count": self.get_word_count(),
            "confidence": self.confidence,
            "processing_time": self.processing_time,
            "language": self.language,
            "is_high_confidence": self.is_high_confidence(),
            "created_at": self.created_at.isoformat()
        } 