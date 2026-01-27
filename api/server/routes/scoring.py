"""
Scoring API endpoints (/score/*).
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from datetime import datetime

from core.models.context import Context
from core.models.entity import Entity
from core.scoring.risk import get_risk_engine, ScoringResult
from api.server.models.request import ScoreRequestBody, EntityType
from api.server.models.response import ScoringResultResponse, StatusResponse
from api.server.middleware.auth import verify_jwt_token, TokenData
from api.server.middleware.rbac import require_permission


router = APIRouter()


@router.post(
    "/score/risk",
    response_model=ScoringResultResponse,
    summary="Score risk for entity",
    tags=["scoring"],
)
async def score_risk(
    request: ScoreRequestBody,
    token_data: TokenData = Depends(verify_jwt_token),
) -> ScoringResultResponse:
    """Score risk for an entity.
    
    Args:
        request: Score request
        token_data: JWT token data
        
    Returns:
        Scoring result
    """
    require_permission("read", token_data)
    
    try:
        # Create entity
        entity = Entity(
            id=request.entity_id,
            entity_type=request.entity_type.value,
        )
        
        # Create context
        context = Context(entity=entity)
        
        # Get risk engine
        risk_engine = get_risk_engine()
        
        # Score risk
        result = risk_engine.score(context)
        
        # Convert to response
        return ScoringResultResponse(
            entity_id=request.entity_id,
            entity_type=request.entity_type.value,
            engine_name="risk",
            score=result.score,
            severity=result.severity,
            factors=result.factors or {},
            signals=[],
            timestamp=datetime.utcnow(),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/score/exposure",
    response_model=ScoringResultResponse,
    summary="Score exposure for entity",
    tags=["scoring"],
)
async def score_exposure(
    request: ScoreRequestBody,
    token_data: TokenData = Depends(verify_jwt_token),
) -> ScoringResultResponse:
    """Score exposure for an entity.
    
    Args:
        request: Score request
        token_data: JWT token data
        
    Returns:
        Scoring result
    """
    require_permission("read", token_data)
    
    try:
        # Create entity
        entity = Entity(
            id=request.entity_id,
            entity_type=request.entity_type.value,
        )
        
        # Create context
        context = Context(entity=entity)
        
        # TODO: Get exposure engine when implemented
        # For now, return mock result
        return ScoringResultResponse(
            entity_id=request.entity_id,
            entity_type=request.entity_type.value,
            engine_name="exposure",
            score=0.5,
            severity="MEDIUM",
            factors={},
            signals=[],
            timestamp=datetime.utcnow(),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/score/drift",
    response_model=ScoringResultResponse,
    summary="Score drift for entity",
    tags=["scoring"],
)
async def score_drift(
    request: ScoreRequestBody,
    token_data: TokenData = Depends(verify_jwt_token),
) -> ScoringResultResponse:
    """Score drift for an entity.
    
    Args:
        request: Score request
        token_data: JWT token data
        
    Returns:
        Scoring result
    """
    require_permission("read", token_data)
    
    try:
        # Create entity
        entity = Entity(
            id=request.entity_id,
            entity_type=request.entity_type.value,
        )
        
        # Create context
        context = Context(entity=entity)
        
        # TODO: Get drift engine when implemented
        # For now, return mock result
        return ScoringResultResponse(
            entity_id=request.entity_id,
            entity_type=request.entity_type.value,
            engine_name="drift",
            score=0.3,
            severity="LOW",
            factors={},
            signals=[],
            timestamp=datetime.utcnow(),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/score/all",
    response_model=List[ScoringResultResponse],
    summary="Score all engines for entity",
    tags=["scoring"],
)
async def score_all(
    request: ScoreRequestBody,
    token_data: TokenData = Depends(verify_jwt_token),
) -> List[ScoringResultResponse]:
    """Score all engines (risk, exposure, drift) for an entity.
    
    Args:
        request: Score request
        token_data: JWT token data
        
    Returns:
        List of scoring results
    """
    require_permission("read", token_data)
    
    try:
        results = []
        
        # Score risk
        risk_result = await score_risk(request, token_data)
        results.append(risk_result)
        
        # Score exposure
        exposure_result = await score_exposure(request, token_data)
        results.append(exposure_result)
        
        # Score drift
        drift_result = await score_drift(request, token_data)
        results.append(drift_result)
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
