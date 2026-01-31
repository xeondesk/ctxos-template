"""
MCP Integration Endpoints - Expose agents via MCP protocol.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from core.models.context import Context
from core.models.entity import Entity
from core.models.signal import Signal
from core.scoring.risk import ScoringResult

from agents.context_summarizer import ContextSummarizer
from agents.gap_detector import GapDetector
from agents.hypothesis_generator import HypothesisGenerator
from agents.explainability import ExplainabilityAgent
from agents.mcp_orchestrator import get_orchestrator, MCPOrchestrator


class MCPMessageType(Enum):
    """MCP message types."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class MCPMethod(Enum):
    """MCP method names."""
    ANALYZE = "analyze"
    EXECUTE_PIPELINE = "execute_pipeline"
    LIST_AGENTS = "list_agents"
    GET_AGENT_INFO = "get_agent_info"
    CREATE_PIPELINE = "create_pipeline"
    LIST_PIPELINES = "list_pipelines"
    GET_AUDIT_LOGS = "get_audit_logs"


@dataclass
class MCPMessage:
    """MCP protocol message."""
    id: Optional[str]
    method: MCPMethod
    params: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        message = {
            "id": self.id,
            "method": self.method.value,
            "params": self.params,
            "timestamp": self.timestamp.isoformat(),
        }
        
        if self.result is not None:
            message["result"] = self.result
        
        if self.error is not None:
            message["error"] = self.error
        
        return message
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPMessage":
        """Create from dictionary."""
        method = MCPMethod(data["method"])
        return cls(
            id=data.get("id"),
            method=method,
            params=data.get("params", {}),
            result=data.get("result"),
            error=data.get("error"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
        )


class MCPEndpointHandler:
    """Handle MCP endpoint requests."""
    
    def __init__(self):
        """Initialize MCP endpoint handler."""
        self.orchestrator = get_orchestrator()
        self._initialize_agents()
    
    def _initialize_agents(self) -> None:
        """Initialize and register all agents."""
        # Create agent instances
        self.agents = {
            "context_summarizer": ContextSummarizer(
                name="context_summarizer",
                version="1.0.0",
                max_risks=5,
                max_exposures=5,
                max_anomalies=3,
            ),
            "gap_detector": GapDetector(
                name="gap_detector",
                version="1.0.0",
                max_data_age_hours=168,
                min_coverage_threshold=0.7,
            ),
            "hypothesis_generator": HypothesisGenerator(
                name="hypothesis_generator",
                version="1.0.0",
                max_hypotheses=10,
                min_confidence_threshold=0.3,
                enable_creative_hypotheses=True,
            ),
            "explainability_agent": ExplainabilityAgent(
                name="explainability_agent",
                version="1.0.0",
                min_factor_weight=0.05,
                max_explanations=5,
                include_comparisons=True,
            ),
        }
        
        # Register agents with orchestrator
        for agent in self.agents.values():
            self.orchestrator.register_agent(agent)
    
    async def handle_request(self, message: MCPMessage) -> MCPMessage:
        """Handle MCP request."""
        try:
            if message.method == MCPMethod.ANALYZE:
                result = await self._handle_analyze(message.params)
            elif message.method == MCPMethod.EXECUTE_PIPELINE:
                result = await self._handle_execute_pipeline(message.params)
            elif message.method == MCPMethod.LIST_AGENTS:
                result = await self._handle_list_agents(message.params)
            elif message.method == MCPMethod.GET_AGENT_INFO:
                result = await self._handle_get_agent_info(message.params)
            elif message.method == MCPMethod.CREATE_PIPELINE:
                result = await self._handle_create_pipeline(message.params)
            elif message.method == MCPMethod.LIST_PIPELINES:
                result = await self._handle_list_pipelines(message.params)
            elif message.method == MCPMethod.GET_AUDIT_LOGS:
                result = await self._handle_get_audit_logs(message.params)
            else:
                raise ValueError(f"Unknown method: {message.method}")
            
            return MCPMessage(
                id=message.id,
                method=message.method,
                result=result,
            )
            
        except Exception as e:
            return MCPMessage(
                id=message.id,
                method=message.method,
                error={
                    "code": -1,
                    "message": str(e),
                    "type": type(e).__name__,
                }
            )
    
    async def _handle_analyze(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analyze request."""
        agent_name = params.get("agent_name")
        if not agent_name:
            raise ValueError("agent_name is required")
        
        # Parse context
        context_data = params.get("context")
        if not context_data:
            raise ValueError("context is required")
        
        context = self._parse_context(context_data)
        
        # Parse scoring result (optional)
        scoring_result = None
        scoring_data = params.get("scoring_result")
        if scoring_data:
            scoring_result = self._parse_scoring_result(scoring_data)
        
        # Get user
        user = params.get("user", "mcp_client")
        
        # Execute agent
        result = await self.orchestrator.execute_agent(
            agent_name,
            context,
            scoring_result,
            user=user
        )
        
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "duration_ms": result.duration_ms,
            "timestamp": result.timestamp.isoformat(),
        }
    
    async def _handle_execute_pipeline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle execute_pipeline request."""
        pipeline_name = params.get("pipeline_name")
        if not pipeline_name:
            raise ValueError("pipeline_name is required")
        
        # Parse context
        context_data = params.get("context")
        if not context_data:
            raise ValueError("context is required")
        
        context = self._parse_context(context_data)
        
        # Parse scoring result (optional)
        scoring_result = None
        scoring_data = params.get("scoring_result")
        if scoring_data:
            scoring_result = self._parse_scoring_result(scoring_data)
        
        # Get user and timeout
        user = params.get("user", "mcp_client")
        timeout = params.get("timeout", 60.0)
        
        # Execute pipeline
        results = await self.orchestrator.execute_pipeline(
            pipeline_name,
            context,
            scoring_result,
            user=user,
            timeout=timeout
        )
        
        # Convert results to serializable format
        serializable_results = {}
        for agent_name, result in results.items():
            serializable_results[agent_name] = {
                "success": result.success,
                "output": result.output,
                "error": result.error,
                "duration_ms": result.duration_ms,
                "timestamp": result.timestamp.isoformat(),
            }
        
        return {
            "pipeline_name": pipeline_name,
            "results": serializable_results,
            "total_agents": len(results),
            "successful_agents": sum(1 for r in results.values() if r.success),
        }
    
    async def _handle_list_agents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list_agents request."""
        agents = self.orchestrator.list_agents()
        
        agent_info = {}
        for agent_name in agents:
            info = self.orchestrator.get_agent_info(agent_name)
            agent_info[agent_name] = info
        
        return {
            "agents": agents,
            "agent_info": agent_info,
            "total_agents": len(agents),
        }
    
    async def _handle_get_agent_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_agent_info request."""
        agent_name = params.get("agent_name")
        if not agent_name:
            raise ValueError("agent_name is required")
        
        info = self.orchestrator.get_agent_info(agent_name)
        return info
    
    async def _handle_create_pipeline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create_pipeline request."""
        pipeline_name = params.get("pipeline_name")
        if not pipeline_name:
            raise ValueError("pipeline_name is required")
        
        parallel = params.get("parallel", False)
        agent_names = params.get("agents", [])
        
        # Create pipeline
        pipeline = self.orchestrator.create_pipeline(pipeline_name, parallel)
        
        # Add agents to pipeline
        for agent_name in agent_names:
            if agent_name in self.agents:
                pipeline.add_agent(self.agents[agent_name])
            else:
                raise ValueError(f"Unknown agent: {agent_name}")
        
        return {
            "pipeline_name": pipeline_name,
            "parallel": parallel,
            "agents": agent_names,
            "total_agents": len(pipeline.agents),
        }
    
    async def _handle_list_pipelines(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list_pipelines request."""
        pipelines = self.orchestrator.list_pipelines()
        
        pipeline_info = {}
        for pipeline_name in pipelines:
            pipeline = self.orchestrator.pipelines[pipeline_name]
            pipeline_info[pipeline_name] = {
                "parallel": pipeline.parallel,
                "agents": [agent.name for agent in pipeline.agents],
                "total_agents": len(pipeline.agents),
                "duration_ms": pipeline.duration_ms,
                "has_results": len(pipeline.results) > 0,
            }
        
        return {
            "pipelines": pipelines,
            "pipeline_info": pipeline_info,
            "total_pipelines": len(pipelines),
        }
    
    async def _handle_get_audit_logs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_audit_logs request."""
        agent_name = params.get("agent_name")
        limit = params.get("limit", 100)
        
        events = self.orchestrator.audit_logger.get_events(agent_name, limit)
        
        # Convert events to serializable format
        serializable_events = []
        for event in events:
            serializable_events.append(event.to_dict())
        
        # Get stats
        stats = self.orchestrator.audit_logger.get_stats(agent_name)
        
        return {
            "events": serializable_events,
            "stats": stats,
            "total_events": len(serializable_events),
        }
    
    def _parse_context(self, context_data: Dict[str, Any]) -> Context:
        """Parse context from dictionary."""
        # Parse entity
        entity_data = context_data.get("entity")
        entity = None
        if entity_data:
            entity = Entity(
                id=entity_data["id"],
                entity_type=entity_data["entity_type"],
                name=entity_data["name"],
                description=entity_data.get("description"),
                properties=entity_data.get("properties"),
            )
        
        # Parse signals
        signals_data = context_data.get("signals", [])
        signals = []
        for signal_data in signals_data:
            signal = Signal(
                id=signal_data["id"],
                source=signal_data["source"],
                signal_type=signal_data["signal_type"],
                severity=signal_data["severity"],
                description=signal_data.get("description"),
                timestamp=datetime.fromisoformat(signal_data["timestamp"]) if signal_data.get("timestamp") else None,
                entity_id=signal_data.get("entity_id"),
            )
            signals.append(signal)
        
        return Context(entity=entity, signals=signals)
    
    def _parse_scoring_result(self, scoring_data: Dict[str, Any]) -> ScoringResult:
        """Parse scoring result from dictionary."""
        return ScoringResult(
            score=scoring_data["score"],
            severity=scoring_data["severity"],
            details=scoring_data.get("details"),
            metrics=scoring_data.get("metrics"),
            recommendations=scoring_data.get("recommendations"),
        )


class MCPServer:
    """MCP Server for agent integration."""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        """Initialize MCP server."""
        self.host = host
        self.port = port
        self.handler = MCPEndpointHandler()
        self.running = False
    
    async def start(self) -> None:
        """Start MCP server."""
        self.running = True
        print(f"MCP Server starting on {self.host}:{self.port}")
        
        # In a real implementation, this would start an actual HTTP/WebSocket server
        # For now, we'll simulate the server startup
        print("MCP Server started successfully")
        print("Available endpoints:")
        print("  - analyze: Execute single agent")
        print("  - execute_pipeline: Execute agent pipeline")
        print("  - list_agents: List available agents")
        print("  - get_agent_info: Get agent information")
        print("  - create_pipeline: Create execution pipeline")
        print("  - list_pipelines: List available pipelines")
        print("  - get_audit_logs: Get audit logs")
    
    async def stop(self) -> None:
        """Stop MCP server."""
        self.running = False
        print("MCP Server stopped")
    
    async def handle_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP message."""
        try:
            message = MCPMessage.from_dict(message_data)
            response = await self.handler.handle_request(message)
            return response.to_dict()
        except Exception as e:
            error_response = MCPMessage(
                id=message_data.get("id"),
                method=MCPMethod.REQUEST,
                error={
                    "code": -1,
                    "message": str(e),
                    "type": type(e).__name__,
                }
            )
            return error_response.to_dict()


# Utility functions for MCP integration
def create_sample_context() -> Dict[str, Any]:
    """Create sample context for testing."""
    return {
        "entity": {
            "id": "sample-entity-001",
            "entity_type": "host",
            "name": "sample-host",
            "description": "Sample host for testing",
            "properties": {
                "environment": "production",
                "public": True,
            },
        },
        "signals": [
            {
                "id": "signal-001",
                "source": "vulnerability_scanner",
                "signal_type": "VULNERABILITY",
                "severity": "critical",
                "description": "Critical vulnerability detected",
                "timestamp": datetime.utcnow().isoformat(),
                "entity_id": "sample-entity-001",
            },
            {
                "id": "signal-002",
                "source": "network_scanner",
                "signal_type": "PORT",
                "severity": "high",
                "description": "Open port detected",
                "timestamp": datetime.utcnow().isoformat(),
                "entity_id": "sample-entity-001",
            },
        ],
    }


def create_sample_scoring_result() -> Dict[str, Any]:
    """Create sample scoring result for testing."""
    return {
        "score": 75.0,
        "severity": "high",
        "details": {"risk_factors": ["vulnerability", "exposure"]},
        "metrics": {
            "vulnerability": 30,
            "exposure": 25,
            "drift": 20,
        },
        "recommendations": ["Patch vulnerabilities", "Reduce exposure"],
    }


async def example_mcp_usage():
    """Example of MCP usage."""
    server = MCPServer()
    await server.start()
    
    # Example 1: List agents
    list_agents_request = {
        "id": "req-001",
        "method": "list_agents",
        "params": {},
    }
    
    response = await server.handle_message(list_agents_request)
    print("List Agents Response:", json.dumps(response, indent=2))
    
    # Example 2: Analyze with context summarizer
    analyze_request = {
        "id": "req-002",
        "method": "analyze",
        "params": {
            "agent_name": "context_summarizer",
            "context": create_sample_context(),
            "scoring_result": create_sample_scoring_result(),
            "user": "example_user",
        },
    }
    
    response = await server.handle_message(analyze_request)
    print("Analyze Response:", json.dumps(response, indent=2))
    
    # Example 3: Create and execute pipeline
    create_pipeline_request = {
        "id": "req-003",
        "method": "create_pipeline",
        "params": {
            "pipeline_name": "example_pipeline",
            "parallel": False,
            "agents": ["context_summarizer", "gap_detector"],
        },
    }
    
    response = await server.handle_message(create_pipeline_request)
    print("Create Pipeline Response:", json.dumps(response, indent=2))
    
    # Execute pipeline
    execute_pipeline_request = {
        "id": "req-004",
        "method": "execute_pipeline",
        "params": {
            "pipeline_name": "example_pipeline",
            "context": create_sample_context(),
            "scoring_result": create_sample_scoring_result(),
            "user": "example_user",
            "timeout": 30.0,
        },
    }
    
    response = await server.handle_message(execute_pipeline_request)
    print("Execute Pipeline Response:", json.dumps(response, indent=2))
    
    await server.stop()


if __name__ == "__main__":
    # Run example usage
    asyncio.run(example_mcp_usage())
