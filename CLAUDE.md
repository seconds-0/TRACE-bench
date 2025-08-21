# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Running the Steel Thread
- **Mock mode (no network)**: `export MOCK_STEEL_THREAD=1; python steel_thread.py --model openai/gpt-3.5-turbo --save-prompt`
- **Live mode**: `export OPENROUTER_API_KEY=your_key; python steel_thread.py --model openai/gpt-3.5-turbo --save-prompt`

### Testing
- **Run all tests**: `pytest -v`
- **Validate results schema**: `python tools/validate_results.py steel_thread_results.json`

### Dependencies
- Install: `pip install pytest jsonschema requests`
- Python 3.8+ required

## Architecture Overview

TRACE (Tracking Resource Allocation Consistency Evaluation) is a benchmark for evaluating LLMs' ability to maintain consistent state tracking under conservation constraints.

### Core Components

1. **Steel Thread** (`steel_thread.py`): Minimal end-to-end implementation
   - Single scenario with 3 entities and token transfers
   - Strict JSON output requirement
   - Conservation and state correctness validation
   - Mock mode for testing without API calls

2. **Validation Tools** (`tools/validate_results.py`):
   - Schema validation against `schemas/trace-result.schema.json`
   - Supports both single JSON files and JSONL streams

3. **Test Suite** (`tests/test_steel_thread.py`):
   - Mock mode testing
   - Schema validation
   - Error handling verification

### Key Design Principles

- **Conservation Laws**: Resources cannot be created/destroyed, only transferred
- **Strict JSON**: Models must return exact schema format, no additional prose
- **Deterministic**: Uses temperature=0, top_p=1 for reproducibility
- **Schema Validation**: All outputs validated against JSON schema
- **Mock Support**: Can run without network calls using `MOCK_STEEL_THREAD=1`

### File Structure
```
steel_thread.py          # Main implementation
tests/                   # Test suite
tools/validate_results.py # Schema validation
schemas/                 # JSON schemas
milestones/             # Development roadmap
.github/workflows/ci.yml # CI configuration
```

### Results Format

Results are JSON objects with schema version tracking, including:
- `trace_schema_version`: Schema version ("0.1.0")
- `model`: Model identifier
- `params`: Model parameters (temperature, top_p)
- `prompt_hash`: SHA256 of full prompt
- `timestamps`: ISO 8601 timestamps
- `conservation_held`: Boolean conservation check
- `state_correct`: Boolean state accuracy
- `expected_state`/`actual_state`: Ground truth vs model output
- `raw_response`: Full model response

### Future Extensions

The codebase is designed for expansion into a full benchmark suite with:
- Multiple difficulty levels
- Procedural scenario generation
- Multi-turn state tracking
- Model adapter interfaces
- CLI for batch evaluation

Current implementation focuses on the "steel thread" - minimal viable benchmark proving the core concept works end-to-end.