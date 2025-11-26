from typing import NamedTuple, Literal, Union, Any
from langchain_core.messages import AIMessage

class TokenStream(NamedTuple):
    """Represents a single streamed update emitted by the agent.
    """
    type: Literal["messages", "values"]
    data: Union[list[AIMessage], dict[str, Any]]