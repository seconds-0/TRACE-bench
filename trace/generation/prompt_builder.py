"""
Build prompts for LLM evaluation (supports final and per-turn modes).
"""

from __future__ import annotations

from typing import List

from .scenario import Scenario


class PromptBuilder:
    """Build prompts from scenarios with strict JSON output instructions."""

    def __init__(self, scenario: Scenario):
        self.scenario = scenario

    def _system_rules(self) -> str:
        totals = ", ".join(
            f"{k}={v}" for k, v in self.scenario.total_resources.items()
        )
        return (
            "You are tracking a system with conserved resources.\n\n"
            "CRITICAL RULES:\n"
            "1. Resources cannot be created or destroyed.\n"
            f"2. Totals must remain constant: {totals}.\n"
            "3. Only transfers between entities are allowed.\n"
        )

    def _initial_state(self) -> str:
        lines: List[str] = ["Initial state:"]
        for name, entity in self.scenario.initial_state.entities.items():
            resources = ", ".join(f"{k}={v}" for k, v in entity.resources.items())
            lines.append(f"- {name}: {resources}")
        totals = self.scenario.initial_state.calculate_totals()
        lines.append(
            "\nTotal: " + ", ".join(f"{k}={v}" for k, v in totals.items())
        )
        return "\n".join(lines)

    def _actions(self) -> str:
        lines = ["Actions to apply:"]
        for a in self.scenario.actions:
            lines.append(f"Turn {a.turn}: {a.description}")
        return "\n".join(lines)

    def build_final_state_prompt(self) -> str:
        return "\n\n".join(
            [
                self._system_rules(),
                self._initial_state(),
                self._actions(),
                (
                    "\nReturn only this JSON (final state):\n"
                    "{\n  \"entities\": {\n    \"<name>\": {\"tokens\": <int>}\n  },\n  \"totals\": {\"tokens\": <int>}\n}"
                ),
            ]
        )

    def build_per_turn_prompt(self) -> str:
        return "\n\n".join(
            [
                self._system_rules(),
                self._initial_state(),
                self._actions(),
                (
                    "\nReturn only this JSON (state after each turn in order):\n"
                    "{\n  \"turns\": [\n    {\"entities\": {\"<name>\": {\"tokens\": <int>}}, \"totals\": {\"tokens\": <int>}},\n    ...\n  ]\n}"
                ),
            ]
        )

