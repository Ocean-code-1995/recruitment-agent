"""OpenAI API settings."""

import sys
from functools import lru_cache
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAISettings(BaseSettings):
    """
    OpenAI API configuration.
    
    Validates that OPENAI_API_KEY is set and provides a helpful error message
    if missing, especially useful in Docker environments.
    """
    
    model_config = SettingsConfigDict(
        extra="ignore",
    )
    
    api_key: str = Field(
        default="",
        alias="OPENAI_API_KEY",
        description="OpenAI API key for model access",
    )
    
    @model_validator(mode="after")
    def validate_api_key(self) -> "OpenAISettings":
        """Validate that API key is set and provide helpful error message."""
        if not self.api_key:
            error_message = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                        ⚠️  OPENAI_API_KEY NOT SET  ⚠️                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  The OPENAI_API_KEY environment variable is required but not set.           ║
║                                                                              ║
║  To fix this:                                                                ║
║                                                                              ║
║  1. Create a .env file in the project root:                                  ║
║     OPENAI_API_KEY=sk-your-api-key-here                                      ║
║                                                                              ║
║  2. Or set it directly in your shell:                                        ║
║     export OPENAI_API_KEY=sk-your-api-key-here                               ║
║                                                                              ║
║  3. Or pass it to Docker:                                                    ║
║     docker compose --env-file .env -f docker/docker-compose.yml up           ║
║                                                                              ║
║  Get your API key at: https://platform.openai.com/api-keys                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
            print(error_message, file=sys.stderr)
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Basic validation that it looks like an OpenAI key
        if not (self.api_key.startswith("sk-") or self.api_key.startswith("org-")):
            print(
                "⚠️  Warning: OPENAI_API_KEY doesn't start with 'sk-' - "
                "make sure it's a valid OpenAI API key.",
                file=sys.stderr
            )
        
        return self
    
    def __repr__(self) -> str:
        """Safe representation without exposing the key."""
        masked = f"{self.api_key[:7]}...{self.api_key[-4:]}" if len(self.api_key) > 11 else "***"
        return f"OpenAISettings(api_key={masked})"


@lru_cache
def get_openai_settings() -> OpenAISettings:
    """
    Get cached OpenAI settings.
    
    Raises ValueError with helpful message if OPENAI_API_KEY is not set.
    """
    return OpenAISettings()


def get_openai_api_key() -> str:
    """
    Convenience function to get just the API key.
    
    Raises ValueError with helpful message if OPENAI_API_KEY is not set.
    """
    return get_openai_settings().api_key

