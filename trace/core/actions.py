"""
Action definitions and application.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .state import GlobalState


class AppliesToState(Protocol):
    def apply(self, state: GlobalState) -> GlobalState: ...  # noqa: E701


@dataclass
class Action:
    """Base action class."""

    turn: int
    description: str

    def apply(self, state: GlobalState) -> GlobalState:  # pragma: no cover - abstract
        raise NotImplementedError


@dataclass
class TransferAction(Action):
    """Transfer resources between entities."""

    from_entity: str
    to_entity: str
    resource_type: str
    amount: int

    def apply(self, state: GlobalState) -> GlobalState:
        new_state = state.clone()

        from_e = new_state.get_entity(self.from_entity)
        to_e = new_state.get_entity(self.to_entity)
        if not from_e or not to_e:
            raise ValueError("Entity not found")

        if self.amount < 0:
            raise ValueError("Transfer amount cannot be negative")

        from_e.modify_resource(self.resource_type, -self.amount)
        to_e.modify_resource(self.resource_type, self.amount)

        new_state.turn = self.turn
        return new_state

