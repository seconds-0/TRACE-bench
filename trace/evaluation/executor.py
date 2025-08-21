"""
Execute benchmark evaluations (final-state and per-turn modes).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..core.state import GlobalState
from ..core.verifier import ConservationVerifier, Violation
from ..generation.scenario import Scenario
from ..generation.prompt_builder import PromptBuilder


@dataclass
class EvaluationResult:
    scenario_seed: int
    model_name: str
    mode: str  # 'final' or 'per_turn'
    conservation_held: bool
    state_correct: bool
    conservation_accuracy: float
    state_accuracy: float
    conservation_accuracy_per_turn: Optional[List[float]] = None
    entity_accuracy_per_turn: Optional[List[float]] = None
    violations: List[Violation] = field(default_factory=list)
    raw_response: str = ""
    parsed_state: Optional[Dict] = None
    ground_truth: Optional[Dict] = None


class Evaluator:
    def __init__(self, model_interface, *, cache_enabled: bool = False, cache_dir: Optional[str] = None):
        self.model = model_interface
        self.cache_enabled = cache_enabled
        self.cache_dir = cache_dir

    def _cache_key(self, prompt: str) -> str:
        import hashlib, os
        h = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        model = getattr(self.model, "name", "unknown").replace("/", "_")
        sub = os.path.join(self.cache_dir or ".trace_cache", model)
        os.makedirs(sub, exist_ok=True)
        return os.path.join(sub, f"{h}.json")

    def _cached_generate(self, prompt: str) -> str:
        import os, tempfile
        if not self.cache_enabled:
            return self.model.generate(prompt)
        path = self._cache_key(prompt)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        resp = self.model.generate(prompt)
        tmp = f"{path}.tmp.{os.getpid()}"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(resp)
        os.replace(tmp, path)
        return resp

    def _parse_final_state(self, response: str) -> GlobalState:
        obj = json.loads(response)
        if not isinstance(obj, dict) or "entities" not in obj or "totals" not in obj:
            raise ValueError("Invalid final-state JSON")
        state = GlobalState()
        for name, res in obj["entities"].items():
            tokens = res.get("tokens")
            if not isinstance(tokens, int):
                raise ValueError("Missing tokens int")
            state.add_entity(name.lower(), {"tokens": tokens})
        return state

    def _parse_per_turn(self, response: str) -> List[GlobalState]:
        obj = json.loads(response)
        turns = obj.get("turns") if isinstance(obj, dict) else None
        if not isinstance(turns, list) or not turns:
            raise ValueError("Invalid per-turn JSON; 'turns' must be non-empty list")
        states: List[GlobalState] = []
        for t in turns:
            entities = t.get("entities") if isinstance(t, dict) else None
            totals = t.get("totals") if isinstance(t, dict) else None
            if not isinstance(entities, dict) or not isinstance(totals, dict):
                raise ValueError("Invalid per-turn entry: missing entities/totals")
            st = GlobalState()
            for name, res in entities.items():
                tokens = res.get("tokens") if isinstance(res, dict) else None
                if not isinstance(tokens, int):
                    raise ValueError("Per-turn entry missing tokens int")
                st.add_entity(name.lower(), {"tokens": tokens})
            states.append(st)
        return states

    def evaluate(self, scenario: Scenario, mode: str = "final") -> EvaluationResult:
        pb = PromptBuilder(scenario)
        if mode == "per_turn":
            prompt = pb.build_per_turn_prompt()
            response = self._cached_generate(prompt)
            model_states = self._parse_per_turn(response)
            gt_states = scenario.get_ground_truth()[1:]  # after each turn (expected count)
            verifier = ConservationVerifier()
            verifier.set_baseline(scenario.initial_state)

            # Per-turn metrics
            cons: List[float] = []
            ent: List[float] = []
            violations: List[Violation] = []

            # Handle turn-count mismatch (pad with zeros, ignore extras)
            expected = len(gt_states)
            actual = len(model_states)
            if actual != expected:
                violations.append(
                    Violation(
                        turn=expected,
                        violation_type="turn_count_mismatch",
                        expected=expected,
                        actual=actual,
                        message=f"Expected {expected} turns, got {actual}",
                    )
                )

            # Evaluate up to expected turns; missing turns score as 0
            for i in range(expected):
                if i >= actual:
                    cons.append(0.0)
                    ent.append(0.0)
                    continue
                ms = model_states[i]
                gt = gt_states[i]
                vios = verifier.verify(ms)
                correct_entities = sum(
                    1
                    for name, e in gt.entities.items()
                    if ms.get_entity(name) and ms.get_entity(name).resources == e.resources
                )
                cons.append(1.0 if len(vios) == 0 else 0.0)
                ent.append(correct_entities / max(1, len(gt.entities)))

            # Final-state booleans use last turn
            final_correct = (len(cons) > 0 and ent[-1] == 1.0 and cons[-1] == 1.0 and len(violations) == 0)
            return EvaluationResult(
                scenario_seed=scenario.seed,
                model_name=getattr(self.model, "name", "unknown"),
                mode="per_turn",
                conservation_held=(len(cons) > 0 and cons[-1] == 1.0 and len(violations) == 0),
                state_correct=final_correct,
                conservation_accuracy=sum(cons) / len(cons),
                state_accuracy=sum(ent) / len(ent),
                conservation_accuracy_per_turn=cons,
                entity_accuracy_per_turn=ent,
                violations=violations,
                raw_response=response,
                parsed_state={"turns": [self._state_to_dict(s) for s in model_states]},
                ground_truth={"turns": [self._state_to_dict(s) for s in gt_states]},
            )

        # Final mode
        prompt = pb.build_final_state_prompt()
        response = self._cached_generate(prompt)
        model_state = self._parse_final_state(response)
        gt_state = scenario.get_ground_truth()[-1]
        verifier = ConservationVerifier()
        verifier.set_baseline(scenario.initial_state)
        violations = verifier.verify(model_state)

        correct_entities = sum(
            1
            for name, e in gt_state.entities.items()
            if model_state.get_entity(name)
            and model_state.get_entity(name).resources == e.resources
        )
        ent_acc = correct_entities / max(1, len(gt_state.entities))
        return EvaluationResult(
            scenario_seed=scenario.seed,
            model_name=getattr(self.model, "name", "unknown"),
            mode="final",
            conservation_held=len(violations) == 0,
            state_correct=ent_acc == 1.0 and len(violations) == 0,
            conservation_accuracy=1.0 if len(violations) == 0 else 0.0,
            state_accuracy=ent_acc,
            violations=violations,
            raw_response=response,
            parsed_state=self._state_to_dict(model_state),
            ground_truth=self._state_to_dict(gt_state),
        )

    def _state_to_dict(self, state: GlobalState) -> Dict:
        return {name: e.resources for name, e in state.entities.items()}
