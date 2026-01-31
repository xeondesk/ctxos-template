"""
Unit tests for scoring engines.
"""

import pytest
from datetime import datetime, timedelta

from core.models import Entity, EntityType, Signal, SignalType, SignalSeverity, Context
from engines import RiskEngine, ExposureEngine, DriftEngine, ScoringUtils


class TestScoringUtils:
    """Tests for ScoringUtils."""

    def test_normalize_score(self):
        """Test score normalization."""
        # Full range
        assert ScoringUtils.normalize_score(50, 0, 100) == 50
        assert ScoringUtils.normalize_score(0, 0, 100) == 0
        assert ScoringUtils.normalize_score(100, 0, 100) == 100

        # Custom range
        assert ScoringUtils.normalize_score(25, 0, 50) == 50
        assert ScoringUtils.normalize_score(10, 0, 20) == 50

    def test_score_to_severity(self):
        """Test score to severity conversion."""
        assert ScoringUtils.score_to_severity(90) == "critical"
        assert ScoringUtils.score_to_severity(70) == "high"
        assert ScoringUtils.score_to_severity(50) == "medium"
        assert ScoringUtils.score_to_severity(25) == "low"
        assert ScoringUtils.score_to_severity(5) == "info"

    def test_aggregate_scores(self):
        """Test score aggregation."""
        scores = [50, 60, 70]

        # Average
        avg = ScoringUtils.aggregate_scores(scores)
        assert avg == 60

        # Weighted
        weighted = ScoringUtils.aggregate_scores(scores, [1, 2, 1])
        assert weighted == 60

    def test_calculate_confidence(self):
        """Test confidence calculation."""
        assert ScoringUtils.calculate_confidence(100, 100) == 1.0
        assert ScoringUtils.calculate_confidence(50, 100) == 0.5
        assert ScoringUtils.calculate_confidence(0, 100) == 0.0


class TestRiskEngine:
    """Tests for Risk Engine."""

    def test_risk_engine_creation(self):
        """Test risk engine initialization."""
        engine = RiskEngine()
        assert engine.name == "RiskEngine"
        assert engine.enabled
        assert engine.run_count == 0

    def test_risk_engine_score_basic(self):
        """Test basic risk scoring."""
        engine = RiskEngine()

        entity = Entity(name="example.com", entity_type=EntityType.DOMAIN, source="test")

        result = engine.score(entity)

        assert result.entity_id == entity.id
        assert result.engine_name == "RiskEngine"
        assert 0 <= result.score <= 100
        assert result.severity in ["critical", "high", "medium", "low", "info"]

    def test_risk_engine_with_signals(self):
        """Test risk scoring with signals."""
        engine = RiskEngine()
        context = Context("test")

        entity = Entity(name="example.com", entity_type=EntityType.DOMAIN, source="test")
        context.add_entity(entity)

        # Add vulnerability signals
        for i in range(3):
            signal = Signal(
                source="scanner",
                signal_type=SignalType.VULNERABILITY,
                data={"cve": f"CVE-2024-{i:04d}"},
                entity_id=entity.id,
                severity=SignalSeverity.HIGH,
            )
            context.add_signal(signal)

        result = engine.score(entity, context)

        # Should have higher score with vulnerabilities
        assert result.score > 20
        assert len(result.recommendations) > 0

    def test_risk_engine_validate_config(self):
        """Test risk engine configuration validation."""
        engine = RiskEngine()

        # Valid config
        valid_config = {
            "vulnerability_weight": 25,
            "open_ports_weight": 25,
            "exposure_weight": 25,
            "activity_weight": 25,
        }
        assert engine.validate_config(valid_config)

        # Invalid config (wrong sum)
        invalid_config = {
            "vulnerability_weight": 50,
            "open_ports_weight": 50,
            "exposure_weight": 50,
            "activity_weight": 50,
        }
        assert not engine.validate_config(invalid_config)


class TestExposureEngine:
    """Tests for Exposure Engine."""

    def test_exposure_engine_creation(self):
        """Test exposure engine initialization."""
        engine = ExposureEngine()
        assert engine.name == "ExposureEngine"
        assert engine.enabled

    def test_exposure_engine_public_domain(self):
        """Test exposure scoring for public domain."""
        engine = ExposureEngine()

        entity = Entity(name="example.com", entity_type=EntityType.DOMAIN, source="test")

        result = engine.score(entity)

        # Public domains should have base exposure
        assert result.score >= 30
        assert "exposed" in result.severity or result.severity in ["critical", "high", "medium"]

    def test_exposure_engine_private_ip(self):
        """Test exposure scoring for private IP."""
        engine = ExposureEngine()

        entity = Entity(name="192.168.1.1", entity_type=EntityType.IP_ADDRESS, source="test")

        result = engine.score(entity)

        # Private IPs should have low exposure
        assert result.score < 30

    def test_exposure_engine_non_exposable(self):
        """Test exposure scoring for non-exposable entity."""
        engine = ExposureEngine()

        entity = Entity(name="John Doe", entity_type=EntityType.PERSON, source="test")

        result = engine.score(entity)

        # Non-exposable entities get 0 score
        assert result.score == 0

    def test_exposure_engine_validate_config(self):
        """Test exposure engine configuration validation."""
        engine = ExposureEngine()

        # Valid config
        valid_config = {
            "public_weight": 30,
            "service_weight": 30,
            "protocol_weight": 20,
            "subdomain_weight": 20,
        }
        assert engine.validate_config(valid_config)


class TestDriftEngine:
    """Tests for Drift Engine."""

    def test_drift_engine_creation(self):
        """Test drift engine initialization."""
        engine = DriftEngine()
        assert engine.name == "DriftEngine"
        assert engine.enabled
        assert len(engine.baselines) == 0

    def test_drift_engine_no_baseline(self):
        """Test drift scoring with no baseline."""
        engine = DriftEngine()

        entity = Entity(name="example.com", entity_type=EntityType.DOMAIN, source="test")

        result = engine.score(entity)

        # First score creates baseline
        assert result.score == 0
        assert entity.id in engine.baselines

    def test_drift_engine_with_changes(self):
        """Test drift scoring with property changes."""
        engine = DriftEngine()

        entity = Entity(name="example.com", entity_type=EntityType.DOMAIN, source="test")
        entity.set_property("registrar", "NameCheap")

        # First scoring creates baseline
        result1 = engine.score(entity)
        assert result1.score == 0

        # Modify entity
        entity.set_property("registrar", "GoDaddy")
        entity.set_property("expiry", "2025-01-01")

        # Second scoring detects drift
        result2 = engine.score(entity)
        assert result2.score > 0
        assert "property_changes" in result2.details

    def test_drift_engine_validate_config(self):
        """Test drift engine configuration validation."""
        engine = DriftEngine()

        # Valid config
        valid_config = {
            "property_change_weight": 30,
            "signal_change_weight": 40,
        }
        assert engine.validate_config(valid_config)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
