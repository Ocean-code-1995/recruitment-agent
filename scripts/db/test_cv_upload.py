"""
Test the CV upload functionality.
Run with:
>>> export PYTHONPATH=$PYTHONPATH:. && python3 scripts/db/test_cv_upload.py
"""


import os
from src.sdk.cv_upload import CVUploadClient

def test_upload():
    client = CVUploadClient(base_url="http://localhost:8080/api/v1/cv")
    
    cv_path = "src/backend/database/cvs/uploads/Sebastian_Wefers_CV.pdf"
    
    if not os.path.exists(cv_path):
        print(f"❌ CV file not found at {cv_path}")
        return

    print(f"📤 Uploading {cv_path}...")
    
    try:
        with open(cv_path, "rb") as f:
            response = client.submit(
                full_name="Test Candidate",
                email="test_candidate@example.com",
                phone="+1234567890",
                cv_file=f,
                filename="test_candidate.pdf"
            )
        
        if response.success:
            print(f"✅ Upload successful: {response.message}")
            print(f"Details: {response}")
        elif response.already_exists:
            print(f"⚠️ Candidate already exists: {response.message}")
        else:
            print(f"❌ Upload failed: {response.message}")

    except Exception as e:
        print(f"❌ Error during upload: {e}")

if __name__ == "__main__":
    test_upload()

