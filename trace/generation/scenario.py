"""
Procedural scenario generation (deterministic, sequential application).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List

from ..core.actions import Action, TransferAction
from ..core.state import GlobalState


@dataclass
class Scenario:
    """Complete test scenario description."""

    initial_state: GlobalState
    actions: List[Action]
    total_resources: Dict[str, int]
    seed: int

    def get_ground_truth(self) -> List[GlobalState]:
        """Calculate ground truth for all states (sequentially)."""
        states = [self.initial_state]
        current_state = self.initial_state
        for action in self.actions:
            current_state = action.apply(current_state)
            states.append(current_state)
        return states


class ScenarioGenerator:
    """Generate scenarios deterministically from a seed."""

    def __init__(self, seed: int | None = None) -> None:
        self.seed = seed if seed is not None else random.randint(0, 1_000_000)
        self.rng = random.Random(self.seed)

    def generate_simple(
        self,
        num_entities: int = 3,
        num_tokens: int = 10,
        num_actions: int = 5,
    ) -> Scenario:
        """Generate a simple transfer-only scenario.

        - Randomly distribute tokens across entities (sum == num_tokens).
        - Sequentially sample transfers, capping per-action transfer at 3 tokens.
        """

        # Create initial state
        state = GlobalState()
        entity_names = [f"entity_{i}" for i in range(num_entities)]

        # Distribute tokens randomly but ensure sum equals num_tokens
        remaining = num_tokens
        for i, name in enumerate(entity_names):
            if i == len(entity_names) - 1:
                tokens = remaining
            else:
                tokens = self.rng.randint(0, remaining)
                remaining -= tokens
            state.add_entity(name, {"tokens": tokens})

        # Generate transfers based on live state
        actions: List[Action] = []
        live_state = state
        for turn in range(1, num_actions + 1):
            from_entity = self.rng.choice(entity_names)
            to_entity_candidates = [e for e in entity_names if e != from_entity]
            if not to_entity_candidates:
                continue
            to_entity = self.rng.choice(to_entity_candidates)

            max_amount = live_state.get_entity(from_entity).get_resource("tokens")
            if max_amount <= 0:
                continue

            amount = self.rng.randint(1, min(max_amount, 3))
            action = TransferAction(
                turn=turn,
                description=f"{from_entity} gives {to_entity} {amount} tokens",
                from_entity=from_entity,
                to_entity=to_entity,
                resource_type="tokens",
                amount=amount,
            )
            actions.append(action)
            live_state = action.apply(live_state)

        return Scenario(
            initial_state=state,
            actions=actions,
            total_resources={"tokens": num_tokens},
            seed=self.seed,
        )

