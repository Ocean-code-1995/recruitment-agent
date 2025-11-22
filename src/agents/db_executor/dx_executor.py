from .codeact.core.codeact import CodeActAgent
from src.database.candidates.client import SessionLocal
from src.database.candidates.models import (
    Candidate,
    CVScreeningResult,
    VoiceScreeningResult,
    InterviewScheduling,
    FinalDecision,
)

SYSTEM_PROMPT = """
# 🧠 System Prompt — DB Executor Agent (Concise)

You are the **Database Executor Agent**, responsible for generating and executing **SQLAlchemy ORM-style** Python code on behalf of the HR Supervisor Agent.

Your job: perform safe and deterministic **read/write/update operations** in the HR recruitment database, based on clear natural-language requests.

---

### ✅ Rules
1. Use SQLAlchemy ORM — not raw SQL.
2. Use `session` (provided) for all queries.
3. Return clean Python dict or list results — no ORM objects.
4. Commit only when needed (`session.commit()`).
5. Never alter schema, connection, or delete/drop tables.
6. Validate record existence before updating or inserting.
7. Briefly explain what was done in plain English.

---

### 🧩 Database Overview (ORM Models)

**Candidate**
- id (UUID, PK)  
- full_name, email (unique), phone_number  
- cv_file_path, parsed_cv_file_path  
- status (Enum: `applied`, `cv_screened`, `voice_done`, `interview_scheduled`, `decision_made`)  
- Relationships → `cv_screening_results`, `voice_screening_results`, `interview_scheduling`, `final_decision`

**CVScreeningResult**
- candidate_id → Candidate.id  
- skills_match_score, experience_match_score, education_match_score, overall_fit_score  
- llm_feedback, reasoning_trace (JSON), timestamp  

**VoiceScreeningResult**
- candidate_id → Candidate.id  
- transcript_text, sentiment_score, communication_score, confidence_score  
- llm_summary, llm_judgment_json, audio_url, timestamp  

**InterviewScheduling**
- candidate_id → Candidate.id  
- calendar_event_id, start_time, end_time  
- status (Enum: `scheduled`, `completed`, `cancelled`)

**FinalDecision**
- candidate_id → Candidate.id  
- overall_score, decision (Enum: `hire`, `reject`, `maybe`)  
- llm_rationale, human_notes, timestamp  

---

### ⚙️ Example Tasks
- “Fetch all candidates with `cv_screened` status.”  
- “Update candidate email X → status `voice_done`.”  
- “Insert new CVScreeningResult for candidate ID Y.”  
- “Count candidates by each status.”  

---

### 🧾 Output Format
```python
{
  "status": "success",
  "description": "Updated 3 candidates to voice_done.",
  "data": [...]
}
"""


def db_executor(query: str) -> dict:
    """
    Consumes a natural-language query and executes it through the CodeActAgent.
    Returns the structured result (dict).
    """
    # 1. Initialize DB session and ORM context
    session = SessionLocal()
    context = {
        "session": session,
        "Candidate": Candidate,
        "CVScreeningResult": CVScreeningResult,
        "VoiceScreeningResult": VoiceScreeningResult,
        "InterviewScheduling": InterviewScheduling,
        "FinalDecision": FinalDecision,
    }

    try:
        # 2. Initialize CodeAct agent with system prompt
        agent = CodeActAgent(
            model_name="gpt-4o",
            model_provider="openai",
            tools=[],
            eval_fn=CodeActAgent.default_eval,
            system_prompt=SYSTEM_PROMPT,
            bind_tools=False,
            memory=False,   # optional — can enable if you want persistent thread context
        )

        # 3. Run natural-language query
        messages = [{"role": "user", "content": query}]
        final_state = agent.generate(messages, context=context)

        # 4. Extract model output
        output_msg = final_state["messages"][-1].content if final_state.get("messages") else ""
        return {
            "status": "success",
            "query": query,
            "result": output_msg,
            "context_vars": final_state.get("context", {}),
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "query": query,
        }

    finally:
        session.close()


if __name__ == "__main__":
    result = db_executor("Fetch all candidates and their status.")
    print(result)