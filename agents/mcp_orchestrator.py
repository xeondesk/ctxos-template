"""
MCP Orchestrator - Coordinate multi-agent execution.
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

from core.models.context import Context
from core.scoring.risk import ScoringResult
from agents.base_agent_async import BaseAgentAsync, AgentResult
from agents.audit_system.audit_logger import get_audit_logger, AuditLevel


@dataclass
class MCPPipeline:
    """Pipeline for coordinated agent execution."""

    name: str
    agents: List[BaseAgentAsync] = field(default_factory=list)
    parallel: bool = False  # Execute in parallel if True
    results: Dict[str, AgentResult] = field(default_factory=dict)
    duration_ms: float = 0.0

    def add_agent(self, agent: BaseAgentAsync) -> None:
        """Add agent to pipeline."""
        self.agents.append(agent)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pipeline": self.name,
            "parallel": self.parallel,
            "agents": [a.name for a in self.agents],
            "results": {k: v.to_dict() for k, v in self.results.items()},
            "duration_ms": self.duration_ms,
        }


class MCPOrchestrator:
    """Orchestrate multi-agent execution via MCP."""

    def __init__(self):
        """Initialize orchestrator."""
        self.audit_logger = get_audit_logger()
        self.agents: Dict[str, BaseAgentAsync] = {}
        self.pipelines: Dict[str, MCPPipeline] = {}

    def register_agent(self, agent: BaseAgentAsync) -> None:
        """Register agent."""
        self.agents[agent.name] = agent
        self.audit_logger.log_event(
            agent_name="MCPOrchestrator",
            action="register_agent",
            status="completed",
            level=AuditLevel.INFO,
            details={"agent": agent.name, "version": agent.version},
        )

    def create_pipeline(self, name: str, parallel: bool = False) -> MCPPipeline:
        """Create execution pipeline."""
        pipeline = MCPPipeline(name=name, parallel=parallel)
        self.pipelines[name] = pipeline
        return pipeline

    async def execute_pipeline(
        self,
        pipeline_name: str,
        context: Context,
        scoring_result: Optional[ScoringResult] = None,
        user: Optional[str] = None,
        timeout: float = 60.0,
    ) -> Dict[str, AgentResult]:
        """Execute pipeline.

        Args:
            pipeline_name: Pipeline to execute
            context: Input context
            scoring_result: Optional scoring result
            user: User running pipeline
            timeout: Total pipeline timeout

        Returns:
            Results from all agents in pipeline
        """
        pipeline = self.pipelines.get(pipeline_name)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_name} not found")

        self.audit_logger.log_event(
            agent_name="MCPOrchestrator",
            action="execute_pipeline",
            status="started",
            level=AuditLevel.INFO,
            details={"pipeline": pipeline_name, "agents": len(pipeline.agents)},
            user=user,
        )

        try:
            if pipeline.parallel:
                results = await self._execute_parallel(
                    pipeline, context, scoring_result, user, timeout
                )
            else:
                results = await self._execute_sequential(
                    pipeline, context, scoring_result, user, timeout
                )

            pipeline.results = results

            self.audit_logger.log_event(
                agent_name="MCPOrchestrator",
                action="execute_pipeline",
                status="completed",
                level=AuditLevel.INFO,
                duration_ms=pipeline.duration_ms,
                details={
                    "pipeline": pipeline_name,
                    "success_count": sum(1 for r in results.values() if r.success),
                    "total_count": len(results),
                },
                user=user,
            )

            return results

        except Exception as e:
            self.audit_logger.log_event(
                agent_name="MCPOrchestrator",
                action="execute_pipeline",
                status="failed",
                level=AuditLevel.ERROR,
                error=str(e),
                details={"pipeline": pipeline_name},
                user=user,
            )
            raise

    async def _execute_sequential(
        self,
        pipeline: MCPPipeline,
        context: Context,
        scoring_result: Optional[ScoringResult],
        user: Optional[str],
        timeout: float,
    ) -> Dict[str, AgentResult]:
        """Execute agents sequentially."""
        import time

        start_time = time.time()
        results = {}
        per_agent_timeout = timeout / len(pipeline.agents)

        for agent in pipeline.agents:
            result = await agent.run(
                context=context,
                scoring_result=scoring_result,
                user=user,
                timeout=per_agent_timeout,
            )
            results[agent.name] = result

        pipeline.duration_ms = (time.time() - start_time) * 1000
        return results

    async def _execute_parallel(
        self,
        pipeline: MCPPipeline,
        context: Context,
        scoring_result: Optional[ScoringResult],
        user: Optional[str],
        timeout: float,
    ) -> Dict[str, AgentResult]:
        """Execute agents in parallel."""
        import time

        start_time = time.time()

        tasks = [
            agent.run(
                context=context,
                scoring_result=scoring_result,
                user=user,
                timeout=timeout,
            )
            for agent in pipeline.agents
        ]

        agent_results = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for agent, result in zip(pipeline.agents, agent_results):
            if isinstance(result, Exception):
                results[agent.name] = AgentResult(
                    agent_name=agent.name,
                    success=False,
                    error=str(result),
                )
            else:
                results[agent.name] = result

        pipeline.duration_ms = (time.time() - start_time) * 1000
        return results

    async def execute_agent(
        self,
        agent_name: str,
        context: Context,
        scoring_result: Optional[ScoringResult] = None,
        user: Optional[str] = None,
    ) -> AgentResult:
        """Execute single agent.

        Args:
            agent_name: Agent to execute
            context: Input context
            scoring_result: Optional scoring result
            user: User running agent

        Returns:
            Agent result
        """
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent {agent_name} not found")

        return await agent.run(context, scoring_result, user)

    def get_agent_info(self, agent_name: str) -> Dict[str, Any]:
        """Get agent information."""
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent {agent_name} not found")

        return {
            "name": agent.name,
            "version": agent.version,
            "state": agent.get_state(),
        }

    def list_agents(self) -> List[str]:
        """List all registered agents."""
        return list(self.agents.keys())

    def list_pipelines(self) -> List[str]:
        """List all pipelines."""
        return list(self.pipelines.keys())


# Global orchestrator instance
_orchestrator = MCPOrchestrator()


def get_orchestrator() -> MCPOrchestrator:
    """Get global MCP orchestrator."""
    return _orchestrator
