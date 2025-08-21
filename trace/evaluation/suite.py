"""
Run complete evaluation suites.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
import uuid
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
        jsonl_path: Optional[str] = None,
    ) -> Dict:
        config = self.DIFFICULTY_CONFIGS[difficulty]
        if seeds is None:
            seeds = list(range(num_scenarios))
        results: List[EvaluationResult] = []
        jsonl_file = None
        if jsonl_path:
            jsonl_file = open(jsonl_path, "w", encoding="utf-8")
        run_started = datetime.now(timezone.utc).isoformat()

        for i, seed in enumerate(seeds):
            print(f"Running scenario {i+1}/{len(seeds)} (seed={seed})")
            try:
                gen = ScenarioGenerator(seed)
                scenario = gen.generate_simple(**config)
                res = self.evaluator.evaluate(scenario, mode=mode)
            except Exception as e:  # noqa: BLE001
                res = EvaluationResult(
                    scenario_seed=seed,
                    model_name=getattr(self.evaluator.model, "name", "unknown"),
                    mode=mode,
                    conservation_held=False,
                    state_correct=False,
                    conservation_accuracy=0.0,
                    state_accuracy=0.0,
                    raw_response="",
                    parsed_state={},
                    ground_truth={},
                    error=str(e),
                )
            results.append(res)
            if jsonl_file:
                jsonl_file.write(json.dumps(asdict(res)) + "\n")
            print(f"  Conservation: {'✓' if res.conservation_held else '✗'}  State: {'✓' if res.state_correct else '✗'}")

        if jsonl_file:
            jsonl_file.close()

        run_ended = datetime.now(timezone.utc).isoformat()
        return self._aggregate(results, difficulty, mode, config, seeds, jsonl_path, run_started, run_ended)

    def _aggregate(self, results: List[EvaluationResult], difficulty: str, mode: str, config: Dict[str, int], seeds: List[int], jsonl_path: Optional[str], started_at: str, ended_at: str) -> Dict:
        total = len(results)
        cons = sum(1 for r in results if r.conservation_held) / max(1, total)
        state = sum(1 for r in results if r.state_correct) / max(1, total)
        mean_entity_acc = sum(r.state_accuracy for r in results) / max(1, total)
        return {
            "trace_schema_version": "0.1.0",
            "run_id": str(uuid.uuid4()),
            "difficulty": difficulty,
            "mode": mode,
            "scenario_config": config,
            "total_scenarios": total,
            "seeds": seeds,
            "jsonl_path": jsonl_path,
            "timestamps": {"started_at": started_at, "ended_at": ended_at},
            "model_info": {
                "name": getattr(self.evaluator.model, "name", "unknown"),
                "params": getattr(self.evaluator, "_extract_model_params", lambda: {})(),
            },
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
