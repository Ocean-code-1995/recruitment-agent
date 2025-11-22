"""
Prompt Registry Module
======================

Centralized prompt management using PromptLayer with local fallbacks.
Provides a singleton PromptManager instance for loading prompts from:
1. PromptLayer cloud service (if PROMPTLAYER_API_KEY is set)
2. Local template files (fallback)
"""

import os
from .prompt_layer import PromptManager

# Get the absolute path to the templates directory
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

# Initialize singleton PromptManager
_prompt_manager = PromptManager(environment=os.getenv("PROMPT_ENVIRONMENT", "production"))


def get_prompt(template_name: str, version: int = None, label: str = None) -> str:
    """
    Get a prompt by template name with automatic fallback path resolution.
    
    Args:
        template_name: Name of the prompt template (e.g., 'db_executor', 'supervisor')
        version: Optional PromptLayer version
        label: Optional environment label (dev, staging, production)
    
    Returns:
        Prompt content as string
    
    Raises:
        ValueError: If prompt cannot be found
    """
    # Construct fallback path to local template file
    fallback_path = os.path.join(TEMPLATES_DIR, f"{template_name}.txt")
    
    # Try to get prompt from PromptLayer, fallback to local file
    return _prompt_manager.get_prompt(
        template_name=template_name,
        version=version,
        label=label,
        fallback_path=fallback_path
    )


def get_prompt_manager() -> PromptManager:
    """
    Get the singleton PromptManager instance.
    
    Returns:
        The global PromptManager instance
    """
    return _prompt_manager


__all__ = ["get_prompt", "get_prompt_manager", "PromptManager"]
