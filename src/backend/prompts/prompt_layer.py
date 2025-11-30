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
        latest_version: bool = False,
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
            latest_version: If True, explicitly fetch the latest version (ignoring label)

        Returns:
            str: Prompt content
        """

        # 1️⃣ Try PromptLayer FIRST if client is available
        label = label or self.environment

        if self.client:
            try:
                if latest_version:
                    # Fetch the latest template definition directly without execution
                    response = self.client.templates.get(template_name)
                    
                    # Extract the prompt text from llm_kwargs (preferred) or prompt_template
                    prompt_content = None
                    
                    # Strategy 1: Try llm_kwargs (cleanest format)
                    if isinstance(response, dict) and "llm_kwargs" in response:
                        messages = response["llm_kwargs"].get("messages", [])
                        # Try to find system message
                        for msg in messages:
                            if msg.get("role") == "system":
                                prompt_content = msg.get("content")
                                break
                        # Fallback to first message
                        if prompt_content is None and messages:
                            prompt_content = messages[0].get("content")

                    # Strategy 2: Try prompt_template dictionary structure
                    if prompt_content is None and isinstance(response, dict) and "prompt_template" in response:
                         pt = response["prompt_template"]
                         if isinstance(pt, dict) and "messages" in pt:
                             messages = pt["messages"]
                             for msg in messages:
                                 # Check role if available
                                 if msg.get("role") == "system" and "content" in msg:
                                     content_list = msg["content"]
                                     if isinstance(content_list, list) and content_list:
                                         # Extract text from content list [{'type': 'text', 'text': '...'}]
                                         for item in content_list:
                                             if item.get("type") == "text":
                                                 prompt_content = item.get("text")
                                                 break
                                 if prompt_content: break
                             
                             # Fallback: first message content
                             if prompt_content is None and messages and "content" in messages[0]:
                                 content_list = messages[0]["content"]
                                 if isinstance(content_list, list) and content_list:
                                     for item in content_list:
                                         if item.get("type") == "text":
                                             prompt_content = item.get("text")
                                             break

                    # Fallback: Stringify if nothing else found
                    if prompt_content is None:
                        prompt_content = str(response)

                    # Try to extract version metadata if available
                    version_info = ""
                    if isinstance(response, dict) and "version" in response:
                        version_info = f" (v{response.get('version')})"
                    elif hasattr(response, "version"): # Some client objects might have it
                        version_info = f" (v{response.version})"

                    print(
                        f"📋 Loaded prompt '{template_name}' from PromptLayer (latest version){version_info}",
                        flush=True
                    )
                    return prompt_content

                # Standard flow using labels (existing logic)
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
                print(f"⚠️  PromptLayer failed: {e}. Falling back to local templates...", flush=True)
        
        # 2️⃣ Fall back to local files if PromptLayer failed or unavailable
        if local_prompt_path:
            try:
                # If a directory is passed, append template_name + .txt
                if os.path.isdir(local_prompt_path):
                    # Try exact match first: template_name.txt (case-sensitive)
                    file_path = os.path.join(local_prompt_path, f"{template_name}.txt")
                    
                    # If not found, try subdirectory with lowercase template_name
                    if not os.path.exists(file_path):
                        lowercase_name = template_name.lower()
                        file_path = os.path.join(local_prompt_path, lowercase_name, "v1.txt")
                    
                    # If still not found, try subdirectory with original template_name
                    if not os.path.exists(file_path):
                        file_path = os.path.join(local_prompt_path, template_name, "v1.txt")
                else:
                    file_path = local_prompt_path

                with open(file_path, "r", encoding="utf-8") as f:
                    print(f"📄 Loaded prompt '{template_name}' from local file: {file_path}", flush=True)
                    return f.read()

            except Exception as e:
                raise ValueError(
                    f"❌ Failed to load '{template_name}' from local path '{local_prompt_path}': {e}"
                )
        
        raise ValueError(
            f"❌ Failed to load '{template_name}': PromptLayer unavailable and no local_prompt_path provided."
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
