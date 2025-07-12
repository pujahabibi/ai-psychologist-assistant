#!/usr/bin/env python3
"""
Audio Service Implementation - Speech processing with parallel TTS
"""

import io
import asyncio
import time
from typing import List, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from ...core.interfaces.audio_service import IAudioService
from ...core.entities.audio_data import AudioData, ProcessedAudioData
from ...infrastructure.config.settings import settings


class AudioService(IAudioService):
    """Audio service implementation using OpenAI APIs"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.performance_stats = {
            "total_tts_calls": 0,
            "total_stt_calls": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
            "parallel_calls_made": 0
        }
        
    async def speech_to_text(self, audio_data: AudioData) -> ProcessedAudioData:
        """Convert speech to text using Whisper"""
        start_time = time.time()
        
        try:
            # Create a temporary file-like object
            audio_file = io.BytesIO(audio_data.audio_bytes)
            audio_file.name = f"temp_audio.{audio_data.format}"
            
            # Transcribe using Whisper
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="id",  # Indonesian language code
            )
            
            processing_time = time.time() - start_time
            
            self.performance_stats["total_stt_calls"] += 1
            self.performance_stats["total_processing_time"] += processing_time
            self.performance_stats["average_processing_time"] = (
                self.performance_stats["total_processing_time"] / 
                (self.performance_stats["total_tts_calls"] + self.performance_stats["total_stt_calls"])
            )
            
            return ProcessedAudioData(
                audio_id=audio_data.audio_id,
                transcription=transcript.text.strip(),
                confidence=0.9,  # Whisper generally has high confidence
                processing_time=processing_time,
                language="id"
            )
            
        except Exception as e:
            print(f"Error in speech-to-text: {e}")
            return ProcessedAudioData(
                audio_id=audio_data.audio_id,
                transcription="",
                confidence=0.0,
                processing_time=time.time() - start_time,
                language="id"
            )
    
    async def text_to_speech(self, text: str) -> AudioData:
        """Convert text to speech using parallel processing (following user preference)"""
        # Always use parallel processing per user preference
        return await self._text_to_speech_parallel(text)
    
    async def _text_to_speech_parallel(self, text: str, max_workers: int = None) -> AudioData:
        """Convert text to speech using parallel processing"""
        start_time = time.time()
        
        if max_workers is None:
            max_workers = settings.audio_config.max_workers
        
        try:
            # Split text into chunks for parallel processing
            chunks = self._split_text_into_sentences(text, settings.audio_config.max_chunk_size)
            
            if len(chunks) == 1:
                # Single chunk, process directly
                audio_bytes = await self._async_text_to_speech_chunk(chunks[0], 0)
                audio_data = AudioData(
                    audio_bytes=audio_bytes[1],
                    format=settings.audio_config.default_format,
                    duration=len(audio_bytes[1]) / 32000  # Approximate duration
                )
                
                processing_time = time.time() - start_time
                self.performance_stats["total_tts_calls"] += 1
                self.performance_stats["total_processing_time"] += processing_time
                self.performance_stats["average_processing_time"] = (
                    self.performance_stats["total_processing_time"] / 
                    (self.performance_stats["total_tts_calls"] + self.performance_stats["total_stt_calls"])
                )
                
                return audio_data
            
            # Multiple chunks, process in parallel
            semaphore = asyncio.Semaphore(max_workers)
            
            async def process_with_semaphore(chunk_id: int, chunk_text: str):
                async with semaphore:
                    return await self._async_text_to_speech_chunk(chunk_text, chunk_id)
            
            # Create tasks for all chunks
            tasks = [
                process_with_semaphore(i, chunk)
                for i, chunk in enumerate(chunks)
            ]
            
            # Execute tasks in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and sort by chunk ID
            valid_results = [r for r in results if not isinstance(r, Exception)]
            valid_results.sort(key=lambda x: x[0])  # Sort by chunk ID
            
            if not valid_results:
                raise Exception("All parallel TTS calls failed")
            
            # Merge audio chunks
            audio_chunks = [result[1] for result in valid_results]
            merged_audio = self._merge_audio_chunks(audio_chunks)
            
            processing_time = time.time() - start_time
            self.performance_stats["total_tts_calls"] += len(chunks)
            self.performance_stats["parallel_calls_made"] += 1
            self.performance_stats["total_processing_time"] += processing_time
            self.performance_stats["average_processing_time"] = (
                self.performance_stats["total_processing_time"] / 
                (self.performance_stats["total_tts_calls"] + self.performance_stats["total_stt_calls"])
            )
            
            return AudioData(
                audio_bytes=merged_audio,
                format=settings.audio_config.default_format,
                duration=len(merged_audio) / 32000  # Approximate duration
            )
            
        except Exception as e:
            print(f"Error in parallel TTS: {e}")
            processing_time = time.time() - start_time
            return AudioData(
                audio_bytes=b"",
                format=settings.audio_config.default_format,
                duration=0.0
            )
    
    def _split_text_into_sentences(self, text: str, max_chunk_size: int = 200) -> List[str]:
        """Split text into sentences with size limits"""
        if len(text) <= max_chunk_size:
            return [text]
        
        # Split by sentences first
        sentences = text.replace('.', '.\n').replace('!', '!\n').replace('?', '?\n').split('\n')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    async def _async_text_to_speech_chunk(self, text_chunk: str, chunk_id: int) -> Tuple[int, bytes]:
        """Convert single text chunk to speech asynchronously"""
        def _sync_tts():
            response = self.client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=text_chunk,
                response_format="mp3"  # Using mp3 per user preference
            )
            return response.content
        
        loop = asyncio.get_event_loop()
        audio_bytes = await loop.run_in_executor(None, _sync_tts)
        return chunk_id, audio_bytes
    
    def _merge_audio_chunks(self, audio_chunks: List[bytes]) -> bytes:
        """Merge multiple audio chunks into single audio file"""
        if not audio_chunks:
            return b""
        
        if len(audio_chunks) == 1:
            return audio_chunks[0]
        
        # Simple concatenation for MP3 files
        # This is a basic implementation - for production, you might want to use
        # proper audio libraries like pydub for better merging
        merged = b""
        for chunk in audio_chunks:
            merged += chunk
        
        return merged
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get TTS performance statistics"""
        return self.performance_stats.copy()
    
    def is_available(self) -> bool:
        """Check if service is available"""
        return bool(self.api_key) 