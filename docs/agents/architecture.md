# CtxOS Agent Architecture

## Overview

The CtxOS Agent Architecture is designed to provide a scalable, maintainable, and extensible framework for intelligent security analysis. The architecture follows modern software engineering principles with clear separation of concerns, async processing, and comprehensive observability.

## Core Principles

### 1. Async-First Design
All agents are built with async/await patterns to ensure:
- Non-blocking I/O operations
- Efficient resource utilization
- Scalable concurrent processing
- Responsive user experience

### 2. Audit Trail Compliance
Every agent action is logged with:
- User attribution
- Timestamp tracking
- Success/failure status
- Performance metrics
- Error details

### 3. Extensible Framework
The architecture supports:
- Easy addition of new agents
- Flexible pipeline configurations
- Pluggable components
- Custom data models

### 4. Production Ready
Built for enterprise deployment with:
- Error handling and recovery
- Performance monitoring
- Resource management
- Security controls

## Architecture Layers

```
┌─────────────────────────────────────────────────┐
│                 Interface Layer                 │
│  ├─ MCP Protocol Endpoints                     │
│  ├─ CLI Commands                              │
│  ├─ REST API Integration                      │
│  └─ WebSocket Support                         │
└───────────────────┬─────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────┐
│              Orchestration Layer                 │
│  ├─ MCP Orchestrator                           │
│  ├─ Pipeline Management                        │
│  ├─ Agent Registry                            │
│  ├─ Result Aggregation                         │
│  └─ Performance Monitoring                     │
└───────────────────┬─────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────┐
│                Agent Layer                      │
│  ├─ BaseAgent (Abstract)                      │
│  ├─ Context Summarizer                        │
│  ├─ Gap Detector                              │
│  ├─ Hypothesis Generator                       │
│  ├─ Explainability Agent                      │
│  └─ Custom Agents (Extensible)                │
└───────────────────┬─────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────┐
│               Foundation Layer                  │
│  ├─ Audit System                              │
│  ├─ Data Models                               │
│  ├─ Error Handling                            │
│  ├─ Configuration Management                   │
│  └─ Logging Framework                         │
└─────────────────────────────────────────────────┘
```

## Component Details

### BaseAgent (Abstract Class)

The foundation for all agents providing:

```python
class BaseAgentAsync(ABC):
    """Base class for async agents."""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.audit_logger = get_audit_logger()
        self.state: Dict[str, Any] = {}
        self.last_result: Optional[AgentResult] = None
    
    async def analyze(
        self,
        context: Context,
        scoring_result: Optional[ScoringResult] = None,
    ) -> AgentResult:
        """Main analysis method - must be implemented by subclasses."""
        pass
    
    async def run(
        self,
        context: Context,
        scoring_result: Optional[ScoringResult] = None,
        user: Optional[str] = None,
        timeout: float = 30.0,
    ) -> AgentResult:
        """Execute with timeout and audit logging."""
        # Implementation includes:
        # - Audit logging start/stop
        # - Timeout handling
        # - Error catching and logging
        # - Result validation
```

### MCP Orchestrator

Central coordination component for multi-agent execution:

```python
class MCPOrchestrator:
    """Orchestrate multi-agent execution via MCP."""
    
    def __init__(self):
        self.audit_logger = get_audit_logger()
        self.agents: Dict[str, BaseAgentAsync] = {}
        self.pipelines: Dict[str, MCPPipeline] = {}
    
    def register_agent(self, agent: BaseAgentAsync) -> None:
        """Register agent for execution."""
    
    def create_pipeline(self, name: str, parallel: bool = False) -> MCPPipeline:
        """Create execution pipeline."""
    
    async def execute_pipeline(
        self,
        pipeline_name: str,
        context: Context,
        scoring_result: Optional[ScoringResult] = None,
        user: Optional[str] = None,
        timeout: float = 60.0,
    ) -> Dict[str, AgentResult]:
        """Execute pipeline with specified configuration."""
```

### Audit System

Comprehensive audit logging for compliance and debugging:

```python
class AuditLogger:
    """Logger for agent audit trail."""
    
    def log_event(
        self,
        agent_name: str,
        action: str,
        status: str,
        entity_id: Optional[str] = None,
        level: AuditLevel = AuditLevel.INFO,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None,
        user: Optional[str] = None,
    ) -> AuditEvent:
        """Log audit event with full context."""
```

## Data Flow Architecture

### 1. Input Processing
```
Context + ScoringResult
    ↓
Validation & Normalization
    ↓
Agent Analysis
    ↓
Result Generation
    ↓
Audit Logging
    ↓
Output Response
```

### 2. Pipeline Execution
```
Pipeline Request
    ↓
Agent Selection
    ↓
Sequential/Parallel Execution
    ↓
Result Collection
    ↓
Aggregation & Formatting
    ↓
Pipeline Response
```

### 3. Error Handling
```
Error Detection
    ↓
Error Classification
    ↓
Audit Logging
    ↓
Error Recovery (if possible)
    ↓
Graceful Degradation
    ↓
Error Response
```

## Agent Lifecycle

### 1. Initialization
```python
# Agent creation
agent = ContextSummarizer(name="summarizer", version="1.0.0")

# Registration with orchestrator
orchestrator.register_agent(agent)

# State initialization
await agent.initialize()
```

### 2. Execution
```python
# Single agent execution
result = await agent.run(
    context=context,
    scoring_result=scoring_result,
    user="security_analyst",
    timeout=30.0
)
```

### 3. Pipeline Execution
```python
# Pipeline creation
pipeline = orchestrator.create_pipeline("analysis", parallel=False)
pipeline.add_agent(agent)

# Pipeline execution
results = await orchestrator.execute_pipeline(
    "analysis",
    context,
    scoring_result,
    user="security_team"
)
```

### 4. Cleanup
```python
# Agent shutdown
await agent.shutdown()

# Pipeline cleanup
orchestrator.pipelines.pop("analysis", None)
```

## Performance Architecture

### 1. Async Processing
- Non-blocking I/O for all operations
- Concurrent agent execution
- Efficient resource utilization
- Scalable throughput

### 2. Memory Management
- Streaming data processing
- Bounded result sets
- Garbage collection optimization
- Memory leak prevention

### 3. Caching Strategy
- Agent result caching
- Pipeline state caching
- Configuration caching
- Metadata caching

### 4. Resource Limits
- Execution timeouts
- Memory limits per agent
- Concurrent execution limits
- Rate limiting

## Security Architecture

### 1. Access Control
```python
# User authentication
user = authenticate_user(token)

# Role-based access control
if not has_permission(user, "execute_agent", agent_name):
    raise PermissionError("Insufficient permissions")

# Audit logging
audit_logger.log_event(
    agent_name=agent_name,
    action="execute",
    status="started",
    user=user.id
)
```

### 2. Data Protection
- Input validation and sanitization
- Output data filtering
- Sensitive data masking
- Encryption in transit

### 3. Isolation
- Agent execution isolation
- Resource separation
- Error boundary enforcement
- Sandboxing capabilities

## Monitoring Architecture

### 1. Metrics Collection
```python
# Performance metrics
metrics = {
    "execution_time_ms": duration_ms,
    "memory_usage_mb": memory_usage,
    "success_rate": success_count / total_count,
    "error_rate": error_count / total_count,
    "throughput_entities_per_min": throughput,
}
```

### 2. Health Checks
```python
async def health_check(agent: BaseAgentAsync) -> HealthStatus:
    """Check agent health and readiness."""
    try:
        # Test agent functionality
        test_result = await agent._health_check()
        
        return HealthStatus(
            status="healthy",
            details=test_result,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return HealthStatus(
            status="unhealthy",
            error=str(e),
            timestamp=datetime.utcnow()
        )
```

### 3. Alerting
- Performance degradation alerts
- Error rate threshold alerts
- Resource exhaustion alerts
- Security incident alerts

## Extension Architecture

### 1. Custom Agent Development
```python
class CustomAgent(BaseAgentAsync):
    """Custom agent implementation."""
    
    async def analyze(
        self,
        context: Context,
        scoring_result: Optional[ScoringResult] = None,
    ) -> AgentResult:
        """Implement custom analysis logic."""
        try:
            # Custom analysis implementation
            result_data = await self._custom_analysis(context, scoring_result)
            
            return AgentResult(
                agent_name=self.name,
                success=True,
                output=result_data
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                success=False,
                error=str(e)
            )
```

### 2. Plugin Architecture
- Dynamic agent loading
- Configuration-driven plugins
- Hot-swapping capabilities
- Version management

### 3. Integration Points
- Custom data sources
- External API integrations
- Third-party tool connections
- Custom output formats

## Deployment Architecture

### 1. Containerization
```dockerfile
FROM python:3.9-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY agents/ /app/agents/
COPY core/ /app/core/

# Set up environment
ENV PYTHONPATH=/app
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s \
  CMD python -m agents.health_check

# Start service
CMD ["python", "-m", "agents.mcp_server"]
```

### 2. Scaling Strategies
- Horizontal scaling with load balancing
- Vertical scaling with resource allocation
- Auto-scaling based on metrics
- Geographic distribution

### 3. High Availability
- Redundant agent instances
- Failover mechanisms
- Data replication
- Disaster recovery

## Testing Architecture

### 1. Unit Testing
```python
class TestCustomAgent(unittest.TestCase):
    """Unit tests for custom agent."""
    
    def setUp(self):
        self.agent = CustomAgent(name="test_agent")
    
    async def test_analysis_success(self):
        """Test successful analysis."""
        context = create_test_context()
        result = await self.agent.analyze(context)
        
        self.assertTrue(result.success)
        self.assertIn("output", result.output)
```

### 2. Integration Testing
```python
class TestAgentIntegration(unittest.TestCase):
    """Integration tests for agent workflows."""
    
    async def test_pipeline_execution(self):
        """Test complete pipeline execution."""
        orchestrator = get_orchestrator()
        
        # Register agents
        orchestrator.register_agent(CustomAgent("agent1"))
        orchestrator.register_agent(CustomAgent("agent2"))
        
        # Create pipeline
        pipeline = orchestrator.create_pipeline("test_pipeline")
        pipeline.add_agent(orchestrator.agents["agent1"])
        pipeline.add_agent(orchestrator.agents["agent2"])
        
        # Execute pipeline
        results = await orchestrator.execute_pipeline(
            "test_pipeline",
            test_context,
            test_scoring_result
        )
        
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.success for r in results.values()))
```

### 3. Performance Testing
- Load testing with concurrent requests
- Stress testing with resource limits
- Endurance testing with sustained load
- Scalability testing with increasing load

## Configuration Architecture

### 1. Agent Configuration
```yaml
agents:
  context_summarizer:
    name: "production_summarizer"
    version: "1.0.0"
    config:
      max_risks: 10
      max_exposures: 10
      max_anomalies: 5
      min_confidence: 0.4
  
  gap_detector:
    name: "production_gap_detector"
    version: "1.0.0"
    config:
      max_data_age_hours: 168
      min_coverage_threshold: 0.8
```

### 2. Pipeline Configuration
```yaml
pipelines:
  security_analysis:
    parallel: false
    agents:
      - context_summarizer
      - gap_detector
      - hypothesis_generator
    timeout: 60.0
    retry_count: 3
  
  parallel_scan:
    parallel: true
    agents:
      - context_summarizer
      - gap_detector
    timeout: 30.0
```

### 3. System Configuration
```yaml
system:
  mcp_server:
    host: "0.0.0.0"
    port: 8080
    workers: 4
  
  audit:
    retention_days: 90
    max_events: 10000
    log_level: "INFO"
  
  performance:
    max_concurrent_agents: 10
    default_timeout: 30.0
    memory_limit_mb: 1024
```

## Best Practices

### 1. Agent Development
- Use async/await for all I/O operations
- Implement comprehensive error handling
- Add detailed logging and metrics
- Write thorough tests
- Document all behaviors and configurations

### 2. Pipeline Design
- Order agents logically based on dependencies
- Use parallel execution when possible
- Set appropriate timeouts
- Validate pipeline results
- Monitor pipeline performance

### 3. Production Deployment
- Implement comprehensive monitoring
- Set up alerting for critical issues
- Plan for scaling and high availability
- Regular security updates and patches
- Backup and disaster recovery planning

### 4. Maintenance
- Regular performance reviews
- Log analysis and optimization
- Security audit and hardening
- Dependency updates and testing
- Documentation maintenance

This architecture provides a solid foundation for building scalable, maintainable, and secure agent-based security analysis systems that can evolve with changing requirements and scale to meet enterprise demands.
