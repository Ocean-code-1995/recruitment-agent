from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class CVScreeningOutput(BaseModel):
    llm_feedback: str
    skills_match_score: float = Field(..., ge=0, le=1)
    experience_match_score: float = Field(..., ge=0, le=1)
    education_match_score: float = Field(..., ge=0, le=1)
    overall_fit_score: float = Field(..., ge=0, le=1)
