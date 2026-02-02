"""
SharedContext - Global working memory for agents.
Includes result consolidation and severity ranking.
"""

from typing import Dict, Any, List
from collections import defaultdict


class SharedContext:
    """
    Central blackboard for cross-agent collaboration.
    """

    # Severity weights (for scoring)
    SEVERITY_WEIGHTS = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1,
    }

    def __init__(self, code: str):
        self.code = code

        # All raw findings
        self._findings: List[Dict[str, Any]] = []

        # Consolidated report
        self._report: Dict[str, Any] = {}

    # ---------------------------------------------------------
    # Storage
    # ---------------------------------------------------------

    def add_finding(self, finding: Dict[str, Any]) -> None:
        """
        Store agent finding.
        """
        self._findings.append(finding)

    def get_all_findings(self) -> List[Dict[str, Any]]:
        """
        Return all raw findings.
        """
        return list(self._findings)

    # ---------------------------------------------------------
    # Consolidation
    # ---------------------------------------------------------

    def consolidate(self) -> Dict[str, Any]:
        """
        Merge, rank, and summarize all findings.
        """

        if not self._findings:
            self._report = self._empty_report()
            return self._report

        merged = self._deduplicate(self._findings)
        ranked = self._rank_severity(merged)
        summary = self._build_summary(ranked)

        self._report = {
            "total_findings": len(ranked),
            "risk_score": summary["risk_score"],
            "severity_breakdown": summary["severity_breakdown"],
            "agent_breakdown": summary["agent_breakdown"],
            "findings": ranked,
        }

        return self._report

    # ---------------------------------------------------------
    # Deduplication
    # ---------------------------------------------------------

    def _deduplicate(
        self,
        findings: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate findings.
        """

        seen = set()
        unique = []

        for f in findings:

            # Dedup key
            key = (
                f.get("category"),
                f.get("line"),
                f.get("description"),
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(f)

        return unique

    # ---------------------------------------------------------
    # Severity Ranking
    # ---------------------------------------------------------

    def _rank_severity(
        self,
        findings: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Sort findings by severity.
        """

        def score(f):
            return self.SEVERITY_WEIGHTS.get(
                f.get("severity", "low"),
                1,
            )

        return sorted(
            findings,
            key=score,
            reverse=True,
        )

    # ---------------------------------------------------------
    # Summary Builder
    # ---------------------------------------------------------

    def _build_summary(
        self,
        findings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build global statistics.
        """

        severity_count = defaultdict(int)
        agent_count = defaultdict(int)

        risk_score = 0

        for f in findings:

            sev = f.get("severity", "low")
            agent = f.get("agent_type", "unknown")

            severity_count[sev] += 1
            agent_count[agent] += 1

            risk_score += self.SEVERITY_WEIGHTS.get(sev, 1)

        return {
            "risk_score": risk_score,
            "severity_breakdown": dict(severity_count),
            "agent_breakdown": dict(agent_count),
        }

    # ---------------------------------------------------------
    # Empty Report
    # ---------------------------------------------------------

    def _empty_report(self) -> Dict[str, Any]:
        """
        Return empty report.
        """

        return {
            "total_findings": 0,
            "risk_score": 0,
            "severity_breakdown": {},
            "agent_breakdown": {},
            "findings": [],
        }

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def get_report(self) -> Dict[str, Any]:
        """
        Get consolidated report.
        """

        if not self._report:
            return self.consolidate()

        return self._report
