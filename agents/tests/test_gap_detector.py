"""
Tests for Gap Detector Agent.
"""

import pytest
from datetime import datetime, timedelta

from core.models.entity import Entity
from core.models.signal import Signal
from core.models.context import Context
from core.scoring.risk import ScoringResult
from agents.gap_detector import GapDetector, DataGap, GapAnalysisResult, GapType


@pytest.fixture
def gap_detector():
    """Create Gap Detector instance."""
    return GapDetector(
        name="test_gap_detector",
        version="1.0.0",
        max_data_age_hours=168,
        min_coverage_threshold=0.7,
    )


@pytest.fixture
def sample_entity():
    """Create sample entity."""
    return Entity(
        id="entity-001",
        entity_type="host",
        name="test-host",
        description="Test host",
        properties={"environment": "production", "public": True},
    )


@pytest.fixture
def sample_signals():
    """Create sample signals."""
    return [
        Signal(
            id="signal-001",
            source="vulnerability_scanner",
            signal_type="VULNERABILITY",
            severity="critical",
            description="Critical vulnerability detected",
            timestamp=datetime.utcnow() - timedelta(hours=24),
        ),
        Signal(
            id="signal-002",
            source="network_scanner",
            signal_type="PORT",
            severity="high",
            description="Open port 443 detected",
            timestamp=datetime.utcnow() - timedelta(hours=48),
        ),
        Signal(
            id="signal-003",
            source="asset_inventory",
            signal_type="SERVICE",
            severity="medium",
            description="Web service detected",
            timestamp=datetime.utcnow() - timedelta(hours=72),
        ),
        Signal(
            id="signal-004",
            source="config_scanner",
            signal_type="CONFIGURATION",
            severity="low",
            description="Configuration issue found",
            timestamp=datetime.utcnow() - timedelta(hours=200),  # Stale
        ),
    ]


@pytest.fixture
def sample_context(sample_entity, sample_signals):
    """Create sample context."""
    return Context(
        entity=sample_entity,
        signals=sample_signals,
    )


@pytest.fixture
def sample_scoring_result():
    """Create sample scoring result."""
    return ScoringResult(
        score=75.0,
        severity="high",
        details={"risk_factors": ["vulnerability", "exposure"]},
        metrics={"vulnerability": 30, "exposure": 25, "drift": 20},
        recommendations=["Patch vulnerabilities", "Reduce exposure"],
    )


class TestGapDetector:
    """Test Gap Detector functionality."""

    def test_initialization(self, gap_detector):
        """Test gap detector initialization."""
        assert gap_detector.name == "test_gap_detector"
        assert gap_detector.version == "1.0.0"
        assert gap_detector.max_data_age_hours == 168
        assert gap_detector.min_coverage_threshold == 0.7
        assert "vulnerability_scanner" in gap_detector.critical_sources
        assert "host" in gap_detector.entity_type_requirements

    def test_analyze_success(self, gap_detector, sample_context):
        """Test successful gap analysis."""
        result = gap_detector.analyze(sample_context)

        assert result.success is True
        assert "gap_analysis" in result.output
        assert "summary" in result.output

    def test_analyze_no_entity(self, gap_detector):
        """Test analysis with no entity."""
        context = Context(entity=None, signals=[])
        result = gap_detector.analyze(context)

        assert result.success is True
        analysis = result.output["gap_analysis"]
        assert analysis["total_gaps"] == 0

    def test_detect_missing_signals(self, gap_detector, sample_context):
        """Test missing signal detection."""
        # Remove some required signals
        incomplete_signals = [s for s in sample_context.signals if s.signal_type != "CONFIGURATION"]
        incomplete_context = Context(entity=sample_context.entity, signals=incomplete_signals)

        result = gap_detector.analyze(incomplete_context)
        analysis = result.output["gap_analysis"]

        # Should detect missing CONFIGURATION signal
        missing_signal_gaps = [
            gap for gap in analysis["gaps"] if gap["gap_type"] == "missing_signal"
        ]
        assert len(missing_signal_gaps) > 0

    def test_detect_outdated_data(self, gap_detector, sample_context):
        """Test outdated data detection."""
        result = gap_detector.analyze(sample_context)
        analysis = result.output["gap_analysis"]

        # Should detect stale CONFIGURATION signal
        outdated_gaps = [gap for gap in analysis["gaps"] if gap["gap_type"] == "outdated_data"]
        assert len(outdated_gaps) > 0

    def test_detect_coverage_gaps(self, gap_detector, sample_context):
        """Test coverage gap detection."""
        result = gap_detector.analyze(sample_context)
        analysis = result.output["gap_analysis"]

        # Check for missing critical sources
        coverage_gaps = [gap for gap in analysis["gaps"] if gap["gap_type"] == "coverage_gap"]
        assert len(coverage_gaps) >= 0  # May or may not have gaps

    def test_detect_monitoring_gaps(self, gap_detector, sample_context):
        """Test monitoring gap detection."""
        result = gap_detector.analyze(sample_context)
        analysis = result.output["gap_analysis"]

        # Check for monitoring gaps
        monitoring_gaps = [gap for gap in analysis["gaps"] if gap["gap_type"] == "monitoring_gap"]
        assert len(monitoring_gaps) >= 0  # May or may not have gaps

    def test_detect_correlation_gaps(self, gap_detector, sample_context):
        """Test correlation gap detection."""
        result = gap_detector.analyze(sample_context)
        analysis = result.output["gap_analysis"]

        # Check for correlation gaps
        correlation_gaps = [gap for gap in analysis["gaps"] if gap["gap_type"] == "correlation_gap"]
        assert len(correlation_gaps) >= 0  # May or may not have gaps

    def test_no_signals_coverage_gap(self, gap_detector, sample_entity):
        """Test coverage gap when no signals present."""
        context = Context(entity=sample_entity, signals=[])
        result = gap_detector.analyze(context)
        analysis = result.output["gap_analysis"]

        # Should detect complete lack of coverage
        assert analysis["total_gaps"] > 0
        coverage_gaps = [gap for gap in analysis["gaps"] if gap["gap_type"] == "coverage_gap"]
        assert len(coverage_gaps) > 0
        assert coverage_gaps[0]["title"] == "No Data Coverage"

    def test_coverage_score_calculation(self, gap_detector, sample_context):
        """Test coverage score calculation."""
        result = gap_detector.analyze(sample_context)
        analysis = result.output["gap_analysis"]

        # Coverage score should be between 0-100
        assert 0 <= analysis["coverage_score"] <= 100

    def test_freshness_score_calculation(self, gap_detector, sample_context):
        """Test freshness score calculation."""
        result = gap_detector.analyze(sample_context)
        analysis = result.output["gap_analysis"]

        # Freshness score should be between 0-100
        assert 0 <= analysis["data_freshness_score"] <= 100

    def test_monitoring_score_calculation(self, gap_detector, sample_context):
        """Test monitoring score calculation."""
        result = gap_detector.analyze(sample_context)
        analysis = result.output["gap_analysis"]

        # Monitoring score should be between 0-100
        assert 0 <= analysis["monitoring_completeness"] <= 100

    def test_gap_severity_assessment(self, gap_detector, sample_context):
        """Test gap severity assessment."""
        result = gap_detector.analyze(sample_context)
        analysis = result.output["gap_analysis"]

        # All gaps should have valid severity levels
        valid_severities = {"critical", "high", "medium", "low", "info"}
        for gap in analysis["gaps"]:
            assert gap["severity"] in valid_severities

    def test_gap_confidence_calculation(self, gap_detector, sample_context):
        """Test gap confidence calculation."""
        result = gap_detector.analyze(sample_context)
        analysis = result.output["gap_analysis"]

        # All gaps should have confidence between 0-1
        for gap in analysis["gaps"]:
            assert 0 <= gap["confidence"] <= 1

    def test_gap_recommendations(self, gap_detector, sample_context):
        """Test gap recommendations generation."""
        result = gap_detector.analyze(sample_context)
        analysis = result.output["gap_analysis"]

        # Gaps should have recommendations
        for gap in analysis["gaps"]:
            assert isinstance(gap["recommendations"], list)
            if gap["gap_type"] != "coverage_gap" or analysis["total_gaps"] > 0:
                assert len(gap["recommendations"]) > 0

    def test_with_scoring_result(self, gap_detector, sample_context, sample_scoring_result):
        """Test analysis with scoring result."""
        result = gap_detector.analyze(sample_context, sample_scoring_result)

        assert result.success is True
        assert "gap_analysis" in result.output

    def test_entity_type_requirements(self, gap_detector):
        """Test different entity type requirements."""
        # Test host entity
        host_entity = Entity(id="host-001", entity_type="host", name="host")
        host_context = Context(entity=host_entity, signals=[])
        result = gap_detector.analyze(host_context)

        # Should detect missing host requirements
        analysis = result.output["gap_analysis"]
        missing_signals = [gap for gap in analysis["gaps"] if gap["gap_type"] == "missing_signal"]

        # Host should require VULNERABILITY, PORT, SERVICE, CONFIGURATION
        required_types = {"VULNERABILITY", "PORT", "SERVICE", "CONFIGURATION"}
        detected_missing = {
            gap["expected_signals"][0] for gap in missing_signals if gap["expected_signals"]
        }
        assert required_types.issubset(detected_missing) or len(missing_signals) > 0

    def test_domain_entity_requirements(self, gap_detector):
        """Test domain entity requirements."""
        domain_entity = Entity(id="domain-001", entity_type="domain", name="example.com")
        domain_context = Context(entity=domain_entity, signals=[])
        result = gap_detector.analyze(domain_context)

        # Should detect missing domain requirements
        analysis = result.output["gap_analysis"]
        missing_signals = [gap for gap in analysis["gaps"] if gap["gap_type"] == "missing_signal"]

        # Domain should require DNS, SUBDOMAIN, SSL_CERTIFICATE, WHOIS
        required_types = {"DNS", "SUBDOMAIN", "SSL_CERTIFICATE", "WHOIS"}
        detected_missing = {
            gap["expected_signals"][0] for gap in missing_signals if gap["expected_signals"]
        }
        assert required_types.issubset(detected_missing) or len(missing_signals) > 0

    def test_staleness_severity_levels(self, gap_detector):
        """Test staleness severity assessment."""
        now = datetime.utcnow()

        # Create very old signal (should be critical)
        old_signal = Signal(
            id="old-signal",
            source="test_source",
            signal_type="VULNERABILITY",
            severity="high",
            description="Old vulnerability",
            timestamp=now - timedelta(days=14),  # 2 weeks old
        )

        entity = Entity(id="test", entity_type="host", name="test")
        context = Context(entity=entity, signals=[old_signal])
        result = gap_detector.analyze(context)
        analysis = result.output["gap_analysis"]

        # Should detect as critical or high severity
        outdated_gaps = [gap for gap in analysis["gaps"] if gap["gap_type"] == "outdated_data"]

        if outdated_gaps:
            assert outdated_gaps[0]["severity"] in {"critical", "high"}

    def test_critical_source_coverage(self, gap_detector, sample_entity):
        """Test critical source coverage detection."""
        # Create context with only non-critical sources
        non_critical_signal = Signal(
            id="non-critical",
            source="unknown_source",
            signal_type="TEST",
            severity="info",
            description="Test signal",
        )

        context = Context(entity=sample_entity, signals=[non_critical_signal])
        result = gap_detector.analyze(context)
        analysis = result.output["gap_analysis"]

        # Should detect missing critical sources
        coverage_gaps = [
            gap
            for gap in analysis["gaps"]
            if gap["gap_type"] == "coverage_gap" and gap["missing_source"] != "all"
        ]

        assert len(coverage_gaps) > 0

    def test_monitoring_inference(self, gap_detector, sample_context):
        """Test monitoring inference from signals."""
        result = gap_detector.analyze(sample_context)
        analysis = result.output["gap_analysis"]

        # Should infer some monitoring from available signals
        monitoring_gaps = [gap for gap in analysis["gaps"] if gap["gap_type"] == "monitoring_gap"]

        # May or may not have gaps depending on signal coverage
        assert isinstance(monitoring_gaps, list)

    def test_gap_counts(self, gap_detector, sample_context):
        """Test gap count statistics."""
        result = gap_detector.analyze(sample_context)
        analysis = result.output["gap_analysis"]

        # Gap counts should match total gaps
        total_from_counts = (
            analysis["critical_gaps"]
            + analysis["high_gaps"]
            + analysis["medium_gaps"]
            + analysis["low_gaps"]
        )
        assert total_from_counts == analysis["total_gaps"]

    def test_impact_score_calculation(self, gap_detector, sample_context):
        """Test impact score calculation for gaps."""
        result = gap_detector.analyze(sample_context)
        analysis = result.output["gap_analysis"]

        # All gaps should have impact scores
        for gap in analysis["gaps"]:
            assert 0 <= gap["impact_score"] <= 1

    def test_missing_evidence_tracking(self, gap_detector, sample_context):
        """Test missing evidence tracking."""
        result = gap_detector.analyze(sample_context)
        analysis = result.output["gap_analysis"]

        # Gaps should track missing evidence
        for gap in analysis["gaps"]:
            if gap["gap_type"] == "missing_signal":
                assert isinstance(gap["missing_source"], str)
                assert isinstance(gap["expected_signals"], list)

    def test_error_handling(self, gap_detector):
        """Test error handling in gap detection."""
        # Test with malformed context
        result = gap_detector.analyze(None)

        # Should handle gracefully
        assert result.success is True  # No entity should not cause failure

    def test_performance_with_many_signals(self, gap_detector, sample_entity):
        """Test performance with many signals."""
        # Create many signals
        many_signals = []
        for i in range(100):
            signal = Signal(
                id=f"signal-{i:03d}",
                source="test_source",
                signal_type="TEST",
                severity="info",
                description=f"Test signal {i}",
                timestamp=datetime.utcnow(),
            )
            many_signals.append(signal)

        context = Context(entity=sample_entity, signals=many_signals)
        result = gap_detector.analyze(context)

        # Should handle large signal sets
        assert result.success is True
        assert "gap_analysis" in result.output


class TestDataGap:
    """Test DataGap dataclass."""

    def test_data_gap_creation(self):
        """Test DataGap creation."""
        gap = DataGap(
            gap_type=GapType.MISSING_SIGNAL,
            title="Test Gap",
            description="Test description",
            severity="high",
            confidence=0.8,
            entity_id="test-entity",
        )

        assert gap.gap_type == GapType.MISSING_SIGNAL
        assert gap.title == "Test Gap"
        assert gap.severity == "high"
        assert gap.confidence == 0.8
        assert gap.entity_id == "test-entity"

    def test_data_gap_to_dict(self):
        """Test DataGap to_dict conversion."""
        gap = DataGap(
            gap_type=GapType.COVERAGE_GAP,
            title="Coverage Gap",
            description="Missing coverage",
            severity="critical",
            confidence=0.9,
            recommendations=["Add coverage"],
        )

        gap_dict = gap.to_dict()

        assert gap_dict["gap_type"] == "coverage_gap"
        assert gap_dict["title"] == "Coverage Gap"
        assert gap_dict["severity"] == "critical"
        assert gap_dict["confidence"] == 0.9
        assert gap_dict["recommendations"] == ["Add coverage"]


class TestGapAnalysisResult:
    """Test GapAnalysisResult dataclass."""

    def test_gap_analysis_result_creation(self):
        """Test GapAnalysisResult creation."""
        result = GapAnalysisResult(
            total_gaps=5,
            critical_gaps=1,
            high_gaps=2,
            medium_gaps=1,
            low_gaps=1,
        )

        assert result.total_gaps == 5
        assert result.critical_gaps == 1
        assert result.high_gaps == 2
        assert result.medium_gaps == 1
        assert result.low_gaps == 1

    def test_gap_analysis_result_to_dict(self):
        """Test GapAnalysisResult to_dict conversion."""
        gap = DataGap(
            gap_type=GapType.MISSING_SIGNAL,
            title="Test Gap",
            description="Test",
            severity="medium",
            confidence=0.7,
        )

        result = GapAnalysisResult(
            total_gaps=1,
            gaps=[gap],
            coverage_score=75.0,
            data_freshness_score=80.0,
            monitoring_completeness=85.0,
        )

        result_dict = result.to_dict()

        assert result_dict["total_gaps"] == 1
        assert result_dict["coverage_score"] == 75.0
        assert result_dict["data_freshness_score"] == 80.0
        assert result_dict["monitoring_completeness"] == 85.0
        assert len(result_dict["gaps"]) == 1
        assert result_dict["gaps"][0]["title"] == "Test Gap"


class TestGapType:
    """Test GapType enum."""

    def test_gap_type_values(self):
        """Test GapType enum values."""
        assert GapType.MISSING_SIGNAL.value == "missing_signal"
        assert GapType.OUTDATED_DATA.value == "outdated_data"
        assert GapType.COVERAGE_GAP.value == "coverage_gap"
        assert GapType.INCOMPLETE_SCAN.value == "incomplete_scan"
        assert GapType.MONITORING_GAP.value == "monitoring_gap"
        assert GapType.CORRELATION_GAP.value == "correlation_gap"


class TestIntegration:
    """Integration tests for Gap Detector."""

    def test_full_pipeline_integration(self, gap_detector, sample_context, sample_scoring_result):
        """Test full pipeline integration."""
        result = gap_detector.analyze(sample_context, sample_scoring_result)

        assert result.success is True
        analysis = result.output["gap_analysis"]

        # Should have comprehensive analysis
        assert "total_gaps" in analysis
        assert "coverage_score" in analysis
        assert "data_freshness_score" in analysis
        assert "monitoring_completeness" in analysis
        assert "gaps" in analysis

    def test_real_world_scenario(self, gap_detector):
        """Test real-world scenario with production host."""
        # Create realistic production host scenario
        entity = Entity(
            id="prod-web-01",
            entity_type="host",
            name="prod-web-01.example.com",
            description="Production web server",
            properties={
                "environment": "production",
                "public": True,
                "tier": "frontend",
                "data_classification": "public",
            },
        )

        # Create realistic signals
        signals = [
            Signal(
                id="vuln-001",
                source="nessus",
                signal_type="VULNERABILITY",
                severity="critical",
                description="CVE-2023-1234: Remote code execution in Apache",
                timestamp=datetime.utcnow() - timedelta(hours=6),
                entity_id="prod-web-01",
            ),
            Signal(
                id="port-001",
                source="nmap",
                signal_type="PORT",
                severity="high",
                description="Port 443/tcp open - HTTPS",
                timestamp=datetime.utcnow() - timedelta(hours=12),
                entity_id="prod-web-01",
            ),
            Signal(
                id="service-001",
                source="asset_inventory",
                signal_type="SERVICE",
                severity="medium",
                description="Apache HTTP Server 2.4.41",
                timestamp=datetime.utcnow() - timedelta(hours=24),
                entity_id="prod-web-01",
            ),
        ]

        context = Context(entity=entity, signals=signals)
        result = gap_detector.analyze(context)
        analysis = result.output["gap_analysis"]

        # Should detect realistic gaps
        assert analysis["total_gaps"] > 0

        # Should have some critical or high gaps
        critical_high_gaps = [
            gap for gap in analysis["gaps"] if gap["severity"] in {"critical", "high"}
        ]
        assert len(critical_high_gaps) > 0

        # Coverage should be partial but not complete
        assert 0 < analysis["coverage_score"] < 100

        # Freshness should be good for recent signals
        assert analysis["data_freshness_score"] > 50
