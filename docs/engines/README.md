# CtxOS Engines Documentation

Welcome to the CtxOS Engines documentation. This comprehensive guide covers the three scoring engines that form the core of CtxOS security assessment capabilities.

## Quick Start

### 1. Score an Entity (Command Line)

```bash
# Score a domain with all engines
ctxos risk --entity example.com

# Output:
# Risk Score:     65 (HIGH)
# Exposure Score: 45 (MEDIUM)  
# Drift Score:    15 (LOW)
# Combined Score: 47 (MEDIUM)
```

### 2. Understanding Scores

All engines return scores from **0-100** with five severity levels:

```
Score       Severity      Meaning
80-100      CRITICAL      Immediate action required
60-79       HIGH          Urgent attention needed
40-59       MEDIUM        Address soon
20-39       LOW           Monitor
0-19        INFO          Informational only
```

### 3. Batch Processing

```bash
# Score all entities in a file
ctxos risk --input entities.json --format json --output results.json

# Filter for critical issues
ctxos risk --input results.json --threshold 80 --format table
```

## The Three Engines

### 🔴 Risk Engine

Assesses vulnerability and security incident risk:
- Counts vulnerabilities (CVEs)
- Detects exposed credentials
- Identifies malware
- Flags suspicious activity
- Applies age decay to older entities

**Use Case**: "What's the risk this entity poses or faces?"

[Read Risk Engine Documentation →](risk_engine.md)

### 🟡 Exposure Engine  

Measures attack surface and public exposure:
- Public accessibility
- Exposed services
- Protocol diversity
- Subdomain count
- Security controls (WAF, CDN, headers)

**Use Case**: "How much is this asset exposed to the internet?"

[Read Exposure Engine Documentation →](exposure_engine.md)

### 🟢 Drift Engine

Detects configuration changes and deviations:
- Property modifications
- Signal additions/removals
- Critical property changes
- Change velocity tracking
- Baseline management

**Use Case**: "Has this entity's configuration changed unexpectedly?"

[Read Drift Engine Documentation →](drift_engine.md)

## Documentation Structure

```
docs/engines/
├── README.md (this file)              # Overview and quick start
├── engine_architecture.md             # Technical architecture
├── risk_engine.md                     # Risk engine guide
├── exposure_engine.md                 # Exposure engine guide
├── drift_engine.md                    # Drift engine guide
├── engine_testing.md                  # Testing strategy
└── engine_cli_workflows.md            # CLI examples and workflows
```

## Core Concepts

### Entities

Entities are security assets being assessed:

```python
Entity types:
- DOMAIN          # Domain registrations
- IP_ADDRESS      # Network addresses
- SERVICE         # Applications/services
- URL             # Web endpoints
- EMAIL           # Email addresses
- PERSON          # People/identities
- FILE            # Files/documents
- COMPANY         # Organizations
- CREDENTIAL      # Passwords/keys
```

### Signals

Signals are pieces of security information about entities:

```python
Signal types:
- VULNERABILITY       # CVE/known weakness
- OPEN_PORT           # Exposed network service
- CREDENTIAL_EXPOSURE # Password/key in breach
- MALWARE             # Malicious software
- SUSPICIOUS_ACTIVITY # Anomalous behavior
- DATA_BREACH         # Compromised data
- DOMAIN_REGISTRATION # Domain/subdomain info
- CERTIFICATE         # SSL/TLS certificate
- HTTP_HEADER         # Web security headers
- DNS_RECORD          # DNS information
```

### Context

Context links entities with their signals:

```python
context = Context(
    entities=[entity1, entity2],
    signals=[signal1, signal2, signal3]
)
```

### ScoringResult

All engines return standardized ScoringResult objects:

```python
ScoringResult(
    engine_name="risk",
    entity_id="domain-1",
    score=65,                    # 0-100
    severity="high",             # critical/high/medium/low/info
    timestamp=datetime.now(),
    details={...},               # Engine-specific details
    metrics={...},               # Detailed metrics breakdown
    recommendations=[...]        # Actionable recommendations
)
```

## Usage Examples

### Example 1: Basic Python Usage

```python
from engines.risk.risk_engine import RiskEngine
from engines.exposure.exposure_engine import ExposureEngine
from engines.drift.drift_engine import DriftEngine
from core.models import Entity, Signal, Context

# Create entities and signals
entity = Entity(id="web-1", type="DOMAIN", name="www.example.com")
signals = [
    Signal(type="VULNERABILITY", severity="high"),
    Signal(type="OPEN_PORT", port=443),
    Signal(type="OPEN_PORT", port=80)
]

context = Context(entities=[entity], signals=signals)

# Score with risk engine
risk_engine = RiskEngine()
risk_result = risk_engine.score(entity, context)
print(f"Risk: {risk_result.score} ({risk_result.severity})")

# Score with exposure engine
exposure_engine = ExposureEngine()
exposure_result = exposure_engine.score(entity, context)
print(f"Exposure: {exposure_result.score} ({exposure_result.severity})")

# Combine results
combined = (risk_result.score * 0.5 + 
            exposure_result.score * 0.3)
print(f"Combined: {combined:.0f}")
```

### Example 2: Batch Processing

```bash
# Create input file (entities.json)
[
  {"id": "domain-1", "type": "DOMAIN", "name": "example.com"},
  {"id": "ip-1", "type": "IP_ADDRESS", "ip": "203.0.113.50"}
]

# Score all entities
ctxos risk --input entities.json \
           --engine all \
           --format json \
           --output results.json

# Filter for critical issues
cat results.json | jq '.[] | select(.combined.score >= 80)'
```

### Example 3: Monitoring Changes

```python
# Establish baseline
baseline = drift_engine.create_baseline(entity, context)

# Later: Check for changes
result = drift_engine.score(entity, updated_context)
if result.score >= 40:
    print(f"Alert: Configuration drift detected!")
    print(f"Changes: {result.details['changes']}")
    for rec in result.recommendations:
        print(f"  - {rec}")
```

## API Reference

### RiskEngine

```python
class RiskEngine(BaseEngine):
    def score(entity: Entity, context: Context) -> ScoringResult
```

### ExposureEngine

```python
class ExposureEngine(BaseEngine):
    def score(entity: Entity, context: Context) -> ScoringResult
```

### DriftEngine

```python
class DriftEngine(BaseEngine):
    def score(entity: Entity, context: Context) -> ScoringResult
    def create_baseline(entity: Entity, context: Context) -> Baseline
    def update_baseline(entity: Entity, context: Context) -> Baseline
```

## Configuration

Engines are configured via `configs/engines.yml`:

```yaml
engines:
  risk:
    enabled: true
    vulnerability_weight: 25
    credential_weight: 20
    severity_multipliers:
      critical: 1.5
      high: 1.2
  
  exposure:
    enabled: true
    public_weight: 30
    service_weight: 25
  
  drift:
    enabled: true
    property_change_weight: 30
    signal_change_weight: 40
```

## Performance

Typical performance metrics:

| Task | Time |
|------|------|
| Score 1 entity | ~4ms (all engines) |
| Score 100 entities | ~400ms |
| Score 1000 entities | ~4s |

## Testing

Comprehensive test suite included:

```bash
# Run all engine tests
pytest engines/tests/ -v

# Run with coverage
pytest engines/tests/ --cov=engines --cov-report=html

# Run specific engine tests
pytest engines/tests/test_risk_engine.py -v
```

**Test Coverage**: 60+ tests, 80%+ code coverage

[Read Testing Guide →](engine_testing.md)

## Common Workflows

### 1. Security Assessment

```bash
ctxos risk --input entities.json \
           --engine all \
           --format json \
           --output assessment.json
```

### 2. Compliance Verification

```bash
ctxos risk --input entities.json \
           --engine exposure \
           --threshold 70 \
           --format csv \
           --output critical_exposures.csv
```

### 3. Change Detection

```bash
ctxos risk --input critical_assets.json \
           --engine drift \
           --baseline baseline.json \
           --threshold 40
```

[Read CLI Workflows Guide →](engine_cli_workflows.md)

## Architecture Overview

```
┌──────────────────────────────────────────────────┐
│           CLI / API Interface                     │
└──────────────────┬───────────────────────────────┘
                   │
         ┌─────────┴──────────┐
         ▼                    ▼
    ┌──────────┐         ┌──────────┐
    │ Engines  │         │ Normaliz │
    │ Manager  │         │ -ers     │
    └────┬─────┘         └──────────┘
         │
    ┌────┴─────┬──────────┬──────────┐
    ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Risk   │ │Exposure│ │ Drift  │ │  Base  │
│ Engine │ │ Engine │ │ Engine │ │ Engine │
└────────┘ └────────┘ └────────┘ └────────┘
    │          │          │          │
    └────┬─────┴──────────┴──────────┘
         │
    ┌────▼──────────────────────┐
    │  Scoring Results (0-100)   │
    │  Severity Assignment       │
    │  Recommendations Gen       │
    └────────────────────────────┘
```

## Recommendations System

Each engine generates actionable recommendations based on scoring:

**Risk Engine Recommendations**:
- Patch vulnerabilities
- Investigate suspicious activity
- Change compromised credentials
- Implement security controls

**Exposure Engine Recommendations**:
- Restrict service access
- Deploy WAF/CDN
- Add security headers
- Reduce subdomain count

**Drift Engine Recommendations**:
- Investigate unauthorized changes
- Restore from known-good baseline
- Review change management
- Monitor for patterns

## Integration Points

Engines integrate with:

- **Collectors**: Receive signals from collection pipeline
- **Normalizers**: Process normalized entities
- **Graph Engine**: Link high-risk entities and patterns
- **API Server**: Expose scoring via REST endpoints
- **CLI**: Command-line access to all engines
- **Database**: Store and retrieve results

## Troubleshooting

### Issue: Scores seem inconsistent

**Solution**: Verify configuration is applied:
```python
engine.configure(config)
result = engine.score(entity, context)
```

### Issue: High memory usage on large batches

**Solution**: Use streaming mode:
```bash
ctxos risk --input huge_file.json --stream --output results.csv
```

### Issue: Performance degradation

**Solution**: Enable parallel processing:
```bash
ctxos risk --input entities.json --parallel 8 --output results.json
```

## Best Practices

1. **Baseline consistently**: Establish baselines for drift detection
2. **Monitor trends**: Compare scores over time
3. **Action quickly**: Address critical severity findings immediately
4. **Combine engines**: Use all three for comprehensive assessment
5. **Custom configs**: Tune weights to your risk appetite
6. **Document changes**: Track baseline updates and authorizations
7. **Test thoroughly**: Validate changes with test data first
8. **Archive results**: Keep historical data for trends

## What's Next?

1. [Engine Architecture](engine_architecture.md) - Deep dive into design
2. [Risk Engine Guide](risk_engine.md) - Vulnerability assessment
3. [Exposure Engine Guide](exposure_engine.md) - Attack surface measurement
4. [Drift Engine Guide](drift_engine.md) - Change detection
5. [Testing Guide](engine_testing.md) - Test strategy and best practices
6. [CLI Workflows](engine_cli_workflows.md) - Real-world usage examples

## Support

For issues or questions:
1. Check relevant documentation above
2. Run tests: `pytest engines/tests/ -v`
3. Enable verbose logging: `--verbose --log-level debug`
4. Review configuration: `cat configs/engines.yml`
5. Check examples: `ls examples/`

## Contributing

To extend engines:

1. Implement new engine extending `BaseEngine`
2. Add unit tests in `engines/tests/`
3. Document in `docs/engines/`
4. Update configuration in `configs/engines.yml`
5. Add CLI support in `cli/commands/`

## License

CtxOS Engines are part of the CtxOS project. See LICENSE for details.

---

**Last Updated**: 2024  
**Status**: Production Ready ✅  
**Test Coverage**: 80%+  
**Performance**: Optimized for 1000+ entities
