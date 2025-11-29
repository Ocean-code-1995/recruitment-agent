"""
Gradio Frontend for Recruitment Agent - Hugging Face Spaces Deployment
Requires Gradio 6.0+
"""

import os
import gradio as gr
from typing import Optional, Tuple, Dict, Any
import sys
from pathlib import Path
from uuid import uuid4

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.sdk import SupervisorClient, DatabaseClient, CVUploadClient
    SDK_AVAILABLE = True
except ImportError as e:
    SDK_AVAILABLE = False
    try:
        alt_root = Path(__file__).parent.parent.parent.parent
        if str(alt_root) not in sys.path:
            sys.path.insert(0, str(alt_root))
        from src.sdk import SupervisorClient, DatabaseClient, CVUploadClient
        SDK_AVAILABLE = True
    except Exception:
        pass

# ============================================================================
# CONFIGURATION
# ============================================================================

def get_api_url(service: str) -> str:
    env_map = {
        "supervisor": "SUPERVISOR_API_URL",
        "db": "DATABASE_API_URL",
        "database": "DATABASE_API_URL",
        "cv": "CV_UPLOAD_API_URL",
        "voice-screener": "VOICE_SCREENER_API_URL",
    }
    path_map = {
        "supervisor": "supervisor",
        "db": "db",
        "database": "db",
        "cv": "cv",
        "voice-screener": "voice-screener",
    }
    env_var = env_map.get(service, f"{service.upper()}_API_URL")
    api_url = os.getenv(env_var)
    if api_url:
        return api_url
    api_path = path_map.get(service, service)
    space_id = os.getenv("SPACE_ID")
    if space_id:
        return f"https://{space_id}.hf.space/api/v1/{api_path}"
    return f"http://localhost:8080/api/v1/{api_path}"

# ============================================================================
# CANDIDATE APPLICATION PORTAL
# ============================================================================

def submit_application(full_name: str, email: str, phone: str, cv_file, session_state: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
    if not SDK_AVAILABLE:
        return "❌ SDK not available. Please check backend connection.", ensure_session(session_state)
    session = ensure_session(session_state)
    if not full_name or not email:
        return "❌ Full name and email are required.", session
    if not cv_file:
        return "❌ Please upload your CV (PDF or DOCX).", session
    try:
        client = CVUploadClient(base_url=get_api_url("cv"), session_id=session["session_id"])
        file_path = cv_file.name if hasattr(cv_file, 'name') else str(cv_file)
        filename = Path(file_path).name
        with open(file_path, 'rb') as f:
            response = client.submit(full_name=full_name, email=email, phone=phone or "", cv_file=f, filename=filename)
        if response.success:
            return f"✅ {response.message}\n\nYour application has been recorded.", session
        elif response.already_exists:
            return f"⚠️ {response.message}\n\nPlease wait for review.", session
        return f"❌ {response.message}", session
    except Exception as e:
        return f"❌ Failed to submit application: {str(e)}", session

def check_application_status(email: str, session_state: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
    if not SDK_AVAILABLE:
        return "❌ SDK not available.", ensure_session(session_state)
    session = ensure_session(session_state)
    if not email:
        return "❌ Please enter your email address.", session
    try:
        client = DatabaseClient(base_url=get_api_url("database"), session_id=session["session_id"])
        response = client.get_candidate_by_email(email, include_relations=True)
        if response.success and response.data:
            c = response.data
            info = f"**Status:** {c.get('status', 'unknown')}\n\n"
            info += f"**Applied:** {c.get('created_at', 'N/A')}\n\n"
            if c.get('cv_screening_results'):
                score = c['cv_screening_results'][0].get('overall_fit_score', 0)
                info += f"**CV Score:** {score * 100:.1f}%\n\n"
            if c.get('voice_screening_results'):
                info += "**Voice Screening:** ✅ Completed\n\n"
            if c.get('interview_scheduling'):
                info += f"**Interview:** {c['interview_scheduling'][0].get('status', 'Scheduled')}\n\n"
            if c.get('final_decision'):
                info += f"**Decision:** {c['final_decision'].get('decision', 'Pending')}"
            return info, session
        return f"❌ No application found for {email}.", session
    except Exception as e:
        return f"❌ Error: {str(e)}", session

# ============================================================================
# HR PORTAL
# ============================================================================

def load_candidates(status_filter: Optional[str] = None, session_state: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
    if not SDK_AVAILABLE:
        return "❌ SDK not available.", ensure_session(session_state)
    session = ensure_session(session_state)
    try:
        client = DatabaseClient(base_url=get_api_url("database"), session_id=session["session_id"])
        response = client.get_candidates(status=status_filter if status_filter != "All" else None, limit=100, include_relations=True)
        if response.success and response.data:
            candidates = response.data
            if not candidates:
                return "No candidates found.", session
            table = "| Name | Email | Status | Applied | Voice |\n|------|-------|--------|---------|-------|\n"
            for c in candidates:
                name = c.get('full_name', 'Unknown')
                email = c.get('email', 'N/A')
                status = c.get('status', 'unknown')
                applied = str(c.get('created_at', 'N/A'))[:10]
                voice = "✅" if c.get('voice_screening_results') else "❌"
                table += f"| {name} | {email} | {status} | {applied} | {voice} |\n"
            return f"**Found {len(candidates)} candidate(s)**\n\n{table}", session
        return "No candidates found.", session
    except Exception as e:
        return f"❌ Error: {str(e)}", session

def trigger_voice_screening(candidate_email: str, session_state: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
    if not SDK_AVAILABLE:
        return "❌ SDK not available.", ensure_session(session_state)
    session = ensure_session(session_state)
    if not candidate_email:
        return "❌ Please enter candidate email.", session
    try:
        client = SupervisorClient(base_url=get_api_url("supervisor"), session_id=session["session_id"])
        thread_id = client.new_chat()
        response = client.chat(message=f"Please trigger voice screening for candidate with email {candidate_email}", thread_id=thread_id)
        token_info = f"\n\n📊 Tokens: {response.token_count:,}" if response.token_count else ""
        return f"✅ Voice screening triggered!\n\n{response.content}{token_info}", session
    except Exception as e:
        return f"❌ Failed: {str(e)}", session

def schedule_interview(candidate_email: str, session_state: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
    if not SDK_AVAILABLE:
        return "❌ SDK not available.", ensure_session(session_state)
    session = ensure_session(session_state)
    if not candidate_email:
        return "❌ Please enter candidate email.", session
    try:
        client = SupervisorClient(base_url=get_api_url("supervisor"), session_id=session["session_id"])
        thread_id = client.new_chat()
        response = client.chat(message=f"Please schedule an interview for candidate with email {candidate_email}", thread_id=thread_id)
        token_info = f"\n\n📊 Tokens: {response.token_count:,}" if response.token_count else ""
        return f"✅ Interview scheduling initiated!\n\n{response.content}{token_info}", session
    except Exception as e:
        return f"❌ Failed: {str(e)}", session

# ============================================================================
# SUPERVISOR AGENT CHAT (per-user state via session dict)
# ============================================================================

def ensure_session(state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Ensure a per-user session dict exists with a unique session_id."""
    if state is None:
        state = {}
    if not state.get("session_id"):
        state["session_id"] = uuid4().hex
    state.setdefault("thread_id", None)
    state.setdefault("messages", [])
    state.setdefault("total_tokens", 0)
    return state

def format_chat_history(messages: list) -> str:
    if not messages:
        return ""
    formatted = []
    for role, content in messages:
        if role == "user":
            formatted.append(f"👤 **You**\n\n{content}")
        else:
            formatted.append(f"🤖 **Assistant**\n\n{content}")
    return "\n\n---\n\n".join(formatted)

def init_chat(session_state: Optional[Dict[str, Any]] = None) -> Tuple[str, str, Dict[str, Any]]:
    if not SDK_AVAILABLE:
        return "❌ SDK not available.", "📊 Tokens: 0", ensure_session(session_state)
    session = ensure_session(session_state)
    try:
        client = SupervisorClient(base_url=get_api_url("supervisor"), session_id=session["session_id"])
        thread_id = client.new_chat()
        session["thread_id"] = thread_id
        session["messages"] = []
        session["total_tokens"] = 0
        welcome = """Hello! I'm the HR Supervisor Agent. I can help you with:

- **Querying** candidate information
- **Screening** CVs and providing insights
- **Scheduling** interviews automatically
- **Managing** the recruitment pipeline

What would you like to know?"""
        session["messages"].append(("assistant", welcome))
        return format_chat_history(session["messages"]), "📊 Tokens: 0", session
    except Exception as e:
        return f"❌ Failed to initialize: {str(e)}", "📊 Tokens: 0", session

def chat_with_supervisor(message: str, history: str, session_state: Optional[Dict[str, Any]]) -> Tuple[str, str, str, Dict[str, Any]]:
    if not SDK_AVAILABLE:
        return history, "❌ SDK not available.", "", ensure_session(session_state)
    session = ensure_session(session_state)
    if not message.strip():
        return history, f"📊 Tokens: {session['total_tokens']:,}", "", session
    if not session.get("thread_id"):
        _, _, session = init_chat(session)
    try:
        client = SupervisorClient(base_url=get_api_url("supervisor"), session_id=session["session_id"])
        session["messages"].append(("user", message))
        response = client.chat(message=message, thread_id=session["thread_id"])
        session["messages"].append(("assistant", response.content))
        session["total_tokens"] += response.token_count or 0
        return format_chat_history(session["messages"]), f"📊 Tokens: {session['total_tokens']:,}", "", session
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        session["messages"].append(("assistant", error_msg))
        return format_chat_history(session["messages"]), f"📊 Tokens: {session['total_tokens']:,}", "", session

# ============================================================================
# CUSTOM CSS
# ============================================================================

CUSTOM_CSS = """
/* =====================================================
   FORCE LIGHT MODE - Aggressive overrides for Gradio 6
   ===================================================== */

/* Root level - override everything */
:root {
    --body-background-fill: #ffffff !important;
    --background-fill-primary: #ffffff !important;
    --background-fill-secondary: #f8fafc !important;
    --block-background-fill: #ffffff !important;
    --input-background-fill: #ffffff !important;
    --body-text-color: #1e293b !important;
    --block-label-text-color: #1e293b !important;
    --block-title-text-color: #1e293b !important;
    --color-text-body: #1e293b !important;
    --text-color: #1e293b !important;
    color-scheme: light !important;
}

/* Target the main gradio wrapper */
#__next, #root, #app, main, .main, 
gradio-app, .gradio-app,
[class*="gradio"], [id*="gradio"] {
    background-color: #ffffff !important;
    background: #ffffff !important;
    color: #1e293b !important;
}

/* Dark mode class overrides */
.dark, [data-theme="dark"], html.dark, body.dark,
.dark *, [data-theme="dark"] * {
    background-color: #ffffff !important;
    color: #1e293b !important;
}

html, body {
    background-color: #ffffff !important;
    background: #ffffff !important;
    color: #1e293b !important;
}

.gradio-container {
    background-color: #ffffff !important;
    background: #ffffff !important;
    color: #1e293b !important;
}

/* Wrap everything */
.wrap, .wrapper, .contain, 
[class*="wrap"], [class*="contain"] {
    background-color: #ffffff !important;
    background: #ffffff !important;
}

/* ALL text elements - force dark text */
*, *::before, *::after {
    --tw-text-opacity: 1 !important;
}

h1, h2, h3, h4, h5, h6, 
p, span, div, label, 
li, td, th, a:not(.main-header a),
strong, b, em, i, u,
.text, [class*="text"] {
    color: #1e293b !important;
}

/* Prose/Markdown specific */
.prose, .prose *, 
.markdown, .markdown *,
[class*="prose"], [class*="markdown"],
.md, .md * {
    color: #1e293b !important;
    background-color: transparent !important;
}

/* Strong/bold text emphasis */
strong, b, .font-bold, .font-semibold {
    color: #0f172a !important;
    font-weight: 600 !important;
}

/* =====================================================
   FORM ELEMENTS
   ===================================================== */

input, textarea, select, option {
    background-color: #ffffff !important;
    background: #ffffff !important;
    color: #1e293b !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 6px !important;
}

input::placeholder, textarea::placeholder {
    color: #94a3b8 !important;
    opacity: 1 !important;
}

input:focus, textarea:focus, select:focus {
    border-color: #2563eb !important;
    outline: none !important;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
}

/* Labels */
label, .label, [class*="label"] {
    color: #1e293b !important;
    font-weight: 500 !important;
}

/* =====================================================
   BLOCKS AND CONTAINERS  
   ===================================================== */

.block, .form, .container, .panel, .card, .box,
[class*="block"], [class*="panel"], [class*="card"],
[class*="svelte-"] {
    background-color: #ffffff !important;
    background: #ffffff !important;
}

/* =====================================================
   HEADER WITH GRADIENT (WHITE TEXT)
   ===================================================== */

.main-header {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    padding: 2rem !important;
    border-radius: 12px !important;
    margin-bottom: 1.5rem !important;
    text-align: center !important;
}

.main-header h1,
.main-header p,
.main-header span,
.main-header * {
    color: white !important;
}

.main-header h1 { 
    font-size: 2.5rem !important; 
    margin: 0 !important; 
    font-weight: 700 !important; 
}

.main-header p { 
    margin: 0.5rem 0 0 0 !important; 
    font-size: 1.1rem !important;
    opacity: 0.95 !important;
}

/* =====================================================
   INFO BOXES (BLUE THEMED)
   ===================================================== */

.info-box {
    background: #eff6ff !important;
    border-left: 4px solid #2563eb !important;
    padding: 1rem !important;
    border-radius: 0 8px 8px 0 !important;
    margin: 1rem 0 !important;
}

.info-box, .info-box * {
    color: #1e40af !important;
}

/* =====================================================
   CHAT DISPLAY
   ===================================================== */

.chat-display {
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    background-color: #ffffff !important;
    background: #ffffff !important;
    min-height: 400px !important;
    max-height: 500px !important;
    overflow-y: auto !important;
}

.chat-display, .chat-display *, 
.chat-display p, .chat-display span,
.chat-display strong, .chat-display li {
    color: #1e293b !important;
}

/* =====================================================
   STATS BOX
   ===================================================== */

.stats-box {
    background-color: #f1f5f9 !important;
    background: #f1f5f9 !important;
    border-radius: 8px !important;
    padding: 1rem !important;
    text-align: center !important;
}

.stats-box, .stats-box * {
    color: #475569 !important;
    font-weight: 600 !important;
}

/* =====================================================
   BUTTONS
   ===================================================== */

/* Primary buttons - blue bg, white text */
button.primary, 
.primary,
button[class*="primary"],
[class*="primary"] button,
button[variant="primary"] {
    background-color: #2563eb !important;
    background: #2563eb !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
}

button.primary:hover,
.primary:hover,
button[class*="primary"]:hover {
    background-color: #1d4ed8 !important;
    background: #1d4ed8 !important;
}

button.primary *,
.primary *,
button[class*="primary"] * {
    color: white !important;
}

/* Secondary buttons */
button.secondary,
.secondary,
button[class*="secondary"],
button[variant="secondary"] {
    background-color: #f1f5f9 !important;
    background: #f1f5f9 !important;
    color: #1e293b !important;
    border: 1px solid #cbd5e1 !important;
}

button.secondary *,
.secondary *,
button[class*="secondary"] * {
    color: #1e293b !important;
}

/* =====================================================
   TABS
   ===================================================== */

button[role="tab"],
[role="tab"],
.tab, .tabs button {
    color: #1e293b !important;
    background-color: transparent !important;
}

button[role="tab"][aria-selected="true"],
[role="tab"][aria-selected="true"],
.tab.selected, .tab.active {
    color: #2563eb !important;
    border-bottom: 2px solid #2563eb !important;
}

.tab-content, .tabs-content, [role="tabpanel"] {
    background-color: #ffffff !important;
}

/* =====================================================
   TABLES
   ===================================================== */

table {
    background-color: #ffffff !important;
}

th, td {
    background-color: #ffffff !important;
    color: #1e293b !important;
    border-color: #e2e8f0 !important;
}

th {
    background-color: #f8fafc !important;
    font-weight: 600 !important;
}

/* =====================================================
   DROPDOWN / SELECT
   ===================================================== */

select, 
.dropdown,
[data-testid="dropdown"],
[class*="dropdown"] {
    background-color: #ffffff !important;
    background: #ffffff !important;
    color: #1e293b !important;
    border: 1px solid #cbd5e1 !important;
}

/* Dropdown options */
option {
    background-color: #ffffff !important;
    color: #1e293b !important;
}

/* =====================================================
   FILE UPLOAD
   ===================================================== */

[class*="file"],
[class*="upload"],
.upload-area,
.dropzone,
[class*="drop"] {
    background-color: #f8fafc !important;
    background: #f8fafc !important;
    border: 2px dashed #cbd5e1 !important;
    border-radius: 8px !important;
}

[class*="file"] *,
[class*="upload"] *,
.dropzone * {
    color: #64748b !important;
}

/* =====================================================
   MISC
   ===================================================== */

hr {
    border-color: #e2e8f0 !important;
}

/* Links (except in header) */
a:not(.main-header a) {
    color: #2563eb !important;
}

a:not(.main-header a):hover {
    color: #1d4ed8 !important;
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}

/* =====================================================
   AUTO-SCROLL FOR CHAT
   ===================================================== */

.auto-scroll {
    overflow-y: auto !important;
    scroll-behavior: smooth !important;
}

/* Remove scrollbar from voice and interview output sections */
.no-scroll-output,
.no-scroll-output *,
[class*="no-scroll-output"] {
    overflow: visible !important;
    overflow-y: visible !important;
    overflow-x: visible !important;
    max-height: none !important;
    height: auto !important;
}

/* Ensure processing loaders are visible */
.no-scroll-output .gradio-loading,
.no-scroll-output [class*="loading"],
.no-scroll-output [class*="spinner"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}
"""

# ============================================================================
# THEME - Use Default theme as base (lighter than Soft)
# ============================================================================

try:
    THEME = gr.themes.Default(
        primary_hue="blue",
        secondary_hue="slate", 
        neutral_hue="slate",
    )
except Exception as e:
    print(f"Theme creation failed: {e}, using string theme")
    THEME = "default"

# ============================================================================
# GRADIO INTERFACE - Gradio 6+ Compatible
# In Gradio 6, theme and css are passed to launch(), not Blocks()
# ============================================================================

def create_app():
    # In Gradio 6, gr.Blocks() takes no theme/css args - they go to launch()
    with gr.Blocks() as app:
        # Force light mode via JavaScript - runs on load and observes for changes
        gr.HTML("""
        <script>
            // Force light mode immediately
            function forceLightMode() {
                document.documentElement.classList.remove('dark');
                document.documentElement.setAttribute('data-theme', 'light');
                document.documentElement.style.colorScheme = 'light';
                document.body.classList.remove('dark');
                document.body.style.backgroundColor = '#ffffff';
                document.body.style.color = '#1e293b';
                
                // Remove dark class from all elements
                document.querySelectorAll('.dark, [data-theme="dark"]').forEach(el => {
                    el.classList.remove('dark');
                    el.setAttribute('data-theme', 'light');
                });
            }
            
            // Run immediately
            forceLightMode();
            
            // Run when DOM is ready
            document.addEventListener('DOMContentLoaded', forceLightMode);
            
            // Observe for any dark mode changes
            const observer = new MutationObserver(forceLightMode);
            observer.observe(document.documentElement, { 
                attributes: true, 
                attributeFilter: ['class', 'data-theme'] 
            });
            
            // Also run after a short delay to catch late changes
            setTimeout(forceLightMode, 100);
            setTimeout(forceLightMode, 500);
            setTimeout(forceLightMode, 1000);
        </script>
        <div class="main-header">
            <h1>🤖 ScionHire AI Labs</h1>
            <p>AI-Powered Recruitment System</p>
        </div>
        """)

        # Per-user session state (persists across interactions)
        session_state = gr.State(value=None)
        
        with gr.Tabs():
            # ============================================================
            # TAB 1: Candidate Portal
            # ============================================================
            with gr.Tab("👤 Candidate Portal"):
                gr.Markdown("## 📝 Submit Your Application")
                gr.HTML('<div class="info-box"><strong>Welcome!</strong> We\'re seeking talented engineers. Submit your CV below to start your application.</div>')
                
                with gr.Row():
                    with gr.Column():
                        full_name = gr.Textbox(label="Full Name", placeholder="Ada Lovelace")
                        email = gr.Textbox(label="Email", placeholder="ada@example.com")
                        phone = gr.Textbox(label="Phone (Optional)", placeholder="+1 234 567 8900")
                        cv_file = gr.File(label="Upload CV (PDF or DOCX)", file_types=[".pdf", ".docx"])
                        submit_btn = gr.Button("📨 Submit Application", variant="primary", size="lg")
                    
                    with gr.Column():
                        gr.Markdown("### 📊 Application Result")
                        application_output = gr.Markdown()
                
                submit_btn.click(
                    fn=submit_application,
                    inputs=[full_name, email, phone, cv_file, session_state],
                    outputs=[application_output, session_state]
                )
                
                gr.Markdown("---")
                gr.Markdown("## 🔍 Check Application Status")
                
                with gr.Row():
                    status_email = gr.Textbox(label="Email", placeholder="Enter your email to check status", scale=3)
                    check_btn = gr.Button("🔍 Check Status", variant="secondary", scale=1)
                
                status_output = gr.Markdown()
                check_btn.click(fn=check_application_status, inputs=[status_email, session_state], outputs=[status_output, session_state])
            
            # ============================================================
            # TAB 2: HR Portal
            # ============================================================
            with gr.Tab("🧑‍💼 HR Portal"):
                gr.Markdown("## 👥 Candidate Management")
                
                with gr.Row():
                    status_filter = gr.Dropdown(
                        label="Filter by Status",
                        choices=["All", "applied", "cv_screened", "cv_passed", "voice_done", "voice_passed", "interview_scheduled"],
                        value="All",
                        scale=2
                    )
                    load_btn = gr.Button("🔄 Load Candidates", variant="primary", scale=1)
                
                candidates_output = gr.Markdown()
                load_btn.click(fn=load_candidates, inputs=[status_filter, session_state], outputs=[candidates_output, session_state])
                
                gr.Markdown("---")
                gr.Markdown("## 🎙️ Voice Screening")
                
                with gr.Row():
                    voice_email = gr.Textbox(label="Candidate Email", placeholder="candidate@example.com", scale=3)
                    voice_btn = gr.Button("🎙️ Trigger Screening", variant="secondary", scale=1)
                
                voice_output = gr.Markdown(elem_classes=["no-scroll-output"])
                voice_btn.click(fn=trigger_voice_screening, inputs=[voice_email, session_state], outputs=[voice_output, session_state])
                
                gr.Markdown("---")
                gr.Markdown("## 📅 Interview Scheduling")
                
                with gr.Row():
                    interview_email = gr.Textbox(label="Candidate Email", placeholder="candidate@example.com", scale=3)
                    interview_btn = gr.Button("📅 Schedule Interview", variant="secondary", scale=1)
                
                interview_output = gr.Markdown(elem_classes=["no-scroll-output"])
                interview_btn.click(fn=schedule_interview, inputs=[interview_email, session_state], outputs=[interview_output, session_state])
            
            # ============================================================
            # TAB 3: Supervisor Chat
            # ============================================================
            with gr.Tab("🤖 Supervisor Chat"):
                gr.Markdown("## 💬 Chat with HR Supervisor Agent")
                gr.HTML('''<div class="info-box">
                    <strong>Capabilities:</strong> Query candidates • Screen CVs • Schedule interviews • Manage recruitment pipeline
                </div>''')
                
                with gr.Row():
                    with gr.Column(scale=3):
                        chat_history = gr.Markdown(elem_classes=["chat-display", "auto-scroll"])
                        chat_input = gr.Textbox(
                            label="Your Message",
                            placeholder="Ask about candidates, screening, interviews...",
                            lines=2
                        )
                        with gr.Row():
                            send_btn = gr.Button("💬 Send Message", variant="primary", scale=2)
                            new_chat_btn = gr.Button("🆕 New Chat", variant="secondary", scale=1)
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 📊 Session Stats")
                        token_info = gr.Markdown("📊 Tokens: 0", elem_classes=["stats-box"])
                        gr.Markdown("""
**💡 Tips:**
- Ask about specific candidates by email
- Request CV screening summaries
- Schedule interviews directly
- Get pipeline statistics
                        """)
                
                # Initialize chat on load with auto-scroll
                def init_chat_with_scroll(state):
                    hist, tokens, new_state = init_chat(state)
                    return hist, tokens, new_state
                
                app.load(
                    fn=init_chat_with_scroll, 
                    inputs=[session_state],
                    outputs=[chat_history, token_info, session_state]
                ).then(
                    fn=None,
                    js="""
                    () => {
                        const chatDisplay = document.querySelector('.auto-scroll');
                        if (chatDisplay) {
                            setTimeout(() => {
                                chatDisplay.scrollTop = chatDisplay.scrollHeight;
                            }, 100);
                        }
                    }
                    """
                )
                
                # Send message with auto-scroll
                send_btn.click(
                    fn=chat_with_supervisor,
                    inputs=[chat_input, chat_history, session_state],
                    outputs=[chat_history, token_info, chat_input, session_state]
                ).then(
                    fn=None,
                    js="""
                    () => {
                        // Auto-scroll chat history to bottom
                        const chatDisplay = document.querySelector('.auto-scroll');
                        if (chatDisplay) {
                            setTimeout(() => {
                                chatDisplay.scrollTop = chatDisplay.scrollHeight;
                            }, 100);
                        }
                    }
                    """
                )
                
                # New chat with auto-scroll
                new_chat_btn.click(
                    fn=init_chat, 
                    inputs=[session_state],
                    outputs=[chat_history, token_info, session_state]
                ).then(
                    fn=None,
                    js="""
                    () => {
                        const chatDisplay = document.querySelector('.auto-scroll');
                        if (chatDisplay) {
                            setTimeout(() => {
                                chatDisplay.scrollTop = chatDisplay.scrollHeight;
                            }, 100);
                        }
                    }
                    """
                )
        
        gr.Markdown("---")
        gr.Markdown("<center><small>Built with ❤️ for the MCP Hackathon</small></center>")
    
    return app

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print(f"Gradio version: {gr.__version__}")
    app = create_app()
    
    # Honor PORT if provided by hosting platform (e.g., Hugging Face Spaces)
    # Some platforms inject quotes around PORT (e.g., "\"7860\""); strip them.
    raw_port = os.getenv("PORT", "7860").strip().strip("\"'")
    port = int(raw_port)
    
    # In Gradio 6, theme and css are passed to launch(), not Blocks()
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        theme=THEME,
        css=CUSTOM_CSS,
        # Try to force light mode if available
        # dark_mode=False,  # Uncomment if supported in your version
    )
