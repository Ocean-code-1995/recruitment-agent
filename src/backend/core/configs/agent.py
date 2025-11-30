# src/core/configs/agent.py
from typing import List, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, ConfigDict
from src.backend.core.configs.model import ModelConfig


class AgentConfig(BaseModel):
    """
    Configuration schema for initializing LangGraph agents.

    Notes:
        Pydantic setting ``model_config = ConfigDict(arbitrary_types_allowed=True)``
        allows this model to include arbitrary Python objects such as LangChain
        tools or runtime components that are not JSON-serializable or Pydantic
        models. These objects (e.g., `BaseTool` instances) are accepted as-is
        without validation or serialization, while all standard fields
        (strings, numbers, nested Pydantic models) remain fully validated.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )
    name: str = Field(
        ...,
        description="Unique name of the agent."
    )
    description: str = Field(
        ...,
        description="Short description of what the agent does."
    )
    model_config: ModelConfig = Field(
        ...,
        description="Configuration of the underlying LLM model."
    )
    tools: Optional[List[BaseTool]] = Field(
        default_factory=list,
        description="List of tools available to the agent."
    )
    system_prompt: str = Field(
        default="",
        description="System prompt to condition the agent's behavior."
    )
    max_iterations: Optional[int] = Field(
        default=None,
        description="Optional limit on reasoning iterations."
    )
