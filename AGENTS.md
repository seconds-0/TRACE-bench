# Repository Guidelines

## Philosophy & Operating Principles
- Senior engineer mindset: you own technical decisions. Be confident, opinionated, and bias toward shipping quality.
- Proactive leadership: propose clear next steps to satisfy the plan and improve the product; don’t wait for prompts.
- Minimize check-ins: only pause for legitimate Product/UX uncertainty or external blockers. Engineering choices are yours—research, decide, execute.
- Guardrails: protect the steel-thread path, conservation invariants, determinism, and result schemas. Prefer small, tested changes.
- Communication: provide concise progress updates and surface risks with recommended mitigations.

## Project Structure & Module Organization
- `trace/`: source package
  - `core/`: state, actions, verification
  - `generation/`: scenarios, prompt builders
  - `evaluation/`: executor and suites
  - `models/`: model adapters (OpenRouter, mock)
- `tests/`: unit/integration tests
- `milestones/`: detailed implementation plans
- `steel_thread.py`: minimal end-to-end demo
- `schemas/` (planned): JSON schemas for results

## Build, Test, and Development Commands
- Install (editable): `pip install -e .`
- Run unit tests: `pytest tests -v`
- Quick check (real model): `trace quick --model openai/gpt-3.5-turbo`
- Full suite: `trace suite --difficulty easy --scenarios 10 --output results.json`
- Mock test (no API): `trace test`
- Env: `export OPENROUTER_API_KEY=your_key`

## Coding Style & Naming Conventions
- Python 3.8+, prefer dataclasses and type hints.
- Raise explicit exceptions (no `assert` for runtime checks).
- Keep functions focused and small; avoid deep nesting.
- Entity keys normalized to lowercase in evaluation.
- Filenames: `snake_case.py`; classes `CamelCase`; functions/vars `snake_case`.

## Testing Guidelines
- Framework: `pytest` (targeted unit tests + small integrations).
- Name tests `test_*.py`; co-locate fixtures in `tests/`.
- Cover: state transitions, verifier, scenario determinism, JSON parsing.
- Before PRs: run `pytest -q` and `trace test` (mock must pass).

## Commit & Pull Request Guidelines
- Commits: imperative mood, scoped when helpful (e.g., `core: raise ValueError on negatives`).
- PRs must include:
  - Summary, rationale, and linked issue/milestone.
  - Tests for new behavior and schema changes.
  - Results snippet (`trace test` output) when touching evaluation.

## Security & Configuration Tips
- Never commit API keys; use `OPENROUTER_API_KEY` env var.
- Avoid logging prompts/responses unless `--save-prompts` explicitly set.
- Respect provider rate limits; keep default temperature=0, top_p=1.

## Architecture Overview
- Steel thread proves end-to-end with strict JSON I/O.
- Core engine enforces conservation; generation is seed-deterministic.
- Evaluation parses strict JSON and computes accuracy metrics.
- Adapters isolate provider specifics; CLI orchestrates runs and artifacts.
