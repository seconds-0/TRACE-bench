"""
State representation and manipulation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from copy import deepcopy
from typing import Dict, Optional


@dataclass
class EntityState:
    """State for a single entity."""

    name: str
    resources: Dict[str, int] = field(default_factory=dict)

    def get_resource(self, resource_type: str) -> int:
        """Get count of specific resource."""
        return self.resources.get(resource_type, 0)

    def set_resource(self, resource_type: str, amount: int) -> None:
        """Set resource amount (non-negative)."""
        if amount < 0:
            raise ValueError(f"Resource amount cannot be negative: {amount}")
        self.resources[resource_type] = amount

    def modify_resource(self, resource_type: str, delta: int) -> None:
        """Modify resource by delta amount (no negatives)."""
        current = self.get_resource(resource_type)
        new_amount = current + delta
        if new_amount < 0:
            raise ValueError(
                f"Insufficient {resource_type}: have {current}, delta {delta} would make {new_amount}"
            )
        self.set_resource(resource_type, new_amount)


@dataclass
class GlobalState:
    """Complete system state."""

    entities: Dict[str, EntityState] = field(default_factory=dict)
    turn: int = 0

    def add_entity(self, name: str, initial_resources: Optional[Dict[str, int]] = None) -> None:
        """Add new entity to system."""
        entity = EntityState(name=name)
        if initial_resources:
            entity.resources = initial_resources.copy()
        self.entities[name] = entity

    def get_entity(self, name: str) -> Optional[EntityState]:
        """Get entity by name."""
        return self.entities.get(name)

    def calculate_totals(self) -> Dict[str, int]:
        """Calculate total resources across all entities."""
        totals: Dict[str, int] = {}
        for entity in self.entities.values():
            for resource, amount in entity.resources.items():
                totals[resource] = totals.get(resource, 0) + amount
        return totals

    def clone(self) -> "GlobalState":
        """Create deep copy of state."""
        return deepcopy(self)
