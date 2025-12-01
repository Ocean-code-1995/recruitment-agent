import os
from pydantic import Field, ConfigDict, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv
from pydantic import ValidationError
import sys
import os


class OpenAIApiKey(BaseSettings):
    """Schema for validating and loading the OpenAI API key configuration.
    """
    model_config = ConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",     # = root/.env
        env_file_encoding="utf-8",
        title="OpenAI API Key Schema",
        description="Validates and loads the OpenAI API key from environment variables.",
    )
    api_key: str = Field(
        ...,                         # >>> required field
        title="OpenAI API Key",
        description="API key for OpenAI authentication.",
        examples=["sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"],
        alias="OPENAI_API_KEY",
    )

    @field_validator("api_key")
    @classmethod
    def validate_openai_api_key(cls, v: str) -> str:
        """Validate that the API key is present and has the correct format.
        """
        if not v:
            raise ValueError(
                "💥 Missing `OPENAI_API_KEY` environment variable."
            )
        if not v.startswith("sk-"):
            raise ValueError(
                "💥 Invalid `OPENAI_API_KEY` — must start with 'sk-'."
            )
        return v
    
    @classmethod
    def validate_environment(cls) -> "OpenAIApiKey":
        """
        Load .env from the root directory 
        and validate that the API key is present and valid.
        """
        try:
            # Pydantic auto-loads .env and validates
            config = cls()                                
            os.environ["OPENAI_API_KEY"] = config.api_key # Set for runtime access
            return config 
        except ValidationError as e:
            print(f"💥 OpenAI API key misconfiguration:\n{e}")
            sys.exit(1)
