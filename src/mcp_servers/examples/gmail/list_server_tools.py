
"""
The only part that can differ across Gmail MCP implementations is the exact tool names and schemas 
(e.g., listEmails, sendEmail, arg names). That's why I recommend a quick introspection step to list 
the tools the server exposes and their JSON schemas—then prompt your agent accordingly.

run as follows:
>>> python -m src.mcp_servers.examples.gmail.list_server_tools
"""

import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from pathlib import Path
from .settings import GMailSettings

UV_PATH  = "/Users/sebastianwefers/.local/bin/uv"  # <= full path to uv (important)
settings = GMailSettings()

async def main():
    client = MultiServerMCPClient({
        "gmail": {
            "command": UV_PATH,
            "args": [
                "--directory", str(settings.gmail_mcp_dir),
                "run", "gmail",
                "--creds-file-path", str(settings.creds), 
                "--token-path", str(settings.token)
            ],
            "transport": "stdio",
        }
    })
    tools = await client.get_tools()
    
    print("\n📬 Tools exposed by Gmail MCP server:\n")
    for t in tools:
        print(f"🔧 TOOL: {t.name}")
        if t.args_schema:
            print("📄 SCHEMA:")
            print(t.args_schema)  # already a dict
        else:
            print("📄 SCHEMA: None")
        print("-" * 60)


if __name__ == "__main__":  
    asyncio.run(main())
