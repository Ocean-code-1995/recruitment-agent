"""
List candidates in the database.

Run standalone:
>>> POSTGRES_HOST=localhost POSTGRES_PORT=5433 python scripts/db/list_candidates.py
"""

from sqlalchemy.exc import ProgrammingError

# Ensure project root is in path
import scripts.db  # noqa: F401

from src.database.candidates.client import SessionLocal
from src.database.candidates.models import Candidate


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
                print(f" - {c.full_name} | {c.email} | Status: {c.status}")
        
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

