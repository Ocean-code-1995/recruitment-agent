"""Register a new candidate in the database."""

from sqlalchemy.exc import IntegrityError

from src.database.candidates.client import SessionLocal
from src.database.candidates.models import Candidate
from src.state.candidate import CandidateStatus


def register_candidate(
    full_name: str,
    email: str,
    phone: str,
    cv_path: str
) -> bool:
    """
    Register a new candidate in the database.
    
    Args:
        full_name: Candidate's full name.
        email: Candidate's email address (unique).
        phone: Candidate's phone number.
        cv_path: Path to the uploaded CV file.
    
    Returns:
        True if successful, False if candidate already exists.
    """
    with SessionLocal() as session:
        candidate = Candidate(
            full_name=full_name,
            email=email,
            phone_number=phone,
            cv_file_path=cv_path,
            status=CandidateStatus.applied,
        )
        session.add(candidate)
        try:
            session.commit()
            print(f"✅ Candidate '{full_name}' registered successfully.")
            return True
        except IntegrityError:
            session.rollback()
            print(f"⚠️ Candidate with email '{email}' already exists.")
            return False

