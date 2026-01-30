"""
SecurityAgent - analyzes code for security vulnerabilities.

Stage 3B implemented:
- Uses OpenAI via LLM adapter
- Emits thinking events
- Emits finding_discovered events
- Stores findings in SharedContext
"""

from typing import Any, Dict, List, Optional
import json

from .base_agent import BaseAgent
from ..llm.openai_client import OpenAIClient
from ..context.shared_context import SharedContext
from ..events import EventType


class SecurityAgent(BaseAgent):
    """Agent responsible for detecting security vulnerabilities."""

    def __init__(self, event_bus):
        super().__init__(
            agent_id="security_agent",
            agent_type="security",
            agent_config={},
            event_bus=event_bus,
        )
        self._llm = OpenAIClient()

    @property
    def system_prompt(self) -> str:
        return (
            "You are a security analysis agent reviewing Python code.\n"
            "Your task is to identify real, high-confidence security issues only.\n\n"
            "Focus on:\n"
            "- SQL injection\n"
            "- Command injection\n"
            "- Hardcoded secrets\n"
            "- Unsafe deserialization\n"
            "- Authentication / authorization flaws\n\n"
            "Rules:\n"
            "- Do NOT report speculative issues\n"
            "- Do NOT invent line numbers\n"
            "- If no issues exist, return an empty list\n\n"
            "Return findings strictly as JSON."
        )

    async def analyze(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze code for security vulnerabilities.

        Returns:
            Dict with findings list
        """
        await self._emit_agent_started("Starting security analysis")

        shared_context: Optional[SharedContext] = None
        if context and "shared_context" in context:
            shared_context = context["shared_context"]

        await self._emit_thinking("Scanning code for security-sensitive patterns")

        user_prompt = (
            "Analyze the following Python code for security vulnerabilities.\n\n"
            "Return a JSON array where each item has:\n"
            "- id\n"
            "- category\n"
            "- severity (critical | high | medium | low)\n"
            "- description\n"
            "- line (if confidently known, else null)\n\n"
            f"CODE:\n{code}"
        )

        raw_response = await self._llm.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
        )

        try:
            findings: List[Dict[str, Any]] = json.loads(raw_response)
        except json.JSONDecodeError:
            await self._emit_error(
                "SecurityAgent failed to parse LLM response as JSON",
                recoverable=False,
            )
            findings = []

        for finding in findings:
            finding["agent_id"] = self.agent_id
            finding["agent_type"] = self.agent_type

            await self._emit_finding(finding)

            if shared_context:
                shared_context.add_finding(finding)

        await self._emit_agent_completed(
            summary=f"Found {len(findings)} security issue(s)"
        )

        return {
            "findings": findings,
        }
