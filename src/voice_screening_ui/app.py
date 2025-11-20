"""
Voice Screening MVP - Streamlit UI for browser-based voice interviews.
"""
import os
import streamlit as st
from datetime import datetime
from pathlib import Path
import uuid

import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load from repo root .env
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, will try to get from environment

# Add src directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))


# Try to import requests for health check (optional)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Helper function to get API key from environment or secrets
def get_openai_api_key():
    """Get OpenAI API key from environment variable or Streamlit secrets."""
    # Try environment variable first (works with docker env_file)
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key:
        return api_key
    
    # Fallback to Streamlit secrets if available
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        return api_key
    except (st.errors.StreamlitSecretNotFoundError, KeyError, AttributeError):
        # Secrets file doesn't exist or key not found
        return ""

# Page configuration
st.set_page_config(
    page_title="Voice Screening Interview",
    page_icon="🎙️",
    layout="centered"
)

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "transcript" not in st.session_state:
    st.session_state.transcript = []
if "is_interview_active" not in st.session_state:
    st.session_state.is_interview_active = False
if "candidate_id" not in st.session_state:
    st.session_state.candidate_id = None

st.title("🎙️ Voice Screening Interview")
st.markdown(
    """
    Welcome to your voice screening interview.  
    Click **Start Interview** to begin, then use the push-to-talk button to speak.
    """
)

# Candidate selection (for MVP, can be simplified)
with st.expander("Candidate Information"):
    candidate_email = st.text_input("Candidate Email", placeholder="candidate@example.com")
    if candidate_email:
        # In a real app, you'd look up the candidate_id from the database
        # For MVP, we'll generate a candidate ID if not set
        if st.session_state.candidate_id is None:
            st.session_state.candidate_id = str(uuid.uuid4())
            st.info(f"Candidate ID: {st.session_state.candidate_id}")

# Interview controls
col1, col2 = st.columns(2)

with col1:
    if not st.session_state.is_interview_active:
        if st.button("🚀 Start Interview", type="primary", use_container_width=True):
            st.session_state.is_interview_active = True
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.transcript = []
            st.session_state.transcript.append({
                "speaker": "system",
                "text": "Interview started",
                "timestamp": datetime.now().isoformat()
            })
            st.rerun()
    else:
        if st.button("⏹️ End Interview", type="secondary", use_container_width=True):
            st.session_state.is_interview_active = False
            st.rerun()

with col2:
    if st.session_state.is_interview_active:
        st.info("🟢 Interview Active")

# Voice interface component
if st.session_state.is_interview_active:
    st.markdown("---")
    st.subheader("Voice Interface")
    
    # Load HTML component with WebSocket and audio handling
    html_file = Path(__file__).parent / "components" / "voice_interface.html"
    if html_file.exists():
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # Inject session ID and API key (from environment variables or Streamlit secrets)
        api_key = get_openai_api_key()
        
        if not api_key:
            st.error("⚠️ OPENAI_API_KEY not found in environment variables or Streamlit secrets")
            st.info("💡 **Debugging Tips:**\n"
                   "- Check that OPENAI_API_KEY is set in your `.env` file\n"
                   "- Verify docker-compose.yml has `env_file: - ../.env`\n"
                   "- Restart the container after adding the key: `docker compose restart voice_screening`")
        else:
            # Determine proxy URL
            # In Docker, use internal service name; locally, use localhost
            proxy_url = os.getenv("WEBSOCKET_PROXY_URL", "ws://localhost:8000/ws/realtime")
            
            # If running in browser, convert Docker internal URL to accessible URL
            # Docker internal: ws://websocket_proxy:8000/ws/realtime
            # Browser needs: ws://localhost:8000/ws/realtime (or host IP)
            if "websocket_proxy" in proxy_url:
                # Replace Docker service name with localhost for browser access
                proxy_url = proxy_url.replace("websocket_proxy", "localhost")
            
            # Show API key status (masked) for debugging
            with st.expander("🔍 Connection Debug Info", expanded=False):
                st.success(f"✅ API Key found: `{api_key[:10]}...{api_key[-4:]}`")
                st.info(f"**WebSocket Proxy:** `{proxy_url}`")
                st.info("**Note:** The connection uses a WebSocket proxy to handle authentication. "
                       "Browsers cannot set custom headers in WebSocket connections, so we proxy through the backend.")
                if "localhost" in proxy_url or "127.0.0.1" in proxy_url:
                    st.warning("⚠️ Make sure the WebSocket proxy service is running! Check docker-compose logs.")
                
                # Proxy health check
                if HAS_REQUESTS:
                    try:
                        health_url = proxy_url.replace("ws://", "http://").replace("wss://", "https://").replace("/ws/realtime", "/health")
                        response = requests.get(health_url, timeout=2)
                        if response.status_code == 200:
                            health_data = response.json()
                            st.success(f"✅ Proxy is healthy: {health_data.get('status', 'unknown')}")
                            if health_data.get('openai_api_key_configured'):
                                st.success("✅ OpenAI API key is configured in proxy")
                            else:
                                st.error("❌ OpenAI API key NOT configured in proxy")
                        else:
                            st.warning(f"⚠️ Proxy health check returned: {response.status_code}")
                    except Exception as e:
                        st.warning(f"⚠️ Could not check proxy health: {e}")
                        st.info("💡 **To view proxy logs:** `docker compose logs -f websocket_proxy`")
                else:
                    st.info("💡 **To check proxy status:** `docker compose logs websocket_proxy`")
                    st.info("💡 **To view live logs:** `docker compose logs -f websocket_proxy`")
            
            html_content = html_content.replace("{{SESSION_ID}}", st.session_state.session_id)
            html_content = html_content.replace("{{API_KEY}}", api_key)
            html_content = html_content.replace("{{PROXY_URL}}", proxy_url)
            
            st.components.v1.html(html_content, height=500)  # Increased height for error messages
    else:
        st.warning("Voice interface component not found. Please ensure voice_interface.html exists.")
    
    # Transcript display
    st.markdown("---")
    st.subheader("Live Transcript")
    
    if st.session_state.transcript:
        for entry in st.session_state.transcript:
            speaker = entry.get("speaker", "unknown")
            text = entry.get("text", "")
            timestamp = entry.get("timestamp", "")
            
            if speaker == "agent":
                st.markdown(f"**🤖 Agent:** {text}")
            elif speaker == "candidate":
                st.markdown(f"**👤 You:** {text}")
            else:
                st.markdown(f"*{text}*")
    
    # Manual transcript update (for testing - in real app, JS updates this)
    with st.expander("Add Transcript Entry (Testing)"):
        col1, col2 = st.columns([3, 1])
        with col1:
            test_text = st.text_input("Text", key="test_transcript")
        with col2:
            test_speaker = st.selectbox("Speaker", ["candidate", "agent"], key="test_speaker")
        
        if st.button("Add Entry"):
            if test_text:
                st.session_state.transcript.append({
                    "speaker": test_speaker,
                    "text": test_text,
                    "timestamp": datetime.now().isoformat()
                })
                st.rerun()

# Analysis and results
if not st.session_state.is_interview_active and st.session_state.transcript:
    st.markdown("---")
    st.subheader("Interview Analysis")
    
    if st.button("📊 Analyze Interview", type="primary"):
        # Build transcript text
        transcript_text = "\n".join([
            f"{entry.get('speaker', 'unknown')}: {entry.get('text', '')}"
            for entry in st.session_state.transcript
            if entry.get("speaker") in ["agent", "candidate"]
        ])
        
        