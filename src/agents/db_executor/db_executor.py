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
from src.prompts import get_prompt


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
        system_prompt = get_prompt("db_executor")
        agent = CodeActAgent(
            model_name="gpt-4o",
            model_provider="openai",
            tools=[],
            eval_fn=CodeActAgent.default_eval,
            system_prompt=system_prompt,
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
