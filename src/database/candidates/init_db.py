"""
Database initialization script.

This is a standalone script to initialize the database.
Kept separate from client.py to avoid circular import issues
when running with `python -m`.

Usage:
    python -m src.database.candidates.init_db
"""

from src.database.candidates.client import engine
from src.database.candidates.models import Base


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

