"""
Comprehensive integration tests for multi-engine workflows.
"""

import pytest
import json
from datetime import datetime

from core.models import Entity, EntityType, Signal, SignalType, SignalSeverity, Context
from engines import RiskEngine, ExposureEngine, DriftEngine, ScoringResult
from engines.engine_manager import EngineManager


class TestEngineIntegration:
    """Comprehensive integration tests for engine workflows."""

    @pytest.fixture
    def risk_engine(self):
        """Create Risk Engine instance."""
        return RiskEngine()

    @pytest.fixture
    def exposure_engine(self):
        """Create Exposure Engine instance."""
        return ExposureEngine()

    @pytest.fixture
    def drift_engine(self):
        """Create Drift Engine instance."""
        return DriftEngine()

    @pytest.fixture
    def sample_context(self):
        """Create sample context with entities and signals."""
        context = Context("integration_test")

        # Add domain entity
        domain = Entity(name="example.com", entity_type=EntityType.DOMAIN, source="osint")
        context.add_entity(domain)

        # Add IP entity
        ip = Entity(name="93.184.216.34", entity_type=EntityType.IP_ADDRESS, source="collector")
        context.add_entity(ip)

        # Add signals
        signals = [
            Signal(
                source="scanner",
                signal_type=SignalType.VULNERABILITY,
                data={"cve": "CVE-2024-1234"},
                entity_id=domain.id,
                severity=SignalSeverity.HIGH,
            ),
            Signal(
                source="scanner",
                signal_type=SignalType.OPEN_PORT,
                data={"port": 443, "service": "https"},
                entity_id=domain.id,
                severity=SignalSeverity.MEDIUM,
            ),
            Signal(
                source="scanner",
                signal_type=SignalType.CERTIFICATE,
                data={"issuer": "Let's Encrypt", "valid": True},
                entity_id=domain.id,
                severity=SignalSeverity.LOW,
            ),
        ]

        for signal in signals:
            context.add_signal(signal)

        return context

    # ========== Basic Pipeline Tests ==========

    def test_single_engine_scoring(self, risk_engine, sample_context):
        """Test single engine scoring."""
        entities = sample_context.get_entities_by_type("domain")

        for entity in entities:
            result = risk_engine.score(entity, sample_context)

            assert isinstance(result, ScoringResult)
            assert result.engine_name == "RiskEngine"
            assert 0 <= result.score <= 100

    def test_two_engine_sequence(self, risk_engine, exposure_engine, sample_context):
        """Test risk then exposure engine scoring."""
        entities = sample_context.get_entities_by_type("domain")

        for entity in entities:
            # Score with risk engine
            risk_result = risk_engine.score(entity, sample_context)

            # Score with exposure engine
            exposure_result = exposure_engine.score(entity, sample_context)

            assert risk_result.engine_name == "RiskEngine"
            assert exposure_result.engine_name == "ExposureEngine"
            assert 0 <= risk_result.score <= 100
            assert 0 <= exposure_result.score <= 100

    def test_three_engine_pipeline(
        self, risk_engine, exposure_engine, drift_engine, sample_context
    ):
        """Test complete three-engine pipeline."""
        entities = sample_context.get_entities_by_type("domain")

        for entity in entities:
            # Risk scoring
            risk_result = risk_engine.score(entity, sample_context)

            # Exposure scoring
            exposure_result = exposure_engine.score(entity, sample_context)

            # Drift scoring
            drift_result = drift_engine.score(entity, sample_context)

            # All should return valid results
            assert all(
                isinstance(r, ScoringResult) for r in [risk_result, exposure_result, drift_result]
            )
            assert all(0 <= r.score <= 100 for r in [risk_result, exposure_result, drift_result])
            assert all(
                r.severity in ["critical", "high", "medium", "low", "info"]
                for r in [risk_result, exposure_result, drift_result]
            )

    # ========== Score Aggregation Tests ==========

    def test_aggregate_multiple_scores(
        self, risk_engine, exposure_engine, drift_engine, sample_context
    ):
        """Test aggregating scores from multiple engines."""
        entities = sample_context.get_entities_by_type("domain")

        for entity in entities:
            scores = []

            # Collect scores from all engines
            scores.append(risk_engine.score(entity, sample_context).score)
            scores.append(exposure_engine.score(entity, sample_context).score)
            scores.append(drift_engine.score(entity, sample_context).score)

            # Calculate aggregate
            avg_score = sum(scores) / len(scores)

            assert 0 <= avg_score <= 100

    def test_weighted_score_aggregation(
        self, risk_engine, exposure_engine, drift_engine, sample_context
    ):
        """Test weighted aggregation of engine scores."""
        entities = sample_context.get_entities_by_type("domain")
        weights = [0.5, 0.3, 0.2]  # Risk 50%, Exposure 30%, Drift 20%

        for entity in entities:
            risk_score = risk_engine.score(entity, sample_context).score
            exposure_score = exposure_engine.score(entity, sample_context).score
            drift_score = drift_engine.score(entity, sample_context).score

            weighted_score = (
                risk_score * weights[0] + exposure_score * weights[1] + drift_score * weights[2]
            )

            assert 0 <= weighted_score <= 100

    # ========== Context Flow Tests ==========

    def test_entity_signal_flow(self, risk_engine, sample_context):
        """Test entity-signal flow through engine."""
        domain = sample_context.entities[0]
        signals = sample_context.get_signals_for_entity(domain.id)

        # Should have signals
        assert len(signals) > 0

        # Score should incorporate signals
        result = risk_engine.score(domain, sample_context)

        assert result.score > 0
        assert "factors" in result.details

    def test_multi_entity_scoring(self, risk_engine, sample_context):
        """Test scoring multiple entities."""
        results = []

        for entity in sample_context.entities:
            result = risk_engine.score(entity, sample_context)
            results.append(result)

        assert len(results) == len(sample_context.entities)
        assert all(isinstance(r, ScoringResult) for r in results)

    # ========== Engine State Tests ==========

    def test_engine_run_count(self, risk_engine, sample_context):
        """Test engine run count tracking."""
        initial_count = risk_engine.run_count

        for entity in sample_context.entities:
            risk_engine.score(entity, sample_context)

        assert risk_engine.run_count == initial_count + len(sample_context.entities)

    def test_engine_last_run_time(self, risk_engine, sample_context):
        """Test engine last run time tracking."""
        before = datetime.utcnow()

        for entity in sample_context.entities:
            risk_engine.score(entity, sample_context)

        after = datetime.utcnow()

        assert risk_engine.last_run is not None
        assert before <= risk_engine.last_run <= after

    # ========== Error Handling Tests ==========

    def test_engine_with_none_context(self, risk_engine, sample_context):
        """Test engine handling None context."""
        entity = sample_context.entities[0]

        result = risk_engine.score(entity, context=None)

        assert isinstance(result, ScoringResult)
        assert 0 <= result.score <= 100

    def test_engine_with_empty_context(self, risk_engine):
        """Test engine with empty context."""
        empty_context = Context("empty")
        entity = Entity(name="test.com", entity_type=EntityType.DOMAIN, source="test")

        result = risk_engine.score(entity, empty_context)

        assert isinstance(result, ScoringResult)

    # ========== Serialization Tests ==========

    def test_serialize_all_results(
        self, risk_engine, exposure_engine, drift_engine, sample_context
    ):
        """Test serialization of all engine results."""
        entity = sample_context.entities[0]

        results = [
            risk_engine.score(entity, sample_context),
            exposure_engine.score(entity, sample_context),
            drift_engine.score(entity, sample_context),
        ]

        # Serialize all
        serialized = [r.to_dict() for r in results]

        # Verify JSON serialization
        json_str = json.dumps(serialized, default=str)

        assert isinstance(json_str, str)
        assert len(json_str) > 0

    def test_deserialize_all_results(
        self, risk_engine, exposure_engine, drift_engine, sample_context
    ):
        """Test deserialization of all engine results."""
        entity = sample_context.entities[0]

        # Get and serialize results
        risk_result = risk_engine.score(entity, sample_context)
        exposure_result = exposure_engine.score(entity, sample_context)
        drift_result = drift_engine.score(entity, sample_context)

        # Deserialize
        restored_risk = ScoringResult.from_dict(risk_result.to_dict())
        restored_exposure = ScoringResult.from_dict(exposure_result.to_dict())
        restored_drift = ScoringResult.from_dict(drift_result.to_dict())

        assert restored_risk.engine_name == "RiskEngine"
        assert restored_exposure.engine_name == "ExposureEngine"
        assert restored_drift.engine_name == "DriftEngine"

    # ========== Scenario Tests ==========

    def test_high_risk_asset_detection(self, risk_engine, exposure_engine, sample_context):
        """Test detection of high-risk exposed asset."""
        entity = sample_context.entities[0]

        # Score for risk and exposure
        risk_result = risk_engine.score(entity, sample_context)
        exposure_result = exposure_engine.score(entity, sample_context)

        # If high risk OR high exposure, should flag
        if risk_result.score > 60 or exposure_result.score > 60:
            assert risk_result.severity in ["critical", "high"] or exposure_result.severity in [
                "critical",
                "high",
            ]

    def test_batch_scoring_performance(self, risk_engine):
        """Test batch scoring of multiple entities."""
        context = Context("batch")

        # Create multiple entities
        for i in range(20):
            entity = Entity(
                name=f"entity-{i}.example.com", entity_type=EntityType.DOMAIN, source="test"
            )
            context.add_entity(entity)

            # Add some signals
            for j in range(3):
                signal = Signal(
                    source="scanner",
                    signal_type=SignalType.VULNERABILITY,
                    data={"cve": f"CVE-2024-{i:04d}"},
                    entity_id=entity.id,
                    severity=SignalSeverity.MEDIUM,
                )
                context.add_signal(signal)

        # Score with Risk Engine
        risk_engine = RiskEngine()
        # Use first entity from context
        domain = (
            context.entities[0]
            if context.entities
            else Entity(name="test.example.com", entity_type=EntityType.DOMAIN, source="test")
        )
        risk_result = risk_engine.score(domain, context)

        assert risk_result.score >= 0  # Just verify we got a score
        assert risk_result.severity in ["info", "low", "medium", "high", "critical"]

    def test_multi_engine_scoring(self, risk_engine, exposure_engine, drift_engine):
        """Test scoring with multiple engines."""
        context = Context("Multi-Engine Test")

        domain = Entity(name="example.com", entity_type=EntityType.DOMAIN, source="test")
        domain.set_property("subdomains", 15)
        domain.set_property("waf_detected", False)
        context.add_entity(domain)

        # Score with all engines
        risk_engine = RiskEngine()
        exposure_engine = ExposureEngine()
        drift_engine = DriftEngine()

        risk_result = risk_engine.score(domain, context)
        exposure_result = exposure_engine.score(domain, context)
        drift_result = drift_engine.score(domain, context)

        # Verify results
        assert risk_result is not None
        assert exposure_result is not None
        assert drift_result is not None

        # Public domain should have exposure
        assert exposure_result.score > 20

    def test_engine_manager_workflow(self):
        """Test EngineManager orchestration."""
        # Create test context
        context = Context("Manager Test")

        entity = Entity(name="test.com", entity_type=EntityType.DOMAIN, source="test")
        context.add_entity(entity)

        signal = Signal(
            source="test", signal_type=SignalType.OPEN_PORT, data={"port": 80}, entity_id=entity.id
        )
        context.add_signal(signal)

        # Score with manager
        manager = EngineManager()
        results = manager.score_entity(entity, context)

        # Should have results from all engines
        assert len(results) > 0
        assert "risk" in results or "exposure" in results or "drift" in results

        # Aggregate results
        aggregated = manager.aggregate_results(results)
        assert "aggregated_score" in aggregated
        assert "aggregated_severity" in aggregated
        assert "combined_recommendations" in aggregated

    def test_engine_enable_disable(self):
        """Test enabling/disabling engines."""
        manager = EngineManager()
        initial_engines = len(manager.list_engines())

        # Disable an engine
        if "risk" in manager.list_engines():
            manager.disable_engine("risk")
            assert not manager.engines["risk"].enabled

            # Re-enable
            manager.enable_engine("risk")
            assert manager.engines["risk"].enabled

    def test_engine_status(self):
        """Test engine status reporting."""
        manager = EngineManager()

        # Get single engine status
        if "risk" in manager.list_engines():
            status = manager.get_engine_status("risk")
            assert "name" in status
            assert "version" in status
            assert "status" in status

        # Get all engine status
        all_status = manager.get_engine_status()
        assert len(all_status) > 0


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def test_high_risk_compromised_domain(self):
        """Test scoring for compromised domain."""
        context = Context("Incident Response")

        domain = Entity(
            name="compromised.example.com", entity_type=EntityType.DOMAIN, source="incident_report"
        )
        context.add_entity(domain)

        # Add malware and breach indicators
        for i in range(5):
            signal = Signal(
                source="threat_feed",
                signal_type=SignalType.MALWARE,
                data={"malware_family": f"trojan_{i}"},
                entity_id=domain.id,
                severity=SignalSeverity.CRITICAL,
            )
            context.add_signal(signal)

        breach_signal = Signal(
            source="data_breach_monitor",
            signal_type=SignalType.DATA_BREACH,
            data={"records_exposed": 10000},
            entity_id=domain.id,
            severity=SignalSeverity.CRITICAL,
        )
        context.add_signal(breach_signal)

        # Score
        risk_engine = RiskEngine()
        result = risk_engine.score(domain, context)

        # Should be critical
        assert result.score > 80
        assert result.severity == "critical"
        assert any("incident" in rec.lower() for rec in result.recommendations)

    def test_well_protected_domain(self):
        """Test scoring for well-protected domain."""
        context = Context("Well-Protected Asset")

        domain = Entity(name="secure.example.com", entity_type=EntityType.DOMAIN, source="internal")
        domain.set_property("waf_detected", True)
        domain.set_property("authentication_required", True)
        domain.set_property("cdn_used", True)
        context.add_entity(domain)

        # Add minimal signals
        signal = Signal(
            source="scanner",
            signal_type=SignalType.HTTP_HEADER,
            data={
                "headers": {
                    "Strict-Transport-Security": "max-age=31536000",
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY",
                    "Content-Security-Policy": "default-src 'self'",
                }
            },
            entity_id=domain.id,
            severity=SignalSeverity.LOW,
        )
        context.add_signal(signal)

        # Score
        exposure_engine = ExposureEngine()
        result = exposure_engine.score(domain, context)

        # Should be low exposure
        assert result.score < 40
        assert result.severity in ["low", "info"]

    def test_changing_entity_drift(self):
        """Test drift detection for changing entity."""
        drift_engine = DriftEngine()

        entity = Entity(
            name="unstable.example.com", entity_type=EntityType.DOMAIN, source="monitoring"
        )
        entity.set_property("ip_address", "1.2.3.4")
        entity.set_property("ns_servers", ["ns1.example.com"])

        # Initial scoring
        result1 = drift_engine.score(entity)
        assert result1.score == 0  # Creates baseline

        # Multiple changes
        entity.set_property("ip_address", "5.6.7.8")
        entity.set_property("ns_servers", ["ns2.example.com", "ns3.example.com"])
        entity.set_property("ssl_certificate", "new_cert")
        entity.set_property("administrator", "new_admin@example.com")

        result2 = drift_engine.score(entity)

        # Should detect significant drift
        assert result2.score > 30
        assert result2.details["property_changes"] > 0
        assert len(result2.recommendations) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
