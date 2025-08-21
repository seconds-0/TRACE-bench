Milestone 4 — Concurrency, Caching, and Robustness

Objective
- Speed up suites safely via bounded concurrency and reduce costs with optional caching. Centralize retry logic and add structured logging.

Scope
- BenchmarkSuite concurrency, cache layer (opt-in), centralized retries, logging and CLI flags.

Implementation Plan
- Concurrency
  - Add `--concurrency N` to CLI `suite`.
  - Use `concurrent.futures.ThreadPoolExecutor(max_workers=N)` to evaluate scenarios in parallel.
  - Queue seeds; ensure thread-safe writes by collecting results in memory and writing after each future completes.

- Caching (optional)
  - Add `--cache` and `--cache-dir` (default `~/.trace_cache`).
  - Cache key: `f"{model_name}:{prompt_hash}"` with JSON response body.
  - On hit, skip API call and use cached response.
  - Atomic writes: write to temp file then rename.

- Retries
  - Keep adapter retries; allow `--retries` CLI override.

- Logging
  - Use Python `logging` with `--log-level` flag.
  - Log per-scenario summary (seed, conservation/state pass).
  - If `--save-prompts`, write prompt/response files in per-run output dir.

Artifacts
- `results.jsonl` incremental writes to support long runs; `results.json` aggregate at end.

Testing Plan
- Unit Tests
  - Cache: key generation, file I/O, atomic writes, reuse read.
  - Concurrency: run small suite with N>1 and assert all seeds processed; no race conditions in result aggregation.

- Integration Tests
  - Use `MockModel` to count generate calls and assert reduction with `--cache` on second run.
  - Simulate rate-limit errors in mock adapter; ensure retries/backoff work.

Validation / Acceptance Criteria
- Suite runs with `--concurrency` show speedup and stable behavior.
- Cache reduces API calls on re-runs when enabled.

Deliverables
- Updated `suite.py` with concurrency and JSONL output.
- Optional cache module and CLI wiring.

Risks & Mitigations
- Provider rate limits → keep default concurrency low; document best practices.
- Cache staleness → include model name and prompt hash; allow `--no-cache` to disable.

Timeline
- 1 day implementation, 0.5 day tests and validation.

Rollback
- Disable cache flag and run sequentially if issues arise.

