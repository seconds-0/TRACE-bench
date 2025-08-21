from __future__ import annotations

from abc import ABC, abstractmethod


class ModelInterface(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str: ...

