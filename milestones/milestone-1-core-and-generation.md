Milestone 1 — Core Engine and Deterministic Scenario Generation

Objective
- Implement the core state engine with robust error handling and build a deterministic scenario generator that applies actions sequentially.

Scope
- State management (`trace/core/state.py`), actions (`trace/core/actions.py`), verifier (`trace/core/verifier.py`).
- Scenario generation (`trace/generation/scenario.py`) with sequential state updates and seed determinism.

Implementation Plan
- Core State
  - Replace `assert` with exceptions in state mutations (done in PRD).
  - Ensure `GlobalState.clone()` uses deep copy.
  - Normalize entity keys consistently (lowercase at parse/evaluation time; keep original names if needed for prompts).
  - Document invariants in docstrings.

- Actions
  - `TransferAction.apply(state)` clones state, validates entities exist, applies deltas with negative checks, sets `turn`.
  - Add clear error messages: missing entity, negative balance.

- Verifier
  - `ConservationVerifier.set_baseline(state)` stores totals.
  - `verify(state)` compares current totals against baseline; report new resource types.
  - Return a list of `Violation` with turn, type, expected, actual, message.

- Scenario Generator
  - Fix sequential application: maintain `live_state` and apply each new action to it.
  - Seed determinism: use `random.Random(seed)` everywhere; record `seed` in `Scenario`.
  - Distribution: random allocation that sums to `num_tokens`.
  - Actions: sample source/target and amount ≤ current source tokens (cap at 3 for difficulty).

Testing Plan
- Unit Tests (core)
  - `EntityState`: set/get/modify; negative operations raise `ValueError`.
  - `GlobalState`: add/get entities; `calculate_totals` correctness; `clone` immutability.
  - `TransferAction`: correct deltas; error on missing entity; error on overdraft.
  - `ConservationVerifier`: no violations on valid transfer; single violation on token creation.

- Unit Tests (generation)
  - Determinism: same seed+config → identical actions and ground truth states.
  - Sequentiality: verify applying `actions` in order yields the same final state as generator’s live progression.
  - Edge: zero-token entity; transfers when source is zero are skipped.

Validation / Acceptance Criteria
- All core unit tests pass.
- Scenario generation is deterministic and sequential; conservation holds across ground truth states.
- `Violation` reports contain meaningful messages.

Deliverables
- Implemented core modules with tests: `trace/core/*`, `trace/generation/scenario.py`.
- `tests/test_core.py` extended for edge cases.

Risks & Mitigations
- Name normalization inconsistencies → normalize in evaluator parsing path; document conventions.
- Random generation corner cases → defensive checks (skip actions when max_amount ≤ 0).

Timeline
- 1 day implementation, 0.5 day tests and validation.

Rollback
- If determinism issues appear, temporarily lock entity list and action sampling order; add debug logging of RNG state.

