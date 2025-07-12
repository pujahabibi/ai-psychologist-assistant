#!/usr/bin/env python3
"""
Audio Service Implementation - Ultra-fast simplified TTS processing
"""

import io
import os
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
    """Simplified audio service implementation with ultra-fast TTS processing"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        
        # Simple single ThreadPoolExecutor for maximum speed
        self.max_workers = min(24, (os.cpu_count() or 1) * 3)  # Simplified worker count
        self.tts_executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="FastTTS"
        )
        
        # Simplified performance tracking
        self.performance_stats = {
            "total_tts_calls": 0,
            "total_stt_calls": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
            "parallel_calls_made": 0,
            "successful_chunks": 0,
            "failed_chunks": 0,
            "fastest_chunk_time": float('inf'),
            "slowest_chunk_time": 0.0
        }
        
        # Thread-safe lock for stats
        self._stats_lock = threading.Lock()
        
        print(f"⚡ SIMPLIFIED ULTRA-FAST TTS initialized with {self.max_workers} workers")
        
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
            
            with self._stats_lock:
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
        """Convert text to speech using parallel processing (user preference)"""
        return await self.text_to_speech_parallel(text)
    
    async def text_to_speech_parallel(self, text: str, max_workers: int = None) -> AudioData:
        """
        Ultra-fast simplified text-to-speech processing
        
        Simple approach: Split text -> Process all chunks in parallel -> Merge
        No complex batching, no multiple strategies, just pure speed
        """
        if not text or not text.strip():
            return AudioData(
                audio_bytes=b"",
                format=settings.audio_config.default_format,
                duration=0.0
            )
        
        start_time = time.time()
        
        try:
            # Split text into chunks
            sentences = self._split_text_into_sentences(text, settings.audio_config.max_chunk_size)
            
            if not sentences:
                return AudioData(
                    audio_bytes=b"",
                    format=settings.audio_config.default_format,
                    duration=0.0
                )
            
            # Use all available workers for maximum speed
            workers_to_use = min(len(sentences), max_workers or self.max_workers)
            
            print(f"⚡ FAST TTS: Processing {len(sentences)} chunks with {workers_to_use} workers...")
            
            # Submit all tasks to ThreadPoolExecutor at once
            loop = asyncio.get_event_loop()
            futures = []
            
            for i, sentence in enumerate(sentences):
                future = self.tts_executor.submit(self._process_chunk, i, sentence)
                futures.append(future)
            
            # Wait for all results - no complex batching
            results = []
            for future in as_completed(futures):
                try:
                    result = await loop.run_in_executor(None, future.result, 10)  # 10 second timeout per chunk
                    results.append(result)
                except Exception as e:
                    print(f"❌ Chunk failed: {e}")
                    with self._stats_lock:
                        self.performance_stats["failed_chunks"] += 1
            
            # Sort results by chunk_id
            results.sort(key=lambda x: x[0])
            
            # Extract audio data
            audio_chunks = [result[1] for result in results if result[1]]
            
            if not audio_chunks:
                print("⚠️ No audio chunks generated")
                return AudioData(
                    audio_bytes=b"",
                    format=settings.audio_config.default_format,
                    duration=0.0
                )
            
            # Simple merge - no complex threading
            merged_audio = self._merge_audio_chunks(audio_chunks)
            
            processing_time = time.time() - start_time
            
            # Update stats
            with self._stats_lock:
                self.performance_stats["total_tts_calls"] += 1
                self.performance_stats["parallel_calls_made"] += 1
                self.performance_stats["successful_chunks"] += len(audio_chunks)
                self.performance_stats["total_processing_time"] += processing_time
                
                # Calculate average per chunk
                avg_per_chunk = processing_time / len(sentences)
                self.performance_stats["fastest_chunk_time"] = min(
                    self.performance_stats["fastest_chunk_time"], avg_per_chunk
                )
                self.performance_stats["slowest_chunk_time"] = max(
                    self.performance_stats["slowest_chunk_time"], avg_per_chunk
                )
            
            print(f"✅ TTS completed in {processing_time:.2f}s ({avg_per_chunk:.2f}s/chunk)")
            
            return AudioData(
                audio_bytes=merged_audio,
                format=settings.audio_config.default_format,
                duration=len(merged_audio) / (16000 * 2)  # Estimated duration
            )
            
        except Exception as e:
            print(f"❌ TTS Error: {e}")
            return AudioData(
                audio_bytes=b"",
                format=settings.audio_config.default_format,
                duration=0.0
            )
    
    def _process_chunk(self, chunk_id: int, text: str) -> Tuple[int, bytes]:
        """Process a single TTS chunk - simplified and fast"""
        start_time = time.time()
        
        try:
            # Create dedicated client for this thread
            client = OpenAI(api_key=self.api_key)
            
            # Direct TTS call - no complex retry logic
            response = client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=text,
                response_format="mp3"
            )
            
            processing_time = time.time() - start_time
            print(f"⚡ Chunk {chunk_id} completed in {processing_time:.2f}s")
            
            return (chunk_id, response.content)
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ Chunk {chunk_id} failed in {processing_time:.2f}s: {e}")
            return (chunk_id, b"")
    
    def _merge_audio_chunks(self, audio_chunks: List[bytes]) -> bytes:
        """Simple audio chunk merging - no complex threading"""
        if not audio_chunks:
            return b""
        
        # Direct concatenation for MP3 files
        merged = b""
        for chunk in audio_chunks:
            if chunk:
                merged += chunk
        
        return merged
    
    def _split_text_into_sentences(self, text: str, max_chunk_size: int = 200) -> List[str]:
        """Split text into manageable chunks - optimized for under 1s per chunk"""
        if not text or not text.strip():
            return []
        
        # Clean text
        text = text.strip()
        
        # For speed optimization, use smaller chunks (50-80 chars) for better parallelization
        target_chunk_size = min(80, max_chunk_size)
        
        # Simple sentence splitting
        sentences = []
        current_chunk = ""
        
        # Split by periods, exclamations, questions, and commas for more aggressive chunking
        potential_sentences = text.replace('!', '.').replace('?', '.').replace(',', '.').split('.')
        
        for sentence in potential_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # More aggressive chunking for better parallelization
            if len(current_chunk) + len(sentence) > target_chunk_size and current_chunk:
                sentences.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence
        
        # Add the last chunk
        if current_chunk:
            sentences.append(current_chunk.strip())
        
        # If we still have large chunks, split them further
        final_sentences = []
        for sentence in sentences:
            if len(sentence) > target_chunk_size:
                # Split long sentences by words
                words = sentence.split()
                current_word_chunk = ""
                for word in words:
                    if len(current_word_chunk) + len(word) + 1 > target_chunk_size and current_word_chunk:
                        final_sentences.append(current_word_chunk.strip())
                        current_word_chunk = word
                    else:
                        if current_word_chunk:
                            current_word_chunk += " " + word
                        else:
                            current_word_chunk = word
                if current_word_chunk:
                    final_sentences.append(current_word_chunk.strip())
            else:
                final_sentences.append(sentence)
        
        return final_sentences
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        with self._stats_lock:
            stats = self.performance_stats.copy()
            
            # Calculate additional metrics
            total_calls = stats["total_tts_calls"] + stats["total_stt_calls"]
            if total_calls > 0:
                stats["average_processing_time"] = stats["total_processing_time"] / total_calls
            
            if stats["successful_chunks"] > 0:
                stats["success_rate"] = (stats["successful_chunks"] / 
                                      (stats["successful_chunks"] + stats["failed_chunks"]) * 100)
            else:
                stats["success_rate"] = 0.0
            
            stats["workers_available"] = self.max_workers
            
            return stats
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.tts_executor.shutdown(wait=True)
            print("🧹 Audio service cleanup completed")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
    
    def is_available(self) -> bool:
        """Check if the service is available"""
        try:
            return self.client is not None and self.api_key is not None
        except Exception:
            return False 