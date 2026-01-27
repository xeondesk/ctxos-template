# Context Summarizer Agent

## Overview

The **Context Summarizer** is an intelligent agent that analyzes entity and signal data to extract key findings and produce structured summaries. It helps security teams quickly understand complex security contexts by distilling raw data into actionable insights.

**Status**: ✅ Production Ready  
**Language**: Python (async)  
**Framework**: asyncio + CtxOS base agent

---

## Purpose

The Context Summarizer analyzes:
- **Entity information** (hosts, domains, services, etc.)
- **Signal data** (vulnerabilities, open ports, certificates, etc.)
- **Scoring results** (risk, exposure, drift scores)

And generates:
- **Top risks** - Ranked by severity
- **Exposure highlights** - Public-facing threats
- **Configuration anomalies** - Deviations from baseline
- **Overall assessment** - Priority level and recommendations

---

## Quick Start

### Python Usage

```python
from agents.agents.context_summarizer import ContextSummarizer
from core.models import Entity, Signal, Context
from datetime import datetime
import asyncio

async def main():
    # Create entity and signals
    entity = Entity(
        id="host-001",
        entity_type="host",
        name="web-server-1"
    )
    
    signals = [
        Signal(
            source="vulnerability_scanner",
            signal_type="VULNERABILITY",
            severity="CRITICAL",
            description="CVE-2024-1234 detected",
            timestamp=datetime.utcnow()
        ),
        Signal(
            source="port_scanner",
            signal_type="OPEN_PORT",
            severity="HIGH",
            description="Port 22 (SSH) open",
            timestamp=datetime.utcnow()
        )
    ]
    
    # Create context
    context = Context(name="assessment")
    context.entity = entity
    context.signals = signals
    
    # Run summarizer
    summarizer = ContextSummarizer()
    result = await summarizer.run(context, user="analyst-001")
    
    # Access summary
    if result.success:
        summary = result.output
        print(f"Priority: {summary['overall_assessment']['priority']}")
        print(f"Top Risks: {len(summary['top_risks'])}")
        print(f"Recommendation: {summary['overall_assessment']['recommendation']}")

asyncio.run(main())
```

### CLI Usage

```bash
# Run summarizer on an entity
ctxos agent run context_summarizer \
  --entity-id host-001 \
  --entity-type host

# Run with input file
ctxos agent run context_summarizer \
  --input context.json \
  --output summary.json

# Run via orchestrator
ctxos pipeline run full_analysis \
  --entity-id host-001
```

### API Usage

```bash
# Run via REST API
curl -X POST http://localhost:8000/api/v1/agents/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "context_summarizer",
    "entity_id": "host-001",
    "entity_type": "host"
  }'
```

---

## Architecture

### Input

The Context Summarizer accepts:

```python
class Input:
    entity: Entity              # Entity to analyze
    signals: List[Signal]       # Signals for entity
    scoring_result: ScoringResult  # Optional: risk/exposure/drift score
```

### Processing

```
Input (Entity + Signals)
    ↓
Extract Top Risks (severity-weighted)
    ↓
Extract Exposure Highlights (public-facing threats)
    ↓
Extract Configuration Anomalies (deviations)
    ↓
Generate Overall Assessment (priority + recommendation)
    ↓
Output (Structured Summary)
```

### Output

```python
{
    "entity_id": "host-001",
    "entity_type": "host",
    "entity_name": "web-server-1",
    "summary_timestamp": "2024-01-27T12:00:00Z",
    
    "top_risks": [
        {
            "source": "vulnerability_scanner",
            "signal_type": "VULNERABILITY",
            "severity": "CRITICAL",
            "description": "CVE-2024-1234 detected",
            "timestamp": "2024-01-27T12:00:00Z"
        }
    ],
    
    "exposure_highlights": [
        {
            "type": "Open Network Port",
            "source": "port_scanner",
            "description": "Port 22 (SSH) open",
            "timestamp": "2024-01-27T12:00:00Z"
        }
    ],
    
    "configuration_anomalies": [
        {
            "type": "Configuration Change",
            "source": "drift_detector",
            "description": "DNS configuration changed",
            "timestamp": "2024-01-27T12:00:00Z"
        }
    ],
    
    "overall_assessment": {
        "priority": "HIGH",
        "critical_findings": 1,
        "total_findings": 3,
        "recommendation": "Urgent attention needed. 1 critical finding(s) require immediate action."
    },
    
    "signal_statistics": {
        "total_signals": 3,
        "signal_types": {
            "VULNERABILITY": 1,
            "OPEN_PORT": 1,
            "CONFIGURATION": 1
        },
        "critical_count": 1,
        "high_count": 1
    }
}
```

---

## Configuration

### YAML Configuration

```yaml
# configs/agents.yml
agents:
  context_summarizer:
    enabled: true
    version: "1.0.0"
    max_risks: 5
    max_exposures: 5
    max_anomalies: 3
    timeout: 30
```

### Python Configuration

```python
from agents.agents.context_summarizer import ContextSummarizer

summarizer = ContextSummarizer(
    name="context_summarizer",
    version="1.0.0",
    max_risks=5,           # Maximum risks to include in summary
    max_exposures=5,       # Maximum exposures to include
    max_anomalies=3        # Maximum anomalies to include
)
```

---

## Features

### 1. Top Risks Extraction

Identifies the most critical security findings:

```python
{
    "source": "vulnerability_scanner",
    "severity": "CRITICAL",
    "score": 95,
    "description": "Critical vulnerability detected",
    "timestamp": "2024-01-27T12:00:00Z"
}
```

**Severity Levels** (in order):
- `CRITICAL` - Immediate action required
- `HIGH` - Urgent attention
- `MEDIUM` - Address soon
- `LOW` - Monitor
- `INFO` - Informational

### 2. Exposure Highlights

Surfaces public-facing threats:

```python
{
    "type": "Open Network Port",
    "source": "port_scanner",
    "description": "Port 22 (SSH) open",
    "timestamp": "2024-01-27T12:00:00Z"
}
```

**Supported Exposure Types**:
- `Open Network Port` - Publicly accessible ports
- `Registered Domain` - Domain registrations
- `Public Certificate` - SSL certificates
- `Web Service Headers` - HTTP header analysis

### 3. Configuration Anomalies

Detects deviations from baseline:

```python
{
    "type": "Configuration Drift",
    "severity": "MEDIUM",
    "score": 65,
    "description": "Configuration has drifted from baseline",
    "timestamp": "2024-01-27T12:00:00Z"
}
```

### 4. Overall Assessment

Provides priority level and recommendations:

```python
{
    "priority": "HIGH",              # CRITICAL, HIGH, MEDIUM, LOW
    "critical_findings": 1,          # Count of critical items
    "total_findings": 3,             # Total findings
    "recommendation": "..."          # Actionable recommendation
}
```

**Priority Levels**:
- `CRITICAL`: 3+ critical findings → "Immediate investigation and remediation required"
- `HIGH`: 1-2 critical findings or 2+ issues → "Urgent attention needed"
- `MEDIUM`: 1+ issues across categories → "Schedule assessment within one week"
- `LOW`: No significant findings → "Continue routine monitoring"

---

## Signal Statistics

Summarizes signal composition:

```python
{
    "total_signals": 10,
    "signal_types": {
        "VULNERABILITY": 3,
        "OPEN_PORT": 2,
        "CERTIFICATE": 1,
        "DNS_RECORD": 4
    },
    "critical_count": 1,
    "high_count": 2
}
```

---

## Integration with Scoring Results

The Context Summarizer can consume scoring results from Section 4 engines:

### Risk Engine Integration

```python
result = await summarizer.analyze(
    context,
    scoring_result=risk_score  # RiskEngine output
)

# Output includes risk engine score in top_risks
```

### Exposure Engine Integration

```python
result = await summarizer.analyze(
    context,
    scoring_result=exposure_score  # ExposureEngine output
)

# Output includes exposure score in exposure_highlights
```

### Drift Engine Integration

```python
result = await summarizer.analyze(
    context,
    scoring_result=drift_score  # DriftEngine output
)

# Output reflects drift in configuration_anomalies
```

---

## Use Cases

### 1. Quick Threat Assessment

```python
# Quickly assess a newly discovered host
entity = Entity(id="new-host", entity_type="host")
context = Context(entity=entity, signals=all_signals)

summary = await summarizer.analyze(context)
priority = summary["overall_assessment"]["priority"]
```

### 2. Incident Response

```python
# Summarize incident context for response team
incident_context = Context(entity=compromised_host)
incident_context.signals = incident_signals

summary = await summarizer.run(
    incident_context,
    user="incident-responder"
)
```

### 3. Compliance Reporting

```python
# Generate summary for compliance reporting
for entity in entities_under_audit:
    summary = await summarizer.analyze(context_for(entity))
    report.add_summary(summary)
```

### 4. Continuous Monitoring

```python
# Run as part of continuous monitoring pipeline
for entity in monitored_entities:
    result = await summarizer.run(
        context_for(entity),
        user="monitoring-system"
    )
    
    if result.output["overall_assessment"]["priority"] in ["HIGH", "CRITICAL"]:
        alert_team(entity, result)
```

---

## Testing

### Run All Tests

```bash
pytest agents/tests/test_context_summarizer.py -v
```

### Run Specific Test Category

```bash
# Basic functionality
pytest agents/tests/test_context_summarizer.py::test_summarizer_initialize -v

# Output structure
pytest agents/tests/test_context_summarizer.py -k "output_structure" -v

# Scoring integration
pytest agents/tests/test_context_summarizer.py -k "with_risk_score" -v

# Error handling
pytest agents/tests/test_context_summarizer.py -k "error" -v
```

### Test Coverage

```bash
pytest agents/tests/test_context_summarizer.py --cov=agents.agents.context_summarizer
```

---

## Performance

### Benchmarks

- **Single entity with 10 signals**: ~15ms
- **Single entity with 100 signals**: ~50ms
- **Single entity with 1000 signals**: ~200ms
- **Concurrent (5 analyses)**: ~100ms total

### Optimization Tips

1. **Limit signals**: Use collectors with quality filters
2. **Cache results**: Store summaries for repeated queries
3. **Parallel execution**: Run multiple agents via orchestrator
4. **Async operations**: Leverage asyncio for concurrent processing

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "No entity in context" | Context.entity is None | Provide entity in context |
| "Summarization failed" | Exception during analysis | Check signal data format |
| Timeout | Analysis taking too long | Reduce signal count or increase timeout |

### Graceful Degradation

```python
result = await summarizer.analyze(context)

if not result.success:
    print(f"Summarization failed: {result.error}")
    # Fall back to basic analysis
    basic_summary = create_basic_summary(context)
```

---

## Advanced Usage

### Custom Configuration

```python
# Create with custom limits
summarizer = ContextSummarizer(
    max_risks=10,          # Show more risks
    max_exposures=8,       # Show more exposures
    max_anomalies=5        # Show more anomalies
)

result = await summarizer.run(context)
```

### Integration with Orchestrator

```python
from agents.mcp_orchestrator import get_orchestrator

orchestrator = get_orchestrator()
orchestrator.register_agent(summarizer)

# Run as part of pipeline
results = await orchestrator.execute_pipeline(
    "full_analysis",
    context,
    user="analyst"
)

summary_result = results["context_summarizer"]
```

### Custom Recommendation Logic

Extend the class to customize recommendations:

```python
class CustomSummarizer(ContextSummarizer):
    def _get_recommendation(self, priority, critical_count, exposure_count, anomaly_count):
        if critical_count >= 5:
            return "EMERGENCY: Isolate system immediately"
        return super()._get_recommendation(...)
```

---

## Troubleshooting

### Summary Missing Risks

**Problem**: Top risks not appearing in summary

**Solution**: Check signal severity levels
```python
# Ensure signals have proper severity
signal.severity = "CRITICAL"  # Not "critical" or "critical_risk"
```

### Assessment Priority Too Low

**Problem**: Priority is LOW when expecting HIGH

**Solution**: Check critical signal count
```python
# Need CRITICAL severity to bump priority
signal.severity = "CRITICAL"  # Not "HIGH"
```

### Timeout During Large Analysis

**Problem**: Timeout with many signals

**Solution**: Increase timeout or reduce signal set
```python
result = await summarizer.run(context, timeout=60.0)  # Increase timeout
```

---

## Roadmap

### Version 1.1 (Planned)
- Custom signal weighting
- Trend analysis (comparing with historical summaries)
- Machine learning-based anomaly detection
- Multi-entity relationship analysis

### Version 2.0 (Future)
- Natural language summary generation
- Visualization generation
- Integration with external threat feeds
- Predictive risk assessment

---

## Related Components

- **[BaseAgentAsync](../base_agent_async.py)** - Async agent foundation
- **[MCP Orchestrator](../mcp_orchestrator.py)** - Multi-agent coordination
- **[Audit Logger](../audit_system/audit_logger.py)** - Activity logging
- **[Risk Engine](../../engines/risk/risk_engine.py)** - Risk scoring
- **[Exposure Engine](../../engines/exposure/exposure_engine.py)** - Exposure scoring
- **[Drift Engine](../../engines/drift/drift_engine.py)** - Drift detection

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review test cases in `agents/tests/test_context_summarizer.py`
3. Check audit logs for execution details
4. Refer to base agent documentation

---

**Status**: ✅ Production Ready  
**Last Updated**: 2024-01-27  
**Version**: 1.0.0
