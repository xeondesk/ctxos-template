# CtxOS API Documentation

## Overview

The CtxOS API provides a comprehensive REST interface for context-driven security analysis and intelligence. It exposes scoring engines, AI agents, configuration management, and audit capabilities through a secure, authenticated API.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps    │    │   Web UI         │    │   CLI Tools     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                    │                    │
          └────────────────────┼────────────────────┘
                               │
                    ┌─────────────────┐
                    │  API Gateway    │
                    │  (FastAPI)      │
                    └─────────┬───────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
    │   Auth    │    │ Scoring   │    │  Agents   │    │  Config  │
    │ Service  │    │ Service  │    │ Service  │    │ Service  │
    └──────────┘    └──────────┘    └──────────┘    └──────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
                    ┌─────────────────┐
                    │   Core Engines   │
                    │   & Agents       │
                    └─────────────────┘
```

## Key Features

- **Secure Authentication**: JWT-based auth with role-based access control (RBAC)
- **Scoring Engines**: Risk, Exposure, and Drift analysis engines
- **AI Agents**: Context Summarizer, Gap Detector, Hypothesis Generator, Explainability
- **Configuration Management**: Dynamic configuration with validation and audit trails
- **Comprehensive Auditing**: Full audit trail for all operations
- **High Performance**: Async operations, batch processing, and caching
- **OpenAPI Documentation**: Auto-generated interactive API docs

## Quick Start

### 1. Authentication

Get an access token by logging in:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_info": {
    "user_id": "admin",
    "username": "admin",
    "role": "admin",
    "permissions": ["read", "write", "delete", "..."]
  }
}
```

### 2. Score an Entity

Score a host entity with vulnerability signals:

```bash
curl -X POST "http://localhost:8000/api/v1/score" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "entity": {
        "id": "host-001",
        "entity_type": "host",
        "name": "web-server-01",
        "properties": {
          "environment": "production"
        }
      },
      "signals": [
        {
          "id": "vuln-001",
          "source": "nessus",
          "signal_type": "vulnerability",
          "severity": "critical",
          "description": "CVE-2023-1234",
          "properties": {
            "cvss_score": 9.8
          }
        }
      ]
    },
    "engines": ["risk"],
    "include_recommendations": true
  }'
```

### 3. Run Agent Analysis

Run a complete security analysis pipeline:

```bash
curl -X POST "http://localhost:8000/api/v1/agents/pipeline" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_name": "full_analysis",
    "context": {
      "entity": {
        "id": "host-001",
        "entity_type": "host",
        "name": "web-server-01"
      },
      "signals": []
    },
    "timeout_seconds": 120.0
  }'
```

## API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Authenticate user and get tokens |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user info |
| POST | `/auth/logout` | Logout and revoke token |
| GET | `/auth/verify` | Verify token validity |
| GET | `/auth/health` | Auth service health check |

### Scoring (`/api/v1/score`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/score` | Score entity with specified engines |
| POST | `/score/batch` | Score multiple entities in batch |
| POST | `/score/history/{entity_id}` | Get historical scoring data |
| GET | `/score/engines` | List available scoring engines |
| POST | `/score/aggregate` | Get aggregate scores for entities |
| POST | `/score/compare` | Compare scores between entities |
| GET | `/score/status` | Scoring service health check |

### Agents (`/api/v1/agents`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agents/run` | Run single agent |
| POST | `/agents/pipeline` | Run agent pipeline |
| POST | `/agents/bulk` | Run agents on multiple entities |
| GET | `/agents/list` | List available agents |
| GET | `/agents/status/{agent_name}` | Get agent status |
| GET | `/agents/pipelines` | List available pipelines |
| POST | `/agents/create-pipeline` | Create new pipeline |
| GET | `/agents/metrics` | Get agent performance metrics |
| GET | `/agents/health` | Agent service health check |
| GET | `/agents/audit-logs` | Get agent audit logs |
| POST | `/agents/filter` | Filter agent results |

### Configuration (`/api/v1/config`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/config` | Get all configuration |
| GET | `/config/{config_key}` | Get specific configuration value |
| POST | `/config/update` | Update configuration |
| GET | `/config/rules` | Get all scoring rules |
| POST | `/config/rules` | Create scoring rule |
| GET | `/config/rules/{rule_id}` | Get specific rule |
| PUT | `/config/rules/{rule_id}` | Update rule |
| DELETE | `/config/rules/{rule_id}` | Delete rule |
| POST | `/config/export` | Export configuration |
| POST | `/config/import` | Import configuration |
| GET | `/config/audit-logs` | Get config audit logs |
| GET | `/config/health` | Config service health check |

## Data Models

### Entity Types

```typescript
type EntityType = "host" | "domain" | "ip" | "user" | "service" | 
                 "application" | "network" | "database";
```

### Signal Types

```typescript
type SignalType = "vulnerability" | "port" | "service" | "dns" |
                 "ssl_certificate" | "configuration" | "activity" |
                 "authentication" | "dependency" | "subdomain" | "whois";
```

### Severity Levels

```typescript
type SeverityLevel = "critical" | "high" | "medium" | "low" | "info";
```

### Context Structure

```json
{
  "entity": {
    "id": "string",
    "entity_type": "EntityType",
    "name": "string",
    "description": "string",
    "properties": "object"
  },
  "signals": [
    {
      "id": "string",
      "source": "string",
      "signal_type": "SignalType",
      "severity": "SeverityLevel",
      "description": "string",
      "timestamp": "ISO8601",
      "entity_id": "string",
      "properties": "object"
    }
  ]
}
```

## Authentication & Authorization

### Token Types

- **Access Token**: Short-lived (24h) token for API access
- **Refresh Token**: Long-lived (7d) token for getting new access tokens

### User Roles

| Role | Permissions |
|------|-------------|
| **admin** | Full access to all resources |
| **analyst** | Read, write, run agents and pipelines |
| **viewer** | Read-only access |
| **api_client** | Read and run agents (for integrations) |

### Permission Matrix

| Resource | Read | Write | Delete | Manage |
|----------|------|-------|--------|--------|
| **Config** | ✓ | ✓ | | ✓ |
| **Rules** | ✓ | ✓ | ✓ | ✓ |
| **Agents** | ✓ | ✓ | ✓ | |
| **Pipelines** | ✓ | ✓ | | ✓ |
| **Audit Logs** | ✓ | | | |

## Error Handling

The API uses standard HTTP status codes:

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "error": "Error description",
  "status_code": 400,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Rate Limiting

- Default rate limit: 1000 requests per hour per user
- Configurable via `api.rate_limit` configuration
- Rate limit headers included in responses:
  - `X-RateLimit-Limit`: Requests allowed per hour
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Time when limit resets

## Pagination

Paginated endpoints use this format:

```json
{
  "items": [...],
  "total": 1000,
  "limit": 100,
  "offset": 0,
  "has_next": true
}
```

Query parameters:
- `limit`: Number of items per page (default: 100, max: 1000)
- `offset`: Number of items to skip (default: 0)

## Real-time Updates

The API supports real-time updates through:

1. **WebSocket Connections**: For live agent execution status
2. **Server-Sent Events**: For streaming results
3. **Polling**: With `last_updated` timestamp filtering

## SDK Examples

### Python

```python
import requests

class CtxOSClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.token = self._login(username, password)
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def _login(self, username, password):
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        return response.json()["access_token"]
    
    def score_entity(self, context, engines=["risk"]):
        response = requests.post(
            f"{self.base_url}/api/v1/score",
            headers=self.headers,
            json={"context": context, "engines": engines}
        )
        return response.json()
    
    def run_agent(self, agent_name, context):
        response = requests.post(
            f"{self.base_url}/api/v1/agents/run",
            headers=self.headers,
            json={"agent_name": agent_name, "context": context}
        )
        return response.json()

# Usage
client = CtxOSClient("http://localhost:8000", "admin", "admin123")
results = client.score_entity(context_data)
```

### JavaScript

```javascript
class CtxOSClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
        this.token = null;
    }
    
    async login(username, password) {
        const response = await fetch(`${this.baseURL}/api/v1/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await response.json();
        this.token = data.access_token;
        return data;
    }
    
    async scoreEntity(context, engines = ['risk']) {
        const response = await fetch(`${this.baseURL}/api/v1/score`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            },
            body: JSON.stringify({context, engines})
        });
        return response.json();
    }
    
    async runAgent(agentName, context) {
        const response = await fetch(`${this.baseURL}/api/v1/agents/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            },
            body: JSON.stringify({agent_name: agentName, context})
        });
        return response.json();
    }
}

// Usage
const client = new CtxOSClient('http://localhost:8000');
await client.login('admin', 'admin123');
const results = await client.scoreEntity(contextData);
```

## Configuration

### Environment Variables

```bash
# Authentication
JWT_SECRET=your-secret-key-here
JWT_EXPIRATION_HOURS=24
JWT_REFRESH_EXPIRATION_DAYS=7

# API Settings
API_RATE_LIMIT=1000
CORS_ORIGINS=http://localhost:3000,https://yourapp.com

# Logging
LOG_LEVEL=INFO
```

### Default Configuration

```json
{
  "agents.timeout": 30,
  "agents.max_parallel": 5,
  "agents.retry_count": 3,
  "scoring.cache_ttl": 300,
  "scoring.batch_size": 100,
  "api.rate_limit": 1000,
  "api.cors_origins": ["*"],
  "logging.level": "INFO",
  "monitoring.enabled": true,
  "monitoring.metrics_retention_days": 30
}
```

## Monitoring & Observability

### Health Checks

- `/health`: Basic service health
- `/api/v1/score/status`: Scoring service health
- `/api/v1/agents/health`: Agent service health
- `/api/v1/config/health`: Configuration service health
- `/api/v1/auth/health`: Authentication service health

### Metrics

The API exposes metrics at `/api/v1/metrics` (when enabled):

- Request counts by endpoint
- Response times
- Error rates
- Agent execution metrics
- Scoring engine performance

### Audit Logs

All operations are logged with:
- Timestamp
- User ID
- Action performed
- Resource affected
- Success/failure status
- Duration

Access via `/api/v1/agents/audit-logs` or `/api/v1/config/audit-logs`.

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check your token is valid and not expired
   - Verify the Authorization header format: `Bearer <token>`

2. **403 Forbidden**
   - Check your user role has required permissions
   - Verify the resource exists

3. **422 Unprocessable Entity**
   - Check request body format
   - Verify required fields are present
   - Validate data types and constraints

4. **500 Internal Server Error**
   - Check server logs for detailed error information
   - Verify all services are running

### Debug Mode

Enable debug logging by setting:
```bash
export LOG_LEVEL=DEBUG
```

### Getting Help

- Check the interactive API docs at `/api/docs`
- Review the OpenAPI spec at `/api/openapi.json`
- Check health endpoints for service status
- Review audit logs for operation history

## Versioning

The API follows semantic versioning:
- **Major**: Breaking changes
- **Minor**: New features (backward compatible)
- **Patch**: Bug fixes

Current version: **1.0.0**

API version is included in responses and can be checked via the root endpoint.

## Contributing

See the [Development Guide](../development.md) for information on:
- Setting up development environment
- Running tests
- Contributing code
- API design principles
