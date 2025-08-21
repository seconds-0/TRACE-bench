from __future__ import annotations

import os

from .base import ModelInterface


class AnthropicModel(ModelInterface):
    """Placeholder Anthropic adapter. Requires ANTHROPIC_API_KEY."""

    def __init__(self, model_name: str = "claude-3-haiku-20240307", api_key: str | None = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required")

    @property
    def name(self) -> str:
        return self.model_name

    def generate(self, prompt: str, **kwargs) -> str:
        # For now, we do not implement a live call here.
        # This adapter satisfies the interface and enforces key presence.
        raise NotImplementedError("Anthropic adapter not implemented for live calls yet")

