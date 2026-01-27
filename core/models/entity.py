"""
Entity model for CtxOS.

Represents security entities such as domains, IPs, hosts, services, etc.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
from datetime import datetime


class EntityType(Enum):
    """Enumeration of entity types."""
    DOMAIN = "domain"
    IP_ADDRESS = "ip_address"
    HOST = "host"
    SERVICE = "service"
    PERSON = "person"
    EMAIL = "email"
    URL = "url"
    CERTIFICATE = "certificate"
    ACCOUNT = "account"
    CREDENTIAL = "credential"
    FILE = "file"
    PROCESS = "process"
    REGISTRY = "registry"
    OTHER = "other"


class EntitySeverity(Enum):
    """Enumeration of entity severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class EntityStatus(Enum):
    """Enumeration of entity status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"
    ARCHIVED = "archived"


@dataclass
class Entity:
    """
    Represents a security entity.
    
    Attributes:
        id: Unique identifier (auto-generated UUID)
        name: Entity name/value
        entity_type: Type of entity
        source: Source collector/system
        properties: Custom properties
        severity: Severity level
        status: Entity status
        confidence: Confidence score (0-1)
        discovered_at: Discovery timestamp
        last_seen_at: Last seen timestamp
        related_entities: IDs of related entities
        tags: Classification tags
        description: Human-readable description
    """
    
    name: str
    entity_type: EntityType
    source: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    properties: Dict[str, Any] = field(default_factory=dict)
    severity: EntitySeverity = EntitySeverity.INFO
    status: EntityStatus = EntityStatus.ACTIVE
    confidence: float = 0.5
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    last_seen_at: Optional[datetime] = None
    related_entities: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate entity after initialization."""
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        if self.last_seen_at is None:
            self.last_seen_at = self.discovered_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        data = asdict(self)
        data["entity_type"] = self.entity_type.value
        data["severity"] = self.severity.value
        data["status"] = self.status.value
        data["discovered_at"] = self.discovered_at.isoformat()
        data["last_seen_at"] = self.last_seen_at.isoformat() if self.last_seen_at else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entity":
        """Create entity from dictionary."""
        data = data.copy()
        
        # Convert string enums back to enum types
        if isinstance(data.get("entity_type"), str):
            data["entity_type"] = EntityType(data["entity_type"])
        if isinstance(data.get("severity"), str):
            data["severity"] = EntitySeverity(data["severity"])
        if isinstance(data.get("status"), str):
            data["status"] = EntityStatus(data["status"])
        
        # Convert ISO format strings back to datetime
        if isinstance(data.get("discovered_at"), str):
            data["discovered_at"] = datetime.fromisoformat(data["discovered_at"])
        if isinstance(data.get("last_seen_at"), str):
            data["last_seen_at"] = datetime.fromisoformat(data["last_seen_at"])
        
        return cls(**data)
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the entity."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the entity."""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def set_property(self, key: str, value: Any) -> None:
        """Set a custom property."""
        self.properties[key] = value
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a custom property."""
        return self.properties.get(key, default)
    
    def add_related_entity(self, entity_id: str) -> None:
        """Add a related entity."""
        if entity_id not in self.related_entities:
            self.related_entities.append(entity_id)
    
    def __repr__(self) -> str:
        return f"Entity(name={self.name}, type={self.entity_type.value}, id={self.id})"
