"""
Plan data structures for the coordinator.

This module defines the canonical structure of an analysis plan.
The plan is intentionally represented as plain dictionaries to ensure:
- JSON serializability
- Easy event emission
- Compatibility with UI and test harness
"""

from typing import Any, Dict, List


def create_plan(
    plan_id: str,
    steps: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Create a standardized execution plan dictionary.

    Args:
        plan_id: Unique identifier for the plan
        steps: Ordered list of plan steps

    Returns:
        A plan dictionary
    """
    return {
        "plan_id": plan_id,
        "steps": steps,
    }
