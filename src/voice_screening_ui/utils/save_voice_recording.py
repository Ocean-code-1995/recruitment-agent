import os
import uuid

# Default upload directory (can be overridden via env var)
UPLOAD_DIR = os.getenv("VOICE_RECORDING_PATH", "src/database/voice_recordings")


def ensure_upload_dir() -> None:
    """
    Ensure the voice recording upload directory exists.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_voice_recording(audio_data: bytes, session_id: str) -> str:
    """
    Save a voice recording WAV file to the local uploads directory.

    Args:
        audio_data: The WAV file data as bytes.
        session_id: The session identifier for the interview.

    Returns:
        str: The full path where the file was saved.
    """
    ensure_upload_dir()

    # Generate unique filename
    file_id = str(uuid.uuid4())
    safe_name = f"{file_id}_{session_id}.wav"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    # Save binary content
    with open(file_path, "wb") as f:
        f.write(audio_data)

    print(f"📂 Saved voice recording to {file_path}")
    return file_path

