"""
Simple React Agent implementation with monitoring capabilities.

- React agent:
    - https://docs.langchain.com/oss/python/langchain/agents


install:
    - langgraph-cli

Run as follows:
>>> cd src/agents/example/
>>> langgraph dev

"""
from langchain.agents import create_agent
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from dotenv import load_dotenv
 
 

load_dotenv()



# --- Tools ---
@tool
def convert_fahrenheit_celsius(fahrenheit: float) -> float:
    """
    Convert fahrenheit to celsius.
    Args:
        fahrenheit (float): Temperature in fahrenheit.
    Returns:
        float: Temperature in celsius.
    """
    return (fahrenheit - 32) * 5.0/9.0
    


web_search = TavilySearch(
    max_results = 5,
    topic = "general",
    # include_answer = False,
    # include_raw_content = False,
    # ...
)


tools = [
    web_search,
    convert_fahrenheit_celsius
]


agent = create_agent(
    "gpt-5",
    tools=tools
)