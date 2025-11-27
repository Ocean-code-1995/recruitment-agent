"""
Run all database debug checks.

Run as follows:
>>> POSTGRES_HOST=localhost POSTGRES_PORT=5433 python scripts/db/debug_all.py

This runs:
1. Connection test
2. Session query test
3. List existing candidates
"""

from scripts.db.test_connection import test_connection
from scripts.db.test_session import test_session_query
from scripts.db.list_candidates import list_candidates


def run_all_checks() -> None:
    """Run all database diagnostic checks."""
    print("=" * 50)
    print("🔍 DATABASE DIAGNOSTICS")
    print("=" * 50)
    
    # 1. Test connection
    conn_ok = test_connection()
    
    if not conn_ok:
        print("\n⛔ Stopping - connection failed")
        return
    
    print()
    
    # 2. Test session
    session_ok = test_session_query()
    
    if not session_ok:
        print("\n⛔ Stopping - session failed")
        return
    
    print()
    
    # 3. List candidates
    list_candidates()
    
    print()
    print("=" * 50)
    print("✅ All checks completed")
    print("=" * 50)


if __name__ == "__main__":
    run_all_checks()

