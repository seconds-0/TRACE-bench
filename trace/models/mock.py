from __future__ import annotations

import json

from .base import ModelInterface


class MockModel(ModelInterface):
    def __init__(self, mode: str = "final", perfect: bool = True):
        self._mode = mode
        self._perfect = perfect

    @property
    def name(self) -> str:
        return f"mock-{self._mode}-{'perfect' if self._perfect else 'failing'}"

    def generate(self, prompt: str, **kwargs) -> str:
        # Very naive mock that returns correct shapes for tests
        if self._mode == "per_turn":
            if self._perfect:
                # Ground truth for test scenario: initial(5,3,2) -> actions: 0->1(1), 2->1(1), 1->2(1)
                # Turn 1: entity_0=4, entity_1=4, entity_2=2
                # Turn 2: entity_0=4, entity_1=5, entity_2=1  
                # Turn 3: entity_0=4, entity_1=4, entity_2=2
                turns = [
                    {"entities": {"entity_0": {"tokens": 4}, "entity_1": {"tokens": 4}, "entity_2": {"tokens": 2}}, "totals": {"tokens": 10}},
                    {"entities": {"entity_0": {"tokens": 4}, "entity_1": {"tokens": 5}, "entity_2": {"tokens": 1}}, "totals": {"tokens": 10}},
                    {"entities": {"entity_0": {"tokens": 4}, "entity_1": {"tokens": 4}, "entity_2": {"tokens": 2}}, "totals": {"tokens": 10}},
                ]
            else:
                # Final turn off by one and break conservation
                turns = [
                    {"entities": {"entity_0": {"tokens": 4}, "entity_1": {"tokens": 4}, "entity_2": {"tokens": 2}}, "totals": {"tokens": 10}},
                    {"entities": {"entity_0": {"tokens": 4}, "entity_1": {"tokens": 3}, "entity_2": {"tokens": 3}}, "totals": {"tokens": 10}},
                    {"entities": {"entity_0": {"tokens": 5}, "entity_1": {"tokens": 3}, "entity_2": {"tokens": 4}}, "totals": {"tokens": 12}},
                ]
            return json.dumps({"turns": turns})

        # final
        if self._perfect:
            # Final state after all actions: entity_0=4, entity_1=4, entity_2=2
            return json.dumps(
                {
                    "entities": {
                        "entity_0": {"tokens": 4},
                        "entity_1": {"tokens": 4},
                        "entity_2": {"tokens": 2},
                    },
                    "totals": {"tokens": 10},
                }
            )
        return json.dumps(
            {
                "entities": {
                    "entity_0": {"tokens": 99},
                    "entity_1": {"tokens": 99},
                    "entity_2": {"tokens": 99},
                },
                "totals": {"tokens": 1000},
            }
        )

