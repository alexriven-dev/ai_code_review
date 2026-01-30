"""
OpenAI LLM client implementation.
"""

import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from .base import LLMClient


class OpenAIClient(LLMClient):
    """OpenAI implementation of the LLMClient interface."""

    def __init__(self, model: str = "gpt-4.1-mini"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not found in environment")

        self._client = OpenAI(api_key=api_key)
        self._model = model

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Generate a completion using OpenAI Responses API.
        """
        response = self._client.responses.create(
            model=self._model,
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            tools=tools,
        )

        # Extract text safely
        for item in response.output:
            if item["type"] == "output_text":
                return item["text"]

        return ""
