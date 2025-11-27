from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class CallTranscript(BaseModel):
    """Structure for storing conversation transcript."""
    speaker: str = Field(..., description="Speaker identifier ('agent' or 'candidate')")
    text: str = Field(..., description="Transcribed text")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the utterance occurred")


class ConversationState(BaseModel):
    """State management during an active call."""
    call_sid: str = Field(..., description="Twilio Call SID")
    candidate_id: str = Field(..., description="Candidate UUID")
    transcript: List[CallTranscript] = Field(default_factory=list, description="Full conversation transcript")
    current_question_index: int = Field(default=0, description="Index of current interview question")
    interview_questions: List[str] = Field(default_factory=list, description="List of interview questions")
    is_active: bool = Field(default=True, description="Whether the call is currently active")
    started_at: Optional[datetime] = Field(default=None, description="Call start time")
    ended_at: Optional[datetime] = Field(default=None, description="Call end time")


class VoiceScreeningOutput(BaseModel):
    """Structured results from voice screening evaluation."""
    sentiment_score: float = Field(..., ge=0, le=1, description="Overall sentiment score (0=negative, 1=positive)")
    confidence_score: float = Field(..., ge=0, le=1, description="Candidate's confidence level")
    communication_score: float = Field(..., ge=0, le=1, description="Communication clarity and effectiveness")
    proficiency_score: float = Field(..., ge=0, le=1, description="Candidate's technical proficiency")
    llm_summary: str = Field(..., description="LLM-generated summary of the interview")
    llm_judgment_json: Optional[Dict[str, Any]] = Field(default=None, description="Structured judgment data from LLM")
    key_traits: List[str] = Field(default_factory=list, description="Key personality/technical traits identified")
    recommendation: str = Field(..., description="Pass/fail or next-step recommendation")

