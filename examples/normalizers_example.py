#!/usr/bin/env python3
"""
Example demonstrating the Normalizers module.

This example shows how to use the normalizers module to:
1. Map fields from different sources
2. Normalize data (case, whitespace)
3. Deduplicate entities
4. Validate against schemas
5. Apply business logic rules
"""

from normalizers import NormalizationEngine, NormalizationConfig
from normalizers.mappers import FieldMapper
from normalizers.validators import SchemaValidator
from normalizers.rules import RuleEngine, DefaultValueRule, FieldRemovalRule


def main():
    """Run normalizers example."""
    print("=" * 60)
    print("CtxOS Normalizers Module Example")
    print("=" * 60)
    
    # Initialize components
    mapper = FieldMapper()
    engine = NormalizationEngine(
        NormalizationConfig(deduplication_strategy="hash")
    )
    validator = SchemaValidator()
    rule_engine = RuleEngine()
    
    # Step 1: Configure field mappings for different sources
    print("\n1. Configuring field mappings...")
    
    mapper.register_mapping(
        "dns_collector",
        {
            "domain_name": "name",
            "registered_date": "discovered",
            "domain_status": "status",
        },
    )
    
    mapper.register_mapping(
        "whois_service",
        {
            "hostname": "name",
            "first_seen": "discovered",
            "registration_status": "status",
        },
    )
    
    print("   - DNS collector mapping registered")
    print("   - WHOIS service mapping registered")
    
    # Step 2: Configure schema validation
    print("\n2. Configuring schema validation...")
    
    entity_schema = {
        "type": "object",
        "required": ["name", "discovered"],
        "properties": {
            "name": {"type": "string"},
            "discovered": {"type": "string"},
            "status": {"type": "string"},
            "confidence": {"type": "number"},
        },
    }
    validator.register_schema("domain_entity", entity_schema)
    print("   - Entity schema registered")
    
    # Step 3: Configure normalization rules
    print("\n3. Configuring normalization rules...")
    
    rule_engine.register_rule(
        DefaultValueRule({"confidence": 0.95, "source_count": 1})
    )
    rule_engine.register_rule(FieldRemovalRule(["_internal", "_debug"]))
    print("   - Default value rule registered")
    print("   - Field removal rule registered")
    
    # Step 4: Process data from multiple sources
    print("\n4. Processing data from multiple sources...")
    
    dns_data = [
        {
            "domain_name": "EXAMPLE.COM",
            "registered_date": "2020-01-15",
            "domain_status": "active",
            "_debug": "collected from DNS",
        },
        {
            "domain_name": "example.com",
            "registered_date": "2020-01-15",
            "domain_status": "active",
            "_debug": "collected from DNS backup",
        },
    ]
    
    whois_data = [
        {
            "hostname": "example.com",
            "first_seen": "2020-01-15",
            "registration_status": "active",
            "_internal": "whois_id_123",
        }
    ]
    
    print(f"   - DNS data: {len(dns_data)} entities")
    print(f"   - WHOIS data: {len(whois_data)} entities")
    
    # Step 5: Execute normalization pipeline
    print("\n5. Executing normalization pipeline...")
    
    # Map fields
    mapped_dns = mapper.map_batch("dns_collector", dns_data)
    mapped_whois = mapper.map_batch("whois_service", whois_data)
    all_mapped = mapped_dns + mapped_whois
    
    print(f"   - Mapped {len(all_mapped)} entities")
    
    # Normalize
    normalized = [engine.normalize_entity(e) for e in all_mapped]
    print(f"   - Normalized {len(normalized)} entities")
    
    # Apply rules
    processed = [rule_engine.apply_rules(e) for e in normalized]
    print(f"   - Applied rules to {len(processed)} entities")
    
    # Deduplicate
    deduplicated = engine.deduplicate_entities(processed)
    print(f"   - Deduplicated to {len(deduplicated)} unique entities")
    
    # Validate
    validation_results = [
        validator.validate_entity(e, "domain_entity") for e in deduplicated
    ]
    valid_count = sum(1 for is_valid, _ in validation_results if is_valid)
    print(f"   - Validated: {valid_count}/{len(deduplicated)} entities passed")
    
    # Step 6: Display results
    print("\n6. Results:")
    print("-" * 60)
    
    for i, entity in enumerate(deduplicated, 1):
        is_valid, errors = validation_results[i - 1]
        status = "✓ VALID" if is_valid else "✗ INVALID"
        print(f"\nEntity {i}: {status}")
        print(f"  Name: {entity.get('name', 'N/A')}")
        print(f"  Discovered: {entity.get('discovered', 'N/A')}")
        print(f"  Status: {entity.get('status', 'N/A')}")
        print(f"  Confidence: {entity.get('confidence', 'N/A')}")
        
        if errors:
            print(f"  Errors: {', '.join(errors)}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
