"""
Supervisor Agent that orchestrates sub-agents for recruitment tasks.

For more transparency in langsmith UI disable memory, then run:
----------------------------------------------------------------
| >>> docker compose -f docker/docker-compose.yml up --build.  |
| >>> POSTGRES_HOST=localhost POSTGRES_PORT=5433 langgraph dev |
----------------------------------------------------------------
"""


from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from src.prompts import get_prompt

load_dotenv()

# ✅ Correct import via src.agents package (which re-exports from src.agents.db_executor)
from src.agents import (
    db_executor,
    cv_screening_workflow,
    gcalendar_agent,
    gmail_agent,
)

SYSTEM_PROMPT = get_prompt(
    template_name="Supervisor",
    latest_version=True,
)

# --------- Subagents as tools ---------
subagents = [
    db_executor,
    cv_screening_workflow,
    gcalendar_agent,
    gmail_agent,
    voice_judge,
]

# --------------- Memory ----------------
# **NOTE:** 
# >>> In UI make sure to use 'thread_id' as a configurable parameter to the agent.invoke() method.
# >>> When willing to use langsmith UI, then you must remove the checkpointer=memory, 
#     otherwise it will not work.
memory = MemorySaver()

# ------------- Supervisor --------------
supervisor_model = ChatOpenAI(
    model="gpt-4o", 
    temperature=0,
)

supervisor_agent = create_agent(
    model=supervisor_model,
    tools=subagents,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=memory,          # outcomment for langsmith UI
)
