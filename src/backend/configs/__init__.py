"""Application configuration."""

from .cv import CVUploadSettings, get_cv_settings
from .database import DatabaseSettings, get_database_settings
from .openai import OpenAISettings, get_openai_settings, get_openai_api_key
from .settings import Settings, get_settings

__all__ = [
    # CV Upload
    "CVUploadSettings",
    "get_cv_settings",
    # Database
    "DatabaseSettings",
    "get_database_settings",
    # OpenAI
    "OpenAISettings",
    "get_openai_settings",
    "get_openai_api_key",
    # Main settings
    "Settings",
    "get_settings",
]
