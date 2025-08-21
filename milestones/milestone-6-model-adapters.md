Milestone 6 — Model Adapters and Extensibility (Optional)

Objective
- Expand supported providers by adding adapters that conform to `ModelInterface`, keeping strict JSON output requirements intact.

Scope
- New adapters (e.g., Anthropic, Cohere, local models), adapter tests, docs.

Implementation Plan
- Adapters
  - Implement classes in `trace/models/` that expose `.name` and `.generate(prompt, **kwargs)`.
  - Add provider-specific headers, timeouts, retry/backoff as needed.
  - Normalize responses to text; Evaluator remains responsible for JSON parsing.

- CLI Integration
  - Allow specifying adapter via `--model` name or a `--provider` flag if needed.
  - Document required environment variables (API keys) and safety.

Testing Plan
- Contract tests with mocks to ensure `.generate` obeys expected signature and returns strings.
- Smoke tests for real providers where feasible (optional/manual), stubbed by environment flags.

Validation / Acceptance Criteria
- Quick suite runs against at least one additional provider using the same prompts.
- No changes required to Evaluator/PromptBuilder logic.

Deliverables
- New adapter modules, docs on configuration and rate limits.

Risks & Mitigations
- Rate limiting and cost → concurrency defaults conservative; support caching.
- Provider formatting differences → strict prompts; fail fast if schema not met.

Timeline
- 1–2 days per provider depending on API complexity.

Rollback
- Keep adapter isolated; do not affect core benchmark if removed.

