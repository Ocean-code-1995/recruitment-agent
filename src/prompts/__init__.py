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

    Strategy:
    - If local_prompt_path is explicitly passed, use it (Highest priority).
    - If PROMPTLAYER_API_KEY is set, assume we want Remote (local_prompt_path=None).
    - If NO API key, fallback to default local TEMPLATES_DIR.
    """
    if local_prompt_path:
        # If path is relative, assume it is inside templates/ directory
        if not os.path.isabs(local_prompt_path):
            local_prompt_path = os.path.join(TEMPLATES_DIR, local_prompt_path)
    else:
        # No path provided
        if os.getenv("PROMPTLAYER_API_KEY"):
            # User has API key -> Use Remote (pass None)
            local_prompt_path = None
        else:
            # No API key -> Force Local Default
            local_prompt_path = TEMPLATES_DIR

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
