# Risk Engine Documentation

## Overview

The Risk Engine assesses entity vulnerability and security risk by analyzing signals indicating compromises, exposures, and security incidents.

## Scoring Formula

```
base_score = (vulnerabilities × v_weight + open_ports × p_weight + 
              credential_exposure × c_weight + 
              suspicious_activity × a_weight) / total_weight

severity_multiplier = 1.0 + (critical_signals × 0.5) + (high_signals × 0.2)
age_decay = 1.0 - (days_old / 1000)  # 0.1% per day

final_score = min(100, base_score × severity_multiplier × age_decay)
```

## Scoring Factors

### 1. Vulnerability Count
- **Weight**: 25% (configurable)
- **Calculation**: Number of detected CVEs
- **Impact**: 2 points per vulnerability (up to 50 base points)
- **Signal Type**: VULNERABILITY

**Example**:
```
5 vulnerabilities × 2 points = 10 base contribution
10 × (0.25 / 0.25) = 10 toward final score
```

### 2. Open Port Exposure
- **Weight**: 15%
- **Calculation**: Number and criticality of exposed ports
- **Impact**: 1 point per normal port, 5 points for critical ports
- **Signal Type**: OPEN_PORT
- **Critical Ports**: 3306 (MySQL), 5432 (PostgreSQL), 27017 (MongoDB), 1433 (MSSQL)

**Example**:
```
Port 22 (SSH) = 1 point
Port 3306 (MySQL) = 5 points (critical)
Total: 6 points toward exposure scoring
```

### 3. Credential Exposure
- **Weight**: 20% (highest single weight)
- **Calculation**: Presence of credentials in breaches or leaks
- **Impact**: Base score 50+ if any credentials found
- **Signal Type**: CREDENTIAL_EXPOSURE
- **Severity**: Usually marked critical or high

**Example**:
```
Credentials found in breach = +50 base score
Result: Critical severity (score ≥ 70)
```

### 4. Suspicious Activity
- **Weight**: 15%
- **Calculation**: Malware, C&C communication, exploitation attempts
- **Impact**: 3-5 points per incident
- **Signal Type**: MALWARE, SUSPICIOUS_ACTIVITY

**Example**:
```
Malware detected = +5 points
C&C communication = +3 points
Total: +8 points contribution
```

### 5. Age Decay
- **Formula**: 0.1% reduction per day old
- **Purpose**: Older entities naturally have lower risk (less active threats)
- **Rationale**: Security updates, decommissioning, threat mitigation over time
- **Cap**: Minimum score doesn't go below 0

**Example**:
```
Entity age: 1000 days
Decay factor: 1.0 - (1000 / 10000) = 0.9
Score reduced by 10%
```

## Signal Processing

### Signal Types
- **VULNERABILITY** - CVE data (count and severity)
- **OPEN_PORT** - Exposed network services
- **CREDENTIAL_EXPOSURE** - Password/API key breaches
- **MALWARE** - Malicious software detection
- **SUSPICIOUS_ACTIVITY** - Anomalous behavior
- **DATA_BREACH** - Company-level data compromise

### Severity Multipliers
- **Critical** signals: ×1.5 multiplier
- **High** signals: ×1.2 multiplier
- **Medium** signals: ×1.0 multiplier
- **Low** signals: ×0.8 multiplier
- **Info** signals: ×0.5 multiplier

## Configuration

**File**: `configs/engines.yml`

```yaml
engines:
  risk:
    enabled: true
    version: 1.0.0
    
    # Signal weights (should sum to 100)
    vulnerability_weight: 25
    open_ports_weight: 15
    credential_weight: 20
    activity_weight: 15
    
    # Age decay parameters
    age_decay_per_day: 0.001  # 0.1% per day
    
    # Severity multipliers
    severity_multipliers:
      critical: 1.5
      high: 1.2
      medium: 1.0
      low: 0.8
      info: 0.5
    
    # Critical port definitions
    critical_ports:
      - 3306    # MySQL
      - 5432    # PostgreSQL
      - 27017   # MongoDB
      - 1433    # MSSQL
    
    # Thresholds
    credential_threshold: 1  # Number of exposed credentials to flag
    malware_weight: 5
    open_port_weight: 1
```

## Usage Examples

### Basic Usage

```python
from engines.risk.risk_engine import RiskEngine
from core.models import Entity, Signal, Context

# Initialize engine
engine = RiskEngine()
config = {
    'vulnerability_weight': 25,
    'severity_multipliers': {'critical': 1.5, 'high': 1.2}
}
engine.configure(config)

# Create entity with signals
entity = Entity(id="domain-1", type="DOMAIN", name="example.com")
signals = [
    Signal(type="VULNERABILITY", severity="high", source="cve_db"),
    Signal(type="OPEN_PORT", severity="medium", source="port_scan"),
    Signal(type="CREDENTIAL_EXPOSURE", severity="critical", source="breach_db")
]
context = Context(entities=[entity], signals=signals)

# Score entity
result = engine.score(entity, context)
print(f"Risk Score: {result.score}, Severity: {result.severity}")
```

### Batch Scoring

```python
# Score multiple entities
for entity in context.entities:
    result = engine.score(entity, context)
    print(f"{entity.name}: {result.score} ({result.severity})")
```

### Custom Configuration

```python
custom_config = {
    'vulnerability_weight': 30,  # Increase vulnerability importance
    'severity_multipliers': {
        'critical': 2.0,  # Increase critical severity impact
        'high': 1.5
    }
}
engine.configure(custom_config)
```

## Recommendations

The engine generates recommendations based on risk factors:

### High Risk (score ≥ 70)
```
- "Immediate investigation required: Critical signals detected"
- "Credential exposure confirmed - change all passwords immediately"
- "Active malware detected - initiate incident response"
```

### Medium-High Risk (score 50-69)
```
- "Patch 5 known vulnerabilities urgently"
- "Review open ports: Services exposed unnecessarily"
- "Investigate suspicious activity patterns"
```

### Medium Risk (score 30-49)
```
- "Update to latest patches (2 available)"
- "Monitor for further security incidents"
- "Review security controls and policies"
```

### Low Risk (score < 30)
```
- "Continue routine monitoring"
- "Standard security practices sufficient"
```

## Examples

### Example 1: Heavily Compromised Domain

```json
{
  "entity": {
    "id": "domain-001",
    "type": "DOMAIN",
    "name": "compromised.example.com",
    "discovered": "2023-01-15"
  },
  "signals": [
    {"type": "VULNERABILITY", "severity": "critical", "count": 8},
    {"type": "CREDENTIAL_EXPOSURE", "severity": "critical", "count": 12},
    {"type": "MALWARE", "severity": "high", "count": 3},
    {"type": "OPEN_PORT", "severity": "high", "count": 5}
  ],
  "scoring": {
    "vulnerabilities": "8 × 2 × 1.5 = 24 points",
    "credentials": "50 base × 1.5 = 75 points",
    "malware": "3 × 5 × 1.2 = 18 points",
    "open_ports": "5 × 1 × 1.2 = 6 points",
    "age_decay": "1 year = 0.9 multiplier",
    "final_score": "92 (CRITICAL)"
  },
  "recommendations": [
    "URGENT: Credential exposure - reset all passwords",
    "Active malware detected - initiate incident response immediately",
    "Patch 8 critical vulnerabilities ASAP"
  ]
}
```

### Example 2: Moderately At-Risk IP

```json
{
  "entity": {
    "id": "ip-002",
    "type": "IP_ADDRESS",
    "ip": "192.168.1.100",
    "discovered": "2023-06-01"
  },
  "signals": [
    {"type": "VULNERABILITY", "severity": "high", "count": 2},
    {"type": "OPEN_PORT", "severity": "medium", "count": 3}
  ],
  "scoring": {
    "vulnerabilities": "2 × 2 × 1.2 = 4.8 points",
    "open_ports": "3 × 1 × 1.0 = 3 points",
    "age_decay": "6 months = 0.95 multiplier",
    "final_score": "38 (MEDIUM)"
  },
  "recommendations": [
    "Patch 2 known vulnerabilities",
    "Review exposed service ports",
    "Monitor for additional risks"
  ]
}
```

## Performance Considerations

- **Single Entity**: ~1ms
- **100 Entities**: ~100ms
- **1000 Entities**: ~1s
- Memory: Minimal (no state maintained per default)

## API Reference

```python
class RiskEngine(BaseEngine):
    def score(entity: Entity, context: Context) -> ScoringResult:
        """Score an entity for risk. Returns ScoringResult with 0-100 score."""
    
    def validate_config(config: Dict) -> bool:
        """Validate configuration dictionary."""
    
    def configure(config: Dict) -> None:
        """Apply configuration."""
    
    def get_status() -> Dict:
        """Get engine operational status."""
```

## Testing

The Risk Engine includes comprehensive test coverage:

```bash
# Run all Risk Engine tests
pytest engines/tests/test_risk_engine.py -v

# Run specific test
pytest engines/tests/test_risk_engine.py::test_credential_exposure_weight -v

# Run with coverage
pytest engines/tests/test_risk_engine.py --cov=engines.risk
```

## Troubleshooting

### Issue: Score always 0
- **Cause**: Entity type not in ["DOMAIN", "IP_ADDRESS", "SERVICE", "URL", "EMAIL"]
- **Solution**: Check entity.type value

### Issue: Score too high/low
- **Cause**: Configuration weights not applied
- **Solution**: Call engine.configure(config) before scoring

### Issue: Recommendations empty
- **Cause**: No signals in context
- **Solution**: Ensure signals are properly linked to entity

## Limitations

1. **Age decay**: Minimum score reduced linearly (no floor)
2. **Signal count**: Assumes signal severity correctly classified
3. **Static weights**: Cannot adjust weights per entity type
4. **No learning**: Multipliers fixed, not adaptive

## Future Enhancements

1. Machine learning-based anomaly detection
2. Predictive risk scoring (anticipate future breaches)
3. Peer comparison (entity vs similar entities)
4. Time-series analysis of risk trends
5. Custom risk models per organization
6. Integration with CVSS scoring
