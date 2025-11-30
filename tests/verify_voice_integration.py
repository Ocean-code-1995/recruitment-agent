import sys
import os
from sqlalchemy import select, desc
from uuid import uuid4
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.backend.database.candidates.models import Candidate, CVScreeningResult, Base
from src.backend.database.candidates.client import SessionLocal, engine
from src.backend.agents.voice_screening.utils.questions import get_screening_questions

def verify_integration():
    print("Verifying integration...")
    
    # Create tables if not exist (for test)
    Base.metadata.create_all(bind=engine)
    
    # Create a dummy candidate
    candidate_id = uuid4()
    candidate = Candidate(
        id=candidate_id,
        full_name="Test Candidate",
        email=f"test_{candidate_id}@example.com",
        status="applied"
    )
    
    # Create a dummy CV result
    cv_result = CVScreeningResult(
        candidate_id=candidate_id,
        job_title="Senior Python Engineer",
        skills_match_score=0.9,
        experience_match_score=0.8,
        education_match_score=0.9,
        overall_fit_score=0.85,
        llm_feedback="Good fit",
        reasoning_trace={}
    )
    
    try:
        with SessionLocal() as db:
            db.add(candidate)
            db.add(cv_result)
            db.commit()
            print(f"Created test candidate: {candidate_id}")
            
            # Simulate the logic in proxy.py
            fetched_candidate = db.execute(
                select(Candidate).where(Candidate.id == candidate_id)
            ).scalar_one_or_none()
            
            if fetched_candidate:
                print(f"Fetched candidate: {fetched_candidate.full_name}")
                
                fetched_cv_result = db.execute(
                    select(CVScreeningResult)
                    .where(CVScreeningResult.candidate_id == candidate_id)
                    .order_by(desc(CVScreeningResult.timestamp))
                    .limit(1)
                ).scalar_one_or_none()
                
                job_title = fetched_cv_result.job_title if fetched_cv_result else "the position"
                print(f"Fetched job title: {job_title}")
                
                questions = get_screening_questions(job_title)
                print(f"Generated {len(questions)} questions")
                
                instructions = (
                    f"You are a friendly HR assistant conducting a phone screening interview with {fetched_candidate.full_name} "
                    f"for the position of {job_title}. "
                    f"Greet the candidate warmly by name. "
                    f"Your goal is to ask the following questions to assess their fit:\n\n"
                )
                
                for i, q in enumerate(questions, 1):
                    instructions += f"{i}. {q}\n"
                    
                instructions += (
                    "\nAsk one question at a time. Wait for their response before moving to the next. "
                    "Be professional but conversational. If they ask clarifying questions, answer them briefly."
                )
                
                print("\nGenerated Instructions:")
                print("-" * 40)
                print(instructions)
                print("-" * 40)
                
                # Clean up
                db.delete(cv_result)
                db.delete(candidate)
                db.commit()
                print("Cleaned up test data")
                
    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_integration()
