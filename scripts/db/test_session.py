"""
Test database session and query execution.

Run standalone:
>>> POSTGRES_HOST=localhost POSTGRES_PORT=5433 python scripts/db/test_session.py
"""

from sqlalchemy import text

# Ensure project root is in path
import scripts.db  # noqa: F401

from src.database.candidates.client import SessionLocal


def test_session_query() -> bool:
    """
    Test session creation and basic query execution.
    
    Returns:
        True if session works, False otherwise.
    """
    print("--- Testing Session Query ---")
    session = SessionLocal()
    try:
        result = session.execute(text("SELECT now()"))
        print(f"✅ Session execute successful: {result.fetchone()[0]}")
        return True
        
    except Exception as e:
        print("\n❌ Session Query FAILED")
        print(f"Error: {e}")
        return False
    finally:
        session.close()


if __name__ == "__main__":
    test_session_query()

