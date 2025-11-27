"""Update the status of a candidate application."""

from datetime import datetime

from src.database.candidates.client import SessionLocal
from src.database.candidates.models import Candidate
from src.state.candidate import CandidateStatus


def update_application_status(candidate_email: str, status: CandidateStatus) -> None:
    """
    Update the status of a candidate application.
    
    Args:
        candidate_email: The email of the candidate.
        status: The new status to set.
    """
    with SessionLocal() as session:
        candidate = session.query(Candidate).filter_by(email=candidate_email).first()
        if candidate:
            candidate.status = status
            candidate.updated_at = datetime.utcnow()
            session.commit()
            print(f"✅ Updated status for {candidate_email} to {status.value}")
        else:
            print(f"⚠️ No candidate found with email: {candidate_email}")

