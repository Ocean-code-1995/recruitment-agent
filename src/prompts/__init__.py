"""
Prompt Registry Module
======================

Centralized prompt management using PromptLayer with optional local files.
Provides a singleton PromptManager instance for loading prompts from:
1. Local prompt files (if local_prompt_path is provided)
2. PromptLayer cloud service (if PROMPTLAYER_API_KEY is set)
"""

import os
from .prompt_layer import PromptManager

# Path to the templates folder inside the package
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

# Singleton PromptManager instance
_prompt_manager = PromptManager(environment=os.getenv("PROMPT_ENVIRONMENT", "production"))


def get_prompt(
    template_name: str,
    version: int = None,
    label: str = None,
    local_prompt_path: str = None,
) -> str:
    """
    Load a prompt either from:
    - A local file (if local_prompt_path is provided)
    - PromptLayer (default)

    Args:
        template_name: Name of the prompt template
        version: PromptLayer version
        label: Environment label for PromptLayer
        local_prompt_path: Path to local file or directory containing prompt

    Returns:
        str: Prompt content
    """
    return _prompt_manager.get_prompt(
        template_name=template_name,
        version=version,
        label=label,
        local_prompt_path=local_prompt_path,
    )


def get_prompt_manager() -> PromptManager:
    """Return singleton PromptManager."""
    return _prompt_manager


__all__ = [
    "get_prompt",
    "get_prompt_manager",
    "PromptManager",
    "TEMPLATES_DIR"
]
