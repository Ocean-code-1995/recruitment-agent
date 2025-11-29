"""
Database initialization script.

This is a standalone script to initialize the database.
Kept separate from client.py to avoid circular import issues
when running with `python -m`.

Usage:
    python -m src.database.candidates.init_db
"""

from src.backend.database.candidates.client import engine
from src.backend.database.candidates.models import Base
from sqlalchemy import inspect

def init_db():
    """
    Creates all database tables if they don't exist.
    Intended for dev setup / Docker initialization.
    """
    try:
        print("🚀 Starting database initialization...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📊 Found tables: {tables}")
        
        if "candidates" in tables:
            print("✅ Database initialized successfully.")
            return True
        else:
            print("❌ Error: 'candidates' table was not created!")
            
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        raise


if __name__ == "__main__":
    init_db()

