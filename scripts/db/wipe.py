"""
Run as follows:
>>> POSTGRES_HOST=localhost POSTGRES_PORT=5433 POSTGRES_PASSWORD=password123 python -m scripts.db.wipe
"""

import sys
import os
from sqlalchemy import text

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_root)

from src.database.candidates.client import get_engine

def wipe_database():
    print("⚠️  WARNING: This will PERMANENTLY DELETE ALL RECORDS from the 'candidates' table and all related tables (CASCADE).")
    confirm = input("Type 'yes' to confirm: ")
    
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return

    engine = get_engine()
    
    try:
        with engine.connect() as connection:
            print("Connecting to database...")
            
            # Using TRUNCATE with CASCADE is faster and cleaner for Postgres
            print("Truncating candidates table with CASCADE...")
            connection.execute(text("TRUNCATE TABLE candidates CASCADE;"))
            connection.commit()
            
            print("✅ Database entries wiped successfully.")
            
    except Exception as e:
        print(f"❌ Error wiping database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    wipe_database()

