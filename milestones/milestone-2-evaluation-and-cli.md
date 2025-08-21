Milestone 2 — Evaluation Framework (Final-State) and CLI Quick/Test

Objective
- Build the evaluation pipeline around strict JSON final-state parsing, add CLI commands for quick/test/suite, and produce reproducible artifacts.

Scope
- PromptBuilder (final-state), Evaluator (strict JSON), BenchmarkSuite (aggregation), CLI enhancements, and result artifacts (JSON/JSONL).

Implementation Plan
- Prompting
  - `PromptBuilder` final-state prompt requiring strict JSON schema; no extra text.
  - Include initial state, actions, and explicit example of JSON shape.

- Evaluator
  - `_parse_json_response(response)` → `GlobalState` with lowercase entity keys.
  - `evaluate_scenario(scenario)` computes:
    - conservation violations against baseline,
    - final-state correctness and per-entity accuracy,
    - result fields: `trace_schema_version`, `prompt_hash`, `scenario_seed`, `scenario_config`, timestamps, model params.
  - Expose serialization helpers `_state_to_dict` and equality `_states_equal`.

- BenchmarkSuite
  - Difficulty presets as in PRD.
  - `run_suite` iterates seeds, generates scenarios, evaluates, aggregates metrics (means).
  - `save_results` writes JSON aggregate; add optional JSONL writing of individual results.

- CLI
  - Commands: `trace test`, `trace quick`, `trace suite`.
  - Add flags: `--output-dir`, `--jsonl`, `--save-prompts`, `--temperature`, `--top-p`, `--retries`.
  - If `--save-prompts`, dump `{seed}.prompt.txt` and `{seed}.response.txt` to output dir.

Artifacts
- Output directory (default `./trace-runs/<timestamp>/`).
- Files: `results.jsonl` (optional), `results.json` (aggregate), `prompts/` (optional), `responses/` (optional).

Testing Plan
- Unit Tests
  - Evaluator JSON parsing: success and bad schema (missing keys, wrong types).
  - Equality: states equal vs off-by-one.
  - Aggregation: mean entity accuracy equals average of individual `state_accuracy`.

- Integration Tests
  - `trace test` with `MockModel` perfect JSON → all metrics 1.0.
  - `trace quick --model mock` writes files; schema validates (using `jsonschema`).
  - Failure: mock returns non-JSON → CLI reports clear error and non-zero exit.

Validation / Acceptance Criteria
- CLI commands work end-to-end with mock and record artifacts.
- Aggregate and per-scenario results pass schema validation; metrics consistent.

Deliverables
- `trace/generation/prompt_builder.py`, `trace/evaluation/executor.py`, `trace/evaluation/suite.py` finalized for final-state.
- `trace/cli.py` with new flags and default output dir behavior.
- Schema file (`schemas/trace-result.schema.json`) optional in this milestone or next.

Risks & Mitigations
- Provider formatting drift → strict prompts and low temp; fail fast with clear schema errors.
- Large outputs → keep prompts concise; cap tokens if provider requires.

Timeline
- 1 day implementation, 0.5 day tests and validation.

Rollback
- If strictness causes frequent provider failures, add a one-time retry with a more forceful instruction.

