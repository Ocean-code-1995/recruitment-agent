"""
Supervisor Agent for HR Recruitment Workflow

Uses ReAct agent pattern with LangChain's create_agent for autonomous 
recruitment decision-making. The agent evaluates candidates and makes
hiring recommendations using available tools.
"""

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

from src.agents.cv_screening.screener import evaluate_cv


# ============================================================================
# TOOLS FOR THE SUPERVISOR AGENT
# ============================================================================

@tool
def screen_cv(cv_text: str, jd_text: str = "") -> dict:
    """
    Screen a candidate's CV against a job description.
    
    Args:
        cv_text: The candidate's CV content as text
        jd_text: The job description to match against (optional)
    
    Returns:
        Dictionary with CV screening results including fit scores and feedback
    """
    if not cv_text:
        return {"error": "CV text is required"}
    
    # Use job description if provided, otherwise use a generic evaluation
    job_description = jd_text or "Evaluate candidate's qualifications and experience"
    
    try:
        result = evaluate_cv(cv_text, job_description)
        return {
            "overall_fit_score": result.overall_fit_score,
            "skills_match_score": result.skills_match_score,
            "experience_match_score": result.experience_match_score,
            "education_match_score": result.education_match_score,
            "llm_feedback": result.llm_feedback,
            "status": "success"
        }
    except Exception as e:
        return {"error": f"CV screening failed: {str(e)}", "status": "error"}


@tool
def voice_screening(candidate_id: str, candidate_email: str) -> dict:
    """
    Schedule or perform voice screening for a candidate.
    TODO: Not yet implemented - returns placeholder.
    
    Args:
        candidate_id: The candidate's ID
        candidate_email: The candidate's email
    
    Returns:
        Placeholder response
    """
    return {
        "status": "not_implemented",
        "message": "Voice screening agent not yet implemented",
        "candidate_id": candidate_id
    }


@tool
def schedule_hr_interview(candidate_id: str, candidate_email: str) -> dict:
    """
    Schedule an HR interview with the candidate.
    TODO: Not yet implemented - returns placeholder.
    
    Args:
        candidate_id: The candidate's ID
        candidate_email: The candidate's email
    
    Returns:
        Placeholder response
    """
    return {
        "status": "not_implemented",
        "message": "HR scheduling agent not yet implemented",
        "candidate_id": candidate_id
    }


# ============================================================================
# CREATE THE SUPERVISOR AGENT
# ============================================================================

tools = [
    screen_cv,
    voice_screening,
    schedule_hr_interview,
]

# Initialize the LLM
model = ChatOpenAI(model="gpt-4o", temperature=0.7)

# Create the ReAct agent
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt="""You are an HR Recruitment Supervisor Agent. Your role is to evaluate candidates and make hiring recommendations.

You have the following tools available:
1. screen_cv - Evaluate a candidate's CV against a job description
2. voice_screening - TODO: Schedule voice screening (not yet implemented)
3. schedule_hr_interview - TODO: Schedule HR interview (not yet implemented)

Your process:
1. Start by screening the candidate's CV using the screen_cv tool
2. Based on CV results, decide if you need additional evaluation
3. Provide a clear recommendation: HIRE, REJECT, or HOLD_FOR_REVIEW
4. Explain your reasoning based on the evaluation results

Always use the available tools to gather information before making recommendations.
Be thorough but efficient in your evaluation."""
)
