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
# Force local-only prompts; disable remote PromptLayer client if present
_prompt_manager.client = None


def get_prompt(
    template_name: str,
    version: int = None,
    label: str = None,
    local_prompt_path: str = None,
    latest_version: bool = False,
) -> str:
    """
    Load a prompt from local templates only (PromptLayer disabled here).

    Strategy:
    - If local_prompt_path is provided, use it.
    - Otherwise, use the default templates directory.
    """
    # Normalize template name to match folder names (lowercase)
    if template_name:
        template_name = template_name.lower()

    if local_prompt_path:
        if not os.path.isabs(local_prompt_path):
            local_prompt_path = os.path.join(TEMPLATES_DIR, local_prompt_path)
    else:
        local_prompt_path = TEMPLATES_DIR

    return _prompt_manager.get_prompt(
        template_name=template_name,
        version=version,
        label=label,
        local_prompt_path=local_prompt_path,
        latest_version=latest_version,
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
