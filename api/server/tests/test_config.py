"""
Configuration API tests.
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


class TestConfigEndpoints:
    """Test configuration endpoints."""

    def test_get_all_config(self, client, admin_token):
        """Test getting all configuration."""
        response = client.get("/api/v1/config", headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert "metadata" in data

        config = data["config"]
        assert "agents.timeout" in config
        assert "scoring.cache_ttl" in config

        metadata = data["metadata"]
        assert metadata["total_keys"] > 0
        assert "last_updated" in metadata
        assert "version" in metadata

    def test_get_config_value(self, client, admin_token):
        """Test getting specific configuration value."""
        response = client.get(
            "/api/v1/config/agents.timeout", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "agents.timeout"
        assert "value" in data
        assert "metadata" in data

        assert isinstance(data["value"], int)
        assert data["metadata"]["type"] == "int"

    def test_get_config_value_not_found(self, client, admin_token):
        """Test getting non-existent configuration value."""
        response = client.get(
            "/api/v1/config/nonexistent.key", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404
        assert "Configuration key not found" in response.json()["detail"]

    def test_update_config_success(self, client, admin_token):
        """Test successful configuration update."""
        response = client.post(
            "/api/v1/config/update",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "config_key": "agents.timeout",
                "value": 45,
                "description": "Updated timeout for testing",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "agents.timeout" in data["message"]
        assert data["key"] == "agents.timeout"
        assert data["new_value"] == 45
        assert "updated_by" == "admin"
        assert "updated_at" in data

    def test_update_config_invalid_key(self, client, admin_token):
        """Test updating non-existent configuration key."""
        response = client.post(
            "/api/v1/config/update",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"config_key": "nonexistent.key", "value": 100},
        )

        assert response.status_code == 404
        assert "Configuration key not found" in response.json()["detail"]

    def test_update_config_invalid_value(self, client, admin_token):
        """Test updating configuration with invalid value."""
        response = client.post(
            "/api/v1/config/update",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"config_key": "agents.timeout", "value": "invalid_value"},  # Should be a number
        )

        assert response.status_code == 400
        assert "Invalid configuration value" in response.json()["detail"]

    def test_get_rules(self, client, admin_token):
        """Test getting all scoring rules."""
        response = client.get(
            "/api/v1/config/rules", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        assert "metadata" in data

        metadata = data["metadata"]
        assert metadata["total_rules"] >= 0
        assert "enabled_rules" >= 0
        assert "rule_types" in metadata
        assert "last_updated" in metadata

    def test_create_rule_success(self, client, admin_token):
        """Test successful rule creation."""
        response = client.post(
            "/api/v1/config/rules",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "rule_id": "test-rule-001",
                "rule_type": "risk",
                "name": "Test Risk Rule",
                "description": "A test rule for risk assessment",
                "condition": {"entity_type": "host", "min_open_ports": 10},
                "action": {"risk_multiplier": 1.5, "recommendation": "Review open ports"},
                "priority": 80,
                "enabled": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "test-rule-001" in data["message"]
        assert "rule" in data

        rule = data["rule"]
        assert rule["id"] == "test-rule-001"
        assert rule["type"] == "risk"
        assert rule["name"] == "Test Risk Rule"
        assert rule["priority"] == 80
        assert rule["enabled"] is True
        assert rule["created_by"] == "admin"
        assert "created_at" in rule

    def test_create_rule_invalid_type(self, client, admin_token):
        """Test creating rule with invalid type."""
        response = client.post(
            "/api/v1/config/rules",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "rule_id": "test-rule-invalid",
                "rule_type": "invalid_type",
                "name": "Invalid Rule",
                "condition": {"entity_type": "host"},
                "action": {"risk_multiplier": 1.0},
            },
        )

        assert response.status_code == 400
        assert "Invalid rule configuration" in response.json()["detail"]

    def test_create_rule_missing_fields(self, client, admin_token):
        """Test creating rule with missing required fields."""
        response = client.post(
            "/api/v1/config/rules",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "rule_id": "test-rule-incomplete",
                "rule_type": "risk",
                "name": "Incomplete Rule"
                # Missing condition and action
            },
        )

        assert response.status_code == 400
        assert "Invalid rule configuration" in response.json()["detail"]

    def test_get_rule(self, client, admin_token):
        """Test getting specific rule."""
        # First create a rule
        create_response = client.post(
            "/api/v1/config/rules",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "rule_id": "test-rule-get",
                "rule_type": "risk",
                "name": "Test Get Rule",
                "condition": {"entity_type": "host"},
                "action": {"risk_multiplier": 1.0},
            },
        )
        assert create_response.status_code == 200

        # Then get the rule
        response = client.get(
            "/api/v1/config/rules/test-rule-get", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "rule" in data
        assert "metadata" in data

        rule = data["rule"]
        assert rule["id"] == "test-rule-get"
        assert rule["name"] == "Test Get Rule"

    def test_get_rule_not_found(self, client, admin_token):
        """Test getting non-existent rule."""
        response = client.get(
            "/api/v1/config/rules/nonexistent-rule",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404
        assert "Rule not found" in response.json()["detail"]

    def test_update_rule(self, client, admin_token):
        """Test updating existing rule."""
        # First create a rule
        create_response = client.post(
            "/api/v1/config/rules",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "rule_id": "test-rule-update",
                "rule_type": "risk",
                "name": "Test Update Rule",
                "condition": {"entity_type": "host"},
                "action": {"risk_multiplier": 1.0},
            },
        )
        assert create_response.status_code == 200

        # Then update the rule
        response = client.put(
            "/api/v1/config/rules/test-rule-update",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Updated Rule Name", "priority": 90, "enabled": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "test-rule-update" in data["message"]

        rule = data["rule"]
        assert rule["name"] == "Updated Rule Name"
        assert rule["priority"] == 90
        assert rule["enabled"] is False
        assert rule["updated_by"] == "admin"
        assert rule["version"] == 2

    def test_delete_rule(self, client, admin_token):
        """Test deleting a rule."""
        # First create a rule
        create_response = client.post(
            "/api/v1/config/rules",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "rule_id": "test-rule-delete",
                "rule_type": "risk",
                "name": "Test Delete Rule",
                "condition": {"entity_type": "host"},
                "action": {"risk_multiplier": 1.0},
            },
        )
        assert create_response.status_code == 200

        # Then delete the rule
        response = client.delete(
            "/api/v1/config/rules/test-rule-delete",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "test-rule-delete" in data["message"]
        assert data["deleted_by"] == "admin"
        assert "deleted_at" in data

    def test_delete_rule_not_found(self, client, admin_token):
        """Test deleting non-existent rule."""
        response = client.delete(
            "/api/v1/config/rules/nonexistent-rule",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404
        assert "Rule not found" in response.json()["detail"]

    def test_export_config(self, client, admin_token):
        """Test exporting configuration."""
        response = client.post(
            "/api/v1/config/export",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"include_rules": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert "rules" in data
        assert "exported_at" in data
        assert "exported_by" in data
        assert "version" in data

        assert data["exported_by"] == "admin"

    def test_import_config(self, client, admin_token):
        """Test importing configuration."""
        export_data = {
            "config": {"agents.timeout": 60, "scoring.cache_ttl": 600},
            "rules": {
                "imported-rule": {
                    "type": "risk",
                    "name": "Imported Rule",
                    "condition": {"entity_type": "host"},
                    "action": {"risk_multiplier": 1.2},
                }
            },
        }

        response = client.post(
            "/api/v1/config/import",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=export_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "imported_config" in data
        assert "imported_rules" in data
        assert "errors" in data
        assert "imported_by" in data

        assert data["imported_config"] >= 0
        assert data["imported_rules"] >= 0

    def test_get_config_audit_logs(self, client, admin_token):
        """Test getting configuration audit logs."""
        response = client.get(
            "/api/v1/config/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"limit": 50, "offset": 0},
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_next" in data

        # Check structure of log items
        if data["items"]:
            item = data["items"][0]
            assert "timestamp" in item
            assert "agent" in item
            assert "action" in item
            assert "status" in item

    def test_get_config_health(self, client, admin_token):
        """Test getting configuration service health."""
        response = client.get(
            "/api/v1/config/health", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "config"
        assert "status" in data
        assert "timestamp" in data
        assert "configuration" in data
        assert "validation_errors" in data
        assert "validation_count" in data

        config_health = data["configuration"]
        assert "total_keys" in config_health
        assert "total_rules" in config_health
        assert "enabled_rules" in config_health


class TestConfigPermissions:
    """Test configuration endpoint permissions."""

    def test_analyst_can_read_config(self, client, analyst_token):
        """Test analyst can read configuration."""
        response = client.get(
            "/api/v1/config", headers={"Authorization": f"Bearer {analyst_token}"}
        )

        assert response.status_code == 200

    def test_analyst_can_read_rules(self, client, analyst_token):
        """Test analyst can read rules."""
        response = client.get(
            "/api/v1/config/rules", headers={"Authorization": f"Bearer {analyst_token}"}
        )

        assert response.status_code == 200

    def test_analyst_cannot_update_config(self, client, analyst_token):
        """Test analyst cannot update configuration."""
        response = client.post(
            "/api/v1/config/update",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={"config_key": "agents.timeout", "value": 45},
        )

        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]

    def test_analyst_cannot_create_rules(self, client, analyst_token):
        """Test analyst cannot create rules."""
        response = client.post(
            "/api/v1/config/rules",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={
                "rule_id": "test-rule",
                "rule_type": "risk",
                "name": "Test Rule",
                "condition": {"entity_type": "host"},
                "action": {"risk_multiplier": 1.0},
            },
        )

        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]

    def test_viewer_can_read_config(self, client, viewer_token):
        """Test viewer can read configuration."""
        response = client.get("/api/v1/config", headers={"Authorization": f"Bearer {viewer_token}"})

        assert response.status_code == 200

    def test_viewer_cannot_export_config(self, client, viewer_token):
        """Test viewer cannot export configuration."""
        response = client.post(
            "/api/v1/config/export", headers={"Authorization": f"Bearer {viewer_token}"}
        )

        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]

    def test_unauthorized_access(self, client):
        """Test unauthorized access to config endpoints."""
        response = client.get("/api/v1/config")

        assert response.status_code == 403


class TestConfigValidation:
    """Test configuration input validation."""

    def test_invalid_config_update_request(self, client, admin_token):
        """Test invalid config update request."""
        response = client.post(
            "/api/v1/config/update",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                # Missing config_key
                "value": 100
            },
        )

        assert response.status_code == 422

    def test_invalid_rule_creation_request(self, client, admin_token):
        """Test invalid rule creation request."""
        response = client.post(
            "/api/v1/config/rules",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                # Missing required fields
                "rule_id": "test-rule"
            },
        )

        assert response.status_code == 422

    def test_invalid_import_data(self, client, admin_token):
        """Test invalid import data structure."""
        response = client.post(
            "/api/v1/config/import",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"invalid": "structure"},
        )

        assert response.status_code == 400
        assert "Import failed" in response.json()["detail"]
