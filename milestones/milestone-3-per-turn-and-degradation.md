Milestone 3 — Per-Turn Mode and Degradation Metrics

Objective
- Extend prompts and evaluation to return and score per-turn states, enabling measurement of degradation over time while preserving final-state compatibility.

Scope
- PromptBuilder per-turn variant, Evaluator per-turn parser, metrics per turn, CLI `--mode {final,per_turn}`.

Implementation Plan
- Prompting
  - Add `PromptBuilder.build_per_turn_prompt()` returning instructions to output:
    ```json
    { "turns": [ {"entities": {..}, "totals": {"tokens": ..}}, ... ] }
    ```
  - Decide whether `turns[0]` is the state after applying the first action (recommended). Document it in PRD.

- Evaluator
  - Implement `_parse_per_turn_response(response)` to produce `List[GlobalState]`.
  - Compute metrics per turn:
    - `conservation_accuracy_per_turn`: 1 if totals match baseline, else 0.
    - `entity_accuracy_per_turn`: fraction of entities exactly matching ground truth per turn.
  - Aggregate:
    - `mean_conservation_accuracy` and `mean_entity_accuracy` across turns,
    - retain final-state `conservation_accuracy` and `state_accuracy` for comparability.
  - Result field `mode`: `per_turn`.

- CLI
  - Add `--mode {final,per_turn}` to `quick` and `suite`.
  - Persist per-turn arrays in JSON/JSONL when `per_turn`.

Artifacts
- Extended result JSON including per-turn arrays and aggregated per-turn metrics.

Testing Plan
- Unit Tests
  - Per-turn parser: valid shapes; missing `turns`; turn entries missing `entities` or `totals`.
  - Metric correctness: hand-built scenario with known per-turn ground truth.

- Integration Tests
  - Mock model returns perfect per-turn sequence → all per-turn metrics 1.0.
  - Mock model with drift (e.g., off-by-one in last turn) → final-state accuracy drops accordingly; per-turn accuracies reflect the deviation.

Validation / Acceptance Criteria
- `--mode per_turn` runs produce valid per-turn arrays and correct averages; schema validates.
- Final-state mode continues to work unchanged.

Deliverables
- Updated `PromptBuilder`, `Evaluator`, CLI.
- Tests for per-turn parsing and metrics.

Risks & Mitigations
- Model output length limits → keep number of turns small by default; optionally request only final plus checkpoints.
- Parsing ambiguity → strict schema and explicit examples in prompt.

Timeline
- 1 day implementation, 0.5 day tests and validation.

Rollback
- If per-turn reliability is low for some models, keep per-turn mode optional and default to final-state in CLI.

