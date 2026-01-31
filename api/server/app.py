"""
FastAPI application for CtxOS API layer.
"""

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from api.server.middleware.auth import verify_jwt_token, TokenData
from api.server.middleware.rbac import RBACMiddleware, require_permission, Permission
from api.server.routes import scoring, analysis, config as config_routes, auth
from core.scoring.risk import get_risk_engine
from agents.mcp_orchestrator import get_orchestrator
from agents.context_summarizer import ContextSummarizer
from agents.gap_detector import GapDetector
from agents.hypothesis_generator import HypothesisGenerator
from agents.explainability import ExplainabilityAgent


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title="CtxOS API",
        description="Context-driven OS Intelligence and Analysis API",
        version="1.0.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure from env
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # GZIP compression
    app.add_middleware(GZIPMiddleware, minimum_size=1000)

    # RBAC middleware
    app.add_middleware(RBACMiddleware)

    # Error handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "status_code": 500,
            },
        )

    # Health check
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "ctxos-api"}

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "CtxOS API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "docs": "/api/docs",
                "auth": "/api/v1/auth",
                "scoring": "/api/v1/score",
                "agents": "/api/v1/agents",
                "config": "/api/v1/config",
            },
        }

    # Include routers
    app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
    app.include_router(scoring.router, prefix="/api/v1", tags=["scoring"])
    app.include_router(analysis.router, prefix="/api/v1", tags=["agents"])
    app.include_router(config_routes.router, prefix="/api/v1", tags=["config"])

    # Initialize services on startup
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on application startup."""
        logger.info("Starting CtxOS API server...")

        # Initialize orchestrator and register agents
        orchestrator = get_orchestrator()

        # Register agents
        agents = [
            ContextSummarizer(name="context_summarizer", version="1.0.0"),
            GapDetector(name="gap_detector", version="1.0.0"),
            HypothesisGenerator(name="hypothesis_generator", version="1.0.0"),
            ExplainabilityAgent(name="explainability", version="1.0.0"),
        ]

        for agent in agents:
            orchestrator.register_agent(agent)
            logger.info(f"Registered agent: {agent.name}")

        # Create default pipelines
        default_pipelines = [
            (
                "security_analysis",
                ["context_summarizer", "gap_detector", "hypothesis_generator"],
                False,
            ),
            (
                "full_analysis",
                ["context_summarizer", "gap_detector", "hypothesis_generator", "explainability"],
                False,
            ),
            ("quick_scan", ["context_summarizer", "gap_detector"], True),
        ]

        for pipeline_name, agent_names, parallel in default_pipelines:
            pipeline = orchestrator.create_pipeline(pipeline_name, parallel)
            for agent_name in agent_names:
                agent = orchestrator.agents.get(agent_name)
                if agent:
                    pipeline.add_agent(agent)
            logger.info(f"Created pipeline: {pipeline_name}")

        # Test engines
        try:
            risk_engine = get_risk_engine()
            logger.info("Risk engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize risk engine: {e}")

        logger.info("CtxOS API server startup complete")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on application shutdown."""
        logger.info("Shutting down CtxOS API server...")

        # Cleanup orchestrator
        orchestrator = get_orchestrator()
        if hasattr(orchestrator, "shutdown"):
            await orchestrator.shutdown()

        logger.info("CtxOS API server shutdown complete")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
