"""
FastAPI server for handling Twilio webhooks and voice screening calls.
"""
import os
import json
import base64
from typing import Optional
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from twilio.twiml.voice_response import VoiceResponse
from twilio.request_validator import RequestValidator
from dotenv import load_dotenv

from src.agents.voice_screening.agent import VoiceScreeningAgent
from src.agents.voice_screening.utils.twilio_client import generate_twiml_say
from src.voice_screening_ui.realtime_handler import (
    get_handler,
    register_handler,
    remove_handler
)
from src.core.configs.agent import AgentConfig
from src.core.configs.model import ModelConfig

load_dotenv()

app = FastAPI(title="Voice Screening API")

# Store active calls: call_sid -> candidate_id
_active_calls: dict[str, str] = {}

# Initialize voice agent (will be configured properly in production)
_voice_agent: Optional[VoiceScreeningAgent] = None


def get_voice_agent() -> VoiceScreeningAgent:
    """Get or create the voice screening agent."""
    global _voice_agent
    if _voice_agent is None:
        model_config = ModelConfig(
            provider="openai",
            model_name="gpt-4o",
            temperature=0.0
        )
        agent_config = AgentConfig(
            name="voice_screening",
            description="Conducts voice screening interviews",
            model_config=model_config,
            system_prompt="You are a friendly HR assistant conducting a phone screening interview."
        )
        _voice_agent = VoiceScreeningAgent(agent_config)
    return _voice_agent


@app.post("/voice/webhook")
async def twilio_webhook(request: Request):
    """
    Handle Twilio status callbacks and initial call setup.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")
    
    if not call_sid:
        return PlainTextResponse("Missing CallSid", status_code=400)
    
    # Handle different call statuses
    if call_status == "ringing" or call_status == "in-progress":
        # Call is starting - set up Media Stream
        media_url = f"{os.getenv('VOICE_SCREENING_WEBHOOK_URL')}/voice/media"
        
        response = VoiceResponse()
        response.start().stream(url=media_url)
        response.say(
            "Hello! Thank you for calling. We'll begin the voice screening interview shortly.",
            voice='alice'
        )
        
        return PlainTextResponse(str(response), media_type="application/xml")
    
    elif call_status == "completed":
        # Call ended - trigger analysis
        candidate_id = _active_calls.get(call_sid)
        if candidate_id:
            # Trigger post-call analysis (this would be done asynchronously)
            # For now, we'll just clean up
            remove_handler(call_sid)
            if call_sid in _active_calls:
                del _active_calls[call_sid]
        
        return PlainTextResponse("OK")
    
    return PlainTextResponse("OK")


@app.post("/voice/media")
async def twilio_media_stream(request: Request):
    """
    Handle Twilio Media Streams webhook for real-time audio.
    """
    form_data = await request.form()
    call_sid = form_data.get("callSid")
    event = form_data.get("event")
    
    if not call_sid:
        return PlainTextResponse("Missing callSid", status_code=400)
    
    if event == "start":
        # Media stream started - initialize handler
        candidate_id = _active_calls.get(call_sid, "unknown")
        handler = register_handler(call_sid, candidate_id)
        await handler.connect()
        
        return PlainTextResponse("OK")
    
    elif event == "media":
        # Audio data received
        payload = form_data.get("payload")
        if payload:
            # Decode base64 audio
            audio_bytes = base64.b64decode(payload)
            
            handler = get_handler(call_sid)
            if handler:
                await handler.send_audio_chunk(audio_bytes)
                await handler.commit_audio()
        
        return PlainTextResponse("OK")
    
    elif event == "stop":
        # Media stream ended
        handler = get_handler(call_sid)
        if handler:
            # Get transcript and trigger analysis
            transcript = handler.get_transcript()
            await handler.close()
            remove_handler(call_sid)
            
            # TODO: Trigger agent's analyze_call node with transcript
        
        return PlainTextResponse("OK")
    
    return PlainTextResponse("OK")


@app.post("/voice/start")
async def start_voice_call(request: Request):
    """
    Internal endpoint to initiate a voice screening call.
    Called by the voice agent.
    
    Expects JSON body with:
    - candidate_id: UUID of the candidate
    - phone_number: Phone number in E.164 format
    """
    data = await request.json()
    candidate_id = data.get("candidate_id")
    phone_number = data.get("phone_number")
    
    if not candidate_id or not phone_number:
        return {"error": "Missing candidate_id or phone_number"}, 400
    
    agent = get_voice_agent()
    call_sid = agent.start_voice_screening(candidate_id, phone_number)
    
    # Store mapping for webhook handling
    _active_calls[call_sid] = candidate_id
    
    return {"call_sid": call_sid, "status": "initiated"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

