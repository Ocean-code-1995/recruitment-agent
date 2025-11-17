from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class CVScreeningOutput(BaseModel):
    skills_match_score: float = Field(..., ge=0, le=1)
    experience_match_score: float = Field(..., ge=0, le=1)
    education_match_score: float = Field(..., ge=0, le=1)
    overall_fit_score: float = Field(..., ge=0, le=1)
    llm_feedback: str
    #reasoning_trace: Optional[Dict[str, Any]] = None
