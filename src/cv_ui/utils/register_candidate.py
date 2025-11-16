from src.database.candidates.client import SessionLocal
from src.database.candidates.models import Candidate

def register_candidate(full_name: str, email: str, phone: str, cv_path: str) -> None:
    """
    Register a new candidate in the database.
    """
    with SessionLocal() as session:
        candidate = Candidate(
            full_name=full_name,
            email=email,
            phone_number=phone,
            cv_file_path=cv_path,
            status="applied",
        )
        session.add(candidate)
        session.commit()
        print(f"✅ Candidate '{full_name}' registered successfully.")