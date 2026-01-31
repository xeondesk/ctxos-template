"""
Agent analysis API tests.
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
        "permissions": [
            "read",
            "write",
            "delete",
            "manage_users",
            "manage_config",
            "view_audit_logs",
            "manage_rules",
            "run_agents",
            "run_pipelines",
            "manage_pipelines",
        ],
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
def viewer_token():
    """Create viewer token for testing."""
    payload = {
        "user_id": "viewer",
        "username": "viewer",
        "role": "viewer",
        "permissions": ["read", "view_audit_logs"],
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "jti": "test-jti-viewer",
        "type": "access",
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


@pytest.fixture
def sample_context():
    """Sample context for agent analysis."""
    return {
        "entity": {
            "id": "host-001",
            "entity_type": "host",
            "name": "web-server-01",
            "properties": {"environment": "production", "os": "linux"},
        },
        "signals": [
            {
                "id": "vuln-001",
                "source": "nessus",
                "signal_type": "vulnerability",
                "severity": "critical",
                "description": "CVE-2023-1234",
                "properties": {"cvss_score": 9.8, "cve_id": "CVE-2023-1234"},
            },
            {
                "id": "port-001",
                "source": "nmap",
                "signal_type": "port",
                "severity": "medium",
                "description": "Open port 443",
                "properties": {"port": 443, "service": "https"},
            },
        ],
    }


@pytest.fixture
def sample_scoring_result():
    """Sample scoring result for agent analysis."""
    return {
        "score": 75.0,
        "severity": "high",
        "metrics": {"vulnerability": 30, "exposure": 25, "configuration": 20},
        "recommendations": ["Update vulnerable services", "Review open ports"],
    }


class TestAgentEndpoints:
    """Test agent analysis endpoints."""

    def test_run_agent_success(self, client, admin_token, sample_context):
        """Test successful agent execution."""
        response = client.post(
            "/api/v1/agents/run",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "agent_name": "context_summarizer",
                "context": sample_context,
                "timeout_seconds": 30.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["agent_name"] == "context_summarizer"
        assert "success" in data
        assert "output" in data
        assert "duration_ms" in data
        assert "timestamp" in data

    def test_run_agent_with_scoring_result(
        self, client, admin_token, sample_context, sample_scoring_result
    ):
        """Test agent execution with scoring result."""
        response = client.post(
            "/api/v1/agents/run",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "agent_name": "explainability",
                "context": sample_context,
                "scoring_result": sample_scoring_result,
                "timeout_seconds": 30.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["agent_name"] == "explainability"
        assert data["success"] is True

    def test_run_agent_not_found(self, client, admin_token, sample_context):
        """Test running non-existent agent."""
        response = client.post(
            "/api/v1/agents/run",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"agent_name": "nonexistent_agent", "context": sample_context},
        )

        assert response.status_code == 404
        assert "Agent not found" in response.json()["detail"]

    def test_run_agent_unauthorized(self, client, viewer_token, sample_context):
        """Test agent execution without permission."""
        response = client.post(
            "/api/v1/agents/run",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={"agent_name": "context_summarizer", "context": sample_context},
        )

        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]

    def test_run_pipeline_success(self, client, admin_token, sample_context):
        """Test successful pipeline execution."""
        response = client.post(
            "/api/v1/agents/pipeline",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "pipeline_name": "security_analysis",
                "context": sample_context,
                "timeout_seconds": 60.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["pipeline_name"] == "security_analysis"
        assert "results" in data
        assert "duration_ms" in data
        assert "success_count" in data
        assert "total_count" in data

    def test_run_pipeline_custom(self, client, admin_token, sample_context):
        """Test custom pipeline execution."""
        response = client.post(
            "/api/v1/agents/pipeline",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "agents": ["context_summarizer", "gap_detector"],
                "context": sample_context,
                "parallel": True,
                "timeout_seconds": 60.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["success_count"] >= 0

    def test_run_pipeline_not_found(self, client, admin_token, sample_context):
        """Test running non-existent pipeline."""
        response = client.post(
            "/api/v1/agents/pipeline",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"pipeline_name": "nonexistent_pipeline", "context": sample_context},
        )

        assert response.status_code == 404
        assert "Pipeline not found" in response.json()["detail"]

    def test_bulk_analysis(self, client, admin_token):
        """Test bulk entity analysis."""
        response = client.post(
            "/api/v1/agents/bulk",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "entity_ids": ["host-001", "host-002", "host-003"],
                "entity_type": "host",
                "engines": ["risk"],
                "agents": ["context_summarizer"],
                "parallel": True,
                "timeout_per_entity": 30.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert "entity_count" in data
        assert "results" in data
        assert "timestamp" in data

        assert data["entity_count"] == 3
        assert len(data["results"]) == 3

    def test_bulk_analysis_too_many_entities(self, client, admin_token):
        """Test bulk analysis with too many entities."""
        entity_ids = [f"host-{i:04d}" for i in range(501)]  # Over limit

        response = client.post(
            "/api/v1/agents/bulk",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"entity_ids": entity_ids, "engines": ["risk"]},
        )

        assert response.status_code == 400
        assert "Maximum 500 entities allowed" in response.json()["detail"]

    def test_list_agents(self, client, admin_token):
        """Test listing available agents."""
        response = client.get(
            "/api/v1/agents/list", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "total" in data
        assert "available" in data
        assert "timestamp" in data

        agents = data["agents"]
        expected_agents = [
            "context_summarizer",
            "gap_detector",
            "hypothesis_generator",
            "explainability",
        ]
        for agent_name in expected_agents:
            assert agent_name in agents

    def test_get_agent_status(self, client, admin_token):
        """Test getting specific agent status."""
        response = client.get(
            "/api/v1/agents/status/context_summarizer",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "name" in data or "status" in data  # Agent info or error
        assert "last_check" in data

    def test_get_agent_status_not_found(self, client, admin_token):
        """Test getting status of non-existent agent."""
        response = client.get(
            "/api/v1/agents/status/nonexistent_agent",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404
        assert "Agent not found" in response.json()["detail"]

    def test_list_pipelines(self, client, admin_token):
        """Test listing available pipelines."""
        response = client.get(
            "/api/v1/agents/pipelines", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "pipelines" in data
        assert "total" in data
        assert "available" in data
        assert "timestamp" in data

        pipelines = data["pipelines"]
        expected_pipelines = ["security_analysis", "full_analysis", "quick_scan"]
        for pipeline_name in expected_pipelines:
            assert pipeline_name in pipelines

    def test_create_pipeline(self, client, admin_token):
        """Test creating new pipeline."""
        response = client.post(
            "/api/v1/agents/create-pipeline",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "pipeline_name": "test_pipeline",
                "agents": ["context_summarizer", "gap_detector"],
                "parallel": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["pipeline_name"] == "test_pipeline"
        assert data["parallel"] is False
        assert "added_agents" in data
        assert "total_agents" in data
        assert "timestamp" in data

    def test_create_pipeline_already_exists(self, client, admin_token):
        """Test creating pipeline that already exists."""
        response = client.post(
            "/api/v1/agents/create-pipeline",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "pipeline_name": "security_analysis",  # Already exists
                "agents": ["context_summarizer"],
            },
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_get_agent_metrics(self, client, admin_token):
        """Test getting agent performance metrics."""
        response = client.get(
            "/api/v1/agents/metrics", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "overall" in data
        assert "agents" in data
        assert "total_agents" in data
        assert "timestamp" in data

    def test_get_agent_health(self, client, admin_token):
        """Test getting agent service health."""
        response = client.get(
            "/api/v1/agents/health", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "agents"
        assert "status" in data
        assert "timestamp" in data
        assert "agents" in data
        assert "total_agents" in data
        assert "healthy_agents" in data
        assert "unhealthy_agents" in data

    def test_get_audit_logs(self, client, admin_token):
        """Test getting agent audit logs."""
        response = client.get(
            "/api/v1/agents/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"limit": 50},
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_next" in data

    def test_filter_agent_results(self, client, admin_token):
        """Test filtering agent results."""
        response = client.post(
            "/api/v1/agents/filter",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "entity_type": "host",
                "min_score": 50.0,
                "max_score": 100.0,
                "limit": 100,
                "offset": 0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_next" in data


class TestAgentPermissions:
    """Test agent endpoint permissions."""

    def test_analyst_can_run_agents(self, client, analyst_token, sample_context):
        """Test analyst can run agents."""
        response = client.post(
            "/api/v1/agents/run",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={"agent_name": "context_summarizer", "context": sample_context},
        )

        assert response.status_code == 200

    def test_analyst_can_run_pipelines(self, client, analyst_token, sample_context):
        """Test analyst can run pipelines."""
        response = client.post(
            "/api/v1/agents/pipeline",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={"pipeline_name": "security_analysis", "context": sample_context},
        )

        assert response.status_code == 200

    def test_analyst_can_list_agents(self, client, analyst_token):
        """Test analyst can list agents."""
        response = client.get(
            "/api/v1/agents/list", headers={"Authorization": f"Bearer {analyst_token}"}
        )

        assert response.status_code == 200

    def test_analyst_cannot_create_pipelines(self, client, analyst_token):
        """Test analyst cannot create pipelines."""
        response = client.post(
            "/api/v1/agents/create-pipeline",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={"pipeline_name": "test_pipeline", "agents": ["context_summarizer"]},
        )

        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]

    def test_viewer_cannot_run_agents(self, client, viewer_token, sample_context):
        """Test viewer cannot run agents."""
        response = client.post(
            "/api/v1/agents/run",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={"agent_name": "context_summarizer", "context": sample_context},
        )

        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]

    def test_viewer_can_list_agents(self, client, viewer_token):
        """Test viewer can list agents."""
        response = client.get(
            "/api/v1/agents/list", headers={"Authorization": f"Bearer {viewer_token}"}
        )

        assert response.status_code == 200

    def test_viewer_can_get_health(self, client, viewer_token):
        """Test viewer can get health status."""
        response = client.get(
            "/api/v1/agents/health", headers={"Authorization": f"Bearer {viewer_token}"}
        )

        assert response.status_code == 200


class TestAgentValidation:
    """Test agent input validation."""

    def test_invalid_agent_request(self, client, admin_token):
        """Test invalid agent request structure."""
        response = client.post(
            "/api/v1/agents/run",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "agent_name": "context_summarizer"
                # Missing context
            },
        )

        assert response.status_code == 422

    def test_invalid_context_structure(self, client, admin_token):
        """Test invalid context structure."""
        response = client.post(
            "/api/v1/agents/run",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"agent_name": "context_summarizer", "context": {"invalid": "structure"}},
        )

        assert response.status_code == 422

    def test_invalid_timeout_value(self, client, admin_token, sample_context):
        """Test invalid timeout value."""
        response = client.post(
            "/api/v1/agents/run",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "agent_name": "context_summarizer",
                "context": sample_context,
                "timeout_seconds": -1.0,  # Invalid negative timeout
            },
        )

        assert response.status_code == 422

    def test_pipeline_without_agents_or_name(self, client, admin_token, sample_context):
        """Test pipeline request without agents or name."""
        response = client.post(
            "/api/v1/agents/pipeline",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "context": sample_context
                # Missing both pipeline_name and agents
            },
        )

        assert response.status_code == 422
