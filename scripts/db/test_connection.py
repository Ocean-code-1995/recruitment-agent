"""
Test basic database connection.

Run standalone:
>>> POSTGRES_HOST=localhost POSTGRES_PORT=5433 python scripts/db/test_connection.py
"""

import os
from sqlalchemy import text

# Ensure project root is in path
import scripts.db  # noqa: F401

from src.backend.database.candidates.client import get_engine


def test_connection() -> bool:
    """
    Test basic database connectivity.
    
    Returns:
        True if connection successful, False otherwise.
    """
    print("--- Testing Database Connection ---")
    
    # Print environment info
    print(f"POSTGRES_HOST (env): {os.environ.get('POSTGRES_HOST')}")
    print(f"POSTGRES_PORT (env): {os.environ.get('POSTGRES_PORT')}")
    
    try:
        engine = get_engine()
        print(f"Engine URL: {engine.url}")
        
        with engine.connect() as connection:
            print("✅ Connection successful!")
            result = connection.execute(text("SELECT 1"))
            print(f"✅ SELECT 1 result: {result.fetchone()}")
            return True
            
    except Exception as e:
        print("\n❌ Connection FAILED")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_connection()

