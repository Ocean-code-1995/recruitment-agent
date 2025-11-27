import time
import random
import uuid
import tiktoken
from datetime import datetime
from typing import List, Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from src.prompts import get_prompt
from src.agents.supervisor.supervisor_v2 import supervisor_agent, memory

"""
Context Engineering Module
--------------------------
Handles context window optimization and memory management for Long-Running Agents.
Implements "Compactive Summarization" to prevent token overflow while preserving
critical conversation history.
"""

# ==================================================================================
# PURE UTILITIES
# ==================================================================================

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


# ==================================================================================
# HISTORY MANAGER
# ==================================================================================

class HistoryManager:
    """
    Manages persistent conversation state and implements compaction logic.
    
    Responsibilities:
    1. Compaction: Summarizing old messages to save tokens.
    2. Persistence: Safely updating the low-level checkpoint storage.
    """
    
    def __init__(self, memory_saver):
        self.memory = memory_saver

    def _messages_to_text(self, messages: List[BaseMessage]) -> str:
        """Convert messages to a plain text transcript.
        """
        text_parts = []
        for msg in messages:
            role = msg.__class__.__name__
            content = msg.content
            if isinstance(content, str):
                text_parts.append(f"{role}: {content}")
            else:
                text_parts.append(f"{role}: {str(content)}")
        return "\n\n".join(text_parts)

    def _is_tool_message(self, msg: BaseMessage) -> bool:
        """Check if a message is a ToolMessage or Tool output.
        """
        msg_type = getattr(msg, "type", None)
        role = getattr(msg, "role", None)
        return msg_type == "tool" or role == "tool" or msg.__class__.__name__ == "ToolMessage"

    def compact_messages(self, messages: List[BaseMessage], compaction_ratio: float = 0.5) -> List[BaseMessage]:
        """
        Apply "Compactive Summarization" to the conversation history.
        
        Technique:
        - Splits history into Old and Recent based on compaction_ratio.
        - Summarizes Old messages into a single narrative block using an LLM.
        - Preserves the System Prompt and Recent messages verbatim.
        
        Args:
            messages: Full list of conversation messages.
            compaction_ratio: Fraction of messages to compact (0.0 to 1.0).
                - 0.5 (Default): Summarizes 50% (Oldest half).
                - 0.8: Aggressive. Summarizes 80% (Keeps only very recent messages).
                - 0.2: Gentle. Summarizes only the oldest 20%.
            
        Returns:
            List[BaseMessage]: optimized list with summary replacing old history.
        """
        if len(messages) < 2:
            return messages
        
        system_msg = None
        conversation_msgs = messages
        
        # Preserve system prompt
        if isinstance(messages[0], SystemMessage):
            system_msg = messages[0]
            conversation_msgs = messages[1:]
        
        if len(conversation_msgs) < 2:
            return messages
        
        # Calculate split point based on ratio
        split_idx = int(len(conversation_msgs) * compaction_ratio)
        
        # Ensure we compact at least something if ratio > 0, but keep at least one recent message
        split_idx = max(1, min(split_idx, len(conversation_msgs) - 1))
        
        first_half = conversation_msgs[:split_idx]
        second_half = conversation_msgs[split_idx:]
        
        # Ensure second_half does not start with orphaned tool message
        while second_half and self._is_tool_message(second_half[0]):
            if first_half:
                second_half.insert(0, first_half.pop())
            else:
                second_half.pop(0)
        
        # Generate summary
        compactor_prompt = get_prompt(template_name="Compactor", latest_version=True)
        conversation_text = self._messages_to_text(first_half)
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=1000)
        messages_for_llm = [
            SystemMessage(content=compactor_prompt),
            HumanMessage(content=f"Conversation history to summarize:\n\n{conversation_text}")
        ]
        
        response = llm.invoke(messages_for_llm)
        summary_text = response.content
        
        print(f"\n{'='*80}\n📝 COMPACTION MESSAGE:\n{summary_text}\n{'='*80}\n", flush=True)
        
        summary_message = AIMessage(content=f"[COMPACTED SUMMARY OF EARLIER CONVERSATION]\n\n{summary_text}")
        
        result = []
        if system_msg:
            result.append(system_msg)
        result.append(summary_message)
        result.extend(second_half)
        
        return result

    def replace_thread_history(self, thread_id: str, new_messages: List[BaseMessage]) -> bool:
        """
        Atomically overwrite the message history in the checkpoint storage.
        
        This bypasses the standard append-only reducer to force a history rewrite.
        Crucial for finalizing the compaction process.
        """
        config = {"configurable": {"thread_id": thread_id}}
        current_checkpoint = self.memory.get_tuple(config)
        
        if not current_checkpoint or not current_checkpoint.checkpoint:
            return False

        checkpoint_config = {
            "configurable": {**current_checkpoint.config.get("configurable", {})}
        }
        checkpoint_config["configurable"].setdefault("thread_id", thread_id)
        checkpoint_config["configurable"].setdefault("checkpoint_ns", "")
        
        current_versions = current_checkpoint.checkpoint.get('channel_versions', {})
        new_msg_version = f"{str(int(time.time())).zfill(32)}.0.{random.random()}"
        
        new_versions = current_versions.copy()
        new_versions['messages'] = new_msg_version
        
        new_checkpoint = {
            'v': current_checkpoint.checkpoint.get('v', 1) + 1,
            'ts': datetime.utcnow().isoformat(),
            'id': str(uuid.uuid4()),
            'channel_versions': new_versions,
            'versions_seen': current_checkpoint.checkpoint.get('versions_seen', {}),
            'updated_channels': ['messages'],
            'channel_values': {'messages': new_messages}
        }
        
        existing_metadata = current_checkpoint.metadata or {}
        new_metadata = {
            **existing_metadata,
            "source": "compaction",
            "compacted_at": datetime.utcnow().isoformat(),
        }
        if "step" not in new_metadata:
            new_metadata["step"] = existing_metadata.get("step", 0)

        self.memory.put(
            config=checkpoint_config,
            checkpoint=new_checkpoint,
            metadata=new_metadata,
            new_versions={'messages': new_msg_version}
        )
        return True


# ==================================================================================
# AGENT WRAPPER
# ==================================================================================

class CompactingSupervisor:
    """
    Wraps an agent to enforce Context Window limits via 'Compaction'.
    
    Technique (Interceptor Pattern):
    1. Intercepts the agent's execution flow.
    2. Runs the agent normally.
    3. Post-execution: Checks if the total context (tokens) exceeds the limit.
    4. If exceeded, triggers `HistoryManager` to compact old history and rewrite memory.
    
    This ensures the agent remains "forever young" regarding token usage, 
    without losing long-term context.
    """
    
    def __init__(self, agent, history_manager: HistoryManager, token_limit: int = 3000, compaction_ratio: float = 0.5):
        self.agent = agent
        self.history_manager = history_manager
        self.token_limit = token_limit
        self.compaction_ratio = compaction_ratio

    def invoke(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent and perform context maintenance if needed.
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        
        # 1. Invoke the agent
        response = self.agent.invoke(input_data, config)
        
        # 2. Check total tokens after response
        if thread_id and "messages" in response:
            all_messages = response["messages"]
            total_tokens = count_tokens_for_messages(all_messages)
            
            if total_tokens > self.token_limit:
                print(f"Tokens ({total_tokens}) exceeded limit ({self.token_limit}). Compacting...", flush=True)
                try:
                    # Delegate complex logic to HistoryManager
                    compacted_messages = self.history_manager.compact_messages(
                        all_messages, 
                        compaction_ratio=self.compaction_ratio
                    )
                    self.history_manager.replace_thread_history(thread_id, compacted_messages)
                    
                    # Update response to reflect compacted state so UI sees the change
                    response["messages"] = compacted_messages
                    
                    # Verify reduction
                    new_tokens = count_tokens_for_messages(compacted_messages)
                    print(f"Compaction complete. {total_tokens} -> {new_tokens}", flush=True)
                except Exception as e:
                    print(f"Compaction failed: {e}", flush=True)
        
        return response

    def stream(self, input_data: Dict[str, Any], config: Dict[str, Any]):
        """
        Stream the agent response token by token, then perform compaction if needed.
        
        Yields:
            dict: Streaming chunks with 'type' and 'content' keys.
                  - type='token': A content token from the AI response
                  - type='done': Final message with token count
                  - type='error': Error occurred
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        full_response_content = ""
        final_messages = []
        
        try:
            # Stream from the agent
            for chunk in self.agent.stream(input_data, config, stream_mode="messages"):
                # chunk is a tuple: (message, metadata)
                message, metadata = chunk
                
                # Only yield content from AI messages that have content
                if hasattr(message, 'content') and message.content:
                    # Check if this is an AIMessageChunk (streaming token)
                    msg_type = message.__class__.__name__
                    if 'AIMessage' in msg_type:
                        yield {"type": "token", "content": message.content}
                        full_response_content += message.content
            
            # After streaming completes, get the final state for compaction check
            # We need to get the current state from memory
            final_state = self.agent.get_state(config)
            if final_state and hasattr(final_state, 'values'):
                final_messages = final_state.values.get("messages", [])
            
            # Perform compaction if needed
            token_count = 0
            if thread_id and final_messages:
                token_count = count_tokens_for_messages(final_messages)
                
                if token_count > self.token_limit:
                    print(f"Tokens ({token_count}) exceeded limit ({self.token_limit}). Compacting...", flush=True)
                    try:
                        compacted_messages = self.history_manager.compact_messages(
                            final_messages,
                            compaction_ratio=self.compaction_ratio
                        )
                        self.history_manager.replace_thread_history(thread_id, compacted_messages)
                        token_count = count_tokens_for_messages(compacted_messages)
                        print(f"Compaction complete. New token count: {token_count}", flush=True)
                    except Exception as e:
                        print(f"Compaction failed: {e}", flush=True)
            
            yield {"type": "done", "token_count": token_count}
            
        except Exception as e:
            yield {"type": "error", "content": str(e)}

# Initialize Singleton Instances
history_manager = HistoryManager(memory_saver=memory)
compacting_supervisor = CompactingSupervisor(
    agent=supervisor_agent, 
    history_manager=history_manager,
    token_limit=500,
    compaction_ratio=0.5
)
