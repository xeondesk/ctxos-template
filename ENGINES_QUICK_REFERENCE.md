# CtxOS Engines - Quick Reference

## 🚀 Quick Start

### Score an Entity (Python)

```python
from engines.risk.risk_engine import RiskEngine
from engines.exposure.exposure_engine import ExposureEngine
from engines.drift.drift_engine import DriftEngine
from core.models import Entity, Signal, Context

# Create entity and signals
entity = Entity(id="1", type="DOMAIN", name="example.com")
signals = [Signal(type="OPEN_PORT", port=443)]
context = Context(entities=[entity], signals=signals)

# Score with each engine
risk = RiskEngine().score(entity, context)
exposure = ExposureEngine().score(entity, context)
drift = DriftEngine().score(entity, context)

# Combined score (50% risk, 30% exposure, 20% drift)
combined = (risk.score * 0.5 + exposure.score * 0.3 + drift.score * 0.2)
print(f"Combined Score: {combined:.0f} ({risk.severity})")
```

### Score via CLI

```bash
# Single entity
ctxos risk --entity example.com

# Batch from file
ctxos risk --input entities.json --engine all --format json --output results.json

# Filter by threshold
ctxos risk --input results.json --threshold 70 --format table
```

## 📊 Scoring Overview

All engines return scores from **0-100**:

| Score | Severity | Action |
|-------|----------|--------|
| 80-100 | CRITICAL | Immediate investigation |
| 60-79 | HIGH | Urgent attention |
| 40-59 | MEDIUM | Address soon |
| 20-39 | LOW | Monitor |
| 0-19 | INFO | Informational |

## 🔴 Risk Engine

**Purpose**: Assess vulnerability and incident risk

**Factors**:
- Vulnerabilities (25%)
- Open Ports (15%)
- Credential Exposure (20%)
- Malware (15%)
- Activity (10%)
- Age Decay (0.1% per day)

**Example**:
```python
entity = Entity(id="1", type="DOMAIN", name="example.com")
signals = [
    Signal(type="VULNERABILITY", severity="critical", count=3),
    Signal(type="CREDENTIAL_EXPOSURE", severity="critical"),
    Signal(type="OPEN_PORT", port=3306)
]
result = RiskEngine().score(entity, Context(entities=[entity], signals=signals))
# High score expected: vulnerabilities + credentials + exposed DB
```

## 🟡 Exposure Engine

**Purpose**: Measure attack surface and public exposure

**Factors**:
- Public Accessibility (30%)
- Services (25%)
- Protocols (20%)
- Subdomains (15%)
- Security Controls (multiplier: WAF ×0.8, CDN ×0.9)

**Example**:
```python
entity = Entity(id="1", type="DOMAIN", name="api.example.com")
signals = [
    Signal(type="OPEN_PORT", port=443),  # HTTPS
    Signal(type="OPEN_PORT", port=80),   # HTTP
    Signal(type="DOMAIN_REGISTRATION", subdomain_count=5),
]
result = ExposureEngine().score(entity, Context(entities=[entity], signals=signals))
# Medium-high score: public, web services, multiple subdomains
```

## 🟢 Drift Engine

**Purpose**: Detect configuration changes and deviations

**Factors**:
- Property Changes (30%)
- Signal Changes (40%)
- Critical Properties (×1.3 multiplier)
- Change Velocity (multiplier)

**Critical Properties**:
- dns_servers
- authentication_method
- firewall_rules
- ssl_certificate
- ip_address
- service_ports
- load_balancer_config
- backup_destination

**Example**:
```python
# Create baseline
baseline = DriftEngine().create_baseline(entity, context)

# Later: Detect changes
new_context = Context(entities=[entity], signals=new_signals)
result = DriftEngine().score(entity, new_context)
# Score reflects new signals + property changes since baseline
```

## 📁 File Structure

```
engines/
├── risk/
│   ├── __init__.py
│   └── risk_engine.py          # RiskEngine implementation
├── exposure/
│   ├── __init__.py
│   └── exposure_engine.py      # ExposureEngine implementation
├── drift/
│   ├── __init__.py
│   └── drift_engine.py         # DriftEngine implementation
├── base_engine.py              # BaseEngine abstract class
├── engine_manager.py           # EngineManager (orchestration)
├── tests/
│   ├── test_risk_engine.py     # 18 tests
│   ├── test_exposure_engine.py # 20 tests
│   ├── test_drift_engine.py    # 22 tests
│   └── test_integration.py     # 12+ integration tests
└── __init__.py

configs/
└── engines.yml                 # Engine configuration

docs/engines/
├── README.md                   # Overview
├── engine_architecture.md      # Technical guide
├── risk_engine.md             # Risk engine docs
├── exposure_engine.md         # Exposure engine docs
├── drift_engine.md            # Drift engine docs
├── engine_testing.md          # Testing guide
└── engine_cli_workflows.md    # CLI examples
```

## 🧪 Testing

### Run All Tests
```bash
pytest engines/tests/ -v
```

### Run Specific Engine
```bash
pytest engines/tests/test_risk_engine.py -v
pytest engines/tests/test_exposure_engine.py -v
pytest engines/tests/test_drift_engine.py -v
```

### Run with Coverage
```bash
pytest engines/tests/ --cov=engines --cov-report=html
```

### Run Specific Test
```bash
pytest engines/tests/test_risk_engine.py::test_vulnerability_signal_weight -v
```

## ⚙️ Configuration

**File**: `configs/engines.yml`

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
    waf_reduction: 0.8
  
  drift:
    enabled: true
    property_change_weight: 30
    signal_change_weight: 40
```

## 📚 Documentation

- [Main README](docs/engines/README.md) - Overview & quick start
- [Architecture](docs/engines/engine_architecture.md) - System design
- [Risk Engine](docs/engines/risk_engine.md) - Vulnerability assessment
- [Exposure Engine](docs/engines/exposure_engine.md) - Attack surface
- [Drift Engine](docs/engines/drift_engine.md) - Change detection
- [Testing Guide](docs/engines/engine_testing.md) - Test strategy
- [CLI Workflows](docs/engines/engine_cli_workflows.md) - Real-world examples

## 🎯 Common Tasks

### Score Multiple Entities

```python
from engines.engine_manager import EngineManager

manager = EngineManager()
for entity in entities:
    results = manager.score_all(entity, context)
    print(f"{entity.name}: Risk={results['risk'].score}, "
          f"Exposure={results['exposure'].score}")
```

### Establish Drift Baseline

```python
drift_engine = DriftEngine()
baseline = drift_engine.create_baseline(entity, context)
# Save baseline for later comparison
```

### Check for High-Risk Assets

```bash
ctxos risk --input entities.json \
           --engine all \
           --threshold 70 \
           --format csv \
           --output high_risk.csv
```

### Detect Configuration Changes

```bash
ctxos risk --input critical_assets.json \
           --engine drift \
           --baseline baseline.json \
           --threshold 40
```

## 🔧 API Reference

### BaseEngine (Abstract)

```python
class BaseEngine:
    def score(entity: Entity, context: Context) -> ScoringResult
    def configure(config: Dict) -> None
    def validate_config(config: Dict) -> bool
    def enable() -> None
    def disable() -> None
    def get_status() -> Dict
```

### ScoringResult

```python
@dataclass
class ScoringResult:
    engine_name: str           # "risk", "exposure", "drift"
    entity_id: str
    score: float               # 0-100
    severity: str              # "critical", "high", "medium", "low", "info"
    timestamp: datetime
    details: Dict              # Engine-specific details
    metrics: Dict              # Detailed metrics
    recommendations: List      # Actionable recommendations
```

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| Score always 0 | Check entity type is scorable (DOMAIN, IP_ADDRESS, SERVICE, URL) |
| High memory usage | Use `--stream` flag or reduce batch size |
| Slow performance | Enable `--parallel 8` for batch processing |
| Configuration not applied | Call `engine.configure(config)` before scoring |
| Drift score 0 | Create baseline first with `create_baseline()` |

## 📈 Performance

| Operation | Time | Entities |
|-----------|------|----------|
| Single score | ~4ms | 1 |
| Batch | ~400ms | 100 |
| Large batch | ~4s | 1000 |

## 💡 Best Practices

1. **Combine engines** for comprehensive assessment
2. **Establish baselines** for drift detection
3. **Monitor trends** over time
4. **Action quickly** on critical severity
5. **Use parallel processing** for large datasets
6. **Archive results** for historical analysis
7. **Test configurations** on sample data first
8. **Document changes** to baselines

## 🚦 Next Steps

1. ✅ Review [Main README](docs/engines/README.md)
2. ✅ Run test suite: `pytest engines/tests/ -v`
3. ✅ Score sample entities
4. ✅ Review real-world examples in CLI workflows
5. ✅ Integrate with API/CLI
6. ✅ Set up monitoring/alerting

## 📞 Support

- Check [documentation](docs/engines/)
- Review test examples in `engines/tests/`
- Run with `--verbose --log-level debug`
- Check configuration in `configs/engines.yml`

---

**Last Updated**: 2024  
**Status**: Production Ready ✅  
**Test Coverage**: 80%+
