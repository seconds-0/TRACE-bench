# TRACE Benchmark - Complete Implementation Plan

## Executive Summary

TRACE (Tracking Resource Allocation Consistency Evaluation) is a benchmark for evaluating large language models' ability to maintain consistent state across multiple entities while respecting conservation laws over extended time horizons.

**Core Concept**: We track tokens across entities, verify conservation laws are maintained, and measure how accuracy degrades over time.

---

## Phase 0: Steel Thread Implementation (Day 1)

### Objective
Build the absolute minimum viable benchmark that proves the concept works end-to-end.

### File: `steel_thread.py`

```python
"""
The complete steel thread implementation.
This file should work standalone with only 'requests' as a dependency.
Uses strict JSON I/O to avoid fragile parsing.
"""

import os
import json
import time
from typing import Dict, Tuple
import requests


class SteelThreadTRACE:
    """Minimal end-to-end implementation of TRACE benchmark"""

    def __init__(self, api_key: str = None):
        """
        Initialize with OpenRouter API key.
        Can be passed directly or set as OPENROUTER_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("Need OPENROUTER_API_KEY environment variable")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def call_model(self, prompt: str, model: str = "openai/gpt-3.5-turbo") -> str:
        """
        Call OpenRouter API with the given prompt and return text content.
        Uses low temperature and top_p=1 for determinism.
        """
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.0,
            "top_p": 1,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        backoff = 1.0
        for attempt in range(3):
            try:
                resp = requests.post(
                    self.base_url, json=payload, headers=headers, timeout=30
                )
                if resp.status_code == 429:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(backoff)
                backoff *= 2

        raise RuntimeError("Exhausted retries calling model")

    def parse_json_state(self, response: str) -> Tuple[Dict[str, int], int]:
        """
        Parse strict JSON response into state and total tokens.
        Expected schema:
          { "entities": {"alice": {"tokens": int}, ...}, "totals": {"tokens": int} }
        """
        try:
            obj = json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Response was not valid JSON: {e}")

        if not isinstance(obj, dict) or "entities" not in obj or "totals" not in obj:
            raise ValueError("Response JSON missing required keys 'entities' and 'totals'")

        entities = obj["entities"]
        totals = obj["totals"]
        if not isinstance(entities, dict) or not isinstance(totals, dict):
            raise ValueError("'entities' and 'totals' must be objects")
        if "tokens" not in totals or not isinstance(totals["tokens"], int):
            raise ValueError("'totals.tokens' must be an integer")

        state: Dict[str, int] = {}
        for name, res in entities.items():
            if not isinstance(res, dict) or "tokens" not in res or not isinstance(res["tokens"], int):
                raise ValueError(f"Entity '{name}' missing integer 'tokens'")
            state[name.lower()] = int(res["tokens"])

        return state, int(totals["tokens"])

    def verify_conservation(self, state: Dict[str, int], expected_total: int) -> bool:
        """Check if conservation law holds"""
        return sum(state.values()) == expected_total

    def run_steel_thread(self, model: str = "openai/gpt-3.5-turbo") -> Dict:
        """
        Run the minimal benchmark test (final-state only for steel thread).
        """

        # Initial setup
        initial_state = {"alice": 5, "bob": 3, "charlie": 2}
        total_tokens = sum(initial_state.values())

        # Build the prompt with strict JSON output requirement
        prompt = f"""
You are tracking a system with 3 entities and a conserved resource 'tokens'.

CRITICAL RULES:
1) Tokens cannot be created or destroyed, only transferred.
2) The total number of tokens must ALWAYS equal {total_tokens}.

Initial state:
  - Alice: tokens={initial_state['alice']}
  - Bob: tokens={initial_state['bob']}
  - Charlie: tokens={initial_state['charlie']}
  - Total: tokens={total_tokens}

Actions (apply in order):
  1. Alice gives Bob 2 tokens.
  2. Charlie gives Alice 1 token.
  3. Bob gives Charlie 3 tokens.

Respond ONLY with a single JSON object of this exact schema and nothing else:
{{
  "entities": {{
    "Alice": {{"tokens": <int>}},
    "Bob": {{"tokens": <int>}},
    "Charlie": {{"tokens": <int>}}
  }},
  "totals": {{"tokens": <int>}}
}}
""".strip()

        print(f"\n🚀 Running steel thread with {model}")
        print(f"📊 Initial total: {total_tokens} tokens")

        # Call the model
        response = self.call_model(prompt, model)
        print(f"\n📝 Model response:\n{response}\n")

        # Parse and verify
        final_state, reported_total = self.parse_json_state(response)
        print(f"📈 Parsed state: {final_state}; reported_total={reported_total}")

        # Calculate ground truth
        ground_truth = {
            "alice": 4,  # 5 - 2 + 1 = 4
            "bob": 2,    # 3 + 2 - 3 = 2
            "charlie": 4 # 2 + 3 - 1 = 4
        }

        # Check conservation
        conservation_held = self.verify_conservation(final_state, total_tokens)
        state_correct = final_state == ground_truth

        # Results
        results = {
            "model": model,
            "params": {"temperature": 0.0, "top_p": 1},
            "conservation_held": conservation_held,
            "state_correct": state_correct,
            "expected_total": total_tokens,
            "actual_total": sum(final_state.values()),
            "reported_total": reported_total,
            "expected_state": ground_truth,
            "actual_state": final_state,
            "raw_response": response
        }

        # Print summary
        print("\n" + "=" * 50)
        print("STEEL THREAD RESULTS")
        print("=" * 50)
        print(f"✓ Conservation: {'PASS ✅' if conservation_held else 'FAIL ❌'}")
        print(f"✓ State Accuracy: {'PASS ✅' if state_correct else 'FAIL ❌'}")

        return results


def main():
    """Run the steel thread test"""
    benchmark = SteelThreadTRACE()
    results = benchmark.run_steel_thread("openai/gpt-3.5-turbo")

    with open("steel_thread_results.json", "w") as f:
        json.dump(results, f, indent=2)

    if results["conservation_held"] and results["state_correct"]:
        print("\n🎉 STEEL THREAD COMPLETE - Core concept validated!")
        return 0
    else:
        print("\n⚠️  STEEL THREAD ISSUES DETECTED")
        return 1


if __name__ == "__main__":
    exit(main())
```

### Validation Criteria
- [ ] Code runs without errors
- [ ] Successfully calls OpenRouter API (with timeouts/retries)
- [ ] Parses strict JSON response correctly (schema validated)
- [ ] Detects conservation violations
- [ ] Produces JSON output file

### Expected Output
```json
{
  "model": "openai/gpt-3.5-turbo",
  "params": {"temperature": 0.0, "top_p": 1},
  "conservation_held": true,
  "state_correct": true,
  "expected_total": 10,
  "actual_total": 10,
  "reported_total": 10,
  "expected_state": {"alice": 4, "bob": 2, "charlie": 4},
  "actual_state": {"alice": 4, "bob": 2, "charlie": 4}
}
```

---

## Phase 1: Core State Engine (Days 2-3)

### Objective
Build the fundamental state tracking and verification system.

### File Structure
```
trace/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── state.py       # State representation
│   ├── actions.py     # Action definitions
│   └── verifier.py    # Conservation verification
```

### File: `trace/core/state.py`

```python
"""
State representation and manipulation.
"""

from typing import Dict, Optional
from dataclasses import dataclass, field
from copy import deepcopy


@dataclass
class EntityState:
    """State for a single entity"""
    name: str
    resources: Dict[str, int] = field(default_factory=dict)

    def get_resource(self, resource_type: str) -> int:
        """Get count of specific resource"""
        return self.resources.get(resource_type, 0)

    def set_resource(self, resource_type: str, amount: int):
        """Set resource amount"""
        if amount < 0:
            raise ValueError(f"Resource amount cannot be negative: {amount}")
        self.resources[resource_type] = amount

    def modify_resource(self, resource_type: str, delta: int):
        """Modify resource by delta amount"""
        current = self.get_resource(resource_type)
        new_amount = current + delta
        if new_amount < 0:
            raise ValueError(f"Would result in negative resources: {new_amount}")
        self.set_resource(resource_type, new_amount)


@dataclass
class GlobalState:
    """Complete system state"""
    entities: Dict[str, EntityState] = field(default_factory=dict)
    turn: int = 0

    def add_entity(self, name: str, initial_resources: Dict[str, int] = None):
        """Add new entity to system"""
        entity = EntityState(name=name)
        if initial_resources:
            entity.resources = initial_resources.copy()
        self.entities[name] = entity

    def get_entity(self, name: str) -> Optional[EntityState]:
        """Get entity by name"""
        return self.entities.get(name)

    def calculate_totals(self) -> Dict[str, int]:
        """Calculate total resources across all entities"""
        totals: Dict[str, int] = {}
        for entity in self.entities.values():
            for resource, amount in entity.resources.items():
                totals[resource] = totals.get(resource, 0) + amount
        return totals

    def clone(self) -> "GlobalState":
        """Create deep copy of state"""
        return deepcopy(self)
```

### File: `trace/core/actions.py`

```python
"""
Action definitions and application.
"""

from dataclasses import dataclass
from typing import Optional
from .state import GlobalState

@dataclass
class Action:
    """Base action class"""
    turn: int
    description: str
    
    def apply(self, state: GlobalState) -> GlobalState:
        """Apply action to state, return new state"""
        raise NotImplementedError

@dataclass
class TransferAction(Action):
    """Transfer resources between entities"""
    from_entity: str
    to_entity: str
    resource_type: str
    amount: int
    
    def apply(self, state: GlobalState) -> GlobalState:
        """Execute transfer"""
        new_state = state.clone()
        
        # Get entities
        from_e = new_state.get_entity(self.from_entity)
        to_e = new_state.get_entity(self.to_entity)
        
        if not from_e or not to_e:
            raise ValueError(f"Entity not found")
        
        # Execute transfer
        from_e.modify_resource(self.resource_type, -self.amount)
        to_e.modify_resource(self.resource_type, self.amount)
        
        new_state.turn = self.turn
        return new_state
```

### File: `trace/core/verifier.py`

```python
"""
Conservation law verification.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from .state import GlobalState

@dataclass
class Violation:
    """Represents a conservation violation"""
    turn: int
    violation_type: str
    expected: any
    actual: any
    message: str

class ConservationVerifier:
    """Verify conservation laws hold"""
    
    def __init__(self):
        self.baseline: Optional[Dict[str, int]] = None
    
    def set_baseline(self, state: GlobalState):
        """Set initial state as baseline for conservation"""
        self.baseline = state.calculate_totals()
    
    def verify(self, state: GlobalState) -> List[Violation]:
        """Check if conservation laws hold"""
        if not self.baseline:
            raise ValueError("Baseline not set")
        
        violations = []
        current_totals = state.calculate_totals()
        
        # Check each resource type
        for resource, expected_amount in self.baseline.items():
            actual_amount = current_totals.get(resource, 0)
            if actual_amount != expected_amount:
                violations.append(Violation(
                    turn=state.turn,
                    violation_type="conservation",
                    expected=expected_amount,
                    actual=actual_amount,
                    message=f"{resource}: expected {expected_amount}, got {actual_amount}"
                ))
        
        # Check for new resource types
        for resource in current_totals:
            if resource not in self.baseline:
                violations.append(Violation(
                    turn=state.turn,
                    violation_type="new_resource",
                    expected=None,
                    actual=current_totals[resource],
                    message=f"New resource type appeared: {resource}"
                ))
        
        return violations
```

### Unit Tests: `tests/test_core.py`

```python
"""
Unit tests for core functionality.
Run with: python -m pytest tests/test_core.py -v
"""

from trace.core.state import EntityState, GlobalState
from trace.core.actions import TransferAction
from trace.core.verifier import ConservationVerifier


def test_entity_state():
    """Test entity state management"""
    entity = EntityState("alice")
    entity.set_resource("tokens", 5)
    assert entity.get_resource("tokens") == 5

    entity.modify_resource("tokens", -2)
    assert entity.get_resource("tokens") == 3


def test_transfer_action():
    """Test resource transfer"""
    state = GlobalState()
    state.add_entity("alice", {"tokens": 5})
    state.add_entity("bob", {"tokens": 3})

    action = TransferAction(
        turn=1,
        description="Alice gives Bob 2 tokens",
        from_entity="alice",
        to_entity="bob",
        resource_type="tokens",
        amount=2,
    )

    new_state = action.apply(state)
    assert new_state.get_entity("alice").get_resource("tokens") == 3
    assert new_state.get_entity("bob").get_resource("tokens") == 5


def test_conservation():
    """Test conservation verification"""
    state = GlobalState()
    state.add_entity("alice", {"tokens": 5})
    state.add_entity("bob", {"tokens": 3})

    verifier = ConservationVerifier()
    verifier.set_baseline(state)

    # Valid transfer
    action = TransferAction(1, "transfer", "alice", "bob", "tokens", 2)
    new_state = action.apply(state)
    violations = verifier.verify(new_state)
    assert len(violations) == 0

    # Invalid state (tokens created)
    bad_state = new_state.clone()
    bad_state.get_entity("alice").set_resource("tokens", 10)
    violations = verifier.verify(bad_state)
    assert len(violations) == 1
    assert violations[0].violation_type == "conservation"
```

---

## Phase 2: Scenario Generation (Days 4-5)

### Objective
Build the system for generating test scenarios procedurally.

### File: `trace/generation/scenario.py`

```python
"""
Procedural scenario generation.
"""

import random
from dataclasses import dataclass
from typing import List, Dict
from ..core.state import GlobalState
from ..core.actions import Action, TransferAction


@dataclass
class Scenario:
    """Complete test scenario"""
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
    """Generate test scenarios procedurally"""

    def __init__(self, seed: int = None):
        self.seed = seed or random.randint(0, 1000000)
        self.rng = random.Random(self.seed)

    def generate_simple(
        self,
        num_entities: int = 3,
        num_tokens: int = 10,
        num_actions: int = 5,
    ) -> Scenario:
        """Generate simple transfer-only scenario (sequential, deterministic by seed)."""

        # Create initial state
        state = GlobalState()
        entity_names = [f"entity_{i}" for i in range(num_entities)]

        # Distribute tokens randomly
        remaining = num_tokens
        for i, name in enumerate(entity_names):
            if i == len(entity_names) - 1:
                tokens = remaining
            else:
                tokens = self.rng.randint(0, remaining)
                remaining -= tokens
            state.add_entity(name, {"tokens": tokens})

        # Generate random transfer actions based on the live state
        actions: List[Action] = []
        live_state = state
        for turn in range(1, num_actions + 1):
            from_entity = self.rng.choice(entity_names)
            to_entity = self.rng.choice([e for e in entity_names if e != from_entity])

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
```

### File: `trace/generation/prompt_builder.py`

```python
"""
Build prompts for LLM evaluation (strict JSON output).
"""

from ..core.state import GlobalState
from .scenario import Scenario


class PromptBuilder:
    """Build prompts from scenarios"""

    def __init__(self, scenario: Scenario):
        self.scenario = scenario

    def build_system_prompt(self) -> str:
        """Build the system/instruction prompt"""
        total_str = ", ".join([f"{k}={v}" for k, v in self.scenario.total_resources.items()])

        return (
            f"You are tracking a system with {len(self.scenario.initial_state.entities)} entities.\n\n"
            "CRITICAL RULES:\n"
            "1. Resources cannot be created or destroyed\n"
            f"2. The total amount of each resource must remain constant: {total_str}\n"
            "3. Resources can only be transferred between entities\n\n"
            "Respond ONLY with a single JSON object matching the schema specified below, and no extra text."
        )

    def build_initial_state_prompt(self) -> str:
        """Describe initial state"""
        lines = ["Initial state:"]
        for name, entity in self.scenario.initial_state.entities.items():
            resources = ", ".join([f"{k}={v}" for k, v in entity.resources.items()])
            lines.append(f"- {name}: {resources}")

        totals = self.scenario.initial_state.calculate_totals()
        lines.append(f"\nTotal: {', '.join([f'{k}={v}' for k, v in totals.items()])}")

        return "\n".join(lines)

    def build_action_sequence_prompt(self) -> str:
        """Build prompt for action sequence (final-state only)."""
        lines = ["Actions to apply:"]
        for action in self.scenario.actions:
            lines.append(f"Turn {action.turn}: {action.description}")

        lines.append(
            "\nReturn only this JSON (final state):\n"
            "{\n  \"entities\": {\n    \"<name>\": {\"tokens\": <int>}\n  },\n  \"totals\": {\"tokens\": <int>}\n}"
        )

        return "\n".join(lines)

    def build_full_prompt(self) -> str:
        """Build complete evaluation prompt"""
        return "\n\n".join(
            [
                self.build_system_prompt(),
                self.build_initial_state_prompt(),
                self.build_action_sequence_prompt(),
            ]
        )
```

---

## Phase 3: Evaluation Framework (Days 6-7)

### Objective
Build the complete evaluation pipeline.

### File: `trace/evaluation/executor.py`

```python
"""
Execute benchmark evaluations.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from ..core.state import GlobalState
from ..core.verifier import ConservationVerifier, Violation
from ..generation.scenario import Scenario
from ..generation.prompt_builder import PromptBuilder


@dataclass
class EvaluationResult:
    """Results from a single evaluation"""
    scenario_seed: int
    model_name: str
    conservation_held: bool
    state_correct: bool
    conservation_accuracy: float  # final-state conservation pass/fail for steel thread
    state_accuracy: float  # fraction of entities tracked correctly (final)
    violations: List[Violation] = field(default_factory=list)
    raw_response: str = ""
    parsed_state: Optional[Dict] = None
    ground_truth: Optional[Dict] = None


class Evaluator:
    """Execute evaluations against models"""

    def __init__(self, model_interface):
        """
        Initialize with a model interface.
        Model interface must have a generate(prompt: str) -> str method.
        """
        self.model = model_interface

    def _parse_json_response(self, response: str) -> GlobalState:
        """Parse strict JSON response into GlobalState."""
        obj = json.loads(response)
        if not isinstance(obj, dict) or "entities" not in obj or "totals" not in obj:
            raise ValueError("Response JSON missing required keys 'entities' and 'totals'")
        entities = obj["entities"]
        state = GlobalState()
        for name, res in entities.items():
            tokens = res.get("tokens") if isinstance(res, dict) else None
            if not isinstance(tokens, int):
                raise ValueError(f"Entity '{name}' missing integer 'tokens'")
            state.add_entity(name.lower(), {"tokens": tokens})
        return state

    def evaluate_scenario(self, scenario: Scenario) -> EvaluationResult:
        """Evaluate model on a single scenario"""

        # Build prompt
        prompt_builder = PromptBuilder(scenario)
        prompt = prompt_builder.build_full_prompt()

        # Get model response
        response = self.model.generate(prompt)

        # Parse response (strict JSON)
        model_state = self._parse_json_response(response)

        # Calculate ground truth
        ground_truth_states = scenario.get_ground_truth()
        final_ground_truth = ground_truth_states[-1]

        # Verify conservation
        verifier = ConservationVerifier()
        verifier.set_baseline(scenario.initial_state)
        violations = verifier.verify(model_state)

        # Check state accuracy
        state_correct = self._states_equal(model_state, final_ground_truth)

        # Calculate accuracy metrics (final only for steel thread)
        conservation_accuracy = 1.0 if len(violations) == 0 else 0.0

        correct_entities = 0
        total_entities = len(final_ground_truth.entities)
        for name, entity in final_ground_truth.entities.items():
            model_entity = model_state.get_entity(name)
            if model_entity and model_entity.resources == entity.resources:
                correct_entities += 1
        state_accuracy = correct_entities / total_entities if total_entities > 0 else 0.0

        return EvaluationResult(
            scenario_seed=scenario.seed,
            model_name=getattr(self.model, "name", "unknown"),
            conservation_held=len(violations) == 0,
            state_correct=state_correct,
            conservation_accuracy=conservation_accuracy,
            state_accuracy=state_accuracy,
            violations=violations,
            raw_response=response,
            parsed_state=self._state_to_dict(model_state),
            ground_truth=self._state_to_dict(final_ground_truth),
        )

    def _states_equal(self, state1: GlobalState, state2: GlobalState) -> bool:
        """Check if two states are equal"""
        if set(state1.entities.keys()) != set(state2.entities.keys()):
            return False
        for name in state1.entities:
            if state1.entities[name].resources != state2.entities[name].resources:
                return False
        return True

    def _state_to_dict(self, state: GlobalState) -> Dict:
        """Convert state to dictionary for serialization"""
        return {name: entity.resources for name, entity in state.entities.items()}
```

### File: `trace/evaluation/suite.py`

```python
"""
Run complete evaluation suites.
"""

import json
from typing import List, Dict, Optional
from dataclasses import asdict
from ..generation.scenario import ScenarioGenerator
from .executor import Evaluator, EvaluationResult

class BenchmarkSuite:
    """Run complete benchmark suites"""
    
    DIFFICULTY_CONFIGS = {
        'trivial': {
            'num_entities': 2,
            'num_tokens': 5,
            'num_actions': 2
        },
        'easy': {
            'num_entities': 3,
            'num_tokens': 10,
            'num_actions': 5
        },
        'medium': {
            'num_entities': 5,
            'num_tokens': 20,
            'num_actions': 10
        },
        'hard': {
            'num_entities': 10,
            'num_tokens': 50,
            'num_actions': 20
        }
    }
    
    def __init__(self, model_interface):
        self.model = model_interface
        self.evaluator = Evaluator(model_interface)
    
    def run_suite(
        self,
        difficulty: str = 'easy',
        num_scenarios: int = 10,
        seeds: Optional[List[int]] = None
    ) -> Dict:
        """Run a complete evaluation suite"""
        
        config = self.DIFFICULTY_CONFIGS[difficulty]
        results = []
        
        # Generate seeds if not provided
        if seeds is None:
            seeds = list(range(num_scenarios))
        
        for i, seed in enumerate(seeds):
            print(f"Running scenario {i+1}/{len(seeds)} (seed={seed})")
            
            # Generate scenario
            generator = ScenarioGenerator(seed)
            scenario = generator.generate_simple(**config)
            
            # Evaluate
            result = self.evaluator.evaluate_scenario(scenario)
            results.append(result)
            
            # Print summary
            print(f"  Conservation: {'✓' if result.conservation_held else '✗'}")
            print(f"  State: {'✓' if result.state_correct else '✗'}")
        
        # Aggregate results
        return self._aggregate_results(results, difficulty)
    
    def _aggregate_results(self, results: List[EvaluationResult], difficulty: str) -> Dict:
        """Aggregate individual results into summary"""
        
        total = len(results)
        conservation_passed = sum(1 for r in results if r.conservation_held)
        state_passed = sum(1 for r in results if r.state_correct)
        
        return {
            'difficulty': difficulty,
            'total_scenarios': total,
            'aggregate_scores': {
                'conservation_accuracy': conservation_passed / total,
                'state_accuracy': state_passed / total,
                'mean_entity_accuracy': sum(r.state_accuracy for r in results) / total
            },
            'individual_results': [asdict(r) for r in results]
        }
    
    def save_results(self, results: Dict, filepath: str):
        """Save results to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
```

---

## Phase 4: Model Adapters (Days 8-9)

### Objective
Create adapters for different model providers.

### File: `trace/models/base.py`

```python
"""
Base model interface.
"""

from abc import ABC, abstractmethod

class ModelInterface(ABC):
    """Abstract base class for model interfaces"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Model name for reporting"""
        pass
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from prompt"""
        pass
```

### File: `trace/models/openrouter.py`

```python
"""
OpenRouter API adapter.
"""

import os
import requests
import time
import random
from typing import Optional
from .base import ModelInterface


class OpenRouterModel(ModelInterface):
    """OpenRouter API adapter"""

    def __init__(
        self,
        model_name: str = "openai/gpt-3.5-turbo",
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        top_p: float = 1.0,
        max_retries: int = 3,
    ):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.temperature = temperature
        self.top_p = top_p
        self.max_retries = max_retries
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        if not self.api_key:
            raise ValueError("API key required")

    @property
    def name(self) -> str:
        return self.model_name

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response with retry logic"""

        temperature = kwargs.get("temperature", self.temperature)
        top_p = kwargs.get("top_p", self.top_p)

        backoff = 1.0
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": temperature,
                        "top_p": top_p,
                    },
                    timeout=30,
                )

                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                elif response.status_code == 429:  # Rate limit
                    # Exponential backoff with jitter
                    sleep = backoff + random.uniform(0, 0.25)
                    time.sleep(sleep)
                    backoff *= 2
                    continue
                else:
                    response.raise_for_status()

            except Exception:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(backoff)
                backoff *= 2

        raise Exception(f"Failed after {self.max_retries} attempts")
```

### File: `trace/models/mock.py`

```python
"""
Mock model for testing.
"""

import json
from .base import ModelInterface


class MockModel(ModelInterface):
    """Mock model that returns perfect JSON responses for the schema."""

    def __init__(self, should_fail: bool = False, total_tokens: int = 10):
        self.should_fail = should_fail
        self.total_tokens = total_tokens

    @property
    def name(self) -> str:
        return "mock-perfect" if not self.should_fail else "mock-failing"

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate perfect or failing JSON response."""

        if self.should_fail:
            # Return response that violates conservation
            return json.dumps(
                {
                    "entities": {
                        "entity_0": {"tokens": 100},
                        "entity_1": {"tokens": 100},
                        "entity_2": {"tokens": 100},
                    },
                    "totals": {"tokens": 300},
                }
            )

        # Simple heuristic: if prompt contains three example entity names (common in generator),
        # return a valid final state; otherwise return a trivial valid distribution.
        if "entity_0" in prompt and "entity_1" in prompt and "entity_2" in prompt:
            return json.dumps(
                {
                    "entities": {
                        "entity_0": {"tokens": 4},
                        "entity_1": {"tokens": 2},
                        "entity_2": {"tokens": 4},
                    },
                    "totals": {"tokens": self.total_tokens},
                }
            )
        else:
            return json.dumps(
                {
                    "entities": {
                        "entity_0": {"tokens": self.total_tokens // 2},
                        "entity_1": {"tokens": self.total_tokens - self.total_tokens // 2},
                    },
                    "totals": {"tokens": self.total_tokens},
                }
            )
```

---

## Phase 5: CLI and Main Entry Point (Day 10)

### Objective
Create user-friendly command-line interface.

### File: `trace/cli.py`

```python
"""
Command-line interface for TRACE benchmark.
"""

import argparse
import json
import sys
from pathlib import Path
from .models.openrouter import OpenRouterModel
from .models.mock import MockModel
from .generation.scenario import ScenarioGenerator
from .evaluation.executor import Evaluator
from .evaluation.suite import BenchmarkSuite

def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description="TRACE: Tracking Resource Allocation Consistency Evaluation"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Quick test command
    quick_parser = subparsers.add_parser('quick', help='Run quick test')
    quick_parser.add_argument('--model', default='openai/gpt-3.5-turbo')
    
    # Full suite command
    suite_parser = subparsers.add_parser('suite', help='Run full suite')
    suite_parser.add_argument('--model', default='openai/gpt-3.5-turbo')
    suite_parser.add_argument('--difficulty', default='easy',
                             choices=['trivial', 'easy', 'medium', 'hard'])
    suite_parser.add_argument('--scenarios', type=int, default=10)
    suite_parser.add_argument('--output', default='results.json')
    
    # Test command (uses mock)
    test_parser = subparsers.add_parser('test', help='Run with mock model')
    
    args = parser.parse_args()
    
    if args.command == 'quick':
        run_quick_test(args.model)
    elif args.command == 'suite':
        run_suite(args.model, args.difficulty, args.scenarios, args.output)
    elif args.command == 'test':
        run_test()
    else:
        parser.print_help()

def run_quick_test(model_name: str):
    """Run a single quick test"""
    
    print(f"Running quick test with {model_name}")
    
    # Initialize model
    model = OpenRouterModel(model_name)
    
    # Generate simple scenario
    generator = ScenarioGenerator(seed=42)
    scenario = generator.generate_simple(
        num_entities=3,
        num_tokens=10,
        num_actions=3
    )
    
    # Evaluate
    evaluator = Evaluator(model)
    result = evaluator.evaluate_scenario(scenario)
    
    # Print results
    print("\nResults:")
    print(f"Conservation: {'PASS ✅' if result.conservation_held else 'FAIL ❌'}")
    print(f"State: {'PASS ✅' if result.state_correct else 'FAIL ❌'}")
    print(f"Conservation Accuracy: {result.conservation_accuracy:.1%}")
    print(f"State Accuracy: {result.state_accuracy:.1%}")
    
    if result.violations:
        print("\nViolations:")
        for v in result.violations:
            print(f"  - {v.message}")

def run_suite(model_name: str, difficulty: str, num_scenarios: int, output_file: str):
    """Run full evaluation suite"""
    
    print(f"Running {difficulty} suite with {num_scenarios} scenarios")
    print(f"Model: {model_name}")
    
    # Initialize model
    model = OpenRouterModel(model_name)
    
    # Run suite
    suite = BenchmarkSuite(model)
    results = suite.run_suite(difficulty, num_scenarios)
    
    # Save results
    suite.save_results(results, output_file)
    
    # Print summary
    scores = results['aggregate_scores']
    print("\nAggregate Scores:")
    print(f"Conservation Accuracy: {scores['conservation_accuracy']:.1%}")
    print(f"State Accuracy: {scores['state_accuracy']:.1%}")
    print(f"Mean Entity Accuracy: {scores['mean_entity_accuracy']:.1%}")
    print(f"\nResults saved to {output_file}")

def run_test():
    """Run test with mock model"""
    
    print("Running test with mock model")
    
    # Test with perfect mock
    model = MockModel(should_fail=False)
    suite = BenchmarkSuite(model)
    results = suite.run_suite('trivial', num_scenarios=2)
    
    scores = results['aggregate_scores']
    assert scores['conservation_accuracy'] == 1.0, "Mock should be perfect"
    assert scores['state_accuracy'] == 1.0, "Mock should be perfect"
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    main()
```

### File: `setup.py`

```python
"""
Setup script for TRACE benchmark.
"""

from setuptools import setup, find_packages

setup(
    name="trace-benchmark",
    version="0.1.0",
    description="Tracking Resource Allocation Consistency Evaluation",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "pytest>=7.0.0",
        "jsonschema>=4.0.0",
    ],
    entry_points={
        "console_scripts": [
            "trace=trace.cli:main",
        ],
    },
)
```

---

## Installation and Usage

### Installation

```bash
# Clone repository
git clone <repository-url>
cd trace-benchmark

# Install package
pip install -e .

# Set API key
export OPENROUTER_API_KEY="your-key-here"
```

### Running Tests

```bash
# Run unit tests
pytest tests/ -v

# Run mock test
trace test

# Run quick evaluation
trace quick --model openai/gpt-3.5-turbo

# Run full suite
trace suite --difficulty easy --scenarios 10 --output results.json
```

---

## Validation Checkpoints

### Checkpoint 1: Steel Thread (Day 1)
- [ ] `steel_thread.py` runs successfully
- [ ] API connection works with retries and timeouts
- [ ] Strict JSON response parsing works (schema validated)
- [ ] Conservation detection works
- [ ] Results match expected JSON format and include params

### Checkpoint 2: Core Engine (Day 3)
- [ ] All unit tests pass
- [ ] State tracking works correctly
- [ ] Conservation verification works
- [ ] Actions apply correctly

### Checkpoint 3: Generation (Day 5)
- [ ] Scenarios generate deterministically (by seed)
- [ ] Prompts require strict JSON output
- [ ] Ground truth calculation correct (sequential application)

### Checkpoint 4: Evaluation (Day 7)
- [ ] Strict JSON response parsing works
- [ ] Metrics calculate correctly (final-state accuracy for steel thread)
- [ ] Results aggregate properly

### Checkpoint 5: Full System (Day 10)
- [ ] CLI works end-to-end
- [ ] Results are reproducible
- [ ] Performance is acceptable
- [ ] Documentation is complete

---

## Expected Results

### Baseline Performance Expectations

| Model | Difficulty | Conservation Accuracy | State Accuracy |
|-------|------------|----------------------|----------------|
| GPT-3.5 | Trivial | >95% | >90% |
| GPT-3.5 | Easy | >90% | >80% |
| GPT-3.5 | Medium | >80% | >60% |
| GPT-3.5 | Hard | >60% | >40% |
| GPT-4 | Easy | >98% | >95% |
| GPT-4 | Medium | >95% | >85% |
| GPT-4 | Hard | >85% | >70% |

---

## Debugging Guide

### Common Issues and Solutions

1. **Model returns empty state**
   - Check response parsing patterns
   - Add debug logging to see raw response
   - Verify prompt format

2. **Conservation always fails**
   - Check baseline calculation
   - Verify resource counting logic
   - Ensure proper state cloning

3. **State never matches ground truth**
   - Check entity name normalization
   - Verify action application order
   - Test with mock model first

4. **API rate limits**
   - Implement exponential backoff
   - Add caching layer
   - Reduce parallel requests

---

## Next Steps After Implementation

1. **Expand rule types**: Add transformation, cascade rules
2. **Multi-resource support**: Track multiple resource types
3. **Perspective testing**: Add information hiding
4. **Longer horizons**: Test 100+ turn scenarios
5. **More models**: Add Anthropic, Cohere, local models
6. **Visualization**: Create degradation curves
7. **Paper writing**: Document findings
8. **Community release**: Open source the benchmark

---

## AI Agent Instructions

```
To implement this benchmark:

1. Start with steel_thread.py - get it working first
2. Build core engine with heavy unit testing
3. Keep functions under 20 lines each
4. Add logging everywhere for debugging
5. Test with mock before real API calls
6. Validate each phase before moving on
7. Document any deviations from plan

Priority order:
1. Steel thread must work
2. Core state tracking must be perfect
3. Everything else builds on top

If stuck, focus on getting simplest version working first.
```

---

## Results Schema and Reproducibility

The benchmark produces structured JSON/JSONL with a stable schema. Key fields:

- trace_schema_version: string (e.g., "0.1.0")
- model: string; params: object (temperature, top_p, etc.)
- prompt_hash: string (SHA256 of full prompt string)
- scenario_config: object (num_entities, num_tokens, num_actions)
- seed: number (or list of numbers for suites)
- timestamps: started_at, ended_at (ISO 8601)
- parsed_state: object; ground_truth: object
- violations: list
- metrics: { conservation_held, state_correct, conservation_accuracy, state_accuracy }

Example JSON Schema (excerpt):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.org/trace-result.schema.json",
  "type": "object",
  "required": ["trace_schema_version", "model", "params", "prompt_hash", "metrics"],
  "properties": {
    "trace_schema_version": {"type": "string"},
    "model": {"type": "string"},
    "params": {"type": "object"},
    "prompt_hash": {"type": "string"},
    "scenario_config": {"type": "object"},
    "seed": {"type": ["integer", "array"]},
    "timestamps": {"type": "object"},
    "parsed_state": {"type": "object"},
    "ground_truth": {"type": "object"},
    "violations": {"type": "array"},
    "metrics": {
      "type": "object",
      "required": ["conservation_held", "state_correct", "conservation_accuracy", "state_accuracy"],
      "properties": {
        "conservation_held": {"type": "boolean"},
        "state_correct": {"type": "boolean"},
        "conservation_accuracy": {"type": "number"},
        "state_accuracy": {"type": "number"}
      }
    }
  }
}
```

Reproducibility: Always capture `seed`, `scenario_config`, model `params`, and `prompt_hash`. For suites, write an incremental `results.jsonl` and an aggregate `results.json`.

---

## Per-Turn Mode (Future Extension)

To measure degradation over time, add a per-turn mode with this output schema:

```json
{
  "turns": [
    {"entities": {"entity_0": {"tokens": 3}, ...}, "totals": {"tokens": 10}},
    {"entities": {"entity_0": {"tokens": 2}, ...}, "totals": {"tokens": 10}},
    {"entities": {"entity_0": {"tokens": 4}, ...}, "totals": {"tokens": 10}}
  ]
}
```

Metrics: per-turn conservation pass rate, per-turn entity accuracy, and aggregate means across turns, while retaining final-state metrics for compatibility.

---

## CLI Options (Overview)

- --model: model identifier (e.g., openai/gpt-3.5-turbo)
- --difficulty: trivial|easy|medium|hard
- --scenarios: number of scenarios to run
- --output / --output-dir: file or directory for results; writes JSONL + JSON
- --jsonl: enable JSONL incremental writes (suite)
- --save-prompts: save prompts/responses per scenario for debugging
- --temperature / --top-p: decoding params; default to 0 and 1
- --retries: number of API retries (default 3)
- --concurrency: max parallel scenarios (suite)
- --cache: enable prompt-hash-based response caching (optional)
