import asyncio
import sys
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from src.mcp_servers.examples.gcalendar.settings import GoogleCalendarSettings
from src.backend.prompts import get_prompt


SYSTEM_PROMPT = get_prompt(
    template_name="GCalendar",
    latest_version=True     
)

@tool
def gcalendar_agent(query: str) -> str:
    """
    A tool that acts as a Google Calendar agent.
    It can list, create, and analyze calendar events using the Google Calendar MCP server.
    
    Args:
        query (str): The natural language request for the calendar (e.g., "Schedule a meeting with X on Friday at 3pm").
        
    Returns:
        str: The natural language response from the agent confirming the action or providing the requested information.

    Example output:
        "I have successfully scheduled the meeting with X for Friday at 3pm. The event ID is 1234567890."
    """
    try:
        import asyncio
        async def _run_async():
            # Load settings
            settings = GoogleCalendarSettings()
            CALENDAR_MCP_DIR = settings.calendar_mcp_dir
            CREDS = settings.creds
            TOKEN = settings.token

            # Initialize model
            model = ChatOpenAI(model="gpt-4o", temperature=0)

            # Connect to MCP server
            # Note: This spawns a new process for each call. 
            # In a production environment, you might want to manage a persistent connection.
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

            # Fetch tools
            try:
                tools = await client.get_tools()
            except Exception as e:
                return f"❌ Failed to connect to Calendar MCP server: {str(e)}"

            if not tools:
                return "❌ No tools available from Calendar MCP server."

            # Create agent
            agent = create_agent(model, tools)

            # Run agent
            # We wrap the user query in a system/user message structure
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
        return f"❌ Error in gcalendar_agent: {str(e)}\n{traceback.format_exc()}"

