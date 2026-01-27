#!/usr/bin/env python3
"""
Core Modules Example - Demonstrates Entity, Signal, and Context usage.

This example shows how to:
1. Create and manage Entity objects
2. Create and manage Signal objects
3. Build Context collections
4. Use utility functions
5. Validate with schemas
"""

import json
from datetime import datetime, timedelta

from core.models import (
    Entity, EntityType, EntitySeverity,
    Signal, SignalType, SignalSeverity, SignalConfidence,
    Context
)
from core.utils import (
    normalize_domain, extract_emails, extract_ips,
    is_valid_domain, flatten_dict, merge_dicts
)
from core.schema import validate_schema, get_schema


def example_1_entity_creation():
    """Example 1: Create and manage entities."""
    print("\n" + "="*60)
    print("Example 1: Entity Creation and Management")
    print("="*60)
    
    # Create a domain entity
    domain = Entity(
        name="example.com",
        entity_type=EntityType.DOMAIN,
        source="dns_collector",
        severity=EntitySeverity.MEDIUM,
        confidence=0.85
    )
    
    print(f"\n✓ Created domain entity: {domain.name}")
    print(f"  Type: {domain.entity_type.value}")
    print(f"  Severity: {domain.severity.value}")
    print(f"  Confidence: {domain.confidence}")
    print(f"  ID: {domain.id}")
    
    # Add properties
    domain.set_property("registrar", "NameCheap")
    domain.set_property("ns_servers", ["ns1.example.com", "ns2.example.com"])
    domain.set_property("registration_date", "2020-01-15")
    
    print(f"\n✓ Added properties:")
    print(f"  Registrar: {domain.get_property('registrar')}")
    print(f"  NS Servers: {domain.get_property('ns_servers')}")
    
    # Add tags
    domain.add_tag("monitored")
    domain.add_tag("external")
    domain.add_tag("critical")
    
    print(f"\n✓ Added tags: {', '.join(domain.tags)}")
    
    return domain


def example_2_signal_creation():
    """Example 2: Create and manage signals."""
    print("\n" + "="*60)
    print("Example 2: Signal Creation and Management")
    print("="*60)
    
    # Create a signal from a collector
    signal = Signal(
        source="dns_collector",
        signal_type=SignalType.DNS_RECORD,
        data={
            "record_type": "A",
            "value": "93.184.216.34",
            "ttl": 3600,
            "timestamp": "2024-01-15T10:30:00Z"
        },
        severity=SignalSeverity.LOW,
        confidence=SignalConfidence.VERIFIED,
        expiry=datetime.utcnow() + timedelta(days=30)
    )
    
    print(f"\n✓ Created signal: {signal.signal_type.value}")
    print(f"  Source: {signal.source}")
    print(f"  Severity: {signal.severity.value}")
    print(f"  Confidence: {signal.confidence.value}")
    print(f"  Data: {json.dumps(signal.data, indent=2)}")
    
    # Add metadata
    signal.set_metadata("resolver", "8.8.8.8")
    signal.set_metadata("query_time_ms", 45)
    signal.set_metadata("response_code", "NOERROR")
    
    print(f"\n✓ Added metadata:")
    print(f"  Resolver: {signal.get_metadata('resolver')}")
    print(f"  Query Time: {signal.get_metadata('query_time_ms')}ms")
    
    # Check expiry
    if not signal.is_expired():
        print(f"\n✓ Signal is valid (expires in {(signal.expiry - datetime.utcnow()).days} days)")
    
    return signal


def example_3_context_management():
    """Example 3: Build and query context."""
    print("\n" + "="*60)
    print("Example 3: Context Management")
    print("="*60)
    
    # Create context
    context = Context(
        name="ACME-Corp-Assessment-2024-Q1",
        description="Security assessment for ACME Corporation"
    )
    
    print(f"\n✓ Created context: {context.name}")
    
    # Create multiple entities
    entities = [
        Entity(
            name="acme.com",
            entity_type=EntityType.DOMAIN,
            source="dns",
            severity=EntitySeverity.HIGH,
            confidence=0.95
        ),
        Entity(
            name="192.0.2.1",
            entity_type=EntityType.IP_ADDRESS,
            source="whois",
            severity=EntitySeverity.MEDIUM,
            confidence=0.85
        ),
        Entity(
            name="admin@acme.com",
            entity_type=EntityType.EMAIL,
            source="osint",
            severity=EntitySeverity.LOW,
            confidence=0.70
        ),
    ]
    
    context.add_entities(entities)
    print(f"\n✓ Added {len(entities)} entities:")
    for entity in entities:
        print(f"  - {entity.name} ({entity.entity_type.value})")
    
    # Create signals
    signals = [
        Signal(
            source="dns_collector",
            signal_type=SignalType.DNS_RECORD,
            data={"record_type": "A", "value": "192.0.2.1"},
            entity_id=entities[0].id,
            severity=SignalSeverity.LOW
        ),
        Signal(
            source="vulnerability_scanner",
            signal_type=SignalType.OPEN_PORT,
            data={"port": 443, "protocol": "https"},
            entity_id=entities[1].id,
            severity=SignalSeverity.MEDIUM
        ),
    ]
    
    context.add_signals(signals)
    print(f"\n✓ Added {len(signals)} signals")
    
    # Query entities by type
    domains = context.get_entities_by_type("domain")
    print(f"\n✓ Domains found: {len(domains)}")
    for domain in domains:
        print(f"  - {domain.name}")
    
    # Get signals for first entity
    entity_signals = context.get_signals_for_entity(entities[0].id)
    print(f"\n✓ Signals for {entities[0].name}: {len(entity_signals)}")
    for sig in entity_signals:
        print(f"  - {sig.signal_type.value}")
    
    # Analytics
    print(f"\n✓ Context Analytics:")
    print(f"  Total Entities: {context.entity_count()}")
    print(f"  Total Signals: {context.signal_count()}")
    
    return context


def example_4_serialization():
    """Example 4: Serialize/deserialize objects."""
    print("\n" + "="*60)
    print("Example 4: Serialization and Deserialization")
    print("="*60)
    
    # Create entity
    original = Entity(
        name="test.com",
        entity_type=EntityType.DOMAIN,
        source="osint"
    )
    original.add_tag("test")
    original.set_property("notes", "Example entity")
    
    # Serialize
    entity_dict = original.to_dict()
    print(f"\n✓ Serialized entity:")
    print(json.dumps(entity_dict, indent=2, default=str))
    
    # Deserialize
    restored = Entity.from_dict(entity_dict)
    print(f"\n✓ Deserialized entity: {restored.name}")
    print(f"  Type: {restored.entity_type.value}")
    print(f"  Tags: {restored.tags}")
    print(f"  Properties: {restored.properties}")
    
    return restored


def example_5_utility_functions():
    """Example 5: Use utility functions."""
    print("\n" + "="*60)
    print("Example 5: Utility Functions")
    print("="*60)
    
    # Domain normalization
    messy_domain = "  EXAMPLE.COM.  "
    clean = normalize_domain(messy_domain)
    print(f"\n✓ Normalized domain: '{messy_domain}' → '{clean}'")
    
    # Domain validation
    test_domains = ["example.com", "valid-domain.org", "invalid..com"]
    print(f"\n✓ Domain validation:")
    for domain in test_domains:
        valid = is_valid_domain(domain)
        print(f"  {domain}: {'✓ Valid' if valid else '✗ Invalid'}")
    
    # Extract information from text
    text = """
    Contact us at admin@example.com or support@example.org.
    Our servers are at 192.0.2.1 and 192.0.2.2.
    Visit https://example.com for more info.
    """
    
    emails = extract_emails(text)
    ips = extract_ips(text)
    
    print(f"\n✓ Extracted from text:")
    print(f"  Emails: {emails}")
    print(f"  IPs: {ips}")
    
    # Dictionary utilities
    dict1 = {
        "name": "John",
        "contact": {
            "email": "john@example.com",
            "phone": "555-1234"
        }
    }
    dict2 = {
        "department": "Security",
        "contact": {
            "address": "123 Main St"
        }
    }
    
    merged = merge_dicts(dict1, dict2)
    print(f"\n✓ Merged dictionaries:")
    print(json.dumps(merged, indent=2))
    
    # Flatten dictionary
    flat = flatten_dict(merged)
    print(f"\n✓ Flattened dictionary:")
    print(json.dumps(flat, indent=2))


def example_6_schema_validation():
    """Example 6: Validate with schemas."""
    print("\n" + "="*60)
    print("Example 6: Schema Validation")
    print("="*60)
    
    # Create entity
    entity = Entity(
        name="acme.com",
        entity_type=EntityType.DOMAIN,
        source="dns_collector"
    )
    
    # Serialize
    entity_dict = entity.to_dict()
    
    # Validate
    is_valid = validate_schema("entity", entity_dict)
    print(f"\n✓ Entity validation: {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    if is_valid:
        print(f"  Entity matches schema v1.0.0")
        
        # Show schema
        schema = get_schema("entity")
        print(f"\n✓ Schema structure:")
        print(json.dumps(schema, indent=2))


def example_7_complete_workflow():
    """Example 7: Complete workflow combining all concepts."""
    print("\n" + "="*60)
    print("Example 7: Complete Workflow")
    print("="*60)
    
    # 1. Create context
    context = Context(name="Security Assessment - Jan 2024")
    
    # 2. Discover entities and signals
    discovered_text = """
    Found the following in reconnaissance:
    - Domain: vulnerable-app.example.com
    - IP: 192.0.2.100
    - Email contacts: admin@example.com, security@example.com
    - Services running on 192.0.2.100:80, 192.0.2.100:443
    """
    
    print(f"\n✓ Processing reconnaissance data:")
    
    # 3. Extract and create entities
    emails = extract_emails(discovered_text)
    ips = extract_ips(discovered_text)
    
    for email in emails:
        entity = Entity(
            name=email,
            entity_type=EntityType.EMAIL,
            source="osint_text_analysis"
        )
        context.add_entity(entity)
    
    for ip in ips:
        entity = Entity(
            name=ip,
            entity_type=EntityType.IP_ADDRESS,
            source="network_discovery"
        )
        context.add_entity(entity)
    
    # 4. Create signals for discovered items
    if ips:
        ip_entity = context.get_entities_by_type("ip_address")[0]
        signal = Signal(
            source="port_scanner",
            signal_type=SignalType.OPEN_PORT,
            data={"ports": [80, 443]},
            entity_id=ip_entity.id,
            severity=SignalSeverity.MEDIUM
        )
        context.add_signal(signal)
    
    # 5. Summary
    print(f"\n✓ Workflow Summary:")
    print(f"  Entities discovered: {context.entity_count()}")
    print(f"  Signals generated: {context.signal_count()}")
    print(f"  Ready for analysis and scoring")
    
    # 6. Export
    context_dict = context.to_dict()
    print(f"\n✓ Context exported to dictionary format")
    print(f"  Size: {len(json.dumps(context_dict))} bytes")


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "Core Modules - Usage Examples" + " "*20 + "║")
    print("╚" + "="*58 + "╝")
    
    # Run examples
    example_1_entity_creation()
    example_2_signal_creation()
    example_3_context_management()
    example_4_serialization()
    example_5_utility_functions()
    example_6_schema_validation()
    example_7_complete_workflow()
    
    print("\n" + "="*60)
    print("All examples completed successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
