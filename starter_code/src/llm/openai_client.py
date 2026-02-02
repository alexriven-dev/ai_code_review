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

        Always returns text or raises an error.
        Never returns empty string silently.
        """

        try:
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

        except Exception as e:
            raise RuntimeError(f"OpenAI API request failed: {e}") from e

        # --------------------------------------------------
        # Preferred: SDK helper
        # --------------------------------------------------

        if hasattr(response, "output_text") and response.output_text:
            return response.output_text.strip()

        # --------------------------------------------------
        # Fallback: manual extraction
        # --------------------------------------------------

        texts: List[str] = []

        for item in response.output or []:

            # New format
            if hasattr(item, "content"):
                for part in item.content:
                    if part.get("type") == "output_text":
                        texts.append(part.get("text", ""))

            # Legacy format
            if hasattr(item, "text"):
                texts.append(item.text)

        final_text = "\n".join(t for t in texts if t).strip()

        if final_text:
            return final_text

        # --------------------------------------------------
        # Hard failure (no silent empty responses)
        # --------------------------------------------------

        raise RuntimeError(
            "OpenAI returned no usable text output. "
            f"Raw response: {response}"
        )
