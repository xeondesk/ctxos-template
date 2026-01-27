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
from api.server.middleware.rbac import RBACMiddleware, require_permission
from api.server.routes import scoring, analysis, config as config_routes
from core.scoring.risk import get_risk_engine


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
                "scoring": "/api/v1/score",
                "agents": "/api/v1/agents",
                "config": "/api/v1/config",
            },
        }
    
    # Include routers
    app.include_router(scoring.router, prefix="/api/v1", tags=["scoring"])
    app.include_router(analysis.router, prefix="/api/v1", tags=["agents"])
    app.include_router(config_routes.router, prefix="/api/v1", tags=["config"])
    
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
