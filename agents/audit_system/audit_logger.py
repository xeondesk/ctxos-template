"""
Audit Logger - Track all agent activities for compliance.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json
import logging


class AuditLevel(Enum):
    """Audit event severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class AuditEvent:
    """Single audit event."""
    timestamp: datetime
    agent_name: str
    action: str
    entity_id: Optional[str]
    status: str  # "started", "completed", "failed"
    level: AuditLevel
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    user: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "agent": self.agent_name,
            "action": self.action,
            "entity_id": self.entity_id,
            "status": self.status,
            "level": self.level.value,
            "details": self.details,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "user": self.user,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class AuditLogger:
    """Logger for agent audit trail."""
    
    def __init__(self, name: str = "CtxOS.Agents"):
        """Initialize audit logger."""
        self.logger = logging.getLogger(name)
        self.events: List[AuditEvent] = []
        self.max_events = 10000  # In-memory limit
    
    def log_event(
        self,
        agent_name: str,
        action: str,
        status: str,
        entity_id: Optional[str] = None,
        level: AuditLevel = AuditLevel.INFO,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None,
        user: Optional[str] = None,
    ) -> AuditEvent:
        """Log an audit event."""
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            agent_name=agent_name,
            action=action,
            entity_id=entity_id,
            status=status,
            level=level,
            details=details or {},
            error=error,
            duration_ms=duration_ms,
            user=user,
        )
        
        self.events.append(event)
        
        # Maintain max size
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
        
        # Log to standard logger
        log_func = {
            AuditLevel.DEBUG: self.logger.debug,
            AuditLevel.INFO: self.logger.info,
            AuditLevel.WARNING: self.logger.warning,
            AuditLevel.ERROR: self.logger.error,
            AuditLevel.CRITICAL: self.logger.critical,
        }[level]
        
        log_func(f"[{agent_name}] {action}: {status}")
        
        return event
    
    def get_events(
        self,
        agent_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Get audit events."""
        events = self.events
        
        if agent_name:
            events = [e for e in events if e.agent_name == agent_name]
        
        return events[-limit:]
    
    def clear_events(self) -> None:
        """Clear all events."""
        self.events = []
    
    def get_stats(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get audit statistics."""
        events = self.events
        if agent_name:
            events = [e for e in events if e.agent_name == agent_name]
        
        if not events:
            return {
                "total_events": 0,
                "agents": [],
                "statuses": {},
                "levels": {},
            }
        
        agents = list(set(e.agent_name for e in events))
        statuses = {}
        levels = {}
        
        for event in events:
            statuses[event.status] = statuses.get(event.status, 0) + 1
            levels[event.level.value] = levels.get(event.level.value, 0) + 1
        
        total_duration = sum(e.duration_ms or 0 for e in events if e.duration_ms)
        avg_duration = total_duration / len(events) if events else 0
        
        return {
            "total_events": len(events),
            "agents": agents,
            "statuses": statuses,
            "levels": levels,
            "total_duration_ms": total_duration,
            "avg_duration_ms": avg_duration,
        }


# Global audit logger instance
_audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Get global audit logger."""
    return _audit_logger
