"""
Supervisor Agent that orchestrates sub-agents for recruitment tasks.

For more transparency in langsmith UI run:
----------------------------------------------------------------
| >>> docker compose -f docker/docker-compose.yml up --build.  |
| >>> POSTGRES_HOST=localhost POSTGRES_PORT=5433 langgraph dev |
----------------------------------------------------------------
"""


from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

# ✅ Correct import via src.agents package (which re-exports from src.agents.db_executor)
from src.agents import (
    db_executor,
    cv_screening_workflow,
)

SYSTEM_PROMPT = """
You are a supervisor agent overseeing the recruitment process.
Your primary role is to orchestrate tasks by delegating them to specialized sub-agents (tools).
You currently have access to:
- db_executor: A powerful agent that can query the database to answer questions about candidates, status, etc.
- cv_screening_workflow: A tool that performs the CV screening for a candidate. It requires the candidate's full name.

IMPORTANT:
1. When asked to screen a CV, ALWAYS use the `cv_screening_workflow` tool first. 
2. After calling `cv_screening_workflow`, you MUST wait for its output to confirm success.
3. ONLY AFTER the screening is confirmed successful, you can use `db_executor` to check the scores if the user asks for them.
4. If the user asks for scores and they don't exist, check if the screening has been run. If not, run it (with permission) or suggest running it.
"""

# --------- Subagents as tools ---------
subagents = [
    db_executor,
    cv_screening_workflow,
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
    #checkpointer=memory,          # outcome for langsmith UI
)
