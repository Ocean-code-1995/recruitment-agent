from typing import List

def get_screening_questions(job_title: str) -> List[str]:
    """
    Returns a list of static screening questions based on the job title.
    For now, it returns a generic set of questions, but can be expanded.
    """
    # Generic questions for any role
    base_questions = [
        "Can you briefly walk me through your background and experience?",
        "What motivated you to apply for this position?",
        "What are your salary expectations?",
        "When would you be available to start?",
    ]
    
    # We could add specific questions based on job_title here
    # if "engineer" in job_title.lower():
    #     base_questions.append("Describe a challenging technical problem you solved.")
        
    return base_questions
