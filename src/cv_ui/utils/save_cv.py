import os
import uuid
from typing import BinaryIO

# Default upload directory (can be overridden via env var)
UPLOAD_DIR = os.getenv("CV_UPLOAD_PATH", "src/database/cvs/uploads")


def ensure_upload_dir() -> None:
    """
    Ensure the CV upload directory exists.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_cv(file_obj: BinaryIO, original_filename: str) -> str:
    """
    Save an uploaded CV to the local uploads directory.

    Args:
        file_obj: The file-like object (from Streamlit upload or HTTP request).
        original_filename: The original name of the uploaded file.

    Returns:
        str: The full path where the file was saved.
    """
    ensure_upload_dir()

    # Generate unique filename
    file_id = str(uuid.uuid4())
    _, file_ext = os.path.splitext(original_filename)
    safe_name = f"{file_id}_{os.path.basename(original_filename)}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    # Save binary content
    with open(file_path, "wb") as f:
        f.write(file_obj.read())

    print(f"📂 Saved CV to {file_path}")
    return file_path
