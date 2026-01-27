"""
Integration tests for the normalizers module.
"""

import pytest
from normalizers.normalization_engine import (
    NormalizationEngine,
    NormalizationConfig,
)
from normalizers.mappers.field_mapper import FieldMapper
from normalizers.validators.schema_validator import SchemaValidator
from normalizers.rules.normalization_rules import (
    FieldRemovalRule,
    FieldRenameRule,
    DefaultValueRule,
    RuleEngine,
)


class TestNormalizationWorkflow:
    """Test complete normalization workflow."""
    
    def test_end_to_end_entity_normalization(self):
        """Test complete entity normalization pipeline."""
        # Setup
        engine = NormalizationEngine(
            NormalizationConfig(deduplication_strategy="hash")
        )
        mapper = FieldMapper()
        validator = SchemaValidator()
        rule_engine = RuleEngine()
        
        # Register field mapping
        mapper.register_mapping(
            "dns_source",
            {
                "domain_name": "name",
                "domain_register_date": "registered_date",
            },
        )
        
        # Register schema
        schema = {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        }
        validator.register_schema("entity", schema)
        
        # Register rules
        rule_engine.register_rule(
            DefaultValueRule({"status": "active", "confidence": 0.0})
        )
        
        # Input data
        raw_entities = [
            {
                "domain_name": "EXAMPLE.COM",
                "domain_register_date": "2024-01-01",
            },
            {
                "domain_name": "example.com",
                "domain_register_date": "2024-01-01",
            },
            {
                "domain_name": "DIFFERENT.ORG",
                "domain_register_date": "2024-06-01",
            },
        ]
        
        # 1. Map fields
        mapped_entities = [
            mapper.map_entity("dns_source", entity) for entity in raw_entities
        ]
        
        # 2. Normalize
        normalized_entities = [
            engine.normalize_entity(entity) for entity in mapped_entities
        ]
        
        # 3. Apply rules
        rule_applied_entities = [
            rule_engine.apply_rules(entity) for entity in normalized_entities
        ]
        
        # 4. Deduplicate
        deduplicated = engine.deduplicate_entities(rule_applied_entities)
        
        # 5. Validate
        validation_results = validator.validate_batch(deduplicated)
        
        # Assertions
        assert len(deduplicated) == 2  # Duplicates removed
        assert all(is_valid for is_valid, _ in validation_results)
        assert all("status" in entity for entity in deduplicated)
        assert deduplicated[0]["name"] == "example.com"
    
    def test_signal_normalization_pipeline(self):
        """Test signal normalization pipeline."""
        engine = NormalizationEngine()
        mapper = FieldMapper()
        rule_engine = RuleEngine()
        
        # Register transformer
        def parse_port(value):
            return int(value) if isinstance(value, str) else value
        
        mapper.register_mapping(
            "firewall",
            {
                "src_address": "source_ip",
                "dst_address": "dest_ip",
                "port_num": "port",
            },
        )
        mapper.register_transformer("firewall", "port_num", parse_port)
        
        # Register field removal rule
        rule_engine.register_rule(FieldRemovalRule(["_internal"]))
        
        raw_signals = [
            {
                "src_address": "  1.2.3.4  ",
                "dst_address": "5.6.7.8",
                "port_num": "443",
                "_internal": "debug_info",
            },
            {
                "src_address": "1.2.3.4",
                "dst_address": "5.6.7.8",
                "port_num": "443",
                "_internal": "debug_info",
            },
        ]
        
        # Process pipeline
        mapped_signals = [
            mapper.map_signal("firewall", signal) for signal in raw_signals
        ]
        normalized_signals = [
            engine.normalize_signal(signal) for signal in mapped_signals
        ]
        processed_signals = [
            rule_engine.apply_rules(signal) for signal in normalized_signals
        ]
        deduplicated = engine.deduplicate_signals(processed_signals)
        
        # Assertions
        assert len(deduplicated) == 1
        assert deduplicated[0]["port"] == 443
        assert "_internal" not in deduplicated[0]
        assert deduplicated[0]["source_ip"] == "1.2.3.4"
    
    def test_mixed_source_normalization(self):
        """Test normalizing data from multiple sources."""
        mapper = FieldMapper()
        engine = NormalizationEngine()
        
        # Register mappings for different sources
        mapper.register_mapping(
            "source_a", {"domain": "name", "found_date": "discovered"}
        )
        mapper.register_mapping(
            "source_b", {"hostname": "name", "first_seen": "discovered"}
        )
        
        entities_a = [
            {"domain": "example.com", "found_date": "2024-01-01"}
        ]
        entities_b = [
            {"hostname": "example.com", "first_seen": "2024-01-01"}
        ]
        
        # Map all entities
        mapped_a = mapper.map_batch("source_a", entities_a)
        mapped_b = mapper.map_batch("source_b", entities_b)
        
        combined = mapped_a + mapped_b
        normalized = [engine.normalize_entity(e) for e in combined]
        deduplicated = engine.deduplicate_entities(normalized)
        
        # Cross-source deduplication should identify these as duplicates
        assert len(deduplicated) == 1
        assert deduplicated[0]["name"] == "example.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
