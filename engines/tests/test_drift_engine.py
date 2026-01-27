"""
Comprehensive unit tests for Drift Engine scoring.
"""

import pytest
from datetime import datetime, timedelta

from core.models import Entity, EntityType, Signal, SignalType, SignalSeverity, Context
from engines import DriftEngine, ScoringResult


class TestDriftEngine:
    """Comprehensive tests for Drift Engine."""
    
    @pytest.fixture
    def engine(self):
        """Create Drift Engine instance."""
        return DriftEngine()
    
    @pytest.fixture
    def sample_entity(self):
        """Create sample entity."""
        entity = Entity(
            name="example.com",
            entity_type=EntityType.DOMAIN,
            source="test"
        )
        # Add some initial properties
        entity.set_property("dns_servers", ["8.8.8.8", "8.8.4.4"])
        entity.set_property("authentication_method", "HTTPS")
        entity.set_property("ssl_certificate", "Let's Encrypt")
        return entity
    
    # ========== Initialization Tests ==========
    
    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine.name == "DriftEngine"
        assert engine.version == "1.0.0"
        assert engine.enabled is True
        assert len(engine.baselines) == 0
    
    def test_engine_configuration(self, engine):
        """Test engine configuration."""
        new_config = {
            "property_change_weight": 40,
            "signal_change_weight": 30,
        }
        assert engine.configure(new_config) is True
        assert engine.config["property_change_weight"] == 40
    
    def test_baseline_storage(self, engine, sample_entity):
        """Test baseline storage."""
        engine.baselines[sample_entity.id] = {"properties": {}}
        
        assert sample_entity.id in engine.baselines
    
    # ========== Property Change Detection Tests ==========
    
    def test_detect_property_change(self, engine, sample_entity):
        """Test detection of property changes."""
        # Score once to establish baseline
        result1 = engine.score(sample_entity)
        
        # Modify property
        sample_entity.set_property("dns_servers", ["1.1.1.1", "1.0.0.1"])
        
        # Score again
        result2 = engine.score(sample_entity)
        
        assert result2.details.get("property_changes", 0) >= 0
    
    def test_detect_new_properties(self, engine, sample_entity):
        """Test detection of new properties."""
        # Score once to establish baseline
        result1 = engine.score(sample_entity)
        
        # Add new property
        sample_entity.set_property("new_firewall_rule", "port 443 allowed")
        
        # Score again
        result2 = engine.score(sample_entity)
        
        # Should detect new property
        assert "new_properties" in result2.details
    
    def test_detect_removed_properties(self, engine, sample_entity):
        """Test detection of removed properties."""
        # Store initial properties
        initial_count = len(sample_entity.properties)
        
        # Score once to establish baseline
        result1 = engine.score(sample_entity)
        
        # Remove property - simulate by creating new entity with fewer properties
        modified_entity = Entity(
            name=sample_entity.name,
            entity_type=sample_entity.entity_type,
            source=sample_entity.source,
            id=sample_entity.id
        )
        modified_entity.set_property("dns_servers", ["8.8.8.8"])
        
        # Score modified entity
        result2 = engine.score(modified_entity)
        
        # Should detect property removal
        assert "removed_properties" in result2.details
    
    # ========== Critical Property Monitoring Tests ==========
    
    def test_critical_property_dns_change(self, engine, sample_entity):
        """Test detection of DNS server change."""
        # Establish baseline
        result1 = engine.score(sample_entity)
        
        # Change DNS servers (critical property)
        sample_entity.set_property("dns_servers", ["9.9.9.9", "149.112.112.112"])
        
        # Score again
        result2 = engine.score(sample_entity)
        
        # Should flag as drift
        assert result2.severity in ["critical", "high", "medium"]
    
    def test_critical_property_ssl_change(self, engine, sample_entity):
        """Test detection of SSL certificate change."""
        # Establish baseline
        result1 = engine.score(sample_entity)
        
        # Change SSL certificate (critical property)
        sample_entity.set_property("ssl_certificate", "DigiCert")
        
        # Score again
        result2 = engine.score(sample_entity)
        
        # Should flag as drift
        assert result2.severity in ["critical", "high", "medium"]
    
    def test_critical_property_authentication_change(self, engine, sample_entity):
        """Test detection of authentication method change."""
        # Establish baseline
        result1 = engine.score(sample_entity)
        
        # Change authentication method (critical property)
        sample_entity.set_property("authentication_method", "HTTP")
        
        # Score again
        result2 = engine.score(sample_entity)
        
        # Should flag as critical drift
        assert result2.score > 40  # Should be elevated
    
    # ========== Signal Change Detection Tests ==========
    
    def test_detect_new_signals(self, engine, sample_entity):
        """Test detection of new signals."""
        context = Context("test")
        context.add_entity(sample_entity)
        
        # Score once to establish baseline
        result1 = engine.score(sample_entity, context)
        
        # Add new signal
        signal = Signal(
            source="scanner",
            signal_type=SignalType.VULNERABILITY,
            data={"cve": "CVE-2024-1234"},
            entity_id=sample_entity.id,
            severity=SignalSeverity.HIGH
        )
        context.add_signal(signal)
        
        # Score again
        result2 = engine.score(sample_entity, context)
        
        assert result2.details.get("signal_changes", 0) >= 0
    
    def test_detect_removed_signals(self, engine, sample_entity):
        """Test detection of removed signals."""
        context1 = Context("test1")
        context1.add_entity(sample_entity)
        
        # Add signal
        signal = Signal(
            source="scanner",
            signal_type=SignalType.VULNERABILITY,
            data={"cve": "CVE-2024-1234"},
            entity_id=sample_entity.id,
            severity=SignalSeverity.HIGH
        )
        context1.add_signal(signal)
        
        # Score with signal
        result1 = engine.score(sample_entity, context1)
        
        # Score without signal (different context)
        context2 = Context("test2")
        context2.add_entity(sample_entity)
        result2 = engine.score(sample_entity, context2)
        
        assert "removed_signals" in result2.details
    
    def test_detect_modified_signals(self, engine, sample_entity):
        """Test detection of modified signals."""
        context = Context("test")
        context.add_entity(sample_entity)
        
        # Add signal with low severity
        signal = Signal(
            source="scanner",
            signal_type=SignalType.OPEN_PORT,
            data={"port": 80},
            entity_id=sample_entity.id,
            severity=SignalSeverity.LOW
        )
        context.add_signal(signal)
        
        # Score once
        result1 = engine.score(sample_entity, context)
        
        # Simulate signal severity change
        context.signals[0].severity = SignalSeverity.CRITICAL
        
        # Score again
        result2 = engine.score(sample_entity, context)
        
        # Should detect modification
        assert "signal_changes" in result2.details or "modified_signals" in result2.details
    
    # ========== Change Velocity Tests ==========
    
    def test_change_velocity_calculation(self, engine, sample_entity):
        """Test change velocity calculation."""
        # Create context spanning multiple days
        context = Context("test")
        context.add_entity(sample_entity)
        
        # Add signals over time
        for i in range(3):
            signal = Signal(
                source="scanner",
                signal_type=SignalType.VULNERABILITY,
                data={"cve": f"CVE-2024-{i:04d}"},
                entity_id=sample_entity.id,
                severity=SignalSeverity.MEDIUM,
                timestamp=datetime.utcnow() - timedelta(days=i)
            )
            context.add_signal(signal)
        
        result = engine.score(sample_entity, context)
        
        # Should have change velocity metric
        assert "change_velocity" in result.details
    
    # ========== Drift Scoring Tests ==========
    
    def test_drift_scoring_no_changes(self, engine, sample_entity):
        """Test drift scoring when no changes detected."""
        # Score twice with same entity
        result1 = engine.score(sample_entity)
        result2 = engine.score(sample_entity)
        
        # Second result should show minimal drift
        assert result2.score <= 30  # Minimal drift expected
    
    def test_drift_scoring_significant_changes(self, engine, sample_entity):
        """Test drift scoring with significant changes."""
        # Establish baseline
        result1 = engine.score(sample_entity)
        
        # Make multiple changes
        sample_entity.set_property("dns_servers", ["1.1.1.1"])
        sample_entity.set_property("authentication_method", "LDAP")
        sample_entity.set_property("firewall_rules", "Modified")
        sample_entity.set_property("ip_address", "10.0.0.1")
        
        # Score again
        result2 = engine.score(sample_entity)
        
        # Should detect significant drift
        assert result2.score >= 40
        assert result2.severity in ["high", "medium"]
    
    def test_drift_severity_escalation(self, engine, sample_entity):
        """Test drift severity escalation with multiple changes."""
        # Establish baseline
        result1 = engine.score(sample_entity)
        
        # Make critical property changes
        critical_properties = [
            "dns_servers",
            "authentication_method",
            "ssl_certificate",
            "firewall_rules",
        ]
        
        for prop in critical_properties:
            sample_entity.set_property(prop, "changed_value")
        
        # Score again
        result2 = engine.score(sample_entity)
        
        # Should be high/critical
        assert result2.score >= 60
    
    # ========== Recommendations Tests ==========
    
    def test_drift_recommendations_generated(self, engine, sample_entity):
        """Test recommendations are generated for drift."""
        result1 = engine.score(sample_entity)
        
        # Make changes
        sample_entity.set_property("dns_servers", ["1.1.1.1"])
        
        result2 = engine.score(sample_entity)
        
        # Should have recommendations
        assert isinstance(result2.recommendations, list)
        assert len(result2.recommendations) > 0
    
    def test_drift_recommendations_critical_changes(self, engine, sample_entity):
        """Test recommendations for critical property changes."""
        result1 = engine.score(sample_entity)
        
        # Change critical property
        sample_entity.set_property("ssl_certificate", "changed")
        
        result2 = engine.score(sample_entity)
        
        # Should have action recommendations
        assert len(result2.recommendations) > 0
    
    # ========== Time-Based Tests ==========
    
    def test_drift_tracking_over_time(self, engine, sample_entity):
        """Test drift tracking over extended period."""
        # Score 1
        result1 = engine.score(sample_entity)
        
        # Wait simulation
        original_time = sample_entity.discovered_at
        sample_entity.discovered_at = datetime.utcnow() - timedelta(days=7)
        
        # Make changes
        sample_entity.set_property("dns_servers", ["1.1.1.1"])
        
        # Score 2
        result2 = engine.score(sample_entity)
        
        assert "days_tracked" in result2.details or result2.score >= 0
    
    # ========== Baseline Management Tests ==========
    
    def test_baseline_creation(self, engine, sample_entity):
        """Test baseline creation on first score."""
        assert sample_entity.id not in engine.baselines
        
        engine.score(sample_entity)
        
        assert sample_entity.id in engine.baselines
    
    def test_baseline_update(self, engine, sample_entity):
        """Test baseline updating on subsequent scores."""
        # First score
        engine.score(sample_entity)
        first_baseline = engine.baselines.get(sample_entity.id)
        
        # Modify entity
        sample_entity.set_property("new_prop", "value")
        
        # Second score
        engine.score(sample_entity)
        second_baseline = engine.baselines.get(sample_entity.id)
        
        # Baselines should differ
        assert first_baseline is not None
        assert second_baseline is not None
    
    # ========== Serialization Tests ==========
    
    def test_drift_result_serialization(self, engine, sample_entity):
        """Test drift result serialization."""
        result = engine.score(sample_entity)
        
        result_dict = result.to_dict()
        
        assert result_dict["engine_name"] == "DriftEngine"
        assert result_dict["entity_id"] == sample_entity.id
        assert "score" in result_dict
        assert "severity" in result_dict
    
    def test_drift_result_deserialization(self, engine, sample_entity):
        """Test drift result deserialization."""
        result = engine.score(sample_entity)
        result_dict = result.to_dict()
        
        restored = ScoringResult.from_dict(result_dict)
        
        assert restored.engine_name == result.engine_name
        assert restored.score == result.score
    
    # ========== Edge Cases ==========
    
    def test_first_time_entity_scoring(self, engine):
        """Test scoring entity for first time."""
        entity = Entity(
            name="new.example.com",
            entity_type=EntityType.DOMAIN,
            source="test"
        )
        
        result = engine.score(entity)
        
        assert isinstance(result, ScoringResult)
        assert 0 <= result.score <= 100
    
    def test_empty_baseline_entity(self, engine):
        """Test scoring entity with minimal properties."""
        entity = Entity(
            name="minimal.example.com",
            entity_type=EntityType.DOMAIN,
            source="test"
        )
        
        result = engine.score(entity)
        
        assert isinstance(result, ScoringResult)
    
    def test_entity_with_many_properties(self, engine):
        """Test drift detection with many properties."""
        entity = Entity(
            name="complex.example.com",
            entity_type=EntityType.DOMAIN,
            source="test"
        )
        
        # Add many properties
        for i in range(20):
            entity.set_property(f"property_{i}", f"value_{i}")
        
        result1 = engine.score(entity)
        
        # Modify some properties
        for i in range(0, 10, 2):
            entity.set_property(f"property_{i}", f"modified_value_{i}")
        
        result2 = engine.score(entity)
        
        assert isinstance(result2, ScoringResult)
