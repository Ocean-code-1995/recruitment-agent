import uuid
from datetime import datetime, timedelta
from src.backend.database.candidates.client import SessionLocal
from src.backend.database.candidates.models import Candidate, CVScreeningResult, VoiceScreeningResult
from src.backend.state.candidate import CandidateStatus

def setup_demo_state():
    print("🚀 Setting up demo state...")
    session = SessionLocal()
    
    # 1. Cleanup existing Jane Doe
    existing = session.query(Candidate).filter(Candidate.email == "jane.doe@example.com").first()
    if existing:
        print(f"Creating clean slate: Deleting existing candidate {existing.full_name}...")
        session.delete(existing)
        session.commit()

    # 2. Create Candidate: Jane Doe (Advanced Stage)
    candidate_id = uuid.uuid4()
    jane = Candidate(
        id=candidate_id,
        full_name="Jane Doe",
        email="jane.doe@example.com",
        phone_number="+15550101",
        status=CandidateStatus.voice_passed,  # Ready for final interview
        created_at=datetime.utcnow() - timedelta(days=2)
    )
    session.add(jane)

    # 3. Add CV Screening Result (She passed this previously)
    cv_result = CVScreeningResult(
        candidate_id=candidate_id,
        job_title="Senior Product Manager",
        skills_match_score=92.0,
        experience_match_score=88.0,
        education_match_score=95.0,
        overall_fit_score=91.0,
        llm_feedback="Candidate demonstrates exceptional strategic thinking and relevant experience in SaaS product management. Strong leadership background.",
        timestamp=datetime.utcnow() - timedelta(days=2)
    )
    session.add(cv_result)

    # 4. Add Voice Screening Result (She just completed this)
    voice_result = VoiceScreeningResult(
        candidate_id=candidate_id,
        transcript_text="I have over 5 years of experience leading agile teams... I believe communication is key to product success... In my last role, I increased user retention by 20%...",
        sentiment_score=0.8,
        confidence_score=0.9,
        communication_score=9.5,
        llm_summary="Candidate spoke clearly and confidently. Provided concrete examples of past success (20% retention increase). demonstrated strong understanding of agile methodologies.",
        llm_judgment_json={"decision": "pass", "reasoning": "High confidence and clear articulation of value."},
        timestamp=datetime.utcnow() - timedelta(hours=1)
    )
    session.add(voice_result)

    session.commit()
    print(f"✅ Successfully created candidate: Jane Doe (ID: {candidate_id})")
    print("   - Status: voice_passed")
    print("   - Has CV Result: Yes")
    print("   - Has Voice Result: Yes")
    print("\nReady for demo video recording! 🎥")

if __name__ == "__main__":
    setup_demo_state()

