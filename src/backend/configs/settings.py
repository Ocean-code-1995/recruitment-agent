"""
Main application settings.

This module aggregates all settings into a single Settings class.
For most use cases, import individual settings directly:

    from src.backend.configs import get_cv_settings, get_openai_settings
    
    cv = get_cv_settings()
    openai = get_openai_settings()
"""

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .cv import CVUploadSettings
from .database import DatabaseSettings
from .openai import OpenAISettings


class Settings(BaseSettings):
    """
    Aggregated application settings.
    
    Combines all configuration in one place. Individual settings
    can also be accessed via their dedicated getter functions.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    cv: CVUploadSettings = Field(default_factory=CVUploadSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)


@lru_cache
def get_settings() -> Settings:
    """Get cached main settings instance."""
    return Settings()
