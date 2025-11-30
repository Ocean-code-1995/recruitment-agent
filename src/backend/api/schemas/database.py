"""
Database Query Schemas.

Flexible schemas for querying any table in the recruitment database.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


# ==================================================================================
# ENUMS
# ==================================================================================

class TableName(str, Enum):
    """Available tables for querying."""
    candidates = "candidates"
    cv_screening_results = "cv_screening_results"
    voice_screening_results = "voice_screening_results"
    interview_scheduling = "interview_scheduling"
    final_decision = "final_decision"


class SortOrder(str, Enum):
    """Sort order options."""
    asc = "asc"
    desc = "desc"


# ==================================================================================
# REQUEST SCHEMAS
# ==================================================================================

class QueryRequest(BaseModel):
    """Flexible query request for any table."""
    
    table: TableName = Field(..., description="Table to query")
    
    # Filtering
    filters: Optional[dict[str, Any]] = Field(
        default=None,
        description="Key-value filters (e.g., {'email': 'john@example.com', 'status': 'applied'})"
    )
    
    # Field selection
    fields: Optional[list[str]] = Field(
        default=None,
        description="Specific fields to return. If None, returns all fields."
    )
    
    # Include related data
    include_relations: Optional[bool] = Field(
        default=False,
        description="Include related tables (only for candidates table)"
    )
    
    # Pagination
    limit: Optional[int] = Field(default=100, ge=1, le=1000, description="Max records to return")
    offset: Optional[int] = Field(default=0, ge=0, description="Number of records to skip")
    
    # Sorting
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: SortOrder = Field(default=SortOrder.desc, description="Sort order")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "table": "candidates",
                    "filters": {"status": "applied"},
                    "fields": ["id", "full_name", "email", "status"],
                    "limit": 10
                },
                {
                    "table": "cv_screening_results",
                    "filters": {"overall_fit_score": {"$gte": 0.8}},
                    "sort_by": "overall_fit_score",
                    "sort_order": "desc"
                }
            ]
        }
    }


# ==================================================================================
# RESPONSE SCHEMAS
# ==================================================================================

class CandidateResponse(BaseModel):
    """Candidate data response."""
    id: UUID
    full_name: str
    email: str
    phone_number: Optional[str] = None
    cv_file_path: Optional[str] = None
    parsed_cv_file_path: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    
    # Related data (populated when include_relations=True)
    cv_screening_results: Optional[list[dict[str, Any]]] = None
    voice_screening_results: Optional[list[dict[str, Any]]] = None
    interview_scheduling: Optional[list[dict[str, Any]]] = None
    final_decision: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class CVScreeningResponse(BaseModel):
    """CV Screening result response."""
    id: UUID
    candidate_id: UUID
    job_title: Optional[str] = None
    skills_match_score: Optional[float] = None
    experience_match_score: Optional[float] = None
    education_match_score: Optional[float] = None
    overall_fit_score: Optional[float] = None
    llm_feedback: Optional[str] = None
    reasoning_trace: Optional[dict[str, Any]] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class VoiceScreeningResponse(BaseModel):
    """Voice Screening result response."""
    id: UUID
    candidate_id: UUID
    call_sid: Optional[str] = None
    transcript_text: Optional[str] = None
    sentiment_score: Optional[float] = None
    confidence_score: Optional[float] = None
    communication_score: Optional[float] = None
    llm_summary: Optional[str] = None
    llm_judgment_json: Optional[dict[str, Any]] = None
    audio_url: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class InterviewSchedulingResponse(BaseModel):
    """Interview scheduling response."""
    id: UUID
    candidate_id: UUID
    calendar_event_id: Optional[str] = None
    event_summary: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class FinalDecisionResponse(BaseModel):
    """Final decision response."""
    id: UUID
    candidate_id: UUID
    overall_score: Optional[float] = None
    decision: Optional[str] = None
    llm_rationale: Optional[str] = None
    human_notes: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class QueryResponse(BaseModel):
    """Generic query response wrapper."""
    success: bool
    table: str
    total_count: int
    returned_count: int
    offset: int
    data: list[dict[str, Any]]
    message: Optional[str] = None


class SingleRecordResponse(BaseModel):
    """Single record response."""
    success: bool
    table: str
    data: Optional[dict[str, Any]] = None
    message: Optional[str] = None

