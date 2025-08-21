from __future__ import annotations

import os

from .base import ModelInterface


class CohereModel(ModelInterface):
    """Placeholder Cohere adapter. Requires COHERE_API_KEY."""

    def __init__(self, model_name: str = "command-r", api_key: str | None = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        if not self.api_key:
            raise ValueError("COHERE_API_KEY required")

    @property
    def name(self) -> str:
        return self.model_name

    def generate(self, prompt: str, **kwargs) -> str:
        # Not implemented yet; interface only.
        raise NotImplementedError("Cohere adapter not implemented for live calls yet")

