"""
Base class for LangGraph-based agents that serves an interface for building,
compiling, and executing custom agent graphs.

Alternatively you can also use `create_agent`, which implements a ReAct agent by default. 
It may be of particular interest, since it enables MiddleWare like `context summarization` 
and `human in the loop`, `dynamic model selection` out of the box.
links: 
    - create_agent: https://docs.langchain.com/oss/python/langchain/agents
    - middleware: https://docs.langchain.com/oss/python/langchain/middleware
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from langgraph.graph import StateGraph
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_openrouter import ChatOpenRouter

from src.core.configs.agent import AgentConfig


class BaseAgent(ABC):
    """Abstract base class for all LangGraph-based agents.
    """

    def __init__(self, config: AgentConfig) -> None:
        """Initialize the agent with configuration.
        """
        self.config = config
        self.name = config.name
        self.description = config.description
        self._graph: Optional[StateGraph] = None
        self._compiled_graph = None

        # Initialize model (tools are bound optionally via bind_tools)
        self.llm = self._init_model()

    # ~~~ ABSTRACT METHODS ~~~
    @abstractmethod
    def build_graph(self) -> StateGraph:
        """Build the agent's LangGraph structure.
        """
        pass

    # ~~~ MODEL INITIALIZATION ~~~
    def _init_model(self) -> ChatOpenAI:
        """Initialize LLM engine based on model provider.
        """
        model_cfg = self.config.model_config
        provider = model_cfg.provider.lower()

        if provider == "openai":
            return ChatOpenAI(
                model=model_cfg.model_name,
                api_key=model_cfg.get_api_key(),
                temperature=model_cfg.temperature,
                max_tokens=model_cfg.max_tokens,
                base_url=model_cfg.api_base,
            )
        elif provider == "openrouter":
            return ChatOpenRouter(
                model=model_cfg.model_name,
                api_key=model_cfg.get_api_key(),
                temperature=model_cfg.temperature,
                max_tokens=model_cfg.max_tokens,
                base_url=model_cfg.api_base,
            )
        else:
            raise NotImplementedError(
                f"Provider '{provider}' not supported yet."
            )


    def bind_tools(
            self,
            tools: Optional[List[BaseTool]] = None,
            strict: bool = True
    ) -> ChatOpenAI:
        """
        Optionally bind tools to the initialized model.

        Args:
            tools: List of tools to bind. Defaults to `self.config.tools` if not provided.
            strict: Enforce schema validation for tools.
        """
        if not hasattr(self, "llm"):
            raise RuntimeError("Model must be initialized before binding tools.")

        tools_to_bind = tools or self.config.tools
        if not tools_to_bind:
            return self.llm  # no-op

        self.llm = self.llm.bind_tools(tools_to_bind, strict=strict)
        return self.llm


    # ~~~ GRAPH MANAGEMENT~~~
    def compile(self, checkpointer=None, store=None) -> StateGraph:
        """Compile the agent graph for execution.
        """
        if self._graph is None:
            self._graph = self.build_graph()

        self._compiled_graph = self._graph.compile(checkpointer=checkpointer, store=store)
        return self._compiled_graph


    def get_graph(self) -> StateGraph:
        """Return compiled graph (compile if needed).
        """
        if self._compiled_graph is None:
            self.compile()
        return self._compiled_graph


    def visualize(self, output_path: Optional[str] = None):
        """Render the graph as a Mermaid diagram.
        """
        if self._compiled_graph is None:
            self.compile()
        return self._compiled_graph.get_graph().draw_mermaid_png(output_file_path=output_path)

    # ~~~ EXECUTION ~~~
    def invoke(
        self,
        input_data: Dict[str, object],
        config: Optional[Dict[str, object]] = None
    ) -> Dict[str, object]:
        """Execute the compiled agent.
        """
        if self._compiled_graph is None:
            self.compile()
        return self._compiled_graph.invoke(input_data, config)


    async def ainvoke(
        self,
        input_data: Dict[str, object],
        config: Optional[Dict[str, object]] = None
    ) -> Dict[str, object]:
        """Execute the agent asynchronously.
        """
        if self._compiled_graph is None:
            self.compile()
        return await self._compiled_graph.ainvoke(input_data, config)


    def stream(
        self,
        input_data: Dict[str, object],
        config: Optional[Dict[str, object]] = None
    ) -> Dict[str, object]:
        """Stream agent execution results.
        """
        if self._compiled_graph is None:
            self.compile()
        return self._compiled_graph.stream(input_data, config)

    # ~~~ UTILITIES ~~~
    def get_tools(self) -> List[BaseTool]:
        """Return the tools this agent can use.
        """
        return list(self.config.tools or [])


    def get_capabilities(self) -> List[str]:
        """List of agent capabilities (override in subclasses).
        """
        return []


    @property
    def metadata(self) -> Dict[str, object]:
        """Return agent metadata for discovery and routing.
        """
        return {
            "name": self.name,
            "description": self.description,
            "tools": [tool.name for tool in self.get_tools()],
            "capabilities": self.get_capabilities(),
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
