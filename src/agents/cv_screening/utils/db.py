from datetime import datetime
from src.database.candidates.client import SessionLocal
from src.database.candidates.models import Candidate, CVScreeningResult
from src.state.candidate import CandidateStatus
from src.agents.cv_screening.schemas.output_schema import CVScreeningOutput


def get_candidate_by_name(full_name: str):
    """
    Retrieve a candidate by their full name.
    
    Args:
        full_name (str): The full name of the candidate.
        
    Returns:
        Candidate: The candidate object or None if not found.
        (Note: attributes are detached after session close, so access them immediately)
    """
    with SessionLocal() as session:
        candidate = session.query(Candidate).filter(Candidate.full_name == full_name).first()
        if candidate:
            # Refresh/expunge to make it usable after session closes if needed, 
            # or just return the data we need. Returning the dict of values is safer.
            return {
                "id": candidate.id,
                "full_name": candidate.full_name,
                "email": candidate.email,
                "parsed_cv_file_path": candidate.parsed_cv_file_path,
                "status": candidate.status
            }
        return None


def update_application_status(candidate_email: str, status: CandidateStatus) -> None:
    """
    Update the status of a candidate application.
    
    Args:
        candidate_email (str): The email of the candidate.
        status (CandidateStatus): The new status to set.
    """
    with SessionLocal() as session:
        candidate = session.query(Candidate).filter_by(email=candidate_email).first()
        if candidate:
            candidate.status = status
            candidate.updated_at = datetime.utcnow()
            session.commit()
            print(f"✅ Updated status for {candidate_email} to {status.value}")
        else:
            print(f"⚠️ No candidate found with email: {candidate_email}")


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
