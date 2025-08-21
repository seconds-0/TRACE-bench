Milestone 0 — Steel Thread v1 (Strict JSON, Final-State)

Objective
- Deliver a minimal, robust end-to-end benchmark path proving concept validity with strict JSON output and deterministic decoding.

Scope
- One-shot scenario with 3 entities, 3 turns, single resource (tokens), conservation invariant.
- Strict JSON output enforced and validated. No per-turn evaluation yet (final-state only).

Implementation Plan
- steel_thread.py
  - Enforce strict JSON output with explicit schema in the prompt; no free-form text.
  - Determinism: set temperature=0, top_p=1.
  - Add retries with exponential backoff and timeouts.
  - Parse JSON and validate required fields; normalize entity names (lowercase keys).
  - Compute and include:
    - trace_schema_version (e.g., 0.1.0),
    - prompt_hash (SHA256),
    - params (temperature, top_p),
    - timestamps (started_at, ended_at),
    - expected_state, actual_state, expected_total, actual_total, reported_total.
  - Write results to steel_thread_results.json.

- Prompt content
  - Include CRITICAL RULES and initial state.
  - Include actions explicitly.
  - Include JSON schema example with placeholders and instruction: “Respond ONLY with a single JSON object.”

- Dependencies
  - Add jsonschema>=4.0.0 to setup.py for validating results (if used in tests).

Testing Plan
- Unit Tests
  - JSON parsing: valid JSON → dict; missing keys → error; wrong types → error.
  - Prompt hashing: compute SHA256; ensure stable across runs.
  - Conservation verification: correct and incorrect cases.

- Integration Tests
  - Mock model returning perfect JSON: conservation_held=True, state_correct=True.
  - Mock model returning over-total JSON: conservation_held=False.
  - OpenRouter smoke (optional/manual): run once and assert JSON decodes.

Validation / Acceptance Criteria
- steel_thread.py executes without error and writes steel_thread_results.json.
- Results include: trace_schema_version, prompt_hash, params, timestamps, expected/actual states and totals.
- Conservation and final state correctness computed correctly for the example.
- Tests pass for success and failure paths.

Deliverables
- steel_thread.py (final-state, strict JSON) with retries and timeouts.
- Mock-based integration tests for conformance.
- steel_thread_results.json sample artifact.

Risks & Mitigations
- Model ignores JSON instruction → fail fast with clear error; optional re-prompt is out-of-scope for v1.
- API rate limits → retries with backoff and logging.

Timeline
- 0.5 day implementation, 0.5 day tests and validation.

Rollback
- Revert to simpler final-state parser if strict JSON causes systematic failures (not recommended); prefer tightening prompt and retrying.

