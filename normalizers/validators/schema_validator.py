"""
Schema validator for validating entities and signals against JSON schemas.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path


class SchemaValidator:
    """
    Validates entities and signals against JSON schemas.
    
    Capabilities:
    - JSON schema validation
    - Custom validation rules
    - Error reporting
    """
    
    def __init__(self):
        """Initialize schema validator."""
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.custom_validators: Dict[str, callable] = {}
    
    def load_schema(self, name: str, schema_path: str) -> None:
        """
        Load a JSON schema from file.
        
        Args:
            name: Name of the schema
            schema_path: Path to schema JSON file
        """
        with open(schema_path, "r") as f:
            self.schemas[name] = json.load(f)
    
    def register_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """
        Register a schema directly.
        
        Args:
            name: Name of the schema
            schema: Schema dictionary
        """
        self.schemas[name] = schema
    
    def register_custom_validator(
        self, name: str, validator: callable
    ) -> None:
        """
        Register a custom validation function.
        
        Args:
            name: Name of the validator
            validator: Validation function that returns (is_valid, errors)
        """
        self.custom_validators[name] = validator
    
    def validate_entity(
        self, entity: Dict[str, Any], schema_name: str = "entity"
    ) -> tuple[bool, List[str]]:
        """
        Validate an entity against a schema.
        
        Args:
            entity: Entity to validate
            schema_name: Name of the schema to use
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        if schema_name not in self.schemas:
            errors.append(f"Schema '{schema_name}' not found")
            return False, errors
        
        schema = self.schemas[schema_name]
        
        # Validate required fields
        if "required" in schema:
            for field in schema["required"]:
                if field not in entity:
                    errors.append(f"Required field '{field}' missing")
        
        # Validate field types
        if "properties" in schema:
            for field, field_schema in schema["properties"].items():
                if field in entity:
                    if not self._validate_field_type(
                        entity[field], field_schema, field
                    ):
                        errors.append(
                            f"Field '{field}' has invalid type. "
                            f"Expected {field_schema.get('type')}"
                        )
        
        # Run custom validators
        if schema_name in self.custom_validators:
            is_valid, custom_errors = self.custom_validators[schema_name](
                entity
            )
            if not is_valid:
                errors.extend(custom_errors)
        
        return len(errors) == 0, errors
    
    def validate_signal(
        self, signal: Dict[str, Any], schema_name: str = "signal"
    ) -> tuple[bool, List[str]]:
        """
        Validate a signal against a schema.
        
        Args:
            signal: Signal to validate
            schema_name: Name of the schema to use
            
        Returns:
            Tuple of (is_valid, errors)
        """
        return self.validate_entity(signal, schema_name)
    
    def validate_batch(
        self, items: List[Dict[str, Any]], schema_name: str = "entity"
    ) -> List[tuple[bool, List[str]]]:
        """
        Validate a batch of items.
        
        Args:
            items: List of items to validate
            schema_name: Name of the schema to use
            
        Returns:
            List of validation results
        """
        return [self.validate_entity(item, schema_name) for item in items]
    
    def _validate_field_type(
        self, value: Any, field_schema: Dict[str, Any], field_name: str
    ) -> bool:
        """Validate a field value against its schema type."""
        expected_type = field_schema.get("type")
        
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "number":
            return isinstance(value, (int, float))
        elif expected_type == "integer":
            return isinstance(value, int)
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        elif expected_type == "null":
            return value is None
        else:
            return True
    
    def get_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a registered schema."""
        return self.schemas.get(name)
    
    def list_schemas(self) -> List[str]:
        """List all registered schemas."""
        return list(self.schemas.keys())
