from .codeact.core.codeact import CodeActAgent
from src.backend.database.candidates.client import SessionLocal
from src.backend.database.candidates.models import (
    Candidate,
    CVScreeningResult,
    VoiceScreeningResult,
    InterviewScheduling,
    FinalDecision,
)
from src.backend.state.candidate import CandidateStatus, InterviewStatus, DecisionStatus
from langchain_core.tools import tool
from typing import Dict, Any
from src.backend.database.candidates import evaluate_cv_screening_decision
from src.backend.prompts import get_prompt


SYSTEM_PROMPT = get_prompt(
    template_name="DB_Executor",
    local_prompt_path="db_executor/v2.txt",
)


@tool
def db_executor(query: str) -> str:
    """
    Consumes a natural-language query as input which is being translated into 
    SQLAlchemy ORM code by the coding agent. Finally, the code is executed against 
    the database and the result is returned.

    Args:
        query (str): Natural-language database query.
    Returns:
        str: The natural language summary of the result or error.
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
        "CandidateStatus": CandidateStatus,
        "InterviewStatus": InterviewStatus,
        "DecisionStatus": DecisionStatus,
    }

    try:
        # 2. Initialize CodeAct agent with system prompt
        agent = CodeActAgent(
            model_name="gpt-4o",
            model_provider="openai",
            tools=[evaluate_cv_screening_decision],  # Passed as a tool
            eval_fn=CodeActAgent.default_eval,
            system_prompt=SYSTEM_PROMPT,
            bind_tools=True, # Enable tool binding so agent sees signature
            memory=False,   # optional — can enable if you want persistent thread context
        )

        # 3. Run natural-language query
        messages = [{"role": "user", "content": query}]
        final_state = agent.generate(messages, context=context)

        # 4. Extract model output
        # Return the final natural language response from the assistant
        output_msg = final_state["messages"][-1].content if final_state.get("messages") else ""
        
        return output_msg

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n❌ Error in db_executor: {e}\n{error_trace}")
        
        # Return a clear text error message
        return f"The DB Executor encountered an internal error: {str(e)}"

    finally:
        session.close()



if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    query = "Fetch all candidates and their status."
    
    console.rule("[bold magenta]DB Executor Test Run[/bold magenta]")
    console.print(f"[cyan]Query:[/] {query}\n")

    result = db_executor(query)

    # 🧠 Show model result nicely
    console.print(Panel.fit(result, title="🧠 Model Output", border_style="blue"))

    console.rule("[bold green]End of Execution[/bold green]")
