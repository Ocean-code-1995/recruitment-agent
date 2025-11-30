"""
List candidates in the database.

Run standalone:
>>> POSTGRES_HOST=localhost POSTGRES_PORT=5433 python scripts/db/list_candidates.py
"""

from sqlalchemy.exc import ProgrammingError

# Ensure project root is in path
import scripts.db  # noqa: F401

from src.backend.database.candidates.client import SessionLocal
from src.backend.database.candidates.models import Candidate


def list_candidates(limit: int = 10) -> bool:
    """
    Check and list existing candidates in the database.
    
    Args:
        limit: Maximum number of candidates to display.
    
    Returns:
        True if query successful, False otherwise.
    """
    print("--- 🧾 Checking Existing Candidates ---")
    session = SessionLocal()
    try:
        count = session.query(Candidate).count()
        print(f"📊 Found {count} candidate(s) in the database.")

        if count == 0:
            print("⚠️ No candidates found.")
        else:
            print(f"\n👀 Listing candidates (up to {limit}):")
            candidates = (
                session.query(Candidate)
                .order_by(Candidate.full_name)
                .limit(limit)
                .all()
            )
            for c in candidates:
                print(f" - ID: {c.id}")
                print(f"   Full Name: {c.full_name}")
                print(f"   Email: {c.email}")
                print(f"   Phone: {c.phone_number}")
                print(f"   CV Path: {c.cv_file_path}")
                print(f"   Parsed CV Path: {c.parsed_cv_file_path}")
                print(f"   Status: {c.status}")
                print(f"   Auth Code: {c.auth_code}")
                print(f"   Created At: {c.created_at}")
                print(f"   Updated At: {c.updated_at}")
                print("-" * 40)
        
        return True

    except ProgrammingError as e:
        print("❌ Table 'candidates' does not exist or schema not initialized.")
        print("ℹ️ Try running your DB initialization script or migrations.")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print("❌ Error during candidate check.")
        print(f"Error: {e}")
        return False
    finally:
        session.close()


if __name__ == "__main__":
    list_candidates()

