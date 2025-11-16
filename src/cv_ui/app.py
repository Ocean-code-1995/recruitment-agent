import os
import uuid
import streamlit as st
from datetime import datetime

from src.database.candidates.client import SessionLocal
from src.database.candidates.models import Candidate
from src.cv_ui.utils.register_candidate import register_candidate
from src.cv_ui.utils.save_cv import save_cv

# --- Configuration ---
UPLOAD_DIR = os.getenv("CV_UPLOAD_PATH", "src/database/cvs/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="AI Engineer Job Portal", page_icon="🤖", layout="centered")

# --- UI Header ---
st.title("🤖 AI Engineer Job Application Portal")
st.markdown(
    """
    Welcome to **ScionHire AI Labs** 👋  
    We’re seeking talented engineers passionate about building intelligent systems!  
    Please submit your CV below to apply for the **AI Engineer** position.
    """
)

# --- Job Description (Static for now) ---
with st.expander("📄 View Job Description"):
    st.markdown(
        """
        ### 🧠 Position: AI Engineer  
        **Location:** Remote / Wiesbaden HQ  
        **About the Role:**  
        Join our AI R&D team to develop, fine-tune, and deploy ML models for production.  
        You will work on projects involving LLMs, LangGraph agents, and context engineering.  

        **Requirements:**  
        - Proficiency in Python & modern AI frameworks (PyTorch, LangChain, etc.)  
        - Solid understanding of NLP and ML pipelines  
        - Experience deploying models or building intelligent systems  
        - Strong communication and teamwork skills  
        """
    )

st.markdown("---")

# --- Candidate Form ---
with st.form("application_form"):
    full_name = st.text_input("Full Name", placeholder="Ada Lovelace")
    email = st.text_input("Email Address", placeholder="ada@lovelabs.ai")
    phone = st.text_input("Phone Number", placeholder="+49 170 1234567")
    uploaded_file = st.file_uploader("Upload Your CV (PDF or DOCX)", type=["pdf", "docx"])
    submitted = st.form_submit_button("📨 Submit Application")

# --- Handle Submission ---
if submitted:
    if not uploaded_file:
        st.error("Please upload your CV before submitting.")
    elif not (full_name and email):
        st.error("Full name and email are required.")
    else:
        try:
            # Save CV using shared helper
            file_path = save_cv(uploaded_file, uploaded_file.name)

            # Register candidate in DB
            register_candidate(full_name, email, phone, file_path, )

            st.success(f"✅ Application submitted successfully for {full_name}!")
            st.info("Your application has been recorded. You will receive updates soon.")

            with st.expander("📬 Submitted Info"):
                st.json(
                    {
                        "full_name": full_name,
                        "email": email,
                        "phone": phone,
                        "cv_file_path": file_path,
                        "position": "AI Engineer",
                    }
                )

        except Exception as e:
            st.error(f"❌ Failed to save your application: {e}")