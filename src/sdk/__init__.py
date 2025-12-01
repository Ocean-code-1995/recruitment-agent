"""
SDK for interacting with Recruitment Agent APIs.

Usage:
    from src.sdk import SupervisorClient, CVUploadClient, DatabaseClient
    
    # Supervisor Agent
    supervisor = SupervisorClient()
    response = supervisor.chat("Show me all candidates")
    print(response.content)
    
    # CV Upload
    cv_client = CVUploadClient()
    with open("my_cv.pdf", "rb") as f:
        response = cv_client.submit(
            full_name="Ada Lovelace",
            email="ada@example.com",
            cv_file=f,
            filename="my_cv.pdf"
        )
    
    # Database Queries
    db = DatabaseClient()
    candidates = db.get_candidates(status="applied")
    candidate = db.get_candidate_by_email("ada@example.com")
"""

from src.sdk.supervisor import SupervisorClient
from src.sdk.cv_upload import CVUploadClient
from src.sdk.database import DatabaseClient

__all__ = ["SupervisorClient", "CVUploadClient", "DatabaseClient"]

