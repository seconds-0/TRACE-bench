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
  - `python steel_thread.py --model openai/gpt-3.5-turbo --save-prompt`

Artifacts:
- `steel_thread_results.json` (results)
- `steel_thread_prompt.txt` and `steel_thread_response.txt` when `--save-prompt` is set.

## Validate Outputs
- Single JSON:
  - `python tools/validate_results.py steel_thread_results.json`
- JSONL (from suites later):
  - `python tools/validate_results.py path/to/results.jsonl`

## Run Tests
- `pytest -v`

## Continuous Integration
- GitHub Actions runs tests on push/PR in mock mode.
- Badge and workflow: see `README.md`.

## Tips
- Determinism: steel thread uses `temperature=0` and `top_p=1`.
- Troubleshooting non-JSON: the script retries once with a stricter reminder.
- Env hygiene: never commit API keys; use `OPENROUTER_API_KEY`.
