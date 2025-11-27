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

# Import analysis and database utilities
try:
    from src.frontend.streamlit.voice_screening_ui.analysis import analyze_transcript
    from src.frontend.streamlit.voice_screening_ui.utils.db import write_voice_results_to_db
except ImportError as e:
    # Will be handled later when used
    analyze_transcript = None
    write_voice_results_to_db = None


# Try to import requests for health check (optional)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Helper function to get proxy URL
def get_proxy_url():
    """Get WebSocket proxy URL from environment or default."""
    proxy_url = os.getenv("WEBSOCKET_PROXY_URL", "ws://localhost:8000/ws/realtime")
    # Convert Docker internal URL to browser-accessible URL
    if "websocket_proxy" in proxy_url:
        proxy_url = proxy_url.replace("websocket_proxy", "localhost")
    return proxy_url

def get_proxy_base_url():
    """Get HTTP base URL for proxy API calls."""
    proxy_url = get_proxy_url()
    return proxy_url.replace("ws://", "http://").replace("wss://", "https://").replace("/ws/realtime", "")

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
if "session_token" not in st.session_state:
    st.session_state.session_token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "auth_code" not in st.session_state:
    st.session_state.auth_code = None
if "audio_file_path" not in st.session_state:
    st.session_state.audio_file_path = None

st.title("🎙️ Voice Screening Interview")

# Authentication screen
if not st.session_state.session_token:
    st.markdown("### 🔐 Authentication")
    st.markdown("Please enter your email and authentication code to start.")
    
    with st.form("auth_form"):
        user_email = st.text_input("Email", placeholder="your.email@example.com", value=st.session_state.user_email or "")
        auth_code = st.text_input("Authentication Code", placeholder="Enter your code", value=st.session_state.auth_code or "")
        
        verify_submitted = st.form_submit_button("✅ Verify & Login", use_container_width=True, type="primary")
        
        if verify_submitted:
            if user_email and auth_code:
                try:
                    proxy_base = get_proxy_base_url()
                    response = requests.post(
                        f"{proxy_base}/auth/verify",
                        json={"email": user_email, "code": auth_code},
                        timeout=5
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.session_token = data["session_token"]
                        st.session_state.user_email = user_email
                        st.success("✅ Authentication successful!")
                        st.rerun()
                    else:
                        error_data = response.json() if response.content else {}
                        st.error(f"❌ Authentication failed: {error_data.get('detail', response.text)}")
                except Exception as e:
                    st.error(f"❌ Error connecting to proxy: {e}")
                    st.info("💡 Make sure the WebSocket proxy service is running.")
            else:
                st.warning("⚠️ Please enter both email and code.")
    
    st.markdown("---")
    st.info("💡 **Note:** Enter your email and authentication code to proceed.")
    st.stop()

# Main interview interface (only shown after authentication)
col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    st.markdown(
        f"""
        Welcome, **{st.session_state.user_email}**!  
        Click **Start Interview** to begin, then use the toggle button to speak.
        """
    )
with col_header2:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.session_token = None
        st.session_state.user_email = None
        st.session_state.auth_code = None
        st.session_state.is_interview_active = False
        st.rerun()

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
            # Save audio recording before ending interview
            if st.session_state.session_id and st.session_state.session_token and HAS_REQUESTS:
                try:
                    proxy_base = get_proxy_base_url()
                    response = requests.post(
                        f"{proxy_base}/audio/save",
                        params={"token": st.session_state.session_token},
                        json={"session_id": st.session_state.session_id},
                        timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.audio_file_path = data.get("file_path")
                        st.success(f"✅ Audio recording saved: {st.session_state.audio_file_path}")
                    else:
                        st.warning(f"⚠️ Failed to save audio: {response.text}")
                except Exception as e:
                    st.warning(f"⚠️ Error saving audio: {e}")
            
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
        
        # Get proxy URL and session token
        proxy_url = get_proxy_url()
        session_token = st.session_state.session_token
        
        if not session_token:
            st.error("⚠️ No session token. Please authenticate first.")
            st.stop()
        
        # Show connection debug info
        with st.expander("🔍 Connection Debug Info", expanded=False):
            st.success(f"✅ Authenticated as: `{st.session_state.user_email}`")
            st.info(f"**WebSocket Proxy:** `{proxy_url}`")
            st.info("**Note:** The connection uses a WebSocket proxy to handle authentication. "
                   "Browsers cannot set custom headers in WebSocket connections, so we proxy through the backend.")
            if "localhost" in proxy_url or "127.0.0.1" in proxy_url:
                st.warning("⚠️ Make sure the WebSocket proxy service is running! Check docker-compose logs.")
            
            # Proxy health check
            if HAS_REQUESTS:
                try:
                    proxy_base = get_proxy_base_url()
                    health_url = f"{proxy_base}/health"
                    response = requests.get(health_url, timeout=2)
                    if response.status_code == 200:
                        health_data = response.json()
                        st.success(f"✅ Proxy is healthy: {health_data.get('status', 'unknown')}")
                        if health_data.get('openai_api_key_configured'):
                            st.success("✅ OpenAI API key is configured in proxy")
                        else:
                            st.error("❌ OpenAI API key NOT configured in proxy")
                        st.info(f"Active sessions: {health_data.get('active_sessions', 0)}")
                    else:
                        st.warning(f"⚠️ Proxy health check returned: {response.status_code}")
                except Exception as e:
                    st.warning(f"⚠️ Could not check proxy health: {e}")
                    st.info("💡 **To view proxy logs:** `docker compose logs -f websocket_proxy`")
            else:
                st.info("💡 **To check proxy status:** `docker compose logs websocket_proxy`")
                st.info("💡 **To view live logs:** `docker compose logs -f websocket_proxy`")
        
        # Build WebSocket URL with session token
        ws_url = f"{proxy_url}?token={session_token}"
        
        html_content = html_content.replace("{{SESSION_ID}}", st.session_state.session_id)
        html_content = html_content.replace("{{SESSION_TOKEN}}", session_token)
        html_content = html_content.replace("{{PROXY_URL}}", ws_url)
            
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
        
        if not transcript_text.strip():
            st.warning("⚠️ No transcript available to analyze.")
        elif not analyze_transcript or not write_voice_results_to_db:
            st.error("❌ Required modules not available. Please check imports.")
        else:
            with st.spinner("Analyzing transcript..."):
                try:
                    # Analyze transcript
                    analysis_output = analyze_transcript(transcript_text)
                    
                    st.success("✅ Analysis complete!")
                    st.json(analysis_output.model_dump())
                    
                    # Save to database
                    if st.session_state.candidate_id:
                        try:
                            write_voice_results_to_db(
                                candidate_id=st.session_state.candidate_id,
                                session_id=st.session_state.session_id,
                                transcript_text=transcript_text,
                                result=analysis_output,
                                audio_url=st.session_state.audio_file_path
                            )
                            st.success("✅ Results saved to database!")
                        except Exception as e:
                            st.error(f"❌ Failed to save results to database: {e}")
                    else:
                        st.warning("⚠️ Cannot save to database: Candidate ID not set.")
                except Exception as e:
                    st.error(f"❌ Failed to analyze transcript: {e}")
                    import traceback
                    st.code(traceback.format_exc())
        
        