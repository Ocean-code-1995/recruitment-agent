import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.candidates.models import Base
from src.database.candidates.config import load_settings


def get_engine():
    """
    Builds a SQLAlchemy engine using validated environment variables.
    Works seamlessly in both local and Docker environments.

    Priority:
    1. Environment variables (e.g., POSTGRES_HOST from Docker)
    2. .env file defaults via Pydantic config
    """
    settings = load_settings()

    # Allow POSTGRES_HOST override (Docker will set it to 'db')
    # Strip whitespace to avoid DNS resolution issues on Windows
    postgres_host = os.getenv("POSTGRES_HOST", settings.POSTGRES_HOST).strip()
    database_url = (
        f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{postgres_host}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )

    print(f"🔌 Connecting to database at {postgres_host}:{settings.POSTGRES_PORT} ...")

    # Optional: echo=True for debugging SQL statements
    return create_engine(database_url, echo=False, future=True)


# --- SQLAlchemy session setup ---
engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    """
    Creates all database tables if they don't exist.
    Intended for dev setup / Docker initialization.
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        raise


if __name__ == "__main__":
    init_db()
