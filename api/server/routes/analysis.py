"""
Agent analysis API endpoints (/api/v1/agents/*).
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import logging

from core.models.context import Context
from core.models.entity import Entity
from core.models.signal import Signal
from core.scoring.risk import ScoringResult
from agents.mcp_orchestrator import get_orchestrator
from agents.context_summarizer import ContextSummarizer
from agents.gap_detector import GapDetector
from agents.hypothesis_generator import HypothesisGenerator
from agents.explainability import ExplainabilityAgent
from api.server.models.request import (
    AgentRunRequest, PipelineRunRequest, AnalysisFilterRequest,
    BulkAnalysisRequest, ContextInput, SignalInput, EntityInput
)
from api.server.models.response import (
    AgentResultResponse, PipelineResultResponse, StatusResponse,
    PaginatedResponse, AnalysisResultResponse
)
from api.server.middleware.auth import verify_jwt_token, TokenData
from api.server.middleware.rbac import require_permission

logger = logging.getLogger(__name__)

router = APIRouter()


def _convert_context_input(context_input: ContextInput) -> Context:
    """Convert ContextInput to Context model."""
    # Convert entity
    entity = Entity(
        id=context_input.entity.id,
        entity_type=context_input.entity.entity_type,
        name=context_input.entity.name,
        description=context_input.entity.description,
        properties=context_input.entity.properties,
    )
    
    # Convert signals
    signals = []
    if context_input.signals:
        for signal_input in context_input.signals:
            signal = Signal(
                id=signal_input.id,
                source=signal_input.source,
                signal_type=signal_input.signal_type,
                severity=signal_input.severity,
                description=signal_input.description,
                timestamp=signal_input.timestamp,
                entity_id=signal_input.entity_id,
            )
            signals.append(signal)
    
    return Context(entity=entity, signals=signals)


def _convert_scoring_result(scoring_data: Optional[Dict[str, Any]]) -> Optional[ScoringResult]:
    """Convert scoring data to ScoringResult model."""
    if not scoring_data:
        return None
    
    return ScoringResult(
        score=scoring_data.get("score", 0.0),
        severity=scoring_data.get("severity", "info"),
        details=scoring_data.get("details"),
        metrics=scoring_data.get("metrics"),
        recommendations=scoring_data.get("recommendations", []),
    )


@router.post(
    "/agents/run",
    response_model=AgentResultResponse,
    summary="Run single agent",
    tags=["agents"],
)
async def run_agent(
    request: AgentRunRequest,
    token_data: TokenData = Depends(verify_jwt_token),
) -> AgentResultResponse:
    """Run a single agent.
    
    Args:
        request: Agent run request
        token_data: JWT token data
        
    Returns:
        Agent result
    """
    require_permission("run_agents", token_data)
    
    try:
        # Convert context
        context = _convert_context_input(request.context)
        
        # Convert scoring result if provided
        scoring_result = _convert_scoring_result(request.scoring_result)
        
        # Get orchestrator
        orchestrator = get_orchestrator()
        
        # Run agent
        result = await orchestrator.execute_agent(
            agent_name=request.agent_name,
            context=context,
            scoring_result=scoring_result,
            user=token_data.username,
            timeout=request.timeout_seconds,
        )
        
        # Convert to response
        return AgentResultResponse(
            agent_name=result.agent_name,
            success=result.success,
            output=result.output,
            error=result.error,
            duration_ms=result.duration_ms,
            timestamp=result.timestamp,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error running agent {request.agent_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}"
        )


@router.post(
    "/agents/pipeline",
    response_model=PipelineResultResponse,
    summary="Run agent pipeline",
    tags=["agents"],
)
async def run_pipeline(
    request: PipelineRunRequest,
    token_data: TokenData = Depends(verify_jwt_token),
) -> PipelineResultResponse:
    """Run an agent pipeline.
    
    Args:
        request: Pipeline run request
        token_data: JWT token data
        
    Returns:
        Pipeline result
    """
    require_permission("run_pipelines", token_data)
    
    try:
        # Convert context
        context = _convert_context_input(request.context)
        
        # Convert scoring result if provided
        scoring_result = _convert_scoring_result(request.scoring_result)
        
        # Get orchestrator
        orchestrator = get_orchestrator()
        
        # Create or get pipeline
        if request.pipeline_name:
            # Use existing pipeline
            pipeline_name = request.pipeline_name
        else:
            # Create custom pipeline
            pipeline_name = f"custom_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            pipeline = orchestrator.create_pipeline(pipeline_name, parallel=request.parallel)
            
            # Add agents to pipeline
            for agent_name in request.agents:
                try:
                    agent = orchestrator.agents.get(agent_name)
                    if agent:
                        pipeline.add_agent(agent)
                except Exception as e:
                    logger.warning(f"Could not add agent {agent_name} to pipeline: {e}")
        
        # Run pipeline
        results = await orchestrator.execute_pipeline(
            pipeline_name=pipeline_name,
            context=context,
            scoring_result=scoring_result,
            user=token_data.username,
            timeout=request.timeout_seconds,
        )
        
        # Convert results
        agent_results = {}
        for name, result in results.items():
            agent_results[name] = AgentResultResponse(
                agent_name=result.agent_name,
                success=result.success,
                output=result.output,
                error=result.error,
                duration_ms=result.duration_ms,
                timestamp=result.timestamp,
            )
        
        success_count = sum(1 for r in results.values() if r.success)
        
        return PipelineResultResponse(
            pipeline_name=pipeline_name,
            entity_id=context.entity.id,
            results=agent_results,
            duration_ms=sum(r.duration_ms for r in results.values()),
            timestamp=datetime.utcnow(),
            success_count=success_count,
            total_count=len(results),
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error running pipeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {str(e)}"
        )


@router.post(
    "/agents/bulk",
    response_model=Dict[str, Any],
    summary="Run agents on multiple entities",
    tags=["agents"],
)
async def run_bulk_analysis(
    request: BulkAnalysisRequest,
    background_tasks: BackgroundTasks,
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Run agents on multiple entities in bulk.
    
    Args:
        request: Bulk analysis request
        background_tasks: FastAPI background tasks
        token_data: JWT token data
        
    Returns:
        Bulk analysis results
    """
    require_permission("run_agents", token_data)
    
    try:
        if len(request.entity_ids) > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 500 entities allowed per bulk request"
            )
        
        engines = request.engines or ["risk", "exposure", "drift"]
        agents = request.agents or ["context_summarizer", "gap_detector"]
        
        # TODO: Implement bulk analysis
        # For now, return mock results
        results = {}
        for entity_id in request.entity_ids:
            results[entity_id] = {
                "status": "queued",
                "engines": engines,
                "agents": agents,
                "estimated_completion": f"{len(request.entity_ids) * len(agents)}s"
            }
        
        return {
            "request_id": f"bulk_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "entity_count": len(request.entity_ids),
            "engines": engines,
            "agents": agents,
            "parallel": request.parallel,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk analysis failed: {str(e)}"
        )


@router.get(
    "/agents/list",
    response_model=Dict[str, Any],
    summary="List available agents",
    tags=["agents"],
)
async def list_agents(
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """List all available agents with their information.
    
    Args:
        token_data: JWT token data
        
    Returns:
        Dictionary of agent information
    """
    require_permission("read", token_data)
    
    try:
        orchestrator = get_orchestrator()
        agent_names = orchestrator.list_agents()
        
        agents_info = {}
        for agent_name in agent_names:
            try:
                agent_info = orchestrator.get_agent_info(agent_name)
                agents_info[agent_name] = agent_info
            except Exception as e:
                logger.warning(f"Could not get info for agent {agent_name}: {e}")
                agents_info[agent_name] = {
                    "name": agent_name,
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "agents": agents_info,
            "total": len(agent_names),
            "available": len([a for a in agents_info.values() if a.get("status") != "error"]),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}"
        )


@router.get(
    "/agents/status/{agent_name}",
    response_model=Dict[str, Any],
    summary="Get agent status",
    tags=["agents"],
)
async def get_agent_status(
    agent_name: str,
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Get status of a specific agent.
    
    Args:
        agent_name: Agent name
        token_data: JWT token data
        
    Returns:
        Agent status
    """
    require_permission("read", token_data)
    
    try:
        orchestrator = get_orchestrator()
        agent_info = orchestrator.get_agent_info(agent_name)
        
        # Add additional status information
        agent_info["status"] = "available"
        agent_info["last_check"] = datetime.utcnow().isoformat()
        
        return agent_info
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent status: {str(e)}"
        )


@router.get(
    "/agents/pipelines",
    response_model=Dict[str, Any],
    summary="List available pipelines",
    tags=["agents"],
)
async def list_pipelines(
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """List all available pipelines with their information.
    
    Args:
        token_data: JWT token data
        
    Returns:
        Dictionary of pipeline information
    """
    require_permission("read", token_data)
    
    try:
        orchestrator = get_orchestrator()
        pipeline_names = orchestrator.list_pipelines()
        
        pipelines_info = {}
        for pipeline_name in pipeline_names:
            try:
                pipeline = orchestrator.pipelines[pipeline_name]
                pipelines_info[pipeline_name] = {
                    "name": pipeline_name,
                    "parallel": pipeline.parallel,
                    "agents": [agent.name for agent in pipeline.agents],
                    "total_agents": len(pipeline.agents),
                    "duration_ms": pipeline.duration_ms,
                    "has_results": len(pipeline.results) > 0,
                    "created_at": datetime.utcnow().isoformat(),  # TODO: Track creation time
                }
            except Exception as e:
                logger.warning(f"Could not get info for pipeline {pipeline_name}: {e}")
                pipelines_info[pipeline_name] = {
                    "name": pipeline_name,
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "pipelines": pipelines_info,
            "total": len(pipeline_names),
            "available": len([p for p in pipelines_info.values() if p.get("status") != "error"]),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error listing pipelines: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list pipelines: {str(e)}"
        )


@router.post(
    "/agents/create-pipeline",
    response_model=Dict[str, Any],
    summary="Create new pipeline",
    tags=["agents"],
)
async def create_pipeline(
    pipeline_name: str,
    agents: List[str],
    parallel: bool = False,
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Create a new agent pipeline.
    
    Args:
        pipeline_name: Pipeline name
        agents: List of agent names to include
        parallel: Whether to run agents in parallel
        token_data: JWT token data
        
    Returns:
        Pipeline creation result
    """
    require_permission("manage_pipelines", token_data)
    
    try:
        orchestrator = get_orchestrator()
        
        # Check if pipeline already exists
        if pipeline_name in orchestrator.pipelines:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Pipeline {pipeline_name} already exists"
            )
        
        # Create pipeline
        pipeline = orchestrator.create_pipeline(pipeline_name, parallel)
        
        # Add agents to pipeline
        added_agents = []
        for agent_name in agents:
            try:
                agent = orchestrator.agents.get(agent_name)
                if agent:
                    pipeline.add_agent(agent)
                    added_agents.append(agent_name)
                else:
                    logger.warning(f"Agent {agent_name} not found, skipping")
            except Exception as e:
                logger.warning(f"Could not add agent {agent_name} to pipeline: {e}")
        
        return {
            "pipeline_name": pipeline_name,
            "parallel": parallel,
            "requested_agents": agents,
            "added_agents": added_agents,
            "total_agents": len(pipeline.agents),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating pipeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pipeline: {str(e)}"
        )


@router.post(
    "/agents/filter",
    response_model=PaginatedResponse,
    summary="Filter agent results",
    tags=["agents"],
)
async def filter_agent_results(
    request: AnalysisFilterRequest,
    token_data: TokenData = Depends(verify_jwt_token),
) -> PaginatedResponse:
    """Filter agent analysis results.
    
    Args:
        request: Filter request parameters
        token_data: JWT token data
        
    Returns:
        Paginated filtered results
    """
    require_permission("read", token_data)
    
    try:
        # TODO: Implement result filtering
        # For now, return empty result
        return PaginatedResponse(
            items=[],
            total=0,
            limit=request.limit,
            offset=request.offset,
            has_next=False,
        )
        
    except Exception as e:
        logger.error(f"Error filtering agent results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to filter results: {str(e)}"
        )


@router.get(
    "/agents/audit-logs",
    response_model=PaginatedResponse,
    summary="Get agent audit logs",
    tags=["agents"],
)
async def get_audit_logs(
    agent_name: Optional[str] = None,
    limit: int = 100,
    token_data: TokenData = Depends(verify_jwt_token),
) -> PaginatedResponse:
    """Get agent audit logs.
    
    Args:
        agent_name: Optional agent name to filter by
        limit: Maximum number of logs to return
        token_data: JWT token data
        
    Returns:
        Paginated audit logs
    """
    require_permission("read", token_data)
    
    try:
        orchestrator = get_orchestrator()
        
        # Get audit events
        events = orchestrator.audit_logger.get_events(agent_name, limit)
        
        # Convert to response format
        items = []
        for event in events:
            items.append({
                "timestamp": event.timestamp.isoformat(),
                "agent": event.agent_name,
                "action": event.action,
                "entity_id": event.entity_id,
                "status": event.status,
                "level": event.level.value,
                "duration_ms": event.duration_ms,
                "error": event.error,
                "user": event.user,
                "details": event.details
            })
        
        return PaginatedResponse(
            items=items,
            total=len(events),
            limit=limit,
            offset=0,
            has_next=len(events) == limit,
        )
        
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit logs: {str(e)}"
        )


@router.get(
    "/agents/metrics",
    response_model=Dict[str, Any],
    summary="Get agent performance metrics",
    tags=["agents"],
)
async def get_agent_metrics(
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Get agent performance metrics.
    
    Args:
        token_data: JWT token data
        
    Returns:
        Agent performance metrics
    """
    require_permission("read", token_data)
    
    try:
        orchestrator = get_orchestrator()
        
        # Get audit statistics
        stats = orchestrator.audit_logger.get_stats()
        
        # Calculate additional metrics
        agent_metrics = {}
        for agent_name in orchestrator.list_agents():
            agent_stats = orchestrator.audit_logger.get_stats(agent_name)
            agent_metrics[agent_name] = agent_stats
        
        return {
            "overall": stats,
            "agents": agent_metrics,
            "total_agents": len(orchestrator.list_agents()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting agent metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get(
    "/agents/health",
    response_model=Dict[str, Any],
    summary="Get agent service health",
    tags=["agents"],
)
async def get_agent_health(
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Get agent service health status.
    
    Args:
        token_data: JWT token data
        
    Returns:
        Health status information
    """
    require_permission("read", token_data)
    
    try:
        orchestrator = get_orchestrator()
        
        # Check individual agent health
        agent_health = {}
        for agent_name in orchestrator.list_agents():
            try:
                agent_info = orchestrator.get_agent_info(agent_name)
                agent_health[agent_name] = {
                    "status": "healthy",
                    "last_result": agent_info.get("last_result") is not None,
                    "version": agent_info.get("version", "unknown")
                }
            except Exception as e:
                agent_health[agent_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Overall health
        healthy_agents = sum(1 for h in agent_health.values() if h["status"] == "healthy")
        total_agents = len(agent_health)
        
        return {
            "service": "agents",
            "status": "healthy" if healthy_agents == total_agents else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "agents": agent_health,
            "total_agents": total_agents,
            "healthy_agents": healthy_agents,
            "unhealthy_agents": total_agents - healthy_agents
        }
        
    except Exception as e:
        logger.error(f"Error getting agent health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health status: {str(e)}"
        )
