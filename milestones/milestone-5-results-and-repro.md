Milestone 5 — Results Schema, Reporting, and Reproducibility

Objective
- Lock down a versioned results schema, improve reporting outputs, and document reproducibility practices.

Scope
- JSON Schema file, JSON/JSONL outputs, metadata completeness, simple plotting utility (optional).

Implementation Plan
- Schema
  - Create `schemas/trace-result.schema.json` (from PRD excerpt, extended as needed).
  - Add a lightweight validator helper used in tests.

- Outputs
  - Always write `results.jsonl` (one JSON per line) during suite execution.
  - Aggregate `results.json` summary with means and counts.
  - Include: `trace_schema_version`, `prompt_hash`, timestamps, `scenario_config`, `mode`.

- Reproducibility Docs
  - Document seeds, prompt hashing, model params, environment capture.
  - Provide a short “repro checklist” in README/PRD.

- Visualization (optional)
  - `tools/plot_degradation.py`: read JSONL and plot per-turn metrics across seeds.

Testing Plan
- Schema validation: validate example results and produced runs against schema via `jsonschema`.
- Aggregation: ensure summary metrics match averages of individual results.

Validation / Acceptance Criteria
- Produced artifacts validate against schema.
- Reproducibility guide is clear and accurate.

Deliverables
- `schemas/trace-result.schema.json` and validator helper.
- Documentation updates for results and repro.

Risks & Mitigations
- Schema drift → version bump `trace_schema_version` and changelog note.

Timeline
- 0.5 day implementation, 0.5 day tests and docs.

Rollback
- Keep previous schema version available; support dual-parse if necessary.

