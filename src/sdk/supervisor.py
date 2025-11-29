"""
Supervisor API Client.

A client for interacting with the HR Supervisor Agent API.
Supports both regular and streaming responses.

=============================================================================
AVAILABLE METHODS:
=============================================================================

WITH CONTEXT ENGINEERING (CompactingSupervisor wrapper):
    - chat()    : Batch response with automatic context compaction
    - stream()  : Streaming response with context compaction [HAS ERRORS - TODO FIX]

RAW SUPERVISOR (Direct agent access, no wrapper):
    - chat_raw()    : Batch response, direct supervisor agent
    - stream_raw()  : Streaming response, direct supervisor agent [HAS ERRORS - TODO FIX]

=============================================================================
NOTE: Both streaming methods (stream() and stream_raw()) have known issues 
that need to be fixed. Use batch methods (chat, chat_raw) for reliable operation.
=============================================================================
"""

import os
import json
from dataclasses import dataclass
from typing import Generator, Optional
import requests


def _clean_base_url(url: str) -> str:
    """Normalize base URL to avoid issues from quoted env vars."""
    cleaned = url.strip().strip("\"'")
    if cleaned.endswith("/"):
        cleaned = cleaned[:-1]
    return cleaned


@dataclass
class ChatResponse:
    """Response from a chat request."""
    content: str
    thread_id: str
    token_count: int


@dataclass
class StreamChunk:
    """A chunk from a streaming response."""
    type: str  # 'token', 'done', or 'error'
    content: Optional[str] = None
    thread_id: Optional[str] = None
    token_count: Optional[int] = None
    error: Optional[str] = None


class SupervisorClient:
    """
    Client for the HR Supervisor Agent API.
    
    Two categories of methods:
    
    1. WITH CONTEXT ENGINEERING (uses CompactingSupervisor wrapper):
       - chat()   : Batch request with automatic context compaction
       - stream() : Streaming with context compaction [HAS ERRORS - TODO FIX]
       
    2. RAW SUPERVISOR (direct agent access, no wrapper):
       - chat_raw()   : Batch request, direct supervisor agent
       - stream_raw() : Streaming, direct supervisor agent [HAS ERRORS - TODO FIX]
    
    ⚠️ NOTE: Both streaming methods have issues. Use batch methods for reliable operation.
    
    Usage:
        client = SupervisorClient()
        
        # Batch chat with context engineering (RECOMMENDED)
        response = client.chat("Show me all candidates")
        print(response.content)
        
        # Batch chat without wrapper (RECOMMENDED)
        response = client.chat_raw("Show me all candidates")
        print(response.content)
        
        # With conversation continuity
        response1 = client.chat("Show me all candidates", thread_id="abc123")
        response2 = client.chat("Tell me more about the first one", thread_id="abc123")
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the Supervisor client.
        
        Args:
            base_url: API base URL. Defaults to SUPERVISOR_API_URL env var
                      or http://localhost:8080/api/v1/supervisor
        """
        raw = base_url or os.getenv(
            "SUPERVISOR_API_URL", 
            "http://localhost:8080/api/v1/supervisor"
        )
        self.base_url = _clean_base_url(raw)
    
    # =========================================================================
    # CONTEXT ENGINEERING METHODS (with CompactingSupervisor wrapper)
    # =========================================================================
    
    def chat(self, message: str, thread_id: Optional[str] = None, timeout: int = 120) -> ChatResponse:
        """
        Send a message and get a complete response.
        
        Uses CompactingSupervisor wrapper for automatic context management.
        When token limit is exceeded, old messages are compacted/summarized.
        
        Args:
            message: The message to send
            thread_id: Optional thread ID for conversation continuity
            timeout: Request timeout in seconds
            
        Returns:
            ChatResponse with content, thread_id, and token_count
            
        Raises:
            requests.exceptions.RequestException: On connection errors
            ValueError: On API errors
        """
        payload = {"message": message, "thread_id": thread_id}
        
        response = requests.post(
            f"{self.base_url}/chat",
            json=payload,
            timeout=timeout
        )
        
        if response.status_code != 200:
            error = response.json().get("detail", "Unknown error")
            raise ValueError(f"API error: {error}")
        
        data = response.json()
        return ChatResponse(
            content=data["response"],
            thread_id=data["thread_id"],
            token_count=data["token_count"]
        )
    
    def stream(
        self, 
        message: str, 
        thread_id: Optional[str] = None, 
        timeout: int = 300
    ) -> Generator[StreamChunk, None, None]:
        """
        Send a message and stream the response token by token.
        
        ⚠️ WARNING: This method has known issues and needs to be fixed.
        Use stream_raw() for reliable streaming, or chat() for batch requests.
        
        Uses CompactingSupervisor wrapper for automatic context management.
        
        Args:
            message: The message to send
            thread_id: Optional thread ID for conversation continuity
            timeout: Request timeout in seconds
            
        Yields:
            StreamChunk objects with type 'token', 'done', or 'error'
            
        Example:
            full_response = ""
            for chunk in client.stream("Hello"):
                if chunk.type == "token":
                    full_response += chunk.content
                    print(chunk.content, end="", flush=True)
                elif chunk.type == "done":
                    print(f"\\nThread: {chunk.thread_id}")
                elif chunk.type == "error":
                    print(f"Error: {chunk.error}")
        """
        payload = {"message": message, "thread_id": thread_id}
        
        try:
            with requests.post(
                f"{self.base_url}/chat/stream",
                json=payload,
                stream=True,
                timeout=timeout
            ) as response:
                if response.status_code != 200:
                    yield StreamChunk(
                        type="error",
                        error=f"API returned status {response.status_code}"
                    )
                    return
                
                current_event = None
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    
                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                    elif line.startswith("data:") and current_event:
                        try:
                            data = json.loads(line[5:].strip())
                            
                            if current_event == "token":
                                yield StreamChunk(
                                    type="token",
                                    content=data.get("content", "")
                                )
                            elif current_event == "done":
                                yield StreamChunk(
                                    type="done",
                                    thread_id=data.get("thread_id"),
                                    token_count=data.get("token_count", 0)
                                )
                            elif current_event == "error":
                                yield StreamChunk(
                                    type="error",
                                    error=data.get("error", "Unknown error")
                                )
                        except json.JSONDecodeError:
                            continue
                        current_event = None
                        
        except requests.exceptions.ConnectionError:
            yield StreamChunk(
                type="error",
                error="Cannot connect to API. Make sure the server is running."
            )
        except requests.exceptions.Timeout:
            yield StreamChunk(type="error", error="Request timed out.")
        except Exception as e:
            yield StreamChunk(type="error", error=str(e))
    
    def new_chat(self) -> str:
        """
        Create a new chat session.
        
        Returns:
            New thread_id
            
        Raises:
            requests.exceptions.RequestException: On connection errors
        """
        response = requests.post(f"{self.base_url}/new")
        response.raise_for_status()
        return response.json()["thread_id"]
    

    
    # =========================================================================
    # RAW SUPERVISOR METHODS (No CompactingSupervisor wrapper)
    # =========================================================================
    
    def chat_raw(self, message: str, thread_id: Optional[str] = None, timeout: int = 120) -> ChatResponse:
        """
        Send a message to the raw supervisor agent (without context compaction).
        
        This bypasses the CompactingSupervisor wrapper, giving direct access
        to the underlying supervisor agent. Useful for debugging or when you
        want full control over context management.
        
        Args:
            message: The message to send
            thread_id: Optional thread ID for conversation continuity
            timeout: Request timeout in seconds
            
        Returns:
            ChatResponse with content, thread_id, and token_count
            
        Raises:
            requests.exceptions.RequestException: On connection errors
            ValueError: On API errors
        """
        payload = {"message": message, "thread_id": thread_id}
        
        response = requests.post(
            f"{self.base_url}/raw/chat",
            json=payload,
            timeout=timeout
        )
        
        if response.status_code != 200:
            error = response.json().get("detail", "Unknown error")
            raise ValueError(f"API error: {error}")
        
        data = response.json()
        return ChatResponse(
            content=data["response"],
            thread_id=data["thread_id"],
            token_count=data["token_count"]
        )
    
    def stream_raw(
        self, 
        message: str, 
        thread_id: Optional[str] = None, 
        timeout: int = 300
    ) -> Generator[StreamChunk, None, None]:
        """
        Stream a response from the raw supervisor agent (without context compaction).
        
        ⚠️ WARNING: This method has known issues and needs to be fixed.
        Use chat_raw() for reliable batch requests.
        
        This bypasses the CompactingSupervisor wrapper, giving direct access
        to the underlying supervisor agent's streaming capabilities.
        
        Args:
            message: The message to send
            thread_id: Optional thread ID for conversation continuity
            timeout: Request timeout in seconds
            
        Yields:
            StreamChunk objects with type 'token', 'done', or 'error'
            
        Example:
            full_response = ""
            for chunk in client.stream_raw("Hello"):
                if chunk.type == "token":
                    full_response += chunk.content
                    print(chunk.content, end="", flush=True)
                elif chunk.type == "done":
                    print(f"\\nThread: {chunk.thread_id}")
                elif chunk.type == "error":
                    print(f"Error: {chunk.error}")
        """
        payload = {"message": message, "thread_id": thread_id}
        
        try:
            with requests.post(
                f"{self.base_url}/raw/chat/stream",
                json=payload,
                stream=True,
                timeout=timeout
            ) as response:
                if response.status_code != 200:
                    yield StreamChunk(
                        type="error",
                        error=f"API returned status {response.status_code}"
                    )
                    return
                
                current_event = None
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    
                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                    elif line.startswith("data:") and current_event:
                        try:
                            data = json.loads(line[5:].strip())
                            
                            if current_event == "token":
                                yield StreamChunk(
                                    type="token",
                                    content=data.get("content", "")
                                )
                            elif current_event == "done":
                                yield StreamChunk(
                                    type="done",
                                    thread_id=data.get("thread_id"),
                                    token_count=data.get("token_count", 0)
                                )
                            elif current_event == "error":
                                yield StreamChunk(
                                    type="error",
                                    error=data.get("error", "Unknown error")
                                )
                        except json.JSONDecodeError:
                            continue
                        current_event = None
                        
        except requests.exceptions.ConnectionError:
            yield StreamChunk(
                type="error",
                error="Cannot connect to API. Make sure the server is running."
            )
        except requests.exceptions.Timeout:
            yield StreamChunk(type="error", error="Request timed out.")
        except Exception as e:
            yield StreamChunk(type="error", error=str(e))


    def health(self) -> bool:
        """
        Check if the API is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
