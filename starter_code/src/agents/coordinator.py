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


import asyncio
import json
from typing import Dict, Any, List, Set

from .base_agent import BaseAgent
from ..events import EventType
from ..llm.openai_client import OpenAIClient



class CoordinatorAgent(BaseAgent):
    """
    Coordinator agent responsible for:
    - Planning
    - Scheduling
    - Executing workflow steps
    """

    def __init__(self, event_bus):
        super().__init__(
            agent_id="coordinator",
            agent_type="coordinator",
            agent_config={},
            event_bus=event_bus,
        )

        # LLM client for planning
        self._llm = OpenAIClient()

        # Maps agent_type -> agent instance
        self._specialists: Dict[str, BaseAgent] = {}



        # ---------------------------------------------------------
        # System Prompt (Required by BaseAgent)
        # ---------------------------------------------------------

    @property
    def system_prompt(self) -> str:
        return (
            "You are a coordination and planning agent.\n"
            "Your task is to analyze code review requests and\n"
            "break them into structured analysis steps.\n\n"
            "You create execution plans for specialist agents."
        )


        # ---------------------------------------------------------
        # LLM-Based Planner
        # ---------------------------------------------------------

    async def _plan_with_llm(
            self,
            code: str,
            context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate execution plan using LLM.
        """

        system_prompt = self.system_prompt

        user_prompt = f"""
Analyze the following code review task and create an execution plan.

Return STRICTLY valid JSON in this format:

{{
  "plan_id": "string",
  "steps": [
    {{
      "step_id": "string",
      "agent_type": "security|bug",
      "description": "string",
      "depends_on": [],
      "can_run_parallel": true,
      "timeout_seconds": 60
    }}
  ]
}}

Rules:
- Do not add explanations
- Do not add markdown
- Do not add extra text
- Output must be JSON only

CODE:
{code}
"""

        raw_response = await self._llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        # Safe parse
        try:
            plan = json.loads(raw_response)

        except Exception as e:
            raise RuntimeError(
                f"Failed to parse coordinator plan JSON: {e}. "
                f"Response: {raw_response[:300]}"
            )

        return plan


    def register_specialist(self, agent_type: str, agent: BaseAgent) -> None:
        """
        Register specialist agent.
        """
        self._specialists[agent_type] = agent

    # ---------------------------------------------------------
    # Result Consolidation
    # ---------------------------------------------------------

    def _consolidate_results(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Consolidate findings from SharedContext.
        """

        shared_context = context.get("shared_context")

        if not shared_context:
            return {}

        return shared_context.get_report()


    # ---------------------------------------------------------
    # Main Entry Point
    # ---------------------------------------------------------

    async def analyze(
        self,
        code: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Main coordinator entry.

        1. Create plan
        2. Execute plan
        3. Return results
        """

        await self._emit_agent_started("Creating analysis plan")

        # Step 1: Create plan (existing logic)
        plan = await self._create_plan(code, context)

        # Step 2: Emit plan created
        await self._emit_event(
            EventType.PLAN_CREATED,
            plan,
        )

        # Step 3: Execute plan automatically
        await self._execute_plan(plan, code, context)

        # Consolidate results
        report = self._consolidate_results(context)

        await self._emit_agent_completed(
            summary=f"Analysis complete. Risk score: {report['risk_score']}"
        )

        return report

        return plan

    # ---------------------------------------------------------
    # Planning (Existing Logic Wrapper)
    # ---------------------------------------------------------

    async def _create_plan(
        self,
        code: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Wrapper around existing planning logic.
        """

        # Call your existing LLM-based planner
        return await self._plan_with_llm(code, context)

    # ---------------------------------------------------------
    # Scheduler / Executor
    # ---------------------------------------------------------

    async def _execute_plan(
        self,
        plan: Dict[str, Any],
        code: str,
        context: Dict[str, Any],
    ) -> None:
        """
        Execute plan with dependency-aware scheduling.
        """

        steps: List[Dict[str, Any]] = plan.get("steps", [])

        # Track completed steps
        completed: Set[str] = set()

        # Track running tasks
        running: Dict[str, asyncio.Task] = {}

        while len(completed) < len(steps):

            # Find steps ready to run
            ready_steps = self._find_ready_steps(
                steps,
                completed,
                running,
            )

            # Schedule ready steps
            for step in ready_steps:
                task = asyncio.create_task(
                    self._run_step(step, code, context)
                )

                running[step["step_id"]] = task

            if not running:
                raise RuntimeError("Deadlock detected in plan execution")

            # Wait for any step to complete
            done, _ = await asyncio.wait(
                running.values(),
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Process completed tasks
            for finished in done:

                step_id = None

                for sid, task in running.items():
                    if task == finished:
                        step_id = sid
                        break

                if step_id is None:
                    continue

                await finished  # propagate errors

                completed.add(step_id)
                del running[step_id]

    # ---------------------------------------------------------
    # Step Selection
    # ---------------------------------------------------------

    def _find_ready_steps(
        self,
        steps: List[Dict[str, Any]],
        completed: Set[str],
        running: Dict[str, asyncio.Task],
    ) -> List[Dict[str, Any]]:
        """
        Find steps whose dependencies are satisfied.
        """

        ready = []

        for step in steps:

            step_id = step["step_id"]

            # Skip finished or running
            if step_id in completed or step_id in running:
                continue

            deps = step.get("depends_on", [])

            # Check dependencies
            if all(dep in completed for dep in deps):
                ready.append(step)

        return ready

    # ---------------------------------------------------------
    # Step Runner
    # ---------------------------------------------------------

    async def _run_step(
        self,
        step: Dict[str, Any],
        code: str,
        context: Dict[str, Any],
    ) -> None:
        """
        Run a single workflow step.
        """

        step_id = step["step_id"]
        agent_type = step["agent_type"]

        # Emit step started
        await self._emit_event(
            EventType.PLAN_STEP_STARTED,
            {
                "step_id": step_id,
                "agent_type": agent_type,
            },
        )

        # Lookup agent
        agent = self._specialists.get(agent_type)

        if not agent:
            raise RuntimeError(f"No specialist for {agent_type}")

        # Run specialist
        await agent.analyze(code, context)

        # Emit step completed
        await self._emit_event(
            EventType.PLAN_STEP_COMPLETED,
            {
                "step_id": step_id,
                "agent_type": agent_type,
            },
        )

