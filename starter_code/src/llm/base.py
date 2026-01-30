"""
LLM base interface.

All LLM providers (OpenAI, Claude, etc.) must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMClient(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Generate a completion from the LLM.

        Args:
            system_prompt: System-level instructions
            user_prompt: User content
            tools: Optional tool definitions

        Returns:
            Generated text
        """
        raise NotImplementedError
