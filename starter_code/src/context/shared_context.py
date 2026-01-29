"""
SharedContext - thread-safe shared state for multi-agent analysis.

Stage 2B:
- Store findings from all agents
- Store agent-specific results
- Provide safe read/write access
"""

from typing import Any, Dict, List
from threading import Lock


class SharedContext:
    """
    Thread-safe shared context for agents and coordinator.

    This object is passed around but never replaced.
    """

    def __init__(self, code: str):
        self.code: str = code
        self.metadata: Dict[str, Any] = {}
        self.findings: List[Dict[str, Any]] = []
        self.agent_results: Dict[str, Any] = {}

        self._lock = Lock()

    # ------------------------------------------------------------------
    # Findings
    # ------------------------------------------------------------------

    def add_finding(self, finding: Dict[str, Any]) -> None:
        """Add a finding in a thread-safe manner."""
        with self._lock:
            self.findings.append(finding)

    def get_all_findings(self) -> List[Dict[str, Any]]:
        """Return a copy of all findings."""
        with self._lock:
            return list(self.findings)

    def get_findings_by_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get findings emitted by a specific agent."""
        with self._lock:
            return [
                f for f in self.findings
                if f.get("agent_id") == agent_id
            ]

    # ------------------------------------------------------------------
    # Agent results
    # ------------------------------------------------------------------

    def set_agent_result(self, agent_id: str, result: Any) -> None:
        """Store the final result from an agent."""
        with self._lock:
            self.agent_results[agent_id] = result

    def get_agent_result(self, agent_id: str) -> Any:
        """Retrieve stored agent result."""
        with self._lock:
            return self.agent_results.get(agent_id)

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def set_metadata(self, key: str, value: Any) -> None:
        """Store arbitrary metadata."""
        with self._lock:
            self.metadata[key] = value

    def get_metadata(self, key: str) -> Any:
        """Retrieve metadata value."""
        with self._lock:
            return self.metadata.get(key)
