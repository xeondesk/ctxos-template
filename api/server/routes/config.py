"""
Configuration API endpoints (/config/*).
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, List
from datetime import datetime

from api.server.models.request import ConfigUpdateRequest, RuleCreateRequest
from api.server.models.response import ConfigResponse, StatusResponse, AuditLogResponse
from api.server.middleware.auth import verify_jwt_token, TokenData
from api.server.middleware.rbac import require_permission, require_role
from agents.audit_system.audit_logger import get_audit_logger


router = APIRouter()


# In-memory configuration store
_config_store: Dict[str, Any] = {
    "agents.timeout": 30,
    "agents.max_parallel": 5,
    "scoring.cache_ttl": 300,
    "api.rate_limit": 1000,
}

# In-memory rules store
_rules_store: Dict[str, Dict[str, Any]] = {}


@router.get(
    "/config",
    response_model=Dict[str, Any],
    summary="Get all configuration",
    tags=["config"],
)
async def get_config(
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Get all configuration.
    
    Args:
        token_data: JWT token data
        
    Returns:
        Configuration dictionary
    """
    require_permission("read", token_data)
    return _config_store.copy()


@router.get(
    "/config/{config_key}",
    response_model=Any,
    summary="Get configuration value",
    tags=["config"],
)
async def get_config_value(
    config_key: str,
    token_data: TokenData = Depends(verify_jwt_token),
) -> Any:
    """Get a specific configuration value.
    
    Args:
        config_key: Configuration key
        token_data: JWT token data
        
    Returns:
        Configuration value
    """
    require_permission("read", token_data)
    
    if config_key not in _config_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration key not found: {config_key}",
        )
    
    return _config_store[config_key]


@router.post(
    "/config/update",
    response_model=StatusResponse,
    summary="Update configuration",
    tags=["config"],
)
async def update_config(
    request: ConfigUpdateRequest,
    token_data: TokenData = Depends(verify_jwt_token),
) -> StatusResponse:
    """Update configuration value.
    
    Args:
        request: Configuration update request
        token_data: JWT token data
        
    Returns:
        Status response
    """
    require_permission("manage_config", token_data)
    
    # Update config
    _config_store[request.config_key] = request.value
    
    # Log audit event
    audit_logger = get_audit_logger()
    audit_logger.log_event(
        agent_name="ConfigService",
        action="update_config",
        status="completed",
        level=None,
        user=token_data.username,
        details={
            "config_key": request.config_key,
            "value": request.value,
        },
    )
    
    return StatusResponse(
        status="success",
        message=f"Configuration updated: {request.config_key}",
    )


@router.get(
    "/config/rules",
    response_model=Dict[str, Any],
    summary="Get all scoring rules",
    tags=["config"],
)
async def get_rules(
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Get all scoring rules.
    
    Args:
        token_data: JWT token data
        
    Returns:
        Rules dictionary
    """
    require_permission("read", token_data)
    return _rules_store.copy()


@router.post(
    "/config/rules",
    response_model=StatusResponse,
    summary="Create scoring rule",
    tags=["config"],
)
async def create_rule(
    request: RuleCreateRequest,
    token_data: TokenData = Depends(verify_jwt_token),
) -> StatusResponse:
    """Create a new scoring rule.
    
    Args:
        request: Rule creation request
        token_data: JWT token data
        
    Returns:
        Status response
    """
    require_permission("manage_rules", token_data)
    
    # Store rule
    _rules_store[request.rule_id] = {
        "id": request.rule_id,
        "type": request.rule_type,
        "condition": request.condition,
        "action": request.action,
        "priority": request.priority or 100,
        "enabled": request.enabled if request.enabled is not None else True,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": token_data.username,
    }
    
    # Log audit event
    audit_logger = get_audit_logger()
    audit_logger.log_event(
        agent_name="RuleService",
        action="create_rule",
        status="completed",
        user=token_data.username,
        details={
            "rule_id": request.rule_id,
            "rule_type": request.rule_type,
        },
    )
    
    return StatusResponse(
        status="success",
        message=f"Rule created: {request.rule_id}",
    )


@router.get(
    "/config/rules/{rule_id}",
    response_model=Dict[str, Any],
    summary="Get scoring rule",
    tags=["config"],
)
async def get_rule(
    rule_id: str,
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Get a specific scoring rule.
    
    Args:
        rule_id: Rule ID
        token_data: JWT token data
        
    Returns:
        Rule details
    """
    require_permission("read", token_data)
    
    if rule_id not in _rules_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule not found: {rule_id}",
        )
    
    return _rules_store[rule_id]


@router.delete(
    "/config/rules/{rule_id}",
    response_model=StatusResponse,
    summary="Delete scoring rule",
    tags=["config"],
)
async def delete_rule(
    rule_id: str,
    token_data: TokenData = Depends(verify_jwt_token),
) -> StatusResponse:
    """Delete a scoring rule.
    
    Args:
        rule_id: Rule ID
        token_data: JWT token data
        
    Returns:
        Status response
    """
    require_permission("manage_rules", token_data)
    
    if rule_id not in _rules_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule not found: {rule_id}",
        )
    
    del _rules_store[rule_id]
    
    # Log audit event
    audit_logger = get_audit_logger()
    audit_logger.log_event(
        agent_name="RuleService",
        action="delete_rule",
        status="completed",
        user=token_data.username,
        details={"rule_id": rule_id},
    )
    
    return StatusResponse(
        status="success",
        message=f"Rule deleted: {rule_id}",
    )


@router.get(
    "/audit/logs",
    response_model=List[AuditLogResponse],
    summary="Get audit logs",
    tags=["config"],
)
async def get_audit_logs(
    agent_name: str = None,
    limit: int = 100,
    token_data: TokenData = Depends(verify_jwt_token),
) -> List[AuditLogResponse]:
    """Get audit logs.
    
    Args:
        agent_name: Filter by agent name
        limit: Number of logs to retrieve
        token_data: JWT token data
        
    Returns:
        List of audit logs
    """
    require_permission("view_audit_logs", token_data)
    
    audit_logger = get_audit_logger()
    events = audit_logger.get_events(agent_name=agent_name, limit=limit)
    
    return [
        AuditLogResponse(
            timestamp=event.timestamp,
            agent=event.agent_name,
            action=event.action,
            entity_id=event.entity_id,
            status=event.status,
            level=event.level.value,
            duration_ms=event.duration_ms,
            error=event.error,
            user=event.user,
        )
        for event in events
    ]


@router.get(
    "/audit/stats",
    response_model=Dict[str, Any],
    summary="Get audit statistics",
    tags=["config"],
)
async def get_audit_stats(
    agent_name: str = None,
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Get audit statistics.
    
    Args:
        agent_name: Filter by agent name
        token_data: JWT token data
        
    Returns:
        Audit statistics
    """
    require_permission("view_audit_logs", token_data)
    
    audit_logger = get_audit_logger()
    return audit_logger.get_stats(agent_name=agent_name)
