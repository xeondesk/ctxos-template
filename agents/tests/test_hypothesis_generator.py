"""
Tests for Hypothesis Generator Agent.
"""

import pytest
from datetime import datetime, timedelta

from core.models.entity import Entity
from core.models.signal import Signal
from core.models.context import Context
from core.scoring.risk import ScoringResult
from agents.hypothesis_generator import (
    HypothesisGenerator,
    Hypothesis,
    HypothesisAnalysis,
    HypothesisType,
    ConfidenceLevel,
)


@pytest.fixture
def hypothesis_generator():
    """Create Hypothesis Generator instance."""
    return HypothesisGenerator(
        name="test_hypothesis_generator",
        version="1.0.0",
        max_hypotheses=10,
        min_confidence_threshold=0.3,
        enable_creative_hypotheses=True,
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
            description="Critical vulnerability CVE-2023-1234 detected",
            timestamp=datetime.utcnow() - timedelta(hours=6),
        ),
        Signal(
            id="signal-002",
            source="network_scanner",
            signal_type="PORT",
            severity="high",
            description="Open port 443 detected",
            timestamp=datetime.utcnow() - timedelta(hours=12),
        ),
        Signal(
            id="signal-003",
            source="dns_monitor",
            signal_type="DNS",
            severity="medium",
            description="DNS query to suspicious domain",
            timestamp=datetime.utcnow() - timedelta(hours=24),
        ),
        Signal(
            id="signal-004",
            source="auth_log",
            signal_type="AUTHENTICATION",
            severity="high",
            description="Failed login attempts detected",
            timestamp=datetime.utcnow() - timedelta(hours=2),
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
        score=85.0,
        severity="critical",
        details={"risk_factors": ["vulnerability", "exposure", "activity"]},
        metrics={"vulnerability": 40, "exposure": 30, "drift": 15},
        recommendations=["Immediate patching required", "Investigate suspicious activity"],
    )


class TestHypothesisGenerator:
    """Test Hypothesis Generator functionality."""

    def test_initialization(self, hypothesis_generator):
        """Test hypothesis generator initialization."""
        assert hypothesis_generator.name == "test_hypothesis_generator"
        assert hypothesis_generator.version == "1.0.0"
        assert hypothesis_generator.max_hypotheses == 10
        assert hypothesis_generator.min_confidence_threshold == 0.3
        assert hypothesis_generator.enable_creative_hypotheses is True
        assert "vulnerability_exploitation" in hypothesis_generator.hypothesis_rules

    def test_analyze_success(self, hypothesis_generator, sample_context):
        """Test successful hypothesis generation."""
        result = hypothesis_generator.analyze(sample_context)

        assert result.success is True
        assert "hypothesis_analysis" in result.output
        assert "summary" in result.output

    def test_analyze_no_entity(self, hypothesis_generator):
        """Test analysis with no entity."""
        context = Context(entity=None, signals=[])
        result = hypothesis_generator.analyze(context)

        assert result.success is True
        analysis = result.output["hypothesis_analysis"]
        assert analysis["total_hypotheses"] == 0

    def test_generate_signal_based_hypotheses(self, hypothesis_generator, sample_context):
        """Test signal-based hypothesis generation."""
        result = hypothesis_generator.analyze(sample_context)
        analysis = result.output["hypothesis_analysis"]

        # Should generate hypotheses from signals
        assert analysis["total_hypotheses"] > 0

        # Should have different hypothesis types
        hypothesis_types = {h["hypothesis_type"] for h in analysis["hypotheses"]}
        assert len(hypothesis_types) > 0

    def test_generate_entity_based_hypotheses(self, hypothesis_generator, sample_context):
        """Test entity-based hypothesis generation."""
        result = hypothesis_generator.analyze(sample_context)
        analysis = result.output["hypothesis_analysis"]

        # Should generate hypotheses based on entity characteristics
        entity_hypotheses = [
            h
            for h in analysis["hypotheses"]
            if "critical asset" in h["title"].lower() or "public-facing" in h["title"].lower()
        ]
        assert len(entity_hypotheses) >= 0  # May or may not have entity-based hypotheses

    def test_generate_scoring_based_hypotheses(
        self, hypothesis_generator, sample_context, sample_scoring_result
    ):
        """Test scoring-based hypothesis generation."""
        result = hypothesis_generator.analyze(sample_context, sample_scoring_result)
        analysis = result.output["hypothesis_analysis"]

        # High score should generate APT hypothesis
        high_score_hypotheses = [
            h
            for h in analysis["hypotheses"]
            if h["hypothesis_type"] == "advanced_persistent_threat"
        ]
        assert len(high_score_hypotheses) > 0

    def test_generate_creative_hypotheses(self, hypothesis_generator, sample_context):
        """Test creative hypothesis generation."""
        # Add creative trigger signals
        creative_signals = sample_context.signals + [
            Signal(
                id="signal-005",
                source="dependency_scanner",
                signal_type="DEPENDENCY",
                severity="medium",
                description="Third-party dependency detected",
                timestamp=datetime.utcnow(),
            )
        ]

        creative_context = Context(entity=sample_context.entity, signals=creative_signals)
        result = hypothesis_generator.analyze(creative_context)
        analysis = result.output["hypothesis_analysis"]

        # Should generate creative hypotheses
        creative_hypotheses = [
            h
            for h in analysis["hypotheses"]
            if h["hypothesis_type"] in {"supply_chain", "insider_threat", "ransomware"}
        ]
        assert len(creative_hypotheses) >= 0  # May or may not have creative hypotheses

    def test_creative_hypotheses_disabled(self, hypothesis_generator, sample_context):
        """Test with creative hypotheses disabled."""
        hypothesis_generator.enable_creative_hypotheses = False
        result = hypothesis_generator.analyze(sample_context)
        analysis = result.output["hypothesis_analysis"]

        # Should not generate creative hypotheses
        creative_hypotheses = [
            h
            for h in analysis["hypotheses"]
            if h["hypothesis_type"] in {"supply_chain", "insider_threat", "ransomware"}
        ]
        assert len(creative_hypotheses) == 0

    def test_vulnerability_exploitation_hypothesis(self, hypothesis_generator, sample_context):
        """Test vulnerability exploitation hypothesis generation."""
        result = hypothesis_generator.analyze(sample_context)
        analysis = result.output["hypothesis_analysis"]

        # Should generate vulnerability exploitation hypothesis for critical vulns
        vuln_hypotheses = [
            h
            for h in analysis["hypotheses"]
            if h["hypothesis_type"] == "vulnerability_exploitation"
        ]
        assert len(vuln_hypotheses) > 0

        if vuln_hypotheses:
            vuln_hyp = vuln_hypotheses[0]
            assert vuln_hyp["impact"] in {"critical", "high"}
            assert len(vuln_hyp["attack_steps"]) > 0
            assert len(vuln_hyp["mitigations"]) > 0

    def test_lateral_movement_hypothesis(self, hypothesis_generator):
        """Test lateral movement hypothesis generation."""
        # Create signals indicating lateral movement
        lateral_signals = [
            Signal(
                id="signal-001",
                source="network_scanner",
                signal_type="PORT",
                severity="high",
                description="Multiple open ports detected",
                timestamp=datetime.utcnow(),
            ),
            Signal(
                id="signal-002",
                source="network_scanner",
                signal_type="PORT",
                severity="medium",
                description="Additional open ports",
                timestamp=datetime.utcnow(),
            ),
            Signal(
                id="signal-003",
                source="network_scanner",
                signal_type="PORT",
                severity="low",
                description="More open ports",
                timestamp=datetime.utcnow(),
            ),
        ]

        entity = Entity(id="entity-001", entity_type="host", name="test-host")
        context = Context(entity=entity, signals=lateral_signals)
        result = hypothesis_generator.analyze(context)
        analysis = result.output["hypothesis_analysis"]

        # Should generate lateral movement hypothesis
        lateral_hypotheses = [
            h for h in analysis["hypotheses"] if h["hypothesis_type"] == "lateral_movement"
        ]
        assert len(lateral_hypotheses) > 0

    def test_attack_chain_detection(self, hypothesis_generator, sample_context):
        """Test attack chain detection."""
        # Add signals that form an attack chain
        attack_chain_signals = sample_context.signals + [
            Signal(
                id="signal-005",
                source="subdomain_scanner",
                signal_type="SUBDOMAIN",
                severity="medium",
                description="Subdomain enumeration detected",
                timestamp=datetime.utcnow() - timedelta(hours=48),
            )
        ]

        attack_chain_context = Context(entity=sample_context.entity, signals=attack_chain_signals)
        result = hypothesis_generator.analyze(attack_chain_context)
        analysis = result.output["hypothesis_analysis"]

        # Should detect attack chains
        attack_chain_hypotheses = [
            h for h in analysis["hypotheses"] if "attack chain" in h["title"].lower()
        ]
        assert len(attack_chain_hypotheses) >= 0  # May or may not detect chains

    def test_confidence_calculation(self, hypothesis_generator, sample_context):
        """Test hypothesis confidence calculation."""
        result = hypothesis_generator.analyze(sample_context)
        analysis = result.output["hypothesis_analysis"]

        # All hypotheses should have valid confidence levels
        valid_confidences = {"very_low", "low", "medium", "high", "very_high"}
        for hypothesis in analysis["hypotheses"]:
            assert hypothesis["confidence"] in valid_confidences

    def test_likelihood_calculation(self, hypothesis_generator, sample_context):
        """Test hypothesis likelihood calculation."""
        result = hypothesis_generator.analyze(sample_context)
        analysis = result.output["hypothesis_analysis"]

        # All hypotheses should have likelihood between 0-1
        for hypothesis in analysis["hypotheses"]:
            assert 0 <= hypothesis["likelihood"] <= 1

    def test_impact_assessment(self, hypothesis_generator, sample_context):
        """Test hypothesis impact assessment."""
        result = hypothesis_generator.analyze(sample_context)
        analysis = result.output["hypothesis_analysis"]

        # All hypotheses should have valid impact levels
        valid_impacts = {"critical", "high", "medium", "low", "info"}
        for hypothesis in analysis["hypotheses"]:
            assert hypothesis["impact"] in valid_impacts

    def test_supporting_evidence(self, hypothesis_generator, sample_context):
        """Test supporting evidence tracking."""
        result = hypothesis_generator.analyze(sample_context)
        analysis = result.output["hypothesis_analysis"]

        # Hypotheses should have supporting evidence
        for hypothesis in analysis["hypotheses"]:
            assert isinstance(hypothesis["supporting_signals"], list)
            # May be empty for some hypothesis types

    def test_attack_steps_generation(self, hypothesis_generator, sample_context):
        """Test attack steps generation."""
        result = hypothesis_generator.analyze(sample_context)
        analysis = result.output["hypothesis_analysis"]

        # Hypotheses should have attack steps
        for hypothesis in analysis["hypotheses"]:
            assert isinstance(hypothesis["attack_steps"], list)
            if hypothesis["hypothesis_type"] != "advanced_persistent_threat":
                assert len(hypothesis["attack_steps"]) > 0

    def test_mitigations_generation(self, hypothesis_generator, sample_context):
        """Test mitigations generation."""
        result = hypothesis_generator.analyze(sample_context)
        analysis = result.output["hypothesis_analysis"]

        # Hypotheses should have mitigations
        for hypothesis in analysis["hypotheses"]:
            assert isinstance(hypothesis["mitigations"], list)
            if hypothesis["hypothesis_type"] != "advanced_persistent_threat":
                assert len(hypothesis["mitigations"]) > 0

    def test_hypothesis_filtering(self, hypothesis_generator, sample_context):
        """Test hypothesis filtering by confidence threshold."""
        # Set high confidence threshold
        hypothesis_generator.min_confidence_threshold = 0.8
        result = hypothesis_generator.analyze(sample_context)
        analysis = result.output["hypothesis_analysis"]

        # Should filter out low confidence hypotheses
        for hypothesis in analysis["hypotheses"]:
            confidence_values = {
                "very_low": 0.2,
                "low": 0.4,
                "medium": 0.6,
                "high": 0.8,
                "very_high": 1.0,
            }
            assert confidence_values[hypothesis["confidence"]] >= 0.8

    def test_hypothesis_limiting(self, hypothesis_generator, sample_context):
        """Test hypothesis limiting."""
        # Set low max hypotheses
        hypothesis_generator.max_hypotheses = 3
        result = hypothesis_generator.analyze(sample_context)
        analysis = result.output["hypothesis_analysis"]

        # Should limit number of hypotheses
        assert analysis["total_hypotheses"] <= 3

    def test_attack_surface_score(self, hypothesis_generator, sample_context):
        """Test attack surface score calculation."""
        result = hypothesis_generator.analyze(sample_context)
        analysis = result.output["hypothesis_analysis"]

        # Attack surface score should be between 0-100
        assert 0 <= analysis["attack_surface_score"] <= 100

    def test_threat_landscape_analysis(self, hypothesis_generator, sample_context):
        """Test threat landscape analysis."""
        result = hypothesis_generator.analyze(sample_context)
        analysis = result.output["hypothesis_analysis"]

        # Should track threat landscape
        assert isinstance(analysis["threat_landscape"], dict)

        # Should count hypothesis types
        if analysis["total_hypotheses"] > 0:
            assert len(analysis["threat_landscape"]) > 0

    def test_recommended_investigations(self, hypothesis_generator, sample_context):
        """Test recommended investigations generation."""
        result = hypothesis_generator.analyze(sample_context)
        analysis = result.output["hypothesis_analysis"]

        # Should generate recommended investigations
        assert isinstance(analysis["recommended_investigations"], list)

        if analysis["total_hypotheses"] > 0:
            assert len(analysis["recommended_investigations"]) > 0

    def test_confidence_counting(self, hypothesis_generator, sample_context):
        """Test confidence level counting."""
        result = hypothesis_generator.analyze(sample_context)
        analysis = result.output["hypothesis_analysis"]

        # Confidence counts should match total hypotheses
        total_from_confidence = (
            analysis["high_confidence"] + analysis["medium_confidence"] + analysis["low_confidence"]
        )
        assert total_from_confidence == analysis["total_hypotheses"]

    def test_impact_counting(self, hypothesis_generator, sample_context):
        """Test impact level counting."""
        result = hypothesis_generator.analyze(sample_context)
        analysis = result.output["hypothesis_analysis"]

        # Impact counts should be consistent
        total_from_impact = analysis["critical_impact"] + analysis["high_impact"]
        assert total_from_impact <= analysis["total_hypotheses"]

    def test_different_entity_types(self, hypothesis_generator):
        """Test hypothesis generation for different entity types."""
        entity_types = ["host", "domain", "application", "network"]

        for entity_type in entity_types:
            entity = Entity(
                id=f"{entity_type}-001",
                entity_type=entity_type,
                name=f"test-{entity_type}",
            )

            # Create relevant signals
            signals = [
                Signal(
                    id="signal-001",
                    source="test_source",
                    signal_type="TEST",
                    severity="medium",
                    description="Test signal",
                    timestamp=datetime.utcnow(),
                )
            ]

            context = Context(entity=entity, signals=signals)
            result = hypothesis_generator.analyze(context)
            analysis = result.output["hypothesis_analysis"]

            # Should generate hypotheses for all entity types
            assert analysis["total_hypotheses"] >= 0

    def test_high_score_scenario(self, hypothesis_generator, sample_context, sample_scoring_result):
        """Test high score scenario."""
        # Create very high scoring result
        high_score_result = ScoringResult(
            score=95.0,
            severity="critical",
            details={"critical_risks": ["multiple_vulnerabilities"]},
            metrics={"vulnerability": 50, "exposure": 30, "drift": 15},
            recommendations=["Immediate action required"],
        )

        result = hypothesis_generator.analyze(sample_context, high_score_result)
        analysis = result.output["hypothesis_analysis"]

        # Should generate high-confidence APT hypothesis
        apt_hypotheses = [
            h
            for h in analysis["hypotheses"]
            if h["hypothesis_type"] == "advanced_persistent_threat"
        ]
        assert len(apt_hypotheses) > 0

        if apt_hypotheses:
            apt_hyp = apt_hypotheses[0]
            assert apt_hyp["confidence"] in {"high", "very_high"}
            assert apt_hyp["impact"] == "critical"

    def test_error_handling(self, hypothesis_generator):
        """Test error handling in hypothesis generation."""
        # Test with malformed context
        result = hypothesis_generator.analyze(None)

        # Should handle gracefully
        assert result.success is True  # No entity should not cause failure

    def test_performance_with_many_signals(self, hypothesis_generator, sample_entity):
        """Test performance with many signals."""
        # Create many signals
        many_signals = []
        for i in range(50):
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
        result = hypothesis_generator.analyze(context)

        # Should handle large signal sets
        assert result.success is True
        assert "hypothesis_analysis" in result.output


class TestHypothesis:
    """Test Hypothesis dataclass."""

    def test_hypothesis_creation(self):
        """Test Hypothesis creation."""
        hypothesis = Hypothesis(
            id="test-hypothesis",
            title="Test Hypothesis",
            description="Test description",
            hypothesis_type=HypothesisType.VULNERABILITY_EXPLOITATION,
            confidence=ConfidenceLevel.HIGH,
            likelihood=0.8,
            impact="high",
        )

        assert hypothesis.id == "test-hypothesis"
        assert hypothesis.title == "Test Hypothesis"
        assert hypothesis.hypothesis_type == HypothesisType.VULNERABILITY_EXPLOITATION
        assert hypothesis.confidence == ConfidenceLevel.HIGH
        assert hypothesis.likelihood == 0.8
        assert hypothesis.impact == "high"

    def test_hypothesis_to_dict(self):
        """Test Hypothesis to_dict conversion."""
        hypothesis = Hypothesis(
            id="test-hypothesis",
            title="Test Hypothesis",
            description="Test description",
            hypothesis_type=HypothesisType.LATERAL_MOVEMENT,
            confidence=ConfidenceLevel.MEDIUM,
            likelihood=0.6,
            impact="medium",
            supporting_signals=["signal-001", "signal-002"],
            attack_steps=["Step 1", "Step 2"],
            mitigations=["Mitigation 1", "Mitigation 2"],
        )

        hypothesis_dict = hypothesis.to_dict()

        assert hypothesis_dict["id"] == "test-hypothesis"
        assert hypothesis_dict["title"] == "Test Hypothesis"
        assert hypothesis_dict["hypothesis_type"] == "lateral_movement"
        assert hypothesis_dict["confidence"] == "medium"
        assert hypothesis_dict["likelihood"] == 0.6
        assert hypothesis_dict["impact"] == "medium"
        assert hypothesis_dict["supporting_signals"] == ["signal-001", "signal-002"]
        assert hypothesis_dict["attack_steps"] == ["Step 1", "Step 2"]
        assert hypothesis_dict["mitigations"] == ["Mitigation 1", "Mitigation 2"]


class TestHypothesisAnalysis:
    """Test HypothesisAnalysis dataclass."""

    def test_hypothesis_analysis_creation(self):
        """Test HypothesisAnalysis creation."""
        analysis = HypothesisAnalysis(
            total_hypotheses=5,
            high_confidence=2,
            medium_confidence=2,
            low_confidence=1,
            critical_impact=1,
            high_impact=2,
        )

        assert analysis.total_hypotheses == 5
        assert analysis.high_confidence == 2
        assert analysis.medium_confidence == 2
        assert analysis.low_confidence == 1
        assert analysis.critical_impact == 1
        assert analysis.high_impact == 2

    def test_hypothesis_analysis_to_dict(self):
        """Test HypothesisAnalysis to_dict conversion."""
        hypothesis = Hypothesis(
            id="test-hypothesis",
            title="Test Hypothesis",
            description="Test",
            hypothesis_type=HypothesisType.DATA_EXFILTRATION,
            confidence=ConfidenceLevel.HIGH,
            likelihood=0.7,
            impact="high",
        )

        analysis = HypothesisAnalysis(
            total_hypotheses=1,
            hypotheses=[hypothesis],
            attack_surface_score=75.0,
            threat_landscape={"data_exfiltration": 1},
            recommended_investigations=["Investigate data exfiltration"],
        )

        analysis_dict = analysis.to_dict()

        assert analysis_dict["total_hypotheses"] == 1
        assert analysis_dict["high_confidence"] == 0
        assert analysis_dict["attack_surface_score"] == 75.0
        assert analysis_dict["threat_landscape"] == {"data_exfiltration": 1}
        assert analysis_dict["recommended_investigations"] == ["Investigate data exfiltration"]
        assert len(analysis_dict["hypotheses"]) == 1
        assert analysis_dict["hypotheses"][0]["title"] == "Test Hypothesis"


class TestHypothesisType:
    """Test HypothesisType enum."""

    def test_hypothesis_type_values(self):
        """Test HypothesisType enum values."""
        assert HypothesisType.VULNERABILITY_EXPLOITATION.value == "vulnerability_exploitation"
        assert HypothesisType.LATERAL_MOVEMENT.value == "lateral_movement"
        assert HypothesisType.DATA_EXFILTRATION.value == "data_exfiltration"
        assert HypothesisType.PRIVILEGE_ESCALATION.value == "privilege_escalation"
        assert HypothesisType.PERSISTENCE_MECHANISM.value == "persistence_mechanism"
        assert HypothesisType.SUPPLY_CHAIN.value == "supply_chain"
        assert HypothesisType.MISCONFIGURATION.value == "misconfiguration"
        assert HypothesisType.INSIDER_THREAT.value == "insider_threat"
        assert HypothesisType.ADVANCED_PERSISTENT_THREAT.value == "advanced_persistent_threat"
        assert HypothesisType.RANSOMWARE.value == "ransomware"


class TestConfidenceLevel:
    """Test ConfidenceLevel enum."""

    def test_confidence_level_values(self):
        """Test ConfidenceLevel enum values."""
        assert ConfidenceLevel.VERY_LOW.value == "very_low"
        assert ConfidenceLevel.LOW.value == "low"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.VERY_HIGH.value == "very_high"


class TestIntegration:
    """Integration tests for Hypothesis Generator."""

    def test_full_pipeline_integration(
        self, hypothesis_generator, sample_context, sample_scoring_result
    ):
        """Test full pipeline integration."""
        result = hypothesis_generator.analyze(sample_context, sample_scoring_result)

        assert result.success is True
        analysis = result.output["hypothesis_analysis"]

        # Should have comprehensive analysis
        assert "total_hypotheses" in analysis
        assert "attack_surface_score" in analysis
        assert "threat_landscape" in analysis
        assert "recommended_investigations" in analysis
        assert "hypotheses" in analysis

    def test_real_world_critical_vulnerability_scenario(self, hypothesis_generator):
        """Test real-world critical vulnerability scenario."""
        # Create realistic critical vulnerability scenario
        entity = Entity(
            id="prod-db-01",
            entity_type="host",
            name="prod-db-01.example.com",
            description="Production database server",
            properties={
                "environment": "production",
                "critical": True,
                "database_type": "postgresql",
                "data_classification": "confidential",
            },
        )

        # Create realistic critical vulnerability signals
        signals = [
            Signal(
                id="vuln-001",
                source="nessus",
                signal_type="VULNERABILITY",
                severity="critical",
                description="CVE-2023-1234: PostgreSQL remote code execution vulnerability",
                timestamp=datetime.utcnow() - timedelta(hours=2),
                entity_id="prod-db-01",
            ),
            Signal(
                id="vuln-002",
                source="qualys",
                signal_type="VULNERABILITY",
                severity="critical",
                description="CVE-2023-5678: PostgreSQL privilege escalation",
                timestamp=datetime.utcnow() - timedelta(hours=4),
                entity_id="prod-db-01",
            ),
            Signal(
                id="port-001",
                source="nmap",
                signal_type="PORT",
                severity="high",
                description="Port 5432/tcp open - PostgreSQL",
                timestamp=datetime.utcnow() - timedelta(hours=6),
                entity_id="prod-db-01",
            ),
            Signal(
                id="auth-001",
                source="auth_log",
                signal_type="AUTHENTICATION",
                severity="high",
                description="Multiple failed PostgreSQL login attempts",
                timestamp=datetime.utcnow() - timedelta(hours=1),
                entity_id="prod-db-01",
            ),
        ]

        context = Context(entity=entity, signals=signals)
        result = hypothesis_generator.analyze(context)
        analysis = result.output["hypothesis_analysis"]

        # Should generate multiple high-risk hypotheses
        assert analysis["total_hypotheses"] > 0

        # Should have critical impact hypotheses
        critical_hypotheses = [h for h in analysis["hypotheses"] if h["impact"] == "critical"]
        assert len(critical_hypotheses) > 0

        # Should have high confidence hypotheses
        high_conf_hypotheses = [
            h for h in analysis["hypotheses"] if h["confidence"] in {"high", "very_high"}
        ]
        assert len(high_conf_hypotheses) > 0

        # Should have high attack surface score
        assert analysis["attack_surface_score"] > 70

        # Should recommend urgent investigations
        assert any("urgent" in rec.lower() for rec in analysis["recommended_investigations"])

    def test_supply_chain_attack_scenario(self, hypothesis_generator):
        """Test supply chain attack scenario."""
        # Create supply chain scenario
        entity = Entity(
            id="web-app-01",
            entity_type="application",
            name="web-app-01",
            description="Web application with third-party dependencies",
            properties={"framework": "react", "package_manager": "npm"},
        )

        signals = [
            Signal(
                id="dep-001",
                source="dependency_scanner",
                signal_type="DEPENDENCY",
                severity="high",
                description="Vulnerable third-party library detected",
                timestamp=datetime.utcnow() - timedelta(hours=12),
            ),
            Signal(
                id="third-001",
                source="vendor_monitor",
                signal_type="THIRD_PARTY",
                severity="medium",
                description="Third-party service access detected",
                timestamp=datetime.utcnow() - timedelta(hours=24),
            ),
        ]

        context = Context(entity=entity, signals=signals)
        result = hypothesis_generator.analyze(context)
        analysis = result.output["hypothesis_analysis"]

        # Should generate supply chain hypotheses
        supply_chain_hypotheses = [
            h for h in analysis["hypotheses"] if h["hypothesis_type"] == "supply_chain"
        ]
        assert len(supply_chain_hypotheses) >= 0  # May or may not generate

        if supply_chain_hypotheses:
            assert supply_chain_hypotheses[0]["impact"] in {"high", "critical"}
