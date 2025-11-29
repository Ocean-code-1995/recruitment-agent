"""
Audio processing utilities for voice screening.
Handles audio combining, resampling, and WAV export.
"""
import io
import wave
import struct
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def combine_and_export_audio(
    user_chunks: List[Dict],
    agent_chunks: List[Dict],
    session_start_time: float,
    session_id: str
) -> bytes:
    """
    Combine user and agent audio chunks and export as WAV file.
    
    Audio chunks are continuous streams - we concatenate them in order and mix
    based on when each stream actually started relative to session start.
    
    Args:
        user_chunks: List of dicts with 'timestamp' and 'data' (bytes)
        agent_chunks: List of dicts with 'timestamp' and 'data' (bytes)
        session_start_time: Session start timestamp for relative positioning
        session_id: The session ID for logging.
    
    Returns:
        bytes: WAV file data.
    """
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
    # NOTE: Frontend now resamples to 24kHz before sending, so we can trust it matches.
    user_sample_rate = SAMPLE_RATE  # Always 24kHz
    logger.info(f"Using standard sample rate: {user_sample_rate}Hz")
    
    # Process and prepare all chunks with their timestamps
    # We need to interleave user and agent chunks based on when they actually occurred
    all_chunks = []
    
    # Process user chunks (resample if needed)
    for chunk in user_chunks:
        chunk_data = chunk["data"]
        chunk_samples = len(chunk_data) // BYTES_PER_SAMPLE
        
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
