# TRACE Benchmark

[![CI](https://github.com/seconds-0/TRACE-bench/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/seconds-0/TRACE-bench/actions/workflows/ci.yml)

TRACE (Tracking Resource Allocation Consistency Evaluation) benchmarks LLMs on state tracking under conservation constraints over time.

## Steel Thread (Quick Start)
- Mock (no network):
  - `export MOCK_STEEL_THREAD=1`
  - `python steel_thread.py --model openai/gpt-3.5-turbo --save-prompt`
- Live (OpenRouter):
  - `export OPENROUTER_API_KEY=your_key`
  - `python steel_thread.py --model mistralai/mistral-7b-instruct:free --save-prompt`

Outputs: `steel_thread_results.json` plus optional `steel_thread_prompt.txt` and `steel_thread_response.txt`.

## CLI: Quick, Suite, JSONL
- Quick per-turn (live):
  - `export OPENROUTER_API_KEY=your_key`
  - `python -m trace.cli quick --mode per_turn --model mistralai/mistral-7b-instruct:free`
- Suite with JSONL + concurrency + cache (live):
  - `export OPENROUTER_API_KEY=your_key`
  - `python -m trace.cli suite --mode per_turn --difficulty easy --scenarios 10 \
    --concurrency 4 --cache --cache-dir .trace_cache \
    --model mistralai/mistral-7b-instruct:free \
    --jsonl results.jsonl --output aggregate.json`

## Validate Results
- Single JSON (steel thread):
  - `python tools/validate_results.py steel_thread_results.json --schema steel`
- JSONL (per-scenario results):
  - `python tools/validate_results.py results.jsonl --schema result`
- Aggregate (suite run):
  - `python tools/validate_results.py aggregate.json --schema aggregate`

## Tests & CI
- Run locally: `pytest -v`
- CI runs on push/PR (badge above) using mock mode. It also generates mock JSONL + aggregate and validates schemas.
- Live smoke on PR: runs a per-turn quick test on a free model when `OPENROUTER_API_KEY` secret is present.

## Adapters
- OpenRouter: requires `OPENROUTER_API_KEY`.
- Anthropic (placeholder): requires `ANTHROPIC_API_KEY`.
- Cohere (placeholder): requires `COHERE_API_KEY`.

For full plans and roadmap, see `PRD.md` and `milestones/`.
