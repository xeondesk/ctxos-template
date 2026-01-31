"""
Response models for API serialization.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class EntityResponse(BaseModel):
    """Entity information in response."""

    id: str
    entity_type: str
    name: Optional[str] = None
    description: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "host-001",
                "entity_type": "host",
                "name": "web-server-1",
            }
        }


class SignalResponse(BaseModel):
    """Signal in response."""

    name: str
    value: Any
    severity: Optional[str] = None
    timestamp: datetime

    class Config:
        schema_extra = {
            "example": {
                "name": "open_ports",
                "value": [22, 80, 443],
                "severity": "medium",
                "timestamp": "2024-01-01T12:00:00Z",
            }
        }


class ScoringResultResponse(BaseModel):
    """Scoring result response."""

    entity_id: str
    entity_type: str
    engine_name: str  # risk, exposure, drift
    score: float = Field(..., ge=0.0, le=1.0)
    severity: str
    factors: Dict[str, Any]
    signals: List[SignalResponse]
    timestamp: datetime

    class Config:
        schema_extra = {
            "example": {
                "entity_id": "host-001",
                "entity_type": "host",
                "engine_name": "risk",
                "score": 0.75,
                "severity": "HIGH",
                "factors": {
                    "open_ports": 0.3,
                    "outdated_services": 0.45,
                },
                "signals": [],
                "timestamp": "2024-01-01T12:00:00Z",
            }
        }


class AgentResultResponse(BaseModel):
    """Agent execution result."""

    agent_name: str
    success: bool
    output: Dict[str, Any]
    error: Optional[str] = None
    duration_ms: float
    timestamp: datetime

    class Config:
        schema_extra = {
            "example": {
                "agent_name": "context_summarizer",
                "success": True,
                "output": {
                    "summary": "Host has critical vulnerabilities",
                    "recommendations": ["Update services", "Close unused ports"],
                },
                "error": None,
                "duration_ms": 245.5,
                "timestamp": "2024-01-01T12:00:00Z",
            }
        }


class PipelineResultResponse(BaseModel):
    """Pipeline execution result."""

    pipeline_name: str
    entity_id: str
    results: Dict[str, AgentResultResponse]
    duration_ms: float
    timestamp: datetime
    success_count: int
    total_count: int

    class Config:
        schema_extra = {
            "example": {
                "pipeline_name": "full_analysis",
                "entity_id": "host-001",
                "results": {
                    "context_summarizer": {
                        "agent_name": "context_summarizer",
                        "success": True,
                        "output": {},
                        "error": None,
                        "duration_ms": 245.5,
                        "timestamp": "2024-01-01T12:00:00Z",
                    }
                },
                "duration_ms": 1023.4,
                "timestamp": "2024-01-01T12:00:00Z",
                "success_count": 2,
                "total_count": 2,
            }
        }


class AnalysisResultResponse(BaseModel):
    """Complete analysis result (all engines + agents)."""

    entity_id: str
    entity_type: str
    entity_info: EntityResponse
    scoring_results: List[ScoringResultResponse]
    agent_results: Dict[str, AgentResultResponse]
    aggregate_risk_score: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime

    class Config:
        schema_extra = {
            "example": {
                "entity_id": "host-001",
                "entity_type": "host",
                "entity_info": {
                    "id": "host-001",
                    "entity_type": "host",
                    "name": "web-server-1",
                },
                "scoring_results": [],
                "agent_results": {},
                "aggregate_risk_score": 0.72,
                "timestamp": "2024-01-01T12:00:00Z",
            }
        }


class StatusResponse(BaseModel):
    """Status response."""

    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Operation completed",
                "data": {},
            }
        }


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    status_code: int
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        schema_extra = {
            "example": {
                "error": "Invalid entity ID",
                "status_code": 400,
                "details": {"entity_id": "host-001"},
                "timestamp": "2024-01-01T12:00:00Z",
            }
        }


class ConfigResponse(BaseModel):
    """Configuration item response."""

    key: str
    value: Any
    description: Optional[str] = None
    updated_at: datetime

    class Config:
        schema_extra = {
            "example": {
                "key": "agents.timeout",
                "value": 30,
                "description": "Agent execution timeout in seconds",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        }


class AuditLogResponse(BaseModel):
    """Audit log entry response."""

    timestamp: datetime
    agent: str
    action: str
    entity_id: Optional[str] = None
    status: str
    level: str
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    user: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2024-01-01T12:00:00Z",
                "agent": "context_summarizer",
                "action": "analyze",
                "entity_id": "host-001",
                "status": "completed",
                "level": "INFO",
                "duration_ms": 245.5,
                "error": None,
                "user": "analyst-001",
            }
        }


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    items: List[Any]
    total: int
    limit: int
    offset: int
    has_next: bool

    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "limit": 50,
                "offset": 0,
                "has_next": True,
            }
        }
