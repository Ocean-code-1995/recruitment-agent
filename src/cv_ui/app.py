"""
CV Upload UI for Job Applications.

Connects to the CV Upload API.
Run with: streamlit run src/cv_ui/app.py

In Docker, set CV_UPLOAD_API_URL environment variable.
Locally, defaults to http://localhost:8080/api/v1/cv
"""

import streamlit as st
from src.sdk import CVUploadClient

# Initialize SDK client
client = CVUploadClient()

st.set_page_config(page_title="AI Engineer Job Portal", page_icon="🤖", layout="centered")

# --- UI Header ---
st.title("🤖 AI Engineer Job Application Portal")
st.markdown(
    """
    Welcome to **ScionHire AI Labs** 👋  
    We're seeking talented engineers passionate about building intelligent systems!  
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
            with st.spinner("📤 Submitting your application..."):
                response = client.submit(
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    cv_file=uploaded_file,
                    filename=uploaded_file.name,
                )
            
            if response.success:
                st.success(f"✅ {response.message}")
                st.info("Your application has been recorded. You will receive updates soon.")

                with st.expander("📬 Submitted Info"):
                    st.json({
                        "full_name": response.candidate_name,
                        "email": response.email,
                            "phone": phone,
                        "cv_file_path": response.cv_file_path,
                            "position": "AI Engineer",
                    })
            
            elif response.already_exists:
                st.warning(
                    f"⚠️ {response.message} "
                    "Please wait for review."
                )
            else:
                st.error(f"❌ {response.message}")
                
        except ValueError as e:
            st.error(f"❌ {str(e)}")
        except Exception as e:
            st.error(f"❌ Failed to submit application. Is the API running?\n\nError: {e}")
