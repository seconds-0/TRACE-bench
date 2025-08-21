"""
Run complete evaluation suites.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Dict, List, Optional

from ..generation.scenario import ScenarioGenerator
from .executor import Evaluator, EvaluationResult


class BenchmarkSuite:
    DIFFICULTY_CONFIGS = {
        "trivial": {"num_entities": 2, "num_tokens": 5, "num_actions": 2},
        "easy": {"num_entities": 3, "num_tokens": 10, "num_actions": 5},
        "medium": {"num_entities": 5, "num_tokens": 20, "num_actions": 10},
    }

    def __init__(self, model_interface):
        self.evaluator = Evaluator(model_interface)

    def run_suite(
        self,
        difficulty: str = "easy",
        num_scenarios: int = 5,
        mode: str = "final",
        seeds: Optional[List[int]] = None,
    ) -> Dict:
        config = self.DIFFICULTY_CONFIGS[difficulty]
        if seeds is None:
            seeds = list(range(num_scenarios))
        results: List[EvaluationResult] = []

        for i, seed in enumerate(seeds):
            print(f"Running scenario {i+1}/{len(seeds)} (seed={seed})")
            gen = ScenarioGenerator(seed)
            scenario = gen.generate_simple(**config)
            res = self.evaluator.evaluate(scenario, mode=mode)
            results.append(res)
            print(f"  Conservation: {'✓' if res.conservation_held else '✗'}  State: {'✓' if res.state_correct else '✗'}")

        return self._aggregate(results, difficulty, mode)

    def _aggregate(self, results: List[EvaluationResult], difficulty: str, mode: str) -> Dict:
        total = len(results)
        cons = sum(1 for r in results if r.conservation_held) / max(1, total)
        state = sum(1 for r in results if r.state_correct) / max(1, total)
        mean_entity_acc = sum(r.state_accuracy for r in results) / max(1, total)
        return {
            "difficulty": difficulty,
            "mode": mode,
            "total_scenarios": total,
            "aggregate_scores": {
                "conservation_accuracy": cons,
                "state_accuracy": state,
                "mean_entity_accuracy": mean_entity_acc,
            },
            "individual_results": [asdict(r) for r in results],
        }

    def save_results(self, results: Dict, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

