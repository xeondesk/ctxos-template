"""
Request models for API validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class EntityType(str, Enum):
    """Entity types."""
    HOST = "host"
    DOMAIN = "domain"
    IP = "ip"
    USER = "user"
    SERVICE = "service"


class ScoreRequestBody(BaseModel):
    """Request to score risk/exposure/drift."""
    entity_id: str = Field(..., description="Entity ID")
    entity_type: EntityType = Field(..., description="Entity type")
    signals: Optional[List[Dict[str, Any]]] = Field(
        None, description="Custom signals"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "entity_id": "host-001",
                "entity_type": "host",
                "signals": [
                    {
                        "name": "open_ports",
                        "value": [22, 80, 443],
                    }
                ],
            }
        }


class AgentRunRequest(BaseModel):
    """Request to run agent."""
    agent_name: str = Field(..., description="Agent name")
    entity_id: str = Field(..., description="Entity ID")
    entity_type: EntityType = Field(..., description="Entity type")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Agent-specific parameters"
    )
    timeout_seconds: Optional[float] = Field(
        30.0, description="Execution timeout"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "agent_name": "context_summarizer",
                "entity_id": "host-001",
                "entity_type": "host",
                "parameters": {"detail_level": "high"},
                "timeout_seconds": 30,
            }
        }


class PipelineRunRequest(BaseModel):
    """Request to run agent pipeline."""
    pipeline_name: str = Field(..., description="Pipeline name")
    entity_id: str = Field(..., description="Entity ID")
    entity_type: EntityType = Field(..., description="Entity type")
    parallel: Optional[bool] = Field(False, description="Run agents in parallel")
    timeout_seconds: Optional[float] = Field(
        60.0, description="Pipeline timeout"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "pipeline_name": "full_analysis",
                "entity_id": "host-001",
                "entity_type": "host",
                "parallel": True,
                "timeout_seconds": 60,
            }
        }


class ConfigUpdateRequest(BaseModel):
    """Request to update configuration."""
    config_key: str = Field(..., description="Configuration key")
    value: Any = Field(..., description="Configuration value")
    
    class Config:
        schema_extra = {
            "example": {
                "config_key": "agents.timeout",
                "value": 45,
            }
        }


class RuleCreateRequest(BaseModel):
    """Request to create scoring rule."""
    rule_id: str = Field(..., description="Rule ID")
    rule_type: str = Field(..., description="Rule type (risk/exposure/drift)")
    condition: Dict[str, Any] = Field(..., description="Rule condition")
    action: Dict[str, Any] = Field(..., description="Rule action")
    priority: Optional[int] = Field(100, description="Rule priority (0-100)")
    enabled: Optional[bool] = Field(True, description="Is rule enabled")
    
    class Config:
        schema_extra = {
            "example": {
                "rule_id": "rule-001",
                "rule_type": "risk",
                "condition": {
                    "entity_type": "host",
                    "min_open_ports": 5,
                },
                "action": {
                    "risk_level": "HIGH",
                },
                "priority": 80,
                "enabled": True,
            }
        }


class AnalysisFilterRequest(BaseModel):
    """Request to filter analysis results."""
    entity_type: Optional[EntityType] = Field(None, description="Filter by entity type")
    min_risk_score: Optional[float] = Field(None, description="Minimum risk score")
    max_risk_score: Optional[float] = Field(None, description="Maximum risk score")
    agents: Optional[List[str]] = Field(None, description="Filter by agents")
    limit: Optional[int] = Field(100, description="Result limit")
    offset: Optional[int] = Field(0, description="Result offset")
    
    class Config:
        schema_extra = {
            "example": {
                "entity_type": "host",
                "min_risk_score": 0.5,
                "max_risk_score": 1.0,
                "agents": ["gap_detector", "hypothesis_generator"],
                "limit": 50,
                "offset": 0,
            }
        }
