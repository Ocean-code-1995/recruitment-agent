"""
CV Upload API Client.

A client for submitting job applications with CV uploads.
"""

import os
from dataclasses import dataclass
from typing import Optional, BinaryIO
import requests


@dataclass
class SubmitResponse:
    """Response from a CV submission."""
    success: bool
    message: str
    candidate_name: str = ""
    email: str = ""
    cv_file_path: str = ""
    already_exists: bool = False


class CVUploadClient:
    """
    Client for the CV Upload API.
    
    Usage:
        client = CVUploadClient()
        
        # Submit application
        with open("my_cv.pdf", "rb") as f:
            response = client.submit(
                full_name="Ada Lovelace",
                email="ada@example.com",
                phone="+49 123 456789",
                cv_file=f,
                filename="my_cv.pdf"
            )
        
        if response.success:
            print(f"Application submitted: {response.message}")
        elif response.already_exists:
            print("You already applied!")
        else:
            print(f"Error: {response.message}")
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the CV Upload client.
        
        Args:
            base_url: API base URL. Defaults to CV_UPLOAD_API_URL env var
                      or http://localhost:8080/api/v1/cv
        """
        self.base_url = base_url or os.getenv(
            "CV_UPLOAD_API_URL",
            "http://localhost:8080/api/v1/cv"
        )
    
    def submit(
        self,
        full_name: str,
        email: str,
        cv_file: BinaryIO,
        filename: str,
        phone: str = "",
        timeout: int = 120
    ) -> SubmitResponse:
        """
        Submit a job application with CV.
        
        Args:
            full_name: Candidate's full name
            email: Candidate's email address
            cv_file: File-like object containing the CV (PDF or DOCX)
            filename: Original filename of the CV
            phone: Optional phone number
            timeout: Request timeout in seconds
            
        Returns:
            SubmitResponse with success status and details
            
        Raises:
            requests.exceptions.RequestException: On connection errors
            ValueError: On API errors
        """
        files = {
            "cv_file": (filename, cv_file, "application/octet-stream")
        }
        data = {
            "full_name": full_name,
            "email": email,
            "phone": phone,
        }
        
        response = requests.post(
            f"{self.base_url}/submit",
            files=files,
            data=data,
            timeout=timeout
        )
        
        if response.status_code == 400:
            error = response.json().get("detail", "Invalid request")
            raise ValueError(f"Validation error: {error}")
        
        if response.status_code == 500:
            error = response.json().get("detail", "Server error")
            raise ValueError(f"Server error: {error}")
        
        if response.status_code != 200:
            raise ValueError(f"Unexpected status: {response.status_code}")
        
        data = response.json()
        return SubmitResponse(
            success=data["success"],
            message=data["message"],
            candidate_name=data.get("candidate_name", ""),
            email=data.get("email", ""),
            cv_file_path=data.get("cv_file_path", ""),
            already_exists=data.get("already_exists", False),
        )
    
    def health(self) -> bool:
        """
        Check if the API is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

