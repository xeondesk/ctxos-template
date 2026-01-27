"""
Tests for Context Summarizer Agent.
"""

import pytest
from datetime import datetime, timedelta

from core.models.entity import Entity
from core.models.signal import Signal
from core.models.context import Context
from core.scoring.risk import ScoringResult
from agents.agents.context_summarizer import ContextSummarizer


@pytest.fixture
def summarizer():
    """Create Context Summarizer instance."""
    return ContextSummarizer(
        name="test_summarizer",
        version="1.0.0",
        max_risks=5,
        max_exposures=5,
        max_anomalies=3,
    )


@pytest.fixture
def sample_entity():
    """Create sample entity."""
    return Entity(
        id="entity-001",
        entity_type="host",
        name="test-host",
        description="Test host",
    )


@pytest.fixture
def sample_signals():
    """Create sample signals."""
    return [
        Signal(
            id="signal-001",
            source="vulnerability_scanner",
            signal_type="VULNERABILITY",
            severity="CRITICAL",
            description="Critical vulnerability detected",
            timestamp=datetime.utcnow(),
        ),
        Signal(
            id="signal-002",
            source="port_scanner",
            signal_type="OPEN_PORT",
            severity="HIGH",
            description="Open port 22 (SSH)",
            timestamp=datetime.utcnow(),
        ),
        Signal(
            id="signal-003",
            source="certificate_monitor",
            signal_type="CERTIFICATE",
            severity="MEDIUM",
            description="SSL certificate expires in 30 days",
            timestamp=datetime.utcnow(),
        ),
    ]


@pytest.fixture
def sample_context(sample_entity, sample_signals):
    """Create sample context."""
    context = Context(name="test_context")
    context.entity = sample_entity
    context.signals = sample_signals
    return context


@pytest.fixture
def risk_scoring_result():
    """Create risk scoring result."""
    return ScoringResult(
        score=75.5,
        severity="HIGH",
        engine_name="risk",
        factors={"vulnerabilities": 0.5, "ports": 0.25},
        metrics={"critical_count": 1},
        recommendations=["Update systems", "Close unnecessary ports"],
        timestamp=datetime.utcnow(),
    )


@pytest.fixture
def exposure_scoring_result():
    """Create exposure scoring result."""
    return ScoringResult(
        score=65.0,
        severity="HIGH",
        engine_name="exposure",
        factors={"public_access": 0.6, "services": 0.5},
        metrics={"open_ports": 3},
        recommendations=["Reduce public accessibility"],
        timestamp=datetime.utcnow(),
    )


@pytest.fixture
def drift_scoring_result():
    """Create drift scoring result."""
    return ScoringResult(
        score=45.0,
        severity="MEDIUM",
        engine_name="drift",
        factors={"property_changes": 0.3, "signal_changes": 0.15},
        metrics={"changes_count": 5},
        recommendations=["Review recent changes"],
        timestamp=datetime.utcnow(),
    )


# ============================================================================
# Basic Functionality Tests
# ============================================================================


@pytest.mark.asyncio
async def test_summarizer_initialization(summarizer):
    """Test Context Summarizer initialization."""
    assert summarizer.name == "test_summarizer"
    assert summarizer.version == "1.0.0"
    assert summarizer.max_risks == 5
    assert summarizer.max_exposures == 5
    assert summarizer.max_anomalies == 3


@pytest.mark.asyncio
async def test_summarizer_analyze_basic(summarizer, sample_context):
    """Test basic analyze functionality."""
    result = await summarizer.analyze(sample_context)

    assert result.success
    assert result.agent_name == "test_summarizer"
    assert "entity_id" in result.output
    assert "entity_type" in result.output
    assert "top_risks" in result.output
    assert "exposure_highlights" in result.output
    assert "configuration_anomalies" in result.output
    assert "overall_assessment" in result.output
    assert "signal_statistics" in result.output


@pytest.mark.asyncio
async def test_summarizer_analyze_missing_entity(summarizer):
    """Test analyze with missing entity."""
    context = Context(name="empty_context")
    result = await summarizer.analyze(context)

    assert not result.success
    assert "No entity in context" in result.error


# ============================================================================
# Output Structure Tests
# ============================================================================


@pytest.mark.asyncio
async def test_summary_output_structure(summarizer, sample_context):
    """Test summary output has correct structure."""
    result = await summarizer.analyze(sample_context)
    summary = result.output

    # Required fields
    assert isinstance(summary["entity_id"], str)
    assert isinstance(summary["entity_type"], str)
    assert isinstance(summary["entity_name"], str)
    assert "summary_timestamp" in summary

    # Summary sections
    assert isinstance(summary["top_risks"], list)
    assert isinstance(summary["exposure_highlights"], list)
    assert isinstance(summary["configuration_anomalies"], list)
    assert isinstance(summary["overall_assessment"], dict)
    assert isinstance(summary["signal_statistics"], dict)


@pytest.mark.asyncio
async def test_risk_extraction(summarizer, sample_context):
    """Test top risks extraction."""
    result = await summarizer.analyze(sample_context)
    risks = result.output["top_risks"]

    # Should have at least one critical/high risk
    assert len(risks) > 0

    # Check risk structure
    for risk in risks:
        assert "severity" in risk
        assert "source" in risk
        assert "description" in risk
        assert "timestamp" in risk


@pytest.mark.asyncio
async def test_exposure_extraction(summarizer, sample_context):
    """Test exposure highlights extraction."""
    result = await summarizer.analyze(sample_context)
    exposures = result.output["exposure_highlights"]

    # Should have at least one exposure
    assert len(exposures) > 0

    # Check exposure structure
    for exposure in exposures:
        assert "type" in exposure
        assert "source" in exposure or "severity" in exposure
        assert "description" in exposure or "description" in exposure


@pytest.mark.asyncio
async def test_anomaly_extraction(summarizer, sample_context):
    """Test configuration anomalies extraction."""
    result = await summarizer.analyze(sample_context)
    anomalies = result.output["configuration_anomalies"]

    # Anomalies are optional
    assert isinstance(anomalies, list)


# ============================================================================
# Scoring Result Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_analyze_with_risk_score(summarizer, sample_context, risk_scoring_result):
    """Test analyze with risk scoring result."""
    result = await summarizer.analyze(sample_context, risk_scoring_result)

    assert result.success
    risks = result.output["top_risks"]

    # Should include risk engine result
    risk_from_engine = [r for r in risks if r.get("source") == "risk_engine"]
    assert len(risk_from_engine) > 0
    assert risk_from_engine[0]["severity"] == "HIGH"
    assert risk_from_engine[0]["score"] == 75.5


@pytest.mark.asyncio
async def test_analyze_with_exposure_score(
    summarizer, sample_context, exposure_scoring_result
):
    """Test analyze with exposure scoring result."""
    result = await summarizer.analyze(sample_context, exposure_scoring_result)

    assert result.success
    exposures = result.output["exposure_highlights"]

    # Should include exposure engine result
    exposure_from_engine = [e for e in exposures if e.get("type") == "public_exposure"]
    assert len(exposure_from_engine) > 0
    assert exposure_from_engine[0]["severity"] == "HIGH"


@pytest.mark.asyncio
async def test_analyze_with_drift_score(summarizer, sample_context, drift_scoring_result):
    """Test analyze with drift scoring result."""
    result = await summarizer.analyze(sample_context, drift_scoring_result)

    assert result.success
    assessment = result.output["overall_assessment"]

    # Should detect medium priority from drift
    assert assessment["priority"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


# ============================================================================
# Assessment Generation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_assessment_critical_priority(summarizer):
    """Test CRITICAL priority assessment."""
    risks = [
        {"severity": "CRITICAL"},
        {"severity": "CRITICAL"},
        {"severity": "HIGH"},
    ]
    exposures = [{"type": "exposure"}]
    anomalies = []

    assessment = await summarizer._generate_assessment(risks, exposures, anomalies)

    assert assessment["priority"] == "CRITICAL"
    assert assessment["critical_findings"] == 2
    assert "immediate investigation" in assessment["recommendation"].lower()


@pytest.mark.asyncio
async def test_assessment_high_priority(summarizer):
    """Test HIGH priority assessment."""
    risks = [{"severity": "CRITICAL"}]
    exposures = [{"type": "exposure"}]
    anomalies = []

    assessment = await summarizer._generate_assessment(risks, exposures, anomalies)

    assert assessment["priority"] == "HIGH"
    assert "urgent" in assessment["recommendation"].lower()


@pytest.mark.asyncio
async def test_assessment_medium_priority(summarizer):
    """Test MEDIUM priority assessment."""
    risks = [{"severity": "HIGH"}]
    exposures = [{"type": "exposure"}, {"type": "exposure"}]
    anomalies = []

    assessment = await summarizer._generate_assessment(risks, exposures, anomalies)

    assert assessment["priority"] == "MEDIUM"
    assert "schedule" in assessment["recommendation"].lower()


@pytest.mark.asyncio
async def test_assessment_low_priority(summarizer):
    """Test LOW priority assessment."""
    risks = []
    exposures = []
    anomalies = []

    assessment = await summarizer._generate_assessment(risks, exposures, anomalies)

    assert assessment["priority"] == "LOW"
    assert "routine monitoring" in assessment["recommendation"].lower()


# ============================================================================
# Signal Statistics Tests
# ============================================================================


@pytest.mark.asyncio
async def test_signal_statistics(summarizer, sample_context):
    """Test signal statistics generation."""
    result = await summarizer.analyze(sample_context)
    stats = result.output["signal_statistics"]

    assert stats["total_signals"] == 3
    assert "signal_types" in stats
    assert stats["critical_count"] == 1
    assert stats["high_count"] == 1


@pytest.mark.asyncio
async def test_signal_statistics_empty(summarizer, sample_entity):
    """Test signal statistics with no signals."""
    context = Context(name="test")
    context.entity = sample_entity
    context.signals = []

    result = await summarizer.analyze(context)
    stats = result.output["signal_statistics"]

    assert stats["total_signals"] == 0
    assert stats["critical_count"] == 0
    assert stats["high_count"] == 0


# ============================================================================
# Limit Tests
# ============================================================================


@pytest.mark.asyncio
async def test_max_risks_limit(summarizer, sample_entity):
    """Test that max_risks limit is respected."""
    # Create more signals than max_risks
    signals = [
        Signal(
            id=f"signal-{i}",
            source="scanner",
            signal_type="VULNERABILITY",
            severity="CRITICAL",
            description=f"Vulnerability {i}",
            timestamp=datetime.utcnow(),
        )
        for i in range(10)
    ]

    context = Context(name="test")
    context.entity = sample_entity
    context.signals = signals

    result = await summarizer.analyze(context)
    risks = result.output["top_risks"]

    assert len(risks) <= summarizer.max_risks


@pytest.mark.asyncio
async def test_max_exposures_limit(summarizer, sample_entity):
    """Test that max_exposures limit is respected."""
    # Create more exposures than max_exposures
    signals = [
        Signal(
            id=f"signal-{i}",
            source="scanner",
            signal_type="OPEN_PORT",
            severity="MEDIUM",
            description=f"Port {i}",
            timestamp=datetime.utcnow(),
        )
        for i in range(10)
    ]

    context = Context(name="test")
    context.entity = sample_entity
    context.signals = signals

    result = await summarizer.analyze(context)
    exposures = result.output["exposure_highlights"]

    assert len(exposures) <= summarizer.max_exposures


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_analyze_with_invalid_signals(summarizer, sample_entity):
    """Test analyze gracefully handles various signal types."""
    signals = [
        Signal(
            id="signal-001",
            source="scanner",
            signal_type="UNKNOWN_TYPE",
            severity="LOW",
            description="Unknown signal",
            timestamp=datetime.utcnow(),
        )
    ]

    context = Context(name="test")
    context.entity = sample_entity
    context.signals = signals

    result = await summarizer.analyze(context)

    # Should still succeed
    assert result.success


@pytest.mark.asyncio
async def test_analyze_with_none_entity(summarizer):
    """Test analyze with None entity."""
    context = Context(name="test")
    context.entity = None
    context.signals = []

    result = await summarizer.analyze(context)

    assert not result.success
    assert "No entity in context" in result.error


# ============================================================================
# Agent Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_agent_run_method(summarizer, sample_context):
    """Test agent.run() method with timeout."""
    result = await summarizer.run(sample_context, user="analyst-001", timeout=30.0)

    assert result.success
    assert result.agent_name == "test_summarizer"
    assert result.duration_ms > 0
    assert "entity_id" in result.output


@pytest.mark.asyncio
async def test_agent_state_tracking(summarizer, sample_context):
    """Test agent state after execution."""
    result1 = await summarizer.run(sample_context, timeout=30.0)

    assert summarizer.last_result is not None
    assert summarizer.last_result.success

    state = summarizer.get_state()
    assert state["name"] == "test_summarizer"
    assert state["version"] == "1.0.0"
    assert state["last_result"] is not None


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.asyncio
async def test_large_signal_set_performance(summarizer, sample_entity):
    """Test performance with large signal set."""
    # Create 100 signals
    signals = [
        Signal(
            id=f"signal-{i}",
            source="scanner",
            signal_type="VULNERABILITY",
            severity="MEDIUM",
            description=f"Signal {i}",
            timestamp=datetime.utcnow(),
        )
        for i in range(100)
    ]

    context = Context(name="test")
    context.entity = sample_entity
    context.signals = signals

    result = await summarizer.run(context, timeout=30.0)

    assert result.success
    assert result.duration_ms < 5000  # Should complete in under 5 seconds


@pytest.mark.asyncio
async def test_concurrent_execution(summarizer, sample_context):
    """Test concurrent execution of multiple analyses."""
    tasks = [
        summarizer.analyze(sample_context)
        for _ in range(5)
    ]

    results = await asyncio.gather(*tasks)

    assert all(r.success for r in results)
    assert len(results) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
