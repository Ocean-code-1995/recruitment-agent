from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class VoiceScreeningOutput(BaseModel):
    """Structured results from voice screening evaluation."""
    sentiment_score: float = Field(..., ge=0, le=1, description="Overall sentiment score (0=negative, 1=positive)")
    confidence_score: float = Field(..., ge=0, le=1, description="Candidate's confidence level")
    communication_score: float = Field(..., ge=0, le=1, description="Communication clarity and effectiveness")
    proficiency_score: float = Field(..., ge=0, le=1, description="Technical/Role proficiency demonstrated")
    llm_summary: str = Field(..., description="LLM-generated summary of the interview")
    key_traits: List[str] = Field(default_factory=list, description="Key personality/technical traits identified")
    recommendation: str = Field(..., description="Pass/fail or next-step recommendation")

