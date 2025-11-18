"""
LangChain tools for voice screening agent.
These tools can be used by supervisor agents to trigger voice screening.
"""
from langchain_core.tools import tool
from typing import Optional
import os


@tool
def start_voice_screening_tool(
    candidate_id: str,
    phone_number: str
) -> str:
    """
    Initiate a voice screening call to a candidate.
    This tool starts an automated phone interview with the candidate.
    
    Args:
        candidate_id: UUID of the candidate to call
        phone_number: Phone number in E.164 format (e.g., +1234567890)
        
    Returns:
        str: Twilio Call SID for tracking the call
    """
    # Import here to avoid circular dependencies
    from src.agents.voice_screening.agent import VoiceScreeningAgent
    from src.core.configs.agent import AgentConfig
    from src.core.configs.model import ModelConfig
    
    # Create agent instance
    model_config = ModelConfig(
        provider="openai",
        model_name="gpt-4o",
        temperature=0.0
    )
    agent_config = AgentConfig(
        name="voice_screening",
        description="Conducts voice screening interviews",
        model_config=model_config,
        system_prompt="You are a friendly HR assistant conducting a phone screening interview."
    )
    agent = VoiceScreeningAgent(agent_config)
    
    # Start the call
    call_sid = agent.start_voice_screening(candidate_id, phone_number)
    
    return f"Voice screening call initiated. Call SID: {call_sid}"


def get_voice_screening_tools():
    """
    Get all voice screening tools for use in LangChain agents.
    
    Returns:
        list: List of LangChain tools
    """
    return [start_voice_screening_tool]

