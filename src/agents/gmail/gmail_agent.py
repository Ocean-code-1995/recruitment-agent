import asyncio
import shutil
from pathlib import Path
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from src.mcp_servers.examples.gmail.settings import GMailSettings
from src.prompts import get_prompt


# Attempt to find uv executable
#-----------------------------------------------------------------------------
# `Dockerfile.supervisor` installs uv in the base image in `/usr/local/bin/uv`
# `which` attempts to find it in the system PATH and returns the full path to it.
UV_PATH = shutil.which("uv")


SYSTEM_PROMPT = get_prompt(
    template_name="gmail",
    local_prompt_path="gmail/v1.txt"
)

@tool
def gmail_agent(query: str) -> str:
    """
    A tool that acts as a Gmail agent.
    It can read, search, label, and send emails using the Gmail MCP server.
    
    Args:
        query (str): The natural language request (e.g., "Send an email to X", "Check unread emails").
        
    Returns:
        str: The natural language response from the agent confirming the action or providing the requested information.

    Example output:
        "I have successfully sent the email to X with the subject 'Interview Invitation'."
    """
    if not UV_PATH:
        return "❌ Error: 'uv' executable not found. Please ensure uv is installed and in the system PATH."

    try:
        import asyncio
        async def _run_async():
            # Load settings
            settings = GMailSettings()
            
            # Initialize model
            model = ChatOpenAI(model="gpt-4o", temperature=0)

            # Connect to MCP server
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

            # Fetch tools
            try:
                tools = await client.get_tools()
            except Exception as e:
                return f"❌ Failed to connect to Gmail MCP server: {str(e)}"

            if not tools:
                return "❌ No tools available from Gmail MCP server."

            # Create agent
            agent = create_agent(model, tools)

            # Run agent
            result = await agent.ainvoke({
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": query,
                    },
                ]
            })

            # Extract result
            output = result["messages"][-1].content
            return output

        return asyncio.run(_run_async())

    except Exception as e:
        import traceback
        return f"❌ Error in gmail_agent: {str(e)}\n{traceback.format_exc()}"

