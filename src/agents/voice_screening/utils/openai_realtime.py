"""
OpenAI Realtime API integration helpers for WebSocket communication.
"""
import os
import json
import asyncio
import websockets
from typing import Optional, Callable, Dict, Any
import base64


class OpenAIRealtimeClient:
    """
    Client for interacting with OpenAI Realtime API via WebSocket.
    """
    
    REALTIME_API_URL = "wss://api.openai.com/v1/realtime"
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-realtime-preview-2024-12-17"):
        """
        Initialize the Realtime API client.
        
        Args:
            api_key (str, optional): OpenAI API key. Defaults to OPENAI_API_KEY env var.
            model (str): Model to use for Realtime API
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment or provided")
        
        self.model = model
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.session_id: Optional[str] = None
        
    async def connect(self) -> None:
        """Establish WebSocket connection to OpenAI Realtime API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        url = f"{self.REALTIME_API_URL}?model={self.model}"
        self.websocket = await websockets.connect(url, extra_headers=headers)
        
        # Wait for session.created event
        initial_message = await self.websocket.recv()
        data = json.loads(initial_message)
        if data.get("type") == "session.created":
            self.session_id = data.get("session_id")
    
    async def send_audio(self, audio_data: bytes, format: str = "pcm16") -> None:
        """
        Send audio data to the Realtime API.
        
        Args:
            audio_data (bytes): Raw audio bytes
            format (str): Audio format (pcm16, g711_ulaw, g711_alaw)
        """
        if not self.websocket:
            raise RuntimeError("Not connected. Call connect() first.")
        
        # Encode audio as base64
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        message = {
            "type": "input_audio_buffer.append",
            "audio": audio_b64
        }
        
        await self.websocket.send(json.dumps(message))
    
    async def commit_audio(self) -> None:
        """Commit the audio buffer for processing."""
        if not self.websocket:
            raise RuntimeError("Not connected. Call connect() first.")
        
        message = {
            "type": "input_audio_buffer.commit"
        }
        
        await self.websocket.send(json.dumps(message))
    
    async def receive_messages(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Continuously receive messages from the Realtime API.
        
        Args:
            callback: Function to call with each received message
        """
        if not self.websocket:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            async for message in self.websocket:
                data = json.loads(message)
                callback(data)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
        except Exception as e:
            print(f"Error receiving messages: {e}")
    
    async def send_text(self, text: str) -> None:
        """
        Send text input to the Realtime API.
        
        Args:
            text (str): Text to send
        """
        if not self.websocket:
            raise RuntimeError("Not connected. Call connect() first.")
        
        message = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": text
                    }
                ]
            }
        }
        
        await self.websocket.send(json.dumps(message))
    
    async def get_response_text(self) -> Optional[str]:
        """
        Get the latest response text from the API.
        This is a simplified version - in practice, you'd handle response.done events.
        
        Returns:
            str: Response text, or None if not available
        """
        # This would need to be implemented based on the actual event flow
        # For now, return None as placeholder
        return None
    
    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

