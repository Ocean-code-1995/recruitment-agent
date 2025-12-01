from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class CVScreeningOutput(BaseModel):
    # CRITICAL: Keep llm_feedback as the first field. 
    # This enforces Chain-of-Thought reasoning: the model must explain its assessment
    # BEFORE assigning scores, leading to better calibration. DO NOT REORDER.
    llm_feedback: str
    skills_match_score: float = Field(..., ge=0, le=1)
    experience_match_score: float = Field(..., ge=0, le=1)
    education_match_score: float = Field(..., ge=0, le=1)
    overall_fit_score: float = Field(..., ge=0, le=1)
