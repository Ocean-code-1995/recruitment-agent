from datetime import datetime
from typing import Optional
from src.database.candidates.client import SessionLocal
from src.database.candidates.models import Candidate, VoiceScreeningResult
from src.state.candidate import CandidateStatus
from src.agents.voice_screening.schemas.output_schema import VoiceScreeningOutput


def write_voice_results_to_db(
    candidate_id: str,
    call_sid: str,
    transcript_text: str,
    result: VoiceScreeningOutput,
    audio_url: Optional[str] = None
) -> None:
    """
    Store the voice screening results in the database and update candidate status.

    Args:
        candidate_id (str): UUID of the candidate.
        call_sid (str): Twilio Call SID.
        transcript_text (str): Full conversation transcript.
        result (VoiceScreeningOutput): The screening results from the LLM.
        audio_url (str, optional): URL to the call recording if available.
    
    Returns:
        None
    """
    import uuid
    
    with SessionLocal() as session:
        candidate = session.query(Candidate).filter_by(id=uuid.UUID(candidate_id)).first()

        if not candidate:
            print(f"⚠️ No candidate found with ID: {candidate_id}")
            return

        # Create new voice screening result entry
        screening_entry = VoiceScreeningResult(
            candidate_id=candidate.id,
            call_sid=call_sid,
            transcript_text=transcript_text,
            sentiment_score=result.sentiment_score,
            confidence_score=result.confidence_score,
            communication_score=result.communication_score,
            llm_summary=result.llm_summary,
            llm_judgment_json=result.llm_judgment_json,
            audio_url=audio_url,
            timestamp=datetime.utcnow(),
        )

        # Add and commit
        session.add(screening_entry)
        candidate.status = CandidateStatus.voice_done
        candidate.updated_at = datetime.utcnow()
        session.commit()

        print(f"✅ Voice screening results saved and status updated for candidate {candidate_id}")

