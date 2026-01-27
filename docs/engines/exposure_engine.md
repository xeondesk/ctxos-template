# Exposure Engine Documentation

## Overview

The Exposure Engine measures and scores the attack surface and public exposure of entities, including service availability, protocol accessibility, and security control effectiveness.

## Scoring Formula

```
exposure_score = 0

# Base exposure calculation
if entity_type in EXPOSABLE_TYPES:
    base = (public_exposure × 0.30 + 
            service_exposure × 0.25 + 
            protocol_exposure × 0.20 + 
            subdomain_exposure × 0.15) / total_weight
    
    # Apply security control factors
    waf_factor = 0.8 if waf_detected else 1.0
    cdn_factor = 0.9 if cdn_detected else 1.0
    headers_factor = 1.0 - (security_headers / 10)  # Up to 10 headers
    
    exposure_score = base × waf_factor × cdn_factor × headers_factor
else:
    exposure_score = 0

# Normalize to 0-100
final_score = min(100, exposure_score)
```

## Supported Entity Types

### Exposable Types (Scored)
- **DOMAIN** - Domain registration and web presence
- **IP_ADDRESS** - Network exposure
- **SERVICE** - Application/service exposure
- **URL** - Specific endpoint exposure

### Non-Exposable Types (Score: 0)
- EMAIL - Not public asset
- PERSON - Not network asset
- FILE - Local storage, not exposed
- COMPANY - Abstract entity
- CREDENTIAL - Not exposed asset itself
- [Others] - Default 0

## Scoring Factors

### 1. Public Accessibility (30% weight)
- **Purpose**: Is entity publicly accessible?
- **Impact**: 0-50 base points
- **Signals**:
  - DNS publicly resolvable = +30 points
  - HTTP(S) accessible = +20 points
  - Public IP address = +25 points

**Example**:
```
Public domain with HTTP access = 30 + 20 = 50 points (max)
Private IP address = 0 points
```

### 2. Service Exposure (25% weight)
- **Purpose**: How many services are exposed?
- **Impact**: 0-75 base points depending on service type
- **Signals**: OPEN_PORT signals with port numbers

**Port Classification**:
- **Critical** (35 points each): 3306, 5432, 27017, 1433, 1521
  - Databases = direct data access
- **High** (25 points each): 22, 23, 3389
  - Remote access = system compromise
- **Medium** (15 points each): 80, 443, 8080, 8443
  - Web services = application compromise
- **Low** (5 points each): Other common services

**Example**:
```
Single MySQL database (critical) = 35 points
Multiple web services (HTTP, HTTPS) = 15 + 15 = 30 points
SSH exposed = 25 points
```

### 3. Protocol Exposure (20% weight)
- **Purpose**: Variety of exposed protocols increases attack surface
- **Impact**: 0-60 base points
- **Calculation**: 1 point per unique protocol
- **Signals**: HTTP_HEADER, CERTIFICATE signals

**Protocols Detected**:
- HTTP/HTTPS (web)
- SSH (secure shell)
- RDP (remote desktop)
- FTP/SFTP (file transfer)
- DNS (name service)
- SMTP/POP3/IMAP (email)
- Database protocols
- Custom application protocols

**Example**:
```
HTTP + HTTPS + SSH = 3 protocols × 20 = 60 points
HTTP only = 1 protocol × 20 = 20 points
```

### 4. Subdomain Exposure (15% weight)
- **Purpose**: More subdomains = larger surface
- **Impact**: 0-45 base points
- **Calculation**: 3 points per subdomain (capped at 15)
- **Signals**: DOMAIN_REGISTRATION signal with subdomain count

**Example**:
```
5 subdomains = min(15, 5 × 3) = 15 points
2 subdomains = 6 points
15+ subdomains = 45 points (cap)
```

### 5. Security Controls (Multiplier)
- **Purpose**: Reduce exposure score if controls present
- **WAF Detection**: ×0.8 multiplier (20% reduction)
- **CDN Detection**: ×0.9 multiplier (10% reduction)
- **Both**: ×0.72 multiplier (combined 28% reduction)

**Example**:
```
Base exposure: 50
With WAF: 50 × 0.8 = 40
With WAF + CDN: 50 × 0.72 = 36
```

### 6. Security Headers (Additional Reduction)
- **Purpose**: Missing security headers increase exposure
- **Headers Checked**:
  - Content-Security-Policy
  - X-Frame-Options
  - X-Content-Type-Options
  - Strict-Transport-Security
  - X-XSS-Protection
  - Referrer-Policy
  - Permissions-Policy
  - And others (up to 10)

- **Calculation**: 1% reduction per header present
- **Maximum Reduction**: 10%

**Example**:
```
Base score: 50
6 headers present = 50 × 0.94 = 47
Missing headers increases risk
```

## Configuration

**File**: `configs/engines.yml`

```yaml
engines:
  exposure:
    enabled: true
    version: 1.0.0
    
    # Exposure weights (should sum to 100)
    public_weight: 30
    service_weight: 25
    protocol_weight: 20
    subdomain_weight: 15
    
    # Service port classifications
    critical_ports:
      - 3306    # MySQL
      - 5432    # PostgreSQL
      - 27017   # MongoDB
      - 1433    # MSSQL
      - 1521    # Oracle
    
    high_ports:
      - 22      # SSH
      - 23      # Telnet
      - 3389    # RDP
    
    medium_ports:
      - 80      # HTTP
      - 443     # HTTPS
      - 8080    # HTTP Alt
      - 8443    # HTTPS Alt
    
    # Port scoring
    port_scores:
      critical: 35
      high: 25
      medium: 15
      low: 5
    
    # Security control factors
    waf_reduction: 0.8      # Reduce by 20%
    cdn_reduction: 0.9      # Reduce by 10%
    
    # Header scoring
    security_header_max: 10
    header_reduction_per: 0.01  # 1% per header
```

## Usage Examples

### Basic Usage

```python
from engines.exposure.exposure_engine import ExposureEngine
from core.models import Entity, Signal, Context

# Initialize engine
engine = ExposureEngine()
engine.configure({
    'public_weight': 30,
    'critical_ports': [3306, 5432, 27017]
})

# Create domain entity with signals
entity = Entity(id="domain-1", type="DOMAIN", name="api.example.com")
signals = [
    Signal(type="OPEN_PORT", port=443, severity="medium"),  # HTTPS
    Signal(type="OPEN_PORT", port=80, severity="low"),      # HTTP
    Signal(type="DOMAIN_REGISTRATION", count_subdomains=3)
]
context = Context(entities=[entity], signals=signals)

# Score exposure
result = engine.score(entity, context)
print(f"Exposure Score: {result.score}, Severity: {result.severity}")
# Output: Exposure Score: 45, Severity: MEDIUM
```

### Service Exposure Analysis

```python
# Database server fully exposed
db_entity = Entity(id="ip-db", type="IP_ADDRESS", ip="10.0.0.5")
db_signals = [
    Signal(type="OPEN_PORT", port=3306, severity="critical"),  # MySQL
    Signal(type="OPEN_PORT", port=22, severity="high"),        # SSH
]

result = engine.score(db_entity, Context(entities=[db_entity], signals=db_signals))
print(f"Database exposure: {result.score}")  # High score (critical service exposed)
```

### WAF-Protected Service

```python
# Web service behind WAF
web_entity = Entity(id="web-1", type="DOMAIN", name="www.example.com")
web_signals = [
    Signal(type="OPEN_PORT", port=443, severity="medium"),
    Signal(type="CERTIFICATE", has_waf=True),  # WAF detected
]

result = engine.score(web_entity, Context(entities=[web_entity], signals=web_signals))
print(f"Protected exposure: {result.score}")  # Lower due to WAF mitigation
```

## Severity Mapping

```
Score Range    Severity      Attack Surface
80-100        CRITICAL      Massive exposure
60-79         HIGH          Significant exposure
40-59         MEDIUM        Moderate exposure
20-39         LOW           Limited exposure
0-19          INFO          Minimal/No exposure
```

## Examples

### Example 1: Fully Exposed Database Server

```json
{
  "entity": {
    "id": "ip-001",
    "type": "IP_ADDRESS",
    "ip": "203.0.113.50"
  },
  "signals": [
    {"type": "OPEN_PORT", "port": 3306, "severity": "critical"},  // MySQL
    {"type": "OPEN_PORT", "port": 5432, "severity": "critical"},  // PostgreSQL
    {"type": "OPEN_PORT", "port": 22, "severity": "high"}         // SSH
  ],
  "scoring": {
    "public_access": 50,
    "service_exposure": "2 critical × 35 + 1 high × 25 = 95 (capped at 75)",
    "protocol_exposure": 3,
    "security_controls": "None detected",
    "final_score": 85,
    "severity": "CRITICAL"
  },
  "recommendations": [
    "Restrict database access immediately",
    "Deploy WAF or rate limiting",
    "Move databases behind firewall",
    "Implement network segmentation"
  ]
}
```

### Example 2: CDN-Protected Web Service

```json
{
  "entity": {
    "id": "domain-001",
    "type": "DOMAIN",
    "name": "cdn.example.com"
  },
  "signals": [
    {"type": "OPEN_PORT", "port": 443, "severity": "medium"},
    {"type": "OPEN_PORT", "port": 80, "severity": "low"},
    {"type": "CERTIFICATE", "cdn_provider": "cloudflare"},
    {"type": "DOMAIN_REGISTRATION", "subdomain_count": 8},
    {"type": "HTTP_HEADER", "security_headers": 7}
  ],
  "scoring": {
    "public_access": 40,
    "service_exposure": 30,
    "protocol_exposure": 20,
    "subdomain_exposure": 24,
    "base_score": 114,
    "cdn_factor": 0.9,
    "header_factor": 0.93,
    "final_score": 95 * 0.9 * 0.93 = 80,
    "severity": "HIGH"
  },
  "recommendations": [
    "Reduce number of exposed subdomains",
    "Add missing security headers",
    "Review subdomain access controls",
    "Monitor CDN usage for anomalies"
  ]
}
```

### Example 3: Private Service (No Exposure)

```json
{
  "entity": {
    "id": "service-001",
    "type": "SERVICE",
    "name": "internal-api"
  },
  "signals": [
    {"type": "OPEN_PORT", "port": 8080, "internal": true}
  ],
  "scoring": {
    "entity_type": "SERVICE - exposable type",
    "public_access": 0,
    "service_exposure": 0,
    "protocol_exposure": 0,
    "final_score": 0,
    "severity": "INFO"
  },
  "recommendations": [
    "Ensure service remains internal-only",
    "Continue current security posture"
  ]
}
```

## API Reference

```python
class ExposureEngine(BaseEngine):
    def score(entity: Entity, context: Context) -> ScoringResult:
        """Score entity exposure surface. Returns 0-100 score."""
    
    def _is_exposable_entity(entity: Entity) -> bool:
        """Check if entity type is exposable."""
    
    def _calculate_public_exposure(context: Context) -> float:
        """Calculate public accessibility score."""
    
    def _calculate_service_exposure(context: Context) -> float:
        """Calculate exposed services score."""
    
    def _calculate_protocol_exposure(signals: List[Signal]) -> float:
        """Calculate protocol diversity score."""
    
    def _apply_security_controls(score: float, entity: Entity) -> float:
        """Apply WAF/CDN/header multipliers."""
```

## Testing

```bash
# Run all Exposure Engine tests
pytest engines/tests/test_exposure_engine.py -v

# Run specific test category
pytest engines/tests/test_exposure_engine.py -k "service_exposure" -v

# Run with coverage
pytest engines/tests/test_exposure_engine.py --cov=engines.exposure
```

## Performance

- **Single Entity**: ~2ms (slightly slower due to protocol detection)
- **100 Entities**: ~200ms
- **1000 Entities**: ~2s

## Troubleshooting

### Issue: Non-exposable types return score 0
- **Cause**: Correct behavior for EMAIL, PERSON, FILE types
- **Solution**: Only use with DOMAIN, IP_ADDRESS, SERVICE, URL

### Issue: Score doesn't change with security controls
- **Cause**: WAF/CDN detection signals missing
- **Solution**: Ensure CERTIFICATE signal includes cdn_provider field

### Issue: Subdomain exposure too high
- **Cause**: Every subdomain counted equally
- **Solution**: Review subdomain enumeration; filter false positives

## Limitations

1. **Port detection**: Assumes port scans accurate
2. **WAF detection**: Requires HTTP headers analysis
3. **Header scoring**: Fixed weight per header (not adaptive)
4. **Entity filtering**: Cannot score non-network entities

## Future Enhancements

1. SSL/TLS certificate weakness scoring
2. API endpoint discovery and scoring
3. Domain reputation scoring
4. Geolocation-based exposure
5. Service fingerprinting for vulnerability association
6. DDoS protection detection (Akamai, Imperva, etc.)
7. Bot/crawler access analysis
