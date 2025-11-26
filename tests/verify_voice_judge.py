import sys
import os
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.database.candidates.models import Candidate, VoiceScreeningResult, CVScreeningResult, Base
from src.database.candidates.client import SessionLocal, engine
from src.agents.voice_screening.judge import evaluate_voice_screening

def verify_voice_judge():
    print("Verifying Voice Screening Judge...")
    
    # Create tables if not exist
    Base.metadata.create_all(bind=engine)
    
    # Create dummy data
    candidate_id = uuid4()
    email = f"test_judge_{candidate_id}@example.com"
    
    try:
        with SessionLocal() as db:
            # 1. Create Candidate
            candidate = Candidate(
                id=candidate_id,
                full_name="Judge Test Candidate",
                email=email,
                status="voice_screened"
            )
            db.add(candidate)
            
            # 2. Create CV Screening Result (for job title context)
            cv_result = CVScreeningResult(
                candidate_id=candidate_id,
                job_title="Senior Python Developer",
                skills_match_score=85.0,
                experience_match_score=90.0,
                education_match_score=80.0,
                overall_fit_score=85.0,
                llm_feedback="Strong candidate.",
                reasoning_trace={}
            )
            db.add(cv_result)
            
            # 3. Create Voice Screening Result (with transcript)
            transcript = (
                "Interviewer: Tell me about your experience with Python.\n"
                "Candidate: I have been using Python for 5 years. I specialize in backend development using Django and FastAPI. "
                "I have also worked with SQLAlchemy and Celery for asynchronous tasks. I am very confident in my ability to build scalable systems.\n"
                "Interviewer: How do you handle testing?\n"
                "Candidate: I believe testing is crucial. I use Pytest for unit and integration tests. I always aim for high code coverage."
            )
            
            # Create dummy audio file
            import wave
            import struct
            
            audio_path = "test_audio.wav"
            with wave.open(audio_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(24000)
                # Generate 1 second of silence
                data = struct.pack('<24000h', *[0]*24000)
                wav_file.writeframes(data)
                
            voice_result = VoiceScreeningResult(
                candidate_id=candidate_id,
                call_sid=f"test_sid_{candidate_id}",
                transcript_text=transcript,
                audio_url=os.path.abspath(audio_path),
                timestamp=datetime.utcnow()
            )
            db.add(voice_result)
            db.commit()
            print(f"Created test candidate: {email} with audio: {audio_path}")
            
        # 4. Run Evaluation
        print("\nRunning evaluation...")
        result_summary = evaluate_voice_screening(str(candidate_id))
        print(result_summary)
        
        # 5. Verify DB Updates
        with SessionLocal() as db:
            updated_candidate = db.query(Candidate).filter_by(id=candidate_id).first()
            updated_voice_result = db.query(VoiceScreeningResult).filter_by(candidate_id=candidate_id).first()
            
            print("\nVerification Results:")
            print(f"Status: {updated_candidate.status}")
            print(f"Proficiency Score: {updated_voice_result.proficiency_score}")
            print(f"Communication Score: {updated_voice_result.communication_score}")
            print(f"LLM Summary: {updated_voice_result.llm_summary}")
            
            if updated_candidate.status in ["voice_passed", "voice_rejected"]:
                print("✅ Candidate status updated correctly.")
            else:
                print("❌ Candidate status NOT updated correctly.")
                
            if updated_voice_result.proficiency_score is not None:
                print("✅ Proficiency score populated.")
            else:
                print("❌ Proficiency score missing.")
                
        # 6. Clean up
        with SessionLocal() as db:
            db.query(Candidate).filter_by(id=candidate_id).delete()
            db.commit()
            print("\nCleaned up test data")
            
        if os.path.exists("test_audio.wav"):
            os.remove("test_audio.wav")
            print("Removed test audio file")
            
    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_voice_judge()
