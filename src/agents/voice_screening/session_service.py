"""
Session service for voice screening.
Handles session configuration, screening questions, and database operations.
"""
import logging
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, desc

from src.database.candidates.client import SessionLocal
from src.database.candidates.models import Candidate, CVScreeningResult, VoiceScreeningResult
from src.state.candidate import CandidateStatus
from src.frontend.streamlit.voice_screening_ui.utils.questions import get_screening_questions

logger = logging.getLogger(__name__)


def get_session_config(candidate_id: str) -> Dict:
    """
    Generate session configuration for a candidate.
    
    Args:
        candidate_id: UUID of the candidate
        
    Returns:
        Dict with session configuration including instructions and questions
    """
    with SessionLocal() as db:
        # Fetch candidate
        candidate = db.execute(
            select(Candidate).where(Candidate.id == UUID(candidate_id))
        ).scalar_one_or_none()
        
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")
        
        # Fetch latest CV screening result for job title
        cv_result = db.execute(
            select(CVScreeningResult)
            .where(CVScreeningResult.candidate_id == UUID(candidate_id))
            .order_by(desc(CVScreeningResult.timestamp))
            .limit(1)
        ).scalar_one_or_none()
        
        job_title = cv_result.job_title if cv_result else "the position"
        questions = get_screening_questions(job_title)
        
        # Build instructions
        instructions = (
            f"You are a friendly HR assistant conducting a phone screening interview with {candidate.full_name} "
            f"for the position of {job_title}. "
            f"Greet the candidate warmly by name. "
            f"Your goal is to ask the following main questions to assess their fit:\n\n"
        )
        
        for i, q in enumerate(questions, 1):
            instructions += f"{i}. {q}\n"
            
        instructions += (
            "\nAsk one question at a time. Wait for their response before moving to the next. "
            "Keep the conversations brief and to the point, ask only one follow-up question per main question. "
            "If they ask clarifying questions, answer them briefly."
        )
        
        return {
            "candidate_name": candidate.full_name,
            "job_title": job_title,
            "instructions": instructions,
            "questions": questions,
            "config": {
                "modalities": ["audio", "text"],
                "instructions": instructions,
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 10000
                }
            }
        }


def save_voice_screening_session(
    candidate_id: str,
    session_id: str,
    transcript_text: str,
    audio_url: Optional[str] = None
) -> None:
    """
    Save voice screening session to database.
    
    Args:
        candidate_id: UUID of the candidate
        session_id: Session identifier
        transcript_text: Full conversation transcript
        audio_url: Path to saved audio file
    """
    with SessionLocal() as db:
        candidate = db.execute(
            select(Candidate).where(Candidate.id == UUID(candidate_id))
        ).scalar_one_or_none()

        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        # Create new voice screening result entry
        screening_entry = VoiceScreeningResult(
            candidate_id=candidate.id,
            call_sid=session_id,  # Using session_id instead of Twilio call_sid
            transcript_text=transcript_text,
            audio_url=audio_url,
            timestamp=datetime.utcnow(),
            # Scores will be filled by judge later
            sentiment_score=None,
            confidence_score=None,
            communication_score=None,
            llm_summary=None,
        )

        # Add and commit
        db.add(screening_entry)
        candidate.status = CandidateStatus.voice_done
        candidate.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"Voice screening session saved for candidate {candidate_id}")
