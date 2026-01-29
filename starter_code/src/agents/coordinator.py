"""
Coordinator Agent - Orchestrates the multi-agent code review.

Stage 1 implemented:
- Create analysis plan
- Emit plan_created
- Emit agent_delegated

Later stages (delegation execution, consolidation, fix verification)
are intentionally left unimplemented.
"""

from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent
from ..config import config
from ..events import EventBus, EventType, Event


class CoordinatorAgent(BaseAgent):
    """
    Coordinator agent that orchestrates the code review process.

    Responsibilities:
    - Create analysis plan
    - Delegate to specialist agents
    - Consolidate findings
    - Manage fix verification workflow
    - Generate final report
    """

    def __init__(self, event_bus: EventBus):
        super().__init__(
            agent_id="coordinator",
            agent_type="coordinator",
            agent_config=config.coordinator_config,
            event_bus=event_bus,
        )

        # Registered specialist agents (security, bug, etc.)
        self._specialists: Dict[str, BaseAgent] = {}

        # Current analysis state
        self._current_plan: Optional[Dict[str, Any]] = None
        self._all_findings: List[Dict[str, Any]] = []

    @property
    def system_prompt(self) -> str:
        """System prompt for the coordinator."""
        return """You are a Coordinator Agent responsible for orchestrating a multi-agent code review system."""

    def get_tools(self) -> List[Dict[str, Any]]:
        """Tools available to the coordinator (used in later stages)."""
        return []

    def register_specialist(self, agent_type: str, agent: BaseAgent) -> None:
        """
        Register a specialist agent.

        Args:
            agent_type: Type of specialist (e.g. 'security', 'bug')
            agent: The agent instance
        """
        self._specialists[agent_type] = agent

    async def analyze(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Stage 1: Orchestrate planning for the code analysis.

        Current implementation:
        1. Emit agent_started
        2. Create analysis plan
        3. Emit plan_created
        4. Emit agent_delegated for each specialist
        5. STOP (no execution yet)

        Args:
            code: The code to analyze
            context: Optional additional context

        Returns:
            The generated analysis plan
        """
        self._emit_agent_started("Creating analysis plan")

        if not code or not code.strip():
            raise ValueError("Coordinator received empty code input.")

        # Stage 1: Create plan
        plan = await self._create_plan(code)
        self._current_plan = plan

        # Emit delegation events for each planned step
        for step in plan["steps"]:
            event = Event(
                event_type=EventType.AGENT_DELEGATED,
                agent_id=self.agent_id,
                data={
                    "plan_id": plan["plan_id"],
                    "step_id": step["step_id"],
                    "agent_type": step["agent_type"],
                    "description": step["description"],
                },
            )
            await self.event_bus.publish(event)

        # Stage 1 ends here intentionally
        return plan

    async def _create_plan(self, code: str) -> Dict[str, Any]:
        """
        Create an analysis plan for the code.

        Stage 1 behavior:
        - Deterministic plan
        - Always include security and bug agents
        - Run in parallel

        Args:
            code: The code to analyze

        Returns:
            Plan dictionary
        """
        plan: Dict[str, Any] = {
            "plan_id": self._generate_plan_id(),
            "steps": [
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
            ],
        }

        # Emit plan_created event
        event = Event(
            event_type=EventType.PLAN_CREATED,
            agent_id=self.agent_id,
            data=plan,
        )
        await self.event_bus.publish(event)

        return plan

    async def _consolidate_findings(
        self,
        findings: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Consolidate findings from all agents.

        Implemented in later stages.
        """
        raise NotImplementedError("Finding consolidation not implemented yet.")

    async def _verify_fix(
        self,
        original_code: str,
        fixed_code: str,
        finding: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Verify a proposed fix.

        Implemented in later stages.
        """
        raise NotImplementedError("Fix verification not implemented yet.")

    @staticmethod
    def _generate_plan_id() -> str:
        """Generate a simple unique plan identifier."""
        from uuid import uuid4

        return str(uuid4())
