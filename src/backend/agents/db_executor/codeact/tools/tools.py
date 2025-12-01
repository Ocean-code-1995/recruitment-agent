import inspect
from langchain_core.tools import StructuredTool
from typing import Optional
from pathlib import Path

# Example tools
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b

def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    return a / b

def subtract(a: float, b: float) -> float:
    """Subtract two numbers."""
    return a - b

# Prompt creation
def create_default_prompt(
    tools: list,
    system_prompt: Optional[str] = None,
    base_prompt: str = "original.txt",
) -> str:
    template_path = Path(__file__).parent.parent / "prompts" / base_prompt
    template = template_path.read_text()

    tool_strings = []
    for t in tools:
        func = t.func if isinstance(t, StructuredTool) else t
        sig = inspect.signature(func)
        doc = (func.__doc__ or "").strip()
        tool_strings.append(
            f"def {func.__name__}{sig}:\n    \"\"\"{doc}\"\"\"\n    ..."
        )
    tools_str = "\n\n".join(tool_strings)

    prompt = template.replace("{tools}", tools_str)

    if system_prompt:
        prompt = f"{system_prompt}\n\n{prompt}"

    return prompt



if __name__ == "__main__":
    tools = [multiply, divide, subtract]
    print(create_default_prompt(tools, system_prompt="You are a coding agent."))
