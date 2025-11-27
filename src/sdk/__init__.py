"""
SDK for interacting with Recruitment Agent APIs.

Usage:
    from src.sdk import SupervisorClient
    
    client = SupervisorClient()
    
    # Simple chat
    response = client.chat("Show me all candidates")
    print(response.content)
    
    # Streaming chat
    for chunk in client.stream("Show me all candidates"):
        print(chunk.content, end="", flush=True)
"""

from src.sdk.supervisor import SupervisorClient

__all__ = ["SupervisorClient"]

