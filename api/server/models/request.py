"""
Request models for API validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from datetime import datetime


class EntityType(str, Enum):
    """Entity types."""
    HOST = "host"
    DOMAIN = "domain"
    IP = "ip"
    USER = "user"
    SERVICE = "service"
    APPLICATION = "application"
    NETWORK = "network"
    DATABASE = "database"


class SeverityLevel(str, Enum):
    """Severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SignalType(str, Enum):
    """Signal types."""
    VULNERABILITY = "vulnerability"
    PORT = "port"
    SERVICE = "service"
    DNS = "dns"
    SSL_CERTIFICATE = "ssl_certificate"
    CONFIGURATION = "configuration"
    ACTIVITY = "activity"
    AUTHENTICATION = "authentication"
    DEPENDENCY = "dependency"
    SUBDOMAIN = "subdomain"
    WHOIS = "whois"


class SignalInput(BaseModel):
    """Signal input model."""
    id: str = Field(..., description="Signal ID")
    source: str = Field(..., description="Signal source")
    signal_type: SignalType = Field(..., description="Signal type")
    severity: SeverityLevel = Field(..., description="Signal severity")
    description: Optional[str] = Field(None, description="Signal description")
    timestamp: Optional[datetime] = Field(None, description="Signal timestamp")
    entity_id: Optional[str] = Field(None, description="Entity ID")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Signal properties")
    
    @validator('timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.utcnow()


class EntityInput(BaseModel):
    """Entity input model."""
    id: str = Field(..., description="Entity ID")
    entity_type: EntityType = Field(..., description="Entity type")
    name: Optional[str] = Field(None, description="Entity name")
    description: Optional[str] = Field(None, description="Entity description")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Entity properties")


class ContextInput(BaseModel):
    """Context input model."""
    entity: EntityInput = Field(..., description="Entity information")
    signals: Optional[List[SignalInput]] = Field(default_factory=list, description="Signals")
    
    class Config:
        schema_extra = {
            "example": {
                "entity": {
                    "id": "host-001",
                    "entity_type": "host",
                    "name": "web-server-01",
                    "properties": {"environment": "production"}
                },
                "signals": [
                    {
                        "id": "vuln-001",
                        "source": "nessus",
                        "signal_type": "vulnerability",
                        "severity": "critical",
                        "description": "CVE-2023-1234"
                    }
                ]
            }
        }


class ScoreRequestBody(BaseModel):
    """Request to score risk/exposure/drift."""
    context: ContextInput = Field(..., description="Entity context and signals")
    engines: Optional[List[str]] = Field(
        default=["risk", "exposure", "drift"],
        description="Engines to run (default: all)"
    )
    include_recommendations: Optional[bool] = Field(True, description="Include recommendations")
    
    @validator('engines')
    def validate_engines(cls, v):
        allowed_engines = {"risk", "exposure", "drift"}
        if v:
            invalid = set(v) - allowed_engines
            if invalid:
                raise ValueError(f"Invalid engines: {invalid}. Allowed: {allowed_engines}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "context": {
                    "entity": {
                        "id": "host-001",
                        "entity_type": "host",
                        "name": "web-server-01"
                    },
                    "signals": [
                        {
                            "id": "port-001",
                            "source": "nmap",
                            "signal_type": "port",
                            "severity": "high",
                            "description": "Open port 443"
                        }
                    ]
                },
                "engines": ["risk", "exposure"],
                "include_recommendations": True
            }
        }


class BatchScoreRequest(BaseModel):
    """Request to score multiple entities."""
    contexts: List[ContextInput] = Field(..., description="Entity contexts", min_items=1, max_items=100)
    engines: Optional[List[str]] = Field(
        default=["risk", "exposure", "drift"],
        description="Engines to run"
    )
    parallel: Optional[bool] = Field(True, description="Process in parallel")
    
    class Config:
        schema_extra = {
            "example": {
                "contexts": [
                    {
                        "entity": {"id": "host-001", "entity_type": "host"},
                        "signals": []
                    },
                    {
                        "entity": {"id": "host-002", "entity_type": "host"},
                        "signals": []
                    }
                ],
                "engines": ["risk"],
                "parallel": True
            }
        }


class AgentRunRequest(BaseModel):
    """Request to run agent."""
    agent_name: str = Field(..., description="Agent name")
    context: ContextInput = Field(..., description="Entity context")
    scoring_result: Optional[Dict[str, Any]] = Field(None, description="Previous scoring result")
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Agent-specific parameters"
    )
    timeout_seconds: Optional[float] = Field(30.0, description="Execution timeout", ge=1.0, le=300.0)
    
    class Config:
        schema_extra = {
            "example": {
                "agent_name": "context_summarizer",
                "context": {
                    "entity": {
                        "id": "host-001",
                        "entity_type": "host",
                        "name": "web-server-01"
                    },
                    "signals": []
                },
                "scoring_result": {
                    "score": 75.0,
                    "severity": "high",
                    "metrics": {"vulnerability": 30, "exposure": 25}
                },
                "parameters": {"detail_level": "high"},
                "timeout_seconds": 30
            }
        }


class PipelineRunRequest(BaseModel):
    """Request to run agent pipeline."""
    pipeline_name: Optional[str] = Field(None, description="Pipeline name (if pre-configured)")
    agents: Optional[List[str]] = Field(None, description="Agents to run (if custom pipeline)")
    context: ContextInput = Field(..., description="Entity context")
    scoring_result: Optional[Dict[str, Any]] = Field(None, description="Previous scoring result")
    parallel: Optional[bool] = Field(False, description="Run agents in parallel")
    timeout_seconds: Optional[float] = Field(60.0, description="Pipeline timeout", ge=1.0, le=600.0)
    
    @validator('agents')
    def validate_agents(cls, v, values):
        if v is None and values.get('pipeline_name') is None:
            raise ValueError("Either pipeline_name or agents must be provided")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "pipeline_name": "security_analysis",
                "context": {
                    "entity": {"id": "host-001", "entity_type": "host"},
                    "signals": []
                },
                "parallel": True,
                "timeout_seconds": 60
            }
        }


class ConfigUpdateRequest(BaseModel):
    """Request to update configuration."""
    config_key: str = Field(..., description="Configuration key")
    value: Any = Field(..., description="Configuration value")
    description: Optional[str] = Field(None, description="Configuration description")
    
    class Config:
        schema_extra = {
            "example": {
                "config_key": "agents.timeout",
                "value": 45,
                "description": "Agent execution timeout in seconds"
            }
        }


class RuleCreateRequest(BaseModel):
    """Request to create scoring rule."""
    rule_id: str = Field(..., description="Rule ID")
    rule_type: str = Field(..., description="Rule type (risk/exposure/drift)")
    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    condition: Dict[str, Any] = Field(..., description="Rule condition")
    action: Dict[str, Any] = Field(..., description="Rule action")
    priority: Optional[int] = Field(100, description="Rule priority (0-100)", ge=0, le=100)
    enabled: Optional[bool] = Field(True, description="Is rule enabled")
    
    @validator('rule_type')
    def validate_rule_type(cls, v):
        allowed_types = {"risk", "exposure", "drift"}
        if v not in allowed_types:
            raise ValueError(f"Invalid rule type: {v}. Allowed: {allowed_types}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "rule_id": "rule-001",
                "rule_type": "risk",
                "name": "High Open Ports Risk",
                "description": "Flag hosts with many open ports",
                "condition": {
                    "entity_type": "host",
                    "min_open_ports": 10,
                    "severity_threshold": "medium"
                },
                "action": {
                    "risk_multiplier": 1.5,
                    "recommendation": "Review open ports and close unnecessary ones"
                },
                "priority": 80,
                "enabled": True
            }
        }


class AnalysisFilterRequest(BaseModel):
    """Request to filter analysis results."""
    entity_type: Optional[EntityType] = Field(None, description="Filter by entity type")
    min_score: Optional[float] = Field(None, description="Minimum score", ge=0.0, le=100.0)
    max_score: Optional[float] = Field(None, description="Maximum score", ge=0.0, le=100.0)
    severity: Optional[SeverityLevel] = Field(None, description="Filter by severity")
    agents: Optional[List[str]] = Field(None, description="Filter by agents")
    engines: Optional[List[str]] = Field(None, description="Filter by engines")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    limit: Optional[int] = Field(100, description="Result limit", ge=1, le=1000)
    offset: Optional[int] = Field(0, description="Result offset", ge=0)
    sort_by: Optional[str] = Field("timestamp", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc/desc)")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in {"asc", "desc"}:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "entity_type": "host",
                "min_score": 50.0,
                "max_score": 100.0,
                "severity": "high",
                "agents": ["gap_detector", "hypothesis_generator"],
                "engines": ["risk", "exposure"],
                "date_from": "2024-01-01T00:00:00Z",
                "date_to": "2024-01-31T23:59:59Z",
                "limit": 50,
                "offset": 0,
                "sort_by": "timestamp",
                "sort_order": "desc"
            }
        }


class HistoricalQueryRequest(BaseModel):
    """Request for historical scoring data."""
    entity_id: str = Field(..., description="Entity ID")
    date_from: Optional[datetime] = Field(None, description="Start date")
    date_to: Optional[datetime] = Field(None, description="End date")
    engines: Optional[List[str]] = Field(
        default=["risk", "exposure", "drift"],
        description="Engines to query"
    )
    granularity: Optional[str] = Field("daily", description="Time granularity (hourly/daily/weekly)")
    limit: Optional[int] = Field(100, description="Result limit", ge=1, le=1000)
    
    @validator('granularity')
    def validate_granularity(cls, v):
        if v not in {"hourly", "daily", "weekly", "monthly"}:
            raise ValueError("granularity must be hourly, daily, weekly, or monthly")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "entity_id": "host-001",
                "date_from": "2024-01-01T00:00:00Z",
                "date_to": "2024-01-31T23:59:59Z",
                "engines": ["risk", "exposure"],
                "granularity": "daily",
                "limit": 31
            }
        }


class BulkAnalysisRequest(BaseModel):
    """Request for bulk entity analysis."""
    entity_ids: List[str] = Field(..., description="Entity IDs", min_items=1, max_items=500)
    entity_type: Optional[EntityType] = Field(None, description="Filter by entity type")
    engines: Optional[List[str]] = Field(
        default=["risk", "exposure", "drift"],
        description="Engines to run"
    )
    agents: Optional[List[str]] = Field(
        default=["context_summarizer", "gap_detector"],
        description="Agents to run"
    )
    parallel: Optional[bool] = Field(True, description="Process in parallel")
    timeout_per_entity: Optional[float] = Field(30.0, description="Timeout per entity", ge=1.0, le=300.0)
    
    class Config:
        schema_extra = {
            "example": {
                "entity_ids": ["host-001", "host-002", "host-003"],
                "entity_type": "host",
                "engines": ["risk"],
                "agents": ["context_summarizer"],
                "parallel": True,
                "timeout_per_entity": 30.0
            }
        }
