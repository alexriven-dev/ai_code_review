"""
BugAgent - analyzes code for logic, runtime, and correctness issues.

Stage 4 compatible:
- Uses OpenAI via LLM adapter
- Enforces structured JSON output
- Safely extracts JSON
- Emits lifecycle + finding events
- Integrates with SharedContext
"""

from typing import Any, Dict, List, Optional
import json
import re

from .base_agent import BaseAgent
from ..llm.openai_client import OpenAIClient
from ..context.shared_context import SharedContext


class BugAgent(BaseAgent):
    """Agent responsible for detecting bugs and logic errors."""

    def __init__(self, event_bus):
        super().__init__(
            agent_id="bug_agent",
            agent_type="bug",
            agent_config={},
            event_bus=event_bus,
        )

        self._llm = OpenAIClient()

    # ------------------------------------------------------------------
    # System Prompt
    # ------------------------------------------------------------------

    @property
    def system_prompt(self) -> str:
        return (
            "You are a software bug detection agent.\n"
            "Your task is to identify real, high-confidence bugs,\n"
            "logic errors, and runtime issues in Python code.\n\n"
            "Focus on:\n"
            "- Null/None errors\n"
            "- Off-by-one mistakes\n"
            "- Unhandled exceptions\n"
            "- Resource leaks\n"
            "- Type errors\n"
            "- Logic flaws\n"
            "- Index errors\n"
            "- Infinite loops\n\n"
            "Output Rules:\n"
            "- Return ONLY valid JSON\n"
            "- No explanations\n"
            "- No markdown\n"
            "- Output must start with [ and end with ]\n\n"
            "If no issues exist, return: []"
        )

    # ------------------------------------------------------------------
    # Prompt Builder
    # ------------------------------------------------------------------

    def _build_user_prompt(self, code: str) -> str:
        return f"""
Analyze the following Python code for bugs and logic errors.

Return a JSON array. Each item must have exactly this format:

{{
  "id": "string",
  "category": "logic|runtime|performance|type|resource",
  "severity": "critical|high|medium|low",
  "description": "string",
  "line": number | null
}}

Rules:
- Do not add explanations
- Do not add comments
- Do not wrap in markdown
- Do not output anything except JSON

If there are no issues, return [].

CODE:
{code}
"""

    # ------------------------------------------------------------------
    # JSON Extraction
    # ------------------------------------------------------------------

    def _extract_json_array(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract first JSON array from LLM output.
        """

        # Fast path
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

        # Fallback
        match = re.search(r"\[.*\]", text, re.DOTALL)

        if not match:
            raise ValueError("No JSON array found in response")

        return json.loads(match.group())

    # ------------------------------------------------------------------
    # Main Analysis
    # ------------------------------------------------------------------

    async def analyze(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze code for bugs and logic errors.
        """

        await self._emit_agent_started("Starting bug analysis")

        shared_context: Optional[SharedContext] = None
        if context and "shared_context" in context:
            shared_context = context["shared_context"]

        await self._emit_thinking("Analyzing code for bugs and logic flaws")

        user_prompt = self._build_user_prompt(code)

        raw_response = await self._llm.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
        )

        # --------------------------------------------------------------
        # Parse response safely
        # --------------------------------------------------------------

        try:
            findings: List[Dict[str, Any]] = self._extract_json_array(
                raw_response
            )

        except Exception as e:
            await self._emit_error(
                f"BugAgent failed to parse LLM JSON: {e}. "
                f"Raw response: {raw_response[:300]}",
                recoverable=False,
            )
            findings = []

        # --------------------------------------------------------------
        # Post-process findings
        # --------------------------------------------------------------

        for finding in findings:

            finding["agent_id"] = self.agent_id
            finding["agent_type"] = self.agent_type

            await self._emit_finding(finding)

            if shared_context:
                shared_context.add_finding(finding)

        await self._emit_agent_completed(
            summary=f"Found {len(findings)} bug(s)"
        )

        return {
            "findings": findings,
        }
