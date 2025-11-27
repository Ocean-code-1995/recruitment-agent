"""Evaluate CV screening decision based on score threshold."""

from datetime import datetime

from src.database.candidates.client import SessionLocal
from src.database.candidates.models import Candidate, CVScreeningResult
from src.state.candidate import CandidateStatus


def evaluate_cv_screening_decision(
    candidate_full_name: str, 
    min_overall_score: float = 7.0
) -> str:
    """
    Decides if a candidate passes CV screening based on a score threshold.
    Updates the candidate status to 'cv_passed' or 'cv_rejected'.

    Args:
        candidate_full_name: The candidate's full name.
        min_overall_score: Minimum score required to pass (default 7.0).

    Returns:
        Outcome message.
    """
    with SessionLocal() as session:
        candidate = session.query(Candidate).filter(
            Candidate.full_name == candidate_full_name
        ).first()
        
        if not candidate:
            return f"❌ Candidate '{candidate_full_name}' not found."
        
        # Get latest screening result
        latest_result = (
            session.query(CVScreeningResult)
            .filter(CVScreeningResult.candidate_id == candidate.id)
            .order_by(CVScreeningResult.timestamp.desc())
            .first()
        )
        
        if not latest_result:
            return f"❌ No screening results found for '{candidate_full_name}'. Run screening workflow first."
            
        score = latest_result.overall_fit_score
        
        if score >= min_overall_score:
            new_status = CandidateStatus.cv_passed
            decision = "PASSED"
        else:
            new_status = CandidateStatus.cv_rejected
            decision = "REJECTED"
            
        candidate.status = new_status
        candidate.updated_at = datetime.utcnow()
        session.commit()
        
        return f"✅ Decision: {decision} (Score: {score} vs Threshold: {min_overall_score}). Status updated to '{new_status.value}'."

