import streamlit as st
import sys
import os
import uuid
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Load env vars
load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the wrapper instead of the raw agent
from src.context_eng.context_manager import compacting_supervisor
# Token counter for display purposes
from src.context_eng.context_manager import count_tokens_for_messages

st.set_page_config(page_title="HR Supervisor Agent", layout="wide")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize thread_id for LangGraph memory
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())[:8]

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
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("Thinking..."):
            try:
                # Config for stateful conversation (checkpointer)
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                
                # Run the wrapped agent
                # The wrapper handles compaction internally if needed
                response = compacting_supervisor.invoke(
                    {"messages": [HumanMessage(content=prompt)]},
                    config=config
                )
                
                # Extract the final response from the agent
                final_message = response["messages"][-1]
                full_response = final_message.content
                
                # Calculate tokens for display
                all_messages = response["messages"]
                total_tokens = count_tokens_for_messages(all_messages)
                
                st.session_state.token_usage = total_tokens
                token_metric_placeholder.metric(label="Context Window Tokens", value=total_tokens)
                
                message_placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"❌ Error: {str(e)}"
                message_placeholder.error(full_response)
                import traceback
                st.error(traceback.format_exc())

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
