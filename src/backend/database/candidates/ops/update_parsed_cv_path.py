"""Update the parsed CV file path for a candidate."""

from src.backend.database.candidates.client import SessionLocal
from src.backend.database.candidates.models import Candidate


def update_parsed_cv_path(email: str, parsed_path: str) -> None:
    """
    Update the parsed CV file path for a candidate identified by email.

    Args:
        email: Candidate's email (unique identifier).
        parsed_path: Path to the parsed markdown file.
    """
    with SessionLocal() as session:
        candidate = session.query(Candidate).filter_by(email=email).first()
        if not candidate:
            print(f"⚠️ No candidate found with email: {email}")
            return

        candidate.parsed_cv_file_path = parsed_path
        session.commit()
        print(f"✅ Updated parsed CV path for {email}: {parsed_path}")

