import json
import os
from pathlib import Path

import jsonschema

from steel_thread import SteelThreadTRACE, TRACE_SCHEMA_VERSION, main as steel_main


def load_schema():
    schema_path = Path("schemas/trace-result.schema.json")
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_steel_thread_mock_pass(tmp_path, monkeypatch):
    # Ensure mock path (no network)
    monkeypatch.setenv("MOCK_STEEL_THREAD", "1")
    # Run the steel thread
    runner = SteelThreadTRACE()
    results = runner.run()

    # Validate basic expectations
    assert results["trace_schema_version"] == TRACE_SCHEMA_VERSION
    assert results["conservation_held"] is True
    assert results["state_correct"] is True
    assert results["expected_total"] == results["actual_total"] == results["reported_total"]

    # Validate schema
    schema = load_schema()
    jsonschema.validate(instance=results, schema=schema)

    # Ensure file can be written and validates
    results_path = tmp_path / "steel_thread_results.json"
    results_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    saved = json.loads(results_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=saved, schema=schema)


def test_live_requires_api_key(monkeypatch):
    # Ensure we don't call live API without key
    monkeypatch.delenv("MOCK_STEEL_THREAD", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    runner = SteelThreadTRACE()
    try:
        runner.run()
    except ValueError as e:
        assert "OPENROUTER_API_KEY" in str(e)
    else:
        raise AssertionError("Expected ValueError due to missing API key for live call")


def test_invalid_json_path(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")
    monkeypatch.delenv("MOCK_STEEL_THREAD", raising=False)
    runner = SteelThreadTRACE()

    # Force call_model to return invalid JSON twice to trigger retry then failure
    calls = {"n": 0}

    def fake_call_model(_prompt: str) -> str:
        calls["n"] += 1
        return "not-json"

    runner.call_model = fake_call_model  # type: ignore
    try:
        runner.run()
    except ValueError as e:
        assert "valid JSON" in str(e)
        assert calls["n"] >= 2  # initial + strict retry attempted
    else:
        raise AssertionError("Expected ValueError for invalid JSON response")

