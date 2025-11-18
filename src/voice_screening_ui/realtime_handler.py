"""
Handler for managing OpenAI Realtime API WebSocket connections and audio processing.
"""
import json
import asyncio
import base64
from typing import Optional, Callable, Dict, Any
from src.agents.voice_screening.utils.openai_realtime import OpenAIRealtimeClient


class RealtimeCallHandler:
    """
    Manages a single call's connection to OpenAI Realtime API.
    """
    
    def __init__(self, call_sid: str, candidate_id: str):
        """
        Initialize handler for a call.
        
        Args:
            call_sid: Twilio Call SID
            candidate_id: Candidate UUID
        """
        self.call_sid = call_sid
        self.candidate_id = candidate_id
        self.client: Optional[OpenAIRealtimeClient] = None
        self.transcript: list = []
        self.is_connected = False
        self.response_callback: Optional[Callable[[str], None]] = None
        
    async def connect(self) -> None:
        """Establish connection to OpenAI Realtime API."""
        self.client = OpenAIRealtimeClient()
        await self.client.connect()
        self.is_connected = True
        
        # Start receiving messages
        asyncio.create_task(self._receive_loop())
    
    async def _receive_loop(self) -> None:
        """Continuously receive and process messages from OpenAI."""
        if not self.client:
            return
        
        async def handle_message(data: Dict[str, Any]):
            event_type = data.get("type")
            
            if event_type == "response.audio_transcript.delta":
                # Partial transcription
                delta = data.get("delta", "")
                # Handle partial transcript
                
            elif event_type == "response.audio_transcript.done":
                # Complete transcription
                transcript_text = data.get("text", "")
                self.transcript.append({
                    "speaker": "candidate",
                    "text": transcript_text
                })
                
            elif event_type == "response.text.done":
                # Agent response text
                text = data.get("text", "")
                if self.response_callback:
                    self.response_callback(text)
        
        await self.client.receive_messages(handle_message)
    
    async def send_audio_chunk(self, audio_data: bytes) -> None:
        """
        Send audio chunk to OpenAI Realtime API.
        
        Args:
            audio_data: Raw audio bytes (PCM16 format from Twilio)
        """
        if not self.client or not self.is_connected:
            return
        
        await self.client.send_audio(audio_data, format="pcm16")
    
    async def commit_audio(self) -> None:
        """Commit audio buffer for processing."""
        if not self.client or not self.is_connected:
            return
        
        await self.client.commit_audio()
    
    async def close(self) -> None:
        """Close the connection."""
        if self.client:
            await self.client.close()
            self.is_connected = False
    
    def get_transcript(self) -> list:
        """Get the current transcript."""
        return self.transcript


# Global store for active call handlers
_active_handlers: Dict[str, RealtimeCallHandler] = {}


def get_handler(call_sid: str) -> Optional[RealtimeCallHandler]:
    """Get handler for a call SID."""
    return _active_handlers.get(call_sid)


def register_handler(call_sid: str, candidate_id: str) -> RealtimeCallHandler:
    """Register a new call handler."""
    handler = RealtimeCallHandler(call_sid, candidate_id)
    _active_handlers[call_sid] = handler
    return handler


def remove_handler(call_sid: str) -> None:
    """Remove handler for a call."""
    if call_sid in _active_handlers:
        handler = _active_handlers[call_sid]
        asyncio.create_task(handler.close())
        del _active_handlers[call_sid]

