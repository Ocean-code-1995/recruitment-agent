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
        local_prompt_path: Optional[str] = None,
    ) -> str:
        """
        Load a prompt from:
            1. A local prompt file (if local_prompt_path is provided)
            2. PromptLayer (if no local path provided)

        Args:
            template_name: Name of the prompt template
            version: Version for PromptLayer
            label: Environment label
            local_prompt_path: Full path to local file OR directory containing prompt files

        Returns:
            str: Prompt content
        """

        # 1️⃣ If local path is provided, ALWAYS load from local
        if local_prompt_path:
            try:
                # If a directory is passed, append template_name + .txt
                if os.path.isdir(local_prompt_path):
                    file_path = os.path.join(local_prompt_path, f"{template_name}.txt")
                else:
                    file_path = local_prompt_path

                with open(file_path, "r", encoding="utf-8") as f:
                    print(f"📄 Loaded prompt '{template_name}' from local file: {file_path}", flush=True)
                    return f.read()

            except Exception as e:
                raise ValueError(
                    f"❌ Failed to load local prompt at '{local_prompt_path}': {e}"
                )

        # 2️⃣ Otherwise, fall back to PromptLayer
        label = label or self.environment

        if self.client:
            try:
                response = self.client.run(
                    prompt_name=template_name,
                    input_variables={},
                    tags=[label],
                )

                if isinstance(response, dict):
                    prompt_content = response.get("output") or str(response)
                else:
                    prompt_content = str(response)

                print(
                    f"📋 Loaded prompt '{template_name}' from PromptLayer (env={label})",
                    flush=True # force the output to the buffer immediately, 
                               # ensuring it shows up in the docker compose log stream immediately.
                )
                return prompt_content

            except Exception as e:
                raise ValueError(
                    f"❌ PromptLayer failed to load '{template_name}': {e}"
                )

        raise ValueError(
            f"❌ No local_prompt_path provided and PromptLayer is unavailable."
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

    def clear_cache(self) -> None:
        """Clear the prompt cache.
        """
        self.get_prompt.cache_clear()
        print("🗑️  Prompt cache cleared")


    def set_environment(self, environment: str) -> None:
        """
        Change the environment label for subsequent prompt requests.

        Args:
            environment: New environment (dev, staging, production)
        """
        self.environment = environment
        self.clear_cache()  # Clear cache since environment changed
        print(f"🔄 Environment changed to: {environment}")
