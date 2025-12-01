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
from sqlalchemy import select, desc
from src.database.candidates.models import Candidate, CVScreeningResult
from src.database.candidates.client import SessionLocal
from src.voice_screening_ui.utils.questions import get_screening_questions
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
                # Dynamic session configuration based on candidate
                current_session_config = SESSION_CONFIG.copy()
                
                if candidate_id:
                    try:
                        with SessionLocal() as db:
                            # Fetch candidate
                            candidate = db.execute(
                                select(Candidate).where(Candidate.id == candidate_id)
                            ).scalar_one_or_none()
                            
                            if candidate:
                                # Fetch latest CV screening result for job title
                                cv_result = db.execute(
                                    select(CVScreeningResult)
                                    .where(CVScreeningResult.candidate_id == candidate_id)
                                    .order_by(desc(CVScreeningResult.timestamp))
                                    .limit(1)
                                ).scalar_one_or_none()
                                
                                job_title = cv_result.job_title if cv_result else "the position"
                                questions = get_screening_questions(job_title)
                                
                                instructions = (
                                    f"You are a friendly HR assistant conducting a phone screening interview with {candidate.full_name} "
                                    f"for the position of {job_title}. "
                                    f"Greet the candidate warmly by name. "
                                    f"Your goal is to ask the following main questions to assess their fit:\n\n"
                                )
                                
                                for i, q in enumerate(questions, 1):
                                    instructions += f"{i}. {q}\n"
                                    
                                instructions += (
                                    "\nAsk one question at a time. Wait for their response before moving to the next. "
                                    "Keep the conversations brief and to the point, ask only one follow-up question per main question. If they ask clarifying questions, answer them briefly."
                                )
                                
                                current_session_config["instructions"] = instructions
                                logger.info(f"[{client_id}] Generated dynamic instructions for candidate {candidate.full_name}")
                    except Exception as e:
                        logger.error(f"[{client_id}] Error fetching candidate info: {e}")
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


def combine_and_export_audio(session_token: str, session_id: str) -> bytes:
    """
    Combine user and agent audio chunks and export as WAV file.
    
    Audio chunks are continuous streams - we concatenate them in order and mix
    based on when each stream actually started relative to session start.
    
    Args:
        session_token: The session token to retrieve audio chunks.
        session_id: The session ID for logging.
    
    Returns:
        bytes: WAV file data.
    """
    session = sessions.get(session_token)
    if not session:
        raise ValueError("Session not found")
    
    user_chunks = session.get("user_audio_chunks", [])
    agent_chunks = session.get("agent_audio_chunks", [])
    session_start_time = session.get("session_start_time")
    
    if not session_start_time:
        raise ValueError("Session start time not found")
    
    if not user_chunks and not agent_chunks:
        logger.warning(f"No audio chunks found for session {session_id}")
        # Return empty WAV file
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit = 2 bytes
            wav_file.setframerate(24000)  # OpenAI uses 24kHz
            wav_file.writeframes(b'')
        return wav_buffer.getvalue()
    
    # Sample rate: OpenAI Realtime API uses 24kHz PCM16
    SAMPLE_RATE = 24000
    BYTES_PER_SAMPLE = 2  # 16-bit = 2 bytes
    
    # Detect user audio sample rate (browser typically captures at 48kHz)
    user_sample_rate = SAMPLE_RATE  # Default to 24kHz
    if len(user_chunks) >= 2:
        time_diff = user_chunks[1]["timestamp"] - user_chunks[0]["timestamp"]
        samples_in_chunk = len(user_chunks[0]["data"]) // BYTES_PER_SAMPLE
        if time_diff > 0:
            detected_rate = samples_in_chunk / time_diff
            # Round to nearest common sample rate
            if detected_rate > 40000:
                user_sample_rate = 48000
            elif detected_rate > 20000:
                user_sample_rate = 24000
            else:
                user_sample_rate = 16000
            logger.info(f"Detected user audio sample rate: {detected_rate:.0f}Hz, using {user_sample_rate}Hz")
    
    # Process and prepare all chunks with their timestamps
    # We need to interleave user and agent chunks based on when they actually occurred
    all_chunks = []
    
    # Process user chunks (resample if needed)
    for chunk in user_chunks:
        chunk_data = chunk["data"]
        chunk_samples_original = len(chunk_data) // BYTES_PER_SAMPLE
        
        # Resample if needed
        if user_sample_rate != SAMPLE_RATE:
            resample_ratio = SAMPLE_RATE / user_sample_rate
            chunk_samples_resampled = int(chunk_samples_original * resample_ratio)
            
            # Convert to samples, resample, convert back
            samples = struct.unpack(f'<{chunk_samples_original}h', chunk_data)
            resampled_samples = []
            for j in range(chunk_samples_resampled):
                src_idx = j / resample_ratio
                idx_low = int(src_idx)
                idx_high = min(idx_low + 1, chunk_samples_original - 1)
                frac = src_idx - idx_low
                if idx_low < chunk_samples_original:
                    interpolated = samples[idx_low] * (1 - frac) + samples[idx_high] * frac
                    resampled_samples.append(int(interpolated))
            
            chunk_data = struct.pack(f'<{chunk_samples_resampled}h', *resampled_samples)
            chunk_samples = chunk_samples_resampled
        else:
            chunk_samples = chunk_samples_original
        
        all_chunks.append({
            "timestamp": chunk["timestamp"],
            "type": "user",
            "data": chunk_data,
            "samples": chunk_samples
        })
    
    # Process agent chunks (already at 24kHz, no resampling needed)
    for chunk in agent_chunks:
        chunk_data = chunk["data"]
        chunk_samples = len(chunk_data) // BYTES_PER_SAMPLE
        
        all_chunks.append({
            "timestamp": chunk["timestamp"],
            "type": "agent",
            "data": chunk_data,
            "samples": chunk_samples
        })
    
    # Sort all chunks by timestamp to get chronological order
    all_chunks.sort(key=lambda x: x["timestamp"])
    
    # Now place chunks sequentially, maintaining continuity within each stream
    # Track cumulative position for each stream type
    user_cumulative = None
    agent_cumulative = None
    
    chunk_placements = []
    
    for chunk in all_chunks:
        chunk_timestamp = chunk["timestamp"]
        chunk_offset_seconds = chunk_timestamp - session_start_time
        chunk_start_sample = max(0, int(chunk_offset_seconds * SAMPLE_RATE))
        
        if chunk["type"] == "user":
            # For user audio, maintain continuity within user stream
            if user_cumulative is None:
                user_cumulative = chunk_start_sample
            
            # Ensure no gaps - if there's a gap, start from where previous user chunk ended
            if chunk_start_sample < user_cumulative:
                chunk_start_sample = user_cumulative
            
            chunk_placements.append({
                "start_sample": chunk_start_sample,
                "data": chunk["data"],
                "samples": chunk["samples"],
                "type": "user"
            })
            
            user_cumulative = chunk_start_sample + chunk["samples"]
        else:  # agent
            # For agent audio, maintain continuity within agent stream
            if agent_cumulative is None:
                agent_cumulative = chunk_start_sample
            
            # Ensure no gaps - if there's a gap, start from where previous agent chunk ended
            if chunk_start_sample < agent_cumulative:
                chunk_start_sample = agent_cumulative
            
            chunk_placements.append({
                "start_sample": chunk_start_sample,
                "data": chunk["data"],
                "samples": chunk["samples"],
                "type": "agent"
            })
            
            agent_cumulative = chunk_start_sample + chunk["samples"]
    
    # Calculate total duration needed
    total_samples = 0
    if chunk_placements:
        for placement in chunk_placements:
            total_samples = max(total_samples, placement["start_sample"] + placement["samples"])
    
    if total_samples == 0:
        logger.warning(f"No audio samples to export for session {session_id}")
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(b'')
        return wav_buffer.getvalue()
    
    # Initialize output buffer with zeros
    output_buffer = bytearray(total_samples * BYTES_PER_SAMPLE)
    
    # Place all chunks in chronological order
    for placement in chunk_placements:
        chunk_data = placement["data"]
        chunk_start = placement["start_sample"]
        chunk_samples = placement["samples"]
        
        for i in range(chunk_samples):
            sample_offset = chunk_start + i
            if 0 <= sample_offset < total_samples:
                # Read PCM16 sample from chunk
                sample_value = struct.unpack('<h', chunk_data[i*2:(i+1)*2])[0]
                # Get current value from buffer
                current_offset = sample_offset * BYTES_PER_SAMPLE
                current_value = struct.unpack('<h', output_buffer[current_offset:current_offset+2])[0]
                # Mix (add) and clamp to prevent clipping
                mixed_value = max(-32768, min(32767, current_value + sample_value))
                # Write back to buffer
                struct.pack_into('<h', output_buffer, current_offset, mixed_value)
    
    # Create WAV file
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit = 2 bytes
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(bytes(output_buffer))
    
    duration_seconds = total_samples / SAMPLE_RATE
    user_chunk_count = len([c for c in chunk_placements if c["type"] == "user"])
    agent_chunk_count = len([c for c in chunk_placements if c["type"] == "agent"])
    logger.info(f"Combined audio: {user_chunk_count} user chunks, {agent_chunk_count} agent chunks, "
                f"total {total_samples} samples ({duration_seconds:.2f}s), sorted chronologically")
    
    return wav_buffer.getvalue()


class SaveAudioRequest(BaseModel):
    session_id: str


@app.post("/audio/save")
async def save_audio(request: SaveAudioRequest, token: Optional[str] = Query(None)):
    """
    Combine and save audio recording for a session.
    
    Args:
        request: Contains session_id.
        token: Session token from query parameter.
    
    Returns:
        dict: Contains file_path where audio was saved.
    """
    session = validate_session_token(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    
    try:
        # Combine audio buffers and export as WAV
        wav_data = combine_and_export_audio(token, request.session_id)
        
        # Import here to avoid circular imports
        from src.voice_screening_ui.utils.save_voice_recording import save_voice_recording
        
        # Save to disk
        file_path = save_voice_recording(wav_data, request.session_id)
        
        # Clear audio buffers (optional, to free memory)
        sessions[token]["user_audio_chunks"] = []
        sessions[token]["agent_audio_chunks"] = []
        
        logger.info(f"Audio saved for session {request.session_id}: {file_path}")
        
        return {"file_path": file_path}
    except Exception as e:
        logger.error(f"Error saving audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save audio: {str(e)}")


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

