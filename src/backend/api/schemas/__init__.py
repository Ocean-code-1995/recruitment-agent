"""API schemas."""

from .cv_upload import SubmitResponse
from .supervisor_chat import ChatRequest, ChatResponse, NewChatResponse
from .database import (
    TableName,
    QueryRequest,
    QueryResponse,
    SingleRecordResponse,
    CandidateResponse,
    CVScreeningResponse,
    VoiceScreeningResponse,
    InterviewSchedulingResponse,
    FinalDecisionResponse,
)

__all__ = [
    "SubmitResponse",
    "ChatRequest",
    "ChatResponse",
    "NewChatResponse",
    # Database schemas
    "TableName",
    "QueryRequest",
    "QueryResponse",
    "SingleRecordResponse",
    "CandidateResponse",
    "CVScreeningResponse",
    "VoiceScreeningResponse",
    "InterviewSchedulingResponse",
    "FinalDecisionResponse",
]

