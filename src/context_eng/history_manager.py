"""
History Manager for conversation memory and compaction.

Handles persistent conversation state and implements "Compactive Summarization"
to prevent token overflow while preserving critical conversation history.
"""

import time
import random
import uuid
from datetime import datetime
from typing import List

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

from src.prompts import get_prompt


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
        """Convert messages to a plain text transcript."""
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
        """Check if a message is a ToolMessage or Tool output."""
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

