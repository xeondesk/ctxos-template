"""
Authentication API endpoints (/api/v1/auth/*).
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from api.server.middleware.auth import (
    AuthService,
    verify_jwt_token,
    verify_refresh_token,
    create_access_token,
    create_refresh_token,
)
from api.server.middleware.rbac import require_permission, Permission
from api.server.models.response import StatusResponse

router = APIRouter()

# Basic auth for login
basic_auth = HTTPBasic()


class LoginRequest(BaseModel):
    """Login request."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: Dict[str, Any]


class RefreshRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str


class RefreshResponse(BaseModel):
    """Refresh token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post(
    "/auth/login",
    response_model=LoginResponse,
    summary="Authenticate user",
    tags=["auth"],
)
async def login(request: LoginRequest) -> LoginResponse:
    """Authenticate user and return tokens.

    Args:
        request: Login credentials

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If authentication fails
    """
    # Authenticate user
    access_token = AuthService.authenticate_user(
        username=request.username,
        password=request.password,
    )

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user info
    user = None
    for u in AuthService.USERS_DB.values():
        if u.username == request.username:
            user = u
            break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Create refresh token
    refresh_token = create_refresh_token(
        user_id=user.id,
        username=user.username,
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=24 * 3600,  # 24 hours in seconds
        user_info={
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "permissions": user.permissions,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        },
    )


@router.post(
    "/auth/refresh",
    response_model=RefreshResponse,
    summary="Refresh access token",
    tags=["auth"],
)
async def refresh_token(request: RefreshRequest) -> RefreshResponse:
    """Refresh access token using refresh token.

    Args:
        request: Refresh token request

    Returns:
        New access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    new_access_token = verify_refresh_token(request.refresh_token)

    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return RefreshResponse(
        access_token=new_access_token,
        expires_in=24 * 3600,  # 24 hours in seconds
    )


@router.get(
    "/auth/me",
    response_model=Dict[str, Any],
    summary="Get current user info",
    tags=["auth"],
)
async def get_current_user(
    token_data: Dict[str, Any] = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Get current user information.

    Args:
        token_data: JWT token data

    Returns:
        User information
    """
    user = AuthService.get_user_by_id(token_data.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "permissions": user.permissions,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "token_info": {
            "issued_at": token_data.iat.isoformat(),
            "expires_at": token_data.exp.isoformat(),
            "token_id": token_data.jti,
        },
    }


@router.post(
    "/auth/logout",
    response_model=StatusResponse,
    summary="Logout user",
    tags=["auth"],
)
async def logout(
    token_data: Dict[str, Any] = Depends(verify_jwt_token),
) -> StatusResponse:
    """Logout user and revoke token.

    Args:
        token_data: JWT token data

    Returns:
        Logout status
    """
    # Revoke token (in production, add to revoked token list)
    AuthService.revoke_token(token_data.jti)

    return StatusResponse(
        status="success",
        message="Successfully logged out",
        details={
            "revoked_at": datetime.utcnow().isoformat(),
            "token_id": token_data.jti,
        },
    )


@router.get(
    "/auth/verify",
    response_model=Dict[str, Any],
    summary="Verify token validity",
    tags=["auth"],
)
async def verify_token(
    token_data: Dict[str, Any] = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """Verify if token is valid and return token info.

    Args:
        token_data: JWT token data

    Returns:
        Token validity information
    """
    return {
        "valid": True,
        "token_info": {
            "user_id": token_data.user_id,
            "username": token_data.username,
            "role": token_data.role,
            "permissions": token_data.permissions,
            "issued_at": token_data.iat.isoformat(),
            "expires_at": token_data.exp.isoformat(),
            "token_id": token_data.jti,
        },
        "expires_in": int((token_data.exp - datetime.utcnow()).total_seconds()),
    }


@router.get(
    "/auth/health",
    response_model=Dict[str, Any],
    summary="Get auth service health",
    tags=["auth"],
)
async def get_auth_health() -> Dict[str, Any]:
    """Get authentication service health status.

    Returns:
        Health status information
    """
    return {
        "service": "auth",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "jwt_auth": True,
            "refresh_tokens": True,
            "api_keys": True,
            "rbac": True,
        },
        "statistics": {
            "total_users": len(AuthService.USERS_DB),
            "active_users": len([u for u in AuthService.USERS_DB.values() if u.is_active]),
            "total_api_keys": len(AuthService.API_KEYS_DB),
            "active_api_keys": len([k for k in AuthService.API_KEYS_DB.values() if k.is_active]),
        },
    }
