from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# ✅ Correct import via src.agents package (which re-exports from src.agents.db_executor)
from src.agents import db_executor

SYSTEM_PROMPT = """
You are a supervisor agent overseeing the recruitment process.
Your primary role is to orchestrate tasks by delegating them to specialized sub-agents (tools).
You currently have access to:
- db_executor: A powerful agent that can query the database to answer questions about candidates, status, etc.

When asked a question, use the db_executor tool to find the answer.
"""

# --------- Subagents as tools ---------
subagents = [
    db_executor,
]

# --- **NOTE:** ---
# >>> In UI make sure to use 'thread_id' as a configurable parameter to the agent.invoke() method.
# >>> When willing to use langsmith UI, then you must remove the checkpointer=memory, 
#     otherwise it will not work.
memory = MemorySaver()

# ------------- Supervisor --------------
supervisor_model = ChatOpenAI(model="gpt-4o", temperature=0)

supervisor_agent = create_agent(
    model=supervisor_model,
    tools=subagents,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=memory,          # outcome for langsmith UI
)
