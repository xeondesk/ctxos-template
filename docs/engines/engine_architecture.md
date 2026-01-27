# Engine Architecture Guide

## Overview

The CtxOS Engines layer provides comprehensive scoring and analysis for security entities. Three specialized engines work together to provide risk assessment, exposure measurement, and change detection.

## Engine Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Scoring Engines                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Risk Engine  │  │Exposure      │  │Drift Engine  │      │
│  │              │  │Engine        │  │              │      │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤      │
│  │ - Vuln Score │  │ - Public     │  │ - Property   │      │
│  │ - Signals    │  │   Exposure   │  │   Changes    │      │
│  │ - Age Decay  │  │ - Services   │  │ - Signal     │      │
│  │              │  │ - Protocols  │  │   Changes    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↑
                     BaseEngine (Abstract)
                            ↑
                    ┌────────┴────────┐
                    │                 │
            ScoringResult        ScoringUtils
            (0-100 scores)       (Aggregation)
```

## Core Components

### 1. BaseEngine (Abstract Base Class)

**Purpose**: Defines common interface for all scoring engines

**Key Methods**:
- `score(entity, context)` - Score an entity (abstract, implemented by subclasses)
- `validate_config(config)` - Validate configuration
- `configure(config)` - Apply configuration
- `enable()` / `disable()` - Control engine state
- `get_status()` - Get engine operational status

**Key Attributes**:
- `name` - Engine identifier
- `version` - Engine version
- `enabled` - Operational flag
- `config` - Configuration dictionary
- `run_count` - Number of scoring runs
- `last_run` - Timestamp of last execution

### 2. ScoringResult

**Purpose**: Standardized result format for all engines

**Fields**:
```python
engine_name: str           # Engine that produced result
entity_id: str             # Scored entity ID
score: float               # 0-100 risk/exposure/drift score
severity: str              # critical/high/medium/low/info
timestamp: datetime        # When score was calculated
details: Dict              # Engine-specific details
metrics: Dict              # Detailed metrics breakdown
recommendations: List      # Actionable recommendations
```

### 3. ScoringUtils

**Purpose**: Shared utility functions for score calculation

**Functions**:
- `normalize_score(value, min, max)` - Normalize to 0-100
- `score_to_severity(score)` - Convert score to severity
- `aggregate_scores(scores, weights)` - Combine multiple scores
- `calculate_confidence(data_points, max)` - Confidence 0-1

## Engine Implementations

### Risk Engine

**Purpose**: Assess entity risk based on vulnerabilities, signals, and age

**Scoring Factors**:
- Vulnerability count (25% weight)
- Open ports (15% weight)
- Credential exposure (20% weight)
- Suspicious activity (15% weight)
- Age decay (10% per 100 days old)
- Severity multipliers

**Signal Types Considered**:
- VULNERABILITY - CVE detections
- OPEN_PORT - Exposed services
- CREDENTIAL_EXPOSURE - Password breaches
- MALWARE - Malicious software
- SUSPICIOUS_ACTIVITY - Anomalous behavior
- DATA_BREACH - Data compromise mentions

**Configuration**:
```yaml
vulnerability_weight: 25
open_ports_weight: 15
exposure_weight: 20
activity_weight: 15
age_decay: 0.1
severity_multipliers:
  critical: 1.5
  high: 1.2
  medium: 1.0
  low: 0.8
  info: 0.5
```

### Exposure Engine

**Purpose**: Score asset exposure and attack surface

**Applicable Entity Types**:
- DOMAIN
- IP_ADDRESS
- SERVICE
- URL

**Scoring Factors**:
- Public accessibility (30% weight)
- Exposed services (25% weight)
- Protocol exposure (20% weight)
- Subdomain count (15% weight)
- Security controls reduction (multiplier)

**Signal Types Considered**:
- DOMAIN_REGISTRATION - Subdomains found
- DNS_RECORD - DNS infrastructure
- OPEN_PORT - Exposed services
- HTTP_HEADER - Web exposure
- CERTIFICATE - SSL/TLS information

**Configuration**:
```yaml
public_weight: 30
service_weight: 25
protocol_weight: 20
subdomain_weight: 15
security_controls_factor: 0.8
exposure_type_scores:
  database: 40
  api: 25
  web_service: 30
  ssh: 20
  rdp: 35
```

### Drift Engine

**Purpose**: Detect and score configuration/state changes

**Change Types Detected**:
- Property modifications
- New properties added
- Properties removed
- Signal additions/removals
- Signal severity changes

**Critical Properties** (monitored closely):
- dns_servers
- authentication_method
- firewall_rules
- ssl_certificate
- ip_address
- service_ports

**Scoring Factors**:
- Property changes (30% weight)
- Signal changes (40% weight)
- Unexpected modifications (multiplier)
- Change velocity (changes/day)

**Configuration**:
```yaml
property_change_weight: 30
signal_change_weight: 40
unexpected_change_multiplier: 1.5
drift_threshold_days: 7
critical_property_list:
  - dns_servers
  - authentication_method
  - firewall_rules
  - ssl_certificate
```

## Data Flow

```
Input Context (Entities + Signals)
        ↓
  ┌─────────────────────────────┐
  │  Validate Entity Type       │
  │  Extract Relevant Signals   │
  │  Gather Properties/Metadata │
  └─────────────────────────────┘
        ↓
  ┌─────────────────────────────┐
  │  Calculate Component Scores │
  │  (Risk/Exposure/Drift)      │
  └─────────────────────────────┘
        ↓
  ┌─────────────────────────────┐
  │  Apply Multipliers/Decay    │
  │  Aggregate Sub-scores       │
  └─────────────────────────────┘
        ↓
  ┌─────────────────────────────┐
  │  Determine Severity         │
  │  Generate Recommendations   │
  └─────────────────────────────┘
        ↓
  ScoringResult (0-100, severity, details, recommendations)
```

## Severity Mapping

All engines use unified severity thresholds:

```
Score Range    Severity      Priority
80-100        CRITICAL      Immediate action
60-79         HIGH          Urgent attention
40-59         MEDIUM        Address soon
20-39         LOW           Monitor
0-19          INFO          Informational
```

## Multi-Engine Scoring

Engines can be combined for comprehensive assessment:

```
Weight Distribution (Example):
- Risk Engine:     50% (primary concern)
- Exposure Engine: 30% (asset visibility)
- Drift Engine:    20% (change detection)

Combined Score = (Risk × 0.5) + (Exposure × 0.3) + (Drift × 0.2)
```

## Integration Points

### With Collectors
- Receive signals from collection pipeline
- Enrich entities with scoring results
- Provide feedback for collection tuning

### With Normalizers
- Consume normalized entities
- Operate on deduplicated data
- Tag high-risk entities for priority

### With CLI
- `ctxos risk --engine all` - Score with all engines
- `ctxos risk --input file.json` - Batch scoring
- `ctxos risk --threshold 0.7` - Filter by threshold

### With API
- REST endpoints for scoring
- Batch scoring requests
- Result caching and history

### With Graph
- Link high-risk entities
- Traverse risk relationships
- Identify attack paths

## Configuration

Engine configurations are loaded from `configs/engines.yml`:

```yaml
engines:
  risk:
    enabled: true
    version: 1.0.0
    vulnerability_weight: 25
    severity_multipliers:
      critical: 1.5
  exposure:
    enabled: true
    public_weight: 30
  drift:
    enabled: true
    property_change_weight: 30
```

## Error Handling

- Invalid entity types return 0 score
- Missing signals return baseline score
- Configuration errors logged and handled gracefully
- Exceptions caught and reported in error_count

## Performance Considerations

- Engines are stateless (except drift baseline storage)
- Linear time complexity for most operations
- Parallel execution supported
- Batch scoring optimization for large datasets

## Testing

- 100+ unit tests per engine
- Integration tests for multi-engine workflows
- Edge case coverage
- Serialization/deserialization tests
- Performance benchmarks

## Future Enhancements

1. Machine learning-based risk prediction
2. Historical trend analysis
3. Anomaly detection
4. Custom scoring models
5. Real-time streaming updates
6. Advanced visualization
7. Predictive threat scoring
