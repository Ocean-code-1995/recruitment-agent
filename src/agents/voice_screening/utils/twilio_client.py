"""
Twilio client utilities for initiating calls and handling webhooks.
"""
import os
from typing import Optional
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse


def get_twilio_client() -> Client:
    """
    Initialize and return a Twilio client using environment variables.
    
    Returns:
        Client: Twilio client instance
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    if not account_sid or not auth_token:
        raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in environment")
    
    return Client(account_sid, auth_token)


def initiate_outbound_call(
    to_phone: str,
    from_phone: str,
    webhook_url: str,
    media_stream_url: Optional[str] = None
) -> str:
    """
    Initiate an outbound call via Twilio.
    
    Args:
        to_phone (str): Phone number to call (E.164 format)
        from_phone (str): Twilio phone number to call from
        webhook_url (str): URL for Twilio status callbacks
        media_stream_url (str, optional): URL for Media Streams webhook
        
    Returns:
        str: Twilio Call SID
    """
    client = get_twilio_client()
    
    # Build TwiML URL that will be used when call connects
    # This will be handled by FastAPI /voice/webhook endpoint
    call = client.calls.create(
        to=to_phone,
        from_=from_phone,
        url=webhook_url,  # Twilio will POST to this URL when call connects
        status_callback=webhook_url,  # Status updates also go here
        status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
        record=False,  # We'll handle recording via Media Streams if needed
    )
    
    return call.sid


def generate_twiml_for_call(media_stream_url: Optional[str] = None) -> str:
    """
    Generate TwiML response for incoming call.
    
    Args:
        media_stream_url (str, optional): URL for Media Streams webhook
        
    Returns:
        str: TwiML XML string
    """
    response = VoiceResponse()
    
    if media_stream_url:
        # Start Media Stream to capture audio
        response.start().stream(url=media_stream_url)
    
    # Greeting message
    response.say(
        "Hello! Thank you for calling. We'll begin the voice screening shortly.",
        voice='alice'
    )
    
    return str(response)


def generate_twiml_say(text: str, voice: str = 'alice') -> str:
    """
    Generate TwiML <Say> instruction for speaking text.
    
    Args:
        text (str): Text to speak
        voice (str): Twilio voice name (default: 'alice')
        
    Returns:
        str: TwiML XML string
    """
    response = VoiceResponse()
    response.say(text, voice=voice)
    return str(response)

