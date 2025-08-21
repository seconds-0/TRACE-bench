import pytest

from trace.models.anthropic import AnthropicModel
from trace.models.cohere import CohereModel


def test_anthropic_requires_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError):
        AnthropicModel()


def test_cohere_requires_key(monkeypatch):
    monkeypatch.delenv("COHERE_API_KEY", raising=False)
    with pytest.raises(ValueError):
        CohereModel()

