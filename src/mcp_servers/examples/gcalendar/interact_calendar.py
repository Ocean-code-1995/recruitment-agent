"""
Test script to interact with the Google Calendar MCP server.
===============================================================
# Only run server
# >>> python src/mcp_servers/examples/gcalendar/interact_calendar_spawn.py
"""


import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_openai.chat_models.base import ChatOpenAI
from .settings import GoogleCalendarSettings
from dotenv import load_dotenv
import sys

load_dotenv()

MODEL = ChatOpenAI(model="gpt-4o", temperature=0)


settings = GoogleCalendarSettings()

CALENDAR_MCP_DIR = settings.calendar_mcp_dir
CREDS = settings.creds
TOKEN = settings.token

async def main():
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

    tools = await client.get_tools()
    agent = create_agent(MODEL, tools)

    result = await agent.ainvoke({
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a scheduling assistant authorized to use Google Calendar MCP tools. "
                    "You can list, create, and analyze events."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Create a calendar event for the coming Friday at 3pm titled "
                    "'Kick-off of the Agent MCP Hackathon'."
                ),
            },
        ]
    })

    print(result["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())
