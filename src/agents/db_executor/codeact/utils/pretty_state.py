import json
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

console = Console(width=100, soft_wrap=False)

_last_context_snapshot = None  # used to suppress repeated context
_last_message_ids = set()  # track printed messages



def serialize_message(msg) -> dict:
    """Convert LangChain message objects into serializable dicts."""
    if hasattr(msg, "dict"):
        return msg.dict()
    elif hasattr(msg, "__dict__"):
        return {k: serialize_message(v) for k, v in msg.__dict__.items()}
    elif isinstance(msg, list):
        return [serialize_message(v) for v in msg]
    elif isinstance(msg, dict):
        return {k: serialize_message(v) for k, v in msg.items()}
    else:
        return msg


def pretty_print_state(state: dict, show_context: bool = True) -> None:
    """
    Pretty-print the agent's state in a clean, color-coded way.

    Parameters
    ----------
    state : dict
        The LangGraph agent state chunk (from the stream).
    show_context : bool, optional
        Whether to display the context (default True).
        If True, only shows context when it has changed since last call.
    """
    global _last_context_snapshot

    # --- Display message chunks ---
    for msg in state.get("messages", []):

        msg_id = getattr(msg, "id", id(msg))
        if msg_id in _last_message_ids:
            continue  # skip duplicates
        _last_message_ids.add(msg_id)

        msg_dict = serialize_message(msg)
        msg_json = json.dumps(msg_dict, indent=2)

        if isinstance(msg, HumanMessage):
            color, title = "cyan", "🧑 HumanMessage"
        elif isinstance(msg, ToolMessage):
            color, title = "yellow", f"🧰 ToolMessage ({msg_dict.get('name','?')})"
        elif isinstance(msg, AIMessage):
            color, title = "magenta", "🤖 AIMessage"
        else:
            color, title = "white", "Other"

        syntax = Syntax(msg_json, "json", theme="monokai", line_numbers=False)
        console.print(Panel(syntax, title=title, border_style=color))

    # --- Optional context view ---
    #if show_context:
    #    context = state.get("context", {})
    #    if context and context != _last_context_snapshot:
    #        _last_context_snapshot = context.copy()  # cache for next comparison

    #        context_json = json.dumps(context, indent=2, default=str)
    #        syntax = Syntax(context_json, "json", theme="monokai", line_numbers=False)
     #       console.print(Panel(syntax, title="🧠 Context (updated)", border_style="green"))
