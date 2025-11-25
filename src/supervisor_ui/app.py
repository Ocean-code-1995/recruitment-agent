import streamlit as st
import sys
import os
import uuid
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.agents.supervisor.supervisor_v2 import supervisor_agent
from langchain_core.messages import HumanMessage, AIMessage

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
        st.rerun()
    
    st.divider()
    st.caption(f"Chat ID:\n`{st.session_state.get('thread_id', 'Not set')}`")

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
                
                message_placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"❌ Error: {str(e)}"
                message_placeholder.error(full_response)
                import traceback
                st.error(traceback.format_exc())

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
