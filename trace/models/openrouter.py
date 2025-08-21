from __future__ import annotations

import os
import random
import time
from typing import Optional

import requests

from .base import ModelInterface


class OpenRouterModel(ModelInterface):
    def __init__(
        self,
        model_name: str = "openai/gpt-3.5-turbo",
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        top_p: float = 1.0,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.temperature = temperature
        self.top_p = top_p
        self.max_retries = max_retries
        self.timeout = timeout
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY required")

    @property
    def name(self) -> str:
        return self.model_name

    def generate(self, prompt: str, **kwargs) -> str:
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", self.temperature),
            "top_p": kwargs.get("top_p", self.top_p),
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "trace-benchmark/0.1 (+https://example.org)",
        }
        backoff = 1.0
        for attempt in range(self.max_retries):
            try:
                resp = requests.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                if resp.status_code == 429:
                    time.sleep(backoff + random.uniform(0, 0.2))
                    backoff *= 2
                    continue
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            except Exception:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(backoff)
                backoff *= 2
        raise RuntimeError("OpenRouter generate failed")

