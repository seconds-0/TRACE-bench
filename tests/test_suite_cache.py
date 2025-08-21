import os
from trace.evaluation.suite import BenchmarkSuite
from trace.evaluation.executor import Evaluator


class CountingModel:
    def __init__(self):
        self.name = "counting-model"
        self.calls = 0

    def generate(self, prompt: str, **kwargs) -> str:
        self.calls += 1
        # Minimal valid final-state JSON (3 entities sum to 10)
        return (
            '{"entities": {"entity_0": {"tokens": 3}, "entity_1": {"tokens": 3}, "entity_2": {"tokens": 4}},'
            ' "totals": {"tokens": 10}}'
        )


class FailingIfCalledModel(CountingModel):
    def generate(self, prompt: str, **kwargs) -> str:
        raise AssertionError("generate should not be called when cache is enabled")


def test_cache_reduces_calls(tmp_path, monkeypatch):
    cache_dir = tmp_path / ".cache"
    model = CountingModel()
    suite = BenchmarkSuite(model)
    suite.evaluator = Evaluator(model, cache_enabled=True, cache_dir=str(cache_dir))
    _ = suite.run_suite("trivial", 2, mode="final", concurrency=1)
    assert model.calls == 2  # two scenarios

    # Second run with a model that would fail if called; should hit cache
    model2 = FailingIfCalledModel()
    suite2 = BenchmarkSuite(model2)
    suite2.evaluator = Evaluator(model2, cache_enabled=True, cache_dir=str(cache_dir))
    _ = suite2.run_suite("trivial", 2, mode="final", concurrency=1)
    assert model2.calls == 0

