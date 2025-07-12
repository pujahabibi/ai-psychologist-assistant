#!/usr/bin/env python3
"""
Audio Service Implementation - Speech processing with optimized multi-threading
"""

import io
import asyncio
import time
import threading
from typing import List, Tuple, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from ...core.interfaces.audio_service import IAudioService
from ...core.entities.audio_data import AudioData, ProcessedAudioData
from ...infrastructure.config.settings import settings


class AudioService(IAudioService):
    """Audio service implementation using OpenAI APIs with optimized multi-threading"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        
        # Thread pool for TTS operations
        self.tts_executor = ThreadPoolExecutor(
            max_workers=settings.audio_config.max_workers,
            thread_name_prefix="tts_worker"
        )
        
        # Thread pool for STT operations
        self.stt_executor = ThreadPoolExecutor(
            max_workers=2,  # Usually one STT at a time
            thread_name_prefix="stt_worker"
        )
        
        # Thread-safe performance statistics
        self._stats_lock = threading.Lock()
        self.performance_stats = {
            "total_tts_calls": 0,
            "total_stt_calls": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
            "parallel_calls_made": 0,
            "concurrent_chunks_processed": 0,
            "thread_pool_utilization": 0.0
        }
        
    async def speech_to_text(self, audio_data: AudioData) -> ProcessedAudioData:
        """Convert speech to text using Whisper with threading"""
        start_time = time.time()
        
        try:
            # Use thread pool for STT operation
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.stt_executor,
                self._sync_speech_to_text,
                audio_data
            )
            
            processing_time = time.time() - start_time
            
            # Thread-safe stats update
            with self._stats_lock:
                self.performance_stats["total_stt_calls"] += 1
                self.performance_stats["total_processing_time"] += processing_time
                self._update_average_processing_time()
            
            return ProcessedAudioData(
                audio_id=audio_data.audio_id,
                transcription=result,
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
    
    def _sync_speech_to_text(self, audio_data: AudioData) -> str:
        """Synchronous STT operation for thread pool"""
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
            
            return transcript.text.strip()
            
        except Exception as e:
            print(f"Error in sync STT: {e}")
            return ""
    
    async def text_to_speech(self, text: str) -> AudioData:
        """Convert text to speech using optimized multi-threading (following user preference)"""
        # Always use parallel processing per user preference
        return await self._text_to_speech_parallel_optimized(text)
    
    async def _text_to_speech_parallel_optimized(self, text: str, max_workers: Optional[int] = None) -> AudioData:
        """Convert text to speech using optimized multi-threading"""
        start_time = time.time()
        
        if max_workers is None:
            max_workers = settings.audio_config.max_workers
        
        try:
            # Split text into chunks for parallel processing
            chunks = self._split_text_into_sentences(text, settings.audio_config.max_chunk_size)
            
            if len(chunks) == 1:
                # Single chunk, process directly but still use thread pool
                loop = asyncio.get_event_loop()
                audio_bytes = await loop.run_in_executor(
                    self.tts_executor,
                    self._sync_text_to_speech_chunk,
                    chunks[0]
                )
                
                audio_data = AudioData(
                    audio_bytes=audio_bytes,
                    format=settings.audio_config.default_format,
                    duration=len(audio_bytes) / 32000  # Approximate duration
                )
                
                processing_time = time.time() - start_time
                
                # Thread-safe stats update
                with self._stats_lock:
                    self.performance_stats["total_tts_calls"] += 1
                    self.performance_stats["total_processing_time"] += processing_time
                    self._update_average_processing_time()
                
                return audio_data
            
            # Multiple chunks, process in parallel using thread pool
            loop = asyncio.get_event_loop()
            
            # Create tasks for all chunks using thread pool
            tasks = []
            for i, chunk in enumerate(chunks):
                task = loop.run_in_executor(
                    self.tts_executor,
                    self._sync_text_to_speech_chunk_with_id,
                    chunk,
                    i
                )
                tasks.append(task)
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and sort by chunk ID
            valid_results = [r for r in results if not isinstance(r, Exception)]
            valid_results.sort(key=lambda x: x[0])  # Sort by chunk ID
            
            if not valid_results:
                raise Exception("All parallel TTS calls failed")
            
            # Merge audio chunks
            audio_chunks = [result[1] for result in valid_results]
            merged_audio = await self._merge_audio_chunks_threaded(audio_chunks)
            
            processing_time = time.time() - start_time
            
            # Thread-safe stats update
            with self._stats_lock:
                self.performance_stats["total_tts_calls"] += len(chunks)
                self.performance_stats["parallel_calls_made"] += 1
                self.performance_stats["concurrent_chunks_processed"] += len(chunks)
                self.performance_stats["total_processing_time"] += processing_time
                self._update_average_processing_time()
                self.performance_stats["thread_pool_utilization"] = (
                    self.performance_stats["concurrent_chunks_processed"] / 
                    max(self.performance_stats["parallel_calls_made"], 1)
                )
            
            return AudioData(
                audio_bytes=merged_audio,
                format=settings.audio_config.default_format,
                duration=len(merged_audio) / 32000  # Approximate duration
            )
            
        except Exception as e:
            print(f"Error in optimized parallel TTS: {e}")
            return AudioData(
                audio_bytes=b"",
                format=settings.audio_config.default_format,
                duration=0.0
            )
    
    def _sync_text_to_speech_chunk(self, text_chunk: str) -> bytes:
        """Synchronous TTS operation for thread pool"""
        try:
            response = self.client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=text_chunk,
                response_format="mp3"  # Using mp3 per user preference
            )
            return response.content
        except Exception as e:
            print(f"Error in sync TTS chunk: {e}")
            return b""
    
    def _sync_text_to_speech_chunk_with_id(self, text_chunk: str, chunk_id: int) -> Tuple[int, bytes]:
        """Synchronous TTS operation with ID for thread pool"""
        try:
            response = self.client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=text_chunk,
                response_format="mp3"  # Using mp3 per user preference
            )
            return chunk_id, response.content
        except Exception as e:
            print(f"Error in sync TTS chunk {chunk_id}: {e}")
            return chunk_id, b""
    
    def _split_text_into_sentences(self, text: str, max_chunk_size: int = 200) -> List[str]:
        """Split text into sentences with size limits for optimal parallel processing"""
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
        
        # Ensure we have at least one chunk per worker for optimal parallelization
        max_optimal_chunks = settings.audio_config.max_workers * 2
        if len(chunks) > max_optimal_chunks:
            # Re-merge some chunks to avoid over-parallelization
            merged_chunks = []
            chunk_size = len(chunks) // max_optimal_chunks
            
            for i in range(0, len(chunks), chunk_size):
                merged_chunk = " ".join(chunks[i:i+chunk_size])
                merged_chunks.append(merged_chunk)
            
            chunks = merged_chunks
        
        return chunks
    
    async def _merge_audio_chunks_threaded(self, audio_chunks: List[bytes]) -> bytes:
        """Merge multiple audio chunks using thread pool"""
        if not audio_chunks:
            return b""
        
        if len(audio_chunks) == 1:
            return audio_chunks[0]
        
        # Use thread pool for merging if chunks are large
        total_size = sum(len(chunk) for chunk in audio_chunks)
        
        if total_size > 1024 * 1024:  # 1MB threshold
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.tts_executor,
                self._sync_merge_audio_chunks,
                audio_chunks
            )
        else:
            # Small chunks, merge directly
            return self._sync_merge_audio_chunks(audio_chunks)
    
    def _sync_merge_audio_chunks(self, audio_chunks: List[bytes]) -> bytes:
        """Synchronous audio chunk merging"""
        # Simple concatenation for MP3 files
        # This is a basic implementation - for production, you might want to use
        # proper audio libraries like pydub for better merging
        merged = b""
        for chunk in audio_chunks:
            merged += chunk
        return merged
    
    def _update_average_processing_time(self):
        """Update average processing time (called within lock)"""
        total_calls = self.performance_stats["total_tts_calls"] + self.performance_stats["total_stt_calls"]
        if total_calls > 0:
            self.performance_stats["average_processing_time"] = (
                self.performance_stats["total_processing_time"] / total_calls
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get thread-safe TTS performance statistics"""
        with self._stats_lock:
            return self.performance_stats.copy()
    
    def get_thread_pool_status(self) -> Dict[str, Any]:
        """Get thread pool status information"""
        return {
            "tts_pool_active_threads": getattr(self.tts_executor, '_threads', 0),
            "stt_pool_active_threads": getattr(self.stt_executor, '_threads', 0),
            "max_tts_workers": settings.audio_config.max_workers,
            "max_stt_workers": 2,
            "parallel_processing_enabled": settings.audio_config.use_parallel_tts
        }
    
    def is_available(self) -> bool:
        """Check if service is available"""
        return bool(self.api_key)
    
    def __del__(self):
        """Cleanup thread pools on destruction"""
        try:
            self.tts_executor.shutdown(wait=False)
            self.stt_executor.shutdown(wait=False)
        except Exception:
            pass  # Ignore cleanup errors 