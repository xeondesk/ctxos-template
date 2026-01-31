"""
Unit tests for normalizers module.
"""

import pytest
from normalizers.normalization_engine import (
    NormalizationEngine,
    NormalizationConfig,
)
from normalizers.mappers.field_mapper import FieldMapper
from normalizers.validators.schema_validator import SchemaValidator


class TestNormalizationEngine:
    """Tests for NormalizationEngine."""

    def test_normalize_entity_case(self):
        """Test entity normalization with case conversion."""
        engine = NormalizationEngine()
        entity = {"name": "TEST_ENTITY"}
        normalized = engine.normalize_entity(entity)
        assert normalized["name"] == "test_entity"

    def test_normalize_entity_whitespace(self):
        """Test entity normalization with whitespace trimming."""
        engine = NormalizationEngine()
        entity = {"name": "  entity  "}
        normalized = engine.normalize_entity(entity)
        assert normalized["name"] == "entity"

    def test_deduplicate_entities_by_hash(self):
        """Test entity deduplication using hash strategy."""
        engine = NormalizationEngine(NormalizationConfig(deduplication_strategy="hash"))
        entities = [
            {"name": "entity1", "type": "domain"},
            {"name": "entity1", "type": "domain"},
            {"name": "entity2", "type": "ip"},
        ]
        deduplicated = engine.deduplicate_entities(entities)
        assert len(deduplicated) == 2

    def test_deduplicate_entities_by_similarity(self):
        """Test entity deduplication using similarity strategy."""
        config = NormalizationConfig(
            deduplication_strategy="field-based",
            similarity_threshold=0.8,
        )
        engine = NormalizationEngine(config)
        entities = [
            {"name": "example.com", "type": "domain"},
            {"name": "example.com", "type": "domain"},
            {"name": "different.com", "type": "domain"},
        ]
        deduplicated = engine.deduplicate_entities(entities)
        assert len(deduplicated) == 2

    def test_deduplicate_signals_by_hash(self):
        """Test signal deduplication."""
        engine = NormalizationEngine(NormalizationConfig(deduplication_strategy="hash"))
        signals = [
            {"source": "collector1", "data": {"ip": "1.2.3.4"}},
            {"source": "collector1", "data": {"ip": "1.2.3.4"}},
            {"source": "collector2", "data": {"ip": "5.6.7.8"}},
        ]
        deduplicated = engine.deduplicate_signals(signals)
        assert len(deduplicated) == 2

    def test_merge_entities(self):
        """Test entity merging."""
        engine = NormalizationEngine()
        primary = {"name": "example.com", "type": "domain"}
        duplicate = {"name": "example.com", "register": "2024-01-01"}
        merged = engine.merge_entities(primary, duplicate)
        assert merged["name"] == "example.com"
        assert merged["type"] == "domain"
        assert merged["register"] == "2024-01-01"

    def test_normalize_signal(self):
        """Test signal normalization."""
        engine = NormalizationEngine()
        signal = {
            "source": "Collector",
            "data": {"KEY": "VALUE", "TEXT": "  spaces  "},
        }
        normalized = engine.normalize_signal(signal)
        assert normalized["data"]["key"] == "value"
        assert normalized["data"]["text"] == "spaces"


class TestFieldMapper:
    """Tests for FieldMapper."""

    def test_register_and_map_entity(self):
        """Test registering and using field mapping."""
        mapper = FieldMapper()
        field_map = {
            "domain_name": "name",
            "domain_type": "type",
        }
        mapper.register_mapping("dns_source", field_map)

        entity = {
            "domain_name": "example.com",
            "domain_type": "registered",
        }
        mapped = mapper.map_entity("dns_source", entity)

        assert mapped["name"] == "example.com"
        assert mapped["type"] == "registered"

    def test_field_transformer(self):
        """Test field value transformation."""
        mapper = FieldMapper()
        field_map = {"port_number": "port"}
        mapper.register_mapping("network_source", field_map)

        def port_transformer(value):
            return int(value)

        mapper.register_transformer("network_source", "port_number", port_transformer)

        signal = {"port_number": "443"}
        mapped = mapper.map_signal("network_source", signal)
        assert mapped["port"] == 443

    def test_map_batch(self):
        """Test batch mapping."""
        mapper = FieldMapper()
        field_map = {"src_ip": "source_ip", "dst_ip": "dest_ip"}
        mapper.register_mapping("firewall", field_map)

        items = [
            {"src_ip": "1.2.3.4", "dst_ip": "5.6.7.8"},
            {"src_ip": "9.10.11.12", "dst_ip": "13.14.15.16"},
        ]
        mapped = mapper.map_batch("firewall", items)

        assert len(mapped) == 2
        assert mapped[0]["source_ip"] == "1.2.3.4"
        assert mapped[1]["dest_ip"] == "13.14.15.16"

    def test_unmapped_fields_preserved(self):
        """Test that unmapped fields are preserved."""
        mapper = FieldMapper()
        field_map = {"field1": "mapped_field1"}
        mapper.register_mapping("source", field_map)

        entity = {"field1": "value1", "field2": "value2"}
        mapped = mapper.map_entity("source", entity)

        assert mapped["mapped_field1"] == "value1"
        assert mapped["field2"] == "value2"


class TestSchemaValidator:
    """Tests for SchemaValidator."""

    def test_register_and_validate_entity(self):
        """Test registering schema and validating entity."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "required": ["name", "type"],
            "properties": {
                "name": {"type": "string"},
                "type": {"type": "string"},
                "confidence": {"type": "number"},
            },
        }
        validator.register_schema("entity", schema)

        entity = {"name": "example.com", "type": "domain", "confidence": 0.95}
        is_valid, errors = validator.validate_entity(entity)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_entity_missing_required_field(self):
        """Test validation fails with missing required field."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "required": ["name", "type"],
            "properties": {
                "name": {"type": "string"},
                "type": {"type": "string"},
            },
        }
        validator.register_schema("entity", schema)

        entity = {"name": "example.com"}
        is_valid, errors = validator.validate_entity(entity)

        assert is_valid is False
        assert any("type" in error for error in errors)

    def test_validate_entity_wrong_type(self):
        """Test validation fails with wrong field type."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "required": ["name", "confidence"],
            "properties": {
                "name": {"type": "string"},
                "confidence": {"type": "number"},
            },
        }
        validator.register_schema("entity", schema)

        entity = {"name": "example.com", "confidence": "high"}
        is_valid, errors = validator.validate_entity(entity)

        assert is_valid is False
        assert any("confidence" in error for error in errors)

    def test_validate_batch(self):
        """Test batch validation."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "string"}},
        }
        validator.register_schema("signal", schema)

        signals = [
            {"id": "sig1"},
            {"id": "sig2"},
            {"id": "sig3"},
        ]
        results = validator.validate_batch(signals, "signal")

        assert len(results) == 3
        assert all(is_valid for is_valid, _ in results)

    def test_custom_validator(self):
        """Test custom validation function."""
        validator = SchemaValidator()

        def custom_domain_validator(entity):
            errors = []
            if "name" in entity and not entity["name"].endswith(".com"):
                errors.append("Domain must end with .com")
            return len(errors) == 0, errors

        validator.register_schema("domain", {})
        validator.register_custom_validator("domain", custom_domain_validator)

        entity_valid = {"name": "example.com"}
        is_valid, errors = validator.validate_entity(entity_valid, "domain")
        assert is_valid is True

        entity_invalid = {"name": "example.org"}
        is_valid, errors = validator.validate_entity(entity_invalid, "domain")
        assert is_valid is False
        assert any(".com" in error for error in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
