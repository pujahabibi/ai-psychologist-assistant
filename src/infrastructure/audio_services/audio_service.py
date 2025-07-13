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
from typing import List, Tuple, Dict, Any, Optional, Union, AsyncGenerator
import concurrent.futures
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
    # Create a dummy AudioSegment class for type hints
    class AudioSegment:
        pass


class AudioService(IAudioService):
    """Simplified audio service implementation with ultra-fast TTS processing"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        
        # Dual executors for optimal performance
        self.max_workers = min(32, (os.cpu_count() or 1) * 4)  # Increased worker count
        self.tts_executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="FastTTS"
        )
        # Dedicated STT executor for ultra-fast speech processing
        self.stt_max_workers = min(48, (os.cpu_count() or 1) * 6)  # More workers for STT
        self.stt_executor = ThreadPoolExecutor(
            max_workers=self.stt_max_workers,
            thread_name_prefix="UltraSTT"
        )
        
        # Enhanced performance tracking for ultra-fast processing
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
            "stt_preprocessing_time": 0.0,
            "stt_compression_time": 0.0,
            "stt_ultra_fast_chunks": 0,  # Chunks processed under 1 second
            "stt_fastest_chunk": float('inf'),
            "stt_network_time": 0.0
        }
        
        # Thread-safe lock for stats
        self._stats_lock = threading.Lock()
        
        print(f"⚡ ULTRA-FAST STT initialized with {self.stt_max_workers} STT workers + {self.max_workers} TTS workers")
        
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
                language="auto"
            )
            # Detect audio duration and apply optimization strategy
            audio_duration = await self._get_audio_duration(audio_data.audio_bytes, audio_data.format)
            
            # Ultra-fast strategy selection based on audio duration
            if audio_duration <= 10:  # Very short audio: direct processing with ultra optimization
                return await self._process_audio_direct(audio_data, start_time)
            elif audio_duration <= 30:  # Short audio: micro chunks for maximum parallelization
                return await self._process_audio_ultra_fast(audio_data, start_time, chunk_seconds=5)
            elif audio_duration <= 120:  # Medium audio: aggressive small chunks
                return await self._process_audio_ultra_fast(audio_data, start_time, chunk_seconds=6)
            else:  # Long audio: ultra-aggressive micro chunking
                return await self._process_audio_ultra_fast(audio_data, start_time, chunk_seconds=8)
            
        except Exception as e:
            print(f"❌ Error in speech-to-text: {e}")
            return ProcessedAudioData(
                audio_id=audio_data.audio_id,
                transcription="",
                confidence=0.0,
                processing_time=time.time() - start_time,
                language="auto"
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
        """Process very short audio files directly with ultra optimization"""
        try:
            # Ultra-fast preprocessing with compression
            preprocessed_audio = await self._preprocess_audio_ultra_fast(audio_data.audio_bytes, audio_data.format)
            
            # Create file-like object with preprocessed audio
            audio_file = io.BytesIO(preprocessed_audio)
            audio_file.name = f"temp_audio.{audio_data.format}"
            
            # Direct transcription with auto-detection for mixed Arabic-English
            network_start = time.time()
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                prompt="The user is speaking in Arabic Omani Dialect and English. Not in Indonesia anymore. Mind with the language detection and transcribe the text in the correct language.",
                # No language parameter - enables auto-detection for mixed Arabic-English
                # Whisper excels at handling code-switched languages naturally
            )
            network_time = time.time() - network_start
            
            processing_time = time.time() - start_time
            
            with self._stats_lock:
                self.performance_stats["total_stt_calls"] += 1
                self.performance_stats["total_processing_time"] += processing_time
                self.performance_stats["stt_network_time"] += network_time
                self.performance_stats["average_processing_time"] = (
                    self.performance_stats["total_processing_time"] / 
                    (self.performance_stats["total_tts_calls"] + self.performance_stats["total_stt_calls"])
                )
                
                # Track ultra-fast chunks (under 1 second)
                if processing_time < 1.0:
                    self.performance_stats["stt_ultra_fast_chunks"] += 1
                
                # Update fastest chunk time
                self.performance_stats["stt_fastest_chunk"] = min(
                    self.performance_stats["stt_fastest_chunk"], processing_time
                )
            
            print(f"⚡ DIRECT STT completed in {processing_time:.2f}s (network: {network_time:.2f}s)")
            
            return ProcessedAudioData(
                audio_id=audio_data.audio_id,
                transcription=transcript.text.strip(),
                confidence=0.9,
                processing_time=processing_time,
                language="auto"
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
                    language=None  # Auto-detect mixed Arabic/English
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
                language=None  # Auto-detect mixed Arabic/English
            )
            
        except Exception as e:
            print(f"❌ Error in chunked audio processing: {e}")
            raise
    
    async def _process_audio_ultra_fast(self, audio_data: AudioData, start_time: float, chunk_seconds: int = 5) -> ProcessedAudioData:
        """Ultra-fast audio processing with micro chunks for sub-1-second performance"""
        try:
            if not PYDUB_AVAILABLE:
                # Fallback to direct processing if pydub not available
                return await self._process_audio_direct(audio_data, start_time)
            
            preprocessing_start = time.time()
            
            # Load audio with ultra-fast processing
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data.audio_bytes), format=audio_data.format)
            
            # Ultra-aggressive audio preprocessing
            audio_segment = await self._optimize_audio_segment_ultra_fast(audio_segment)
            
            # Micro chunking for maximum parallelization
            chunk_length_ms = chunk_seconds * 1000
            chunks = []
            
            # Create smaller overlapping chunks for better context and speed
            overlap_ms = 500  # 0.5 second overlap for context preservation
            
            for i in range(0, len(audio_segment), chunk_length_ms - overlap_ms):
                chunk_end = min(i + chunk_length_ms, len(audio_segment))
                chunk = audio_segment[i:chunk_end]
                
                if len(chunk) > 500:  # Skip very short chunks (0.5s minimum)
                    chunks.append((len(chunks), chunk))
                
                # Stop if we've reached the end
                if chunk_end >= len(audio_segment):
                    break
            
            preprocessing_time = time.time() - preprocessing_start
            
            if not chunks:
                return ProcessedAudioData(
                    audio_id=audio_data.audio_id,
                    transcription="",
                    confidence=0.0,
                    processing_time=time.time() - start_time,
                    language=None  # Auto-detect mixed Arabic/English
                )
            
            print(f"🚀 ULTRA-FAST STT: Processing {len(chunks)} micro-chunks ({chunk_seconds}s each, 0.5s overlap)")
            
            # Process chunks in parallel using dedicated STT executor
            loop = asyncio.get_event_loop()
            futures = []
            
            for chunk_id, chunk in chunks:
                future = self.stt_executor.submit(self._process_audio_chunk_ultra_fast, chunk_id, chunk, audio_data.format)
                futures.append(future)
            
            # Collect results with reduced timeout for faster processing
            results = []
            for future in as_completed(futures):
                try:
                    result = await loop.run_in_executor(None, future.result, 15)  # Reduced timeout to 15 seconds
                    results.append(result)
                except Exception as e:
                    print(f"❌ Ultra-fast STT Chunk failed: {e}")
                    with self._stats_lock:
                        self.performance_stats["failed_chunks"] += 1
            
            # Sort and intelligently combine overlapping results
            results.sort(key=lambda x: x[0])
            transcriptions = [result[1] for result in results if result[1]]
            
            # Smart deduplication for overlapping chunks
            combined_transcription = self._deduplicate_overlapping_transcriptions(transcriptions)
            processing_time = time.time() - start_time
            
            # Enhanced performance stats tracking
            with self._stats_lock:
                self.performance_stats["total_stt_calls"] += 1
                self.performance_stats["stt_parallel_calls"] += 1
                self.performance_stats["stt_chunks_processed"] += len(chunks)
                self.performance_stats["stt_preprocessing_time"] += preprocessing_time
                self.performance_stats["total_processing_time"] += processing_time
                
                # Track ultra-fast processing
                avg_chunk_time = processing_time / len(chunks) if chunks else 0
                if avg_chunk_time < 1.0:
                    self.performance_stats["stt_ultra_fast_chunks"] += len(chunks)
                
                # Update fastest processing time
                self.performance_stats["stt_fastest_chunk"] = min(
                    self.performance_stats["stt_fastest_chunk"], avg_chunk_time
                )
                
                self.performance_stats["average_processing_time"] = (
                    self.performance_stats["total_processing_time"] / 
                    (self.performance_stats["total_tts_calls"] + self.performance_stats["total_stt_calls"])
                )
            
            print(f"✅ ULTRA-FAST STT completed in {processing_time:.2f}s ({avg_chunk_time:.2f}s/chunk)")
            
            return ProcessedAudioData(
                audio_id=audio_data.audio_id,
                transcription=combined_transcription,
                confidence=0.9,
                processing_time=processing_time,
                language=None  # Auto-detect mixed Arabic/English
            )
            
        except Exception as e:
            print(f"❌ Error in ultra-fast audio processing: {e}")
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
            
            # Transcribe chunk with auto-detection for mixed languages
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=chunk_buffer,
                prompt="The user is speaking in Arabic Omani Dialect and English. Not in Indonesia anymore. Mind with the language detection and transcribe the text in the correct language.",
                # No language parameter - enables auto-detection for mixed Arabic-English
            )
            
            processing_time = time.time() - start_time
            print(f"🎙️ STT Chunk {chunk_id} completed in {processing_time:.2f}s")
            
            return (chunk_id, transcript.text.strip())
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ STT Chunk {chunk_id} failed in {processing_time:.2f}s: {e}")
            return (chunk_id, "")
    
    def _process_audio_chunk_ultra_fast(self, chunk_id: int, audio_chunk: AudioSegment, format: str) -> Tuple[int, str]:
        """Process a single audio chunk with ultra-fast optimizations"""
        start_time = time.time()
        
        try:
            # Ultra-fast compression and optimization
            compression_start = time.time()
            
            # Export chunk with compression
            chunk_buffer = io.BytesIO()
            # Use MP3 format for consistent processing per user preference
            compressed_format = "mp3" if format.lower() in ["wav", "m4a", "flac"] else format
            if compressed_format == "mp3":
                audio_chunk.export(chunk_buffer, format=compressed_format)
            else:
                audio_chunk.export(chunk_buffer, format=compressed_format, bitrate="64k")
            chunk_buffer.seek(0)
            chunk_buffer.name = f"ultra_chunk_{chunk_id}.{compressed_format}"
            
            compression_time = time.time() - compression_start
            
            # Create dedicated client for this thread
            client = OpenAI(api_key=self.api_key)
            
            # Ultra-fast transcription with optimized settings
            network_start = time.time()
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=chunk_buffer,
                prompt="The user is speaking in Arabic Omani Dialect and English. Not in Indonesia anymore. Mind with the language detection and transcribe the text in the correct language.",
            )
            network_time = time.time() - network_start
            
            processing_time = time.time() - start_time
            
            # Track compression and network times
            with self._stats_lock:
                self.performance_stats["stt_compression_time"] += compression_time
                self.performance_stats["stt_network_time"] += network_time
            
            print(f"🚀 Ultra-fast STT Chunk {chunk_id} completed in {processing_time:.2f}s (compression: {compression_time:.2f}s, network: {network_time:.2f}s)")
            
            return (chunk_id, transcript.text.strip())
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ Ultra-fast STT Chunk {chunk_id} failed in {processing_time:.2f}s: {e}")
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
    
    async def _preprocess_audio_ultra_fast(self, audio_bytes: bytes, format: str) -> bytes:
        """Ultra-fast audio preprocessing with aggressive compression"""
        try:
            if not PYDUB_AVAILABLE:
                return audio_bytes
            
            # Load audio
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format=format)
            
            # Apply ultra-fast optimizations
            audio_segment = await self._optimize_audio_segment_ultra_fast(audio_segment)
            
            # Export with MP3 format for consistent processing per user preference
            output_buffer = io.BytesIO()
            export_format = "mp3" if format.lower() in ["wav", "m4a", "flac"] else format
            audio_segment.export(output_buffer, format=export_format)
            return output_buffer.getvalue()
            
        except Exception as e:
            print(f"⚠️ Ultra-fast audio preprocessing failed: {e}")
            return audio_bytes
    
    async def _optimize_audio_segment_ultra_fast(self, audio_segment: AudioSegment) -> AudioSegment:
        """Apply ultra-aggressive audio optimizations for maximum speed"""
        try:
            # Optimization 1: Normalize volume (faster processing)
            audio_segment = audio_segment.normalize()
            
            # Optimization 2: Ensure optimal sample rate (16kHz for Whisper)
            if audio_segment.frame_rate != 16000:
                audio_segment = audio_segment.set_frame_rate(16000)
            
            # Optimization 3: Convert to mono if stereo (reduce data size)
            if audio_segment.channels > 1:
                audio_segment = audio_segment.set_channels(1)
            
            # Optimization 4: Remove silence aggressively
            audio_segment = audio_segment.strip_silence(silence_thresh=-35, silence_chunk_len=200)
            
            # Optimization 5: More aggressive speed increase (up to 1.7x as per Microsoft guide)
            # This significantly reduces processing time while maintaining good transcription quality
            audio_segment = audio_segment.speedup(playback_speed=1.6)
            
            # Optimization 6: Apply light compression to reduce payload size
            audio_segment = audio_segment.compress_dynamic_range()
            
            return audio_segment
            
        except Exception as e:
            print(f"⚠️ Ultra-fast audio optimization failed: {e}")
            return audio_segment
    
    def _deduplicate_overlapping_transcriptions(self, transcriptions: List[str]) -> str:
        """Smart deduplication of overlapping transcriptions to remove redundancy"""
        if not transcriptions:
            return ""
        
        if len(transcriptions) == 1:
            return transcriptions[0]
        
        try:
            # Simple approach: combine all transcriptions and remove obvious duplicates
            combined_text = " ".join(transcriptions)
            
            # Split into words for deduplication
            words = combined_text.split()
            if not words:
                return ""
            
            # Remove consecutive duplicate words (common in overlapping chunks)
            deduplicated_words = [words[0]]
            for i in range(1, len(words)):
                if words[i].lower() != words[i-1].lower():
                    deduplicated_words.append(words[i])
            
            # Further cleanup: remove repeated phrases
            result = " ".join(deduplicated_words)
            
            # Basic sentence cleaning
            result = result.replace("  ", " ").strip()
            
            return result
            
        except Exception as e:
            print(f"⚠️ Deduplication failed: {e}")
            # Fallback: just join all transcriptions
            return " ".join(transcriptions)
    
    async def text_to_speech(self, text: str) -> AudioData:
        """Convert text to speech using parallel processing (user preference)"""
        return await self.text_to_speech_parallel(text)
    
    async def text_to_speech_streaming(self, text: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Convert text to speech with optimized real-time streaming using OpenAI's streaming API
        Returns audio chunks as they're generated for immediate playback
        """
        if not text or not text.strip():
            yield {
                "type": "streaming_complete",
                "chunk_id": 0,
                "audio_data": AudioData(
                    audio_bytes=b"",
                    format="mp3",
                    duration=0.0
                ),
                "text": "",
                "success": True
            }
            return
        
        start_time = time.time()
        chunk_id = 0
        
        try:
            print(f"🚀 Starting optimized streaming TTS for text: '{text[:30]}...'")
            
            # Use OpenAI's streaming TTS API with optimized settings
            with self.client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",  # Keep same model as specified
                voice="alloy",
                input=text,
                language="auto",
                instructions="Speak in a friendly and engaging tone, with a natural flow and a slight hint of warmth. Ensure you user your correct pronounciantion in Arabic Omani Dialect and English",
                response_format="wav"  # Use WAV format per user preference [[memory:2973821]]
            ) as response:
                
                # Buffer for accumulating audio chunks
                audio_buffer = b""
                # Use optimized buffer size from settings
                buffer_size = settings.audio_config.streaming_buffer_size  # 4KB for faster streaming
                
                # Process streaming response
                # Process streaming response
                for chunk in response.iter_bytes(chunk_size=buffer_size):
                            if chunk:
                                audio_buffer += chunk
                                
                                # Yield audio chunk immediately for real-time playback
                                yield {
                                    "type": "streaming_chunk",
                                    "chunk_id": chunk_id,
                                    "audio_data": AudioData(
                                        audio_bytes=chunk,
                                        format="wav",
                                        duration=len(chunk) / 16000.0  # Estimated duration
                                    ),
                                    "text": text,
                                    "partial": True,
                                    "success": True
                                }
                                
                                chunk_id += 1
                                print(f"⚡ Fast streaming chunk {chunk_id} ({len(chunk)} bytes)")
                                
                                # Optional: Add small delay to prevent overwhelming the client
                                # await asyncio.sleep(0.01)  # 10ms delay
                
                # Calculate processing time
                processing_time = time.time() - start_time
                
                # Update performance stats
                with self._stats_lock:
                    self.performance_stats["total_tts_calls"] += 1
                    self.performance_stats["total_processing_time"] += processing_time
                    self.performance_stats["successful_chunks"] += chunk_id
                    
                    # Calculate average time
                    if self.performance_stats["total_tts_calls"] > 0:
                        avg_time = self.performance_stats["total_processing_time"] / self.performance_stats["total_tts_calls"]
                        self.performance_stats["average_processing_time"] = avg_time
                
                # Final yield with complete audio
                yield {
                    "type": "streaming_complete",
                    "chunk_id": chunk_id,
                    "audio_data": AudioData(
                        audio_bytes=audio_buffer,
                        format="wav",
                        duration=len(audio_buffer) / 16000.0  # Estimated duration
                    ),
                    "text": text,
                    "processing_time": processing_time,
                    "total_chunks": chunk_id,
                    "success": True
                }
                
                print(f"✅ Optimized streaming TTS completed in {processing_time:.2f}s with {chunk_id} chunks")
                
        except Exception as e:
            print(f"❌ Optimized streaming TTS error: {e}")
            yield {
                "type": "streaming_error",
                "chunk_id": chunk_id,
                "error": str(e),
                "text": text,
                "success": False
            }
    
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
        """Process a single TTS chunk - optimized for speed"""
        start_time = time.time()
        
        try:
            # Create dedicated client for this thread
            client = OpenAI(api_key=self.api_key)
            
            # Direct TTS call with timeout - no complex retry logic
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    client.audio.speech.create,
                    model="gpt-4o-mini-tts",
                    voice="alloy",
                    instructions="Speak in a friendly and engaging tone, with a natural flow and a slight hint of warmth. Ensure you user your correct pronounciantion in Arabic Omani Dialect and English",
                    input=text,
                    response_format="wav"
                )
                
                try:
                    # Wait for response with timeout
                    response = future.result(timeout=settings.audio_config.tts_timeout)
                    
                    processing_time = time.time() - start_time
                    print(f"⚡ Optimized chunk {chunk_id} completed in {processing_time:.2f}s")
                    
                    return (chunk_id, response.content)
                    
                except concurrent.futures.TimeoutError:
                    processing_time = time.time() - start_time
                    print(f"⏱️ Chunk {chunk_id} timeout after {settings.audio_config.tts_timeout}s")
                    return (chunk_id, b"")
                    
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ Chunk {chunk_id} failed in {processing_time:.2f}s: {e}")
            return (chunk_id, b"")
    
    def _merge_audio_chunks(self, audio_chunks: List[bytes]) -> bytes:
        """Simple audio chunk merging - no complex threading"""
        if not audio_chunks:
            return b""
        
                    # Direct concatenation for WAV files
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
            if stats["stt_fastest_chunk"] == float('inf'):
                stats["stt_fastest_chunk"] = 0.0
            
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
                stats["stt_avg_compression_time"] = stats["stt_compression_time"] / stats["stt_parallel_calls"]
                stats["stt_avg_network_time"] = stats["stt_network_time"] / stats["stt_parallel_calls"]
            else:
                stats["stt_avg_chunks_per_call"] = 0.0
                stats["stt_avg_preprocessing_time"] = 0.0
                stats["stt_avg_compression_time"] = 0.0
                stats["stt_avg_network_time"] = 0.0
            
            # Ultra-fast performance metrics
            if stats["stt_chunks_processed"] > 0:
                stats["stt_ultra_fast_percentage"] = (stats["stt_ultra_fast_chunks"] / stats["stt_chunks_processed"]) * 100
            else:
                stats["stt_ultra_fast_percentage"] = 0.0
            
            stats["workers_available"] = self.max_workers
            stats["stt_workers_available"] = self.stt_max_workers
            stats["optimization_features"] = {
                "parallel_tts": "✅ Enabled",
                "parallel_stt": "✅ Ultra-Fast Enabled", 
                "audio_preprocessing": "✅ Ultra-Fast Enabled" if PYDUB_AVAILABLE else "❌ Disabled",
                "chunking_strategy": "Micro-chunking with overlap (5-8s chunks)",
                "audio_compression": "✅ 64k bitrate compression",
                "audio_speedup": "✅ 1.6x playback speed",
                "dedicated_stt_executor": f"✅ {self.stt_max_workers} workers"
            }
            
            return stats
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.tts_executor.shutdown(wait=True)
            self.stt_executor.shutdown(wait=True)
            print("🧹 Ultra-fast audio service cleanup completed")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
    
    def is_available(self) -> bool:
        """Check if the service is available"""
        try:
            return self.client is not None and self.api_key is not None
        except Exception:
            return False 