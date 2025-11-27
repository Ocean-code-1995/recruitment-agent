"""
API Client utilities for the Supervisor UI.

Handles communication with the Supervisor API including SSE streaming.
"""

import os
import json
from typing import Generator
import requests


# API Configuration - use env var in Docker, fallback for local dev
API_BASE_URL = os.getenv("SUPERVISOR_API_URL", "http://localhost:8080/api/v1/supervisor")


def parse_sse_event(line: str) -> tuple[str | None, str | None]:
    """Parse a single SSE line into event type and data."""
    if line.startswith("event:"):
        return ("event", line[6:].strip())
    elif line.startswith("data:"):
        return ("data", line[5:].strip())
    return (None, None)


def stream_response(prompt: str, thread_id: str | None) -> Generator[tuple[str, dict], None, None]:
    """
    Stream response from the API using Server-Sent Events.
    
    Args:
        prompt: The user message to send
        thread_id: The conversation thread ID (or None for new conversation)
    
    Yields:
        tuple: (event_type, data) where event_type is 'token', 'done', or 'error'
    """
    payload = {
        "message": prompt,
        "thread_id": thread_id
    }
    
    try:
        with requests.post(
            f"{API_BASE_URL}/chat/stream",
            json=payload,
            stream=True,
            timeout=300  # Long timeout for agent processing
        ) as response:
            if response.status_code != 200:
                yield ("error", {"error": f"API returned status {response.status_code}"})
                return
            
            current_event = None
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                    
                key, value = parse_sse_event(line)
                
                if key == "event":
                    current_event = value
                elif key == "data" and current_event:
                    try:
                        data = json.loads(value)
                        yield (current_event, data)
                    except json.JSONDecodeError:
                        continue
                    current_event = None
                        
    except requests.exceptions.ConnectionError:
        yield ("error", {"error": "Cannot connect to API. Make sure the server is running."})
    except requests.exceptions.Timeout:
        yield ("error", {"error": "Request timed out."})
    except Exception as e:
        yield ("error", {"error": str(e)})


def create_new_chat() -> dict | None:
    """
    Create a new chat session via the API.
    
    Returns:
        dict with 'thread_id' and 'message' on success, None on failure
    """
    try:
        response = requests.post(f"{API_BASE_URL}/new")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None

