"""
Unit tests for schema versioning and validation.
"""

import pytest
import json

from core.schema import (
    SchemaRegistry, SchemaVersion,
    get_registry, validate_schema, get_schema
)


class TestSchemaVersion:
    """Tests for SchemaVersion."""
    
    def test_schema_version_creation(self):
        """Test creating a schema version."""
        version = SchemaVersion(
            version="1.0.0",
            name="Initial Release",
            schema={"type": "object"}
        )
        
        assert version.version == "1.0.0"
        assert version.name == "Initial Release"


class TestSchemaRegistry:
    """Tests for SchemaRegistry."""
    
    def test_registry_creation(self):
        """Test creating a registry."""
        registry = SchemaRegistry()
        assert registry is not None
    
    def test_register_schema(self):
        """Test registering a schema."""
        registry = SchemaRegistry()
        
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }
        
        registry.register_schema("test", "1.0.0", schema)
        
        retrieved = registry.get_schema("test", "1.0.0")
        assert retrieved is not None
    
    def test_get_current_version(self):
        """Test getting current schema version."""
        registry = SchemaRegistry()
        
        schema1 = {
            "type": "object",
            "properties": {"name": {"type": "string"}}
        }
        schema2 = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        
        registry.register_schema("user", "1.0.0", schema1)
        registry.register_schema("user", "2.0.0", schema2)
        registry.set_current_version("user", "2.0.0")
        
        current = registry.get_schema("user")
        assert current is not None
    
    def test_list_schema_versions(self):
        """Test listing schema versions."""
        registry = SchemaRegistry()
        
        schema = {"type": "object"}
        registry.register_schema("test", "1.0.0", schema)
        registry.register_schema("test", "2.0.0", schema)
        
        versions = registry.list_schema_versions("test")
        assert len(versions) >= 2
    
    def test_validate_data(self):
        """Test data validation against schema."""
        registry = SchemaRegistry()
        
        schema = {
            "type": "object",
            "required": ["name", "source"],
            "properties": {
                "name": {"type": "string"},
                "source": {"type": "string"}
            }
        }
        
        registry.register_schema("entity", "1.0.0", schema)
        
        # Valid data
        valid_data = {"name": "example.com", "source": "dns"}
        assert registry.validate("entity", valid_data) is True
        
        # Invalid data (missing required field)
        invalid_data = {"name": "example.com"}
        assert registry.validate("entity", invalid_data) is False
    
    def test_migration(self):
        """Test migration registration and execution."""
        registry = SchemaRegistry()
        
        # Register migration function
        def migrate_1_0_to_2_0(data):
            data["version"] = "2.0.0"
            return data
        
        registry.register_migration("test", "1.0.0", "2.0.0", migrate_1_0_to_2_0)
        
        # Run migration
        old_data = {"name": "value"}
        new_data = registry.migrate("test", old_data, "1.0.0", "2.0.0")
        
        assert new_data.get("version") == "2.0.0"
        assert new_data.get("name") == "value"


class TestGlobalRegistry:
    """Tests for global registry functions."""
    
    def test_get_registry(self):
        """Test getting global registry."""
        registry = get_registry()
        assert registry is not None
    
    def test_validate_schema_function(self):
        """Test validate_schema function."""
        # Entity schema validation
        entity_data = {
            "name": "example.com",
            "entity_type": "domain",
            "source": "dns_collector"
        }
        
        assert validate_schema("entity", entity_data) is True
    
    def test_get_schema_function(self):
        """Test get_schema function."""
        schema = get_schema("entity")
        assert schema is not None
        assert "type" in schema
    
    def test_pre_registered_schemas(self):
        """Test that default schemas are registered."""
        registry = get_registry()
        
        # Check entity schema
        entity_schema = registry.get_schema("entity")
        assert entity_schema is not None
        
        # Check signal schema
        signal_schema = registry.get_schema("signal")
        assert signal_schema is not None
        
        # Check context schema
        context_schema = registry.get_schema("context")
        assert context_schema is not None


class TestSchemaIntegration:
    """Integration tests with core models."""
    
    def test_entity_with_schema(self):
        """Test entity validation with schema."""
        from core.models import Entity, EntityType
        
        entity = Entity(
            name="example.com",
            entity_type=EntityType.DOMAIN,
            source="dns"
        )
        
        entity_dict = entity.to_dict()
        assert validate_schema("entity", entity_dict) is True
    
    def test_signal_with_schema(self):
        """Test signal validation with schema."""
        from core.models import Signal, SignalType
        
        signal = Signal(
            source="collector",
            signal_type=SignalType.OPEN_PORT,
            data={}
        )
        
        signal_dict = signal.to_dict()
        assert validate_schema("signal", signal_dict) is True
    
    def test_context_with_schema(self):
        """Test context validation with schema."""
        from core.models import Context
        
        context = Context(name="Test")
        context_dict = context.to_dict()
        
        assert validate_schema("context", context_dict) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
