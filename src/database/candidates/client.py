import os
import socket
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.candidates.models import Base
from src.configs import get_database_settings


def get_engine():
    """
    Builds a SQLAlchemy engine using validated environment variables.
    Works seamlessly in both local and Docker environments.

    Priority:
    1. Environment variables (e.g., POSTGRES_HOST from Docker)
    2. .env file defaults via Pydantic config
    """
    settings = get_database_settings()

    # Allow POSTGRES_HOST override; strip whitespace/quotes to avoid DNS issues
    raw_host = os.getenv("POSTGRES_HOST", settings.host)
    postgres_host = raw_host.strip().strip("\"'")

    # If 'db' (compose) is not resolvable (single-container run), fall back to host.docker.internal
    try:
        socket.gethostbyname(postgres_host)
    except Exception:
        fallback = os.getenv("POSTGRES_HOST_FALLBACK", "host.docker.internal").strip().strip("\"'")
        print(f"[db-client] Host '{postgres_host}' not resolvable; falling back to '{fallback}'")
        postgres_host = fallback

    database_url = (
        f"postgresql+psycopg2://{settings.user}:{settings.password}"
        f"@{postgres_host}:{settings.port}/{settings.db}"
    )

    print(f"[db-client] Connecting to database at host={postgres_host} port={settings.port} db={settings.db} user={settings.user}", flush=True)

    return create_engine(database_url, echo=False, future=True)


# --- SQLAlchemy session setup ---
engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
