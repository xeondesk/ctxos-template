"""
Unit tests for core models.
"""

import pytest
from datetime import datetime, timedelta

from core.models import Entity, EntityType, EntitySeverity, EntityStatus
from core.models import Signal, SignalType, SignalSeverity, SignalConfidence
from core.models import Context


class TestEntity:
    """Tests for Entity model."""
    
    def test_entity_creation(self):
        """Test basic entity creation."""
        entity = Entity(
            name="example.com",
            entity_type=EntityType.DOMAIN,
            source="dns_collector"
        )
        
        assert entity.name == "example.com"
        assert entity.entity_type == EntityType.DOMAIN
        assert entity.source == "dns_collector"
        assert entity.id is not None
        assert entity.confidence == 0.5
        assert entity.status == EntityStatus.ACTIVE
    
    def test_entity_to_dict(self):
        """Test converting entity to dictionary."""
        entity = Entity(
            name="example.com",
            entity_type=EntityType.DOMAIN,
            source="dns_collector"
        )
        
        entity_dict = entity.to_dict()
        assert entity_dict["name"] == "example.com"
        assert entity_dict["entity_type"] == "domain"
        assert entity_dict["source"] == "dns_collector"
    
    def test_entity_from_dict(self):
        """Test creating entity from dictionary."""
        data = {
            "name": "example.com",
            "entity_type": "domain",
            "source": "dns_collector",
            "id": "test-id-123"
        }
        
        entity = Entity.from_dict(data)
        assert entity.name == "example.com"
        assert entity.entity_type == EntityType.DOMAIN
        assert entity.id == "test-id-123"
    
    def test_entity_tags(self):
        """Test entity tag management."""
        entity = Entity(
            name="example.com",
            entity_type=EntityType.DOMAIN,
            source="dns_collector"
        )
        
        entity.add_tag("monitored")
        entity.add_tag("external")
        
        assert "monitored" in entity.tags
        assert "external" in entity.tags
        
        entity.remove_tag("monitored")
        assert "monitored" not in entity.tags
    
    def test_entity_properties(self):
        """Test entity property management."""
        entity = Entity(
            name="example.com",
            entity_type=EntityType.DOMAIN,
            source="dns_collector"
        )
        
        entity.set_property("registrar", "NameCheap")
        entity.set_property("expiry", "2024-12-31")
        
        assert entity.get_property("registrar") == "NameCheap"
        assert entity.get_property("expiry") == "2024-12-31"
        assert entity.get_property("nonexistent") is None
    
    def test_entity_invalid_confidence(self):
        """Test entity rejects invalid confidence."""
        with pytest.raises(ValueError):
            Entity(
                name="example.com",
                entity_type=EntityType.DOMAIN,
                source="dns_collector",
                confidence=1.5
            )


class TestSignal:
    """Tests for Signal model."""
    
    def test_signal_creation(self):
        """Test basic signal creation."""
        signal = Signal(
            source="dns_collector",
            signal_type=SignalType.DNS_RECORD,
            data={"record_type": "A", "value": "93.184.216.34"}
        )
        
        assert signal.source == "dns_collector"
        assert signal.signal_type == SignalType.DNS_RECORD
        assert signal.data["record_type"] == "A"
        assert signal.id is not None
    
    def test_signal_expiry(self):
        """Test signal expiry checking."""
        past = datetime.utcnow() - timedelta(days=1)
        
        signal = Signal(
            source="collector",
            signal_type=SignalType.OPEN_PORT,
            data={},
            expiry=past
        )
        
        assert signal.is_expired()
    
    def test_signal_not_expired(self):
        """Test signal that hasn't expired."""
        future = datetime.utcnow() + timedelta(days=1)
        
        signal = Signal(
            source="collector",
            signal_type=SignalType.OPEN_PORT,
            data={},
            expiry=future
        )
        
        assert not signal.is_expired()
    
    def test_signal_to_dict(self):
        """Test converting signal to dictionary."""
        signal = Signal(
            source="dns_collector",
            signal_type=SignalType.DNS_RECORD,
            data={"record_type": "A"}
        )
        
        signal_dict = signal.to_dict()
        assert signal_dict["source"] == "dns_collector"
        assert signal_dict["signal_type"] == "dns_record"
    
    def test_signal_tags(self):
        """Test signal tag management."""
        signal = Signal(
            source="collector",
            signal_type=SignalType.OPEN_PORT,
            data={}
        )
        
        signal.add_tag("verified")
        signal.add_tag("critical")
        
        assert "verified" in signal.tags
        assert "critical" in signal.tags
    
    def test_signal_metadata(self):
        """Test signal metadata management."""
        signal = Signal(
            source="collector",
            signal_type=SignalType.OPEN_PORT,
            data={}
        )
        
        signal.set_metadata("port", 443)
        signal.set_metadata("protocol", "https")
        
        assert signal.get_metadata("port") == 443
        assert signal.get_metadata("protocol") == "https"


class TestContext:
    """Tests for Context model."""
    
    def test_context_creation(self):
        """Test basic context creation."""
        context = Context(name="Assessment-2024-01")
        
        assert context.name == "Assessment-2024-01"
        assert context.id is not None
        assert context.entity_count() == 0
        assert context.signal_count() == 0
    
    def test_context_add_entity(self):
        """Test adding entity to context."""
        context = Context(name="Test")
        entity = Entity(
            name="example.com",
            entity_type=EntityType.DOMAIN,
            source="dns"
        )
        
        context.add_entity(entity)
        assert context.entity_count() == 1
    
    def test_context_add_signal(self):
        """Test adding signal to context."""
        context = Context(name="Test")
        signal = Signal(
            source="collector",
            signal_type=SignalType.OPEN_PORT,
            data={}
        )
        
        context.add_signal(signal)
        assert context.signal_count() == 1
    
    def test_context_get_entity(self):
        """Test retrieving entity from context."""
        context = Context(name="Test")
        entity = Entity(
            name="example.com",
            entity_type=EntityType.DOMAIN,
            source="dns"
        )
        
        context.add_entity(entity)
        retrieved = context.get_entity(entity.id)
        
        assert retrieved is not None
        assert retrieved.name == "example.com"
    
    def test_context_get_entities_by_type(self):
        """Test getting entities by type."""
        context = Context(name="Test")
        
        entity1 = Entity(
            name="example.com",
            entity_type=EntityType.DOMAIN,
            source="dns"
        )
        entity2 = Entity(
            name="example.org",
            entity_type=EntityType.DOMAIN,
            source="dns"
        )
        entity3 = Entity(
            name="1.2.3.4",
            entity_type=EntityType.IP_ADDRESS,
            source="dns"
        )
        
        context.add_entities([entity1, entity2, entity3])
        
        domains = context.get_entities_by_type("domain")
        assert len(domains) == 2
        
        ips = context.get_entities_by_type("ip_address")
        assert len(ips) == 1
    
    def test_context_get_signals_for_entity(self):
        """Test getting signals for a specific entity."""
        context = Context(name="Test")
        
        entity = Entity(
            name="example.com",
            entity_type=EntityType.DOMAIN,
            source="dns"
        )
        
        signal1 = Signal(
            source="collector",
            signal_type=SignalType.DNS_RECORD,
            data={},
            entity_id=entity.id
        )
        signal2 = Signal(
            source="collector",
            signal_type=SignalType.CERTIFICATE,
            data={},
            entity_id=entity.id
        )
        
        context.add_entity(entity)
        context.add_signals([signal1, signal2])
        
        signals = context.get_signals_for_entity(entity.id)
        assert len(signals) == 2
    
    def test_context_remove_entity(self):
        """Test removing entity from context."""
        context = Context(name="Test")
        entity = Entity(
            name="example.com",
            entity_type=EntityType.DOMAIN,
            source="dns"
        )
        
        context.add_entity(entity)
        assert context.entity_count() == 1
        
        removed = context.remove_entity(entity.id)
        assert removed is True
        assert context.entity_count() == 0
    
    def test_context_to_dict(self):
        """Test converting context to dictionary."""
        context = Context(name="Test")
        
        entity = Entity(
            name="example.com",
            entity_type=EntityType.DOMAIN,
            source="dns"
        )
        context.add_entity(entity)
        
        context_dict = context.to_dict()
        assert context_dict["name"] == "Test"
        assert len(context_dict["entities"]) == 1
        assert context_dict["signal_count"] == 0
    
    def test_context_from_dict(self):
        """Test creating context from dictionary."""
        data = {
            "id": "test-id",
            "name": "Test Context",
            "entities": [
                {
                    "id": "ent-1",
                    "name": "example.com",
                    "entity_type": "domain",
                    "source": "dns"
                }
            ],
            "signals": []
        }
        
        context = Context.from_dict(data)
        assert context.name == "Test Context"
        assert context.entity_count() == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
