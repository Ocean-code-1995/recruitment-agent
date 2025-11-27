"""
Compacting Supervisor - Agent wrapper with automatic context management.

Wraps an agent to enforce Context Window limits via 'Compaction'.
Implements the Interceptor Pattern to transparently manage token usage.
"""

from typing import Dict, Any, Generator

from src.agents.supervisor.supervisor_v2 import supervisor_agent, memory

from .token_counter import count_tokens_for_messages
from .history_manager import HistoryManager


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

    def stream(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
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


# =============================================================================
# SINGLETON INSTANCES
# =============================================================================

history_manager = HistoryManager(memory_saver=memory)

compacting_supervisor = CompactingSupervisor(
    agent=supervisor_agent, 
    history_manager=history_manager,
    token_limit=500,
    compaction_ratio=0.5
)

