import streamlit as st
import sys
import os
import uuid
import time
import random
from datetime import datetime
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
import threading


# Load env vars
load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.agents.supervisor.supervisor_v2 import supervisor_agent, memory
from src.supervisor_ui.utils.token_counter import count_tokens_for_messages
from src.supervisor_ui.utils.message_compactor import compact_messages

st.set_page_config(page_title="HR Supervisor Agent", layout="wide")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize thread_id for LangGraph memory
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())[:8]

# Track if we just compacted to avoid immediate re-compaction
if "last_compacted_token_count" not in st.session_state:
    st.session_state.last_compacted_token_count = 0

# Lock to prevent concurrent compaction
if "compaction_lock" not in st.session_state:
    st.session_state.compaction_lock = threading.Lock()
    
# Flag to indicate compaction is in progress
if "is_compacting" not in st.session_state:
    st.session_state.is_compacting = False

st.title("🤖 HR Supervisor Agent")
st.caption("I can query the candidate database and help with recruitment tasks.")

# Sidebar with "New Chat" button to reset context
with st.sidebar:
    st.header("Controls")
    if st.button("Start New Chat", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())[:8]
        st.session_state.token_usage = 0
        st.rerun()
    
    st.divider()
    st.caption(f"Chat ID:\n`{st.session_state.get('thread_id', 'Not set')}`")
    
    # Placeholder for token usage to allow dynamic updates
    token_metric_placeholder = st.empty()
    
    if "token_usage" in st.session_state:
        token_metric_placeholder.metric(label="Context Window Tokens", value=st.session_state.token_usage)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Ask me anything about candidates..."):
    # Wait for any ongoing compaction to complete
    if st.session_state.is_compacting:
        with st.spinner("⏳ Waiting for compaction to complete..."):
            with st.session_state.compaction_lock:
                pass  # Lock acquired, compaction is done
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        response = None
        all_messages = None
        total_tokens = 0
        
        with st.spinner("Thinking..."):
            try:
                # Config for stateful conversation (checkpointer)
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                
                # Run the agent with ONLY the new message
                # Because we use a checkpointer, the agent "remembers" previous messages automatically
                response = supervisor_agent.invoke(
                    {"messages": [HumanMessage(content=prompt)]},
                    config=config
                )
                
                # Extract the final response from the agent
                # LangGraph returns the final state. We want the last AIMessage.
                final_message = response["messages"][-1]
                full_response = final_message.content
                
                # Calculate tokens for the FULL history (context window)
                all_messages = response["messages"]
                total_tokens = count_tokens_for_messages(all_messages)
                
                st.session_state.token_usage = total_tokens
                
                # Update sidebar immediately
                token_metric_placeholder.metric(label="Context Window Tokens", value=total_tokens)
                
                message_placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"❌ Error: {str(e)}"
                message_placeholder.error(full_response)
                import traceback
                st.error(traceback.format_exc())

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # 🔄 COMPACTION HAPPENS AFTER RESPONSE IS COMPLETE
    # Only compact if we have valid message history
    if all_messages and total_tokens > 0:
        original_token_count = total_tokens
        
        # Only compact if tokens exceeded threshold
        if total_tokens > 3000:
            # Use lock to prevent concurrent compaction
            with st.session_state.compaction_lock:
                try:
                    st.session_state.is_compacting = True
                    
                    compacted_messages = compact_messages(all_messages)
                    
                    # Get the current checkpoint to preserve metadata
                    config = {"configurable": {"thread_id": st.session_state.thread_id}}
                    current_checkpoint = memory.get_tuple(config)
                    
                    if current_checkpoint and current_checkpoint.checkpoint:
                        # Use the checkpoint's config so checkpoint_ns/checkpoint_id are preserved
                        checkpoint_config = {
                            "configurable": {
                                **current_checkpoint.config.get("configurable", {})
                            }
                        }
                        checkpoint_config["configurable"].setdefault("thread_id", st.session_state.thread_id)
                        checkpoint_config["configurable"].setdefault("checkpoint_ns", "")
                        
                        # Create a new checkpoint with compacted messages
                        # This completely replaces the message history instead of appending
                        
                        # Get current channel versions (preserve the complex version string format)
                        current_versions = current_checkpoint.checkpoint.get('channel_versions', {})
                        
                        # Create a new version string for messages channel
                        # Format: padded_number.decimal.random_fraction
                        import random
                        new_msg_version = f"{str(int(time.time())).zfill(32)}.0.{random.random()}"
                        
                        # Update all channel versions to reflect the new state
                        new_versions = current_versions.copy()
                        new_versions['messages'] = new_msg_version
                        
                        new_checkpoint = {
                            'v': current_checkpoint.checkpoint.get('v', 1) + 1,
                            'ts': datetime.utcnow().isoformat(),
                            'id': str(uuid.uuid4()),
                            'channel_versions': new_versions,
                            'versions_seen': current_checkpoint.checkpoint.get('versions_seen', {}),
                            'updated_channels': ['messages'],
                            'channel_values': {
                                'messages': compacted_messages
                            }
                        }
                        
                        # Directly replace the checkpoint in memory
                        existing_metadata = current_checkpoint.metadata or {}
                        new_metadata = {
                            **existing_metadata,
                            "source": "compaction",
                            "compacted_at": datetime.utcnow().isoformat(),
                        }
                        # Ensure required step field is carried over to avoid KeyError downstream
                        if "step" not in new_metadata:
                            new_metadata["step"] = existing_metadata.get("step", 0)
                        memory.put(
                            config=checkpoint_config,
                            checkpoint=new_checkpoint,
                            metadata=new_metadata,
                            new_versions={'messages': new_msg_version}
                        )

                    # Recalculate tokens after compaction
                    total_tokens = count_tokens_for_messages(compacted_messages)
                    st.session_state.last_compacted_token_count = total_tokens
                    reduction = original_token_count - total_tokens
                    percent_saved = int(100 * reduction / original_token_count)
                    
                    print(f"Before: {original_token_count} tokens | After: {total_tokens} tokens | Saved: {percent_saved}%", flush=True)
                    
                    # Update UI
                    token_metric_placeholder.metric(label="Context Window Tokens", value=total_tokens)
                    st.success(f"✅ Conversation compacted! Tokens reduced: {original_token_count} → {total_tokens}")
                    
                    st.session_state.is_compacting = False
                    
                except Exception as compact_error:
                    st.session_state.is_compacting = False
                    print(f"Compaction error: {str(compact_error)}", flush=True)
                    st.warning(f"⚠️ Compaction skipped: {str(compact_error)}")
