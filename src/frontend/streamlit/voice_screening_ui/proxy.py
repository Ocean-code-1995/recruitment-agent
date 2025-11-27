"""
WebSocket proxy for OpenAI Realtime API.
Handles authentication since browsers cannot set custom headers in WebSocket connections.
Also handles user authentication and session management.
"""
import asyncio
import os
import json
import logging
import secrets
import time
import base64
import wave
import io
import struct
from typing import Dict, Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import aiohttp
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice Screening WebSocket Proxy")

# Enable CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your Streamlit domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-realtime-mini"

# Session management (in-memory for MVP)
# In production, use Redis or database
sessions: Dict[str, dict] = {}  # session_token -> {email, expires_at, created_at}

# Session configuration (moved from frontend)
SESSION_CONFIG = {
    "modalities": ["audio", "text"],
    "instructions": "You are a friendly HR assistant conducting a phone screening interview. Greet the candidate warmly and ask them about their background and interest in the position.",
    "voice": "alloy",
    "input_audio_format": "pcm16",
    "output_audio_format": "pcm16",
    "turn_detection": {
        "type": "server_vad",
        "threshold": 0.5,
        "prefix_padding_ms": 300,
        "silence_duration_ms": 10000
    }
}

# Auth models
class LoginRequest(BaseModel):
    email: EmailStr

class VerifyRequest(BaseModel):
    email: EmailStr
    code: str


def generate_session_token() -> str:
    """Generate a secure session token."""
    return secrets.token_urlsafe(32)

def cleanup_expired_sessions():
    """Remove expired sessions."""
    current_time = time.time()
    
    # Clean up expired sessions
    expired_sessions = [
        token for token, session in sessions.items()
        if session.get("expires_at", 0) < current_time
    ]
    for token in expired_sessions:
        del sessions[token]

@app.post("/auth/login")
async def login(request: LoginRequest):
    """
    Request authentication for email.
    Just accepts the email - no code generation needed.
    """
    cleanup_expired_sessions()
    
    email = request.email.lower()

    logger.info(f"Login request for {email}")

    return {
        "message": "Please enter your authentication code",
        "email": email
    }

@app.post("/auth/verify")
async def verify(request: VerifyRequest):
    """
    Verify email and code, return session token.
    Authentication logic left empty for now - just accepts any code.
    """
    cleanup_expired_sessions()
    
    email = request.email.lower()
    code = request.code
    
    # TODO: Implement actual authentication logic here
    # For testing: accepts any email and code combination
    def authenticate_user(email: str, code: str) -> bool:
        """
        Authenticate user with email and code.
        For testing: accepts anything typed.
        TODO: Implement actual authentication logic.
        """
        # For testing purposes, accept any input
        return True
    
    # Authenticate user
    if not authenticate_user(email, code):
        raise HTTPException(status_code=401, detail="Invalid authentication code")
    
    # Authentication successful, create session
    session_token = generate_session_token()
    
    sessions[session_token] = {
        "email": email,
        "expires_at": time.time() + 3600,  # 1 hour
        "created_at": time.time(),
        "user_audio_chunks": [],  # List of {timestamp, data: bytes}
        "agent_audio_chunks": [],  # List of {timestamp, data: bytes}
        "transcript": [],  # List of {speaker, text, timestamp}
        "session_start_time": None  # Set when WebSocket connects
    }
    
    logger.info(f"Session created for {email}: {session_token[:8]}...")
    
    return {
        "session_token": session_token,
        "expires_in": 3600
    }

def validate_session_token(token: Optional[str]) -> Optional[dict]:
    """Validate session token and return session data."""
    if not token:
        return None
    
    cleanup_expired_sessions()
    
    if token not in sessions:
        return None
    
    session = sessions[token]
    
    if session["expires_at"] < time.time():
        del sessions[token]
        return None
    
    return session

@app.websocket("/ws/realtime")
async def websocket_proxy(websocket: WebSocket, token: Optional[str] = Query(None), candidate_id: Optional[str] = Query(None)):
    """
    Proxy WebSocket connection to OpenAI Realtime API.
    Adds proper authentication headers that browsers cannot set.
    Requires valid session token for authentication.
    """
    client_id = id(websocket)
    logger.info(f"[{client_id}] Client connecting...")
    
    # Validate session token
    session = validate_session_token(token)
    if not session:
        logger.warning(f"[{client_id}] Invalid or missing session token")
        await websocket.close(code=1008, reason="Invalid or expired session token")
        return
    
    await websocket.accept()
    logger.info(f"[{client_id}] Client connected (user: {session['email']})")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        error_msg = "API key not configured"
        logger.error(f"[{client_id}] {error_msg}")
        await websocket.close(code=1008, reason=error_msg)
        return
    
    try:
        # Connect to OpenAI Realtime API using aiohttp (better header support)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        logger.info(f"[{client_id}] Connecting to OpenAI Realtime API: {OPENAI_REALTIME_URL}")
        
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                OPENAI_REALTIME_URL,
                headers=headers
            ) as openai_ws:
                logger.info(f"[{client_id}] Connected to OpenAI Realtime API")
                
                # Send connection success message to client
                await websocket.send_json({
                    "type": "proxy.status",
                    "status": "connected",
                    "message": "Proxy connected to OpenAI Realtime API"
                })
                
                # Configure session (moved from frontend)
                # Get session configuration from backend API
                current_session_config = SESSION_CONFIG.copy()
                
                if candidate_id:
                    try:
                        import requests
                        # Get backend API URL
                        backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")
                        response = requests.get(
                            f"{backend_url}/api/v1/voice-screener/session/dummy/config",
                            params={"candidate_id": candidate_id},
                            timeout=5
                        )
                        if response.status_code == 200:
                            config_data = response.json()
                            current_session_config = config_data["config"]
                            logger.info(f"[{client_id}] Retrieved session config from backend for {config_data['candidate_name']}")
                        else:
                            logger.warning(f"[{client_id}] Failed to get config from backend: {response.status_code}")
                            # Fallback to default
                    except Exception as e:
                        logger.error(f"[{client_id}] Error fetching config from backend: {e}")
                        # Fallback to default instructions
                
                await openai_ws.send_str(json.dumps({
                    "type": "session.update",
                    "session": current_session_config
                }))
                logger.info(f"[{client_id}] Session configured")
                
                # Initialize session start time for audio buffering
                sessions[token]["session_start_time"] = time.time()
                
                # Send greeting after session is configured
                await asyncio.sleep(0.5)  # Small delay to ensure session is configured
                await openai_ws.send_str(json.dumps({
                    "type": "response.create",
                    "response": {
                        "modalities": ["audio", "text"],
                        "instructions": "Greet the candidate and ask them to tell you about themselves."
                    }
                }))
                logger.info(f"[{client_id}] Greeting sent")
                
                # Bidirectional message forwarding
                async def forward_to_openai():
                    """Forward messages from client to OpenAI."""
                    try:
                        async for message in websocket.iter_text():
                            try:
                                # Log message for debugging
                                msg_data = json.loads(message) if message else {}
                                msg_type = msg_data.get("type", "unknown")
                                logger.debug(f"[{client_id}] Client -> OpenAI: {msg_type}")
                                
                                # Capture user audio for recording
                                if msg_type == "input_audio_buffer.append":
                                    audio_base64 = msg_data.get("audio", "")
                                    if audio_base64:
                                        try:
                                            audio_data = base64.b64decode(audio_base64)
                                            sessions[token]["user_audio_chunks"].append({
                                                "timestamp": time.time(),
                                                "data": audio_data
                                            })
                                        except Exception as e:
                                            logger.warning(f"[{client_id}] Failed to decode user audio: {e}")
                                
                                await openai_ws.send_str(message)
                            except json.JSONDecodeError:
                                logger.warning(f"[{client_id}] Invalid JSON from client: {message[:100]}")
                                await openai_ws.send_str(message)
                    except WebSocketDisconnect:
                        logger.info(f"[{client_id}] Client disconnected")
                    except Exception as e:
                        error_msg = f"Error forwarding to OpenAI: {str(e)}"
                        logger.error(f"[{client_id}] {error_msg}", exc_info=True)
                        try:
                            await websocket.send_json({
                                "type": "proxy.error",
                                "error": error_msg,
                                "source": "forward_to_openai"
                            })
                        except:
                            pass
                
                async def forward_to_client():
                    """Forward messages from OpenAI to client."""
                    try:
                        async for msg in openai_ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                try:
                                    # Log message for debugging
                                    msg_data = json.loads(msg.data) if msg.data else {}
                                    msg_type = msg_data.get("type", "unknown")
                                    logger.debug(f"[{client_id}] OpenAI -> Client: {msg_type}")
                                    
                                    # Capture agent audio for recording
                                    if msg_type == "response.audio.delta":
                                        audio_base64 = msg_data.get("delta", "")
                                        if audio_base64:
                                            try:
                                                audio_data = base64.b64decode(audio_base64)
                                                sessions[token]["agent_audio_chunks"].append({
                                                    "timestamp": time.time(),
                                                    "data": audio_data
                                                })
                                            except Exception as e:
                                                logger.warning(f"[{client_id}] Failed to decode agent audio: {e}")
                                    
                                    # Capture transcript
                                    elif msg_type == "response.audio_transcript.done":
                                        # Candidate transcript
                                        text = msg_data.get("transcript", "")
                                        if text:
                                            sessions[token]["transcript"].append({
                                                "speaker": "candidate",
                                                "text": text,
                                                "timestamp": time.time()
                                            })
                                            logger.info(f"[{client_id}] Captured candidate transcript: {text[:30]}...")
                                            
                                    elif msg_type == "response.text.done":
                                        # Agent transcript (if using text modality)
                                        text = msg_data.get("text", "")
                                        if text:
                                            sessions[token]["transcript"].append({
                                                "speaker": "agent",
                                                "text": text,
                                                "timestamp": time.time()
                                            })
                                            logger.info(f"[{client_id}] Captured agent transcript: {text[:30]}...")
                                            
                                    # Also capture agent audio transcript if available (more accurate than text.done for audio)
                                    elif msg_type == "response.audio_transcript.done":
                                        # This event is for user input transcription usually, but check documentation
                                        pass
                                    
                                    await websocket.send_text(msg.data)
                                except Exception as e:
                                    logger.error(f"[{client_id}] Error sending message to client: {e}")
                                    await websocket.send_json({
                                        "type": "proxy.error",
                                        "error": f"Error sending message: {str(e)}",
                                        "source": "forward_to_client"
                                    })
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                error = openai_ws.exception()
                                error_msg = f"WebSocket error from OpenAI: {error}"
                                logger.error(f"[{client_id}] {error_msg}")
                                await websocket.send_json({
                                    "type": "proxy.error",
                                    "error": error_msg,
                                    "source": "openai_websocket"
                                })
                                break
                            elif msg.type == aiohttp.WSMsgType.CLOSE:
                                logger.info(f"[{client_id}] OpenAI closed connection: {msg.data}")
                                break
                            else:
                                logger.warning(f"[{client_id}] Unexpected message type from OpenAI: {msg.type}")
                    except Exception as e:
                        error_msg = f"Error forwarding to client: {str(e)}"
                        logger.error(f"[{client_id}] {error_msg}", exc_info=True)
                        try:
                            await websocket.send_json({
                                "type": "proxy.error",
                                "error": error_msg,
                                "source": "forward_to_client"
                            })
                        except:
                            pass
                
                # Run both forwarding tasks concurrently
                results = await asyncio.gather(
                    forward_to_openai(),
                    forward_to_client(),
                    return_exceptions=True
                )
                
                # Log any exceptions from the tasks
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"[{client_id}] Task {i} raised exception: {result}", exc_info=True)
            
    except aiohttp.ClientError as e:
        error_msg = f"OpenAI connection failed: {str(e)}"
        logger.error(f"[{client_id}] {error_msg}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "proxy.error",
                "error": error_msg,
                "source": "connection"
            })
        except:
            pass
        await websocket.close(code=1008, reason=error_msg)
    except Exception as e:
        error_msg = f"Proxy error: {str(e)}"
        logger.error(f"[{client_id}] {error_msg}", exc_info=True)
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({
                "type": "proxy.error",
                "error": error_msg,
                "source": "proxy",
                "traceback": traceback.format_exc()
            })
        except:
            pass
        await websocket.close(code=1011, reason=error_msg)



class RetrieveAudioRequest(BaseModel):
    session_id: str


@app.post("/audio/retrieve")
async def retrieve_audio(request: RetrieveAudioRequest, token: Optional[str] = Query(None)):
    """
    Retrieve audio chunks for a session.
    Backend will call this to get chunks for processing.
    
    Args:
        request: Contains session_id.
        token: Session token from query parameter.
    
    Returns:
        dict: Contains user_chunks, agent_chunks, and session_start_time.
    """
    session = validate_session_token(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    
    try:
        user_chunks = session.get("user_audio_chunks", [])
        agent_chunks = session.get("agent_audio_chunks", [])
        transcript = session.get("transcript", [])
        session_start_time = session.get("session_start_time")
        
        # Base64 encode chunks for JSON transport
        encoded_user_chunks = []
        for chunk in user_chunks:
            encoded_chunk = chunk.copy()
            if isinstance(chunk.get("data"), bytes):
                encoded_chunk["data"] = base64.b64encode(chunk["data"]).decode("utf-8")
            encoded_user_chunks.append(encoded_chunk)
            
        encoded_agent_chunks = []
        for chunk in agent_chunks:
            encoded_chunk = chunk.copy()
            if isinstance(chunk.get("data"), bytes):
                encoded_chunk["data"] = base64.b64encode(chunk["data"]).decode("utf-8")
            encoded_agent_chunks.append(encoded_chunk)
        
        logger.info(f"Retrieved {len(user_chunks)} user chunks, {len(agent_chunks)} agent chunks, and {len(transcript)} transcript lines for session {request.session_id}")
        
        return {
            "user_chunks": encoded_user_chunks,
            "agent_chunks": encoded_agent_chunks,
            "transcript": transcript,
            "session_start_time": session_start_time
        }
    except Exception as e:
        logger.error(f"Error retrieving audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audio: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    cleanup_expired_sessions()
    return {
        "status": "healthy",
        "openai_api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "active_sessions": len(sessions)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

