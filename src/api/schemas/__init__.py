"""API schemas."""

from .cv_upload import SubmitResponse
from .supervisor_chat import ChatRequest, ChatResponse, NewChatResponse

__all__ = [
    "SubmitResponse",
    "ChatRequest",
    "ChatResponse",
    "NewChatResponse",
]

