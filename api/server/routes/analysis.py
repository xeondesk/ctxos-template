"""
Agent analysis API endpoints (/agents/*).
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, List
from datetime import datetime

from core.models.context import Context
from core.models.entity import Entity
from agents.mcp_orchestrator import get_orchestrator
from api.server.models.request import AgentRunRequest, PipelineRunRequest
from api.server.models.response import AgentResultResponse, PipelineResultResponse, StatusResponse
from api.server.middleware.auth import verify_jwt_token, TokenData
from api.server.middleware.rbac import require_permission


router = APIRouter()


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
        # Create entity
        entity = Entity(
            id=request.entity_id,
            entity_type=request.entity_type.value,
        )
        
        # Create context
        context = Context(entity=entity)
        
        # Get orchestrator
        orchestrator = get_orchestrator()
        
        # Run agent
        result = await orchestrator.execute_agent(
            agent_name=request.agent_name,
            context=context,
            user=token_data.username,
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
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/agents/list",
    response_model=List[str],
    summary="List available agents",
    tags=["agents"],
)
async def list_agents(
    token_data: TokenData = Depends(verify_jwt_token),
) -> List[str]:
    """List all available agents.
    
    Args:
        token_data: JWT token data
        
    Returns:
        List of agent names
    """
    require_permission("read", token_data)
    
    orchestrator = get_orchestrator()
    return orchestrator.list_agents()


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
        return orchestrator.get_agent_info(agent_name)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
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
        # Create entity
        entity = Entity(
            id=request.entity_id,
            entity_type=request.entity_type.value,
        )
        
        # Create context
        context = Context(entity=entity)
        
        # Get orchestrator
        orchestrator = get_orchestrator()
        
        # Run pipeline
        results = await orchestrator.execute_pipeline(
            pipeline_name=request.pipeline_name,
            context=context,
            user=token_data.username,
            timeout=request.timeout_seconds or 60.0,
        )
        
        # Convert results
        agent_results = {
            name: AgentResultResponse(
                agent_name=result.agent_name,
                success=result.success,
                output=result.output,
                error=result.error,
                duration_ms=result.duration_ms,
                timestamp=result.timestamp,
            )
            for name, result in results.items()
        }
        
        success_count = sum(1 for r in results.values() if r.success)
        
        return PipelineResultResponse(
            pipeline_name=request.pipeline_name,
            entity_id=request.entity_id,
            results=agent_results,
            duration_ms=sum(r.duration_ms for r in results.values()),
            timestamp=datetime.utcnow(),
            success_count=success_count,
            total_count=len(results),
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/agents/pipelines",
    response_model=List[str],
    summary="List available pipelines",
    tags=["agents"],
)
async def list_pipelines(
    token_data: TokenData = Depends(verify_jwt_token),
) -> List[str]:
    """List all available pipelines.
    
    Args:
        token_data: JWT token data
        
    Returns:
        List of pipeline names
    """
    require_permission("read", token_data)
    
    orchestrator = get_orchestrator()
    return orchestrator.list_pipelines()
