#!/usr/bin/env python3
"""
PromptLayer Integration for Prompt Management
==============================================

This module provides a centralized way to manage prompts using PromptLayer platform.
Allows for versioned, labeled prompts that can be easily updated without code changes.
"""

import promptlayer
from promptlayer import PromptLayer
from dotenv import load_dotenv
import os
from typing import Dict, Any, Optional
from functools import lru_cache

load_dotenv()


class PromptManager:
    """
    Centralized prompt management using PromptLayer platform.
    link:
        - https://www.promptlayer.com

    Features:
    - Version control for prompts
    - Environment-based prompt labels (dev, staging, production)
    - Caching for performance
    - Fallback to local files if PromptLayer unavailable
    """

    def __init__(self, api_key: Optional[str] = None, environment: str = "production"):
        """
        Initialize PromptManager.

        Args:
            api_key: PromptLayer API key (defaults to PROMPTLAYER_API_KEY env var)
            environment: Environment label for prompts (dev, staging, production)
        """
        self.api_key = api_key or os.getenv("PROMPTLAYER_API_KEY")
        self.environment = environment
        self.client = None

        # Initialize client if API key is available
        if self.api_key:
            try:
                self.client = PromptLayer(api_key=self.api_key)
                print(f"✅ PromptLayer connected (environment: {environment})")

            except Exception as e:
                print(f"⚠️  PromptLayer connection failed: {e}")
                self.client = None
        else:
            print("⚠️ No PROMPTLAYER_API_KEY found, using local fallback")

    @lru_cache(maxsize=128)
    def get_prompt(
        self,
        template_name: str,
        version: Optional[int] = None,
        label: Optional[str] = None,
        fallback_path: Optional[str] = None
    ) -> str:
        """
        Get a prompt from PromptLayer with fallback to local file.

        Args:
            template_name: Name of the prompt template
            version: Specific version number (defaults to latest)
            label: Environment label (defaults to instance environment)
            fallback_path: Local file path if PromptLayer unavailable

        Returns:
            Prompt content as string

        Raises:
            ValueError: If prompt cannot be found and no fallback provided
        """
        # Use provided label or instance default
        label = label or self.environment

        # Try PromptLayer first
        if self.client:
            try:
                template_config = {
                    "label": label
                }
                if version:
                    template_config["version"] = version

                prompttemplate = self.client.templates.get(
                    template_name,
                    template_config
                )
                # Extract prompt content from response
                prompt_content = prompttemplate["llm_kwargs"]["messages"][0]["content"]
                print(f"📋 Loaded prompt '{template_name}' from PromptLayer (v{prompttemplate.get('version', 'latest')}, {label})")
                return prompt_content

            except Exception as e:
                print(f"⚠️ PromptLayer failed: {e}, trying fallback...")
                # Fall through to fallback instead of raising

        # Fallback to local file
        if fallback_path:
            try:
                with open(fallback_path, 'r') as f:
                    content = f.read()
                print(f"📂 Loaded prompt '{template_name}' from local file: {fallback_path}")
                return content
            except Exception as e:
                raise ValueError(
                    f"❌ Failed to load fallback file '{fallback_path}': {e}"
                )

        # Only raise if both PromptLayer AND fallback fail
        raise ValueError(
            f"Could not load prompt '{template_name}' from any source"
        )


    def list_available_prompts(self) -> Dict[str, Any]:
        """
        List all available prompts from PromptLayer.

        Returns:
            Dictionary of available prompts with metadata
        """
        if not self.client:
            return {"error": "PromptLayer client not available"}

        try:
            # This would depend on PromptLayer's API for listing templates
            # Placeholder implementation
            return {
                "message": "PromptLayer template listing not implemented in this version",
                "available_methods": [
                    "get_judge_prompt(simple=True/False)",
                    "get_agent_prompt(version=int)",
                    "get_prompt(template_name, version, label, fallback_path)"
                ]
            }
        except Exception as e:
            return {"error": f"Failed to list prompts: {e}"}

    def clear_cache(self):
        """Clear the prompt cache."""
        self.get_prompt.cache_clear()
        print("🗑️  Prompt cache cleared")

    def set_environment(self, environment: str):
        """
        Change the environment label for subsequent prompt requests.

        Args:
            environment: New environment (dev, staging, production)
        """
        self.environment = environment
        self.clear_cache()  # Clear cache since environment changed
        print(f"🔄 Environment changed to: {environment}")

