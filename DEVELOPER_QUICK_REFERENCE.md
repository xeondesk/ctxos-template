# Developer Quick Reference - Sections 5 & 7

## File Locations

| Component | Location | Status |
|-----------|----------|--------|
| Audit System | `agents/audit_system/` | ✅ Ready |
| Base Agent | `agents/base_agent_async.py` | ✅ Ready |
| MCP Orchestrator | `agents/mcp_orchestrator.py` | ✅ Ready |
| FastAPI App | `api/server/app.py` | ✅ Ready |
| Authentication | `api/server/middleware/auth.py` | ✅ Ready |
| RBAC | `api/server/middleware/rbac.py` | ✅ Ready |
| Scoring Routes | `api/server/routes/scoring.py` | ✅ Ready |
| Agent Routes | `api/server/routes/analysis.py` | ✅ Ready |
| Config Routes | `api/server/routes/config.py` | ✅ Ready |

## Key Classes & Functions

### Audit System
```python
from agents.audit_system.audit_logger import (
    AuditLogger,        # Main logging class
    AuditEvent,         # Event dataclass
    AuditLevel,         # Severity enum
    get_audit_logger()  # Get global instance
)

# Usage
logger = get_audit_logger()
logger.log_event(
    agent_name="my_agent",
    action="analyze",
    status="started",
    level=AuditLevel.INFO
)
```

### Base Agent (Async)
```python
from agents.base_agent_async import (
    BaseAgentAsync,     # Abstract base class
    AgentResult,        # Result dataclass
)

# Implementation
class MyAgent(BaseAgentAsync):
    async def analyze(self, context, scoring_result=None):
        # Your agent logic here
        return AgentResult(
            agent_name=self.name,
            success=True,
            output={"key": "value"}
        )

# Usage
agent = MyAgent("my_agent")
result = await agent.run(context, user="analyst-001")
```

### MCP Orchestrator
```python
from agents.mcp_orchestrator import (
    get_orchestrator,   # Get global instance
    MCPPipeline,        # Pipeline class
)

# Register agents
orchestrator = get_orchestrator()
orchestrator.register_agent(agent1)
orchestrator.register_agent(agent2)

# Create pipeline
pipeline = orchestrator.create_pipeline("my_pipeline", parallel=False)
pipeline.add_agent(agent1)
pipeline.add_agent(agent2)

# Execute
results = await orchestrator.execute_pipeline(
    "my_pipeline",
    context,
    user="analyst-001"
)
```

### Authentication
```python
from api.server.middleware.auth import (
    create_access_token,     # Create JWT
    verify_jwt_token,        # Verify token
    TokenData,              # Token payload
    AuthService,            # Auth utilities
)

# Create token
token = create_access_token(
    user_id="user-001",
    username="analyst",
    role="analyst",
    permissions=["read", "write"]
)

# Use in endpoint
@router.get("/endpoint")
async def my_endpoint(token: TokenData = Depends(verify_jwt_token)):
    # token_data available here
    pass
```

### RBAC
```python
from api.server.middleware.rbac import (
    require_permission,  # Check permission
    require_role,        # Check role
    require_role_in,     # Check multiple roles
    Role,                # Role enum
)

# In endpoint
@router.post("/admin-only")
async def admin_endpoint(
    token: TokenData = Depends(require_role(Role.ADMIN))
):
    pass

@router.post("/write-access")
async def write_endpoint(
    token: TokenData = Depends(require_permission("write"))
):
    pass
```

## API Endpoint Patterns

### Scoring Endpoints
```bash
# Score Risk
curl -X POST http://localhost:8000/api/v1/score/risk \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "host-001",
    "entity_type": "host"
  }'

# Score All Engines
curl -X POST http://localhost:8000/api/v1/score/all \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "host-001",
    "entity_type": "host"
  }'
```

### Agent Endpoints
```bash
# Run Agent
curl -X POST http://localhost:8000/api/v1/agents/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "context_summarizer",
    "entity_id": "host-001",
    "entity_type": "host"
  }'

# List Agents
curl http://localhost:8000/api/v1/agents/list \
  -H "Authorization: Bearer $TOKEN"

# Run Pipeline
curl -X POST http://localhost:8000/api/v1/agents/pipeline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_name": "full_analysis",
    "entity_id": "host-001",
    "entity_type": "host",
    "parallel": true
  }'
```

### Config Endpoints
```bash
# Get Config
curl http://localhost:8000/api/v1/config \
  -H "Authorization: Bearer $TOKEN"

# Update Config
curl -X POST http://localhost:8000/api/v1/config/update \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "config_key": "agents.timeout",
    "value": 45
  }'

# Create Rule
curl -X POST http://localhost:8000/api/v1/config/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_id": "rule-001",
    "rule_type": "risk",
    "condition": {"min_open_ports": 5},
    "action": {"risk_level": "HIGH"},
    "priority": 80
  }'

# Get Audit Logs
curl http://localhost:8000/api/v1/audit/logs \
  -H "Authorization: Bearer $TOKEN"
```

## Testing Templates

### Agent Test
```python
import pytest
from agents.base_agent_async import BaseAgentAsync
from core.models.context import Context

@pytest.mark.asyncio
async def test_my_agent():
    agent = MyAgent("test_agent")
    context = Context(entity=Entity(id="test-001", entity_type="host"))
    
    result = await agent.run(context)
    
    assert result.success
    assert result.agent_name == "test_agent"
    assert "key" in result.output
```

### API Test
```python
from fastapi.testclient import TestClient
from api.server.app import app
from api.server.middleware.auth import create_access_token

client = TestClient(app)

def test_scoring_endpoint():
    token = create_access_token("user-001", "analyst", "analyst")
    
    response = client.post(
        "/api/v1/score/risk",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "entity_id": "host-001",
            "entity_type": "host"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["score"] >= 0 and data["score"] <= 1
```

## Role Permissions Matrix

| Role | read | write | delete | run_agents | manage_config | view_audit_logs | manage_rules |
|------|------|-------|--------|-----------|---------------|-----------------|--------------|
| **admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **analyst** | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ |
| **viewer** | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **api_client** | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |

## Environment Variables

```bash
# JWT Configuration
JWT_SECRET=your-secret-key-here
JWT_EXPIRATION_HOURS=24

# API Configuration
API_PORT=8000
API_HOST=0.0.0.0

# API Key
API_KEY=dev-api-key

# Logging
LOG_LEVEL=INFO
```

## Common Tasks

### Create a New Agent
1. Create file: `agents/agents/my_agent.py`
2. Import `BaseAgentAsync`
3. Implement `analyze()` method
4. Register with orchestrator
5. Write tests in `agents/tests/`

### Add API Endpoint
1. Create route in `api/server/routes/`
2. Define request model in `models/request.py`
3. Define response model in `models/response.py`
4. Add dependency: `token: TokenData = Depends(verify_jwt_token)`
5. Add permission check: `require_permission("read", token)`
6. Write tests

### Test Locally
```bash
# Terminal 1: Start API
python -m uvicorn api.server.app:app --reload

# Terminal 2: Run tests
pytest agents/tests/ -v
pytest api/server/tests/ -v

# Terminal 3: Manual testing
curl http://localhost:8000/health
```

## Debugging

### Check Audit Logs
```python
from agents.audit_system.audit_logger import get_audit_logger

logger = get_audit_logger()
events = logger.get_events(limit=10)
for event in events:
    print(f"{event.timestamp} | {event.agent_name} | {event.status}")
```

### Get Agent Status
```python
from agents.mcp_orchestrator import get_orchestrator

orchestrator = get_orchestrator()
info = orchestrator.get_agent_info("my_agent")
print(info)
```

### API Documentation
- Swagger: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `Agent not found` | Unregistered agent | Register with `orchestrator.register_agent()` |
| `Permission denied` | Insufficient permissions | Check role and token |
| `Token expired` | JWT token expired | Generate new token |
| `Timeout` | Agent taking too long | Increase timeout parameter |
| `Invalid entity_type` | Wrong enum value | Use EntityType enum values |

## Performance Tuning

```python
# Increase agent timeout
result = await agent.run(context, timeout=60.0)

# Run agents in parallel
pipeline = orchestrator.create_pipeline("fast", parallel=True)

# Limit audit logs stored
logger = get_audit_logger()
logger.max_events = 5000  # Reduce memory usage
```

## Security Checklist

- [ ] Change JWT_SECRET in production
- [ ] Configure CORS origins (not "*")
- [ ] Set strong API keys
- [ ] Enable HTTPS in production
- [ ] Audit logs regularly
- [ ] Rotate API keys periodically
- [ ] Use environment variables for secrets
- [ ] Implement rate limiting

---

**Last Updated**: Section 5 & 7 Scaffolding Complete
**Status**: Ready for Implementation
