"""Token counting utilities for context window management."""

from typing import List, Any

import tiktoken


def count_tokens_for_messages(messages: List[Any], model: str = "gpt-4o") -> int:
    """
    Calculate token usage for a list of messages using tiktoken.
    
    Handles text content, function calls, and tool outputs with approximate
    overhead calculations for the ChatML format.
    
    Args:
        messages: List of LangChain message objects.
        model: Target model encoding to use.
        
    Returns:
        int: Total estimated token count.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    
    num_tokens = 0
    for message in messages:
        # Every message follows <im_start>{role/name}\n{content}<im_end>\n
        num_tokens += 4
        
        # Handle content which might be a string or list of content blocks
        content = getattr(message, "content", "")
        if isinstance(content, str):
            num_tokens += len(encoding.encode(content))
        
        # If there are additional keys (like name, function_call, etc.) we should add them
        if hasattr(message, "name") and message.name:
            num_tokens += len(encoding.encode(message.name))
        
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                num_tokens += len(encoding.encode(str(tool_call)))
                
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens

