# TRACE Benchmark

[![CI](https://github.com/seconds-0/TRACE-bench/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/seconds-0/TRACE-bench/actions/workflows/ci.yml)

TRACE (Tracking Resource Allocation Consistency Evaluation) benchmarks LLMs on state tracking under conservation constraints over time.

## Steel Thread (Quick Start)
- Mock (no network):
  - `export MOCK_STEEL_THREAD=1`
  - `python steel_thread.py --model openai/gpt-3.5-turbo --save-prompt`
- Live (OpenRouter):
  - `export OPENROUTER_API_KEY=your_key`
  - `python steel_thread.py --model openai/gpt-3.5-turbo --save-prompt`

Outputs: `steel_thread_results.json` plus optional `steel_thread_prompt.txt` and `steel_thread_response.txt`.

## Validate Results
Validate a single JSON file or a JSONL stream against the schema:

- `python tools/validate_results.py steel_thread_results.json`
- `python tools/validate_results.py path/to/results.jsonl`

Schema: `schemas/trace-result.schema.json`.

## Tests & CI
- Run locally: `pytest -v`
- CI runs on push/PR (badge above) using mock mode.

For full plans and roadmap, see `PRD.md` and `milestones/`.

