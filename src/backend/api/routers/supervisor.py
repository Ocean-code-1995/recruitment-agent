"""
Supervisor Agent Router.

Handles chat interactions with the HR Supervisor Agent.
Supports both regular and streaming responses.

=============================================================================
ENDPOINTS:
=============================================================================

WITH CONTEXT ENGINEERING (CompactingSupervisor wrapper):
    - POST /chat         : Batch response with automatic context compaction
    - POST /chat/stream  : Streaming with context compaction [HAS ERRORS - TODO FIX]

RAW SUPERVISOR (Direct agent access, no wrapper):
    - POST /raw/chat         : Batch response, direct supervisor agent
    - POST /raw/chat/stream  : Streaming, direct supervisor agent [HAS ERRORS - TODO FIX]

UTILITY:
    - POST /new    : Create new chat session
    - GET  /health : Health check

=============================================================================
NOTE: Both streaming endpoints (/chat/stream and /raw/chat/stream) have 
known issues that need to be fixed. Use batch endpoints (/chat or /raw/chat) 
for reliable operation.
=============================================================================
"""

import json
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from langchain_core.messages import HumanMessage
from src.backend.api.schemas.supervisor_chat import ChatRequest, ChatResponse, NewChatResponse
from src.backend.context_eng import compacting_supervisor, count_tokens_for_messages
from src.backend.agents.supervisor.supervisor_v2 import supervisor_agent


router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the HR Supervisor Agent and receive a response.
    
    Uses CompactingSupervisor wrapper for automatic context management.
    When token limit is exceeded, old messages are compacted/summarized.
    
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
    
    ⚠️ WARNING: This endpoint has known issues and needs to be fixed.
    Use /raw/chat/stream for reliable streaming, or /chat for batch requests.
    
    Uses CompactingSupervisor wrapper for automatic context management.
    
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


# =============================================================================
# RAW SUPERVISOR ENDPOINTS (No CompactingSupervisor wrapper)
# =============================================================================

@router.post("/raw/chat", response_model=ChatResponse)
async def raw_chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the raw HR Supervisor Agent (without context compaction).
    
    This endpoint bypasses the CompactingSupervisor wrapper, giving direct access
    to the underlying supervisor agent. Useful for debugging or when you want
    full control over context management.
    
    Use the returned `thread_id` in subsequent requests to maintain conversation context.
    """
    thread_id = request.thread_id or str(uuid.uuid4())[:8]
    
    try:
        config = {"configurable": {"thread_id": thread_id}}
        
        # Invoke the raw supervisor agent directly
        response = supervisor_agent.invoke(
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
            detail=f"Raw agent execution failed: {str(e)}"
        )


@router.post("/raw/chat/stream")
async def raw_chat_stream(request: ChatRequest):
    """
    Stream a response from the raw HR Supervisor Agent using Server-Sent Events (SSE).
    
    ⚠️ WARNING: This endpoint has known issues and needs to be fixed.
    Use /raw/chat for reliable batch requests.
    
    This endpoint bypasses the CompactingSupervisor wrapper, giving direct access
    to the underlying supervisor agent's streaming capabilities.
    
    Yields chunks as SSE events:
    - event: token - A content token from the AI response
    - event: done - Final message with metadata (token_count, thread_id)
    - event: error - Error occurred
    """
    thread_id = request.thread_id or str(uuid.uuid4())[:8]
    
    def generate():
        try:
            config = {"configurable": {"thread_id": thread_id}}
            full_response_content = ""
            
            # Stream from the raw supervisor agent
            for chunk in supervisor_agent.stream(
                {"messages": [HumanMessage(content=request.message)]},
                config=config,
                stream_mode="messages"
            ):
                # chunk is a tuple: (message, metadata)
                message, metadata = chunk
                
                # Only yield content from AI messages that have content
                if hasattr(message, 'content') and message.content:
                    msg_type = message.__class__.__name__
                    if 'AIMessage' in msg_type:
                        yield f"event: token\ndata: {json.dumps({'content': message.content})}\n\n"
                        full_response_content += message.content
            
            # Get final state for token counting
            final_state = supervisor_agent.get_state(config)
            token_count = 0
            if final_state and hasattr(final_state, 'values'):
                final_messages = final_state.values.get("messages", [])
                token_count = count_tokens_for_messages(final_messages)
            
            yield f"event: done\ndata: {json.dumps({'thread_id': thread_id, 'token_count': token_count})}\n\n"
                    
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

