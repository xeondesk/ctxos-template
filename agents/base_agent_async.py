"""
Enhanced BaseAgent with async/await support for CtxOS.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from time import time

from core.models.context import Context
from core.models.entity import Entity
from core.models.signal import Signal
from core.scoring.risk import ScoringResult
from agents.audit_system.audit_logger import get_audit_logger, AuditLevel


@dataclass
class AgentResult:
    """Result from agent execution."""
    agent_name: str
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent": self.agent_name,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
        }


class BaseAgentAsync(ABC):
    """Base class for async agents."""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        """Initialize agent.
        
        Args:
            name: Agent name
            version: Agent version
        """
        self.name = name
        self.version = version
        self.audit_logger = get_audit_logger()
        self.state: Dict[str, Any] = {}
        self.last_result: Optional[AgentResult] = None
    
    async def initialize(self) -> None:
        """Initialize agent (async)."""
        await self._setup()
    
    async def shutdown(self) -> None:
        """Shutdown agent (async)."""
        await self._teardown()
    
    @abstractmethod
    async def analyze(
        self,
        context: Context,
        scoring_result: Optional[ScoringResult] = None,
    ) -> AgentResult:
        """Analyze context and return result.
        
        Args:
            context: Input context
            scoring_result: Optional scoring result from engines
            
        Returns:
            AgentResult with analysis
        """
        pass
    
    async def _setup(self) -> None:
        """Setup agent resources (override in subclass)."""
        pass
    
    async def _teardown(self) -> None:
        """Cleanup agent resources (override in subclass)."""
        pass
    
    async def run(
        self,
        context: Context,
        scoring_result: Optional[ScoringResult] = None,
        user: Optional[str] = None,
        timeout: float = 30.0,
    ) -> AgentResult:
        """Run agent with timeout and audit logging.
        
        Args:
            context: Input context
            scoring_result: Optional scoring result from engines
            user: User running agent (for audit)
            timeout: Execution timeout in seconds
            
        Returns:
            AgentResult
        """
        start_time = time()
        entity_id = context.entity.id if context.entity else None
        
        # Log start
        self.audit_logger.log_event(
            agent_name=self.name,
            action="analyze",
            status="started",
            entity_id=entity_id,
            level=AuditLevel.INFO,
            user=user,
            details={"version": self.version},
        )
        
        try:
            # Run analysis with timeout
            result = await asyncio.wait_for(
                self.analyze(context, scoring_result),
                timeout=timeout
            )
            
            duration_ms = (time() - start_time) * 1000
            result.duration_ms = duration_ms
            
            # Log success
            self.audit_logger.log_event(
                agent_name=self.name,
                action="analyze",
                status="completed",
                entity_id=entity_id,
                level=AuditLevel.INFO,
                duration_ms=duration_ms,
                user=user,
                details={"output_keys": list(result.output.keys())},
            )
            
            self.last_result = result
            return result
            
        except asyncio.TimeoutError:
            duration_ms = (time() - start_time) * 1000
            error_msg = f"Agent {self.name} timed out after {timeout}s"
            
            self.audit_logger.log_event(
                agent_name=self.name,
                action="analyze",
                status="failed",
                entity_id=entity_id,
                level=AuditLevel.ERROR,
                error=error_msg,
                duration_ms=duration_ms,
                user=user,
            )
            
            result = AgentResult(
                agent_name=self.name,
                success=False,
                error=error_msg,
                duration_ms=duration_ms,
            )
            
            self.last_result = result
            return result
            
        except Exception as e:
            duration_ms = (time() - start_time) * 1000
            error_msg = str(e)
            
            self.audit_logger.log_event(
                agent_name=self.name,
                action="analyze",
                status="failed",
                entity_id=entity_id,
                level=AuditLevel.ERROR,
                error=error_msg,
                duration_ms=duration_ms,
                user=user,
            )
            
            result = AgentResult(
                agent_name=self.name,
                success=False,
                error=error_msg,
                duration_ms=duration_ms,
            )
            
            self.last_result = result
            return result
    
    async def chain_with(self, next_agent: "BaseAgentAsync") -> None:
        """Chain execution to next agent.
        
        Args:
            next_agent: Agent to chain to
        """
        if self.last_result and self.last_result.success:
            # Pass output as context to next agent
            pass
    
    def get_state(self) -> Dict[str, Any]:
        """Get agent state."""
        return {
            "name": self.name,
            "version": self.version,
            "state": self.state,
            "last_result": self.last_result.to_dict() if self.last_result else None,
        }
