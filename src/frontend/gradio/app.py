"""
Gradio Frontend for Recruitment Agent - Hugging Face Spaces Deployment

This is a unified Gradio interface that combines all recruitment agent features:
- Candidate Application Portal
- HR Portal (Candidate Management)
- Supervisor Agent Chat

Deploy to Hugging Face Spaces for the MCP 1st Birthday Hackathon.
"""

import os
import gradio as gr
from typing import Optional, Tuple
import sys
from pathlib import Path

# Add project root to path to enable SDK imports
# __file__ is src/frontend/gradio/app.py
# We need to go up 4 levels to get to project root (where src/ folder is)
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.sdk import SupervisorClient, DatabaseClient, CVUploadClient
    SDK_AVAILABLE = True
    print(f"✅ SDK loaded successfully from {project_root}")
except ImportError as e:
    SDK_AVAILABLE = False
    print(f"⚠️ Warning: SDK not available. Some features may not work.")
    print(f"   Import error: {e}")
    print(f"   Project root: {project_root}")
    print(f"   Python path: {sys.path[:3]}")
    # Try alternative import path (in case resolve() didn't work)
    try:
        alt_root = Path(__file__).parent.parent.parent.parent
        if str(alt_root) not in sys.path:
            sys.path.insert(0, str(alt_root))
        from src.sdk import SupervisorClient, DatabaseClient, CVUploadClient
        SDK_AVAILABLE = True
        print(f"✅ SDK loaded on retry from {alt_root}!")
    except Exception as e2:
        print(f"   Retry also failed: {e2}")


# ============================================================================
# CONFIGURATION
# ============================================================================

def get_api_url(service: str) -> str:
    """Get API URL from environment or default."""
    # Map service names to environment variable names
    env_map = {
        "supervisor": "SUPERVISOR_API_URL",
        "db": "DATABASE_API_URL",
        "database": "DATABASE_API_URL",
        "cv": "CV_UPLOAD_API_URL",
        "voice-screener": "VOICE_SCREENER_API_URL",
    }
    
    # Map service names to actual API paths (matches Next.js config)
    path_map = {
        "supervisor": "supervisor",
        "db": "db",
        "database": "db",  # "database" maps to "db" endpoint
        "cv": "cv",
        "voice-screener": "voice-screener",
    }
    
    env_var = env_map.get(service, f"{service.upper()}_API_URL")
    default_port = "8080"
    
    # Check for environment variable
    api_url = os.getenv(env_var)
    if api_url:
        return api_url
    
    # Get the correct API path
    api_path = path_map.get(service, service)
    
    # Default to localhost or Hugging Face Space URL
    space_id = os.getenv("SPACE_ID")
    if space_id:
        # Running on Hugging Face Spaces - assume backend is on same domain
        # Or use environment variable if set
        return f"https://{space_id}.hf.space/api/v1/{api_path}"
    else:
        # Local development
        return f"http://localhost:{default_port}/api/v1/{api_path}"


# ============================================================================
# CANDIDATE APPLICATION PORTAL
# ============================================================================

def submit_application(full_name: str, email: str, phone: str, cv_file) -> Tuple[str, Optional[str]]:
    """Submit a job application with CV."""
    if not SDK_AVAILABLE:
        return "❌ SDK not available. Please check backend connection.", None
    
    if not full_name or not email:
        return "❌ Full name and email are required.", None
    
    if not cv_file:
        return "❌ Please upload your CV (PDF or DOCX).", None
    
    try:
        client = CVUploadClient(base_url=get_api_url("cv"))
        
        # Gradio file object has .name attribute with the file path
        file_path = cv_file.name if hasattr(cv_file, 'name') else str(cv_file)
        filename = Path(file_path).name
        
        # Open file and pass file handle to SDK (it expects a file-like object)
        with open(file_path, 'rb') as f:
            response = client.submit(
                full_name=full_name,
                email=email,
                phone=phone or "",
                cv_file=f,
                filename=filename
            )
        
        if response.success:
            return f"✅ {response.message}\n\nYour application has been recorded. You will receive updates soon.", None
        elif response.already_exists:
            return f"⚠️ {response.message}\n\nPlease wait for review.", None
        else:
            return f"❌ {response.message}", None
            
    except Exception as e:
        return f"❌ Failed to submit application: {str(e)}\n\nMake sure the backend API is running.", None


def check_application_status(email: str) -> str:
    """Check application status by email."""
    if not SDK_AVAILABLE:
        return "❌ SDK not available. Please check backend connection."
    
    if not email:
        return "❌ Please enter your email address."
    
    try:
        client = DatabaseClient(base_url=get_api_url("database"))
        response = client.get_candidate_by_email(email, include_relations=True)
        
        if response.success and response.data:
            candidate = response.data
            status = candidate.get('status', 'unknown')
            created_at = candidate.get('created_at', 'N/A')
            
            info = f"**Application Status:** {status}\n"
            info += f"**Applied:** {created_at}\n\n"
            
            # CV Screening results
            if candidate.get('cv_screening_results'):
                latest = candidate['cv_screening_results'][0]
                score = latest.get('overall_fit_score', 0)
                info += f"**CV Screening Score:** {score * 100:.1f}%\n"
            
            # Voice screening
            if candidate.get('voice_screening_results'):
                info += "**Voice Screening:** ✅ Completed\n"
            
            # Interview
            if candidate.get('interview_scheduling'):
                interview = candidate['interview_scheduling'][0]
                info += f"**Interview:** {interview.get('status', 'Scheduled')}\n"
            
            # Final decision
            if candidate.get('final_decision'):
                decision = candidate['final_decision']
                info += f"**Final Decision:** {decision.get('decision', 'Pending')}\n"
            
            return info
        else:
            return f"❌ No application found for {email}. Please submit an application first."
            
    except Exception as e:
        return f"❌ Error checking status: {str(e)}"


# ============================================================================
# HR PORTAL
# ============================================================================

def load_candidates(status_filter: Optional[str] = None) -> Tuple[str, list]:
    """Load candidates from database."""
    if not SDK_AVAILABLE:
        return "❌ SDK not available. Please check backend connection.", []
    
    try:
        client = DatabaseClient(base_url=get_api_url("database"))
        response = client.get_candidates(
            status=status_filter if status_filter != "All" else None,
            limit=100,
            include_relations=True
        )
        
        if response.success and response.data:
            candidates = response.data
            if not candidates:
                return "No candidates found.", []
            
            # Format candidates for display
            table_rows = []
            for c in candidates:
                name = c.get('full_name', 'Unknown')
                email = c.get('email', 'N/A')
                status = c.get('status', 'unknown')
                applied = c.get('created_at', 'N/A')
                has_voice = bool(c.get('voice_screening_results'))
                
                table_rows.append([
                    name,
                    email,
                    status,
                    str(applied)[:10] if applied != 'N/A' else 'N/A',
                    "✅" if has_voice else "❌"
                ])
            
            header = "| Name | Email | Status | Applied | Voice Screening |\n"
            header += "|------|-------|-------|---------|------------------|\n"
            table = header + "\n".join([f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |" for r in table_rows])
            
            return f"Found {len(candidates)} candidate(s):\n\n{table}", table_rows
        else:
            return "No candidates found.", []
            
    except Exception as e:
        return f"❌ Error loading candidates: {str(e)}", []


def trigger_voice_screening(candidate_email: str) -> str:
    """Trigger voice screening for a candidate."""
    if not SDK_AVAILABLE:
        return "❌ SDK not available. Please check backend connection."
    
    if not candidate_email:
        return "❌ Please enter candidate email."
    
    try:
        supervisor_client = SupervisorClient(base_url=get_api_url("supervisor"))
        # Create a new thread for this action
        thread_id = supervisor_client.new_chat()
        response = supervisor_client.chat(
            message=f"Please trigger voice screening for candidate with email {candidate_email}",
            thread_id=thread_id
        )
        
        token_info = f"\n\n📊 Token usage: {response.token_count:,} tokens" if response.token_count else ""
        return f"✅ Voice screening triggered!\n\n{response.content}{token_info}"
        
    except Exception as e:
        return f"❌ Failed to trigger voice screening: {str(e)}"


def schedule_interview(candidate_email: str) -> str:
    """Schedule interview for a candidate."""
    if not SDK_AVAILABLE:
        return "❌ SDK not available. Please check backend connection."
    
    if not candidate_email:
        return "❌ Please enter candidate email."
    
    try:
        supervisor_client = SupervisorClient(base_url=get_api_url("supervisor"))
        # Create a new thread for this action
        thread_id = supervisor_client.new_chat()
        response = supervisor_client.chat(
            message=f"Please schedule an interview for candidate with email {candidate_email}",
            thread_id=thread_id
        )
        
        token_info = f"\n\n📊 Token usage: {response.token_count:,} tokens" if response.token_count else ""
        return f"✅ Interview scheduling initiated!\n\n{response.content}{token_info}"
        
    except Exception as e:
        return f"❌ Failed to schedule interview: {str(e)}"


# ============================================================================
# SUPERVISOR AGENT CHAT
# ============================================================================

class ChatState:
    """Manage chat state across interactions."""
    def __init__(self):
        self.thread_id: Optional[str] = None
        self.messages: list = []
        self.total_tokens: int = 0
    
    def reset(self):
        """Reset chat state."""
        self.thread_id = None
        self.messages = []
        self.total_tokens = 0


chat_state = ChatState()


def init_chat() -> Tuple[str, str, str]:
    """Initialize a new chat session."""
    if not SDK_AVAILABLE:
        return "❌ SDK not available. Please check backend connection.", "", "📊 Total tokens: 0"
    
    try:
        client = SupervisorClient(base_url=get_api_url("supervisor"))
        thread_id = client.new_chat()
        chat_state.thread_id = thread_id
        chat_state.messages = []
        chat_state.total_tokens = 0
        
        welcome = "Hello! I'm the HR Supervisor Agent. I can help you with:\n\n"
        welcome += "• Querying candidate information\n"
        welcome += "• Screening CVs\n"
        welcome += "• Scheduling interviews\n"
        welcome += "• Managing the recruitment pipeline\n"
        welcome += "• Answering questions about candidates\n\n"
        welcome += "What would you like to know?"
        
        chat_state.messages.append(("assistant", welcome))
        chat_history = format_chat_history(chat_state.messages)
        token_info = "📊 Total tokens: 0"
        
        return welcome, chat_history, token_info
        
    except Exception as e:
        return f"❌ Failed to initialize chat: {str(e)}", "", "📊 Total tokens: 0"


def format_chat_history(messages: list) -> str:
    """Format chat messages for display."""
    formatted = []
    for role, content in messages:
        if role == "user":
            formatted.append(f"**You:** {content}")
        else:
            formatted.append(f"**Assistant:** {content}")
    return "\n\n".join(formatted)


def chat_with_supervisor(message: str, history: str) -> Tuple[str, str]:
    """Send a message to the supervisor agent."""
    if not SDK_AVAILABLE:
        return history, "❌ SDK not available. Please check backend connection."
    
    if not message.strip():
        return history, ""
    
    # Initialize chat if needed
    if not chat_state.thread_id:
        init_chat()
    
    try:
        client = SupervisorClient(base_url=get_api_url("supervisor"))
        
        # Add user message
        chat_state.messages.append(("user", message))
        
        # Get response
        response = client.chat(
            message=message,
            thread_id=chat_state.thread_id
        )
        
        # Add assistant response
        chat_state.messages.append(("assistant", response.content))
        chat_state.total_tokens += response.token_count or 0
        
        # Format history
        new_history = format_chat_history(chat_state.messages)
        token_info = f"📊 Total tokens: {chat_state.total_tokens:,}"
        
        return new_history, token_info
        
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        chat_state.messages.append(("assistant", error_msg))
        new_history = format_chat_history(chat_state.messages)
        token_info = f"📊 Total tokens: {chat_state.total_tokens:,}"
        return new_history, token_info


# ============================================================================
# GRADIO INTERFACE
# ============================================================================

def create_interface():
    """Create the main Gradio interface."""
    
    # White background, black text, blue highlights theme
    custom_theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="blue",
    ).set(
        body_background_fill="#ffffff",
        body_background_fill_dark="#ffffff",
        button_primary_background_fill="#2563eb",
        button_primary_background_fill_hover="#1d4ed8",
        button_primary_text_color="#ffffff",
        button_secondary_background_fill="#ffffff",
        button_secondary_background_fill_hover="#f3f4f6",
        button_secondary_text_color="#000000",
        border_color_primary="#e5e7eb",
        input_background_fill="#ffffff",
        input_border_color="#2563eb",
        block_background_fill="#ffffff",
        block_background_fill_dark="#ffffff",
        block_label_text_color="#000000",
        block_title_text_color="#000000",
        shadow_drop="0 1px 3px rgba(0, 0, 0, 0.1)",
    )
    
    # Custom CSS for white background, black text, blue highlights
    custom_css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Global white background */
    body, html {
        background-color: #ffffff !important;
    }
    
    .gradio-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Ensure all text is black */
    .gradio-container * {
        color: #000000 !important;
    }
    
    /* Header styling with blue background */
    .main-header {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white !important;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        color: white !important;
    }
    
    .main-header p {
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
        color: white !important;
        opacity: 0.95;
    }
    
    .main-header a {
        color: #fbbf24 !important;
        text-decoration: underline;
    }
    
    /* Section headers - black text */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #000000 !important;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #2563eb;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
    }
    
    h3 {
        color: #000000 !important;
        font-weight: 600;
    }
    
    /* Info boxes - white background with blue border */
    .info-box {
        background: #ffffff !important;
        border: 2px solid #2563eb !important;
        border-left: 4px solid #2563eb !important;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #000000 !important;
    }
    
    .info-box strong {
        color: #2563eb !important;
    }
    
    .success-box {
        background: #ffffff !important;
        border: 2px solid #2563eb !important;
        border-left: 4px solid #2563eb !important;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #000000 !important;
    }
    
    .warning-box {
        background: #ffffff !important;
        border: 2px solid #2563eb !important;
        border-left: 4px solid #2563eb !important;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #000000 !important;
    }
    
    /* Text inputs and textboxes - white background, black text */
    .gradio-textbox textarea,
    .gradio-textbox input {
        color: #000000 !important;
        background-color: #ffffff !important;
        border-color: #2563eb !important;
    }
    
    .gradio-textbox label {
        color: #000000 !important;
        font-weight: 500;
    }
    
    /* Chat history - black text on white */
    textarea[readonly] {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Markdown content - black text */
    .markdown-text {
        color: #000000 !important;
    }
    
    .markdown-text strong {
        color: #000000 !important;
    }
    
    /* Buttons - blue primary, white secondary with blue border */
    .gradio-button {
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    .gradio-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }
    
    /* Form elements */
    .gradio-textbox, .gradio-dropdown {
        border-radius: 8px !important;
        background-color: #ffffff !important;
    }
    
    .gradio-dropdown select {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Tabs - black text */
    .tab-nav {
        font-weight: 500 !important;
        color: #000000 !important;
    }
    
    /* All blocks and panels - white background */
    .gradio-block, .panel, .panel-group {
        background-color: #ffffff !important;
    }
    
    /* Status output - black text */
    .status-output {
        color: #000000 !important;
    }
    
    /* File hint text - dark gray */
    .file-hint {
        color: #4b5563 !important;
    }
    
    /* All labels - black text */
    label {
        color: #000000 !important;
    }
    
    /* Placeholder text - light gray */
    ::placeholder {
        color: #9ca3af !important;
        opacity: 1;
    }
    
    /* Statistics panel - white background, black text */
    .gradio-textbox[readonly] {
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
    }
    
    /* Links - blue */
    a {
        color: #2563eb !important;
    }
    
    a:hover {
        color: #1d4ed8 !important;
    }
    
    /* Tables - black text on white */
    table {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    table th, table td {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Ensure all markdown renders with black text */
    .markdown {
        color: #000000 !important;
    }
    
    /* Input borders - blue when focused */
    input:focus, textarea:focus, select:focus {
        border-color: #2563eb !important;
        outline-color: #2563eb !important;
    }
    """
    
    with gr.Blocks(
        title="🤖 ScionHire AI Labs - Recruitment Agent",
        theme=custom_theme,
        css=custom_css,
    ) as app:
        # Header with custom styling
        gr.HTML("""
        <div class="main-header">
            <h1>🤖 ScionHire AI Labs</h1>
            <p>AI-Powered Recruitment System</p>
            <p style="font-size: 0.95rem; margin-top: 0.5rem;">
                AI-Powered Recruitment System
            </p>
        </div>
        """)
        
        gr.Markdown(
            """
            <div style="text-align: center; color: #4b5563; margin-bottom: 2rem;">
                <p style="font-size: 1.1rem; line-height: 1.6;">
                    Automate CV screening, voice interviews, and candidate management with intelligent AI agents.
                    Streamline your recruitment process and make data-driven hiring decisions.
                </p>
            </div>
            """,
            elem_classes="intro-text"
        )
        
        with gr.Tabs():
            # ================================================================
            # TAB 1: Candidate Application Portal
            # ================================================================
            with gr.Tab("👤 Candidate Portal", elem_classes="tab-nav"):
                gr.Markdown(
                    """
                    <div class="section-header">📝 Submit Your Application</div>
                    """,
                    elem_classes="section-header"
                )
                gr.Markdown(
                    """
                    <div class="info-box">
                        <strong>Welcome to ScionHire AI Labs! 👋</strong><br>
                        We're seeking talented engineers passionate about building intelligent systems!
                        Submit your CV below to start your application journey.
                    </div>
                    """
                )
                
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 👤 Personal Information")
                        full_name = gr.Textbox(
                            label="Full Name",
                            placeholder="Ada Lovelace",
                            info="Enter your full name",
                            container=True
                        )
                        email = gr.Textbox(
                            label="Email Address",
                            placeholder="ada@lovelabs.ai",
                            info="Your email address",
                            container=True
                        )
                        phone = gr.Textbox(
                            label="Phone Number (Optional)",
                            placeholder="+49 170 1234567",
                            info="Your contact number",
                            container=True
                        )
                        
                        gr.Markdown("### 📄 CV Upload")
                        cv_file = gr.File(
                            label="Upload CV",
                            file_types=[".pdf", ".docx"],
                            container=True
                        )
                        gr.Markdown(
                            "<small style='color: #6b7280;'>Accepted formats: PDF or DOCX (Max 10MB)</small>",
                            elem_classes="file-hint"
                        )
                        
                        submit_btn = gr.Button(
                            "📨 Submit Application", 
                            variant="primary",
                            size="lg",
                            scale=1
                        )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 📊 Application Status")
                        application_output = gr.Textbox(
                            label="",
                            lines=12,
                            interactive=False,
                            container=True,
                            show_label=False
                        )
                
                submit_btn.click(
                    fn=submit_application,
                    inputs=[full_name, email, phone, cv_file],
                    outputs=[application_output, gr.Textbox(visible=False)]
                )
                
                gr.Markdown("---")
                gr.Markdown(
                    """
                    <div class="section-header">🔍 Check Application Status</div>
                    """,
                    elem_classes="section-header"
                )
                
                with gr.Row():
                    with gr.Column(scale=3):
                        status_email = gr.Textbox(
                            label="Email Address",
                            placeholder="Enter your email to check status",
                            container=True
                        )
                    with gr.Column(scale=1, min_width=150):
                        check_status_btn = gr.Button(
                            "🔍 Check Status", 
                            variant="secondary",
                            size="lg"
                        )
                
                status_output = gr.Markdown(
                    label="",
                    elem_classes="status-output"
                )
                
                check_status_btn.click(
                    fn=check_application_status,
                    inputs=status_email,
                    outputs=status_output
                )
            
            # ================================================================
            # TAB 2: HR Portal
            # ================================================================
            with gr.Tab("🧑‍💼 HR Portal", elem_classes="tab-nav"):
                gr.Markdown(
                    """
                    <div class="section-header">👥 Candidate Management</div>
                    """,
                    elem_classes="section-header"
                )
                
                with gr.Row():
                    with gr.Column(scale=2):
                        status_filter = gr.Dropdown(
                            label="Filter by Status",
                            choices=["All", "applied", "cv_screened", "cv_passed", "voice_done", "voice_passed", "interview_scheduled"],
                            value="All",
                            info="Filter candidates by application status",
                            container=True
                        )
                    with gr.Column(scale=1, min_width=200):
                        load_btn = gr.Button(
                            "🔄 Load Candidates", 
                            variant="primary",
                            size="lg"
                        )
                
                candidates_output = gr.Markdown(label="Candidates")
                
                load_btn.click(
                    fn=load_candidates,
                    inputs=status_filter,
                    outputs=[candidates_output, gr.Dataframe(visible=False)]
                )
                
                gr.Markdown("---")
                gr.Markdown(
                    """
                    <div class="section-header">🎙️ Voice Screening</div>
                    """,
                    elem_classes="section-header"
                )
                
                with gr.Row():
                    with gr.Column(scale=3):
                        voice_email = gr.Textbox(
                            label="Candidate Email",
                            placeholder="candidate@example.com",
                            container=True
                        )
                    with gr.Column(scale=1, min_width=200):
                        voice_btn = gr.Button(
                            "🎙️ Trigger Voice Screening", 
                            variant="secondary",
                            size="lg"
                        )
                
                voice_output = gr.Textbox(
                    label="Voice Screening Status", 
                    lines=6,
                    container=True
                )
                
                voice_btn.click(
                    fn=trigger_voice_screening,
                    inputs=voice_email,
                    outputs=voice_output
                )
                
                gr.Markdown("---")
                gr.Markdown(
                    """
                    <div class="section-header">📅 Interview Scheduling</div>
                    """,
                    elem_classes="section-header"
                )
                
                with gr.Row():
                    with gr.Column(scale=3):
                        interview_email = gr.Textbox(
                            label="Candidate Email",
                            placeholder="candidate@example.com",
                            container=True
                        )
                    with gr.Column(scale=1, min_width=200):
                        interview_btn = gr.Button(
                            "📅 Schedule Interview", 
                            variant="secondary",
                            size="lg"
                        )
                
                interview_output = gr.Textbox(
                    label="Interview Status", 
                    lines=6,
                    container=True
                )
                
                interview_btn.click(
                    fn=schedule_interview,
                    inputs=interview_email,
                    outputs=interview_output
                )
            
            # ================================================================
            # TAB 3: Supervisor Agent Chat
            # ================================================================
            with gr.Tab("🤖 Supervisor Chat", elem_classes="tab-nav"):
                gr.Markdown(
                    """
                    <div class="section-header">💬 Chat with HR Supervisor Agent</div>
                    """,
                    elem_classes="section-header"
                )
                gr.Markdown(
                    """
                    <div class="info-box">
                        <strong>What can the Supervisor Agent do?</strong><br>
                        • Query candidate information from the database<br>
                        • Screen CVs and provide insights<br>
                        • Schedule interviews automatically<br>
                        • Manage the recruitment pipeline<br>
                        • Answer questions about candidates and processes
                    </div>
                    """
                )
                
                with gr.Row():
                    with gr.Column(scale=3):
                        chat_history = gr.Textbox(
                            label="Chat History",
                            lines=18,
                            interactive=False,
                            placeholder="Click 'Start New Chat' to begin...",
                            container=True,
                            show_copy_button=True
                        )
                        chat_input = gr.Textbox(
                            label="Your Message",
                            placeholder="Ask me anything about candidates or the recruitment process...",
                            lines=2,
                            container=True
                        )
                        
                        with gr.Row():
                            send_btn = gr.Button(
                                "💬 Send Message", 
                                variant="primary",
                                size="lg",
                                scale=2
                            )
                            new_chat_btn = gr.Button(
                                "🆕 New Chat", 
                                variant="secondary",
                                size="lg",
                                scale=1
                            )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 📊 Statistics")
                        token_info = gr.Textbox(
                            label="Token Usage",
                            lines=4,
                            interactive=False,
                            container=True
                        )
                        gr.Markdown(
                            """
                            <div class="info-box" style="font-size: 0.9rem;">
                                <strong>💡 Tip:</strong> The agent maintains context across messages. 
                                Start a new chat to reset the conversation.
                            </div>
                            """
                        )
                
                # Initialize chat on load
                app.load(
                    fn=init_chat,
                    outputs=[chat_history, token_info]
                )
                
                # Send message
                send_btn.click(
                    fn=chat_with_supervisor,
                    inputs=[chat_input, chat_history],
                    outputs=[chat_history, token_info]
                ).then(
                    fn=lambda: "",  # Clear input
                    outputs=chat_input
                )
                
                # New chat
                new_chat_btn.click(
                    fn=init_chat,
                    outputs=[chat_history, token_info]
                )
        
        # Footer removed
    
    return app


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )

