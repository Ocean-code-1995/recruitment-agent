import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.backend.database.candidates.models import Base
from src.backend.configs import get_database_settings


def get_engine():
    """
    Builds a SQLAlchemy engine using validated environment variables.
    Works seamlessly in both local and Docker environments.

    Priority:
    1. Environment variables (e.g., POSTGRES_HOST from Docker)
    2. .env file defaults via Pydantic config
    """
    settings = get_database_settings()

    # Allow POSTGRES_HOST override (Docker will set it to 'db')
    # Strip whitespace to avoid DNS resolution issues on Windows
    postgres_host = os.getenv("POSTGRES_HOST", settings.host).strip()
    database_url = (
        f"postgresql+psycopg2://{settings.user}:{settings.password}"
        f"@{postgres_host}:{settings.port}/{settings.db}"
    )

    print(f"🔌 Connecting to database at {postgres_host}:{settings.port} ...")

    # Optional: echo=True for debugging SQL statements
    return create_engine(database_url, echo=False, future=True)


# --- SQLAlchemy session setup ---
engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
