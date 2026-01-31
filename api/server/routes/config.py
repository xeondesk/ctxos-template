"""
Configuration API endpoints (/api/v1/config/*).
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json

from api.server.models.request import (
    ConfigUpdateRequest, RuleCreateRequest, AnalysisFilterRequest
)
from api.server.models.response import (
    ConfigResponse, StatusResponse, PaginatedResponse
)
from api.server.middleware.auth import verify_jwt_token, TokenData
from api.server.middleware.rbac import require_permission, Permission
from agents.audit_system.audit_logger import get_audit_logger

logger = logging.getLogger(__name__)

router = APIRouter()


# In-memory configuration store (replace with database in production)
_config_store: Dict[str, Any] = {
    "agents.timeout": 30,
    "agents.max_parallel": 5,
    "agents.retry_count": 3,
    "scoring.cache_ttl": 300,
    "scoring.batch_size": 100,
    "api.rate_limit": 1000,
    "api.cors_origins": ["*"],
    "logging.level": "INFO",
    "monitoring.enabled": True,
    "monitoring.metrics_retention_days": 30,
}

# In-memory rules store (replace with database in production)
_rules_store: Dict[str, Dict[str, Any]] = {}


class ConfigManager:
    """Configuration manager."""
    
    @staticmethod
    def get_config(key: Optional[str] = None) -> Any:
        """Get configuration value(s).
        
        Args:
            key: Configuration key (optional)
            
        Returns:
            Configuration value or all config
        """
        if key:
            return _config_store.get(key)
        return _config_store.copy()
    
    @staticmethod
    def update_config(key: str, value: Any, user: str) -> bool:
        """Update configuration value.
        
        Args:
            key: Configuration key
            value: New value
            user: User making the change
            
        Returns:
            True if updated, False if key not found
        """
        # Validate configuration key
        valid_keys = _config_store.keys()
        if key not in valid_keys:
            return False
        
        # Validate value type
        old_value = _config_store[key]
        if type(old_value) != type(value) and key not in ["api.cors_origins"]:
            # Allow type change for certain keys
            return False
        
        # Update configuration
        _config_store[key] = value
        
        # Log change
        logger.info(f"Config updated by {user}: {key} = {value} (was {old_value})")
        
        return True
    
    @staticmethod
    def validate_config(key: str, value: Any) -> bool:
        """Validate configuration value.
        
        Args:
            key: Configuration key
            value: Value to validate
            
        Returns:
            True if valid, False otherwise
        """
        validators = {
            "agents.timeout": lambda x: isinstance(x, (int, float)) and 1 <= x <= 300,
            "agents.max_parallel": lambda x: isinstance(x, int) and 1 <= x <= 20,
            "agents.retry_count": lambda x: isinstance(x, int) and 0 <= x <= 10,
            "scoring.cache_ttl": lambda x: isinstance(x, (int, float)) and 60 <= x <= 3600,
            "scoring.batch_size": lambda x: isinstance(x, int) and 1 <= x <= 1000,
            "api.rate_limit": lambda x: isinstance(x, int) and 1 <= x <= 10000,
            "logging.level": lambda x: x in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            "monitoring.enabled": lambda x: isinstance(x, bool),
            "monitoring.metrics_retention_days": lambda x: isinstance(x, int) and 1 <= x <= 365,
        }
        
        validator = validators.get(key)
        if validator:
            return validator(value)
        
        return True


class RuleManager:
    """Rule management for scoring engines."""
    
    @staticmethod
    def create_rule(
        rule_id: str,
        rule_type: str,
        name: str,
        description: Optional[str],
        condition: Dict[str, Any],
        action: Dict[str, Any],
        priority: int,
        enabled: bool,
        user: str,
    ) -> Dict[str, Any]:
        """Create a new rule.
        
        Args:
            rule_id: Rule ID
            rule_type: Rule type
            name: Rule name
            description: Rule description
            condition: Rule condition
            action: Rule action
            priority: Rule priority
            enabled: Whether rule is enabled
            user: User creating the rule
            
        Returns:
            Created rule
        """
        # Validate rule
        if not RuleManager.validate_rule(rule_type, condition, action):
            raise ValueError("Invalid rule configuration")
        
        rule = {
            "id": rule_id,
            "type": rule_type,
            "name": name,
            "description": description,
            "condition": condition,
            "action": action,
            "priority": priority,
            "enabled": enabled,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": user,
            "updated_at": datetime.utcnow().isoformat(),
            "updated_by": user,
            "version": 1,
        }
        
        _rules_store[rule_id] = rule
        logger.info(f"Rule created by {user}: {rule_id} ({rule_type})")
        
        return rule
    
    @staticmethod
    def update_rule(
        rule_id: str,
        updates: Dict[str, Any],
        user: str,
    ) -> Dict[str, Any]:
        """Update existing rule.
        
        Args:
            rule_id: Rule ID
            updates: Updates to apply
            user: User updating the rule
            
        Returns:
            Updated rule
        """
        if rule_id not in _rules_store:
            raise ValueError(f"Rule not found: {rule_id}")
        
        rule = _rules_store[rule_id].copy()
        
        # Apply updates
        for key, value in updates.items():
            if key in ["condition", "action"]:
                # Validate rule structure
                if not RuleManager.validate_rule(rule["type"], value, rule["action"] if key == "condition" else value):
                    raise ValueError(f"Invalid {key} configuration")
            rule[key] = value
        
        rule["updated_at"] = datetime.utcnow().isoformat()
        rule["updated_by"] = user
        rule["version"] = rule.get("version", 1) + 1
        
        _rules_store[rule_id] = rule
        logger.info(f"Rule updated by {user}: {rule_id}")
        
        return rule
    
    @staticmethod
    def delete_rule(rule_id: str, user: str) -> bool:
        """Delete a rule.
        
        Args:
            rule_id: Rule ID
            user: User deleting the rule
            
        Returns:
            True if deleted, False if not found
        """
        if rule_id in _rules_store:
            del _rules_store[rule_id]
            logger.info(f"Rule deleted by {user}: {rule_id}")
            return True
        return False
    
    @staticmethod
    def validate_rule(rule_type: str, condition: Dict[str, Any], action: Dict[str, Any]) -> bool:
        """Validate rule configuration.
        
        Args:
            rule_type: Rule type
            condition: Rule condition
            action: Rule action
            
        Returns:
            True if valid, False otherwise
        """
        # Basic validation
        if not isinstance(condition, dict) or not isinstance(action, dict):
            return False
        
        # Rule type specific validation
        if rule_type == "risk":
            required_condition_fields = ["entity_type"]
            required_action_fields = ["risk_multiplier", "recommendation"]
        elif rule_type == "exposure":
            required_condition_fields = ["entity_type"]
            required_action_fields = ["exposure_multiplier", "recommendation"]
        elif rule_type == "drift":
            required_condition_fields = ["entity_type", "field"]
            required_action_fields = ["drift_multiplier", "recommendation"]
        else:
            return False
        
        # Check required fields
        for field in required_condition_fields:
            if field not in condition:
                return False
        
        for field in required_action_fields:
            if field not in action:
                return False
        
        return True


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
    require_permission(Permission.READ, token_data)
    
    config = ConfigManager.get_config()
    
    # Add metadata
    return {
        "config": config,
        "metadata": {
            "total_keys": len(config),
            "last_updated": datetime.utcnow().isoformat(),
            "version": "1.0.0",
        }
    }


@router.get(
    "/config/{config_key}",
    response_model=Dict[str, Any],
    summary="Get configuration value",
    tags=["config"],
)
async def get_config_value(
    config_key: str,
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Get a specific configuration value.
    
    Args:
        config_key: Configuration key
        token_data: JWT token data
        
    Returns:
        Configuration value with metadata
    """
    require_permission(Permission.READ, token_data)
    
    value = ConfigManager.get_config(config_key)
    
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration key not found: {config_key}",
        )
    
    return {
        "key": config_key,
        "value": value,
        "metadata": {
            "type": type(value).__name__,
            "retrieved_at": datetime.utcnow().isoformat(),
        }
    }


@router.post(
    "/config/update",
    response_model=Dict[str, Any],
    summary="Update configuration",
    tags=["config"],
)
async def update_config(
    request: ConfigUpdateRequest,
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Update configuration value.
    
    Args:
        request: Configuration update request
        token_data: JWT token data
        
    Returns:
        Update result
    """
    require_permission(Permission.MANAGE_CONFIG, token_data)
    
    # Validate configuration
    if not ConfigManager.validate_config(request.config_key, request.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid configuration value for key: {request.config_key}",
        )
    
    # Update configuration
    if not ConfigManager.update_config(request.config_key, request.value, token_data.username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration key not found: {request.config_key}",
        )
    
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
            "description": request.description,
        },
    )
    
    return {
        "status": "success",
        "message": f"Configuration updated: {request.config_key}",
        "key": request.config_key,
        "old_value": ConfigManager.get_config(f"_{request.config_key}_old"),  # Would need to track old values
        "new_value": request.value,
        "updated_at": datetime.utcnow().isoformat(),
        "updated_by": token_data.username,
    }


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
        Rules dictionary with metadata
    """
    require_permission(Permission.READ, token_data)
    
    rules = _rules_store.copy()
    
    return {
        "rules": rules,
        "metadata": {
            "total_rules": len(rules),
            "enabled_rules": len([r for r in rules.values() if r["enabled"]]),
            "rule_types": list(set(r["type"] for r in rules.values())),
            "last_updated": datetime.utcnow().isoformat(),
        }
    }


@router.post(
    "/config/rules",
    response_model=Dict[str, Any],
    summary="Create scoring rule",
    tags=["config"],
)
async def create_rule(
    request: RuleCreateRequest,
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Create a new scoring rule.
    
    Args:
        request: Rule creation request
        token_data: JWT token data
        
    Returns:
        Created rule details
    """
    require_permission(Permission.MANAGE_RULES, token_data)
    
    try:
        rule = RuleManager.create_rule(
            rule_id=request.rule_id,
            rule_type=request.rule_type,
            name=request.name,
            description=request.description,
            condition=request.condition,
            action=request.action,
            priority=request.priority or 100,
            enabled=request.enabled if request.enabled is not None else True,
            user=token_data.username,
        )
        
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
                "rule_name": request.name,
            },
        )
        
        return {
            "status": "success",
            "message": f"Rule created: {request.rule_id}",
            "rule": rule,
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
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
    require_permission(Permission.READ, token_data)
    
    rule = _rules_store.get(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule not found: {rule_id}",
        )
    
    return {
        "rule": rule,
        "metadata": {
            "retrieved_at": datetime.utcnow().isoformat(),
        }
    }


@router.put(
    "/config/rules/{rule_id}",
    response_model=Dict[str, Any],
    summary="Update scoring rule",
    tags=["config"],
)
async def update_rule(
    rule_id: str,
    updates: Dict[str, Any],
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Update a scoring rule.
    
    Args:
        rule_id: Rule ID
        updates: Updates to apply
        token_data: JWT token data
        
    Returns:
        Updated rule details
    """
    require_permission(Permission.MANAGE_RULES, token_data)
    
    try:
        rule = RuleManager.update_rule(rule_id, updates, token_data.username)
        
        # Log audit event
        audit_logger = get_audit_logger()
        audit_logger.log_event(
            agent_name="RuleService",
            action="update_rule",
            status="completed",
            user=token_data.username,
            details={
                "rule_id": rule_id,
                "updates": list(updates.keys()),
            },
        )
        
        return {
            "status": "success",
            "message": f"Rule updated: {rule_id}",
            "rule": rule,
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/config/rules/{rule_id}",
    response_model=Dict[str, Any],
    summary="Delete scoring rule",
    tags=["config"],
)
async def delete_rule(
    rule_id: str,
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Delete a scoring rule.
    
    Args:
        rule_id: Rule ID
        token_data: JWT token data
        
    Returns:
        Deletion result
    """
    require_permission(Permission.MANAGE_RULES, token_data)
    
    if not RuleManager.delete_rule(rule_id, token_data.username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule not found: {rule_id}",
        )
    
    # Log audit event
    audit_logger = get_audit_logger()
    audit_logger.log_event(
        agent_name="RuleService",
        action="delete_rule",
        status="completed",
        user=token_data.username,
        details={"rule_id": rule_id},
    )
    
    return {
        "status": "success",
        "message": f"Rule deleted: {rule_id}",
        "deleted_at": datetime.utcnow().isoformat(),
        "deleted_by": token_data.username,
    }


@router.post(
    "/config/export",
    response_model=Dict[str, Any],
    summary="Export configuration",
    tags=["config"],
)
async def export_config(
    include_rules: bool = True,
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Export configuration and rules.
    
    Args:
        include_rules: Whether to include rules
        token_data: JWT token data
        
    Returns:
        Export data
    """
    require_permission(Permission.READ, token_data)
    
    export_data = {
        "config": ConfigManager.get_config(),
        "exported_at": datetime.utcnow().isoformat(),
        "exported_by": token_data.username,
        "version": "1.0.0",
    }
    
    if include_rules:
        export_data["rules"] = _rules_store.copy()
    
    return export_data


@router.post(
    "/config/import",
    response_model=Dict[str, Any],
    summary="Import configuration",
    tags=["config"],
)
async def import_config(
    import_data: Dict[str, Any],
    token_data: TokenData = Depends(verify_jwt_token),
    overwrite: bool = False,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """Import configuration and rules.
    
    Args:
        import_data: Import data
        overwrite: Whether to overwrite existing config
        background_tasks: FastAPI background tasks
        token_data: JWT token data
        
    Returns:
        Import result
    """
    require_permission(Permission.MANAGE_CONFIG, token_data)
    
    try:
        imported_config = 0
        imported_rules = 0
        errors = []
        
        # Import configuration
        if "config" in import_data:
            for key, value in import_data["config"].items():
                if overwrite or key not in _config_store:
                    if ConfigManager.validate_config(key, value):
                        ConfigManager.update_config(key, value, token_data.username)
                        imported_config += 1
                    else:
                        errors.append(f"Invalid config value for {key}")
                else:
                    errors.append(f"Config key {key} already exists (use overwrite=true)")
        
        # Import rules
        if "rules" in import_data:
            for rule_id, rule_data in import_data["rules"].items():
                if overwrite or rule_id not in _rules_store:
                    try:
                        RuleManager.create_rule(
                            rule_id=rule_id,
                            rule_type=rule_data["type"],
                            name=rule_data.get("name", rule_id),
                            description=rule_data.get("description"),
                            condition=rule_data["condition"],
                            action=rule_data["action"],
                            priority=rule_data.get("priority", 100),
                            enabled=rule_data.get("enabled", True),
                            user=token_data.username,
                        )
                        imported_rules += 1
                    except (ValueError, KeyError) as e:
                        errors.append(f"Invalid rule {rule_id}: {e}")
                else:
                    errors.append(f"Rule {rule_id} already exists (use overwrite=true)")
        
        # Log audit event
        audit_logger = get_audit_logger()
        audit_logger.log_event(
            agent_name="ConfigService",
            action="import_config",
            status="completed",
            user=token_data.username,
            details={
                "imported_config": imported_config,
                "imported_rules": imported_rules,
                "errors": len(errors),
                "overwrite": overwrite,
            },
        )
        
        return {
            "status": "success",
            "message": "Configuration imported",
            "imported_config": imported_config,
            "imported_rules": imported_rules,
            "errors": errors,
            "imported_at": datetime.utcnow().isoformat(),
            "imported_by": token_data.username,
        }
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Import failed: {str(e)}",
        )


@router.get(
    "/config/audit-logs",
    response_model=PaginatedResponse,
    summary="Get configuration audit logs",
    tags=["config"],
)
async def get_config_audit_logs(
    limit: int = 100,
    offset: int = 0,
    token_data: TokenData = Depends(verify_jwt_token),
) -> PaginatedResponse:
    """Get configuration-related audit logs.
    
    Args:
        limit: Number of logs to retrieve
        offset: Offset for pagination
        token_data: JWT token data
        
    Returns:
        Paginated audit logs
    """
    require_permission(Permission.VIEW_AUDIT_LOGS, token_data)
    
    audit_logger = get_audit_logger()
    
    # Filter for config-related events
    all_events = audit_logger.get_events(limit=limit + offset)
    config_events = [
        event for event in all_events
        if event.agent_name in ["ConfigService", "RuleService"]
    ]
    
    # Apply pagination
    paginated_events = config_events[offset:offset + limit]
    
    items = []
    for event in paginated_events:
        items.append({
            "timestamp": event.timestamp.isoformat(),
            "agent": event.agent_name,
            "action": event.action,
            "entity_id": event.entity_id,
            "status": event.status,
            "level": event.level.value,
            "duration_ms": event.duration_ms,
            "error": event.error,
            "user": event.user,
            "details": event.details,
        })
    
    return PaginatedResponse(
        items=items,
        total=len(config_events),
        limit=limit,
        offset=offset,
        has_next=offset + limit < len(config_events),
    )


@router.get(
    "/config/health",
    response_model=Dict[str, Any],
    summary="Get configuration service health",
    tags=["config"],
)
async def get_config_health(
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Get configuration service health status.
    
    Args:
        token_data: JWT token data
        
    Returns:
        Health status information
    """
    require_permission(Permission.READ, token_data)
    
    # Check configuration integrity
    config_health = {
        "total_keys": len(_config_store),
        "total_rules": len(_rules_store),
        "enabled_rules": len([r for r in _rules_store.values() if r["enabled"]]),
        "last_updated": datetime.utcnow().isoformat(),
    }
    
    # Validate configuration values
    validation_errors = []
    for key, value in _config_store.items():
        if not ConfigManager.validate_config(key, value):
            validation_errors.append(f"Invalid value for {key}")
    
    return {
        "service": "config",
        "status": "healthy" if not validation_errors else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "configuration": config_health,
        "validation_errors": validation_errors,
        "validation_count": len(validation_errors),
    }
