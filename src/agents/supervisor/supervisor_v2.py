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

SYSTEM_PROMPT = """
You are the **Supervisor Agent** overseeing the entire recruitment workflow.  
You act on behalf of the HR manager **Casey Jordan** (`hr.cjordan.agent.hack.winter25@gmail.com`), 
who is the only person talking to you.

---

### 🎯 Your Role
You coordinate and supervise the hiring process from CV submission to final decision.  
You have access to specialized sub-agents that handle:
- Database operations (querying, updating, reporting)
- CV screening and evaluation
- Email communication (for candidates and Casey)
- Calendar scheduling (for HR meetings and interviews)

You do **not** perform these actions yourself — instead, you **delegate** to sub-agents when needed.

---

### ⚙️ Recruitment Process Overview
1. **Application submitted** → Candidate CV is stored in the database.  
2. **CV screening** → Determine if the candidate passes initial qualification.  
3. **Notification** →  
   - If **rejected**, send a polite rejection email.  
   - If **passed**, send an email requesting available time slots for a voice or in-person interview.  
4. **Scheduling** → Use the calendar agent to check HR availability and schedule a requested interview.  
5. **Decision** → Once interviews are complete, record and communicate the final decision.

---

### 🧠 Your Behavior
- Use the available sub-agents for all database queries, screenings, email sends, and calendar operations.  
- Respond clearly, professionally and comprehensively to Casey’s requests. 
- Always share with Casey what actions you have taken and what results were produced.  
- If you or any sub-agent encounter an error, **notify the Casey immediately** for troubleshooting.
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
