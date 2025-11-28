"""
Voice Screener API Router.
Handles voice screening sessions, configuration, and audio/transcript saving.
"""
import logging
import os
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.agents.voice_screening.session_service import (
    get_session_config,
    save_voice_screening_session
)
from src.agents.voice_screening.audio_processor import combine_and_export_audio

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class CreateSessionRequest(BaseModel):
    candidate_id: str


class CreateSessionResponse(BaseModel):
    session_id: str
    candidate_name: str
    job_title: str
    message: str


class SessionConfigResponse(BaseModel):
    candidate_name: str
    job_title: str
    instructions: str
    questions: list[str]
    config: dict


class SaveSessionRequest(BaseModel):
    session_id: str
    candidate_id: str
    transcript_text: str
    proxy_token: str  # Token to retrieve audio chunks from proxy


class SaveSessionResponse(BaseModel):
    audio_file_path: Optional[str]
    message: str


@router.post("/session/create", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """
    Create a new voice screening session for a candidate.
    
    Args:
        request: Contains candidate_id
        
    Returns:
        Session information including session_id
    """
    try:
        import uuid
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Get session config (validates candidate exists)
        config = get_session_config(request.candidate_id)
        
        logger.info(f"Created session {session_id} for candidate {request.candidate_id}")
        
        return CreateSessionResponse(
            session_id=session_id,
            candidate_name=config["candidate_name"],
            job_title=config["job_title"],
            message="Session created successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/session/{session_id}/config", response_model=SessionConfigResponse)
async def get_config(session_id: str, candidate_id: str = Query(...)):
    """
    Get session configuration for a candidate.
    
    Args:
        session_id: Session identifier (for logging)
        candidate_id: Candidate UUID
        
    Returns:
        Session configuration including instructions and questions
    """
    try:
        config = get_session_config(candidate_id)
        
        logger.info(f"Retrieved config for session {session_id}, candidate {candidate_id}")
        
        return SessionConfigResponse(
            candidate_name=config["candidate_name"],
            job_title=config["job_title"],
            instructions=config["instructions"],
            questions=config["questions"],
            config=config["config"]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@router.post("/session/{session_id}/save", response_model=SaveSessionResponse)
async def save_session(session_id: str, request: SaveSessionRequest):
    """
    Save audio recording and transcript for a session.
    
    This endpoint:
    1. Retrieves audio chunks from the proxy using the token
    2. Combines and saves the audio file
    3. Saves transcript and audio path to database
    
    Args:
        session_id: Session identifier (must match request.session_id)
        request: Contains candidate_id, transcript_text, and proxy_token
        
    Returns:
        Audio file path and success message
    """
    if session_id != request.session_id:
        raise HTTPException(status_code=400, detail="Session ID mismatch")
    
    try:
        # Import here to avoid circular dependency
        import requests
        
        # Get proxy URL from environment
        proxy_url = os.getenv("WEBSOCKET_PROXY_URL", "ws://localhost:8000/ws/realtime")
        proxy_base = proxy_url.replace("ws://", "http://").replace("wss://", "https://").replace("/ws/realtime", "")
        
        # Retrieve audio chunks from proxy
        try:
            response = requests.post(
                f"{proxy_base}/audio/retrieve",
                params={"token": request.proxy_token},
                json={"session_id": session_id},
                timeout=30
            )
            response.raise_for_status()
            audio_data = response.json()
            
            import base64
            
            user_chunks = audio_data.get("user_chunks", [])
            # Decode Base64 audio data
            for chunk in user_chunks:
                if isinstance(chunk.get("data"), str):
                    chunk["data"] = base64.b64decode(chunk["data"])
                    
            agent_chunks = audio_data.get("agent_chunks", [])
            # Decode Base64 audio data
            for chunk in agent_chunks:
                if isinstance(chunk.get("data"), str):
                    chunk["data"] = base64.b64decode(chunk["data"])
                    
            session_start_time = audio_data.get("session_start_time")
            
            # Get transcript from proxy if available
            proxy_transcript = audio_data.get("transcript", [])
            transcript_text = request.transcript_text
            
            if proxy_transcript:
                logger.info(f"Using transcript from proxy ({len(proxy_transcript)} entries)")
                transcript_text = "\n".join([
                    f"{entry.get('speaker', 'unknown')}: {entry.get('text', '')}"
                    for entry in proxy_transcript
                ])
            
            if not session_start_time:
                raise ValueError("Session start time not found in proxy response")
                
            logger.info(f"Audio Debug: Retrieved {len(user_chunks)} user chunks and {len(agent_chunks)} agent chunks")
            if user_chunks:
                logger.info(f"Audio Debug: First user chunk size: {len(user_chunks[0].get('data', b''))} bytes")
                
        except Exception as e:
            logger.error(f"Error retrieving audio from proxy: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve audio from proxy: {str(e)}")
        
        # Combine audio chunks
        audio_file_path = None
        if user_chunks or agent_chunks:
            try:
                logger.info("Audio Debug: Combining audio chunks...")
                wav_data = combine_and_export_audio(
                    user_chunks=user_chunks,
                    agent_chunks=agent_chunks,
                    session_start_time=session_start_time,
                    session_id=session_id
                )
                
                logger.info(f"Audio Debug: Generated WAV data size: {len(wav_data)} bytes")
                
                # Save WAV file
                recordings_dir = Path("src/database/voice_recordings")
                recordings_dir.mkdir(parents=True, exist_ok=True)
                audio_file_path = str(recordings_dir / f"{session_id}.wav")
                
                with open(audio_file_path, "wb") as f:
                    f.write(wav_data)
                
                logger.info(f"Saved audio file: {audio_file_path}")
                
                # Verify file exists and size
                if os.path.exists(audio_file_path):
                    size = os.path.getsize(audio_file_path)
                    logger.info(f"Audio Debug: File verified on disk. Size: {size} bytes")
                else:
                    logger.error("Audio Debug: File NOT found on disk after writing!")
                    
            except Exception as e:
                logger.error(f"Error processing audio: {e}", exc_info=True)
                # Continue even if audio fails - we still want to save the transcript
        else:
            logger.warning("Audio Debug: No audio chunks found to process!")
        
        # Save to database
        try:
            save_voice_screening_session(
                candidate_id=request.candidate_id,
                session_id=session_id,
                transcript_text=transcript_text,
                audio_url=audio_file_path
            )
        except ValueError as e:
            # Candidate not found
            logger.warning(f"Failed to save session: {e}")
            raise HTTPException(status_code=404, detail=str(e))
            
        logger.info(f"Saved session {session_id} for candidate {request.candidate_id}")
        
        return SaveSessionResponse(
            audio_file_path=audio_file_path,
            message="Session saved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save session: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "voice-screener"}
