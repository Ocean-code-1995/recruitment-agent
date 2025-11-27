"""CV Upload API schemas."""

from pydantic import BaseModel, Field


class SubmitResponse(BaseModel):
    """Response model for CV submission."""
    success: bool = Field(..., description="Whether the submission was successful")
    message: str = Field(..., description="Status message")
    candidate_name: str = Field(default="", description="Name of the candidate")
    email: str = Field(default="", description="Email of the candidate")
    cv_file_path: str = Field(default="", description="Path where CV was saved")
    already_exists: bool = Field(default=False, description="True if candidate already applied")

