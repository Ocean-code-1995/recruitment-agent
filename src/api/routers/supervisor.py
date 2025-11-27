"""
Supervisor Agent Router.

Handles chat interactions with the HR Supervisor Agent.
Supports both regular and streaming responses.
"""

import json
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from langchain_core.messages import HumanMessage
from src.api.schemas.supervisor_chat import ChatRequest, ChatResponse, NewChatResponse
from src.context_eng import compacting_supervisor, count_tokens_for_messages


router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the HR Supervisor Agent and receive a response.
    
    The agent can:
    - Query the candidate database
    - Screen CVs
    - Schedule calendar events
    - Send emails via Gmail
    
    Use the returned `thread_id` in subsequent requests to maintain conversation context.
    """
    # Generate or use provided thread_id
    thread_id = request.thread_id or str(uuid.uuid4())[:8]
    
    try:
        # Config for stateful conversation
        config = {"configurable": {"thread_id": thread_id}}
        
        # Invoke the compacting supervisor wrapper
        response = compacting_supervisor.invoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config
        )
        
        # Extract response and calculate tokens
        final_message = response["messages"][-1]
        all_messages = response["messages"]
        token_count = count_tokens_for_messages(all_messages)
        
        return ChatResponse(
            response=final_message.content,
            thread_id=thread_id,
            token_count=token_count,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream a response from the HR Supervisor Agent using Server-Sent Events (SSE).
    
    Yields chunks as SSE events:
    - event: token - A content token from the AI response
    - event: done - Final message with metadata (token_count, thread_id)
    - event: error - Error occurred
    
    Use the returned `thread_id` in subsequent requests to maintain conversation context.
    """
    thread_id = request.thread_id or str(uuid.uuid4())[:8]
    
    def generate():
        try:
            config = {"configurable": {"thread_id": thread_id}}
            
            for chunk in compacting_supervisor.stream(
                {"messages": [HumanMessage(content=request.message)]},
                config=config
            ):
                if chunk["type"] == "token":
                    # SSE format: event type + data
                    yield f"event: token\ndata: {json.dumps({'content': chunk['content']})}\n\n"
                elif chunk["type"] == "done":
                    yield f"event: done\ndata: {json.dumps({'thread_id': thread_id, 'token_count': chunk['token_count']})}\n\n"
                elif chunk["type"] == "error":
                    yield f"event: error\ndata: {json.dumps({'error': chunk['content']})}\n\n"
                    
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.post("/new", response_model=NewChatResponse)
async def new_chat() -> NewChatResponse:
    """
    Create a new chat session with a fresh thread ID.
    
    Returns a new thread_id to use for subsequent chat requests.
    """
    thread_id = str(uuid.uuid4())[:8]
    
    return NewChatResponse(
        thread_id=thread_id,
        message="New chat session created. Use the thread_id for your conversations.",
    )


@router.get("/health")
async def supervisor_health():
    """Health check for supervisor router."""
    return {"status": "healthy", "service": "supervisor"}

