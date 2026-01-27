"""
JWT authentication middleware.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta
import os


class TokenData(BaseModel):
    """JWT token payload."""
    user_id: str
    username: str
    role: str  # admin, analyst, viewer, api_client
    permissions: list
    exp: datetime


# Security
security = HTTPBearer()

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


def create_access_token(
    user_id: str,
    username: str,
    role: str,
    permissions: Optional[list] = None,
) -> str:
    """Create JWT access token.
    
    Args:
        user_id: User ID
        username: Username
        role: User role
        permissions: List of permissions
        
    Returns:
        JWT token
    """
    if permissions is None:
        permissions = []
    
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "permissions": permissions,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow(),
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_jwt_token(credentials: HTTPAuthCredentials = Depends(security)) -> TokenData:
    """Verify JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        TokenData
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        user_id: str = payload.get("user_id")
        username: str = payload.get("username")
        role: str = payload.get("role")
        permissions: list = payload.get("permissions", [])
        
        if not all([user_id, username, role]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(
            user_id=user_id,
            username=username,
            role=role,
            permissions=permissions,
            exp=datetime.fromtimestamp(payload["exp"]),
        )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthService:
    """Authentication service."""
    
    @staticmethod
    def get_token_from_credentials(
        user_id: str,
        password: str,
    ) -> Optional[str]:
        """Authenticate user and return token.
        
        Args:
            user_id: User ID
            password: Password
            
        Returns:
            JWT token or None
        """
        # TODO: Implement actual authentication with database
        # This is a placeholder
        if user_id and password:  # Placeholder validation
            return create_access_token(
                user_id=user_id,
                username=user_id,
                role="analyst",
                permissions=["read", "write"],
            )
        return None
    
    @staticmethod
    def validate_api_key(api_key: str) -> Optional[TokenData]:
        """Validate API key.
        
        Args:
            api_key: API key
            
        Returns:
            TokenData or None
        """
        # TODO: Implement API key validation
        # This is a placeholder
        if api_key == os.getenv("API_KEY", "dev-api-key"):
            return TokenData(
                user_id="api-client",
                username="api-client",
                role="api_client",
                permissions=["read"],
                exp=datetime.utcnow() + timedelta(hours=24),
            )
        return None
