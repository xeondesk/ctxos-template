"""
Integration tests for the complete API.
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
        "permissions": ["read", "write", "delete", "manage_users", "manage_config", "view_audit_logs", "manage_rules", "run_agents", "run_pipelines", "manage_pipelines"],
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
    """Sample context for testing."""
    return {
        "entity": {
            "id": "host-001",
            "entity_type": "host",
            "name": "web-server-01",
            "properties": {
                "environment": "production",
                "os": "linux",
                "ip_address": "192.168.1.100"
            }
        },
        "signals": [
            {
                "id": "vuln-001",
                "source": "nessus",
                "signal_type": "vulnerability",
                "severity": "critical",
                "description": "CVE-2023-1234: Remote Code Execution",
                "properties": {
                    "cvss_score": 9.8,
                    "cve_id": "CVE-2023-1234",
                    "affected_service": "nginx"
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
                    "service": "https",
                    "state": "open"
                }
            },
            {
                "id": "config-001",
                "source": "config_audit",
                "signal_type": "configuration",
                "severity": "low",
                "description": "SSL certificate expiring soon",
                "properties": {
                    "cert_expiry_days": 15,
                    "cert_issuer": "Let's Encrypt"
                }
            }
        ]
    }


class TestAPIIntegration:
    """Test complete API integration scenarios."""
    
    def test_complete_analysis_workflow(self, client, admin_token, sample_context):
        """Test complete analysis workflow: score -> analyze -> explain."""
        # Step 1: Score the entity
        score_response = client.post(
            "/api/v1/score",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "context": sample_context,
                "engines": ["risk"],
                "include_recommendations": True
            }
        )
        
        assert score_response.status_code == 200
        score_data = score_response.json()
        assert len(score_data) > 0
        scoring_result = score_data[0]
        
        # Step 2: Run agent analysis pipeline
        pipeline_response = client.post(
            "/api/v1/agents/pipeline",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "pipeline_name": "full_analysis",
                "context": sample_context,
                "scoring_result": {
                    "score": scoring_result["score"],
                    "severity": scoring_result["severity"],
                    "factors": scoring_result["factors"]
                },
                "timeout_seconds": 120.0
            }
        )
        
        assert pipeline_response.status_code == 200
        pipeline_data = pipeline_response.json()
        assert pipeline_data["success_count"] > 0
        assert pipeline_data["total_count"] > 0
        
        # Step 3: Get comprehensive results
        results = pipeline_data["results"]
        assert "context_summarizer" in results
        assert "gap_detector" in results
        assert "hypothesis_generator" in results
        assert "explainability" in results
        
        # Verify each agent succeeded
        for agent_name, result in results.items():
            assert result["success"] is True
            assert "output" in result
            assert "duration_ms" in result
    
    def test_config_and_agent_integration(self, client, admin_token, sample_context):
        """Test configuration changes affecting agent behavior."""
        # Step 1: Update agent timeout configuration
        config_response = client.post(
            "/api/v1/config/update",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "config_key": "agents.timeout",
                "value": 60,
                "description": "Increased timeout for testing"
            }
        )
        
        assert config_response.status_code == 200
        
        # Step 2: Create a custom rule
        rule_response = client.post(
            "/api/v1/config/rules",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "rule_id": "integration-test-rule",
                "rule_type": "risk",
                "name": "Integration Test Rule",
                "description": "Rule for integration testing",
                "condition": {
                    "entity_type": "host",
                    "min_critical_vulns": 1
                },
                "action": {
                    "risk_multiplier": 2.0,
                    "recommendation": "Address critical vulnerabilities immediately"
                },
                "priority": 90,
                "enabled": True
            }
        )
        
        assert rule_response.status_code == 200
        
        # Step 3: Run analysis with new configuration
        agent_response = client.post(
            "/api/v1/agents/run",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "agent_name": "context_summarizer",
                "context": sample_context,
                "timeout_seconds": 60.0  # Use updated timeout
            }
        )
        
        assert agent_response.status_code == 200
        agent_data = agent_response.json()
        assert agent_data["success"] is True
        assert agent_data["duration_ms"] < 60000  # Should complete within timeout
    
    def test_batch_processing_workflow(self, client, admin_token):
        """Test batch processing of multiple entities."""
        # Create multiple contexts for batch processing
        contexts = []
        for i in range(5):
            context = {
                "entity": {
                    "id": f"host-{i:03d}",
                    "entity_type": "host",
                    "name": f"server-{i:03d}",
                    "properties": {"environment": "production"}
                },
                "signals": [
                    {
                        "id": f"vuln-{i:03d}",
                        "source": "scanner",
                        "signal_type": "vulnerability",
                        "severity": "high" if i % 2 == 0 else "medium",
                        "description": f"Test vulnerability {i}"
                    }
                ]
            }
            contexts.append(context)
        
        # Step 1: Batch scoring
        batch_score_response = client.post(
            "/api/v1/score/batch",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "contexts": contexts,
                "engines": ["risk"],
                "parallel": True
            }
        )
        
        assert batch_score_response.status_code == 200
        batch_score_data = batch_score_response.json()
        assert len(batch_score_data) == 5  # One result per entity
        
        # Step 2: Bulk agent analysis
        entity_ids = [f"host-{i:03d}" for i in range(5)]
        bulk_response = client.post(
            "/api/v1/agents/bulk",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "entity_ids": entity_ids,
                "entity_type": "host",
                "engines": ["risk"],
                "agents": ["context_summarizer"],
                "parallel": True,
                "timeout_per_entity": 30.0
            }
        )
        
        assert bulk_response.status_code == 200
        bulk_data = bulk_response.json()
        assert bulk_data["entity_count"] == 5
        assert len(bulk_data["results"]) == 5
    
    def test_audit_trail_integration(self, client, admin_token, sample_context):
        """Test audit trail across all operations."""
        # Step 1: Perform various operations
        operations = [
            # Config update
            client.post(
                "/api/v1/config/update",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"config_key": "agents.timeout", "value": 45}
            ),
            # Rule creation
            client.post(
                "/api/v1/config/rules",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "rule_id": "audit-test-rule",
                    "rule_type": "risk",
                    "name": "Audit Test Rule",
                    "condition": {"entity_type": "host"},
                    "action": {"risk_multiplier": 1.0}
                }
            ),
            # Entity scoring
            client.post(
                "/api/v1/score",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"context": sample_context, "engines": ["risk"]}
            ),
            # Agent execution
            client.post(
                "/api/v1/agents/run",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"agent_name": "context_summarizer", "context": sample_context}
            ),
        ]
        
        # Verify all operations succeeded
        for response in operations:
            assert response.status_code in [200, 201]
        
        # Step 2: Check audit logs
        audit_response = client.get(
            "/api/v1/agents/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"limit": 50}
        )
        
        assert audit_response.status_code == 200
        audit_data = audit_response.json()
        assert len(audit_data["items"]) > 0
        
        # Step 3: Check config-specific audit logs
        config_audit_response = client.get(
            "/api/v1/config/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"limit": 50}
        )
        
        assert config_audit_response.status_code == 200
        config_audit_data = config_audit_response.json()
        assert len(config_audit_data["items"]) > 0
        
        # Verify audit log structure
        for log_item in config_audit_data["items"]:
            assert "timestamp" in log_item
            assert "agent" in log_item
            assert "action" in log_item
            assert "user" in log_item
            assert log_item["user"] == "admin"
    
    def test_error_handling_and_recovery(self, client, admin_token):
        """Test error handling and recovery scenarios."""
        # Step 1: Test invalid agent execution
        invalid_agent_response = client.post(
            "/api/v1/agents/run",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "agent_name": "nonexistent_agent",
                "context": {
                    "entity": {"id": "test", "entity_type": "host"},
                    "signals": []
                }
            }
        )
        
        assert invalid_agent_response.status_code == 404
        
        # Step 2: Test invalid configuration update
        invalid_config_response = client.post(
            "/api/v1/config/update",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "config_key": "nonexistent.key",
                "value": "test"
            }
        )
        
        assert invalid_config_response.status_code == 404
        
        # Step 3: Verify system is still functional
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"
        
        # Step 4: Verify valid operations still work
        valid_agent_response = client.post(
            "/api/v1/agents/run",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "agent_name": "context_summarizer",
                "context": {
                    "entity": {"id": "test", "entity_type": "host"},
                    "signals": []
                }
            }
        )
        
        assert valid_agent_response.status_code == 200
    
    def test_performance_and_limits(self, client, admin_token):
        """Test performance limits and boundaries."""
        # Test batch size limits
        large_batch = [
            {
                "entity": {"id": f"host-{i:03d}", "entity_type": "host"},
                "signals": []
            }
            for i in range(101)  # Over the limit
        ]
        
        batch_limit_response = client.post(
            "/api/v1/score/batch",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"contexts": large_batch, "engines": ["risk"]}
        )
        
        assert batch_limit_response.status_code == 400
        assert "Maximum 100 entities allowed" in batch_limit_response.json()["detail"]
        
        # Test aggregate limits
        many_entity_ids = [f"host-{i:04d}" for i in range(1001)]  # Over limit
        
        aggregate_limit_response = client.post(
            "/api/v1/score/aggregate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"entity_ids": many_entity_ids, "engines": ["risk"]}
        )
        
        assert aggregate_limit_response.status_code == 400
        assert "Maximum 1000 entity IDs allowed" in aggregate_limit_response.json()["detail"]
        
        # Test timeout handling
        timeout_response = client.post(
            "/api/v1/agents/run",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "agent_name": "context_summarizer",
                "context": {
                    "entity": {"id": "test", "entity_type": "host"},
                    "signals": []
                },
                "timeout_seconds": 0.001  # Very short timeout
            }
        )
        
        # Should either succeed quickly or timeout, but not crash
        assert timeout_response.status_code in [200, 408, 500]


class TestCrossServiceIntegration:
    """Test integration between different API services."""
    
    def test_auth_to_config_to_agents_flow(self, client):
        """Test authentication -> configuration -> agents flow."""
        # Step 1: Login and get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Step 2: Use token to access configuration
        config_response = client.get(
            "/api/v1/config",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert config_response.status_code == 200
        
        # Step 3: Use same token to run agents
        agent_response = client.post(
            "/api/v1/agents/list",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert agent_response.status_code == 200
        
        # Step 4: Verify token info
        verify_response = client.get(
            "/api/v1/auth/verify",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert verify_response.status_code == 200
        assert verify_response.json()["valid"] is True
    
    def test_scoring_to_agents_pipeline(self, client, admin_token, sample_context):
        """Test scoring results feeding into agent pipeline."""
        # Step 1: Get scoring results
        score_response = client.post(
            "/api/v1/score",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"context": sample_context, "engines": ["risk"]}
        )
        
        assert score_response.status_code == 200
        score_data = score_response.json()
        scoring_result = score_data[0]
        
        # Step 2: Use scoring results in explainability agent
        explain_response = client.post(
            "/api/v1/agents/run",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "agent_name": "explainability",
                "context": sample_context,
                "scoring_result": {
                    "score": scoring_result["score"],
                    "severity": scoring_result["severity"],
                    "factors": scoring_result["factors"]
                }
            }
        )
        
        assert explain_response.status_code == 200
        explain_data = explain_response.json()
        
        # Step 3: Verify explanation includes scoring context
        assert explain_data["success"] is True
        assert "output" in explain_data
    
    def test_configuration_affects_all_services(self, client, admin_token):
        """Test configuration changes affecting multiple services."""
        # Step 1: Update a global configuration
        config_response = client.post(
            "/api/v1/config/update",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "config_key": "logging.level",
                "value": "DEBUG"
            }
        )
        
        assert config_response.status_code == 200
        
        # Step 2: Verify configuration is reflected
        get_config_response = client.get(
            "/api/v1/config/logging.level",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert get_config_response.status_code == 200
        assert get_config_response.json()["value"] == "DEBUG"
        
        # Step 3: Verify service health reflects changes
        health_response = client.get(
            "/api/v1/config/health",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] in ["healthy", "degraded"]


class TestSecurityIntegration:
    """Test security integration across the API."""
    
    def test_permission_enforcement_across_services(self, client, analyst_token, sample_context):
        """Test permission enforcement across all services."""
        # Test analyst permissions on different endpoints
        
        # Should work: Read operations
        read_endpoints = [
            ("/api/v1/config", "GET"),
            ("/api/v1/config/rules", "GET"),
            ("/api/v1/score/engines", "GET"),
            ("/api/v1/agents/list", "GET"),
            ("/api/v1/agents/pipelines", "GET"),
            ("/api/v1/agents/health", "GET"),
        ]
        
        for endpoint, method in read_endpoints:
            if method == "GET":
                response = client.get(endpoint, headers={"Authorization": f"Bearer {analyst_token}"})
            else:
                response = client.post(endpoint, headers={"Authorization": f"Bearer {analyst_token}"})
            
            assert response.status_code == 200, f"Should allow {method} {endpoint} for analyst"
        
        # Should fail: Write operations on config
        write_endpoints = [
            ("/api/v1/config/update", "POST", {"config_key": "test", "value": "test"}),
            ("/api/v1/config/rules", "POST", {
                "rule_id": "test", "rule_type": "risk", "name": "test",
                "condition": {"entity_type": "host"}, "action": {"risk_multiplier": 1.0}
            }),
            ("/api/v1/agents/create-pipeline", "POST", {
                "pipeline_name": "test", "agents": ["context_summarizer"]
            }),
        ]
        
        for endpoint, method, data in write_endpoints:
            response = client.post(endpoint, headers={"Authorization": f"Bearer {analyst_token}"}, json=data)
            assert response.status_code == 403, f"Should deny {method} {endpoint} for analyst"
    
    def test_token_validation_consistency(self, client, admin_token):
        """Test token validation is consistent across services."""
        # Use the same token across different services
        endpoints = [
            "/api/v1/config",
            "/api/v1/score/engines",
            "/api/v1/agents/list",
            "/api/v1/config/health",
            "/api/v1/agents/health",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers={"Authorization": f"Bearer {admin_token}"})
            assert response.status_code == 200, f"Token should work for {endpoint}"
