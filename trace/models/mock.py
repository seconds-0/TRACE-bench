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
                # Three turns, entity_0: 5->4->4; etc. Keep totals at 10
                turns = [
                    {"entities": {"entity_0": {"tokens": 4}, "entity_1": {"tokens": 4}, "entity_2": {"tokens": 2}}, "totals": {"tokens": 10}},
                    {"entities": {"entity_0": {"tokens": 4}, "entity_1": {"tokens": 3}, "entity_2": {"tokens": 3}}, "totals": {"tokens": 10}},
                    {"entities": {"entity_0": {"tokens": 3}, "entity_1": {"tokens": 3}, "entity_2": {"tokens": 4}}, "totals": {"tokens": 10}},
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
            return json.dumps(
                {
                    "entities": {
                        "entity_0": {"tokens": 3},
                        "entity_1": {"tokens": 3},
                        "entity_2": {"tokens": 4},
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

