"""
SDK for interacting with Recruitment Agent APIs.

Usage:
    from src.sdk import SupervisorClient, CVUploadClient
    
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
"""

from src.sdk.supervisor import SupervisorClient
from src.sdk.cv_upload import CVUploadClient

__all__ = ["SupervisorClient", "CVUploadClient"]

