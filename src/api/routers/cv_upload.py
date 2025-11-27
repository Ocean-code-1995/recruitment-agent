"""
CV Upload Router.

Handles CV submission and candidate registration.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from src.database.candidates import register_candidate, update_parsed_cv_path
from src.database.cvs import save_cv
from src.doc_parser import pdf_to_markdown


router = APIRouter()

# Configuration
UPLOAD_DIR = Path(os.getenv("CV_UPLOAD_PATH", "src/database/cvs/uploads"))
PARSED_DIR = Path(os.getenv("CV_PARSED_PATH", "src/database/cvs/parsed"))
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PARSED_DIR, exist_ok=True)


# ==================================================================================
# RESPONSE MODELS
# ==================================================================================

class SubmitResponse(BaseModel):
    """Response model for CV submission."""
    success: bool = Field(..., description="Whether the submission was successful")
    message: str = Field(..., description="Status message")
    candidate_name: str = Field(default="", description="Name of the candidate")
    email: str = Field(default="", description="Email of the candidate")
    cv_file_path: str = Field(default="", description="Path where CV was saved")
    already_exists: bool = Field(default=False, description="True if candidate already applied")


# ==================================================================================
# ENDPOINTS
# ==================================================================================

@router.post("/submit", response_model=SubmitResponse)
async def submit_application(
    full_name: str = Form(..., description="Candidate's full name"),
    email: str = Form(..., description="Candidate's email address"),
    phone: str = Form(default="", description="Candidate's phone number"),
    cv_file: UploadFile = File(..., description="CV file (PDF or DOCX)")
) -> SubmitResponse:
    """
    Submit a job application with CV.
    
    This endpoint:
    1. Saves the uploaded CV file
    2. Registers the candidate in the database
    3. Parses the CV to markdown for AI processing
    4. Updates the parsed CV path in the database
    
    Returns success status and details about the submission.
    """
    # Validate file type
    allowed_extensions = {".pdf", ".docx"}
    file_ext = Path(cv_file.filename or "").suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        # 1. Save CV locally
        file_path = save_cv(cv_file.file, cv_file.filename or "cv.pdf", candidate_name=full_name)
        file_path = Path(file_path)
        
        # 2. Register candidate in DB
        success = register_candidate(full_name, email, phone, str(file_path))
        
        if not success:
            return SubmitResponse(
                success=False,
                message=f"An application with email '{email}' already exists. You can only apply once.",
                candidate_name=full_name,
                email=email,
                already_exists=True,
            )
        
        # 3. Parse CV to markdown
        pdf_to_markdown(
            input_path=file_path,
            output_path=PARSED_DIR,
            model="gpt-4.1-mini",
        )
        
        # 4. Update parsed CV path in DB
        parsed_path = PARSED_DIR / (file_path.stem + ".txt")
        update_parsed_cv_path(email, str(parsed_path))
        
        return SubmitResponse(
            success=True,
            message=f"Application submitted successfully for {full_name}!",
            candidate_name=full_name,
            email=email,
            cv_file_path=str(file_path),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process application: {str(e)}"
        )


@router.get("/health")
async def cv_upload_health():
    """Health check for CV upload router."""
    return {"status": "healthy", "service": "cv_upload"}

