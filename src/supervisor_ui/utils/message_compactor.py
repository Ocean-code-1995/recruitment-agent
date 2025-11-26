"""
Message Compactor: Reduces token count by summarizing conversation history.

When conversation reaches 3000 tokens, compacts the first half of messages
into a high-level summary using the "Compactor" prompt template.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from src.prompts import get_prompt


def compact_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    """
    Compact the first half of messages into a summary.
    Preserves the original system prompt and replaces the conversation history
    with a compacted summary.
    
    Args:
        messages: Full list of conversation messages
        
    Returns:
        list[BaseMessage]: Compacted message list with summary replacing first half
    """
    if len(messages) < 2:
        return messages
    
    # Preserve the original system prompt (first message if it's SystemMessage)
    system_msg = None
    conversation_msgs = messages
    
    if isinstance(messages[0], SystemMessage):
        system_msg = messages[0]
        conversation_msgs = messages[1:]
    
    if len(conversation_msgs) < 2:
        return messages
    
    # Split conversation: first half vs second half
    midpoint = len(conversation_msgs) // 2
    first_half = conversation_msgs[:midpoint]
    second_half = conversation_msgs[midpoint:]
    
    # Ensure second_half does not start with a tool message missing its invoking assistant
    while second_half and _is_tool_message(second_half[0]):
        if first_half:
            # Move the assistant/tool-call message from the first half to preserve ordering
            second_half.insert(0, first_half.pop())
        else:
            # No matching caller available; drop orphaned tool messages
            second_half.pop(0)
    
    # Get the compactor prompt
    compactor_prompt = get_prompt(
        template_name="Compactor",
        latest_version=True
    )
    
    # Convert first half messages to readable format
    conversation_text = _messages_to_text(first_half)
    
    # Create LLM call to summarize
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=1000,
    )
    
    messages_for_llm = [
        SystemMessage(content=compactor_prompt),
        HumanMessage(
            content=(
                f"Conversation history to summarize:\n\n{conversation_text}"
            )
        ),
    ]
    
    response = llm.invoke(messages_for_llm)
    summary_text = response.content
    
    # Print the full compaction output
    print(f"\n{'='*80}", flush=True)
    print(f"📝 COMPACTION MESSAGE:\n{summary_text}", flush=True)
    print(f"{'='*80}\n", flush=True)
    
    # Create an AI message with the summary (not System)
    summary_message = AIMessage(
        content=f"[COMPACTED SUMMARY OF EARLIER CONVERSATION]\n\n{summary_text}"
    )
    
    # Build result: system prompt (if exists) + summary + second half
    result = []
    if system_msg:
        result.append(system_msg)
    result.append(summary_message)
    result.extend(second_half)
    
    return result


def _messages_to_text(messages: list[BaseMessage]) -> str:
    """
    Convert a list of messages to readable text format.
    
    Args:
        messages: List of BaseMessage objects
        
    Returns:
        str: Formatted conversation text
    """
    text_parts = []
    for msg in messages:
        role = msg.__class__.__name__
        content = msg.content
        
        # Handle different message types
        if isinstance(content, str):
            text_parts.append(f"{role}: {content}")
        elif isinstance(content, list):
            # Tool results or other structured content
            text_parts.append(f"{role}: {str(content)}")
        else:
            text_parts.append(f"{role}: {str(content)}")
    
    return "\n\n".join(text_parts)


def _is_tool_message(msg: BaseMessage) -> bool:
    """
    Detect whether a message represents a tool response that requires a preceding tool call.
    """
    msg_type = getattr(msg, "type", None)
    role = getattr(msg, "role", None)
    return msg_type == "tool" or role == "tool" or msg.__class__.__name__ == "ToolMessage"
