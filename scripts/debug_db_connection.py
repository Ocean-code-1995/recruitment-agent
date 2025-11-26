"""
Run as follows:
>>> POSTGRES_HOST=localhost POSTGRES_PORT=5433 python scripts/debug_db_connection.py

This script tests the database connection and the session query.
It also checks if the candidates table exists and if there are any candidates in the database.
"""

import sys
import os
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

# Add project root to sys.path
# This assumes the script is located at scripts/debug_db_connection.py
# We need to go up 1 level to reach the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.append(project_root)

from src.database.candidates.client import SessionLocal, get_engine
from src.database.candidates.models import Candidate



def test_connection():
    print("--- Testing Database Connection ---")
    
    # Print environment info
    print(f"POSTGRES_HOST (env): {os.environ.get('POSTGRES_HOST')}")
    print(f"POSTGRES_PORT (env): {os.environ.get('POSTGRES_PORT')}")
    
    try:
        engine = get_engine()
        print(f"Engine URL: {engine.url}")
        
        # Try to connect
        with engine.connect() as connection:
            print("✅ Connection successful!")
            result = connection.execute(text("SELECT 1"))
            print(f"✅ SELECT 1 result: {result.fetchone()}")
            
    except Exception as e:
        print("\n❌ Connection FAILED")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        traceback.print_exc()



def test_session_query():
    print("\n--- Testing Session Query ---")
    session = SessionLocal()
    try:
        # Try to fetch candidates (even if table is empty, it shouldn't error if connected)
        # We need to import Candidate model to query it, but let's just use text for now or raw session execute
        # to minimalize dependencies on models.py correctness
        result = session.execute(text("SELECT now()"))
        print(f"✅ Session execute successful: {result.fetchone()[0]}")
        
    except Exception as e:
        print("\n❌ Session Query FAILED")
        print(f"Error: {e}")
    finally:
        session.close()


def check_existing_candidates():
    print("\n--- 🧾 Checking Existing Candidates ---")
    session = SessionLocal()
    try:
        count = session.query(Candidate).count()
        print(f"📊 Found {count} candidate(s) in the database.")

        if count == 0:
            print("⚠️ No candidates found.")
        else:
            print("\n👀 Listing candidates (up to 10):")
            candidates = (
                session.query(Candidate)
                .order_by(Candidate.full_name)
                .limit(10)
                .all()
            )
            for c in candidates:
                print(
                    f" - {c.full_name} | {c.email} | Status: {c.status}"
                )

    except ProgrammingError as e:
        print("❌ Table 'candidates' does not exist or schema not initialized.")
        print("ℹ️ Try running your DB initialization script or migrations.")
        print(f"Error: {e}")
    except Exception as e:
        print("❌ Error during candidate check.")
        print(f"Error: {e}")
    finally:
        session.close()




if __name__ == "__main__":
    test_connection()
    test_session_query()
    check_existing_candidates()