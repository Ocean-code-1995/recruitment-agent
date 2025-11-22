from .codeact.core.codeact import CodeActAgent
from src.database.candidates.client import SessionLocal
from src.database.candidates.models import (
    Candidate,
    CVScreeningResult,
    VoiceScreeningResult,
    InterviewScheduling,
    FinalDecision,
)
from langchain_core.tools import tool


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
# Note: All these models are already imported and available in the global context. 
# DO NOT try to import them again. Use them directly (e.g. `session.query(Candidate)...`).

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

🧾 Expected Execution Pattern
When asked to perform a task, you must:
1. Construct ORM-based Python code using session and the given models.
2. Store final results in a variable named result.
3. Print the results using:
```python
import json
print(json.dumps(result, indent=2, default=str))
```
4. Optionally, include a short explanatory comment after the code.

### 🧾 Output Format
```python
{
  "status": "success",
  "description": "Updated 3 candidates to voice_done.",
  "data": [...]
}
"""


@tool
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
    # define a consistent result structure from the start
    result_template = {
        "status": "error",
        "query": query,
        "result": "",
        "error": None,
        "context_vars": {},
        "debug_messages": [],
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
        
        # Debug: extract tool messages to see errors
        debug_messages = []
        if final_state.get("messages"):
            for msg in final_state["messages"]:
                role = getattr(msg, "role", "unknown")
                content = getattr(msg, "content", "")
                debug_messages.append(f"[{role}] {content}")

        # Filter out non-serializable objects from context_vars
        safe_context = {
            k: v for k, v in final_state.get("context", {}).items()
            if isinstance(v, (str, int, float, bool, list, dict, type(None)))
        }

        result_template.update({
            "status": "success",
            "result": output_msg,
            "context_vars": safe_context,
            "debug_messages": debug_messages,
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n❌ Error in db_executor: {e}\n{error_trace}")
        result_template.update({
            "status": "error",
            "error": str(e),
        })
    finally:
        session.close()

    return result_template

if __name__ == "__main__":
    #import json
    #result = db_executor("Fetch all candidates and their status.")
    #print(json.dumps(result, indent=2, ensure_ascii=False)) 

    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.json import JSON
    from rich.syntax import Syntax

    console = Console()
    query = "Fetch all candidates and their status."
    result = db_executor(query)

    console.rule("[bold magenta]DB Executor Test Run[/bold magenta]")
    console.print(f"[cyan]Query:[/] {query}\n")

    status_color = "green" if result["status"] == "success" else "red"
    console.print(f"[{status_color}]Status:[/] {result['status']}")

    # 🧠 Show model result nicely
    console.print(Panel.fit(result["result"], title="🧠 Model Output", border_style="blue"))

    # 🗂️ Show context vars (omit large objects)
    context_vars = ", ".join(result.get("context_vars", {}).keys()) or "None"
    console.print(f"\n[bold]Context Variables:[/bold] {context_vars}\n")

    # 🪶 Optionally show debug trace
    console.rule("[dim]Debug Trace[/dim]")
    for msg in result.get("debug_messages", []):
        if "```python" in msg:
            # Syntax-highlight code snippets
            code = msg.split("```python")[1].split("```")[0]
            console.print(Syntax(code.strip(), "python", theme="monokai", line_numbers=False))
        else:
            console.print(f"[dim]{msg}[/dim]")

    console.rule("[bold green]End of Execution[/bold green]")
