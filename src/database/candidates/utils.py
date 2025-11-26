import secrets
import string

def generate_auth_code() -> str:
    """Generate a 6-digit random authentication code."""
    return "".join(secrets.choice(string.digits) for _ in range(6))
