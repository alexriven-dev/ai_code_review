"""
SecurityAgent - analyzes code for security vulnerabilities.

Stage 3B implemented:
- Uses OpenAI via LLM adapter
- Emits thinking events
- Emits finding_discovered events
- Stores findings in SharedContext
- Enforces structured JSON output
- Safely extracts JSON from LLM responses
"""

from typing import Any, Dict, List, Optional
import json
import re

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

    # ------------------------------------------------------------------
    # Prompting
    # ------------------------------------------------------------------

    @property
    def system_prompt(self) -> str:
        return (
            "You are a security analysis system for Python code.\n"
            "Your task is to identify real, high-confidence security issues.\n\n"
            "Focus ONLY on:\n"
            "- SQL injection\n"
            "- Command injection\n"
            "- Hardcoded secrets\n"
            "- Unsafe deserialization\n"
            "- Authentication / authorization flaws\n\n"
            "Output Rules:\n"
            "- Return ONLY valid JSON\n"
            "- No explanations\n"
            "- No markdown\n"
            "- No extra text\n"
            "- Output must start with [ and end with ]\n\n"
            "If no issues exist, return: []"
        )

    def _build_user_prompt(self, code: str) -> str:
        """
        Build user prompt with strict schema.
        """
        return f"""
Analyze the following Python code for security vulnerabilities.

Return a JSON array. Each item must have exactly this format:

{{
  "id": "string",
  "category": "string",
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
        Extract first JSON array from LLM output and validate structure.
        """

        # Fast path: pure JSON
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return self._validate_findings(parsed)
        except Exception:
            pass

        # Non-greedy fallback
        match = re.search(r"\[[\s\S]*?\]", text)

        if not match:
            raise ValueError("No JSON array found in response")

        parsed = json.loads(match.group())

        if not isinstance(parsed, list):
            raise ValueError("Extracted JSON is not an array")

        return self._validate_findings(parsed)

    def _validate_findings(self, findings: list) -> List[Dict[str, Any]]:
        """
        Validate structure of security findings.
        """

        validated = []

        required_keys = {
            "id",
            "category",
            "severity",
            "description",
            "line",
        }

        for item in findings:
            if not isinstance(item, dict):
                continue

            missing = required_keys - item.keys()

            if missing:
                continue

            validated.append(item)

        return validated

    # ------------------------------------------------------------------
    # Main Analysis
    # ------------------------------------------------------------------

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

        user_prompt = self._build_user_prompt(code)

        raw_response = await self._llm.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
        )

        # --------------------------------------------------------------
        # Parse response safely
        # --------------------------------------------------------------

        try:
            findings: List[Dict[str, Any]] = self._extract_json_array(raw_response)

        except Exception as e:
            await self._emit_error(
                f"Failed to parse LLM JSON response: {e}. "
                f"Raw response: {raw_response[:300]}",
                recoverable=False,
            )
            findings = []

        # --------------------------------------------------------------
        # Post-process findings
        # --------------------------------------------------------------

        for finding in findings:

            # Attach agent metadata
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
