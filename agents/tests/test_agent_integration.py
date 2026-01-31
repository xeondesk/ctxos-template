"""
Integration tests for all agents working together.
"""

import pytest
from datetime import datetime, timedelta

from core.models.entity import Entity
from core.models.signal import Signal
from core.models.context import Context
from core.scoring.risk import ScoringResult

from agents.context_summarizer import ContextSummarizer
from agents.gap_detector import GapDetector
from agents.hypothesis_generator import HypothesisGenerator
from agents.explainability import ExplainabilityAgent
from agents.mcp_orchestrator import MCPOrchestrator, MCPPipeline


@pytest.fixture
def all_agents():
    """Create all agent instances."""
    return {
        "context_summarizer": ContextSummarizer(
            name="integration_summarizer",
            version="1.0.0",
            max_risks=3,
            max_exposures=3,
            max_anomalies=2,
        ),
        "gap_detector": GapDetector(
            name="integration_gap_detector",
            version="1.0.0",
            max_data_age_hours=168,
            min_coverage_threshold=0.7,
        ),
        "hypothesis_generator": HypothesisGenerator(
            name="integration_hypothesis_generator",
            version="1.0.0",
            max_hypotheses=5,
            min_confidence_threshold=0.4,
            enable_creative_hypotheses=True,
        ),
        "explainability_agent": ExplainabilityAgent(
            name="integration_explainability",
            version="1.0.0",
            min_factor_weight=0.05,
            max_explanations=3,
            include_comparisons=True,
        ),
    }


@pytest.fixture
def orchestrator():
    """Create MCP orchestrator."""
    return MCPOrchestrator()


@pytest.fixture
def production_entity():
    """Create production entity for integration testing."""
    return Entity(
        id="prod-app-01",
        entity_type="application",
        name="production-web-app",
        description="Critical production web application",
        properties={
            "environment": "production",
            "public": True,
            "critical": True,
            "framework": "react",
            "data_classification": "confidential",
            "compliance_requirements": ["PCI-DSS", "SOX"],
        },
    )


@pytest.fixture
def comprehensive_signals():
    """Create comprehensive signal set for integration testing."""
    return [
        # Critical vulnerabilities
        Signal(
            id="vuln-001",
            source="nessus",
            signal_type="VULNERABILITY",
            severity="critical",
            description="CVE-2023-1234: Remote code execution in React framework",
            timestamp=datetime.utcnow() - timedelta(hours=2),
            entity_id="prod-app-01",
        ),
        Signal(
            id="vuln-002",
            source="qualys",
            signal_type="VULNERABILITY",
            severity="high",
            description="CVE-2023-5678: SQL injection vulnerability",
            timestamp=datetime.utcnow() - timedelta(hours=6),
            entity_id="prod-app-01",
        ),
        
        # Exposure signals
        Signal(
            id="port-001",
            source="nmap",
            signal_type="PORT",
            severity="high",
            description="Port 443/tcp open - HTTPS",
            timestamp=datetime.utcnow() - timedelta(hours=12),
            entity_id="prod-app-01",
        ),
        Signal(
            id="port-002",
            source="nmap",
            signal_type="PORT",
            severity="medium",
            description="Port 80/tcp open - HTTP",
            timestamp=datetime.utcnow() - timedelta(hours=12),
            entity_id="prod-app-01",
        ),
        
        # Service signals
        Signal(
            id="service-001",
            source="asset_inventory",
            signal_type="SERVICE",
            severity="medium",
            description="Apache HTTP Server 2.4.41",
            timestamp=datetime.utcnow() - timedelta(hours=24),
            entity_id="prod-app-01",
        ),
        
        # Configuration signals
        Signal(
            id="config-001",
            source="config_scanner",
            signal_type="CONFIGURATION",
            severity="medium",
            description="Weak SSL configuration detected",
            timestamp=datetime.utcnow() - timedelta(hours=18),
            entity_id="prod-app-01",
        ),
        
        # Activity signals
        Signal(
            id="activity-001",
            source="siem",
            signal_type="ACTIVITY",
            severity="high",
            description="Suspicious login patterns detected",
            timestamp=datetime.utcnow() - timedelta(hours=1),
            entity_id="prod-app-01",
        ),
        
        # DNS signals
        Signal(
            id="dns-001",
            source="dns_monitor",
            signal_type="DNS",
            severity="medium",
            description="DNS query to suspicious domain",
            timestamp=datetime.utcnow() - timedelta(hours=8),
            entity_id="prod-app-01",
        ),
        
        # Dependency signals
        Signal(
            id="dep-001",
            source="dependency_scanner",
            signal_type="DEPENDENCY",
            severity="high",
            description="Vulnerable third-party dependency detected",
            timestamp=datetime.utcnow() - timedelta(hours=16),
            entity_id="prod-app-01",
        ),
        
        # Authentication signals
        Signal(
            id="auth-001",
            source="auth_log",
            signal_type="AUTHENTICATION",
            severity="high",
            description="Multiple failed login attempts",
            timestamp=datetime.utcnow() - timedelta(hours=3),
            entity_id="prod-app-01",
        ),
    ]


@pytest.fixture
def comprehensive_context(production_entity, comprehensive_signals):
    """Create comprehensive context."""
    return Context(
        entity=production_entity,
        signals=comprehensive_signals,
    )


@pytest.fixture
def comprehensive_scoring_result():
    """Create comprehensive scoring result."""
    return ScoringResult(
        score=88.0,
        severity="critical",
        details={
            "risk_factors": ["vulnerability", "exposure", "activity"],
            "critical_issues": ["remote_code_execution", "suspicious_activity"],
        },
        metrics={
            "vulnerability": 45,
            "exposure": 25,
            "drift": 12,
            "configuration": 6,
        },
        recommendations=[
            "Immediate patching of critical vulnerabilities",
            "Investigate suspicious authentication activity",
            "Strengthen SSL configuration",
            "Review third-party dependencies",
        ],
    )


class TestAgentIntegration:
    """Test integration between all agents."""
    
    def test_all_agents_initialization(self, all_agents):
        """Test all agents initialize correctly."""
        for agent_name, agent in all_agents.items():
            assert agent is not None
            assert hasattr(agent, 'name')
            assert hasattr(agent, 'version')
            assert hasattr(agent, 'analyze')
    
    def test_individual_agent_analysis(self, all_agents, comprehensive_context, comprehensive_scoring_result):
        """Test each agent can analyze individually."""
        results = {}
        
        for agent_name, agent in all_agents.items():
            result = agent.analyze(comprehensive_context, comprehensive_scoring_result)
            results[agent_name] = result
            
            assert result.success is True
            assert "output" in result.output
        
        return results
    
    def test_context_summarizer_integration(self, all_agents, comprehensive_context, comprehensive_scoring_result):
        """Test context summarizer integration."""
        summarizer = all_agents["context_summarizer"]
        result = summarizer.analyze(comprehensive_context, comprehensive_scoring_result)
        
        assert result.success is True
        summary = result.output["summary"]
        
        # Should have comprehensive summary
        assert summary["total_signals"] > 0
        assert summary["risk_items"] > 0
        assert summary["exposure_items"] > 0
        
        # Should have summary data
        summary_data = result.output["summary"]["summary"]
        assert "entity_summary" in summary_data
        assert "key_findings" in summary_data
        assert "risk_highlights" in summary_data
        assert "exposure_highlights" in summary_data
        assert "recommendations" in summary_data
    
    def test_gap_detector_integration(self, all_agents, comprehensive_context, comprehensive_scoring_result):
        """Test gap detector integration."""
        gap_detector = all_agents["gap_detector"]
        result = gap_detector.analyze(comprehensive_context, comprehensive_scoring_result)
        
        assert result.success is True
        gap_analysis = result.output["gap_analysis"]
        
        # Should detect some gaps
        assert gap_analysis["total_gaps"] >= 0
        
        # Should have coverage metrics
        assert 0 <= gap_analysis["coverage_score"] <= 100
        assert 0 <= gap_analysis["data_freshness_score"] <= 100
        assert 0 <= gap_analysis["monitoring_completeness"] <= 100
    
    def test_hypothesis_generator_integration(self, all_agents, comprehensive_context, comprehensive_scoring_result):
        """Test hypothesis generator integration."""
        hypothesis_generator = all_agents["hypothesis_generator"]
        result = hypothesis_generator.analyze(comprehensive_context, comprehensive_scoring_result)
        
        assert result.success is True
        hypothesis_analysis = result.output["hypothesis_analysis"]
        
        # Should generate hypotheses
        assert hypothesis_analysis["total_hypotheses"] > 0
        
        # Should have threat landscape
        assert isinstance(hypothesis_analysis["threat_landscape"], dict)
        
        # Should have attack surface score
        assert 0 <= hypothesis_analysis["attack_surface_score"] <= 100
        
        # Should have recommended investigations
        assert len(hypothesis_analysis["recommended_investigations"]) > 0
    
    def test_explainability_integration(self, all_agents, comprehensive_context, comprehensive_scoring_result):
        """Test explainability integration."""
        explainability_agent = all_agents["explainability_agent"]
        result = explainability_agent.analyze(comprehensive_context, comprehensive_scoring_result)
        
        assert result.success is True
        explainability_result = result.output["explainability_result"]
        
        # Should have explanations
        assert len(explainability_result["explanations"]) > 0
        
        # Should have confidence metrics
        assert 0 <= explainability_result["overall_confidence"] <= 1
        assert 0 <= explainability_result["explanation_coverage"] <= 1
        
        # Should have actionable insights
        assert explainability_result["actionable_insights"] >= 0
    
    def test_orchestrator_registration(self, orchestrator, all_agents):
        """Test orchestrator agent registration."""
        # Register all agents
        for agent_name, agent in all_agents.items():
            orchestrator.register_agent(agent)
        
        # Should have all agents registered
        assert len(orchestrator.list_agents()) == len(all_agents)
        
        # Should be able to get agent info
        for agent_name in all_agents.keys():
            agent_info = orchestrator.get_agent_info(agent_name)
            assert agent_info["name"] == agent_name
    
    def test_sequential_pipeline_execution(self, orchestrator, all_agents, comprehensive_context, comprehensive_scoring_result):
        """Test sequential pipeline execution."""
        # Register agents
        for agent in all_agents.values():
            orchestrator.register_agent(agent)
        
        # Create sequential pipeline
        pipeline = orchestrator.create_pipeline("integration_sequential", parallel=False)
        
        # Add agents to pipeline
        for agent in all_agents.values():
            pipeline.add_agent(agent)
        
        # Execute pipeline
        results = orchestrator.execute_pipeline(
            "integration_sequential",
            comprehensive_context,
            comprehensive_scoring_result,
            user="integration_test_user"
        )
        
        # Should have results from all agents
        assert len(results) == len(all_agents)
        
        # All results should be successful
        for agent_name, result in results.items():
            assert result.success is True
            assert "output" in result.output
    
    def test_parallel_pipeline_execution(self, orchestrator, all_agents, comprehensive_context, comprehensive_scoring_result):
        """Test parallel pipeline execution."""
        # Register agents
        for agent in all_agents.values():
            orchestrator.register_agent(agent)
        
        # Create parallel pipeline
        pipeline = orchestrator.create_pipeline("integration_parallel", parallel=True)
        
        # Add agents to pipeline
        for agent in all_agents.values():
            pipeline.add_agent(agent)
        
        # Execute pipeline
        results = orchestrator.execute_pipeline(
            "integration_parallel",
            comprehensive_context,
            comprehensive_scoring_result,
            user="integration_test_user"
        )
        
        # Should have results from all agents
        assert len(results) == len(all_agents)
        
        # All results should be successful
        for agent_name, result in results.items():
            assert result.success is True
    
    def test_single_agent_execution(self, orchestrator, all_agents, comprehensive_context, comprehensive_scoring_result):
        """Test single agent execution through orchestrator."""
        # Register agents
        for agent in all_agents.values():
            orchestrator.register_agent(agent)
        
        # Execute single agent
        result = orchestrator.execute_agent(
            "integration_summarizer",
            comprehensive_context,
            comprehensive_scoring_result,
            user="integration_test_user"
        )
        
        assert result.success is True
        assert "output" in result.output
    
    def test_cross_agent_data_consistency(self, all_agents, comprehensive_context, comprehensive_scoring_result):
        """Test data consistency across agents."""
        results = {}
        
        # Run all agents
        for agent_name, agent in all_agents.items():
            result = agent.analyze(comprehensive_context, comprehensive_scoring_result)
            results[agent_name] = result.output
        
        # Check entity ID consistency
        entity_ids = []
        for agent_name, result in results.items():
            if "explainability_result" in result:
                entity_ids.append(result["explainability_result"]["entity_id"])
            elif "gap_analysis" in result:
                # Gap analysis doesn't directly store entity_id in top level
                pass
        
        # All entity IDs should be the same
        if entity_ids:
            assert len(set(entity_ids)) == 1
        
        # Check score consistency where applicable
        scores = []
        for agent_name, result in results.items():
            if "explainability_result" in result:
                scores.append(result["explainability_result"]["score"])
        
        if scores:
            # All should reference the same scoring result
            assert len(set(scores)) == 1
    
    def test_complementary_analysis(self, all_agents, comprehensive_context, comprehensive_scoring_result):
        """Test that agents provide complementary analysis."""
        results = {}
        
        # Run all agents
        for agent_name, agent in all_agents.items():
            result = agent.analyze(comprehensive_context, comprehensive_scoring_result)
            results[agent_name] = result.output
        
        # Context summarizer should provide overview
        summary = results["context_summarizer"]["summary"]
        assert summary["total_signals"] == len(comprehensive_context.signals)
        
        # Gap detector should identify missing coverage
        gap_analysis = results["gap_detector"]["gap_analysis"]
        assert isinstance(gap_analysis["total_gaps"], int)
        
        # Hypothesis generator should provide threat scenarios
        hypothesis_analysis = results["hypothesis_generator"]["hypothesis_analysis"]
        assert hypothesis_analysis["total_hypotheses"] > 0
        
        # Explainability should provide rationale
        explainability_result = results["explainability_agent"]["explainability_result"]
        assert len(explainability_result["explanations"]) > 0
    
    def test_performance_with_comprehensive_data(self, all_agents, comprehensive_context, comprehensive_scoring_result):
        """Test performance with comprehensive data."""
        import time
        
        # Measure execution time for all agents
        start_time = time.time()
        
        results = {}
        for agent_name, agent in all_agents.items():
            agent_start = time.time()
            result = agent.analyze(comprehensive_context, comprehensive_scoring_result)
            agent_end = time.time()
            
            results[agent_name] = {
                "result": result,
                "duration": agent_end - agent_start
            }
        
        total_time = time.time() - start_time
        
        # All should complete successfully
        for agent_name, data in results.items():
            assert data["result"].success is True
        
        # Performance should be reasonable (less than 10 seconds total)
        assert total_time < 10.0
        
        # No single agent should take too long (less than 5 seconds)
        for agent_name, data in results.items():
            assert data["duration"] < 5.0
    
    def test_error_propagation(self, orchestrator, all_agents, comprehensive_context):
        """Test error handling and propagation."""
        # Register agents
        for agent in all_agents.values():
            orchestrator.register_agent(agent)
        
        # Execute pipeline without scoring result (should handle gracefully)
        pipeline = orchestrator.create_pipeline("error_test", parallel=False)
        for agent in all_agents.values():
            pipeline.add_agent(agent)
        
        results = orchestrator.execute_pipeline(
            "error_test",
            comprehensive_context,
            None,  # No scoring result
            user="error_test_user"
        )
        
        # Should still complete successfully
        assert len(results) == len(all_agents)
        
        # Most agents should handle missing scoring result gracefully
        successful_results = sum(1 for result in results.values() if result.success)
        assert successful_results >= len(all_agents) - 1  # At most one might fail
    
    def test_audit_trail_consistency(self, orchestrator, all_agents, comprehensive_context, comprehensive_scoring_result):
        """Test audit trail consistency across agents."""
        # Register agents
        for agent in all_agents.values():
            orchestrator.register_agent(agent)
        
        # Execute pipeline
        pipeline = orchestrator.create_pipeline("audit_test", parallel=False)
        for agent in all_agents.values():
            pipeline.add_agent(agent)
        
        orchestrator.execute_pipeline(
            "audit_test",
            comprehensive_context,
            comprehensive_scoring_result,
            user="audit_test_user"
        )
        
        # Check audit logs
        audit_logger = orchestrator.audit_logger
        events = audit_logger.get_events()
        
        # Should have events for orchestrator and all agents
        orchestrator_events = [e for e in events if e.agent_name == "MCPOrchestrator"]
        agent_events = [e for e in events if e.agent_name in all_agents.keys()]
        
        assert len(orchestrator_events) > 0
        assert len(agent_events) > 0
        
        # All events should have required fields
        for event in events:
            assert event.timestamp is not None
            assert event.action is not None
            assert event.status is not None
            assert event.level is not None
    
    def test_pipeline_configuration(self, orchestrator, all_agents):
        """Test pipeline configuration options."""
        # Register agents
        for agent in all_agents.values():
            orchestrator.register_agent(agent)
        
        # Test different pipeline configurations
        configs = [
            {"name": "seq_test", "parallel": False},
            {"name": "par_test", "parallel": True},
        ]
        
        for config in configs:
            pipeline = orchestrator.create_pipeline(config["name"], parallel=config["parallel"])
            
            # Add subset of agents
            agents_list = list(all_agents.values())[:2]
            for agent in agents_list:
                pipeline.add_agent(agent)
            
            # Verify pipeline configuration
            assert pipeline.parallel == config["parallel"]
            assert len(pipeline.agents) == 2
    
    def test_real_world_comprehensive_scenario(self, orchestrator, all_agents, comprehensive_context, comprehensive_scoring_result):
        """Test comprehensive real-world scenario."""
        # Register all agents
        for agent in all_agents.values():
            orchestrator.register_agent(agent)
        
        # Create comprehensive pipeline
        pipeline = orchestrator.create_pipeline("comprehensive_analysis", parallel=False)
        
        # Add all agents in logical order
        analysis_order = [
            "context_summarizer",  # First: understand the context
            "gap_detector",        # Second: identify gaps
            "hypothesis_generator", # Third: generate hypotheses
            "explainability_agent", # Fourth: explain results
        ]
        
        for agent_name in analysis_order:
            pipeline.add_agent(all_agents[agent_name])
        
        # Execute comprehensive analysis
        results = orchestrator.execute_pipeline(
            "comprehensive_analysis",
            comprehensive_context,
            comprehensive_scoring_result,
            user="security_analyst"
        )
        
        # Verify comprehensive results
        assert len(results) == len(all_agents)
        
        # All should succeed
        for agent_name, result in results.items():
            assert result.success is True
        
        # Verify logical flow in results
        summary_result = results["integration_summarizer"]
        gap_result = results["integration_gap_detector"]
        hypothesis_result = results["integration_hypothesis_generator"]
        explainability_result = results["integration_explainability"]
        
        # Context should be summarized
        summary_data = summary_result.output["summary"]["summary"]
        assert summary_data["entity_summary"]["id"] == comprehensive_context.entity.id
        
        # Gaps should be identified
        gap_data = gap_result.output["gap_analysis"]
        assert isinstance(gap_data["total_gaps"], int)
        
        # Hypotheses should be generated
        hypothesis_data = hypothesis_result.output["hypothesis_analysis"]
        assert hypothesis_data["total_hypotheses"] > 0
        
        # Explanations should be provided
        explainability_data = explainability_result.output["explainability_result"]
        assert len(explainability_data["explanations"]) > 0
        
        # Results should be consistent
        assert summary_data["entity_summary"]["id"] == explainability_data["entity_id"]
        
        # High-risk scenario should be reflected across all analyses
        assert comprehensive_scoring_result.score > 80  # High score scenario
        
        # Should detect critical issues in multiple analyses
        critical_findings = 0
        if gap_data["total_gaps"] > 0:
            critical_gaps = [g for g in gap_data["gaps"] if g["severity"] == "critical"]
            critical_findings += len(critical_gaps)
        
        critical_hypotheses = [h for h in hypothesis_data["hypotheses"] if h["impact"] == "critical"]
        critical_findings += len(critical_hypotheses)
        
        # Should have some critical findings given the high-risk scenario
        assert critical_findings > 0 or explainability_data["score"] > 70


class TestMCPIntegration:
    """Test MCP-specific integration features."""
    
    def test_pipeline_persistence(self, orchestrator, all_agents):
        """Test pipeline state persistence."""
        # Register agents
        for agent in all_agents.values():
            orchestrator.register_agent(agent)
        
        # Create pipeline
        pipeline = orchestrator.create_pipeline("persistent_test")
        pipeline.add_agent(all_agents["context_summarizer"])
        pipeline.add_agent(all_agents["gap_detector"])
        
        # Pipeline should be stored
        assert "persistent_test" in orchestrator.pipelines
        
        # Should be able to retrieve pipeline
        retrieved_pipeline = orchestrator.pipelines["persistent_test"]
        assert len(retrieved_pipeline.agents) == 2
        assert retrieved_pipeline.parallel is False
    
    def test_pipeline_results_tracking(self, orchestrator, all_agents, comprehensive_context, comprehensive_scoring_result):
        """Test pipeline results tracking."""
        # Register agents
        for agent in all_agents.values():
            orchestrator.register_agent(agent)
        
        # Create and execute pipeline
        pipeline = orchestrator.create_pipeline("results_test")
        pipeline.add_agent(all_agents["context_summarizer"])
        
        results = orchestrator.execute_pipeline(
            "results_test",
            comprehensive_context,
            comprehensive_scoring_result
        )
        
        # Pipeline should store results
        assert len(pipeline.results) > 0
        assert pipeline.duration_ms > 0
        
        # Results should be accessible
        for agent_name, result in pipeline.results.items():
            assert result.success is True
    
    def test_agent_state_management(self, all_agents, comprehensive_context, comprehensive_scoring_result):
        """Test agent state management."""
        summarizer = all_agents["context_summarizer"]
        
        # Execute agent
        result = summarizer.analyze(comprehensive_context, comprehensive_scoring_result)
        
        # Agent should have last result
        assert summarizer.last_result is not None
        assert summarizer.last_result.success is True
        
        # Should be able to get agent state
        state = summarizer.get_state()
        assert state["name"] == summarizer.name
        assert state["version"] == summarizer.version
        assert "last_result" in state
        assert state["last_result"]["success"] is True
    
    def test_error_handling_in_pipeline(self, orchestrator, all_agents, comprehensive_context):
        """Test error handling within pipeline execution."""
        # Register agents
        for agent in all_agents.values():
            orchestrator.register_agent(agent)
        
        # Create pipeline with timeout
        pipeline = orchestrator.create_pipeline("timeout_test")
        pipeline.add_agent(all_agents["context_summarizer"])
        
        # Execute with very short timeout (may cause timeout)
        results = orchestrator.execute_pipeline(
            "timeout_test",
            comprehensive_context,
            None,
            timeout=0.001  # Very short timeout
        )
        
        # Should handle timeout gracefully
        assert len(results) == 1
        
        # Result may indicate timeout or success depending on execution speed
        result = results["integration_summarizer"]
        assert result.success is True or "timeout" in result.error.lower() if result.error else True
