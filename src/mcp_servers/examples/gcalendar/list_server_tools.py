"""
Calendar MCP Server Tool Introspection
======================================

# Only run sserver:
# (wont make this script work, since this script launches the server itself)
# >>> python src/mcp_servers/calendar-mcp/run_server.py

# start server & list mcp tools:
# >>> python src/mcp_servers/examples/gcalendar/list_server_tools.py

"""

import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
import sys

from .settings import GoogleCalendarSettings


settings = GoogleCalendarSettings()

CALENDAR_MCP_DIR = settings.calendar_mcp_dir
CREDS = settings.creds
TOKEN = settings.token


#settings = GoogleCalendarSettings()

async def main():
    # Connect to the Calendar MCP server
    client = MultiServerMCPClient({
        "calendar": {
            "command": sys.executable,
            "args": [
                f"{CALENDAR_MCP_DIR}/run_server.py",
                "--creds-file-path", str(CREDS),
                "--token-path", str(TOKEN),
            ],
            "transport": "stdio",
        }
    })


    # Fetch MCP tool definitions
    tools = await client.get_tools()

    print("\n📅 Tools exposed by Calendar MCP server:\n")
    for t in tools:
        print(f"🔧 TOOL: {t.name}")
        if t.args_schema:
            print("📄 SCHEMA:")
            print(t.args_schema)
        else:
            print("📄 SCHEMA: None")
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(main())
