# CtxOS Agents & MCP - Intelligent Analysis Layer

## Overview

The CtxOS Agents & MCP module provides intelligent analysis capabilities that consume scoring results from the engines and generate actionable insights, hypotheses, and explanations. This layer transforms raw security data into meaningful intelligence that security teams can act upon.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                 User Interfaces                │
│  ├─ CLI: ctxos analyze commands               │
│  ├─ Web: Dashboard integration               │
│  └─ API: REST/GraphQL endpoints              │
└───────────────────┬─────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────┐
│              MCP Protocol Layer                 │
│  ├─ Agent orchestration                       │
│  ├─ Pipeline execution                        │
│  ├─ Audit logging                            │
│  └─ Error handling                           │
└───────────────────┬─────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────┐
│                Agent Layer                      │
│  ├─ Context Summarizer                         │
│  ├─ Gap Detector                              │
│  ├─ Hypothesis Generator                       │
│  └─ Explainability Agent                      │
└───────────────────┬─────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────┐
│           Scoring Engines (Section 4)          │
│  ├─ Risk Engine                               │
│  ├─ Exposure Engine                           │
│  └─ Drift Engine                              │
└─────────────────────────────────────────────────┘
```

## Core Components

### 1. BaseAgent Infrastructure

The `BaseAgentAsync` class provides the foundation for all agents:

- **Async Support**: Full async/await support for performance
- **Audit Logging**: Complete audit trail of all agent activities
- **Error Handling**: Robust error handling and recovery
- **Timeout Management**: Configurable execution timeouts
- **State Management**: Agent state tracking and persistence

### 2. MCP Orchestrator

The `MCPOrchestrator` coordinates multi-agent execution:

- **Pipeline Management**: Create and manage execution pipelines
- **Parallel/Sequential Execution**: Flexible execution modes
- **Agent Registration**: Dynamic agent registration and discovery
- **Result Aggregation**: Collect and aggregate results from multiple agents
- **Performance Monitoring**: Track execution performance and metrics

### 3. Audit System

Comprehensive audit logging for compliance and debugging:

- **Event Tracking**: Log all agent activities with full context
- **User Attribution**: Track which users executed which analyses
- **Performance Metrics**: Record execution times and success rates
- **Error Logging**: Detailed error information for troubleshooting
- **Compliance Support**: Meet audit and compliance requirements

## Agent Types

### Context Summarizer

**Purpose**: Reduce complex security context to key findings and actionable insights.

**Key Features**:
- Signal categorization and prioritization
- Risk, exposure, and anomaly highlighting
- Confidence scoring for all findings
- Actionable recommendation generation
- Entity criticality assessment

**Use Cases**:
- Daily security briefings
- Executive summaries
- Triage prioritization
- Incident response overviews

**Configuration**:
```python
summarizer = ContextSummarizer(
    name="security_summarizer",
    max_risks=5,           # Maximum risk items to include
    max_exposures=5,       # Maximum exposure items to include
    max_anomalies=3,       # Maximum anomaly items to include
    min_confidence=0.3,    # Minimum confidence threshold
)
```

### Gap Detector

**Purpose**: Identify missing data, coverage gaps, and monitoring blind spots.

**Key Features**:
- Missing signal detection
- Outdated data identification
- Coverage gap analysis
- Monitoring completeness assessment
- Data freshness scoring

**Use Cases**:
- Data quality assessment
- Monitoring coverage validation
- Compliance gap analysis
- Tool deployment planning

**Configuration**:
```python
gap_detector = GapDetector(
    name="gap_detector",
    max_data_age_hours=168,     # Maximum data age before considered stale
    min_coverage_threshold=0.7, # Minimum acceptable coverage
    critical_sources={          # Critical data sources
        "vulnerability_scanner",
        "asset_inventory",
        "network_scanner",
    },
)
```

### Hypothesis Generator

**Purpose**: Generate likely security scenarios and attack hypotheses based on available data.

**Key Features**:
- Attack chain detection
- Threat scenario generation
- Creative hypothesis generation
- Confidence-based filtering
- Attack surface analysis

**Use Cases**:
- Threat hunting
- Risk assessment
- Security planning
- Incident investigation

**Configuration**:
```python
hypothesis_generator = HypothesisGenerator(
    name="hypothesis_generator",
    max_hypotheses=10,              # Maximum hypotheses to generate
    min_confidence_threshold=0.3,  # Minimum confidence for hypotheses
    enable_creative_hypotheses=True, # Enable advanced scenarios
)
```

### Explainability Agent

**Purpose**: Explain why scores are what they are and provide rationale for security decisions.

**Key Features**:
- Score breakdown analysis
- Factor contribution analysis
- Root cause identification
- Temporal trend analysis
- Comparative analysis

**Use Cases**:
- Security decision justification
- Audit trail explanation
- Stakeholder communication
- Regulatory compliance

**Configuration**:
```python
explainability_agent = ExplainabilityAgent(
    name="explainability_agent",
    min_factor_weight=0.05,      # Minimum weight for factors
    max_explanations=5,          # Maximum explanations to generate
    include_comparisons=True,    # Include comparative analysis
    temporal_analysis_days=30,   # Days for temporal analysis
)
```

## MCP Integration

### MCP Protocol

The Model Context Protocol (MCP) enables standardized communication between agents and external systems:

**Available Methods**:
- `analyze`: Execute single agent analysis
- `execute_pipeline`: Execute agent pipeline
- `list_agents`: List available agents
- `get_agent_info`: Get detailed agent information
- `create_pipeline`: Create execution pipeline
- `list_pipelines`: List available pipelines
- `get_audit_logs`: Retrieve audit logs

### Example Usage

```python
from agents.mcp_endpoints import MCPServer

# Start MCP server
server = MCPServer(host="localhost", port=8080)
await server.start()

# Execute agent analysis
request = {
    "id": "req-001",
    "method": "analyze",
    "params": {
        "agent_name": "context_summarizer",
        "context": {
            "entity": {
                "id": "host-001",
                "entity_type": "host",
                "name": "prod-web-01",
                "properties": {"environment": "production"},
            },
            "signals": [
                {
                    "id": "vuln-001",
                    "source": "nessus",
                    "signal_type": "VULNERABILITY",
                    "severity": "critical",
                    "description": "CVE-2023-1234",
                },
            ],
        },
        "scoring_result": {
            "score": 85.0,
            "severity": "critical",
            "metrics": {"vulnerability": 50, "exposure": 35},
        },
        "user": "security_analyst",
    },
}

response = await server.handle_message(request)
```

## Pipeline Execution

### Sequential Pipelines

Execute agents in sequence, passing results from one to the next:

```python
orchestrator = get_orchestrator()

# Create sequential pipeline
pipeline = orchestrator.create_pipeline("security_analysis", parallel=False)
pipeline.add_agent(context_summarizer)
pipeline.add_agent(gap_detector)
pipeline.add_agent(hypothesis_generator)
pipeline.add_agent(explainability_agent)

# Execute pipeline
results = orchestrator.execute_pipeline(
    "security_analysis",
    context,
    scoring_result,
    user="security_team"
)
```

### Parallel Pipelines

Execute multiple agents simultaneously for faster analysis:

```python
# Create parallel pipeline
pipeline = orchestrator.create_pipeline("parallel_analysis", parallel=True)
pipeline.add_agent(context_summarizer)
pipeline.add_agent(gap_detector)
pipeline.add_agent(hypothesis_generator)

# Execute in parallel
results = orchestrator.execute_pipeline(
    "parallel_analysis",
    context,
    scoring_result,
    timeout=30.0
)
```

## CLI Integration

### Basic Commands

```bash
# Run context summarizer
ctxos analyze --agent context_summarizer --entity host-001

# Execute full analysis pipeline
ctxos analyze --pipeline security_analysis --entity host-001

# List available agents
ctxos agents list

# Get agent information
ctxos agents info --agent context_summarizer

# View audit logs
ctxos agents audit --agent context_summarizer --limit 50
```

### Advanced Usage

```bash
# Custom pipeline execution
ctxos analyze --pipeline custom_pipeline \
  --entity host-001 \
  --parallel \
  --timeout 60 \
  --user security_analyst

# Gap analysis
ctxos analyze --agent gap_detector \
  --entity domain-001 \
  --format json \
  --output gap_analysis.json

# Hypothesis generation with creative mode
ctxos analyze --agent hypothesis_generator \
  --entity application-001 \
  --creative \
  --max-hypotheses 15
```

## Performance Considerations

### Optimization Strategies

1. **Parallel Execution**: Use parallel pipelines for independent agents
2. **Caching**: Enable result caching for repeated analyses
3. **Timeout Management**: Set appropriate timeouts for different scenarios
4. **Resource Limits**: Configure memory and CPU limits for agents
5. **Batch Processing**: Process multiple entities together when possible

### Performance Metrics

- **Execution Time**: Track agent and pipeline execution times
- **Memory Usage**: Monitor memory consumption during analysis
- **Success Rate**: Track agent success and failure rates
- **Throughput**: Measure entities processed per minute
- **Latency**: Track end-to-end analysis latency

## Security Considerations

### Access Control

- **User Authentication**: Require user authentication for all operations
- **Role-Based Access**: Implement role-based access control (RBAC)
- **Audit Logging**: Log all access and modifications
- **Data Privacy**: Protect sensitive data in transit and at rest

### Data Protection

- **Input Validation**: Validate all input data and parameters
- **Output Sanitization**: Sanitize all output data
- **Error Handling**: Avoid exposing sensitive information in errors
- **Rate Limiting**: Implement rate limiting to prevent abuse

## Troubleshooting

### Common Issues

1. **Agent Timeouts**: Increase timeout values or optimize agent performance
2. **Memory Issues**: Reduce batch sizes or increase available memory
3. **Missing Data**: Check data sources and collector configurations
4. **Pipeline Failures**: Verify agent dependencies and configurations
5. **Audit Log Issues**: Check logging configuration and permissions

### Debugging Tools

- **Audit Logs**: Review audit logs for execution details
- **Agent State**: Check agent state and last results
- **Pipeline Metrics**: Monitor pipeline execution metrics
- **Error Logs**: Review detailed error information
- **Performance Metrics**: Analyze performance bottlenecks

## Best Practices

### Agent Development

1. **Async Design**: Use async/await for I/O operations
2. **Error Handling**: Implement comprehensive error handling
3. **Logging**: Add detailed logging for debugging
4. **Testing**: Write comprehensive tests for all scenarios
5. **Documentation**: Document all agent behaviors and configurations

### Pipeline Design

1. **Logical Ordering**: Order agents logically based on dependencies
2. **Parallel Opportunities**: Identify opportunities for parallel execution
3. **Timeout Configuration**: Set appropriate timeouts for each agent
4. **Result Validation**: Validate pipeline results before use
5. **Monitoring**: Monitor pipeline performance and success rates

### Production Deployment

1. **Resource Planning**: Plan resource requirements carefully
2. **Monitoring**: Implement comprehensive monitoring
3. **Backup Strategies**: Plan for data backup and recovery
4. **Scaling**: Design for horizontal scaling
5. **Maintenance**: Plan for regular maintenance and updates

## API Reference

### Agent Methods

All agents implement the following interface:

```python
async def analyze(
    self,
    context: Context,
    scoring_result: Optional[ScoringResult] = None,
) -> AgentResult
```

### Orchestrator Methods

```python
# Agent management
register_agent(agent: BaseAgentAsync)
list_agents() -> List[str]
get_agent_info(agent_name: str) -> Dict[str, Any]

# Pipeline management
create_pipeline(name: str, parallel: bool = False) -> MCPPipeline
list_pipelines() -> List[str]
execute_pipeline(...) -> Dict[str, AgentResult]

# Single agent execution
execute_agent(agent_name: str, ...) -> AgentResult
```

### Data Models

Key data models used across the agent system:

- `Context`: Entity and signals for analysis
- `ScoringResult`: Results from scoring engines
- `AgentResult`: Result from agent execution
- `MCPPipeline`: Pipeline configuration and state
- `AuditEvent`: Audit log entry

## Examples

### Basic Agent Usage

```python
from agents.context_summarizer import ContextSummarizer
from core.models.context import Context
from core.scoring.risk import ScoringResult

# Create agent
summarizer = ContextSummarizer(name="demo_summarizer")

# Prepare data
context = Context(entity=entity, signals=signals)
scoring_result = ScoringResult(score=75.0, severity="high")

# Execute analysis
result = await summarizer.analyze(context, scoring_result)

# Process results
if result.success:
    summary = result.output["summary"]
    print(f"Found {summary['risk_items']} risk items")
    print(f"Confidence: {summary['summary']['confidence']}")
```

### Pipeline Orchestration

```python
from agents.mcp_orchestrator import get_orchestrator

# Get orchestrator
orchestrator = get_orchestrator()

# Register agents
orchestrator.register_agent(context_summarizer)
orchestrator.register_agent(gap_detector)
orchestrator.register_agent(hypothesis_generator)

# Create pipeline
pipeline = orchestrator.create_pipeline("full_analysis")
pipeline.add_agent(context_summarizer)
pipeline.add_agent(gap_detector)
pipeline.add_agent(hypothesis_generator)

# Execute pipeline
results = orchestrator.execute_pipeline(
    "full_analysis",
    context,
    scoring_result,
    user="security_analyst"
)

# Process results
for agent_name, result in results.items():
    if result.success:
        print(f"{agent_name}: {result.output}")
```

### MCP Server Usage

```python
from agents.mcp_endpoints import MCPServer

# Start server
server = MCPServer()
await server.start()

# Handle requests
request = {
    "id": "req-001",
    "method": "analyze",
    "params": {
        "agent_name": "context_summarizer",
        "context": context_data,
        "user": "api_client",
    },
}

response = await server.handle_message(request)
print(response["result"])
```

## Next Steps

1. **Explore Agent Capabilities**: Try different agents with your data
2. **Create Custom Pipelines**: Build pipelines for your specific use cases
3. **Integrate with Existing Tools**: Connect agents to your security stack
4. **Monitor Performance**: Track agent performance and optimize as needed
5. **Extend Functionality**: Develop custom agents for specialized analysis

For more detailed information, see the individual agent documentation and API reference.
