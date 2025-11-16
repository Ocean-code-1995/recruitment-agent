from datetime import datetime
from src.database.candidates.client import SessionLocal
from src.database.candidates.models import Candidate, CVScreeningResult
from src.state.candidate import CandidateStatus
from src.agents.cv_screening.schemas.output_schema import CVScreeningOutput


def write_results_to_db(
    candidate_email: str,
    result: CVScreeningOutput,
    job_title: str = "AI Engineer"
) -> None:
    """
    Store the CV screening results in the database and update candidate status.

    Args:
        candidate_email (str): Email of the candidate.
        result (LLMResultSchema): The screening results from the LLM.
        job_title (str): The job title the candidate applied for.
    
    Returns:
        None
    """
    with SessionLocal() as session:
        candidate = session.query(Candidate).filter_by(email=candidate_email).first()

        if not candidate:
            print(f"⚠️ No candidate found with email: {candidate_email}")
            return

        # Create new CV screening result entry
        screening_entry = CVScreeningResult(
            candidate_id=candidate.id,
            job_title=job_title,
            skills_match_score=result.skills_match_score,
            experience_match_score=result.experience_match_score,
            education_match_score=result.education_match_score,
            overall_fit_score=result.overall_fit_score,
            llm_feedback=result.llm_feedback,
            reasoning_trace=None,
            timestamp=datetime.utcnow(),
        )

        # Add and commit
        session.add(screening_entry)
        candidate.status = CandidateStatus.cv_screened
        candidate.updated_at = datetime.utcnow()
        session.commit()

        print(f"✅ Screening results saved and status updated for {candidate_email}")
