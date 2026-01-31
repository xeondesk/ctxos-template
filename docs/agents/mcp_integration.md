# MCP Integration Guide

## Overview

The Model Context Protocol (MCP) integration provides a standardized way for CtxOS agents to communicate with external systems, enabling seamless integration with various security tools, dashboards, and automation platforms.

## MCP Protocol

### Message Format

All MCP messages follow a standardized JSON format:

```json
{
  "id": "unique-request-id",
  "method": "method_name",
  "params": {
    "parameter": "value"
  },
  "result": {
    "response_data": "value"
  },
  "error": {
    "code": -1,
    "message": "Error description",
    "type": "ErrorType"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Available Methods

#### 1. analyze
Execute a single agent analysis.

**Request:**
```json
{
  "id": "req-001",
  "method": "analyze",
  "params": {
    "agent_name": "context_summarizer",
    "context": {
      "entity": {
        "id": "host-001",
        "entity_type": "host",
        "name": "prod-web-01",
        "description": "Production web server",
        "properties": {
          "environment": "production",
          "public": true
        }
      },
      "signals": [
        {
          "id": "signal-001",
          "source": "nessus",
          "signal_type": "VULNERABILITY",
          "severity": "critical",
          "description": "CVE-2023-1234 detected",
          "timestamp": "2024-01-01T10:00:00Z",
          "entity_id": "host-001"
        }
      ]
    },
    "scoring_result": {
      "score": 85.0,
      "severity": "critical",
      "details": {"risk_factors": ["vulnerability"]},
      "metrics": {"vulnerability": 50, "exposure": 35},
      "recommendations": ["Patch immediately"]
    },
    "user": "security_analyst"
  }
}
```

**Response:**
```json
{
  "id": "req-001",
  "method": "analyze",
  "result": {
    "success": true,
    "output": {
      "summary": {
        "total_signals": 1,
        "risk_items": 1,
        "exposure_items": 0,
        "summary": {
          "entity_summary": {
            "id": "host-001",
            "type": "host",
            "criticality": "high"
          },
          "key_findings": [
            {
              "category": "critical_finding",
              "title": "Critical vulnerability detected",
              "description": "CVE-2023-1234 requires immediate attention"
            }
          ],
          "recommendations": ["Patch CVE-2023-1234 immediately"]
        }
      }
    },
    "duration_ms": 1250,
    "timestamp": "2024-01-01T12:00:01Z"
  }
}
```

#### 2. execute_pipeline
Execute multiple agents in a pipeline.

**Request:**
```json
{
  "id": "req-002",
  "method": "execute_pipeline",
  "params": {
    "pipeline_name": "security_analysis",
    "context": {...},
    "scoring_result": {...},
    "user": "security_team",
    "timeout": 60.0
  }
}
```

**Response:**
```json
{
  "id": "req-002",
  "method": "execute_pipeline",
  "result": {
    "pipeline_name": "security_analysis",
    "results": {
      "context_summarizer": {
        "success": true,
        "output": {...},
        "duration_ms": 1200
      },
      "gap_detector": {
        "success": true,
        "output": {...},
        "duration_ms": 800
      },
      "hypothesis_generator": {
        "success": true,
        "output": {...},
        "duration_ms": 1500
      }
    },
    "total_agents": 3,
    "successful_agents": 3
  }
}
```

#### 3. list_agents
List all available agents.

**Request:**
```json
{
  "id": "req-003",
  "method": "list_agents",
  "params": {}
}
```

**Response:**
```json
{
  "id": "req-003",
  "method": "list_agents",
  "result": {
    "agents": [
      "context_summarizer",
      "gap_detector",
      "hypothesis_generator",
      "explainability_agent"
    ],
    "agent_info": {
      "context_summarizer": {
        "name": "context_summarizer",
        "version": "1.0.0",
        "state": {...}
      }
    },
    "total_agents": 4
  }
}
```

#### 4. get_agent_info
Get detailed information about a specific agent.

**Request:**
```json
{
  "id": "req-004",
  "method": "get_agent_info",
  "params": {
    "agent_name": "context_summarizer"
  }
}
```

#### 5. create_pipeline
Create a new execution pipeline.

**Request:**
```json
{
  "id": "req-005",
  "method": "create_pipeline",
  "params": {
    "pipeline_name": "custom_analysis",
    "parallel": false,
    "agents": [
      "context_summarizer",
      "gap_detector"
    ]
  }
}
```

#### 6. list_pipelines
List all available pipelines.

**Request:**
```json
{
  "id": "req-006",
  "method": "list_pipelines",
  "params": {}
}
```

#### 7. get_audit_logs
Retrieve audit logs for monitoring and compliance.

**Request:**
```json
{
  "id": "req-007",
  "method": "get_audit_logs",
  "params": {
    "agent_name": "context_summarizer",
    "limit": 100
  }
}
```

## Server Implementation

### Starting the MCP Server

```python
from agents.mcp_endpoints import MCPServer

# Create server instance
server = MCPServer(host="localhost", port=8080)

# Start server
await server.start()

# Handle requests
request = {
    "id": "req-001",
    "method": "analyze",
    "params": {...}
}

response = await server.handle_message(request)

# Stop server
await server.stop()
```

### HTTP Endpoint Example

```python
from fastapi import FastAPI, HTTPException
from agents.mcp_endpoints import MCPServer

app = FastAPI()
mcp_server = MCPServer()

@app.post("/mcp")
async def mcp_endpoint(request: dict):
    """Handle MCP requests via HTTP."""
    try:
        response = await mcp_server.handle_message(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
```

### WebSocket Support

```python
from fastapi import WebSocket, WebSocketDisconnect
import json

@app.websocket("/ws/mcp")
async def websocket_endpoint(websocket: WebSocket):
    """Handle MCP requests via WebSocket."""
    await websocket.accept()
    
    try:
        while True:
            # Receive request
            data = await websocket.receive_text()
            request = json.loads(data)
            
            # Process request
            response = await mcp_server.handle_message(request)
            
            # Send response
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        pass
```

## Client Integration

### Python Client

```python
import aiohttp
import json

class MCPClient:
    """MCP client for Python applications."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def analyze(self, agent_name: str, context: dict, 
                      scoring_result: dict = None, user: str = None) -> dict:
        """Execute agent analysis."""
        request = {
            "id": f"req-{int(time.time())}",
            "method": "analyze",
            "params": {
                "agent_name": agent_name,
                "context": context,
                "scoring_result": scoring_result,
                "user": user
            }
        }
        
        async with self.session.post(f"{self.base_url}/mcp", json=request) as resp:
            response = await resp.json()
            
            if "error" in response:
                raise Exception(f"MCP Error: {response['error']['message']}")
            
            return response["result"]
    
    async def execute_pipeline(self, pipeline_name: str, context: dict,
                              scoring_result: dict = None, user: str = None,
                              timeout: float = 60.0) -> dict:
        """Execute pipeline."""
        request = {
            "id": f"req-{int(time.time())}",
            "method": "execute_pipeline",
            "params": {
                "pipeline_name": pipeline_name,
                "context": context,
                "scoring_result": scoring_result,
                "user": user,
                "timeout": timeout
            }
        }
        
        async with self.session.post(f"{self.base_url}/mcp", json=request) as resp:
            response = await resp.json()
            
            if "error" in response:
                raise Exception(f"MCP Error: {response['error']['message']}")
            
            return response["result"]

# Usage example
async def main():
    async with MCPClient("http://localhost:8080") as client:
        # Execute context summarizer
        result = await client.analyze(
            agent_name="context_summarizer",
            context=create_sample_context(),
            scoring_result=create_sample_scoring_result(),
            user="security_analyst"
        )
        
        print("Analysis result:", result)
```

### JavaScript Client

```javascript
class MCPClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
    
    async analyze(agentName, context, scoringResult = null, user = null) {
        const request = {
            id: `req-${Date.now()}`,
            method: "analyze",
            params: {
                agent_name: agentName,
                context: context,
                scoring_result: scoringResult,
                user: user
            }
        };
        
        const response = await fetch(`${this.baseUrl}/mcp`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(request)
        });
        
        const result = await response.json();
        
        if (result.error) {
            throw new Error(`MCP Error: ${result.error.message}`);
        }
        
        return result.result;
    }
    
    async executePipeline(pipelineName, context, scoringResult = null, user = null, timeout = 60.0) {
        const request = {
            id: `req-${Date.now()}`,
            method: "execute_pipeline",
            params: {
                pipeline_name: pipelineName,
                context: context,
                scoring_result: scoringResult,
                user: user,
                timeout: timeout
            }
        };
        
        const response = await fetch(`${this.baseUrl}/mcp`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(request)
        });
        
        const result = await response.json();
        
        if (result.error) {
            throw new Error(`MCP Error: ${result.error.message}`);
        }
        
        return result.result;
    }
}

// Usage example
const client = new MCPClient("http://localhost:8080");

async function analyzeEntity() {
    try {
        const result = await client.analyze(
            "context_summarizer",
            createSampleContext(),
            createSampleScoringResult(),
            "security_analyst"
        );
        
        console.log("Analysis result:", result);
    } catch (error) {
        console.error("Analysis failed:", error);
    }
}
```

## Integration Examples

### SIEM Integration

```python
class SIEMIntegration:
    """Integrate CtxOS agents with SIEM systems."""
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
    
    async def analyze_security_event(self, event_data: dict) -> dict:
        """Analyze security event using CtxOS agents."""
        # Convert SIEM event to CtxOS context
        context = self._siem_to_ctxos_context(event_data)
        
        # Execute analysis pipeline
        result = await self.mcp_client.execute_pipeline(
            "security_analysis",
            context,
            user="siem_system"
        )
        
        # Convert results back to SIEM format
        return self._ctxos_to_siem_result(result)
    
    def _siem_to_ctxos_context(self, event_data: dict) -> dict:
        """Convert SIEM event to CtxOS context."""
        return {
            "entity": {
                "id": event_data.get("entity_id"),
                "entity_type": event_data.get("entity_type", "host"),
                "name": event_data.get("entity_name"),
                "properties": event_data.get("properties", {})
            },
            "signals": event_data.get("signals", [])
        }
    
    def _ctxos_to_siem_result(self, ctxos_result: dict) -> dict:
        """Convert CtxOS result to SIEM format."""
        return {
            "risk_score": self._extract_risk_score(ctxos_result),
            "recommendations": self._extract_recommendations(ctxos_result),
            "analysis_summary": self._extract_summary(ctxos_result),
            "hypotheses": self._extract_hypotheses(ctxos_result)
        }
```

### Dashboard Integration

```javascript
class DashboardIntegration {
    """Integrate CtxOS agents with security dashboards."""
    
    constructor(mcpClient) {
        this.mcpClient = mcpClient;
    }
    
    async async getSecurityOverview(entityId) {
        """Get security overview for dashboard display."""
        const context = await this.fetchEntityContext(entityId);
        const scoringResult = await this.fetchScoringResult(entityId);
        
        // Execute comprehensive analysis
        const results = await this.mcpClient.executePipeline(
            "security_analysis",
            context,
            scoringResult,
            "dashboard_user"
        );
        
        return this.formatForDashboard(results);
    }
    
    formatForDashboard(results) {
        return {
            summary: results.context_summarizer.output.summary,
            gaps: results.gap_detector.output.gap_analysis,
            hypotheses: results.hypothesis_generator.output.hypothesis_analysis,
            explanations: results.explainability_agent.output.explainability_result,
            timestamp: new Date().toISOString()
        };
    }
    
    async fetchEntityContext(entityId) {
        // Fetch entity context from data source
        return {
            entity: { id: entityId, entity_type: "host", name: `host-${entityId}` },
            signals: [] // Fetch signals from database
        };
    }
    
    async fetchScoringResult(entityId) {
        // Fetch scoring result from engines
        return {
            score: 75.0,
            severity: "high",
            metrics: { vulnerability: 30, exposure: 25 }
        };
    }
}
```

### Automation Integration

```python
class AutomationIntegration:
    """Integrate CtxOS agents with security automation."""
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
    
    async def trigger_automated_response(self, entity_id: str, trigger_event: dict) -> dict:
        """Trigger automated response based on agent analysis."""
        # Get entity context
        context = await self._get_entity_context(entity_id)
        
        # Analyze with hypothesis generator
        hypotheses = await self.mcp_client.analyze(
            "hypothesis_generator",
            context,
            user="automation_system"
        )
        
        # Determine appropriate response
        response_actions = self._determine_response_actions(hypotheses)
        
        # Execute automated response
        execution_results = []
        for action in response_actions:
            result = await self._execute_action(action, entity_id)
            execution_results.append(result)
        
        return {
            "hypotheses": hypotheses,
            "actions_taken": response_actions,
            "execution_results": execution_results
        }
    
    def _determine_response_actions(self, hypotheses: dict) -> list:
        """Determine appropriate automated response actions."""
        actions = []
        hypothesis_analysis = hypotheses["output"]["hypothesis_analysis"]
        
        for hypothesis in hypothesis_analysis["hypotheses"]:
            if hypothesis["impact"] == "critical" and hypothesis["confidence"] in {"high", "very_high"}:
                if hypothesis["hypothesis_type"] == "vulnerability_exploitation":
                    actions.append({
                        "type": "isolate_system",
                        "priority": "critical",
                        "reason": f"Critical vulnerability exploitation: {hypothesis['title']}"
                    })
                elif hypothesis["hypothesis_type"] == "lateral_movement":
                    actions.append({
                        "type": "block_network",
                        "priority": "high",
                        "reason": f"Lateral movement detected: {hypothesis['title']}"
                    })
        
        return actions
    
    async def _execute_action(self, action: dict, entity_id: str) -> dict:
        """Execute automated response action."""
        # Implementation would integrate with actual security tools
        if action["type"] == "isolate_system":
            return await self._isolate_system(entity_id, action["reason"])
        elif action["type"] == "block_network":
            return await self._block_network_access(entity_id, action["reason"])
        
        return {"status": "unknown_action", "action": action}
```

## Error Handling

### Error Types

MCP defines standard error types:

```json
{
  "error": {
    "code": -1,
    "message": "Detailed error message",
    "type": "ValidationError",
    "details": {
      "field": "agent_name",
      "issue": "Invalid agent name"
    }
  }
}
```

Common error codes:
- `-1`: General error
- `-2`: Validation error
- `-3`: Authentication error
- `-4`: Authorization error
- `-5`: Timeout error
- `-6`: Resource not found
- `-7`: Internal server error

### Error Handling Best Practices

1. **Client Side**: Always check for error responses
2. **Retry Logic**: Implement exponential backoff for transient errors
3. **Logging**: Log all errors with context
4. **User Feedback**: Provide meaningful error messages to users
5. **Graceful Degradation**: Fall back to alternative methods when possible

```python
async def robust_analyze(client: MCPClient, agent_name: str, context: dict, 
                        max_retries: int = 3) -> dict:
    """Robust analysis with retry logic."""
    for attempt in range(max_retries):
        try:
            return await client.analyze(agent_name, context)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            # Exponential backoff
            delay = 2 ** attempt
            await asyncio.sleep(delay)
            
            logger.warning(f"Analysis attempt {attempt + 1} failed: {e}")
    
    raise Exception("All retry attempts failed")
```

## Performance Considerations

### Optimization Strategies

1. **Connection Pooling**: Reuse HTTP connections
2. **Batch Processing**: Process multiple entities together
3. **Caching**: Cache frequently used results
4. **Parallel Execution**: Use parallel pipelines when possible
5. **Timeout Management**: Set appropriate timeouts

### Monitoring

Monitor MCP integration metrics:

```python
class MCPMetrics:
    """Monitor MCP integration performance."""
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
    
    def record_request(self, response_time: float, success: bool):
        """Record request metrics."""
        self.request_count += 1
        self.response_times.append(response_time)
        
        if not success:
            self.error_count += 1
    
    def get_stats(self) -> dict:
        """Get performance statistics."""
        if not self.response_times:
            return {}
        
        return {
            "total_requests": self.request_count,
            "error_rate": self.error_count / self.request_count,
            "avg_response_time": sum(self.response_times) / len(self.response_times),
            "max_response_time": max(self.response_times),
            "min_response_time": min(self.response_times)
        }
```

## Security Considerations

### Authentication

Implement proper authentication for MCP endpoints:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    """Verify authentication token."""
    if not validate_token(token.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return token

@app.post("/mcp")
async def secure_mcp_endpoint(
    request: dict, 
    token: str = Depends(verify_token)
):
    """Secure MCP endpoint with authentication."""
    return await mcp_server.handle_message(request)
```

### Rate Limiting

Implement rate limiting to prevent abuse:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/mcp")
@limiter.limit("100/minute")
async def rate_limited_mcp_endpoint(request: dict):
    """Rate-limited MCP endpoint."""
    return await mcp_server.handle_message(request)
```

### Input Validation

Validate all input data:

```python
from pydantic import BaseModel, validator

class MCPRequest(BaseModel):
    """MCP request validation model."""
    id: str
    method: str
    params: dict = {}
    
    @validator('method')
    def validate_method(cls, v):
        allowed_methods = ['analyze', 'execute_pipeline', 'list_agents']
        if v not in allowed_methods:
            raise ValueError(f"Method {v} not allowed")
        return v

@app.post("/mcp")
async def validated_mcp_endpoint(request: MCPRequest):
    """Validated MCP endpoint."""
    return await mcp_server.handle_message(request.dict())
```

This MCP integration guide provides comprehensive information for integrating CtxOS agents with external systems, enabling seamless automation and analysis workflows across your security infrastructure.
