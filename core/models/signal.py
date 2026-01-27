"""
Signal model for CtxOS.

Represents security signals/evidence collected from various sources.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
from datetime import datetime


class SignalType(Enum):
    """Enumeration of signal types."""
    DOMAIN_REGISTRATION = "domain_registration"
    DNS_RECORD = "dns_record"
    IP_WHOIS = "ip_whois"
    CERTIFICATE = "certificate"
    HTTP_HEADER = "http_header"
    OPEN_PORT = "open_port"
    VULNERABILITY = "vulnerability"
    MALWARE = "malware"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    CONFIGURATION = "configuration"
    CREDENTIAL_EXPOSURE = "credential_exposure"
    DATA_BREACH = "data_breach"
    OTHER = "other"


class SignalSeverity(Enum):
    """Enumeration of signal severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SignalConfidence(Enum):
    """Enumeration of signal confidence levels."""
    VERIFIED = "verified"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNVERIFIED = "unverified"


@dataclass
class Signal:
    """
    Represents a security signal.
    
    Attributes:
        id: Unique identifier (auto-generated UUID)
        source: Source collector/system that produced the signal
        signal_type: Type of signal
        data: Signal data payload
        severity: Severity level
        confidence: Confidence level
        entity_id: ID of related entity (optional)
        timestamp: When signal was collected
        expiry: When signal expires (optional)
        tags: Classification tags
        metadata: Additional metadata
        raw_data: Original raw data from source
        description: Human-readable description
    """
    
    source: str
    signal_type: SignalType
    data: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    severity: SignalSeverity = SignalSeverity.INFO
    confidence: SignalConfidence = SignalConfidence.MEDIUM
    entity_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    expiry: Optional[datetime] = None
    tags: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_data: Optional[str] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary."""
        signal_dict = asdict(self)
        signal_dict["signal_type"] = self.signal_type.value
        signal_dict["severity"] = self.severity.value
        signal_dict["confidence"] = self.confidence.value
        signal_dict["timestamp"] = self.timestamp.isoformat()
        signal_dict["expiry"] = self.expiry.isoformat() if self.expiry else None
        return signal_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Signal":
        """Create signal from dictionary."""
        data = data.copy()
        
        # Convert string enums back to enum types
        if isinstance(data.get("signal_type"), str):
            data["signal_type"] = SignalType(data["signal_type"])
        if isinstance(data.get("severity"), str):
            data["severity"] = SignalSeverity(data["severity"])
        if isinstance(data.get("confidence"), str):
            data["confidence"] = SignalConfidence(data["confidence"])
        
        # Convert ISO format strings back to datetime
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if isinstance(data.get("expiry"), str):
            data["expiry"] = datetime.fromisoformat(data["expiry"])
        
        return cls(**data)
    
    def is_expired(self) -> bool:
        """Check if signal has expired."""
        if self.expiry is None:
            return False
        return datetime.utcnow() > self.expiry
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the signal."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata field."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata field."""
        return self.metadata.get(key, default)
    
    def __repr__(self) -> str:
        return f"Signal(type={self.signal_type.value}, source={self.source}, id={self.id})"
