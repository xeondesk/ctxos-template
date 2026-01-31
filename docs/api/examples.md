# CtxOS API Examples

This document provides practical examples of using the CtxOS API for common use cases.

## Table of Contents

1. [Authentication Examples](#authentication-examples)
2. [Scoring Examples](#scoring-examples)
3. [Agent Analysis Examples](#agent-analysis-examples)
4. [Configuration Examples](#configuration-examples)
5. [Batch Processing Examples](#batch-processing-examples)
6. [Integration Examples](#integration-examples)
7. [Error Handling Examples](#error-handling-examples)

## Authentication Examples

### Basic Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

### Login and Store Token

```bash
# Login and save token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | \
  jq -r '.access_token')

echo "Token: $TOKEN"
```

### Token Refresh

```bash
# Get refresh token from login response
REFRESH_TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | \
  jq -r '.refresh_token')

# Use refresh token to get new access token
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"
```

### Verify Token

```bash
curl -X GET "http://localhost:8000/api/v1/auth/verify" \
  -H "Authorization: Bearer $TOKEN"
```

## Scoring Examples

### Score a Single Host

```bash
curl -X POST "http://localhost:8000/api/v1/score" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "entity": {
        "id": "web-server-01",
        "entity_type": "host",
        "name": "web-server-01.example.com",
        "properties": {
          "environment": "production",
          "os": "Ubuntu 20.04",
          "ip_address": "192.168.1.100"
        }
      },
      "signals": [
        {
          "id": "vuln-001",
          "source": "nessus",
          "signal_type": "vulnerability",
          "severity": "critical",
          "description": "CVE-2023-1234: Apache Struts RCE",
          "properties": {
            "cvss_score": 9.8,
            "cve_id": "CVE-2023-1234",
            "affected_service": "apache2"
          }
        },
        {
          "id": "port-001",
          "source": "nmap",
          "signal_type": "port",
          "severity": "medium",
          "description": "Open port 8080",
          "properties": {
            "port": 8080,
            "service": "http-proxy",
            "state": "open"
          }
        }
      ]
    },
    "engines": ["risk"],
    "include_recommendations": true
  }'
```

### Score with Multiple Engines

```bash
curl -X POST "http://localhost:8000/api/v1/score" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "entity": {
        "id": "db-server-01",
        "entity_type": "host",
        "name": "db-server-01",
        "properties": {
          "environment": "production"
        }
      },
      "signals": []
    },
    "engines": ["risk", "exposure", "drift"],
    "include_recommendations": true
  }'
```

### Batch Scoring

```bash
curl -X POST "http://localhost:8000/api/v1/score/batch" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "contexts": [
      {
        "entity": {
          "id": "host-001",
          "entity_type": "host",
          "name": "web-01"
        },
        "signals": []
      },
      {
        "entity": {
          "id": "host-002",
          "entity_type": "host",
          "name": "web-02"
        },
        "signals": []
      },
      {
        "entity": {
          "id": "host-003",
          "entity_type": "host",
          "name": "db-01"
        },
        "signals": []
      }
    ],
    "engines": ["risk"],
    "parallel": true
  }'
```

### Get Historical Scores

```bash
curl -X POST "http://localhost:8000/api/v1/score/history/web-server-01" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2024-01-01T00:00:00Z",
    "date_to": "2024-01-31T23:59:59Z",
    "engines": ["risk"],
    "granularity": "daily",
    "limit": 31
  }'
```

### Compare Entity Scores

```bash
curl -X POST "http://localhost:8000/api/v1/score/compare" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_ids": ["web-server-01", "web-server-02", "db-server-01"],
    "engines": ["risk"]
  }'
```

## Agent Analysis Examples

### Run Single Agent

```bash
# Context Summarizer
curl -X POST "http://localhost:8000/api/v1/agents/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "context_summarizer",
    "context": {
      "entity": {
        "id": "critical-host",
        "entity_type": "host",
        "name": "production-web-01"
      },
      "signals": [
        {
          "id": "vuln-critical",
          "signal_type": "vulnerability",
          "severity": "critical",
          "description": "Remote code execution vulnerability"
        }
      ]
    },
    "timeout_seconds": 30.0
  }'
```

### Run Agent with Scoring Results

```bash
# Explainability Agent with scoring context
curl -X POST "http://localhost:8000/api/v1/agents/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "explainability",
    "context": {
      "entity": {
        "id": "host-001",
        "entity_type": "host",
        "name": "server-01"
      },
      "signals": []
    },
    "scoring_result": {
      "score": 85.0,
      "severity": "high",
      "factors": {
        "vulnerability_score": 40,
        "exposure_score": 25,
        "configuration_score": 20
      }
    },
    "timeout_seconds": 45.0
  }'
```

### Run Predefined Pipeline

```bash
# Full security analysis pipeline
curl -X POST "http://localhost:8000/api/v1/agents/pipeline" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_name": "full_analysis",
    "context": {
      "entity": {
        "id": "target-host",
        "entity_type": "host",
        "name": "target-server"
      },
      "signals": [
        {
          "id": "vuln-001",
          "signal_type": "vulnerability",
          "severity": "high",
          "description": "Multiple vulnerabilities detected"
        }
      ]
    },
    "timeout_seconds": 120.0
  }'
```

### Run Custom Pipeline

```bash
# Custom parallel pipeline
curl -X POST "http://localhost:8000/api/v1/agents/pipeline" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agents": ["context_summarizer", "gap_detector"],
    "context": {
      "entity": {
        "id": "test-host",
        "entity_type": "host",
        "name": "test-server"
      },
      "signals": []
    },
    "parallel": true,
    "timeout_seconds": 60.0
  }'
```

### Bulk Analysis

```bash
# Analyze multiple entities
curl -X POST "http://localhost:8000/api/v1/agents/bulk" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_ids": ["host-001", "host-002", "host-003"],
    "entity_type": "host",
    "engines": ["risk"],
    "agents": ["context_summarizer", "gap_detector"],
    "parallel": true,
    "timeout_per_entity": 30.0
  }'
```

## Configuration Examples

### View All Configuration

```bash
curl -X GET "http://localhost:8000/api/v1/config" \
  -H "Authorization: Bearer $TOKEN"
```

### Update Configuration

```bash
# Update agent timeout
curl -X POST "http://localhost:8000/api/v1/config/update" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "config_key": "agents.timeout",
    "value": 60,
    "description": "Increased timeout for complex analysis"
  }'
```

### Create Scoring Rule

```bash
# Create risk rule
curl -X POST "http://localhost:8000/api/v1/config/rules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_id": "critical-vuln-rule",
    "rule_type": "risk",
    "name": "Critical Vulnerability Risk Multiplier",
    "description": "Increase risk score for critical vulnerabilities",
    "condition": {
      "entity_type": "host",
      "min_critical_vulns": 1
    },
    "action": {
      "risk_multiplier": 2.0,
      "recommendation": "Address critical vulnerabilities immediately"
    },
    "priority": 90,
    "enabled": true
  }'
```

### Update Rule

```bash
curl -X PUT "http://localhost:8000/api/v1/config/rules/critical-vuln-rule" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "priority": 95,
    "enabled": false
  }'
```

### Export Configuration

```bash
curl -X POST "http://localhost:8000/api/v1/config/export" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "include_rules": true
  }'
```

### Import Configuration

```bash
curl -X POST "http://localhost:8000/api/v1/config/import" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "agents.timeout": 45,
      "scoring.cache_ttl": 600
    },
    "rules": {
      "imported-rule": {
        "type": "risk",
        "name": "Imported Rule",
        "condition": {"entity_type": "host"},
        "action": {"risk_multiplier": 1.5}
      }
    },
    "overwrite": false
  }'
```

## Batch Processing Examples

### Process Large Dataset

```bash
# Create a script to process 1000 hosts
#!/bin/bash

TOKEN="your-access-token"
BASE_URL="http://localhost:8000"

# Process in batches of 100
for batch in {0..9}; do
  start=$((batch * 100))
  end=$(((batch + 1) * 100))
  
  # Generate batch data
  batch_data=$(python3 - <<EOF
import json
contexts = []
for i in range($start, $end):
    contexts.append({
        "entity": {
            "id": f"host-{i:04d}",
            "entity_type": "host",
            "name": f"server-{i:04d}"
        },
        "signals": []
    })
print(json.dumps({"contexts": contexts, "engines": ["risk"], "parallel": True}))
EOF
)
  
  echo "Processing batch $batch (hosts $start-$end)"
  
  curl -X POST "$BASE_URL/api/v1/score/batch" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$batch_data" \
    -o "batch_${batch}_results.json"
  
  echo "Batch $batch completed"
done
```

### Parallel Agent Analysis

```bash
# Run multiple agents in parallel for different entity types
curl -X POST "http://localhost:8000/api/v1/agents/bulk" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_ids": ["host-001", "host-002", "domain-001", "ip-001"],
    "entity_types": ["host", "host", "domain", "ip"],
    "engines": ["risk"],
    "agents": ["context_summarizer"],
    "parallel": true,
    "timeout_per_entity": 30.0
  }'
```

## Integration Examples

### SIEM Integration

```python
# Python script for SIEM integration
import requests
import json
from datetime import datetime

class CtxOSSiemIntegration:
    def __init__(self, api_url, username, password):
        self.api_url = api_url
        self.token = self._authenticate(username, password)
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def _authenticate(self, username, password):
        response = requests.post(
            f"{self.api_url}/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()["access_token"]
    
    def analyze_alert(self, alert_data):
        """Convert SIEM alert to CtxOS context and analyze"""
        context = {
            "entity": {
                "id": alert_data.get("host_id", "unknown"),
                "entity_type": "host",
                "name": alert_data.get("hostname", "unknown"),
                "properties": {
                    "environment": alert_data.get("environment", "unknown")
                }
            },
            "signals": []
        }
        
        # Convert alert to signals
        for event in alert_data.get("events", []):
            signal = {
                "id": event.get("id"),
                "source": "siem",
                "signal_type": event.get("type", "activity"),
                "severity": event.get("severity", "medium"),
                "description": event.get("description"),
                "timestamp": event.get("timestamp"),
                "properties": event.get("details", {})
            }
            context["signals"].append(signal)
        
        # Score the entity
        score_response = requests.post(
            f"{self.api_url}/api/v1/score",
            headers=self.headers,
            json={"context": context, "engines": ["risk"]}
        )
        score_response.raise_for_status()
        
        # Run analysis
        analysis_response = requests.post(
            f"{self.api_url}/api/v1/agents/pipeline",
            headers=self.headers,
            json={
                "pipeline_name": "security_analysis",
                "context": context,
                "scoring_result": score_response.json()[0]
            }
        )
        analysis_response.raise_for_status()
        
        return {
            "alert_id": alert_data.get("id"),
            "score": score_response.json()[0],
            "analysis": analysis_response.json(),
            "timestamp": datetime.utcnow().isoformat()
        }

# Usage
integration = CtxOSSiemIntegration(
    "http://localhost:8000",
    "analyst",
    "analyst123"
)

# Process SIEM alert
siem_alert = {
    "id": "alert-001",
    "host_id": "web-server-01",
    "hostname": "web-01.example.com",
    "environment": "production",
    "events": [
        {
            "id": "event-001",
            "type": "vulnerability",
            "severity": "critical",
            "description": "CVE-2023-1234 detected",
            "timestamp": "2024-01-15T10:30:00Z",
            "details": {"cve": "CVE-2023-1234", "cvss": 9.8}
        }
    ]
}

result = integration.analyze_alert(siem_alert)
print(json.dumps(result, indent=2))
```

### Docker Integration

```dockerfile
# Dockerfile for CtxOS API client
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY client.py .

CMD ["python", "client.py"]
```

```python
# client.py
import os
import requests
import time
import json

def main():
    api_url = os.getenv("CTXOS_API_URL", "http://localhost:8000")
    username = os.getenv("CTXOS_USERNAME", "admin")
    password = os.getenv("CTXOS_PASSWORD", "admin123")
    
    # Authenticate
    response = requests.post(
        f"{api_url}/api/v1/auth/login",
        json={"username": username, "password": password}
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Monitor health
    while True:
        try:
            health_response = requests.get(
                f"{api_url}/health",
                headers=headers
            )
            
            if health_response.status_code == 200:
                print(f"Service healthy: {health_response.json()}")
            else:
                print(f"Service unhealthy: {health_response.status_code}")
            
            time.sleep(30)
            
        except Exception as e:
            print(f"Error checking health: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
```

### Kubernetes Integration

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ctxos-api-client
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ctxos-api-client
  template:
    metadata:
      labels:
        app: ctxos-api-client
    spec:
      containers:
      - name: client
        image: ctxos/api-client:latest
        env:
        - name: CTXOS_API_URL
          value: "http://ctxos-api-service:8000"
        - name: CTXOS_USERNAME
          valueFrom:
            secretKeyRef:
              name: ctxos-secrets
              key: username
        - name: CTXOS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ctxos-secrets
              key: password
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
```

## Error Handling Examples

### Handle Authentication Errors

```python
import requests
from requests.exceptions import HTTPError

class CtxOSClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.token = None
        self._authenticate(username, password)
    
    def _authenticate(self, username, password):
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": username, "password": password}
            )
            response.raise_for_status()
            self.token = response.json()["access_token"]
        except HTTPError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid credentials")
            else:
                raise
    
    def _make_request(self, method, endpoint, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            response = requests.request(
                method,
                f"{self.base_url}{endpoint}",
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except HTTPError as e:
            if e.response.status_code == 401:
                # Token expired, try to refresh
                self._refresh_token()
                # Retry request
                headers["Authorization"] = f"Bearer {self.token}"
                response = requests.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
            elif e.response.status_code == 403:
                raise PermissionError("Insufficient permissions")
            elif e.response.status_code == 404:
                raise ValueError("Resource not found")
            elif e.response.status_code == 422:
                raise ValueError(f"Validation error: {e.response.json()['detail']}")
            else:
                raise
    
    def score_entity(self, context, engines=["risk"]):
        return self._make_request(
            "POST",
            "/api/v1/score",
            json={"context": context, "engines": engines}
        )
```

### Retry Logic

```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=1, backoff=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        raise
                    
                    print(f"Attempt {retries} failed, retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
        return wrapper
    return decorator

# Usage
@retry_on_failure(max_retries=3, delay=1, backoff=2)
def score_with_retry(client, context):
    return client.score_entity(context)
```

### Rate Limiting

```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests, time_window):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def wait_if_needed(self):
        now = time.time()
        
        # Remove old requests
        while self.requests and self.requests[0] <= now - self.time_window:
            self.requests.popleft()
        
        # Check if we're at the limit
        if len(self.requests) >= self.max_requests:
            sleep_time = self.requests[0] + self.time_window - now
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Add current request
        self.requests.append(now)

# Usage
rate_limiter = RateLimiter(max_requests=100, time_window=60)  # 100 requests per minute

def make_rate_limited_request(client, context):
    rate_limiter.wait_if_needed()
    return client.score_entity(context)
```
