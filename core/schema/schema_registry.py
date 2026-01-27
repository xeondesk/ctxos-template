"""
Schema versioning and management for CtxOS.

Handles versioning, compatibility, and schema evolution.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json


@dataclass
class SchemaVersion:
    """Represents a schema version."""
    
    version: str
    name: str
    description: str = ""
    schema: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.schema is None:
            self.schema = {}


class SchemaRegistry:
    """
    Registry for managing schema versions.
    
    Supports multiple schema versions and migrations between them.
    """
    
    def __init__(self):
        """Initialize schema registry."""
        self.schemas: Dict[str, SchemaVersion] = {}
        self.migrations: Dict[str, callable] = {}
        self._current_version = "1.0.0"
        self._register_default_schemas()
    
    def _register_default_schemas(self):
        """Register default schemas."""
        # Entity schema
        entity_schema = {
            "type": "object",
            "required": ["id", "name", "entity_type", "source"],
            "properties": {
                "id": {"type": "string", "description": "Unique identifier"},
                "name": {"type": "string", "description": "Entity name"},
                "entity_type": {"type": "string", "description": "Type of entity"},
                "source": {"type": "string", "description": "Source collector"},
                "properties": {"type": "object", "description": "Custom properties"},
                "severity": {"type": "string", "description": "Severity level"},
                "status": {"type": "string", "description": "Entity status"},
                "confidence": {"type": "number", "description": "Confidence score"},
                "discovered_at": {"type": "string", "description": "Discovery time"},
                "last_seen_at": {"type": "string", "description": "Last seen time"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "description": {"type": "string", "description": "Description"},
            },
        }
        
        self.register_schema(
            "entity",
            SchemaVersion(
                version="1.0.0",
                name="Entity Schema",
                description="Schema for security entities",
                schema=entity_schema,
            ),
        )
        
        # Signal schema
        signal_schema = {
            "type": "object",
            "required": ["id", "source", "signal_type", "data"],
            "properties": {
                "id": {"type": "string", "description": "Unique identifier"},
                "source": {"type": "string", "description": "Source collector"},
                "signal_type": {"type": "string", "description": "Type of signal"},
                "data": {"type": "object", "description": "Signal data"},
                "severity": {"type": "string", "description": "Severity level"},
                "confidence": {"type": "string", "description": "Confidence level"},
                "entity_id": {"type": "string", "description": "Related entity"},
                "timestamp": {"type": "string", "description": "Timestamp"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "metadata": {"type": "object", "description": "Metadata"},
            },
        }
        
        self.register_schema(
            "signal",
            SchemaVersion(
                version="1.0.0",
                name="Signal Schema",
                description="Schema for security signals",
                schema=signal_schema,
            ),
        )
        
        # Context schema
        context_schema = {
            "type": "object",
            "required": ["id", "name"],
            "properties": {
                "id": {"type": "string", "description": "Unique identifier"},
                "name": {"type": "string", "description": "Context name"},
                "description": {"type": "string", "description": "Description"},
                "entities": {"type": "array", "description": "Entities"},
                "signals": {"type": "array", "description": "Signals"},
                "metadata": {"type": "object", "description": "Metadata"},
                "created_at": {"type": "string", "description": "Creation time"},
                "updated_at": {"type": "string", "description": "Update time"},
            },
        }
        
        self.register_schema(
            "context",
            SchemaVersion(
                version="1.0.0",
                name="Context Schema",
                description="Schema for security context",
                schema=context_schema,
            ),
        )
    
    def register_schema(self, schema_name: str, schema_version: SchemaVersion) -> None:
        """Register a schema version."""
        key = f"{schema_name}:{schema_version.version}"
        self.schemas[key] = schema_version
    
    def get_schema(self, schema_name: str, version: Optional[str] = None) -> Optional[SchemaVersion]:
        """Get a schema by name and version."""
        if version is None:
            version = self._current_version
        
        key = f"{schema_name}:{version}"
        return self.schemas.get(key)
    
    def list_schema_versions(self, schema_name: str) -> List[str]:
        """List all versions of a schema."""
        versions = []
        for key in self.schemas.keys():
            name, version = key.split(":", 1)
            if name == schema_name:
                versions.append(version)
        return sorted(versions)
    
    def register_migration(self, from_version: str, to_version: str, migration_func: callable) -> None:
        """Register a migration function."""
        key = f"{from_version}->{to_version}"
        self.migrations[key] = migration_func
    
    def migrate(self, data: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
        """Migrate data from one version to another."""
        if from_version == to_version:
            return data
        
        key = f"{from_version}->{to_version}"
        if key not in self.migrations:
            raise ValueError(f"No migration found from {from_version} to {to_version}")
        
        return self.migrations[key](data)
    
    def validate(self, data: Dict[str, Any], schema_name: str, version: Optional[str] = None) -> bool:
        """Validate data against a schema."""
        schema_version = self.get_schema(schema_name, version)
        if schema_version is None:
            return False
        
        # Simple validation - check required fields
        schema = schema_version.schema
        if "required" in schema:
            for field in schema["required"]:
                if field not in data:
                    return False
        
        return True
    
    def set_current_version(self, version: str) -> None:
        """Set the current default version."""
        self._current_version = version


# Global schema registry instance
_registry = SchemaRegistry()


def get_registry() -> SchemaRegistry:
    """Get the global schema registry."""
    return _registry


def validate_schema(data: Dict[str, Any], schema_name: str, version: Optional[str] = None) -> bool:
    """Validate data against schema."""
    return _registry.validate(data, schema_name, version)


def get_schema(schema_name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get schema definition."""
    schema_version = _registry.get_schema(schema_name, version)
    return schema_version.schema if schema_version else None
