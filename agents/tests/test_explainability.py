"""
Tests for Explainability Agent.
"""

import pytest
from datetime import datetime, timedelta

from core.models.entity import Entity
from core.models.signal import Signal
from core.models.context import Context
from core.scoring.risk import ScoringResult
from agents.explainability import (
    ExplainabilityAgent, ScoreExplanation, ExplainabilityResult,
    ExplanationType, ConfidenceLevel, ExplanationFactor
)


@pytest.fixture
def explainability_agent():
    """Create Explainability Agent instance."""
    return ExplainabilityAgent(
        name="test_explainability_agent",
        version="1.0.0",
        min_factor_weight=0.05,
        max_explanations=5,
        include_comparisons=True,
        temporal_analysis_days=30,
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
            source="config_scanner",
            signal_type="CONFIGURATION",
            severity="medium",
            description="Configuration issue found",
            timestamp=datetime.utcnow() - timedelta(hours=24),
        ),
        Signal(
            id="signal-004",
            source="activity_monitor",
            signal_type="ACTIVITY",
            severity="low",
            description="Unusual activity detected",
            timestamp=datetime.utcnow() - timedelta(hours=48),
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
        metrics={
            "vulnerability": 30,
            "exposure": 25,
            "drift": 15,
            "configuration": 5,
        },
        recommendations=["Patch vulnerabilities", "Reduce exposure"],
    )


class TestExplainabilityAgent:
    """Test Explainability Agent functionality."""
    
    def test_initialization(self, explainability_agent):
        """Test explainability agent initialization."""
        assert explainability_agent.name == "test_explainability_agent"
        assert explainability_agent.version == "1.0.0"
        assert explainability_agent.min_factor_weight == 0.05
        assert explainability_agent.max_explanations == 5
        assert explainability_agent.include_comparisons is True
        assert explainability_agent.temporal_analysis_days == 30
        assert "vulnerability" in explainability_agent.factor_weights
    
    def test_analyze_success(self, explainability_agent, sample_context, sample_scoring_result):
        """Test successful explainability analysis."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        
        assert result.success is True
        assert "explainability_result" in result.output
        assert "summary" in result.output
    
    def test_analyze_no_scoring_result(self, explainability_agent, sample_context):
        """Test analysis with no scoring result."""
        result = explainability_agent.analyze(sample_context)
        
        assert result.success is True
        explainability_result = result.output["explainability_result"]
        assert explainability_result["score"] == 0.0
        assert explainability_result["severity"] == "info"
    
    def test_generate_score_breakdown(self, explainability_agent, sample_context, sample_scoring_result):
        """Test score breakdown explanation generation."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Should have score breakdown explanation
        score_breakdown_explanations = [
            exp for exp in explainability_result["explanations"]
            if exp["explanation_type"] == "score_breakdown"
        ]
        assert len(score_breakdown_explanations) > 0
        
        if score_breakdown_explanations:
            breakdown = score_breakdown_explanations[0]
            assert breakdown["final_score"] == sample_scoring_result.score
            assert breakdown["severity"] == sample_scoring_result.severity
            assert len(breakdown["factors"]) > 0
    
    def test_generate_factor_analysis(self, explainability_agent, sample_context, sample_scoring_result):
        """Test factor analysis explanation generation."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Should have factor analysis explanation
        factor_analysis_explanations = [
            exp for exp in explainability_result["explanations"]
            if exp["explanation_type"] == "factor_analysis"
        ]
        assert len(factor_analysis_explanations) > 0
        
        if factor_analysis_explanations:
            factor_analysis = factor_analysis_explanations[0]
            assert len(factor_analysis["factors"]) > 0
            assert isinstance(factor_analysis["risk_drivers"], list)
    
    def test_generate_root_cause_analysis(self, explainability_agent, sample_context, sample_scoring_result):
        """Test root cause analysis explanation generation."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Should have root cause analysis explanation
        root_cause_explanations = [
            exp for exp in explainability_result["explanations"]
            if exp["explanation_type"] == "root_cause"
        ]
        assert len(root_cause_explanations) > 0
        
        if root_cause_explanations:
            root_cause = root_cause_explanations[0]
            assert len(root_cause["factors"]) > 0
            assert isinstance(root_cause["key_drivers"], list)
    
    def test_generate_temporal_analysis(self, explainability_agent, sample_context, sample_scoring_result):
        """Test temporal analysis explanation generation."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Should have temporal analysis explanation
        temporal_explanations = [
            exp for exp in explainability_result["explanations"]
            if exp["explanation_type"] == "temporal_analysis"
        ]
        assert len(temporal_explanations) > 0
        
        if temporal_explanations:
            temporal = temporal_explanations[0]
            assert isinstance(temporal["temporal_trends"], dict)
    
    def test_generate_comparative_analysis(self, explainability_agent, sample_context, sample_scoring_result):
        """Test comparative analysis explanation generation."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Should have comparative analysis explanation
        comparative_explanations = [
            exp for exp in explainability_result["explanations"]
            if exp["explanation_type"] == "comparative_analysis"
        ]
        assert len(comparative_explanations) > 0
        
        if comparative_explanations:
            comparative = comparative_explanations[0]
            assert isinstance(comparative["comparisons"], dict)
    
    def test_comparative_analysis_disabled(self, explainability_agent, sample_context, sample_scoring_result):
        """Test with comparative analysis disabled."""
        explainability_agent.include_comparisons = False
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Should not have comparative analysis explanation
        comparative_explanations = [
            exp for exp in explainability_result["explanations"]
            if exp["explanation_type"] == "comparative_analysis"
        ]
        assert len(comparative_explanations) == 0
    
    def test_signal_factor_analysis(self, explainability_agent, sample_context, sample_scoring_result):
        """Test signal-based factor analysis."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Should analyze signal factors
        factor_analysis_explanations = [
            exp for exp in explainability_result["explanations"]
            if exp["explanation_type"] == "factor_analysis"
        ]
        
        if factor_analysis_explanations:
            factor_analysis = factor_analysis_explanations[0]
            signal_factors = [
                factor for factor in factor_analysis["factors"]
                if "vulnerability" in factor["name"] or "port" in factor["name"]
            ]
            assert len(signal_factors) > 0
    
    def test_entity_factor_analysis(self, explainability_agent, sample_context, sample_scoring_result):
        """Test entity-based factor analysis."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Should analyze entity factors
        factor_analysis_explanations = [
            exp for exp in explainability_result["explanations"]
            if exp["explanation_type"] == "factor_analysis"
        ]
        
        if factor_analysis_explanations:
            factor_analysis = factor_analysis_explanations[0]
            entity_factors = [
                factor for factor in factor_analysis["factors"]
                if factor["name"] == "entity_type" or factor["name"].startswith("property_")
            ]
            assert len(entity_factors) > 0
    
    def test_root_cause_identification(self, explainability_agent, sample_context, sample_scoring_result):
        """Test root cause identification."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Should identify root causes
        root_cause_explanations = [
            exp for exp in explainability_result["explanations"]
            if exp["explanation_type"] == "root_cause"
        ]
        
        if root_cause_explanations:
            root_cause = root_cause_explanations[0]
            # Should identify critical vulnerabilities as root cause
            critical_vuln_factors = [
                factor for factor in root_cause["factors"]
                if factor["name"] == "critical_vulnerabilities"
            ]
            assert len(critical_vuln_factors) > 0
    
    def test_temporal_trend_analysis(self, explainability_agent, sample_context, sample_scoring_result):
        """Test temporal trend analysis."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Should analyze temporal trends
        temporal_explanations = [
            exp for exp in explainability_result["explanations"]
            if exp["explanation_type"] == "temporal_analysis"
        ]
        
        if temporal_explanations:
            temporal = temporal_explanations[0]
            assert "signal_frequency" in temporal["temporal_trends"]
    
    def test_confidence_calculation(self, explainability_agent, sample_context, sample_scoring_result):
        """Test explanation confidence calculation."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # All explanations should have valid confidence levels
        valid_confidences = {"very_low", "low", "medium", "high", "very_high"}
        for explanation in explainability_result["explanations"]:
            assert explanation["confidence"] in valid_confidences
    
    def test_factor_contributions(self, explainability_agent, sample_context, sample_scoring_result):
        """Test factor contribution calculations."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # All factors should have valid contributions
        for explanation in explainability_result["explanations"]:
            for factor in explanation["factors"]:
                assert -1 <= factor["contribution"] <= 1
                assert factor["direction"] in {"positive", "negative"}
    
    def test_recommendations_generation(self, explainability_agent, sample_context, sample_scoring_result):
        """Test recommendations generation."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Explanations should have recommendations
        for explanation in explainability_result["explanations"]:
            assert isinstance(explanation["recommendations"], list)
            # Some explanations may not have recommendations
    
    def test_next_steps_generation(self, explainability_agent, sample_context, sample_scoring_result):
        """Test next steps generation."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Explanations should have next steps
        for explanation in explainability_result["explanations"]:
            assert isinstance(explanation["next_steps"], list)
            # Some explanations may not have next steps
    
    def test_overall_confidence_calculation(self, explainability_agent, sample_context, sample_scoring_result):
        """Test overall confidence calculation."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Overall confidence should be between 0-1
        assert 0 <= explainability_result["overall_confidence"] <= 1
    
    def test_explanation_coverage_calculation(self, explainability_agent, sample_context, sample_scoring_result):
        """Test explanation coverage calculation."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Explanation coverage should be between 0-1
        assert 0 <= explainability_result["explanation_coverage"] <= 1
    
    def test_actionable_insights_counting(self, explainability_agent, sample_context, sample_scoring_result):
        """Test actionable insights counting."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Actionable insights should be non-negative integer
        assert isinstance(explainability_result["actionable_insights"], int)
        assert explainability_result["actionable_insights"] >= 0
    
    def test_key_findings_extraction(self, explainability_agent, sample_context, sample_scoring_result):
        """Test key findings extraction."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Should extract key findings
        assert isinstance(explainability_result["key_findings"], list)
        
        if explainability_result["key_findings"]:
            # Key findings should be strings
            for finding in explainability_result["key_findings"]:
                assert isinstance(finding, str)
                assert len(finding) > 0
    
    def test_high_score_findings(self, explainability_agent, sample_context):
        """Test key findings for high score."""
        # Create high scoring result
        high_score_result = ScoringResult(
            score=85.0,
            severity="critical",
            details={"critical_risks": ["vulnerabilities"]},
            metrics={"vulnerability": 40, "exposure": 30, "drift": 15},
            recommendations=["Immediate action required"],
        )
        
        result = explainability_agent.analyze(sample_context, high_score_result)
        explainability_result = result.output["explainability_result"]
        
        # Should have high score finding
        high_score_findings = [
            finding for finding in explainability_result["key_findings"]
            if "high risk score" in finding.lower()
        ]
        assert len(high_score_findings) > 0
    
    def test_entity_type_weighting(self, explainability_agent):
        """Test entity type weighting."""
        entity_types = ["host", "application", "database", "domain", "network"]
        
        for entity_type in entity_types:
            entity = Entity(
                id=f"{entity_type}-001",
                entity_type=entity_type,
                name=f"test-{entity_type}",
            )
            
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
            
            scoring_result = ScoringResult(
                score=50.0,
                severity="medium",
                metrics={"test": 25},
            )
            
            context = Context(entity=entity, signals=signals)
            result = explainability_agent.analyze(context, scoring_result)
            explainability_result = result.output["explainability_result"]
            
            # Should generate explanations for all entity types
            assert len(explainability_result["explanations"]) > 0
    
    def test_property_weighting(self, explainability_agent):
        """Test entity property weighting."""
        # Create entity with high-risk properties
        entity = Entity(
            id="entity-001",
            entity_type="host",
            name="test-host",
            properties={
                "public": True,
                "critical": True,
                "environment": "production",
                "internet_facing": True,
            },
        )
        
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
        
        scoring_result = ScoringResult(
            score=60.0,
            severity="high",
            metrics={"test": 30},
        )
        
        context = Context(entity=entity, signals=signals)
        result = explainability_agent.analyze(context, scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Should detect high-risk properties
        factor_analysis_explanations = [
            exp for exp in explainability_result["explanations"]
            if exp["explanation_type"] == "factor_analysis"
        ]
        
        if factor_analysis_explanations:
            factor_analysis = factor_analysis_explanations[0]
            property_factors = [
                factor for factor in factor_analysis["factors"]
                if factor["name"].startswith("property_")
            ]
            
            # Should have high-weight property factors
            high_weight_properties = [
                factor for factor in property_factors
                if factor["weight"] > 0.5
            ]
            assert len(high_weight_properties) > 0
    
    def test_severity_weighting(self, explainability_agent, sample_context, sample_scoring_result):
        """Test severity weighting in factors."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Should weight critical vulnerabilities higher
        factor_analysis_explanations = [
            exp for exp in explainability_result["explanations"]
            if exp["explanation_type"] == "factor_analysis"
        ]
        
        if factor_analysis_explanations:
            factor_analysis = factor_analysis_explanations[0]
            critical_vuln_factors = [
                factor for factor in factor_analysis["factors"]
                if "vulnerability" in factor["name"] and "critical" in factor["name"]
            ]
            
            if critical_vuln_factors:
                # Critical vulnerability factors should have high weight
                assert critical_vuln_factors[0]["weight"] > 0.7
    
    def test_evidence_tracking(self, explainability_agent, sample_context, sample_scoring_result):
        """Test evidence tracking in factors."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Factors should track evidence
        for explanation in explainability_result["explanations"]:
            for factor in explanation["factors"]:
                assert isinstance(factor["evidence"], list)
                # Some factors may not have evidence
    
    def test_error_handling(self, explainability_agent):
        """Test error handling in explainability analysis."""
        # Test with malformed context
        result = explainability_agent.analyze(None)
        
        # Should handle gracefully
        assert result.success is True
        explainability_result = result.output["explainability_result"]
        assert explainability_result["score"] == 0.0
    
    def test_performance_with_many_signals(self, explainability_agent, sample_entity):
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
        
        scoring_result = ScoringResult(
            score=50.0,
            severity="medium",
            metrics={"test": 25},
        )
        
        context = Context(entity=sample_entity, signals=many_signals)
        result = explainability_agent.analyze(context, scoring_result)
        
        # Should handle large signal sets
        assert result.success is True
        assert "explainability_result" in result.output


class TestScoreExplanation:
    """Test ScoreExplanation dataclass."""
    
    def test_score_explanation_creation(self):
        """Test ScoreExplanation creation."""
        explanation = ScoreExplanation(
            explanation_type=ExplanationType.SCORE_BREAKDOWN,
            title="Test Explanation",
            summary="Test summary",
            final_score=75.0,
            severity="high",
            confidence=ConfidenceLevel.HIGH,
        )
        
        assert explanation.explanation_type == ExplanationType.SCORE_BREAKDOWN
        assert explanation.title == "Test Explanation"
        assert explanation.final_score == 75.0
        assert explanation.severity == "high"
        assert explanation.confidence == ConfidenceLevel.HIGH
    
    def test_score_explanation_to_dict(self):
        """Test ScoreExplanation to_dict conversion."""
        factor = ExplanationFactor(
            name="test_factor",
            value=10,
            weight=0.3,
            contribution=0.15,
            direction="negative",
            description="Test factor description",
            evidence=["signal-001"],
        )
        
        explanation = ScoreExplanation(
            explanation_type=ExplanationType.FACTOR_ANALYSIS,
            title="Factor Analysis",
            summary="Factor analysis summary",
            final_score=60.0,
            severity="medium",
            confidence=ConfidenceLevel.MEDIUM,
            factors=[factor],
            key_drivers=["test_factor"],
            risk_drivers=["test_factor"],
            recommendations=["Test recommendation"],
            next_steps=["Test next step"],
        )
        
        explanation_dict = explanation.to_dict()
        
        assert explanation_dict["explanation_type"] == "factor_analysis"
        assert explanation_dict["title"] == "Factor Analysis"
        assert explanation_dict["final_score"] == 60.0
        assert explanation_dict["severity"] == "medium"
        assert explanation_dict["confidence"] == "medium"
        assert len(explanation_dict["factors"]) == 1
        assert explanation_dict["factors"][0]["name"] == "test_factor"
        assert explanation_dict["key_drivers"] == ["test_factor"]
        assert explanation_dict["risk_drivers"] == ["test_factor"]
        assert explanation_dict["recommendations"] == ["Test recommendation"]
        assert explanation_dict["next_steps"] == ["Test next step"]


class TestExplainabilityResult:
    """Test ExplainabilityResult dataclass."""
    
    def test_explainability_result_creation(self):
        """Test ExplainabilityResult creation."""
        result = ExplainabilityResult(
            entity_id="test-entity",
            score=75.0,
            severity="high",
            overall_confidence=0.8,
            explanation_coverage=0.6,
            actionable_insights=3,
        )
        
        assert result.entity_id == "test-entity"
        assert result.score == 75.0
        assert result.severity == "high"
        assert result.overall_confidence == 0.8
        assert result.explanation_coverage == 0.6
        assert result.actionable_insights == 3
    
    def test_explainability_result_to_dict(self):
        """Test ExplainabilityResult to_dict conversion."""
        explanation = ScoreExplanation(
            explanation_type=ExplanationType.SCORE_BREAKDOWN,
            title="Test Explanation",
            summary="Test summary",
            final_score=50.0,
            severity="medium",
            confidence=ConfidenceLevel.MEDIUM,
        )
        
        result = ExplainabilityResult(
            entity_id="test-entity",
            score=50.0,
            severity="medium",
            explanations=[explanation],
            overall_confidence=0.7,
            explanation_coverage=0.5,
            actionable_insights=2,
            key_findings=["Key finding 1", "Key finding 2"],
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["entity_id"] == "test-entity"
        assert result_dict["score"] == 50.0
        assert result_dict["severity"] == "medium"
        assert result_dict["overall_confidence"] == 0.7
        assert result_dict["explanation_coverage"] == 0.5
        assert result_dict["actionable_insights"] == 2
        assert len(result_dict["explanations"]) == 1
        assert result_dict["explanations"][0]["title"] == "Test Explanation"
        assert result_dict["key_findings"] == ["Key finding 1", "Key finding 2"]


class TestExplanationFactor:
    """Test ExplanationFactor dataclass."""
    
    def test_explanation_factor_creation(self):
        """Test ExplanationFactor creation."""
        factor = ExplanationFactor(
            name="test_factor",
            value=10,
            weight=0.3,
            contribution=0.15,
            direction="negative",
            description="Test factor description",
            evidence=["signal-001", "signal-002"],
        )
        
        assert factor.name == "test_factor"
        assert factor.value == 10
        assert factor.weight == 0.3
        assert factor.contribution == 0.15
        assert factor.direction == "negative"
        assert factor.description == "Test factor description"
        assert factor.evidence == ["signal-001", "signal-002"]
    
    def test_explanation_factor_to_dict(self):
        """Test ExplanationFactor to_dict conversion."""
        factor = ExplanationFactor(
            name="test_factor",
            value=25.5,
            weight=0.4,
            contribution=0.2,
            direction="positive",
            description="Positive factor",
            evidence=["evidence-001"],
        )
        
        factor_dict = factor.to_dict()
        
        assert factor_dict["name"] == "test_factor"
        assert factor_dict["value"] == 25.5
        assert factor_dict["weight"] == 0.4
        assert factor_dict["contribution"] == 0.2
        assert factor_dict["direction"] == "positive"
        assert factor_dict["description"] == "Positive factor"
        assert factor_dict["evidence"] == ["evidence-001"]


class TestExplanationType:
    """Test ExplanationType enum."""
    
    def test_explanation_type_values(self):
        """Test ExplanationType enum values."""
        assert ExplanationType.SCORE_BREAKDOWN.value == "score_breakdown"
        assert ExplanationType.FACTOR_ANALYSIS.value == "factor_analysis"
        assert ExplanationType.TEMPORAL_ANALYSIS.value == "temporal_analysis"
        assert ExplanationType.COMPARATIVE_ANALYSIS.value == "comparative_analysis"
        assert ExplanationType.ROOT_CAUSE.value == "root_cause"
        assert ExplanationType.RECOMMENDATION_RATIONALE.value == "recommendation_rationale"


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
    """Integration tests for Explainability Agent."""
    
    def test_full_pipeline_integration(self, explainability_agent, sample_context, sample_scoring_result):
        """Test full pipeline integration."""
        result = explainability_agent.analyze(sample_context, sample_scoring_result)
        
        assert result.success is True
        explainability_result = result.output["explainability_result"]
        
        # Should have comprehensive analysis
        assert len(explainability_result["explanations"]) > 0
        assert explainability_result["overall_confidence"] > 0
        assert explainability_result["explanation_coverage"] > 0
        assert isinstance(explainability_result["key_findings"], list)
    
    def test_real_world_critical_vulnerability_scenario(self, explainability_agent):
        """Test real-world critical vulnerability scenario."""
        # Create realistic critical vulnerability scenario
        entity = Entity(
            id="prod-web-01",
            entity_type="host",
            name="prod-web-01.example.com",
            description="Production web server",
            properties={
                "environment": "production",
                "public": True,
                "critical": True,
                "data_classification": "public",
            },
        )
        
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
        
        scoring_result = ScoringResult(
            score=90.0,
            severity="critical",
            details={"critical_vulnerabilities": ["CVE-2023-1234"]},
            metrics={
                "vulnerability": 50,
                "exposure": 25,
                "drift": 10,
                "configuration": 5,
            },
            recommendations=["Immediate patching required", "Isolate affected system"],
        )
        
        context = Context(entity=entity, signals=signals)
        result = explainability_agent.analyze(context, scoring_result)
        explainability_result = result.output["explainability_result"]
        
        # Should have comprehensive explanations
        assert len(explainability_result["explanations"]) > 0
        
        # Should have high overall confidence
        assert explainability_result["overall_confidence"] > 0.6
        
        # Should have good explanation coverage
        assert explainability_result["explanation_coverage"] > 0.5
        
        # Should identify critical vulnerability as key driver
        score_breakdown_explanations = [
            exp for exp in explainability_result["explanations"]
            if exp["explanation_type"] == "score_breakdown"
        ]
        
        if score_breakdown_explanations:
            breakdown = score_breakdown_explanations[0]
            vulnerability_factors = [
                factor for factor in breakdown["factors"]
                if "vulnerability" in factor["name"]
            ]
            assert len(vulnerability_factors) > 0
            
            # Vulnerability factor should have high contribution
            if vulnerability_factors:
                assert vulnerability_factors[0]["contribution"] > 0.1
        
        # Should have actionable insights
        assert explainability_result["actionable_insights"] > 0
        
        # Should have key findings about high score
        high_score_findings = [
            finding for finding in explainability_result["key_findings"]
            if "high risk score" in finding.lower()
        ]
        assert len(high_score_findings) > 0
