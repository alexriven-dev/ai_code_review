"""
BaseAgent - shared lifecycle, event emission, and utilities for all agents.

- Agent lifecycle events
- Thinking stream
- Tool call scaffolding
- Error handling
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio

from ..events import EventBus, EventType, Event


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.

    Responsibilities:
    - Manage agent identity & configuration
    - Emit lifecycle and observability events
    - Provide helper methods for subclasses
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        agent_config: Dict[str, Any],
        event_bus: EventBus,
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.agent_config = agent_config
        self.event_bus = event_bus

    # ---------------------------------------------------------------------
    # Abstract API
    # ---------------------------------------------------------------------

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt describing this agent's role."""
        raise NotImplementedError

    @abstractmethod
    async def analyze(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point for agent analysis.

        Args:
            code: The code to analyze
            context: Shared context from coordinator

        Returns:
            Agent-specific results
        """
        raise NotImplementedError

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Tools available to this agent (LLM tool calling).

        Default: no tools.
        """
        return []

    # ---------------------------------------------------------------------
    # Lifecycle & observability helpers
    # ---------------------------------------------------------------------

    async def _emit_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
    ) -> None:
        """Emit a structured event via the event bus."""
        event = Event(
            event_type=event_type,
            agent_id=self.agent_id,
            data=data,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
        await self.event_bus.publish(event)

    async def _emit_agent_started(self, message: str) -> None:
        """Emit agent_started event."""
        await self._emit_event(
            EventType.AGENT_STARTED,
            {
                "message": message,
                "agent_type": self.agent_type,
            },
        )

    async def _emit_agent_completed(
        self,
        summary: Optional[str] = None,
    ) -> None:
        """Emit agent_completed event."""
        payload: Dict[str, Any] = {
            "agent_type": self.agent_type,
        }
        if summary:
            payload["summary"] = summary

        await self._emit_event(EventType.AGENT_COMPLETED, payload)

    async def _emit_thinking(self, content: str) -> None:
        """
        Emit a thinking event (streamed reasoning).

        This should be called incrementally.
        """
        await self._emit_event(
            EventType.THINKING,
            {
                "content": content,
            },
        )

    async def _emit_tool_call_start(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        purpose: Optional[str] = None,
    ) -> str:
        """
        Emit tool_call_start event.

        Returns:
            tool_call_id for correlation with result
        """
        tool_call_id = f"{self.agent_id}_{tool_name}_{datetime.utcnow().timestamp()}"

        await self._emit_event(
            EventType.TOOL_CALL_START,
            {
                "tool_call_id": tool_call_id,
                "tool_name": tool_name,
                "input": input_data,
                "purpose": purpose,
            },
        )

        return tool_call_id

    async def _emit_tool_call_result(
        self,
        tool_call_id: str,
        output_data: Any,
        duration_ms: Optional[int] = None,
    ) -> None:
        """Emit tool_call_result event."""
        payload: Dict[str, Any] = {
            "tool_call_id": tool_call_id,
            "output": output_data,
        }
        if duration_ms is not None:
            payload["duration_ms"] = duration_ms

        await self._emit_event(EventType.TOOL_CALL_RESULT, payload)

    async def _emit_finding(self, finding: Dict[str, Any]) -> None:
        """Emit finding_discovered event."""
        await self._emit_event(
            EventType.FINDING_DISCOVERED,
            finding,
        )

    async def _emit_fix_proposed(self, fix: Dict[str, Any]) -> None:
        """Emit fix_proposed event."""
        await self._emit_event(
            EventType.FIX_PROPOSED,
            fix,
        )

    async def _emit_fix_verified(self, verification: Dict[str, Any]) -> None:
        """Emit fix_verified event."""
        await self._emit_event(
            EventType.FIX_VERIFIED,
            verification,
        )

    async def _emit_error(
        self,
        error_message: str,
        recoverable: bool = True,
        will_retry: bool = False,
    ) -> None:
        """Emit agent_error event."""
        await self._emit_event(
            EventType.AGENT_ERROR,
            {
                "message": error_message,
                "recoverable": recoverable,
                "will_retry": will_retry,
            },
        )
