"""
Conservation law verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .state import GlobalState


@dataclass
class Violation:
    """Represents a conservation violation."""

    turn: int
    violation_type: str
    expected: Any
    actual: Any
    message: str


class ConservationVerifier:
    """Verify conservation laws hold across states."""

    def __init__(self) -> None:
        self.baseline: Optional[Dict[str, int]] = None

    def set_baseline(self, state: GlobalState) -> None:
        """Set initial state as baseline for conservation."""
        self.baseline = state.calculate_totals()

    def verify(self, state: GlobalState) -> List[Violation]:
        """Check if conservation laws hold for a given state."""
        if not self.baseline:
            raise ValueError("Baseline not set")

        violations: List[Violation] = []
        current_totals = state.calculate_totals()

        # Check each known resource type
        for resource, expected_amount in self.baseline.items():
            actual_amount = current_totals.get(resource, 0)
            if actual_amount != expected_amount:
                violations.append(
                    Violation(
                        turn=state.turn,
                        violation_type="conservation",
                        expected=expected_amount,
                        actual=actual_amount,
                        message=f"{resource}: expected {expected_amount}, got {actual_amount}",
                    )
                )

        # Check for new resource types appearing
        for resource in current_totals:
            if resource not in self.baseline:
                violations.append(
                    Violation(
                        turn=state.turn,
                        violation_type="new_resource",
                        expected=None,
                        actual=current_totals[resource],
                        message=f"New resource type appeared: {resource}",
                    )
                )

        return violations

