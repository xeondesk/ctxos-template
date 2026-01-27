# Engine CLI Workflows

## Overview

This guide demonstrates how to use the CtxOS engines through the command-line interface for practical security assessment workflows.

## Basic Commands

### Score an Entity

```bash
# Score single entity with all engines
ctxos risk --entity example.com

# Output:
# Entity: example.com
# Risk Score: 65 (HIGH)
# Exposure Score: 45 (MEDIUM)
# Drift Score: 15 (LOW)
# Combined Score: 47 (MEDIUM)
```

### Specify Engine

```bash
# Score with risk engine only
ctxos risk --engine risk --entity example.com

# Score with multiple engines
ctxos risk --engine risk,exposure --entity example.com

# Score with all engines (default)
ctxos risk --engine all --entity example.com
```

### Set Threshold

```bash
# Show only HIGH and CRITICAL severity
ctxos risk --entity example.com --severity high,critical

# Show only scores above 50
ctxos risk --entity example.com --threshold 50
```

## Batch Scoring

### Score from File

```bash
# Score entities from JSON file
ctxos risk --input entities.json --engine all

# entities.json format:
# [
#   {"id": "domain-1", "type": "DOMAIN", "name": "example.com"},
#   {"id": "ip-1", "type": "IP_ADDRESS", "ip": "203.0.113.50"}
# ]
```

### Score from CSV

```bash
# Score from CSV with entity data
ctxos risk --input entities.csv --engine all

# entities.csv format:
# id,type,name/ip,signals
# domain-1,DOMAIN,example.com,"VULNERABILITY:critical,OPEN_PORT:443"
# ip-1,IP_ADDRESS,203.0.113.50,"OPEN_PORT:3306"
```

### Score from Database

```bash
# Query entities from database and score
ctxos risk --db postgresql://user:pass@localhost/ctxos \
           --query "SELECT * FROM entities WHERE type='DOMAIN'" \
           --engine all
```

## Output Formats

### JSON Output

```bash
ctxos risk --entity example.com --format json
```

Output:
```json
{
  "entity": {
    "id": "domain-1",
    "type": "DOMAIN",
    "name": "example.com"
  },
  "results": {
    "risk": {
      "score": 65,
      "severity": "high",
      "details": {
        "vulnerabilities": 3,
        "critical_ports": 1
      },
      "recommendations": [
        "Patch 3 known vulnerabilities"
      ]
    },
    "exposure": {
      "score": 45,
      "severity": "medium",
      "details": {
        "public": true,
        "services_exposed": 2
      }
    },
    "combined": {
      "score": 47,
      "severity": "medium"
    }
  }
}
```

### CSV Output

```bash
ctxos risk --input entities.csv --format csv --output results.csv
```

Output (results.csv):
```
entity_id,entity_type,risk_score,risk_severity,exposure_score,exposure_severity,combined_score,combined_severity
domain-1,DOMAIN,65,high,45,medium,47,medium
ip-1,IP_ADDRESS,85,critical,72,high,80,critical
```

### Table Output (Default)

```bash
ctxos risk --input entities.json --format table

# ┌──────────────┬──────────┬──────────────┬────────────────┬─────────┐
# │ Entity       │ Risk     │ Exposure     │ Drift          │ Combined│
# ├──────────────┼──────────┼──────────────┼────────────────┼─────────┤
# │ example.com  │ 65 HIGH  │ 45 MEDIUM    │ 15 LOW         │ 47 MED  │
# │ 203.0.113.50 │ 85 CRIT  │ 72 HIGH      │ 28 LOW         │ 80 CRIT │
# └──────────────┴──────────┴──────────────┴────────────────┴─────────┘
```

## Real-World Workflows

### Workflow 1: Security Assessment

**Goal**: Identify highest-risk assets in organization

```bash
# 1. Export all entities to JSON
ctxos collect --type all --format json --output all_entities.json

# 2. Score all entities with all engines
ctxos risk --input all_entities.json \
           --engine all \
           --format json \
           --output risk_assessment.json

# 3. Filter for HIGH and CRITICAL
ctxos risk --input risk_assessment.json \
           --threshold 60 \
           --format table

# 4. Generate report
ctxos graph --input risk_assessment.json \
            --format html \
            --output assessment_report.html
```

### Workflow 2: Compliance Checking

**Goal**: Verify no critical exposures exist

```bash
# Score all exposed services
ctxos risk --input entities.json \
           --engine exposure \
           --severity critical,high \
           --format csv \
           --output exposed_services.csv

# Verify results are empty (no critical exposures)
if [ $(wc -l < exposed_services.csv) -eq 1 ]; then
    echo "✓ No critical exposures detected"
else
    echo "✗ Critical exposures found - see exposed_services.csv"
fi
```

### Workflow 3: Change Detection

**Goal**: Monitor for unauthorized configuration changes

```bash
# Establish baseline for critical assets
ctxos risk --input critical_assets.json \
           --engine drift \
           --create-baseline \
           --output baseline.json

# Schedule daily drift checks
# (Cron job or scheduled task)
ctxos risk --input critical_assets.json \
           --engine drift \
           --baseline baseline.json \
           --threshold 40 \
           --format email \
           --recipients security@company.com

# Receive alert if drift score >= 40
```

### Workflow 4: Incident Response

**Goal**: Quickly assess compromised asset

```bash
# Get full assessment of potentially compromised entity
ctxos risk --entity 192.168.1.100 \
           --engine all \
           --verbose \
           --format json

# Output includes:
# - Risk score and signals
# - Exposure assessment
# - Configuration drift from baseline
# - Detailed recommendations

# Feed results to incident management system
ctxos risk --entity 192.168.1.100 \
           --engine all \
           --format json | \
  jq -r '.results.*.recommendations[]' | \
  while read rec; do
    echo "- $rec"
  done
```

### Workflow 5: Periodic Risk Review

**Goal**: Monthly risk trend analysis

```bash
# Score all entities this month
ctxos risk --input all_entities.json \
           --engine all \
           --timestamp $(date -u +%Y-%m-%d) \
           --format json \
           --output risk_$(date +%Y%m%d).json

# Compare to last month
python3 compare_risk_trends.py \
    risk_20240101.json \
    risk_20240201.json \
    --output trend_analysis.csv

# Generate dashboard
ctxos graph --input trend_analysis.csv \
            --type timeline \
            --format dashboard \
            --output dashboard.html
```

## Advanced Options

### Configuration Tuning

```bash
# Use custom engine weights
ctxos risk --entity example.com \
           --config custom_engines.yml

# custom_engines.yml:
# engines:
#   risk:
#     vulnerability_weight: 40  # Increase from 25
#     credential_weight: 30     # Increase from 20
#   exposure:
#     public_weight: 40         # Increase from 30
```

### Verbose Logging

```bash
# Show detailed scoring calculations
ctxos risk --entity example.com --verbose --log-level debug

# Output:
# [DEBUG] Initializing RiskEngine
# [DEBUG] Loading configuration from configs/engines.yml
# [DEBUG] Scoring entity: example.com (DOMAIN)
# [DEBUG] Found 3 vulnerability signals
# [DEBUG] Vulnerability score contribution: 15 points
# [DEBUG] Found 1 critical port (MySQL)
# [DEBUG] Port score contribution: 35 points
# [DEBUG] Final risk score: 65 (HIGH)
```

### Parallel Processing

```bash
# Score large datasets in parallel
ctxos risk --input huge_entity_list.json \
           --engine all \
           --parallel 8 \
           --format json \
           --output results.json
```

### Real-Time Monitoring

```bash
# Continuous monitoring of critical assets
ctxos risk --input critical_assets.json \
           --engine drift \
           --monitor \
           --interval 3600 \
           --alert-threshold 50 \
           --alert-webhook https://webhook.company.com/security
```

## Integration Examples

### Integrate with SIEM

```bash
# Send scoring results to Splunk
ctxos risk --input entities.json \
           --engine all \
           --format splunk-hec \
           --output-url https://splunk.company.com:8088 \
           --output-token <hec_token>
```

### Integrate with Ticketing System

```bash
# Create tickets for critical issues
ctxos risk --input entities.json \
           --engine all \
           --threshold 80 \
           --create-tickets \
           --ticket-system jira \
           --jira-url https://jira.company.com \
           --jira-project SEC
```

### Integrate with Slack

```bash
# Send summary to Slack channel
ctxos risk --input entities.json \
           --engine all \
           --slack-webhook https://hooks.slack.com/services/XXX \
           --slack-channel security \
           --summary-only
```

## Script Examples

### Python Script: Batch Scoring

```python
#!/usr/bin/env python3
from ctxos.api.client import CtxOSClient
from ctxos.core.models import Entity, Context

# Initialize client
client = CtxOSClient()

# Load entities
entities = [
    Entity(id="domain-1", type="DOMAIN", name="example.com"),
    Entity(id="domain-2", type="DOMAIN", name="test.com"),
]

# Create context with signals from collectors
context = client.collect(entities)

# Score with all engines
risk_results = []
for entity in entities:
    result = client.score_risk(entity, context)
    exposure_result = client.score_exposure(entity, context)
    drift_result = client.score_drift(entity, context)
    
    combined = {
        "entity": entity.id,
        "risk": result.score,
        "exposure": exposure_result.score,
        "drift": drift_result.score,
        "combined": (result.score * 0.5 + 
                     exposure_result.score * 0.3 + 
                     drift_result.score * 0.2)
    }
    risk_results.append(combined)

# Output results
for r in sorted(risk_results, key=lambda x: x['combined'], reverse=True):
    print(f"{r['entity']}: {r['combined']:.0f}")
```

### Bash Script: Daily Risk Check

```bash
#!/bin/bash

# Daily risk assessment script
ENTITIES_FILE="entities.json"
OUTPUT_DIR="risk_reports"
DATE=$(date +%Y%m%d)

# Create output directory
mkdir -p $OUTPUT_DIR

# Run scoring
echo "Running daily risk assessment..."
ctxos risk --input $ENTITIES_FILE \
           --engine all \
           --format json \
           --output $OUTPUT_DIR/risk_$DATE.json

# Identify critical issues
echo "Checking for critical issues..."
CRITICAL=$(jq '[.results[] | select(.combined.score >= 80)]' \
           $OUTPUT_DIR/risk_$DATE.json)

if [ $(echo $CRITICAL | jq 'length') -gt 0 ]; then
    echo "⚠️  Critical issues found!"
    echo $CRITICAL | jq '.' | mail -s "Critical Issues Detected" \
                            security@company.com
else
    echo "✓ No critical issues detected"
fi

# Generate report
echo "Generating report..."
ctxos graph --input $OUTPUT_DIR/risk_$DATE.json \
            --type summary \
            --format html \
            --output $OUTPUT_DIR/report_$DATE.html

echo "Assessment complete. Results in $OUTPUT_DIR/"
```

## Troubleshooting

### Issue: Slow Scoring Performance

```bash
# Use parallel processing
ctxos risk --input entities.json --parallel 8

# Or use batch mode
ctxos risk --input entities.json --batch-size 100
```

### Issue: Out of Memory on Large Datasets

```bash
# Stream results instead of loading all
ctxos risk --input entities.json \
           --stream \
           --format csv \
           --output results.csv
```

### Issue: Scores Seem Wrong

```bash
# Show detailed calculation steps
ctxos risk --entity example.com \
           --engine risk \
           --verbose \
           --log-level debug | grep -A 20 "Risk calculation"
```

## Performance Tips

1. **Use `--parallel` for batch jobs**: 4-8 workers recommended
2. **Filter early with `--threshold`**: Reduce output size
3. **Use CSV for large outputs**: JSON loads full results in memory
4. **Enable `--stream` for huge datasets**: Prevents memory issues
5. **Schedule batch jobs during off-hours**: Avoid production impact

## Best Practices

1. **Validate input data before scoring**: Use `ctxos validate --input entities.json`
2. **Version your configs**: Keep configs in version control
3. **Monitor engine performance**: Enable `--stats` flag
4. **Archive results**: Keep historical data for trend analysis
5. **Use consistent timestamps**: All results use UTC
6. **Document custom configurations**: Explain any non-standard weights
7. **Test with small samples first**: Before running large batches
8. **Verify integrations**: Test webhook/SIEM integration before deployment

## Command Reference

```bash
# Display full help
ctxos risk --help

# Common flags
--entity <name>              # Score single entity
--input <file>               # Load entities from file
--engine <list>              # Specify engines (risk,exposure,drift)
--threshold <score>          # Filter by minimum score
--severity <list>            # Filter by severity
--format <type>              # Output format (json,csv,table)
--output <file>              # Save results to file
--verbose                    # Show detailed output
--log-level <level>          # Logging level (debug,info,warn,error)
--parallel <count>           # Parallel worker count
--stream                     # Stream mode (memory efficient)
--config <file>              # Custom engine config
--baseline <file>            # Drift engine baseline
--create-baseline            # Create new baseline
--timestamp <iso-datetime>   # Specify assessment time
--db <url>                   # Database connection string
--query <sql>                # SQL query for entities
```

## See Also

- [Engine Architecture](engine_architecture.md)
- [Risk Engine](risk_engine.md)
- [Exposure Engine](exposure_engine.md)
- [Drift Engine](drift_engine.md)
- [Engine Testing](engine_testing.md)
