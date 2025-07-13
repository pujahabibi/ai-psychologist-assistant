#!/usr/bin/env python3
"""
Therapy Interaction Use Cases - Business logic for therapeutic interactions
"""

import time
import asyncio
import re
from typing import Dict, Optional, Any, List, AsyncGenerator
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from ..entities.therapeutic_session import TherapeuticSession
from ..entities.audio_data import AudioData
from ..entities.therapeutic_response import TherapeuticResponse, ModelValidationResponse
from ..interfaces.ai_service import IAIOrchestrator
from ..interfaces.audio_service import IAudioService
from ..interfaces.session_service import ISessionManager


class TherapyInteractionUseCase:
    """Use case for handling therapy interactions"""
    
    def __init__(
        self,
        ai_orchestrator: IAIOrchestrator,
        audio_service: IAudioService,
        session_manager: ISessionManager,
        system_prompt: str
    ):
        self.ai_orchestrator = ai_orchestrator
        self.audio_service = audio_service
        self.session_manager = session_manager
        self.system_prompt = system_prompt
        # Create executor for parallel TTS processing
        self.tts_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="StreamTTS")
    
    async def process_voice_therapy(
        self,
        audio_data: AudioData,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process complete voice therapy interaction"""
        start_time = time.time()
        
        try:
            # Get or create session
            if not session_id:
                session_id = str(uuid4())
            
            session = self.session_manager.get_session(session_id)
            if not session:
                session = self.session_manager.create_session(session_id)
            
            # Convert speech to text
            processed_audio = await self.audio_service.speech_to_text(audio_data)
            
            if not processed_audio.transcription:
                return {
                    "success": False,
                    "error": "Maaf, saya tidak dapat mendengar suara Anda dengan jelas. Silakan coba lagi.",
                    "session_id": session_id
                }
            
            # Add user input to session
            session.add_conversation_entry("user", processed_audio.transcription)
            
            # Get therapeutic response
            response = await self.ai_orchestrator.get_therapeutic_response(
                processed_audio.transcription,
                session.get_conversation_context(),
                session_id,
                self.system_prompt
            )
            
            # Add AI response to session
            session.add_conversation_entry("assistant", response.content)
            
            # Convert response to speech (always use parallel processing per user preference)
            response_audio = await self.audio_service.text_to_speech(response.content)
            
            # Update session
            self.session_manager.update_session(session)
            
            # Calculate latency
            latency = time.time() - start_time
            
            return {
                "success": True,
                "user_text": processed_audio.transcription,
                "ai_response": response.content,
                "audio_data": response_audio,
                "session_id": session_id,
                "latency": latency,
                "response_metrics": response.get_response_metrics()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Terjadi kesalahan dalam memproses permintaan Anda: {str(e)}",
                "session_id": session_id
            }

    async def process_streaming_therapy(
        self,
        user_input: str,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process streaming therapy interaction with optimized word-based chunking"""
        start_time = time.time()
        
        try:
            # Get or create session
            if not session_id:
                session_id = str(uuid4())
            
            session = self.session_manager.get_session(session_id)
            if not session:
                session = self.session_manager.create_session(session_id)
            
            # Add user input to session
            session.add_conversation_entry("user", user_input)
            
            # Initialize optimized streaming variables
            word_buffer = []
            full_response = ""
            chunk_id = 0
            words_per_chunk = 5  # Process 5 words at a time for faster response
            
            print(f"🚀 Starting optimized streaming therapy for session {session_id}")
            
            # Start streaming response
            async for chunk in self.ai_orchestrator.get_streaming_therapeutic_response(
                user_input,
                session.get_conversation_context(),
                session_id,
                self.system_prompt
            ):
                # Add chunk to buffer and full response
                full_response += chunk
                
                # Split chunk into words
                words = chunk.split()
                word_buffer.extend(words)
                
                # Process words in chunks for immediate TTS
                while len(word_buffer) >= words_per_chunk:
                    # Get current word chunk
                    current_words = word_buffer[:words_per_chunk]
                    word_buffer = word_buffer[words_per_chunk:]
                    
                    # Create text from words
                    chunk_text = " ".join(current_words)
                    
                    if chunk_text.strip():
                        print(f"⚡ Processing word chunk {chunk_id}: '{chunk_text}'")
                        
                        # Process TTS immediately without complex async nesting
                        try:
                            # Start streaming TTS processing
                            async for audio_chunk in self.audio_service.text_to_speech_streaming(chunk_text):
                                    if audio_chunk.get("type") == "streaming_chunk":
                                        yield {
                                            "type": "realtime_audio_chunk",
                                            "content": chunk_text,
                                            "session_id": session_id,
                                            "chunk_id": chunk_id,
                                            "audio_chunk_id": audio_chunk.get("chunk_id", 0),
                                            "audio_data": audio_chunk["audio_data"],
                                            "partial": True,
                                            "partial_response": full_response
                                        }
                                    elif audio_chunk.get("type") == "streaming_complete":
                                        yield {
                                            "type": "sentence_audio_complete",
                                            "content": chunk_text,
                                            "session_id": session_id,
                                            "chunk_id": chunk_id,
                                            "audio_data": audio_chunk["audio_data"],
                                            "processing_time": audio_chunk.get("processing_time", 0),
                                            "total_chunks": audio_chunk.get("total_chunks", 0),
                                            "partial_response": full_response
                                        }
                                        break

                        except Exception as e:
                            print(f"❌ TTS error for chunk {chunk_id}: {e}")
                            yield {
                                "type": "sentence_audio_error",
                                "content": chunk_text,
                                "session_id": session_id,
                                "chunk_id": chunk_id,
                                "error": str(e),
                                "partial_response": full_response
                            }
                        
                        # Yield text chunk
                        yield {
                            "type": "text_chunk",
                            "content": chunk_text,
                            "session_id": session_id,
                            "chunk_id": chunk_id,
                            "partial_response": full_response
                        }
                        
                        chunk_id += 1
                
                # Yield streaming update
                yield {
                    "type": "streaming_chunk",
                    "content": chunk,
                    "session_id": session_id,
                    "partial_response": full_response
                }
            
            # Process remaining words in buffer
            if word_buffer:
                remaining_text = " ".join(word_buffer)
                if remaining_text.strip():
                    print(f"⚡ Processing remaining words: '{remaining_text}'")
                    
                    try:
                        # Process remaining text streaming TTS
                        async for audio_chunk in self.audio_service.text_to_speech_streaming(remaining_text):
                                if audio_chunk.get("type") == "streaming_chunk":
                                    yield {
                                        "type": "realtime_audio_chunk",
                                        "content": remaining_text,
                                        "session_id": session_id,
                                        "chunk_id": chunk_id,
                                        "audio_chunk_id": audio_chunk.get("chunk_id", 0),
                                        "audio_data": audio_chunk["audio_data"],
                                        "partial": True,
                                        "partial_response": full_response
                                    }
                                elif audio_chunk.get("type") == "streaming_complete":
                                    yield {
                                        "type": "sentence_audio_complete",
                                        "content": remaining_text,
                                        "session_id": session_id,
                                        "chunk_id": chunk_id,
                                        "audio_data": audio_chunk["audio_data"],
                                        "processing_time": audio_chunk.get("processing_time", 0),
                                        "total_chunks": audio_chunk.get("total_chunks", 0),
                                        "partial_response": full_response
                                    }
                                    break
                    except Exception as e:
                        print(f"❌ TTS error for remaining text: {e}")
            
            # Add AI response to session
            session.add_conversation_entry("assistant", full_response)
            
            # Update session
            self.session_manager.update_session(session)
            
            # Calculate latency
            latency = time.time() - start_time
            
            print(f"✅ Optimized streaming completed in {latency:.2f}s with {chunk_id} chunks")
            
            # Final yield with complete response
            yield {
                "type": "complete_response",
                "content": full_response,
                "session_id": session_id,
                "latency": latency,
                "chunks_processed": chunk_id,
                "success": True
            }
            
        except Exception as e:
            print(f"❌ Streaming therapy error: {e}")
            yield {
                "type": "error",
                "error": f"Terjadi kesalahan dalam memproses permintaan Anda: {str(e)}",
                "session_id": session_id,
                "success": False
            }

    def _extract_complete_sentences(self, text: str) -> List[str]:
        """Extract complete sentences from text buffer"""
        # Indonesian sentence endings
        sentence_endings = r'[.!?;]\s+'
        
        # Find all complete sentences
        sentences = re.split(sentence_endings, text)
        
        # Check if the text ends with a sentence ending
        if re.search(r'[.!?;]\s*$', text):
            # All sentences are complete
            return [s.strip() for s in sentences if s.strip()]
        else:
            # Last sentence is incomplete, return all but the last
            return [s.strip() for s in sentences[:-1] if s.strip()]

    def _get_remaining_text(self, text: str, processed_sentences: List[str]) -> str:
        """Get remaining text after removing processed sentences"""
        remaining = text
        for sentence in processed_sentences:
            # Remove the sentence and its ending punctuation
            pattern = re.escape(sentence) + r'[.!?;]\s*'
            remaining = re.sub(pattern, '', remaining, count=1)
        return remaining

    def _process_sentence_tts(self, sentence: str, chunk_id: int) -> Dict[str, Any]:
        """Process a single sentence through streaming TTS (synchronous for executor) - Legacy method"""
        try:
            print(f"🎤 Processing streaming TTS for chunk {chunk_id}: '{sentence[:50]}...'")
            
            # Run streaming TTS processing synchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Use streaming TTS processing for real-time audio
                audio_chunks = []
                complete_audio = None
                
                async def collect_streaming_chunks():
                    async for chunk in self.audio_service.text_to_speech_streaming(sentence):
                        if chunk.get("type") == "streaming_chunk":
                            # Collect streaming chunks
                            audio_chunks.append(chunk["audio_data"].audio_bytes)
                        elif chunk.get("type") == "streaming_complete":
                            # Get the complete audio data
                            nonlocal complete_audio
                            complete_audio = chunk["audio_data"]
                            break
                        elif chunk.get("type") == "streaming_error":
                            print(f"❌ Streaming TTS error for chunk {chunk_id}: {chunk.get('error')}")
                            raise Exception(chunk.get("error", "Unknown streaming error"))
                
                # Run the async function in the event loop
                loop.run_until_complete(collect_streaming_chunks())
                
                # Return the complete audio data
                return {
                    "chunk_id": chunk_id,
                    "audio_data": complete_audio,
                    "sentence": sentence,
                    "success": True,
                    "streaming_chunks": len(audio_chunks)
                }
                
            finally:
                loop.close()
                
        except Exception as e:
            print(f"❌ Streaming TTS processing failed for chunk {chunk_id}: {e}")
            return {
                "chunk_id": chunk_id,
                "audio_data": None,
                "sentence": sentence,
                "success": False,
                "error": str(e)
            }

    # Note: Streaming TTS processing is now handled directly in the main streaming loop for better performance
    
    # Note: Audio merging method removed - now sending individual audio chunks
    
    async def process_text_therapy(
        self,
        user_input: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process text-based therapy interaction"""
        try:
            # Get or create session
            if not session_id:
                session_id = str(uuid4())
            
            session = self.session_manager.get_session(session_id)
            if not session:
                session = self.session_manager.create_session(session_id)
            
            # Add user input to session
            session.add_conversation_entry("user", user_input)
            
            # Get therapeutic response
            response = await self.ai_orchestrator.get_therapeutic_response(
                user_input,
                session.get_conversation_context(),
                session_id,
                self.system_prompt
            )
            
            # Add AI response to session
            session.add_conversation_entry("assistant", response.content)
            
            # Update session
            self.session_manager.update_session(session)
            
            return {
                "success": True,
                "response": response.content,
                "session_id": session_id,
                "response_metrics": response.get_response_metrics()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Terjadi kesalahan dalam memproses permintaan Anda: {str(e)}",
                "session_id": session_id
            }
    
    async def get_validated_response(
        self,
        user_input: str,
        session_id: Optional[str] = None
    ) -> ModelValidationResponse:
        """Get validated response from multiple models"""
        if not session_id:
            session_id = str(uuid4())
        
        session = self.session_manager.get_session(session_id)
        if not session:
            session = self.session_manager.create_session(session_id)
        
        return await self.ai_orchestrator.get_validated_response(
            user_input,
            session.get_conversation_context(),
            session_id,
            self.system_prompt
        )
    
    async def convert_text_to_speech(
        self,
        text: str,
        use_parallel: bool = True  # Always use parallel per user preference
    ) -> AudioData:
        """Convert text to speech with parallel processing"""
        return await self.audio_service.text_to_speech(text)
    
    async def convert_speech_to_text(
        self,
        audio_data: AudioData
    ) -> str:
        """Convert speech to text"""
        processed = await self.audio_service.speech_to_text(audio_data)
        return processed.transcription
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        session = self.session_manager.get_session(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "conversation_count": session.get_conversation_count(),
            "user_messages": session.get_user_messages_count(),
            "assistant_messages": session.get_assistant_messages_count(),
            "duration": session.get_session_duration(),
            "is_active": session.is_active(),
            "metadata": session.metadata
        }
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        return self.session_manager.delete_session(session_id)
    
    def list_sessions(self) -> list:
        """List all active sessions"""
        return self.session_manager.list_sessions()
    
    def get_session_analysis(self, session_id: str) -> Dict[str, Any]:
        """Get session analysis"""
        session = self.session_manager.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return session.get_analysis_summary() 