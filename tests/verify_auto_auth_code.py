import sys
import os
from uuid import uuid4
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.database.candidates.models import Candidate, Base
from src.database.candidates.client import SessionLocal, engine

def verify_auth_code_generation():
    print("Verifying auth code generation...")
    
    # Create tables if not exist
    Base.metadata.create_all(bind=engine)
    
    # Create a dummy candidate WITHOUT specifying auth_code
    candidate_id = uuid4()
    email = f"test_auto_auth_{candidate_id}@example.com"
    candidate = Candidate(
        id=candidate_id,
        full_name="Auto Auth Test Candidate",
        email=email,
        status="applied"
    )
    
    try:
        # 1. Create candidate
        with SessionLocal() as db:
            db.add(candidate)
            db.commit()
            print(f"Created test candidate: {email}")
            
        # 2. Verify in DB
        with SessionLocal() as db:
            fetched_candidate = db.query(Candidate).filter_by(email=email).first()
            if fetched_candidate and fetched_candidate.auth_code:
                print(f"✅ Auth code automatically generated: {fetched_candidate.auth_code}")
                if len(fetched_candidate.auth_code) == 6 and fetched_candidate.auth_code.isdigit():
                     print("✅ Auth code format is correct (6 digits).")
                else:
                     print(f"❌ Auth code format incorrect: {fetched_candidate.auth_code}")
            else:
                print("❌ Auth code was NOT generated.")
                
        # 3. Clean up
        with SessionLocal() as db:
            db.query(Candidate).filter_by(id=candidate_id).delete()
            db.commit()
            print("Cleaned up test data")
            
    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_auth_code_generation()
