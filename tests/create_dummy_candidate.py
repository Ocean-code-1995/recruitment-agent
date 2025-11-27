import uuid
from datetime import datetime
from src.database.candidates.client import SessionLocal
from src.database.candidates.models import Candidate, CVScreeningResult
from src.state.candidate import CandidateStatus

def create_dummy_candidate():
    with SessionLocal() as db:
        # Check if dummy candidate exists
        candidate = db.query(Candidate).filter(Candidate.email == "test_candidate@example.com").first()
        
        if not candidate:
            candidate_id = uuid.uuid4()
            candidate = Candidate(
                id=candidate_id,
                full_name="Test Candidate",
                email="test_candidate@example.com",
                phone_number="+1234567890",
                status=CandidateStatus.applied,
                created_at=datetime.utcnow()
            )
            db.add(candidate)
            
            # Add dummy CV screening result so we have a job title
            cv_result = CVScreeningResult(
                id=uuid.uuid4(),
                candidate_id=candidate_id,
                job_title="Software Engineer",
                skills_match_score=85.0,
                experience_match_score=90.0,
                education_match_score=80.0,
                overall_fit_score=85.0,
                llm_feedback="Strong candidate",
                timestamp=datetime.utcnow()
            )
            db.add(cv_result)
            
            db.commit()
            print(f"✅ Created dummy candidate with ID: {candidate_id}")
            print(f"Email: test_candidate@example.com")
        else:
            print(f"ℹ️ Dummy candidate already exists with ID: {candidate.id}")
            print(f"Email: {candidate.email}")
            
        return str(candidate.id)

if __name__ == "__main__":
    create_dummy_candidate()
