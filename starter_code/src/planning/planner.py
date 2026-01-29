"""
Planner responsible for building execution plans.

Stage 1 behavior:
- Deterministic
- Always includes security + bug agents
- Agents run in parallel
"""

from typing import Any, Dict, List
from uuid import uuid4

from .plan import create_plan


class PlanBuilder:
    """Builds an execution plan for a code review run."""

    def build(self, code: str) -> Dict[str, Any]:
        """
        Build the execution plan for the given code.

        Stage 1 rules:
        - Always include security and bug analysis
        - Both can run in parallel
        - No dependency ordering yet

        Args:
            code: The code to analyze (currently unused, reserved for future heuristics)

        Returns:
            Execution plan dictionary
        """
        plan_id = str(uuid4())

        steps: List[Dict[str, Any]] = [
            {
                "step_id": "security_analysis",
                "agent_type": "security",
                "description": "Analyze code for security vulnerabilities",
                "depends_on": [],
                "can_run_parallel": True,
                "timeout_seconds": 60,
            },
            {
                "step_id": "bug_analysis",
                "agent_type": "bug",
                "description": "Analyze code for bugs and logic errors",
                "depends_on": [],
                "can_run_parallel": True,
                "timeout_seconds": 60,
            },
        ]

        return create_plan(plan_id=plan_id, steps=steps)
