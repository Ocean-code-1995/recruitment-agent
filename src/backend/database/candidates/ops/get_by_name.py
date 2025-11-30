"""Get a candidate by their full name."""

from typing import Optional, Dict, Any

from src.backend.database.candidates.client import SessionLocal
from src.backend.database.candidates.models import Candidate


def get_candidate_by_name(full_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a candidate by their full name.
    
    Args:
        full_name: The full name of the candidate.
        
    Returns:
        A dictionary with candidate data, or None if not found.
        Contains: id, full_name, email, parsed_cv_file_path, status
    """
    with SessionLocal() as session:
        candidate = session.query(Candidate).filter(
            Candidate.full_name == full_name
        ).first()
        
        if candidate:
            return {
                "id": candidate.id,
                "full_name": candidate.full_name,
                "email": candidate.email,
                "parsed_cv_file_path": candidate.parsed_cv_file_path,
                "status": candidate.status
            }
        return None

