import os
import uuid
from pathlib import Path
import streamlit as st
from datetime import datetime

from src.cv_ui.utils.register_candidate import register_candidate
from src.cv_ui.utils.save_cv import save_cv
from src.cv_ui.utils.pdf_to_markdown import pdf_to_markdown
from src.cv_ui.utils.parced_cv_path import update_parsed_cv_path

# --- Configuration ---
UPLOAD_DIR = Path(os.getenv("CV_UPLOAD_PATH", "src/database/cvs/uploads"))
PARSED_DIR = Path(os.getenv("CV_PARSED_PATH", "src/database/cvs/parsed"))
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PARSED_DIR, exist_ok=True)

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
        # ~~~~~~~~~~~~~~~~process the application~~~~~~~~~~~~~~~
        try:
            # 1️⃣ Save CV locally
            file_path = save_cv(uploaded_file, uploaded_file.name)
            file_path = Path(file_path)

            # 2️⃣ Register candidate
            register_candidate(full_name, email, phone, str(file_path))

            # 3️⃣ Parse automatically → save in parsed/
            st.info("🧠 Parsing your CV, please wait...")
            pdf_to_markdown(
                input_path=file_path,
                output_path=PARSED_DIR,
                model="gpt-4.1-mini",
            )
            # 4️⃣ Update parsed CV path in DB
            parsed_path = PARSED_DIR / (file_path.stem + ".txt")
            update_parsed_cv_path(email, str(parsed_path))
        
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