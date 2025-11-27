"""
CV file storage operations.

This module handles saving and managing CV files on disk.
"""

import os
from typing import BinaryIO

# Default upload directory (can be overridden via env var)
UPLOAD_DIR = os.getenv("CV_UPLOAD_PATH", "src/database/cvs/uploads")


def ensure_upload_dir() -> None:
    """Ensure the CV upload directory exists."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_cv(file_obj: BinaryIO, original_filename: str, candidate_name: str = "") -> str:
    """
    Save an uploaded CV to the local uploads directory.

    Args:
        file_obj: The file-like object (from Streamlit upload or HTTP request).
        original_filename: The original name of the uploaded file.
        candidate_name: The full name of the candidate (optional).

    Returns:
        The full path where the file was saved.
    """
    ensure_upload_dir()

    # Generate unique filename
    _, file_ext = os.path.splitext(original_filename)
    
    if candidate_name:
        # Sanitize candidate name: remove non-alphanumeric (except space/hyphen), replace spaces with underscores
        safe_candidate_name = "".join(c for c in candidate_name if c.isalnum() or c in (" ", "-", "_"))
        safe_candidate_name = safe_candidate_name.replace(" ", "_")
        safe_name = f"{safe_candidate_name}_CV{file_ext}"
    else:
        safe_name = f"{os.path.basename(original_filename)}"
        
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    # Save binary content
    with open(file_path, "wb") as f:
        f.write(file_obj.read())

    print(f"📂 Saved CV to {file_path}")
    return file_path

