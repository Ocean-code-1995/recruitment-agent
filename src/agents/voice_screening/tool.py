from langchain_core.tools import tool
from src.agents.voice_screening.judge import evaluate_voice_screening

@tool
def voice_screening_judge(candidate_id: str) -> str:
    """
    Evaluates a completed voice screening session for a candidate.
    Analyzes the transcript for tone, confidence, communication, and proficiency.
    Updates the candidate's status to 'voice_passed' or 'voice_rejected'.
    
    Args:
        candidate_id (str): The UUID of the candidate to evaluate.
        
    Returns:
        str: A summary of the evaluation result.
    """
    return evaluate_voice_screening(candidate_id)
