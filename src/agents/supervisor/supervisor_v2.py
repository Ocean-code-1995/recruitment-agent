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

load_dotenv()

# ✅ Correct import via src.agents package (which re-exports from src.agents.db_executor)
from src.agents import (
    db_executor,
    cv_screening_workflow,
    gcalendar_agent,
    gmail_agent,
)



# -----------------------------------------------------------------------------
# this was icnldued before, but to my knowledge the tools are already injected as context 
# when passing tool list in 'create_agent' function.
# However, I'm keeping it here for reference.
OPTIONAL_CONTEXT = """
You currently have access to:
- db_executor: A powerful agent that can query the database to answer questions about candidates, status, etc.
- cv_screening_workflow: A tool that performs the CV screening for a candidate. It requires the candidate's full name.
- gcalendar_agent: An agent that can manage Google Calendar events (schedule interviews, list meetings, etc.).
- gmail_agent: An agent that can read and send emails (contact candidates, check communications, etc.).

IMPORTANT:
1. When asked to screen a CV, ALWAYS use the `cv_screening_workflow` tool first. 
2. After calling `cv_screening_workflow`, you MUST wait for its output to confirm success.
3. ONLY AFTER the screening is confirmed successful, you can use `db_executor` to check the scores if the user asks for them.
4. If the user asks for scores and they don't exist, check if the screening has been run. If not, run it (with permission) or suggest running it.
5. For any scheduling tasks (e.g., "Schedule an interview with X"), use `gcalendar_agent`.
6. For any email communication (e.g., "Send an email to X"), use `gmail_agent`.
"""
# >>> yes model is aware of the tools.
# -----------------------------------------------------------------------------



SYSTEM_PROMPT = """
You are a supervisor agent overseeing the recruitment process.
Your primary role is to orchestrate tasks by delegating them to specialized sub-agents (tools).

***NOTE***:
Please notify the user if you yourself or your subagents encounter any errors. 
"""

# --------- Subagents as tools ---------
subagents = [
    db_executor,
    cv_screening_workflow,
    gcalendar_agent,
    gmail_agent,
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
    checkpointer=memory,          # outcome for langsmith UI
)
