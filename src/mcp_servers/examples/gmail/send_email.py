"""
Gmail MCP Server
================

This file implements a Model Context Protocol (MCP) server that bridges
a local Gmail API client to an AI model (e.g. Claude or LangGraph agents).

How it works:
-------------
- The LLM connects to this server through an MCP client (e.g. MultiServerMCPClient)
  using STDIO as a transport layer.
- When the server starts, it authenticates with Gmail (via OAuth2) and registers
  all available Gmail operations as MCP tools (send, read, search, label, etc.).
- The MCP client fetches these tool definitions and exposes them to the LLM.
- When the LLM decides to use one (e.g. “send an email”), it triggers a tool call,
  which this server executes and returns the result.

Why these arguments:
--------------------
--creds-file-path : path to the Google OAuth2 client credentials (for login)
--token-path      : path to the saved access/refresh token (for session reuse)

Together, these allow the MCP server to securely spin up a Gmail session and
respond to model-issued actions via standard I/O.

run as follows:
>>> python -m src.mcp_servers.examples.gmail.send_email
"""



import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

from langchain_openai.chat_models.base import ChatOpenAI
from pathlib import Path
from .settings import GMailSettings
from dotenv import load_dotenv
load_dotenv()


UV_PATH = "/Users/sebastianwefers/.local/bin/uv"  # <= full path to uv (important)
MODEL =  ChatOpenAI(model="gpt-4o", temperature=0)

settings = GMailSettings()


async def main():
    # 1) Connect to the Gmail MCP server via stdio
    client = MultiServerMCPClient(
        {
            "gmail": {
                "command": UV_PATH,
                "args": [
                    "--directory", str(settings.gmail_mcp_dir),
                    "run", "gmail",
                    "--creds-file-path", str(settings.creds),
                    "--token-path", str(settings.token),
                ],
                "transport": "stdio",
            }
        }
    )

    # 2) Fetch tool specs from the server
    tools = await client.get_tools()

    # 3) Build a simple agent with those tools
    agent = create_agent(MODEL, tools)

    # 4) Test: ask the agent to list unread emails or send a draft
    # Tailor the prompt to the tool names your Gmail MCP exposes (e.g., listEmails, sendEmail, etc.)
    result = await agent.ainvoke({
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an automated agent authorized to use Gmail MCP tools, "
                    "including sending emails through the user's authorized account."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Send an email to sebastianwefersnz@gmail.com "
                    "with subject 'Sailing Cuuuuunt!' and message "
                    "'Hello there Sebastian,\n\n"
                    "'Wanna go sailing soon when the wind blows dogs off chains?'"
                    "'Warm regards,'"
                    "'GPT-4o via Gmail MCP server 😊'"
                ),
            },
        ]
    })

    print(result['messages'][-1].content)

    # Example follow-up: ask it to draft an email (depends on tool naming/params in gmail-mcp)
    # result2 = await agent.ainvoke(
    #     {"messages": [{"role": "user", "content": "Draft an email to myself with subject 'Hello MCP' and body 'Testing LangGraph + MCP Gmail'."}]}
    # )
    # print(result2)

if __name__ == "__main__":
    asyncio.run(main())
    

