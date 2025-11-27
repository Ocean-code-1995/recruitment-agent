"""
Streamlit UI for HR Supervisor Agent.

Connects to the Supervisor API with streaming support.
Run with: streamlit run src/supervisor_ui/app.py

In Docker, set SUPERVISOR_API_URL environment variable.
Locally, defaults to http://localhost:8080/api/v1/supervisor
"""

import streamlit as st
from src.sdk import SupervisorClient

# Initialize SDK client
client = SupervisorClient()

st.set_page_config(page_title="HR Supervisor Agent", layout="wide")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize thread_id for conversation continuity
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

st.title("🤖 HR Supervisor Agent")
st.caption("I can query the candidate database and help with recruitment tasks.")

# Sidebar with "New Chat" button to reset context
with st.sidebar:
    st.header("Controls")
    if st.button("Start New Chat", type="primary", use_container_width=True):
        try:
            st.session_state.thread_id = client.new_chat()
        st.session_state.messages = []
        st.session_state.token_usage = 0
        except Exception:
            st.error("⚠️ Cannot connect to API. Is the server running?")
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

    # Generate streaming response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Stream the response using SDK
        for chunk in client.stream(prompt, st.session_state.thread_id):
            if chunk.type == "token":
                full_response += chunk.content or ""
                message_placeholder.markdown(full_response + "▌")
                
            elif chunk.type == "done":
                # Update thread_id if this was first message
                if st.session_state.thread_id is None:
                    st.session_state.thread_id = chunk.thread_id
                
                # Update token usage
                st.session_state.token_usage = chunk.token_count or 0
                token_metric_placeholder.metric(
                    label="Context Window Tokens", 
                    value=chunk.token_count or 0
                )
                
                # Final display without cursor
                message_placeholder.markdown(full_response)
                
            elif chunk.type == "error":
                full_response = f"❌ Error: {chunk.error}"
                message_placeholder.error(full_response)
        
        # Handle empty response
        if not full_response:
            full_response = "No response received from agent."
            message_placeholder.warning(full_response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
