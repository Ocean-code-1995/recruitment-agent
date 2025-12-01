# src/core/configs/model.py
from typing import Optional, Literal
from pydantic import BaseModel, Field, SecretStr, field_validator, ConfigDict
import os


class ModelConfig(BaseModel):
    """
    Configuration object for connecting to and parameterizing an LLM provider.

    Notes:
        The ``model_config = ConfigDict(arbitrary_types_allowed=True)`` setting
        is included for consistency with other configs. It has no effect here
        since all fields are natively supported types (e.g., str, float, int).
        Standard Pydantic validation applies to all fields in this model.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    provider: Literal["openai", "anthropic", "bedrock", "azure"] = Field(
        ...,
        description="LLM provider identifier (e.g., openai, anthropic, bedrock, azure)."
    )
    model_name: str = Field(
        ...,
        description="Model identifier (e.g., gpt-4o, claude-3, etc.)."
    )
    api_key: Optional[SecretStr] = Field(
        default=None,
        description="API key for the model provider. Fallbacks to env var if omitted."
    )
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for model randomness."
    )
    max_tokens: Optional[int] = Field(
        default=None,
        gt=0,
        description="Optional token limit for completions."
    )
    api_base: Optional[str] = Field(
        default=None,
        description="Optional override for the model's base API URL."
    )

    # ~~~ VALIDATION ~~~
    @field_validator("api_key", mode="before")
    @classmethod
    def resolve_api_key(cls, v, info):
        """Resolve the API key from the provided value or environment.
        """
        if v is not None:
            return v

        provider = info.data.get("provider")
        env_vars = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "bedrock": "AWS_ACCESS_KEY_ID",
            "azure": "AZURE_OPENAI_API_KEY",
        }

        env_var = env_vars.get(provider)
        if env_var:
            api_key = os.getenv(env_var)
            if api_key:
                return SecretStr(api_key)

        raise ValueError(
            f"Missing API key: provide explicitly or set {env_var} in environment."
        )

    # ~~~ UTILITIES ~~~
    def get_api_key(self) -> str:
        """Safely return the underlying API key string.
        """
        return self.api_key.get_secret_value() if self.api_key else ""

    def __repr__(self) -> str:
        """Safe string representation (without exposing secret)."""
        return (
            f"ModelConfig(provider='{self.provider}', "
            f"model_name='{self.model_name}', "
            f"temperature={self.temperature}, "
            f"max_tokens={self.max_tokens})"
        )
