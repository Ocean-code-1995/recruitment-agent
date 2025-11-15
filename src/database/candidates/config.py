from pydantic_settings import BaseSettings, SettingsConfigDict  # ✅ preferred modern import
from pydantic import Field, ValidationError
from typing import Optional
import sys

class Settings(BaseSettings):
    POSTGRES_USER: str = Field(..., description="Database username")
    POSTGRES_PASSWORD: str = Field(..., description="Database password")
    POSTGRES_DB: str = Field(..., description="Database name")
    POSTGRES_HOST: str = Field("localhost", description="Database host")
    POSTGRES_PORT: int = Field(5432, description="Database port")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore" #  this line tells Pydantic to ignore unrelated vars
        )



def load_settings() -> Settings:
    """
    Loads and validates environment variables from .env file.
    If any required variable is missing, exits with a clear message.
    """
    try:
        return Settings()
    except ValidationError as e:
        print("❌ Environment configuration invalid:\n")
        print(e)
        sys.exit(1)
