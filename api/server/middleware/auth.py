"""
JWT authentication middleware.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import jwt
from datetime import datetime, timedelta
import os
import hashlib
import secrets
from dataclasses import dataclass


class TokenData(BaseModel):
    """JWT token payload."""

    user_id: str
    username: str
    email: Optional[str] = None
    role: str  # admin, analyst, viewer, api_client
    permissions: List[str]
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for token revocation


class User(BaseModel):
    """User model."""

    id: str
    username: str
    email: Optional[str] = None
    role: str
    permissions: List[str]
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None


class APIKey(BaseModel):
    """API key model."""

    id: str
    name: str
    key_hash: str
    user_id: str
    permissions: List[str]
    is_active: bool = True
    expires_at: Optional[datetime] = None
    created_at: datetime
    last_used: Optional[datetime] = None


# Security
security = HTTPBearer()

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
JWT_REFRESH_EXPIRATION_DAYS = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))

# In-memory user store (replace with database in production)
USERS_DB: Dict[str, User] = {}
API_KEYS_DB: Dict[str, APIKey] = {}


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = secrets.token_hex(32)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    try:
        salt, hash_value = password_hash.split(":")
        computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return computed_hash == hash_value
    except ValueError:
        return False


def hash_api_key(api_key: str) -> str:
    """Hash API key."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def create_access_token(
    user_id: str,
    username: str,
    role: str,
    permissions: Optional[List[str]] = None,
    email: Optional[str] = None,
    expires_in_hours: Optional[int] = None,
) -> str:
    """Create JWT access token.

    Args:
        user_id: User ID
        username: Username
        role: User role
        permissions: List of permissions
        email: User email
        expires_in_hours: Custom expiration in hours

    Returns:
        JWT token
    """
    if permissions is None:
        permissions = []

    expiration_hours = expires_in_hours or JWT_EXPIRATION_HOURS
    jti = secrets.token_urlsafe(32)

    payload = {
        "user_id": user_id,
        "username": username,
        "email": email,
        "role": role,
        "permissions": permissions,
        "exp": datetime.utcnow() + timedelta(hours=expiration_hours),
        "iat": datetime.utcnow(),
        "jti": jti,
        "type": "access",
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def create_refresh_token(
    user_id: str,
    username: str,
) -> str:
    """Create JWT refresh token.

    Args:
        user_id: User ID
        username: Username

    Returns:
        JWT refresh token
    """
    jti = secrets.token_urlsafe(32)

    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(days=JWT_REFRESH_EXPIRATION_DAYS),
        "iat": datetime.utcnow(),
        "jti": jti,
        "type": "refresh",
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

        # Check token type
        token_type = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id: str = payload.get("user_id")
        username: str = payload.get("username")
        email: Optional[str] = payload.get("email")
        role: str = payload.get("role")
        permissions: List[str] = payload.get("permissions", [])
        exp: datetime = datetime.fromtimestamp(payload["exp"])
        iat: datetime = datetime.fromtimestamp(payload["iat"])
        jti: str = payload.get("jti")

        if not all([user_id, username, role]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is still active
        user = USERS_DB.get(user_id)
        if user and not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenData(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
            permissions=permissions,
            exp=exp,
            iat=iat,
            jti=jti,
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_refresh_token(token: str) -> Optional[str]:
    """Verify refresh token and return new access token.

    Args:
        token: Refresh token

    Returns:
        New access token or None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Check token type
        token_type = payload.get("type")
        if token_type != "refresh":
            return None

        user_id = payload.get("user_id")
        username = payload.get("username")

        if not all([user_id, username]):
            return None

        # Check if user is still active
        user = USERS_DB.get(user_id)
        if not user or not user.is_active:
            return None

        # Create new access token
        return create_access_token(
            user_id=user_id,
            username=username,
            role=user.role,
            permissions=user.permissions,
            email=user.email,
        )

    except jwt.JWTError:
        return None


class AuthService:
    """Authentication service."""

    @staticmethod
    def create_user(
        username: str,
        password: str,
        email: Optional[str] = None,
        role: str = "viewer",
        permissions: Optional[List[str]] = None,
    ) -> User:
        """Create a new user.

        Args:
            username: Username
            password: Password
            email: Email
            role: User role
            permissions: User permissions

        Returns:
            Created user
        """
        user_id = secrets.token_urlsafe(16)
        password_hash = hash_password(password)

        if permissions is None:
            permissions = ["read"]

        user = User(
            id=user_id,
            username=username,
            email=email,
            role=role,
            permissions=permissions,
            created_at=datetime.utcnow(),
        )

        USERS_DB[user_id] = user
        return user

    @staticmethod
    def authenticate_user(
        username: str,
        password: str,
    ) -> Optional[str]:
        """Authenticate user and return token.

        Args:
            username: Username
            password: Password

        Returns:
            JWT access token or None
        """
        # Find user by username (in production, use database)
        user = None
        for u in USERS_DB.values():
            if u.username == username and u.is_active:
                user = u
                break

        if not user:
            return None

        # In production, verify against stored password hash
        # For now, use simple password check
        if password and len(password) > 0:  # Placeholder validation
            # Update last login
            user.last_login = datetime.utcnow()

            return create_access_token(
                user_id=user.id,
                username=user.username,
                role=user.role,
                permissions=user.permissions,
                email=user.email,
            )

        return None

    @staticmethod
    def create_api_key(
        user_id: str,
        name: str,
        permissions: List[str],
        expires_in_days: Optional[int] = None,
    ) -> str:
        """Create API key for user.

        Args:
            user_id: User ID
            name: API key name
            permissions: API key permissions
            expires_in_days: Expiration in days

        Returns:
            API key
        """
        api_key = f"ctxos_{secrets.token_urlsafe(32)}"
        key_hash = hash_api_key(api_key)

        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        api_key_obj = APIKey(
            id=secrets.token_urlsafe(16),
            name=name,
            key_hash=key_hash,
            user_id=user_id,
            permissions=permissions,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
        )

        API_KEYS_DB[api_key_obj.id] = api_key_obj
        return api_key

    @staticmethod
    def validate_api_key(api_key: str) -> Optional[TokenData]:
        """Validate API key.

        Args:
            api_key: API key

        Returns:
            TokenData or None
        """
        key_hash = hash_api_key(api_key)

        # Find API key by hash
        api_key_obj = None
        for key_obj in API_KEYS_DB.values():
            if key_obj.key_hash == key_hash and key_obj.is_active:
                api_key_obj = key_obj
                break

        if not api_key_obj:
            return None

        # Check expiration
        if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
            return None

        # Get user
        user = USERS_DB.get(api_key_obj.user_id)
        if not user or not user.is_active:
            return None

        # Update last used
        api_key_obj.last_used = datetime.utcnow()

        return TokenData(
            user_id=user.id,
            username=user.username,
            email=user.email,
            role="api_client",
            permissions=api_key_obj.permissions,
            exp=datetime.utcnow() + timedelta(hours=1),  # API keys are short-lived
            iat=datetime.utcnow(),
            jti=api_key_obj.id,
        )

    @staticmethod
    def revoke_token(jti: str) -> bool:
        """Revoke token by JWT ID.

        Args:
            jti: JWT ID

        Returns:
            True if revoked, False if not found
        """
        # In production, maintain a revoked token list in database
        # For now, just return True
        return True

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User or None
        """
        return USERS_DB.get(user_id)

    @staticmethod
    def update_user_permissions(
        user_id: str,
        permissions: List[str],
    ) -> bool:
        """Update user permissions.

        Args:
            user_id: User ID
            permissions: New permissions

        Returns:
            True if updated, False if not found
        """
        user = USERS_DB.get(user_id)
        if user:
            user.permissions = permissions
            return True
        return False


# Initialize default users for development
def init_default_users():
    """Initialize default users for development."""
    if not USERS_DB:
        # Create admin user
        AuthService.create_user(
            username="admin",
            password="admin123",
            email="admin@ctxos.local",
            role="admin",
            permissions=[
                "read",
                "write",
                "delete",
                "manage_users",
                "manage_config",
                "view_audit_logs",
                "manage_rules",
            ],
        )

        # Create analyst user
        AuthService.create_user(
            username="analyst",
            password="analyst123",
            email="analyst@ctxos.local",
            role="analyst",
            permissions=["read", "write", "run_agents", "run_pipelines", "view_audit_logs"],
        )

        # Create viewer user
        AuthService.create_user(
            username="viewer",
            password="viewer123",
            email="viewer@ctxos.local",
            role="viewer",
            permissions=["read", "view_audit_logs"],
        )

        # Create API key for system
        AuthService.create_api_key(
            user_id="admin",  # Will be replaced with actual admin user ID
            name="system-api-key",
            permissions=["read", "run_agents", "run_pipelines"],
        )


# Initialize default users
init_default_users()
