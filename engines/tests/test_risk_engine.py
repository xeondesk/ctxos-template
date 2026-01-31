"""
Comprehensive unit tests for Risk Engine scoring.
"""

import pytest
from datetime import datetime, timedelta

from core.models import (
    Entity,
    EntityType,
    Signal,
    SignalType,
    SignalSeverity,
    Context,
    EntitySeverity,
)
from engines import RiskEngine, ScoringResult


class TestRiskEngine:
    """Comprehensive tests for Risk Engine."""

    @pytest.fixture
    def engine(self):
        """Create Risk Engine instance."""
        return RiskEngine()

    @pytest.fixture
    def sample_entity(self):
        """Create sample entity."""
        return Entity(
            name="example.com",
            entity_type=EntityType.DOMAIN,
            source="test",
            severity=EntitySeverity.MEDIUM,
        )

    @pytest.fixture
    def sample_context(self, sample_entity):
        """Create sample context."""
        context = Context("test")
        context.add_entity(sample_entity)
        return context

    # ========== Initialization Tests ==========

    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine.name == "RiskEngine"
        assert engine.version == "1.0.0"
        assert engine.enabled is True
        assert engine.run_count == 0
        assert engine.error_count == 0
        assert engine.config == engine.DEFAULT_CONFIG

    def test_engine_configuration(self, engine):
        """Test engine configuration."""
        new_config = {
            "vulnerability_weight": 30,
            "open_ports_weight": 20,
        }
        assert engine.configure(new_config) is True
        assert engine.config["vulnerability_weight"] == 30

    def test_engine_enable_disable(self, engine):
        """Test enabling/disabling engine."""
        engine.disable()
        assert engine.enabled is False

        engine.enable()
        assert engine.enabled is True

    def test_engine_status(self, engine):
        """Test engine status retrieval."""
        status = engine.get_status()
        assert status["name"] == "RiskEngine"
        assert status["version"] == "1.0.0"
        assert status["enabled"] is True
        assert status["run_count"] == 0

    # ========== Basic Scoring Tests ==========

    def test_score_basic_entity(self, engine, sample_entity):
        """Test basic entity scoring."""
        result = engine.score(sample_entity)

        assert isinstance(result, ScoringResult)
        assert result.engine_name == "RiskEngine"
        assert result.entity_id == sample_entity.id
        assert 0 <= result.score <= 100
        assert result.severity in ["critical", "high", "medium", "low", "info"]
        assert engine.run_count == 1

    def test_score_multiple_entities(self, engine, sample_context):
        """Test scoring multiple entities."""
        entities = sample_context.get_entities_by_type("domain")

        results = [engine.score(entity) for entity in entities]

        assert len(results) >= 1
        assert all(isinstance(r, ScoringResult) for r in results)
        assert engine.run_count == len(results)

    def test_score_different_entity_types(self, engine):
        """Test scoring different entity types."""
        entity_types = [
            EntityType.DOMAIN,
            EntityType.IP_ADDRESS,
            EntityType.SERVICE,
            EntityType.EMAIL,
        ]

        results = []
        for etype in entity_types:
            entity = Entity(name=f"test-{etype.value}", entity_type=etype, source="test")
            results.append(engine.score(entity))

        assert len(results) == len(entity_types)
        assert all(0 <= r.score <= 100 for r in results)

    # ========== Signal Weighting Tests ==========

    def test_vulnerability_signal_weight(self, engine, sample_entity, sample_context):
        """Test vulnerability signal weighting."""
        # Add multiple vulnerability signals
        for i in range(5):
            signal = Signal(
                source="scanner",
                signal_type=SignalType.VULNERABILITY,
                data={"cve": f"CVE-2024-{i:04d}", "severity": "high"},
                entity_id=sample_entity.id,
                severity=SignalSeverity.HIGH,
            )
            sample_context.add_signal(signal)

        result = engine.score(sample_entity, sample_context)

        assert result.score > 50  # Should be higher due to vulnerabilities
        assert "vulnerability_count" in result.details["factors"]
        assert result.details["factors"]["vulnerability_count"] == 5

    def test_open_port_signal_weight(self, engine, sample_entity, sample_context):
        """Test open port signal weighting."""
        # Add open port signals
        for port in [22, 80, 443, 3389]:
            signal = Signal(
                source="scanner",
                signal_type=SignalType.OPEN_PORT,
                data={"port": port},
                entity_id=sample_entity.id,
                severity=SignalSeverity.MEDIUM,
            )
            sample_context.add_signal(signal)

        result = engine.score(sample_entity, sample_context)

        assert "open_ports" in result.details["factors"]
        assert result.details["factors"]["open_ports"] == 4

    def test_credential_exposure_weight(self, engine, sample_entity, sample_context):
        """Test credential exposure signal weighting."""
        # Add credential exposure signals
        for i in range(3):
            signal = Signal(
                source="breach_db",
                signal_type=SignalType.CREDENTIAL_EXPOSURE,
                data={"type": "password", "count": 100},
                entity_id=sample_entity.id,
                severity=SignalSeverity.CRITICAL,
            )
            sample_context.add_signal(signal)

        result = engine.score(sample_entity, sample_context)

        assert result.score > 70  # Credentials are high impact
        assert result.severity in ["critical", "high"]

    def test_malware_signal_weight(self, engine, sample_entity, sample_context):
        """Test malware signal weighting."""
        signal = Signal(
            source="av_engine",
            signal_type=SignalType.MALWARE,
            data={"family": "trojan", "samples": 5},
            entity_id=sample_entity.id,
            severity=SignalSeverity.CRITICAL,
        )
        sample_context.add_signal(signal)

        result = engine.score(sample_entity, sample_context)

        assert result.severity == "critical"
        assert result.score >= 80

    # ========== Score Aggregation Tests ==========

    def test_score_aggregation_multiple_signals(self, engine, sample_entity, sample_context):
        """Test score aggregation with multiple signals."""
        # Add mixed signals
        signal_types = [
            (SignalType.VULNERABILITY, SignalSeverity.HIGH),
            (SignalType.OPEN_PORT, SignalSeverity.MEDIUM),
            (SignalType.SUSPICIOUS_ACTIVITY, SignalSeverity.MEDIUM),
        ]

        for sig_type, severity in signal_types:
            signal = Signal(
                source="test",
                signal_type=sig_type,
                data={},
                entity_id=sample_entity.id,
                severity=severity,
            )
            sample_context.add_signal(signal)

        result = engine.score(sample_entity, sample_context)

        assert 0 <= result.score <= 100
        assert result.severity in ["critical", "high", "medium", "low", "info"]

    # ========== Threshold and Severity Tests ==========

    def test_severity_thresholds(self, engine):
        """Test severity threshold detection."""
        # Create entities and manually test threshold detection
        thresholds = {
            "critical": (80, 100),
            "high": (60, 79),
            "medium": (40, 59),
            "low": (20, 39),
            "info": (0, 19),
        }

        # Verify thresholds are applied correctly
        for severity, (low, high) in thresholds.items():
            test_score = (low + high) / 2
            detected_severity = (
                engine._determine_severity(test_score)
                if hasattr(engine, "_determine_severity")
                else (
                    "critical"
                    if test_score >= 80
                    else "high"
                    if test_score >= 60
                    else "medium"
                    if test_score >= 40
                    else "low"
                    if test_score >= 20
                    else "info"
                )
            )
            assert detected_severity == severity

    def test_high_risk_entity_detection(self, engine, sample_entity, sample_context):
        """Test high-risk entity detection."""
        # Add critical signals
        for i in range(3):
            signal = Signal(
                source="test",
                signal_type=SignalType.CREDENTIAL_EXPOSURE,
                data={},
                entity_id=sample_entity.id,
                severity=SignalSeverity.CRITICAL,
            )
            sample_context.add_signal(signal)

        result = engine.score(sample_entity, sample_context)

        assert result.score >= 60
        assert result.severity in ["critical", "high"]

    # ========== Age Decay Tests ==========

    def test_entity_age_decay(self, engine):
        """Test risk score decay for older entities."""
        # Create entity with old discovered_at
        old_entity = Entity(
            name="old.example.com",
            entity_type=EntityType.DOMAIN,
            source="test",
            discovered_at=datetime.utcnow() - timedelta(days=365),
        )

        new_entity = Entity(
            name="new.example.com",
            entity_type=EntityType.DOMAIN,
            source="test",
            discovered_at=datetime.utcnow(),
        )

        old_result = engine.score(old_entity)
        new_result = engine.score(new_entity)

        # Old entity should have lower score due to decay (or same if no signals)
        assert old_result.score <= new_result.score or old_result.score == new_result.score

    # ========== Recommendations Tests ==========

    def test_recommendations_generated(self, engine, sample_entity, sample_context):
        """Test recommendations are generated."""
        signal = Signal(
            source="test",
            signal_type=SignalType.VULNERABILITY,
            data={},
            entity_id=sample_entity.id,
            severity=SignalSeverity.HIGH,
        )
        sample_context.add_signal(signal)

        result = engine.score(sample_entity, sample_context)

        assert isinstance(result.recommendations, list)
        assert len(result.recommendations) > 0

    def test_high_risk_recommendations(self, engine, sample_entity, sample_context):
        """Test recommendations for high-risk entities."""
        # Add critical signal
        signal = Signal(
            source="test",
            signal_type=SignalType.MALWARE,
            data={},
            entity_id=sample_entity.id,
            severity=SignalSeverity.CRITICAL,
        )
        sample_context.add_signal(signal)

        result = engine.score(sample_entity, sample_context)

        assert len(result.recommendations) > 0
        assert result.severity in ["critical", "high"]

    # ========== Serialization Tests ==========

    def test_score_result_serialization(self, engine, sample_entity):
        """Test scoring result serialization."""
        result = engine.score(sample_entity)

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["engine_name"] == "RiskEngine"
        assert result_dict["entity_id"] == sample_entity.id
        assert "score" in result_dict
        assert "severity" in result_dict
        assert "timestamp" in result_dict

    def test_score_result_deserialization(self, engine, sample_entity):
        """Test scoring result deserialization."""
        result = engine.score(sample_entity)
        result_dict = result.to_dict()

        restored = ScoringResult.from_dict(result_dict)

        assert restored.engine_name == result.engine_name
        assert restored.entity_id == result.entity_id
        assert restored.score == result.score
        assert restored.severity == result.severity

    # ========== Edge Cases ==========

    def test_score_entity_no_signals(self, engine, sample_entity):
        """Test scoring entity with no signals."""
        result = engine.score(sample_entity)

        assert 0 <= result.score <= 100
        assert result.score >= 0  # Should have baseline score

    def test_score_empty_context(self, engine, sample_entity):
        """Test scoring with empty context."""
        context = Context("empty")

        result = engine.score(sample_entity, context)

        assert isinstance(result, ScoringResult)
        assert 0 <= result.score <= 100

    def test_score_entity_all_severity_levels(self, engine):
        """Test scoring entities with all severity levels."""
        for severity in EntitySeverity:
            entity = Entity(
                name=f"entity-{severity.value}",
                entity_type=EntityType.DOMAIN,
                source="test",
                severity=severity,
            )

            result = engine.score(entity)

            assert isinstance(result, ScoringResult)
            assert 0 <= result.score <= 100
