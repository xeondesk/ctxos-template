"""
Authentication API tests.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import jwt

from api.server.app import create_app
from api.server.middleware.auth import JWT_SECRET, JWT_ALGORITHM


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def admin_token():
    """Create admin token for testing."""
    payload = {
        "user_id": "admin",
        "username": "admin",
        "email": "admin@ctxos.local",
        "role": "admin",
        "permissions": ["read", "write", "delete", "manage_users", "manage_config", "view_audit_logs", "manage_rules"],
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "jti": "test-jti-admin",
        "type": "access",
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


@pytest.fixture
def analyst_token():
    """Create analyst token for testing."""
    payload = {
        "user_id": "analyst",
        "username": "analyst",
        "email": "analyst@ctxos.local",
        "role": "analyst",
        "permissions": ["read", "write", "run_agents", "run_pipelines", "view_audit_logs"],
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "jti": "test-jti-analyst",
        "type": "access",
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_login_success(self, client):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user_info" in data
        assert data["user_info"]["username"] == "admin"
        assert data["user_info"]["role"] == "admin"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin"
                # Missing password
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_current_user(self, client, admin_token):
        """Test getting current user info."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"
        assert "permissions" in data
        assert "token_info" in data
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without token."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 403  # No auth header
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
    
    def test_verify_token(self, client, admin_token):
        """Test token verification."""
        response = client.get(
            "/api/v1/auth/verify",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "token_info" in data
        assert "expires_in" in data
        assert data["token_info"]["username"] == "admin"
    
    def test_logout(self, client, admin_token):
        """Test logout."""
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "revoked_at" in data
    
    def test_refresh_token(self, client, admin_token):
        """Test token refresh."""
        # First login to get refresh token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token to get new access token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_refresh_token"}
        )
        
        assert response.status_code == 401
        assert "Invalid or expired refresh token" in response.json()["detail"]
    
    def test_auth_health(self, client):
        """Test auth service health check."""
        response = client.get("/api/v1/auth/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "auth"
        assert data["status"] == "healthy"
        assert "features" in data
        assert "statistics" in data


class TestRBAC:
    """Test role-based access control."""
    
    def test_admin_access(self, client, admin_token):
        """Test admin can access admin endpoints."""
        response = client.get(
            "/api/v1/config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
    
    def test_analyst_access(self, client, analyst_token):
        """Test analyst can access read endpoints."""
        response = client.get(
            "/api/v1/config",
            headers={"Authorization": f"Bearer {analyst_token}"}
        )
        
        assert response.status_code == 200
    
    def test_analyst_cannot_manage_config(self, client, analyst_token):
        """Test analyst cannot manage config."""
        response = client.post(
            "/api/v1/config/update",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={
                "config_key": "agents.timeout",
                "value": 45
            }
        )
        
        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access."""
        response = client.get("/api/v1/config")
        
        assert response.status_code == 403


class TestTokenValidation:
    """Test token validation and security."""
    
    def test_expired_token(self, client):
        """Test expired token rejection."""
        # Create expired token
        payload = {
            "user_id": "admin",
            "username": "admin",
            "role": "admin",
            "permissions": ["read"],
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired
            "iat": datetime.utcnow() - timedelta(hours=2),
            "jti": "test-expired",
            "type": "access",
        }
        expired_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
        assert "Token expired" in response.json()["detail"]
    
    def test_wrong_token_type(self, client):
        """Test wrong token type rejection."""
        # Create refresh token and try to use as access token
        payload = {
            "user_id": "admin",
            "username": "admin",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "jti": "test-refresh",
            "type": "refresh",  # Wrong type
        }
        refresh_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        
        assert response.status_code == 401
        assert "Invalid token type" in response.json()["detail"]
    
    def test_malformed_token(self, client):
        """Test malformed token rejection."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not.a.valid.jwt"}
        )
        
        assert response.status_code == 401
    
    def test_missing_bearer_prefix(self, client, admin_token):
        """Test missing Bearer prefix."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": admin_token}  # Missing "Bearer "
        )
        
        assert response.status_code == 403
