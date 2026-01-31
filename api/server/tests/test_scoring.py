"""
Scoring API tests.
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
        "role": "analyst",
        "permissions": ["read", "write", "run_agents", "run_pipelines", "view_audit_logs"],
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "jti": "test-jti-analyst",
        "type": "access",
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


@pytest.fixture
def sample_context():
    """Sample context for scoring."""
    return {
        "entity": {
            "id": "host-001",
            "entity_type": "host",
            "name": "web-server-01",
            "properties": {
                "environment": "production",
                "os": "linux"
            }
        },
        "signals": [
            {
                "id": "vuln-001",
                "source": "nessus",
                "signal_type": "vulnerability",
                "severity": "critical",
                "description": "CVE-2023-1234",
                "properties": {
                    "cvss_score": 9.8,
                    "cve_id": "CVE-2023-1234"
                }
            },
            {
                "id": "port-001",
                "source": "nmap",
                "signal_type": "port",
                "severity": "medium",
                "description": "Open port 443",
                "properties": {
                    "port": 443,
                    "service": "https"
                }
            }
        ]
    }


class TestScoringEndpoints:
    """Test scoring endpoints."""
    
    def test_score_entity_success(self, client, admin_token, sample_context):
        """Test successful entity scoring."""
        response = client.post(
            "/api/v1/score",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "context": sample_context,
                "engines": ["risk"],
                "include_recommendations": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        result = data[0]
        assert result["entity_id"] == "host-001"
        assert result["entity_type"] == "host"
        assert result["engine_name"] == "risk"
        assert "score" in result
        assert "severity" in result
        assert "factors" in result
        assert "timestamp" in result
    
    def test_score_entity_all_engines(self, client, admin_token, sample_context):
        """Test scoring with all engines."""
        response = client.post(
            "/api/v1/score",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "context": sample_context,
                "engines": ["risk", "exposure", "drift"],
                "include_recommendations": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should return results for available engines (risk is implemented)
        assert len(data) >= 1
    
    def test_score_entity_unauthorized(self, client, sample_context):
        """Test scoring without authentication."""
        response = client.post(
            "/api/v1/score",
            json={
                "context": sample_context,
                "engines": ["risk"]
            }
        )
        
        assert response.status_code == 403
    
    def test_score_entity_invalid_engines(self, client, admin_token, sample_context):
        """Test scoring with invalid engines."""
        response = client.post(
            "/api/v1/score",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "context": sample_context,
                "engines": ["invalid_engine"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should return empty list for invalid engines
        assert len(data) == 0
    
    def test_batch_scoring_success(self, client, admin_token):
        """Test batch entity scoring."""
        contexts = [
            {
                "entity": {
                    "id": f"host-{i:03d}",
                    "entity_type": "host",
                    "name": f"web-server-{i:03d}"
                },
                "signals": []
            }
            for i in range(3)
        ]
        
        response = client.post(
            "/api/v1/score/batch",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "contexts": contexts,
                "engines": ["risk"],
                "parallel": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3  # One result per entity
    
    def test_batch_scoring_too_many_entities(self, client, admin_token):
        """Test batch scoring with too many entities."""
        contexts = [
            {
                "entity": {"id": f"host-{i:03d}", "entity_type": "host"},
                "signals": []
            }
            for i in range(101)  # Over the limit of 100
        ]
        
        response = client.post(
            "/api/v1/score/batch",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "contexts": contexts,
                "engines": ["risk"]
            }
        )
        
        assert response.status_code == 400
        assert "Maximum 100 entities allowed" in response.json()["detail"]
    
    def test_get_scoring_history(self, client, admin_token):
        """Test getting scoring history."""
        response = client.post(
            "/api/v1/score/history/host-001",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "date_from": "2024-01-01T00:00:00Z",
                "date_to": "2024-01-31T23:59:59Z",
                "engines": ["risk"],
                "granularity": "daily",
                "limit": 31
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_next" in data
    
    def test_get_available_engines(self, client, admin_token):
        """Test getting available scoring engines."""
        response = client.get(
            "/api/v1/score/engines",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data
        assert "total" in data
        assert "available" in data
        
        engines = data["engines"]
        assert "risk" in engines
        assert engines["risk"]["status"] == "available"
        assert "exposure" in engines
        assert "drift" in engines
    
    def test_get_aggregate_scores(self, client, admin_token):
        """Test getting aggregate scores."""
        response = client.post(
            "/api/v1/score/aggregate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "entity_ids": ["host-001", "host-002", "host-003"],
                "engines": ["risk"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "entity_count" in data
        assert "engines" in data
        assert "statistics" in data
        assert "timestamp" in data
        
        assert data["entity_count"] == 3
        assert "risk" in data["statistics"]
    
    def test_get_aggregate_scores_too_many_entities(self, client, admin_token):
        """Test aggregate scores with too many entities."""
        entity_ids = [f"host-{i:04d}" for i in range(1001)]  # Over limit
        
        response = client.post(
            "/api/v1/score/aggregate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "entity_ids": entity_ids,
                "engines": ["risk"]
            }
        )
        
        assert response.status_code == 400
        assert "Maximum 1000 entity IDs allowed" in response.json()["detail"]
    
    def test_compare_entities(self, client, admin_token):
        """Test entity comparison."""
        response = client.post(
            "/api/v1/score/compare",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "entity_ids": ["host-001", "host-002"],
                "engines": ["risk"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert "engines" in data
        assert "comparison" in data
        assert "timestamp" in data
        
        assert data["entities"] == ["host-001", "host-002"]
        assert "risk" in data["comparison"]
    
    def test_compare_entities_invalid_count(self, client, admin_token):
        """Test entity comparison with invalid entity count."""
        response = client.post(
            "/api/v1/score/compare",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "entity_ids": ["host-001"],  # Only one entity
                "engines": ["risk"]
            }
        )
        
        assert response.status_code == 400
        assert "Must provide 2-10 entity IDs" in response.json()["detail"]
    
    def test_get_scoring_status(self, client, admin_token):
        """Test getting scoring service status."""
        response = client.get(
            "/api/v1/score/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "scoring"
        assert "status" in data
        assert "timestamp" in data
        assert "engines" in data
        assert "metrics" in data
        
        engines = data["engines"]
        assert "risk" in engines
        assert engines["risk"]["status"] == "available"


class TestScoringValidation:
    """Test scoring input validation."""
    
    def test_invalid_context_structure(self, client, admin_token):
        """Test scoring with invalid context structure."""
        response = client.post(
            "/api/v1/score",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "context": {
                    "invalid": "structure"
                },
                "engines": ["risk"]
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_missing_required_fields(self, client, admin_token):
        """Test scoring with missing required fields."""
        response = client.post(
            "/api/v1/score",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "engines": ["risk"]
                # Missing context
            }
        )
        
        assert response.status_code == 422
    
    def test_invalid_entity_type(self, client, admin_token):
        """Test scoring with invalid entity type."""
        response = client.post(
            "/api/v1/score",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "context": {
                    "entity": {
                        "id": "test-001",
                        "entity_type": "invalid_type",
                        "name": "test"
                    },
                    "signals": []
                },
                "engines": ["risk"]
            }
        )
        
        assert response.status_code == 422


class TestScoringPermissions:
    """Test scoring endpoint permissions."""
    
    def test_analyst_can_score(self, client, analyst_token, sample_context):
        """Test analyst can score entities."""
        response = client.post(
            "/api/v1/score",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={
                "context": sample_context,
                "engines": ["risk"]
            }
        )
        
        assert response.status_code == 200
    
    def test_analyst_can_get_engines(self, client, analyst_token):
        """Test analyst can get available engines."""
        response = client.get(
            "/api/v1/score/engines",
            headers={"Authorization": f"Bearer {analyst_token}"}
        )
        
        assert response.status_code == 200
    
    def test_analyst_can_get_status(self, client, analyst_token):
        """Test analyst can get scoring status."""
        response = client.get(
            "/api/v1/score/status",
            headers={"Authorization": f"Bearer {analyst_token}"}
        )
        
        assert response.status_code == 200
