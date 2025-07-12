#!/usr/bin/env python3
"""
Audio Service Implementation - Ultra-fast simplified TTS processing
"""

import io
import os
import asyncio
import time
import threading
import tempfile
import math
from typing import List, Tuple, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from ...core.interfaces.audio_service import IAudioService
from ...core.entities.audio_data import AudioData, ProcessedAudioData
from ...infrastructure.config.settings import settings

try:
    import pydub
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("⚠️ pydub not available - audio preprocessing disabled")


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
            "slowest_chunk_time": 0.0,
            "stt_chunks_processed": 0,
            "stt_parallel_calls": 0,
            "stt_preprocessing_time": 0.0
        }
        
        # Thread-safe lock for stats
        self._stats_lock = threading.Lock()
        
        print(f"⚡ SIMPLIFIED ULTRA-FAST TTS initialized with {self.max_workers} workers")
        
    async def speech_to_text(self, audio_data: AudioData) -> ProcessedAudioData:
        """Convert speech to text using optimized parallel Whisper processing"""
        start_time = time.time()
        
        try:
            # Quick check for empty audio
            if not audio_data.audio_bytes or len(audio_data.audio_bytes) < 1000:
                return ProcessedAudioData(
                    audio_id=audio_data.audio_id,
                    transcription="",
                    confidence=0.0,
                    processing_time=time.time() - start_time,
                    language="id"
                )
            
            # Detect audio duration and apply optimization strategy
            audio_duration = await self._get_audio_duration(audio_data.audio_bytes, audio_data.format)
            
            # Strategy selection based on audio duration
            if audio_duration <= 30:  # Short audio: direct processing
                return await self._process_audio_direct(audio_data, start_time)
            elif audio_duration <= 120:  # Medium audio: small chunks
                return await self._process_audio_chunked(audio_data, start_time, chunk_seconds=20)
            else:  # Long audio: aggressive chunking
                return await self._process_audio_chunked(audio_data, start_time, chunk_seconds=15)
            
        except Exception as e:
            print(f"❌ Error in speech-to-text: {e}")
            return ProcessedAudioData(
                audio_id=audio_data.audio_id,
                transcription="",
                confidence=0.0,
                processing_time=time.time() - start_time,
                language="id"
            )
    
    async def _get_audio_duration(self, audio_bytes: bytes, format: str) -> float:
        """Get audio duration using pydub for optimization decisions"""
        try:
            if not PYDUB_AVAILABLE:
                # Fallback: estimate based on file size (rough approximation)
                # Assume 16kHz mono 16-bit: ~32KB per second
                return len(audio_bytes) / 32000
            
            # Use pydub to get accurate duration
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format=format)
            return len(audio_segment) / 1000.0  # Convert ms to seconds
        except Exception as e:
            print(f"⚠️ Could not determine audio duration: {e}")
            # Conservative fallback
            return len(audio_bytes) / 32000
    
    async def _process_audio_direct(self, audio_data: AudioData, start_time: float) -> ProcessedAudioData:
        """Process short audio files directly without chunking"""
        try:
            # Preprocess audio for optimization
            preprocessed_audio = await self._preprocess_audio(audio_data.audio_bytes, audio_data.format)
            
            # Create file-like object with preprocessed audio
            audio_file = io.BytesIO(preprocessed_audio)
            audio_file.name = f"temp_audio.{audio_data.format}"
            
            # Direct transcription
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
                confidence=0.9,
                processing_time=processing_time,
                language="id"
            )
            
        except Exception as e:
            print(f"❌ Error in direct audio processing: {e}")
            raise
    
    async def _process_audio_chunked(self, audio_data: AudioData, start_time: float, chunk_seconds: int = 20) -> ProcessedAudioData:
        """Process longer audio files using parallel chunking for speed"""
        try:
            if not PYDUB_AVAILABLE:
                # Fallback to direct processing if pydub not available
                return await self._process_audio_direct(audio_data, start_time)
            
            preprocessing_start = time.time()
            
            # Load and preprocess audio
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data.audio_bytes), format=audio_data.format)
            
            # Audio preprocessing optimizations
            audio_segment = await self._optimize_audio_segment(audio_segment)
            
            # Split into chunks
            chunk_length_ms = chunk_seconds * 1000
            chunks = []
            
            for i in range(0, len(audio_segment), chunk_length_ms):
                chunk = audio_segment[i:i + chunk_length_ms]
                if len(chunk) > 1000:  # Skip very short chunks
                    chunks.append((i // chunk_length_ms, chunk))
            
            preprocessing_time = time.time() - preprocessing_start
            
            if not chunks:
                return ProcessedAudioData(
                    audio_id=audio_data.audio_id,
                    transcription="",
                    confidence=0.0,
                    processing_time=time.time() - start_time,
                    language="id"
                )
            
            print(f"🎙️ PARALLEL STT: Processing {len(chunks)} chunks ({chunk_seconds}s each)")
            
            # Process chunks in parallel
            loop = asyncio.get_event_loop()
            futures = []
            
            for chunk_id, chunk in chunks:
                future = self.tts_executor.submit(self._process_audio_chunk, chunk_id, chunk, audio_data.format)
                futures.append(future)
            
            # Collect results
            results = []
            for future in as_completed(futures):
                try:
                    result = await loop.run_in_executor(None, future.result, 30)  # 30 second timeout
                    results.append(result)
                except Exception as e:
                    print(f"❌ STT Chunk failed: {e}")
                    with self._stats_lock:
                        self.performance_stats["failed_chunks"] += 1
            
            # Sort and combine results
            results.sort(key=lambda x: x[0])
            transcriptions = [result[1] for result in results if result[1]]
            
            combined_transcription = " ".join(transcriptions).strip()
            processing_time = time.time() - start_time
            
            # Update performance stats
            with self._stats_lock:
                self.performance_stats["total_stt_calls"] += 1
                self.performance_stats["stt_parallel_calls"] += 1
                self.performance_stats["stt_chunks_processed"] += len(chunks)
                self.performance_stats["stt_preprocessing_time"] += preprocessing_time
                self.performance_stats["total_processing_time"] += processing_time
                self.performance_stats["average_processing_time"] = (
                    self.performance_stats["total_processing_time"] / 
                    (self.performance_stats["total_tts_calls"] + self.performance_stats["total_stt_calls"])
                )
            
            print(f"✅ STT completed in {processing_time:.2f}s ({processing_time/len(chunks):.2f}s/chunk)")
            
            return ProcessedAudioData(
                audio_id=audio_data.audio_id,
                transcription=combined_transcription,
                confidence=0.9,
                processing_time=processing_time,
                language="id"
            )
            
        except Exception as e:
            print(f"❌ Error in chunked audio processing: {e}")
            raise
    
    def _process_audio_chunk(self, chunk_id: int, audio_chunk: AudioSegment, format: str) -> Tuple[int, str]:
        """Process a single audio chunk for transcription"""
        start_time = time.time()
        
        try:
            # Export chunk to bytes
            chunk_buffer = io.BytesIO()
            audio_chunk.export(chunk_buffer, format=format)
            chunk_buffer.seek(0)
            chunk_buffer.name = f"chunk_{chunk_id}.{format}"
            
            # Create dedicated client for this thread
            client = OpenAI(api_key=self.api_key)
            
            # Transcribe chunk
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=chunk_buffer,
                language="id",
            )
            
            processing_time = time.time() - start_time
            print(f"🎙️ STT Chunk {chunk_id} completed in {processing_time:.2f}s")
            
            return (chunk_id, transcript.text.strip())
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ STT Chunk {chunk_id} failed in {processing_time:.2f}s: {e}")
            return (chunk_id, "")
    
    async def _preprocess_audio(self, audio_bytes: bytes, format: str) -> bytes:
        """Preprocess audio for optimal transcription performance"""
        try:
            if not PYDUB_AVAILABLE:
                return audio_bytes
            
            # Load audio
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format=format)
            
            # Apply optimizations
            audio_segment = await self._optimize_audio_segment(audio_segment)
            
            # Export back to bytes
            output_buffer = io.BytesIO()
            audio_segment.export(output_buffer, format=format)
            return output_buffer.getvalue()
            
        except Exception as e:
            print(f"⚠️ Audio preprocessing failed: {e}")
            return audio_bytes
    
    async def _optimize_audio_segment(self, audio_segment: AudioSegment) -> AudioSegment:
        """Apply audio optimizations for faster transcription"""
        try:
            # Optimization 1: Normalize volume
            audio_segment = audio_segment.normalize()
            
            # Optimization 2: Ensure optimal sample rate (16kHz for Whisper)
            if audio_segment.frame_rate != 16000:
                audio_segment = audio_segment.set_frame_rate(16000)
            
            # Optimization 3: Convert to mono if stereo
            if audio_segment.channels > 1:
                audio_segment = audio_segment.set_channels(1)
            
            # Optimization 4: Remove silence from beginning and end
            audio_segment = audio_segment.strip_silence(silence_thresh=-40)
            
            # Optimization 5: Slight speed increase (1.05x) for faster processing
            # This reduces processing time while maintaining transcription quality
            audio_segment = audio_segment.speedup(playback_speed=1.05)
            
            return audio_segment
            
        except Exception as e:
            print(f"⚠️ Audio optimization failed: {e}")
            return audio_segment
    
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
            
            # Handle infinity values for JSON serialization
            if stats["fastest_chunk_time"] == float('inf'):
                stats["fastest_chunk_time"] = 0.0
            
            # Calculate additional metrics
            total_calls = stats["total_tts_calls"] + stats["total_stt_calls"]
            if total_calls > 0:
                stats["average_processing_time"] = stats["total_processing_time"] / total_calls
            
            if stats["successful_chunks"] > 0:
                stats["success_rate"] = (stats["successful_chunks"] / 
                                      (stats["successful_chunks"] + stats["failed_chunks"]) * 100)
            else:
                stats["success_rate"] = 0.0
            
            # STT-specific metrics
            if stats["stt_parallel_calls"] > 0:
                stats["stt_avg_chunks_per_call"] = stats["stt_chunks_processed"] / stats["stt_parallel_calls"]
                stats["stt_avg_preprocessing_time"] = stats["stt_preprocessing_time"] / stats["stt_parallel_calls"]
            else:
                stats["stt_avg_chunks_per_call"] = 0.0
                stats["stt_avg_preprocessing_time"] = 0.0
            
            stats["workers_available"] = self.max_workers
            stats["optimization_features"] = {
                "parallel_tts": "✅ Enabled",
                "parallel_stt": "✅ Enabled", 
                "audio_preprocessing": "✅ Enabled" if PYDUB_AVAILABLE else "❌ Disabled",
                "chunking_strategy": "Duration-based adaptive chunking"
            }
            
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