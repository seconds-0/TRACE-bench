# Run Instructions

This guide shows how to run the TRACE steel thread locally, validate outputs, and use CI.

## Prerequisites
- Python 3.8+
- Dependencies: `pip install pytest jsonschema requests`

## Steel Thread (Local)
- Mock (no network):
  - `export MOCK_STEEL_THREAD=1`
  - `python steel_thread.py --model openai/gpt-3.5-turbo --save-prompt`
- Live (OpenRouter):
  - `export OPENROUTER_API_KEY=your_key`
  - `python steel_thread.py --model mistralai/mistral-7b-instruct:free --save-prompt`

Artifacts:
- `steel_thread_results.json` (results)
- `steel_thread_prompt.txt` and `steel_thread_response.txt` when `--save-prompt` is set.

## Validate Outputs
- Single JSON:
  - `python tools/validate_results.py steel_thread_results.json --schema steel`
- JSONL (per-scenario):
  - `python tools/validate_results.py path/to/results.jsonl --schema result`
- Aggregate (suite):
  - `python tools/validate_results.py path/to/aggregate.json --schema aggregate`

## CLI (Quick/Suite)
- Quick (per-turn):
  - `python -m trace.cli quick --mode per_turn --model mistralai/mistral-7b-instruct:free`
- Suite (with JSONL, concurrency, caching):
  - `python -m trace.cli suite --mode per_turn --difficulty easy --scenarios 10 \
    --concurrency 4 --cache --cache-dir .trace_cache \
    --model mistralai/mistral-7b-instruct:free \
    --jsonl results.jsonl --output aggregate.json`

## Run Tests
- `pytest -v`

## Continuous Integration
- GitHub Actions runs tests on push/PR in mock mode.
- Badge and workflow: see `README.md`.
 - Live Smoke runs on PRs when `OPENROUTER_API_KEY` is available as a repo secret.

## Tips
- Determinism: steel thread uses `temperature=0` and `top_p=1`.
- Troubleshooting non-JSON: the script retries once with a stricter reminder.
- Env hygiene: never commit API keys; use `OPENROUTER_API_KEY`.
 - Adapters: OpenRouter (live), Anthropic/Cohere placeholders requiring keys.
