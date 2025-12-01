"""CV Upload settings."""

from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CVUploadSettings(BaseSettings):
    """Settings for CV upload and parsing."""
    
    model_config = SettingsConfigDict(
        env_prefix="CV_",  # CV_UPLOAD_PATH, CV_PARSED_PATH
        extra="ignore",
    )
    
    upload_path: Path = Field(
        default=Path("src/backend/database/cvs/uploads"),
        description="Directory for uploaded CV files",
    )
    parsed_path: Path = Field(
        default=Path("src/backend/database/cvs/parsed"),
        description="Directory for parsed CV markdown files",
    )
    
    def ensure_dirs(self) -> None:
        """Create upload and parsed directories if they don't exist."""
        self.upload_path.mkdir(parents=True, exist_ok=True)
        self.parsed_path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_cv_settings() -> CVUploadSettings:
    """Get cached CV upload settings."""
    return CVUploadSettings()

