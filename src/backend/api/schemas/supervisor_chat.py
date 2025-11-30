from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message to send to the supervisor agent")
    thread_id: Optional[str] = Field(
        default=None,
        description="Thread ID for conversation continuity. If not provided, a new thread is created."
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="Agent's response message")
    thread_id: str = Field(..., description="Thread ID for conversation continuity")
    token_count: int = Field(..., description="Current token count in context window")


class NewChatResponse(BaseModel):
    """Response model for creating a new chat session."""
    thread_id: str = Field(..., description="New thread ID for the conversation")
    message: str = Field(..., description="Welcome message")