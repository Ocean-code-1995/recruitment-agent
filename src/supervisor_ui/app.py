"""
Streamlit UI for HR Supervisor Agent.

Connects to the Supervisor API.
Run with: streamlit run src/supervisor_ui/app.py

In Docker, set SUPERVISOR_API_URL environment variable.
Locally, defaults to http://localhost:8080/api/v1/supervisor
"""

import os
import streamlit as st
import requests

# API Configuration - use env var in Docker, fallback for local dev
API_BASE_URL = os.getenv("SUPERVISOR_API_URL", "http://localhost:8080/api/v1/supervisor")

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
        # Call API to create new chat session
        try:
            response = requests.post(f"{API_BASE_URL}/new")
            if response.status_code == 200:
                data = response.json()
                st.session_state.thread_id = data["thread_id"]
                st.session_state.messages = []
                st.session_state.token_usage = 0
            else:
                st.error("Failed to create new chat session")
        except requests.exceptions.ConnectionError:
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

    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("Thinking..."):
            try:
                # Call the API
                payload = {
                    "message": prompt,
                    "thread_id": st.session_state.thread_id
                }
                
                response = requests.post(
                    f"{API_BASE_URL}/chat",
                    json=payload,
                    timeout=120  # Long timeout for agent processing
                )
                
                if response.status_code == 200:
                    data = response.json()
                    full_response = data["response"]
                    
                    # Update thread_id if this was first message
                    if st.session_state.thread_id is None:
                        st.session_state.thread_id = data["thread_id"]
                    
                    # Update token usage
                    st.session_state.token_usage = data["token_count"]
                    token_metric_placeholder.metric(label="Context Window Tokens", value=data["token_count"])
                    
                    message_placeholder.markdown(full_response)
                else:
                    error_detail = response.json().get("detail", "Unknown error")
                    full_response = f"❌ API Error: {error_detail}"
                    message_placeholder.error(full_response)
                    
            except requests.exceptions.ConnectionError:
                full_response = "❌ Cannot connect to API. Make sure the server is running:\n\n`uvicorn src.api.app:app --reload --port 8080`"
                message_placeholder.error(full_response)
            except requests.exceptions.Timeout:
                full_response = "❌ Request timed out. The agent is taking too long to respond."
                message_placeholder.error(full_response)
            except Exception as e:
                full_response = f"❌ Error: {str(e)}"
                message_placeholder.error(full_response)
                import traceback
                st.error(traceback.format_exc())

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
