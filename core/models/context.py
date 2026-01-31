"""
Context model for CtxOS.

Represents the security context - a collection of entities and signals.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import uuid

from .entity import Entity
from .signal import Signal


@dataclass
class Context:
    """
    Represents security context.

    A Context is a collection of entities and signals that form a security
    picture for an organization, project, or scope of assessment.

    Attributes:
        id: Unique identifier
        name: Context name
        entities: List of entities
        signals: List of signals
        metadata: Context metadata
        created_at: Creation timestamp
        updated_at: Last update timestamp
        description: Context description
    """

    name: str
    entities: List[Entity] = field(default_factory=list)
    signals: List[Signal] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    description: Optional[str] = None

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the context."""
        self.entities.append(entity)
        self.updated_at = datetime.utcnow()

    def add_signal(self, signal: Signal) -> None:
        """Add a signal to the context."""
        self.signals.append(signal)
        self.updated_at = datetime.utcnow()

    def add_entities(self, entities: List[Entity]) -> None:
        """Add multiple entities to the context."""
        self.entities.extend(entities)
        self.updated_at = datetime.utcnow()

    def add_signals(self, signals: List[Signal]) -> None:
        """Add multiple signals to the context."""
        self.signals.extend(signals)
        self.updated_at = datetime.utcnow()

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        for entity in self.entities:
            if entity.id == entity_id:
                return entity
        return None

    def get_signal(self, signal_id: str) -> Optional[Signal]:
        """Get signal by ID."""
        for signal in self.signals:
            if signal.id == signal_id:
                return signal
        return None

    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Get entities by type."""
        return [e for e in self.entities if e.entity_type.value == entity_type]

    def get_signals_by_type(self, signal_type: str) -> List[Signal]:
        """Get signals by type."""
        return [s for s in self.signals if s.signal_type.value == signal_type]

    def get_signals_for_entity(self, entity_id: str) -> List[Signal]:
        """Get all signals related to an entity."""
        return [s for s in self.signals if s.entity_id == entity_id]

    def remove_entity(self, entity_id: str) -> bool:
        """Remove an entity from context."""
        for i, entity in enumerate(self.entities):
            if entity.id == entity_id:
                self.entities.pop(i)
                self.updated_at = datetime.utcnow()
                return True
        return False

    def remove_signal(self, signal_id: str) -> bool:
        """Remove a signal from context."""
        for i, signal in enumerate(self.signals):
            if signal.id == signal_id:
                self.signals.pop(i)
                self.updated_at = datetime.utcnow()
                return True
        return False

    def get_active_signals(self) -> List[Signal]:
        """Get all non-expired signals."""
        return [s for s in self.signals if not s.is_expired()]

    def entity_count(self) -> int:
        """Get count of entities."""
        return len(self.entities)

    def signal_count(self) -> int:
        """Get count of signals."""
        return len(self.signals)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "entities": [e.to_dict() for e in self.entities],
            "signals": [s.to_dict() for s in self.signals],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Context":
        """Create context from dictionary."""
        data = data.copy()

        # Convert timestamps
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        # Convert entities and signals
        entities = [Entity.from_dict(e) for e in data.pop("entities", [])]
        signals = [Signal.from_dict(s) for s in data.pop("signals", [])]

        context = cls(**data)
        context.add_entities(entities)
        context.add_signals(signals)

        return context

    def __repr__(self) -> str:
        return f"Context(name={self.name}, entities={len(self.entities)}, signals={len(self.signals)}, id={self.id})"
