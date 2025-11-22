import re
import io
import builtins
import contextlib
from collections.abc import Generator
import inspect
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional, Sequence, Type, TypeVar, Union, Literal
import types
import json

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import StructuredTool
from langchain_core.tools import tool as create_tool
from langchain_core.messages import AIMessageChunk, AIMessage
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver

from codeact.schemas import TokenStream
from codeact.schemas.openai_key import OpenAIApiKey
from codeact.utils import pretty_print_state




class CodeActState(MessagesState):
    """State for CodeAct agent."""

    script: Optional[str]
    """The Python code script to be executed."""
    context: dict[str, Any]
    """Dictionary containing the execution context with available tools and variables."""

EvalFunction = Callable[[str, dict[str, Any]], tuple[str, dict[str, Any]]]
EvalCoroutine = Callable[[str, dict[str, Any]], Awaitable[tuple[str, dict[str, Any]]]]

StateSchema = TypeVar("StateSchema", bound=CodeActState)
StateSchemaType = Type[StateSchema]


import inspect
from pathlib import Path
import tiktoken
from typing import Any, Optional, Union, Sequence
from langchain_core.tools import StructuredTool


class CodeActAgent:
    def __init__(
        self,
        model_name: str,
        model_provider: str,
        tools: Optional[Sequence] = None,
        eval_fn=None,
        system_prompt: Union[str, Path] = None,
        bind_tools: bool = False,
        memory: bool = True,
    ) -> None:
        """
        Parameters
        ----------
        - model_name : str
            The name of the chat model to use (e.g., "gpt-4o").
        - model_provider : str
            The model provider (e.g., "openai").
        - tools : Optional[Sequence], optional
            A list of tools (functions or StructuredTool) available to the agent.
        - eval_fn : Optional[EvalFunction or EvalCoroutine], optional
            The function or coroutine to evaluate generated code. If None, uses default_eval.
        - system_prompt : Union[str, Path], optional
            The system prompt as a file path or raw string.
        - bind_tools : bool, optional
            Whether to bind tool signatures and docstrings into the system prompt.
        - memory : bool, optional
            Whether to enable memory checkpointing.
        """
        self.model_name = model_name
        self.model_provider = model_provider
        self.tools = tools or []
        self.eval_fn = eval_fn or self.default_eval
        self.system_prompt = system_prompt
        self.bind_tools = bind_tools
        self.memory = memory

        # Initialize components
        self.model = init_chat_model(model_name, model_provider=model_provider)
        self.prompt = self._create_system_prompt()
        self.agent = self._create_codeact(self.model, self.tools, self.eval_fn)

        checkpointer = MemorySaver() if memory else None
        self.compiled_agent = self.agent.compile(checkpointer=checkpointer)


    def _create_system_prompt(self) -> tuple[str, dict[str, int]]:
        """Build the final system prompt and compute token counts.
        """
        system_text = self._load_prompt(self.system_prompt)
        if not system_text:
            raise ValueError("`system_prompt` must be provided as a file path or string.")

        system_text = system_text.strip()
        
        # Base version (without tools)
        prompt_text = system_text

        # If bind_tools enabled, build and append
        if self.bind_tools:
            if not self.tools:
                print("[⚠️] bind_tools=True but no tools provided. Skipping tool injection.")
            else:
                tools_text = self._build_tool_context()
                prompt_text = f"{system_text.strip()}\n\n{tools_text.strip()}"

        # Compute token counts
        tokens_without_tools = self._count_tokens(system_text)
        tokens_with_tools = self._count_tokens(prompt_text)

        # Print summary neatly
        print(
            f"🧮 System prompt token count:\n"
            f"       - Without tools: {tokens_without_tools}\n"
            f"       - With tools:    {tokens_with_tools}"
        )

        return prompt_text


    def _build_tool_context(self) -> str:
        """Constructs the tool context block with docstrings and signatures.
        """
        tool_strings = []
        for t in self.tools:
            func = t.func if isinstance(t, StructuredTool) else t
            sig = inspect.signature(func)
            doc = (func.__doc__ or "").strip()
            tool_strings.append(
                f"def {func.__name__}{sig}:\n    \"\"\"{doc}\"\"\"\n    ..."
            )

        joined_tools = "\n\n".join(tool_strings)
        return (
            "\n\nNote that you have access to the following predefined tools:\n\n"
            f"{joined_tools}"
        )

    @staticmethod
    def _load_prompt(p: Optional[Union[str, Path]]) -> Optional[str]:
        """Load a prompt from file path or treat as raw string.
        """
        if p is None:
            return None
        p = Path(p)
        if p.exists() and p.is_file():
            return p.read_text(encoding="utf-8")
        return str(p)

    def _count_tokens(self, text: str) -> int:
        """Count tokens for a given text.
        """
        try:
            enc = tiktoken.encoding_for_model(self.model_name)
        except Exception:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))



    def _extract_and_combine_codeblocks(self, text: str) -> str:
        """ 
        Extract and combine code blocks from the model completion.
        Helper function to execute extracted code in sandbox environment.
        """
        pattern = r"(?:^|\n)```(.*?)(?:```(?:\n|$))"   #r"(?:^|\n)```(.*?)(?:```(?:\n|$))"
        code_blocks = re.findall(pattern, text, re.DOTALL)
        if not code_blocks:
            return ""
        processed = []
        for block in code_blocks:
            lines = block.strip().split("\n")
            if lines and (not lines[0].strip() or " " not in lines[0].strip()):
                block = "\n".join(lines[1:])
            processed.append(block)
        return "\n\n".join(processed)


    @staticmethod
    def default_eval(code: str, _locals: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Evaluate the code in the sandbox.
        """
        original_keys = set(_locals.keys())
        try:
            with contextlib.redirect_stdout(io.StringIO()) as f:
                exec(code, builtins.__dict__, _locals)
            result = f.getvalue() or "<code ran, no output printed to stdout>"
        except Exception as e:
            result = f"Error during execution: {repr(e)}"
        new_keys = set(_locals.keys()) - original_keys
        new_vars = {key: _locals[key] for key in new_keys}
        return result, new_vars

    @staticmethod
    def _filter_serializable(d: dict[str, Any]) -> dict[str, Any]:
        """Keep only JSON/msgpack-serializable values (basic Python types).
        """
        serializable_types = (
            str, int, float, bool, list, dict, type(None)
        )
        return {
            k: v for k, v in d.items() if isinstance(v, serializable_types)
        }


    def _create_codeact(
        self,
        model: BaseChatModel,
        tools: Sequence[Union[StructuredTool, Callable]],
        eval_fn: Union[EvalFunction, EvalCoroutine],
        *,
        state_schema: StateSchemaType = CodeActState,
    ) -> StateGraph:
        """Create a LangGraph state graph for the CodeAct agent.
        """
        tools = [
            t if isinstance(t, StructuredTool) else create_tool(t)
            for t in tools
        ]
        self.tools_context = {tool.name: tool.func for tool in tools}

        def call_model_stream(state: StateSchema):
            messages = [{"role": "system", "content": self.prompt}] + state["messages"]

            # Accumulate into one combined chunk
            accumulated: AIMessageChunk | None = None

            # stream partial tokens as AIMessagesChunks wioth .content = "Hel",
            for delta in self.model.stream(messages):
                if accumulated is None:
                    accumulated = delta
                else:
                    accumulated = accumulated + delta   # merge chunks

                # yield partial update immediately (for streaming UI)
                yield Command(update={"messages": [delta], "script": None})

            # after streaming completes
            if accumulated is None:
                yield Command(update={"messages": [], "script": None})
                return  # nothing came back

            # Convert merged chunks into a final message
            full_text = accumulated.content or ""

            # Check for code blocks
            code = self._extract_and_combine_codeblocks(full_text)

            if code:
                # Create a fake tool call entry
                tool_call_id = "sandbox"
                fake_tool_call = {
                    "id": tool_call_id,
                    "type": "function",
                    "function": {
                        "name": "sandbox",
                        "arguments": code
                    }
                }
                # Patch the assistant message with tool_calls
                accumulated.additional_kwargs = {"tool_calls": [fake_tool_call]}

                #  Pass both the patched assistant message and code to sandbox
                yield Command(
                    goto="sandbox",
                    update={
                        "messages": [accumulated],
                        "script": code
                    }
                )
            else:
                yield Command(
                    update={
                        "messages": [accumulated],
                        "script": None
                    }
                )


        if inspect.iscoroutinefunction(eval_fn):

            async def sandbox(state: StateSchema):
                """Run the code in the sandbox and return a proper OpenAI tool message.
                """
                existing_context = state.get("context", {})

                # Combine persistent context with runtime-only tools
                exec_context = {**existing_context, **self.tools_context}

                # Get tool_call_id for traceability
                prev_msgs = state.get("messages", [])
                tool_call_id = "sandbox"
                for msg in reversed(prev_msgs):
                    if hasattr(msg, "additional_kwargs") and msg.additional_kwargs.get("tool_calls"):
                        tool_call_id = msg.additional_kwargs["tool_calls"][0]["id"]
                        break

                # Execute user code
                output, new_vars = await eval_fn(state["script"], exec_context)

                # Only persist serializable data
                serializable_new_vars = self._filter_serializable(new_vars)
                new_context = {**existing_context, **serializable_new_vars}

                # Return OpenAI-compliant tool result
                return {
                    "messages": [
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": "sandbox",
                            "content": (
                                f"Sandbox result of your executed code:\n{json.dumps(output)}"
                                if not isinstance(output, str)
                                else f"Sandbox result of your executed code:\n{output}"
                                # Keep as string if already string else JSON serialize
                            ),

                        }
                    ],
                    "context": new_context,
                }


        else:
            def sandbox(state: StateSchema):
                """Run the code in the sandbox and return a proper OpenAI tool message.
                """
                existing_context = state.get("context", {})

                # Combine persistent context with runtime-only tools
                exec_context = {**existing_context, **self.tools_context}

                # Get tool_call_id for traceability
                prev_msgs = state.get("messages", [])
                tool_call_id = "sandbox"
                for msg in reversed(prev_msgs):
                    if hasattr(msg, "additional_kwargs") and msg.additional_kwargs.get("tool_calls"):
                        tool_call_id = msg.additional_kwargs["tool_calls"][0]["id"]
                        break

                # Execute user code
                output, new_vars = eval_fn(state["script"], exec_context)

                # Only persist serializable data
                serializable_new_vars = self._filter_serializable(new_vars)
                new_context = {**existing_context, **serializable_new_vars}

                # Return OpenAI-compliant tool result
                return {
                    "messages": [
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": "sandbox",
                            "content": (
                                f"Sandbox result of your executed code:\n{json.dumps(output)}"
                                if not isinstance(output, str)
                                else f"Sandbox result of your executed code:\n{output}"
                            ),
                            # Keep as string if already string else JSON serialize      
                        }
                    ],
                    "context": new_context,
                }

        # --- Build the state graph ---
        agent = StateGraph(state_schema)
        agent.add_node(call_model_stream, destinations=(END, "sandbox"))
        agent.add_node(sandbox)
        agent.add_edge(START, "call_model_stream")
        agent.add_edge("sandbox", "call_model_stream")
        return agent
        

    def stream(
        self,
        messages: list[dict],
        thread_id: int = 1
    ) -> Generator[
            TokenStream,
            None,
            None
        ]:
        """
        Generator yielding agent outputs during execution.

        Yields
        ------
        tuple[str, Any]
            - "messages": list of chat message objects (e.g. AIMessage)
            - "values":   dict of current agent state (messages, script, context)

        Example
        -------
        messages [AIMessage(content="```python\nresult = 3*7+5\nprint(result)\n```")]
        values   {"messages": [...], "script": "result = 3*7+5\nprint(result)", "context": {}}
        messages [AIMessage(content="26")]
        values   {"messages": [...], "script": None, "context": {"result": 26}}
        """

        config = {
            "configurable": {
                "thread_id": thread_id
                }
        }
        for typ, chunk in self.compiled_agent.stream(
            {"messages": messages},
            stream_mode=["values", "messages"],
            config=config,
        ):
            yield TokenStream(type=typ, data=chunk)

    #------- BEFORE DB AGENT EXECUTOR -------#
    #def generate(
    #    self,
    #    messages: list[dict],
    #    thread_id: int = 1
    #) -> dict[str, Any]:
    #    """
    #    Run the agent to completion and return final state.#

    #    Returns
    #    -------
    #    dict
    #        Final agent state containing messages, script, context.
    #    """
    #    config = {
    #        "configurable": {
    #            "thread_id": thread_id
    #            }
    #    }
    #    final_state = self.compiled_agent.generate(
    #        {"messages": messages},
    #        config=config,
    #    )
    #    return final_state
    #------- BEFORE DB AGENT EXECUTOR -------#
    def generate(
        self,
        messages: list[dict],
        thread_id: int = 1,
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        *** Test method for db executor ***
        """
        config = {
            "configurable": {"thread_id": thread_id}
        }
        state = {
            "messages": messages, "context": context or {}
        }
        return self.compiled_agent.generate(
            state, config=config
        )




if __name__ == "__main__":
    """
    Run the CodeActAgent in different modes:
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    - python -m agent.core.codeact --mode chat
    - python -m agent.core.codeact --mode debug
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """
    import argparse
    import json
    from rich.console import Console

    # Validate environment (api key) before doing *anything* else
    OpenAIApiKey.validate_environment()

    # --- Parse args ---
    parser = argparse.ArgumentParser(description="Run CodeActAgent in different modes")
    parser.add_argument(
        "--mode",
        choices=["chat", "debug"],
        default="chat",
        help="Mode: 'chat' for normal conversation, 'debug' to also show state values."
    )
    args = parser.parse_args()

    # --- Instantiate agent ---
    agent = CodeActAgent(
        model_name="gpt-4o",
        model_provider="openai",
        tools=[],
        eval_fn=CodeActAgent.default_eval,   # built-in evaluator
        system_prompt="agent/prompts/local_archive/original.txt",
        bind_tools=False,
        memory=True
    )
    #~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # --- Conversation loop ---#
    #~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # --- Rich console setup ---
    console = Console(width=100, soft_wrap=False)

    while True:
        user_query = input("\n😎 USER:\n››› ")
        if user_query.lower() == "exit":
            break

        messages = [{"role": "user", "content": user_query}]

        # --- Dynamic assistant header (chat only) ---
        if args.mode == "chat":
            console.print("\n🧠 [bold magenta]Assistant[/]:\n››› ", end="")

        # --- Stream agent responses ---
        for typ, chunk in agent.stream(messages):
            if args.mode == "chat" and typ == "messages":
                print(chunk[0].content, end="", flush=True)

            elif args.mode == "debug":
                if typ == "values":
                    # Print only the nicely formatted message + optional context
                    pretty_print_state(chunk, show_context=False)

        print("\n")

