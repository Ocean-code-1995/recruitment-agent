"""Database connection settings."""

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """PostgreSQL database connection settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_",
        extra="ignore",
    )
    
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    user: str = Field(default="agentic_user")
    password: str = Field(default="")
    db: str = Field(default="agentic_hr")
    
    @property
    def url(self) -> str:
        """Build database URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"
    
    @property
    def async_url(self) -> str:
        """Build async database URL for SQLAlchemy async."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


@lru_cache
def get_database_settings() -> DatabaseSettings:
    """Get cached database settings."""
    return DatabaseSettings()

