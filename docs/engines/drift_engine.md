# Drift Engine Documentation

## Overview

The Drift Engine detects and scores configuration changes and deviations in entity state, identifying unexpected modifications that may indicate compromise, configuration drift, or security incidents.

## Scoring Formula

```
# Baseline established for each entity
baseline = snapshot_of_current_state

# Compare to current state
property_changes = count(properties_modified) + count(properties_added) + count(properties_removed)
signal_changes = count(signals_added) + count(signals_removed) + count(signals_modified)

# Calculate change metrics
property_change_score = property_changes × 10
signal_change_score = signal_changes × 8
critical_property_multiplier = 1.0 + (critical_changes × 0.3)

# Time-based velocity
days_since_baseline = current_time - baseline_timestamp
change_velocity = total_changes / days_since_baseline

# Final scoring
drift_score = (property_change_score × 0.3 + signal_change_score × 0.4)
drift_score *= critical_property_multiplier
drift_score *= min(2.0, 1.0 + (change_velocity / 10))  # Velocity factor (capped)

final_score = min(100, drift_score)
```

## Key Concepts

### Baseline

A baseline is a snapshot of entity state at a point in time:

```python
baseline = {
    "timestamp": datetime.now(),
    "properties": {
        "ip_address": "10.0.0.5",
        "dns_servers": ["8.8.8.8", "8.8.4.4"],
        "authentication_method": "active_directory",
        "firewall_rules": 42,
        "ssl_certificate": "CN=example.com"
    },
    "signals": [
        {"type": "OPEN_PORT", "port": 443},
        {"type": "OPEN_PORT", "port": 80}
    ]
}
```

### Change Types

1. **Property Changes** - Entity attribute modifications
   - IP address changed
   - DNS servers modified
   - Authentication method changed
   - Service ports altered
   
2. **Property Additions** - New properties detected
   - New service added
   - New DNS server configured
   - Additional firewall rule

3. **Property Removals** - Properties disappeared
   - Service removed/decommissioned
   - DNS server deleted
   - Firewall rule removed

4. **Signal Changes** - New/modified security signals
   - Vulnerability discovered
   - New malware detected
   - Credential exposure identified

### Critical Properties

Certain properties are monitored more closely due to security implications:

```python
CRITICAL_PROPERTIES = [
    'dns_servers',              # DNS hijacking
    'authentication_method',    # Auth bypass
    'firewall_rules',           # Access control
    'ssl_certificate',          # Man-in-the-middle
    'ip_address',               # Network redirection
    'service_ports',            # Unauthorized access
    'load_balancer_config',     # Traffic redirection
    'backup_destination',       # Data exfiltration
]
```

When critical properties change, scoring is elevated (×1.3 multiplier).

## Scoring Factors

### 1. Property Changes (30% weight)
- **Purpose**: Detect unexpected modifications
- **Impact**: 10 points per change type
- **Severity**: Depends on property criticality

**Example**:
```
DNS servers changed: 10 points × 1.3 (critical) = 13 points
SSL certificate updated: 10 points × 1.3 (critical) = 13 points
Service port added: 10 points
IP address modified: 10 points × 1.3 (critical) = 13 points
Total: ~50 points contribution to final score
```

### 2. Signal Changes (40% weight - primary indicator)
- **Purpose**: Detect new threats/incidents
- **Impact**: 8 points per signal change
- **Signals Tracked**:
  - VULNERABILITY - CVE detection
  - CREDENTIAL_EXPOSURE - Breach mentions
  - MALWARE - Malicious software
  - SUSPICIOUS_ACTIVITY - Anomalous behavior
  - Data signals

**Example**:
```
New CVE discovered: +8 points
Credential exposure found: +8 points
Malware detected: +8 points
Total: 24 points from signals
```

### 3. Critical Property Multiplier
- **Formula**: 1.0 + (count_critical_changes × 0.3)
- **Purpose**: Emphasize dangerous property changes
- **Cap**: Up to 2.0 multiplier (6+ critical changes)

**Example**:
```
1 critical property changed: 1.0 + 0.3 = 1.3× multiplier
3 critical properties changed: 1.0 + 0.9 = 1.9× multiplier
```

### 4. Change Velocity
- **Formula**: Total changes / days since baseline
- **Purpose**: High change rate indicates instability or attack
- **Impact**: Multiplier 1.0 to 2.0 (capped)

**Example**:
```
5 changes in 1 day = 5 changes/day = 1.5× velocity multiplier
5 changes in 30 days = 0.17 changes/day = 1.02× velocity multiplier
```

## Configuration

**File**: `configs/engines.yml`

```yaml
engines:
  drift:
    enabled: true
    version: 1.0.0
    
    # Change weights
    property_change_weight: 30
    signal_change_weight: 40
    
    # Multipliers
    critical_property_multiplier: 0.3  # Add 30% per critical change
    velocity_multiplier_cap: 2.0
    
    # Time-based thresholds
    drift_threshold_days: 7
    alert_threshold_hours: 24
    
    # Critical properties to monitor
    critical_properties:
      - dns_servers
      - authentication_method
      - firewall_rules
      - ssl_certificate
      - ip_address
      - service_ports
      - load_balancer_config
      - backup_destination
    
    # Recommendation thresholds
    high_drift_score: 60
    medium_drift_score: 40
    velocity_alert_threshold: 5  # changes/day
```

## Usage Examples

### Baseline Creation

```python
from engines.drift.drift_engine import DriftEngine
from core.models import Entity, Signal, Context

# Initialize engine
engine = DriftEngine()

# Create entity and initial signals
entity = Entity(id="server-1", type="IP_ADDRESS", ip="192.168.1.100")
signals = [
    Signal(type="OPEN_PORT", port=443),
    Signal(type="OPEN_PORT", port=22),
]
context = Context(entities=[entity], signals=signals)

# Establish baseline
baseline = engine.create_baseline(entity, context)
print(f"Baseline created: {baseline.timestamp}")
```

### Change Detection

```python
# Later: Detect changes
entity_updated = Entity(id="server-1", type="IP_ADDRESS", ip="192.168.1.100")
signals_updated = [
    Signal(type="OPEN_PORT", port=443),
    Signal(type="OPEN_PORT", port=22),
    Signal(type="OPEN_PORT", port=3306),  # NEW: MySQL exposed
    Signal(type="VULNERABILITY", severity="critical"),  # NEW CVE
]
context_updated = Context(entities=[entity_updated], signals=signals_updated)

# Score drift
result = engine.score(entity_updated, context_updated)
print(f"Drift Score: {result.score}, Changes: {len(result.details['changes'])}")
```

### Critical Property Monitoring

```python
# DNS server changed (critical property)
# Previous: 8.8.8.8, 8.8.4.4
# Current: 1.1.1.1, 1.0.0.1

entity = Entity(id="router-1", type="IP_ADDRESS", ip="192.168.1.1")
entity.dns_servers = ["1.1.1.1", "1.0.0.1"]  # Changed

context = Context(entities=[entity])
result = engine.score(entity, context)

# DNS change = critical property = higher score
print(f"Critical property detected - Score elevated: {result.score}")
print(f"Severity: {result.severity}")  # Likely MEDIUM or HIGH
```

## Recommendations

Based on drift analysis, engine generates recommendations:

### High Drift (score ≥ 60)
```
- "Significant configuration drift detected"
- "Multiple critical properties have changed"
- "Recommend investigation of recent changes"
- "Consider restoring from known-good baseline"
```

### Medium Drift (score 40-59)
```
- "Moderate drift detected - review recent changes"
- "New security signals detected"
- "Verify authorization for configuration changes"
```

### Low Drift (score 20-39)
```
- "Minor configuration changes detected"
- "Review changes against change management policies"
- "Monitor for patterns"
```

### Minimal Drift (score < 20)
```
- "Baseline stable - current changes within normal range"
- "Continue monitoring"
```

## Examples

### Example 1: Compromised Database Server

```json
{
  "entity": {
    "id": "db-prod-1",
    "type": "IP_ADDRESS",
    "ip": "10.0.1.50"
  },
  "baseline": {
    "timestamp": "2024-01-01T12:00:00Z",
    "properties": {
      "authentication_method": "pam_ldap",
      "firewall_rules": 12,
      "ssl_certificate": "CN=db.company.internal",
      "service_ports": [5432]
    },
    "signals": [
      {"type": "OPEN_PORT", "port": 5432}
    ]
  },
  "current": {
    "timestamp": "2024-01-02T08:30:00Z",
    "properties": {
      "authentication_method": "none",  // CHANGED
      "firewall_rules": 14,             // NEW rule
      "ssl_certificate": "CN=suspicious.com",  // CHANGED
      "service_ports": [5432, 22, 3389]  // NEW ports
    },
    "signals": [
      {"type": "OPEN_PORT", "port": 5432},
      {"type": "OPEN_PORT", "port": 22},
      {"type": "OPEN_PORT", "port": 3389},
      {"type": "MALWARE", "severity": "critical"},  // NEW
      {"type": "CREDENTIAL_EXPOSURE", "severity": "critical"}  // NEW
    ]
  },
  "scoring": {
    "property_changes": 3,  // auth, ssl_cert, new ports
    "critical_properties_changed": 3,  // all critical
    "signal_changes": 2,  // malware + credential
    "velocity": 20,  // changes per day
    "calculation": "(3×10×0.3 + 2×8×0.4) × (1+3×0.3) × 2.0",
    "final_score": 92,
    "severity": "CRITICAL"
  },
  "recommendations": [
    "CRITICAL: Multiple critical properties changed",
    "CRITICAL: Malware and credential exposure detected",
    "URGENT: Investigate potential compromise",
    "URGENT: Restore to known-good baseline",
    "URGENT: Check authentication logs for unauthorized access"
  ]
}
```

### Example 2: Authorized Maintenance

```json
{
  "entity": {
    "id": "web-app-1",
    "type": "DOMAIN",
    "name": "app.example.com"
  },
  "baseline": {
    "timestamp": "2024-01-01T00:00:00Z",
    "signals": [
      {"type": "OPEN_PORT", "port": 443},
      {"type": "CERTIFICATE", "issuer": "Let's Encrypt"}
    ]
  },
  "current": {
    "timestamp": "2024-01-10T14:00:00Z",
    "signals": [
      {"type": "OPEN_PORT", "port": 443},
      {"type": "CERTIFICATE", "issuer": "DigiCert"}  // CHANGED (renewal)
    ]
  },
  "scoring": {
    "property_changes": 1,  // SSL certificate renewal (not critical for drift)
    "signal_changes": 0,    // Port same, certificate expected change
    "velocity": 0.1,  // Low velocity (9 days)
    "calculation": "(1×10×0.3 + 0) × 1.0 × 1.0",
    "final_score": 3,
    "severity": "INFO"
  },
  "recommendations": [
    "Minor configuration change (expected)",
    "Certificate renewal completed successfully",
    "Continue monitoring"
  ]
}
```

### Example 3: Network Expansion

```json
{
  "entity": {
    "id": "network-segment-01",
    "type": "DOMAIN",
    "name": "prod.internal"
  },
  "baseline": {
    "timestamp": "2024-01-01T00:00:00Z",
    "properties": {
      "service_count": 3,
      "firewall_rules": 8
    }
  },
  "current": {
    "timestamp": "2024-01-08T10:00:00Z",
    "properties": {
      "service_count": 5,      // NEW services
      "firewall_rules": 12     // NEW rules
    }
  },
  "scoring": {
    "property_changes": 2,  // service_count increased, firewall_rules increased
    "critical_properties": 1,  // firewall_rules is critical
    "velocity": 0.29,  // 2 changes over 7 days
    "calculation": "(2×10×0.3 + 0) × (1+0.3) × 1.03",
    "final_score": 8,
    "severity": "LOW"
  },
  "recommendations": [
    "Network expansion detected (expected)",
    "Verify new services match authorization",
    "Review firewall rule changes for correctness"
  ]
}
```

## API Reference

```python
class DriftEngine(BaseEngine):
    def score(entity: Entity, context: Context) -> ScoringResult:
        """Score configuration drift. Returns 0-100 score."""
    
    def create_baseline(entity: Entity, context: Context) -> Baseline:
        """Create baseline snapshot for entity."""
    
    def update_baseline(entity: Entity, context: Context) -> Baseline:
        """Update baseline to current state."""
    
    def detect_changes(entity: Entity, baseline: Baseline, context: Context) -> Dict:
        """Detect changes since baseline."""
    
    def _detect_property_changes(current, baseline) -> List:
        """Detect property modifications."""
    
    def _detect_signal_changes(signals: List[Signal], baseline_signals) -> Dict:
        """Detect signal additions/removals."""
```

## Baseline Management

### Storage
Baselines are stored per entity to enable change detection:

```python
baselines = {
    "entity-1": {
        "timestamp": "2024-01-01T12:00:00Z",
        "properties": {...},
        "signals": [...]
    },
    "entity-2": {
        "timestamp": "2024-01-02T08:30:00Z",
        "properties": {...},
        "signals": [...]
    }
}
```

### Baseline Updates
Call `update_baseline()` after authorized changes:

```python
# After successful maintenance
new_baseline = engine.update_baseline(entity, context)
print(f"Baseline updated: {new_baseline.timestamp}")
```

## Testing

```bash
# Run all Drift Engine tests
pytest engines/tests/test_drift_engine.py -v

# Run baseline tests
pytest engines/tests/test_drift_engine.py -k "baseline" -v

# Run critical property tests
pytest engines/tests/test_drift_engine.py -k "critical" -v

# Run with coverage
pytest engines/tests/test_drift_engine.py --cov=engines.drift
```

## Performance

- **Single Entity**: ~1-2ms
- **100 Entities**: ~150ms
- **1000 Entities**: ~1.5s
- **Baseline Storage**: Minimal (per entity)

## Troubleshooting

### Issue: Drift score high after expected maintenance
- **Cause**: Baseline not updated
- **Solution**: Call `engine.update_baseline()` after changes

### Issue: Drift score always 0
- **Cause**: No baseline established
- **Solution**: Call `engine.create_baseline()` first

### Issue: False positives on property changes
- **Cause**: Property order or minor variations detected
- **Solution**: Normalize properties before comparison

## Limitations

1. **Baseline storage**: Requires persistent storage per entity
2. **Property comparison**: Exact match (no fuzzy matching)
3. **Time sensitivity**: Velocity calculations depend on timestamp accuracy
4. **Critical list**: Fixed set of critical properties

## Future Enhancements

1. Machine learning for anomaly detection
2. Peer comparison (entity vs similar entities)
3. Automated baseline suggestions
4. Approval workflow for known-good changes
5. Integration with change management systems
6. Predictive drift analysis
7. Rollback capability
8. Change reason tracking and documentation
