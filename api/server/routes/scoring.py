"""
Scoring API endpoints (/api/v1/score/*).
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import logging

from core.models.context import Context
from core.models.entity import Entity
from core.models.signal import Signal
from core.scoring.risk import get_risk_engine, ScoringResult
from api.server.models.request import (
    ScoreRequestBody,
    BatchScoreRequest,
    HistoricalQueryRequest,
    ContextInput,
    SignalInput,
    EntityInput,
)
from api.server.models.response import (
    ScoringResultResponse,
    StatusResponse,
    PaginatedResponse,
    EntityResponse,
    SignalResponse,
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


def _convert_scoring_result_to_response(
    result: ScoringResult, entity_id: str, entity_type: str, engine_name: str
) -> ScoringResultResponse:
    """Convert ScoringResult to response model."""
    # Convert signals
    signal_responses = []
    if hasattr(result, "signals") and result.signals:
        for signal in result.signals:
            signal_response = SignalResponse(
                name=signal.signal_type,
                value=signal.severity,
                severity=signal.severity,
                timestamp=signal.timestamp,
            )
            signal_responses.append(signal_response)

    return ScoringResultResponse(
        entity_id=entity_id,
        entity_type=entity_type,
        engine_name=engine_name,
        score=result.score,
        severity=result.severity,
        factors=result.factors or {},
        signals=signal_responses,
        timestamp=result.timestamp or datetime.utcnow(),
    )


@router.post(
    "/score",
    response_model=List[ScoringResultResponse],
    summary="Score entity with specified engines",
    tags=["scoring"],
)
async def score_entity(
    request: ScoreRequestBody,
    token_data: TokenData = Depends(verify_jwt_token),
) -> List[ScoringResultResponse]:
    """Score an entity using specified engines.

    Args:
        request: Score request with context and engines
        token_data: JWT token data

    Returns:
        List of scoring results from requested engines
    """
    require_permission("read", token_data)

    try:
        # Convert context
        context = _convert_context_input(request.context)

        # Determine engines to run
        engines = request.engines or ["risk", "exposure", "drift"]
        results = []

        # Run each engine
        for engine_name in engines:
            try:
                if engine_name == "risk":
                    engine = get_risk_engine()
                    result = engine.score(context)
                    response = _convert_scoring_result_to_response(
                        result, context.entity.id, context.entity.entity_type, engine_name
                    )
                    results.append(response)
                elif engine_name == "exposure":
                    # TODO: Implement exposure engine integration
                    logger.warning("Exposure engine not yet implemented")
                    continue
                elif engine_name == "drift":
                    # TODO: Implement drift engine integration
                    logger.warning("Drift engine not yet implemented")
                    continue
                else:
                    logger.warning(f"Unknown engine: {engine_name}")

            except Exception as e:
                logger.error(f"Error running {engine_name} engine: {e}")
                # Continue with other engines
                continue

        if not results:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No scoring engines are currently available",
            )

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scoring entity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Scoring failed: {str(e)}"
        )


@router.post(
    "/score/batch",
    response_model=List[ScoringResultResponse],
    summary="Score multiple entities in batch",
    tags=["scoring"],
)
async def score_batch(
    request: BatchScoreRequest,
    background_tasks: BackgroundTasks,
    token_data: TokenData = Depends(verify_jwt_token),
) -> List[ScoringResultResponse]:
    """Score multiple entities in batch.

    Args:
        request: Batch score request
        background_tasks: FastAPI background tasks
        token_data: JWT token data

    Returns:
        List of scoring results for all entities
    """
    require_permission("read", token_data)

    try:
        if len(request.contexts) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 entities allowed per batch request",
            )

        engines = request.engines or ["risk", "exposure", "drift"]
        all_results = []

        if request.parallel:
            # Process entities in parallel
            tasks = []
            for context_input in request.contexts:
                task = _score_single_entity(context_input, engines)
                tasks.append(task)

            # Wait for all tasks to complete
            results_per_entity = await asyncio.gather(*tasks, return_exceptions=True)

            # Flatten results and handle exceptions
            for i, entity_results in enumerate(results_per_entity):
                if isinstance(entity_results, Exception):
                    logger.error(
                        f"Error scoring entity {request.contexts[i].entity.id}: {entity_results}"
                    )
                    continue
                all_results.extend(entity_results)
        else:
            # Process entities sequentially
            for context_input in request.contexts:
                try:
                    entity_results = await _score_single_entity(context_input, engines)
                    all_results.extend(entity_results)
                except Exception as e:
                    logger.error(f"Error scoring entity {context_input.entity.id}: {e}")
                    continue

        if not all_results:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No scoring results available",
            )

        return all_results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch scoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch scoring failed: {str(e)}",
        )


async def _score_single_entity(
    context_input: ContextInput, engines: List[str]
) -> List[ScoringResultResponse]:
    """Score a single entity with specified engines."""
    context = _convert_context_input(context_input)
    results = []

    for engine_name in engines:
        try:
            if engine_name == "risk":
                engine = get_risk_engine()
                result = engine.score(context)
                response = _convert_scoring_result_to_response(
                    result, context.entity.id, context.entity.entity_type, engine_name
                )
                results.append(response)
            elif engine_name == "exposure":
                # TODO: Implement exposure engine
                continue
            elif engine_name == "drift":
                # TODO: Implement drift engine
                continue
        except Exception as e:
            logger.error(f"Error in {engine_name} engine: {e}")
            continue

    return results


@router.post(
    "/score/history/{entity_id}",
    response_model=PaginatedResponse,
    summary="Get historical scoring data for entity",
    tags=["scoring"],
)
async def get_scoring_history(
    entity_id: str,
    request: HistoricalQueryRequest,
    token_data: TokenData = Depends(verify_jwt_token),
) -> PaginatedResponse:
    """Get historical scoring data for an entity.

    Args:
        entity_id: Entity ID
        request: Historical query parameters
        token_data: JWT token data

    Returns:
        Paginated historical scoring data
    """
    require_permission("read", token_data)

    try:
        # TODO: Implement historical data retrieval
        # For now, return empty result
        return PaginatedResponse(
            items=[],
            total=0,
            limit=request.limit,
            offset=request.offset,
            has_next=False,
        )

    except Exception as e:
        logger.error(f"Error getting scoring history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scoring history: {str(e)}",
        )


@router.get(
    "/score/engines",
    response_model=Dict[str, Any],
    summary="Get available scoring engines",
    tags=["scoring"],
)
async def get_available_engines(
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Get list of available scoring engines and their status.

    Args:
        token_data: JWT token data

    Returns:
        Dictionary of available engines
    """
    require_permission("read", token_data)

    try:
        engines = {
            "risk": {
                "name": "Risk Engine",
                "description": "Assesses vulnerability and security incident risk",
                "status": "available",
                "version": "1.0.0",
            },
            "exposure": {
                "name": "Exposure Engine",
                "description": "Measures attack surface and public exposure",
                "status": "coming_soon",
                "version": "1.0.0",
            },
            "drift": {
                "name": "Drift Engine",
                "description": "Detects configuration changes and deviations",
                "status": "coming_soon",
                "version": "1.0.0",
            },
        }

        return {
            "engines": engines,
            "total": len(engines),
            "available": len([e for e in engines.values() if e["status"] == "available"]),
        }

    except Exception as e:
        logger.error(f"Error getting available engines: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get engines: {str(e)}",
        )


@router.post(
    "/score/aggregate",
    response_model=Dict[str, Any],
    summary="Get aggregate scores for multiple entities",
    tags=["scoring"],
)
async def get_aggregate_scores(
    entity_ids: List[str],
    engines: Optional[List[str]] = None,
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Get aggregate scoring statistics for multiple entities.

    Args:
        entity_ids: List of entity IDs
        engines: Engines to include (default: all)
        token_data: JWT token data

    Returns:
        Aggregate scoring statistics
    """
    require_permission("read", token_data)

    try:
        if len(entity_ids) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 1000 entity IDs allowed"
            )

        engines = engines or ["risk", "exposure", "drift"]

        # TODO: Implement aggregate scoring
        # For now, return mock statistics
        return {
            "entity_count": len(entity_ids),
            "engines": engines,
            "statistics": {
                "risk": {
                    "average_score": 45.2,
                    "max_score": 95.0,
                    "min_score": 12.5,
                    "high_risk_count": 15,
                    "critical_risk_count": 3,
                },
                "exposure": {
                    "average_score": 38.7,
                    "max_score": 87.0,
                    "min_score": 8.2,
                    "high_exposure_count": 12,
                    "critical_exposure_count": 2,
                },
                "drift": {
                    "average_score": 25.1,
                    "max_score": 72.0,
                    "min_score": 5.0,
                    "high_drift_count": 8,
                    "critical_drift_count": 1,
                },
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting aggregate scores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get aggregate scores: {str(e)}",
        )


@router.post(
    "/score/compare",
    response_model=Dict[str, Any],
    summary="Compare scores between entities",
    tags=["scoring"],
)
async def compare_entities(
    entity_ids: List[str],
    engines: Optional[List[str]] = None,
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Compare scoring results between multiple entities.

    Args:
        entity_ids: List of entity IDs to compare
        engines: Engines to include in comparison
        token_data: JWT token data

    Returns:
        Comparison results
    """
    require_permission("read", token_data)

    try:
        if len(entity_ids) < 2 or len(entity_ids) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide 2-10 entity IDs for comparison",
            )

        engines = engines or ["risk", "exposure", "drift"]

        # TODO: Implement entity comparison
        # For now, return mock comparison
        return {
            "entities": entity_ids,
            "engines": engines,
            "comparison": {
                "risk": {
                    "highest": entity_ids[0],
                    "lowest": entity_ids[1],
                    "average": 52.3,
                    "range": 82.5,
                },
                "exposure": {
                    "highest": entity_ids[0],
                    "lowest": entity_ids[2],
                    "average": 41.7,
                    "range": 78.9,
                },
                "drift": {
                    "highest": entity_ids[1],
                    "lowest": entity_ids[0],
                    "average": 28.4,
                    "range": 67.0,
                },
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing entities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare entities: {str(e)}",
        )


@router.get(
    "/score/status",
    response_model=Dict[str, Any],
    summary="Get scoring service status",
    tags=["scoring"],
)
async def get_scoring_status(
    token_data: TokenData = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Get scoring service status and health.

    Args:
        token_data: JWT token data

    Returns:
        Service status information
    """
    require_permission("read", token_data)

    try:
        # Check engine availability
        risk_engine = get_risk_engine()

        status = {
            "service": "scoring",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "engines": {
                "risk": {
                    "status": "available",
                    "last_run": datetime.utcnow().isoformat(),
                    "version": "1.0.0",
                },
                "exposure": {"status": "not_implemented", "version": "1.0.0"},
                "drift": {"status": "not_implemented", "version": "1.0.0"},
            },
            "metrics": {
                "total_requests": 0,  # TODO: Implement metrics
                "successful_requests": 0,
                "failed_requests": 0,
                "average_response_time_ms": 0.0,
            },
        }

        return status

    except Exception as e:
        logger.error(f"Error getting scoring status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}",
        )
