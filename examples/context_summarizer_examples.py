"""
Context Summarizer Agent - Integration Examples

This module demonstrates how to use the Context Summarizer agent
in various scenarios.
"""

import asyncio
from datetime import datetime
import json

from core.models.entity import Entity
from core.models.signal import Signal
from core.models.context import Context
from core.scoring.risk import ScoringResult
from agents.agents.context_summarizer import ContextSummarizer
from agents.mcp_orchestrator import get_orchestrator
from agents.audit_system.audit_logger import get_audit_logger


# ===========================================================================
# Example 1: Basic Usage
# ===========================================================================

async def example_basic_usage():
    """Example: Basic context summarization."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Context Summarization")
    print("="*70)

    # Create entity
    entity = Entity(
        id="web-server-01",
        entity_type="host",
        name="production-web-server",
        description="Main web server"
    )

    # Create signals
    signals = [
        Signal(
            id="sig-001",
            source="vulnerability_scanner",
            signal_type="VULNERABILITY",
            severity="CRITICAL",
            description="CVE-2024-1234: Critical RCE vulnerability",
            timestamp=datetime.utcnow()
        ),
        Signal(
            id="sig-002",
            source="port_scanner",
            signal_type="OPEN_PORT",
            severity="HIGH",
            description="Port 22 (SSH) open to public",
            timestamp=datetime.utcnow()
        ),
        Signal(
            id="sig-003",
            source="certificate_monitor",
            signal_type="CERTIFICATE",
            severity="MEDIUM",
            description="SSL certificate expires in 30 days",
            timestamp=datetime.utcnow()
        ),
        Signal(
            id="sig-004",
            source="config_monitor",
            signal_type="CONFIGURATION",
            severity="LOW",
            description="SELinux disabled",
            timestamp=datetime.utcnow()
        ),
    ]

    # Create context
    context = Context(name="web-server-assessment")
    context.entity = entity
    context.signals = signals

    # Run summarizer
    summarizer = ContextSummarizer()
    result = await summarizer.run(context, user="security-analyst")

    # Display results
    if result.success:
        summary = result.output
        print(f"\n✓ Analysis complete ({result.duration_ms:.1f}ms)")
        print(f"\nEntity: {summary['entity_name']} ({summary['entity_type']})")
        print(f"\nAssessment Priority: {summary['overall_assessment']['priority']}")
        print(f"Critical Findings: {summary['overall_assessment']['critical_findings']}")
        print(f"Total Findings: {summary['overall_assessment']['total_findings']}")
        print(f"Recommendation: {summary['overall_assessment']['recommendation']}")
        print(f"\nTop Risks ({len(summary['top_risks'])}): ")
        for i, risk in enumerate(summary['top_risks'][:3], 1):
            print(f"  {i}. [{risk['severity']}] {risk['description']}")
    else:
        print(f"✗ Analysis failed: {result.error}")


# ===========================================================================
# Example 2: Integration with Scoring Results
# ===========================================================================

async def example_with_scoring_results():
    """Example: Summarize with scoring results from engines."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Integration with Scoring Results")
    print("="*70)

    # Create entity
    entity = Entity(
        id="api-server-01",
        entity_type="host",
        name="api-server"
    )

    # Create signals
    signals = [
        Signal(
            source="vulnerability_scanner",
            signal_type="VULNERABILITY",
            severity="HIGH",
            description="Outdated dependencies",
            timestamp=datetime.utcnow()
        ),
        Signal(
            source="port_scanner",
            signal_type="OPEN_PORT",
            severity="MEDIUM",
            description="Port 8080 (API) publicly accessible",
            timestamp=datetime.utcnow()
        ),
    ]

    # Create scoring results
    risk_score = ScoringResult(
        score=72.5,
        severity="HIGH",
        engine_name="risk",
        factors={
            "vulnerabilities": 0.6,
            "open_ports": 0.3,
            "credentials": 0.0
        },
        metrics={"critical_count": 0, "high_count": 2},
        recommendations=["Update dependencies", "Close unnecessary ports"],
        timestamp=datetime.utcnow()
    )

    exposure_score = ScoringResult(
        score=65.0,
        severity="HIGH",
        engine_name="exposure",
        factors={
            "public_access": 1.0,
            "services": 0.4
        },
        metrics={"open_ports": 1},
        recommendations=["Implement WAF", "Use API gateway"],
        timestamp=datetime.utcnow()
    )

    # Create context
    context = Context(name="api-assessment")
    context.entity = entity
    context.signals = signals

    # Summarize with risk score
    summarizer = ContextSummarizer()
    result_risk = await summarizer.analyze(context, risk_score)

    # Summarize with exposure score
    result_exposure = await summarizer.analyze(context, exposure_score)

    print("\n✓ Multi-score analysis complete")
    print(f"  Risk Summary Priority: {result_risk.output['overall_assessment']['priority']}")
    print(f"  Exposure Summary Priority: {result_exposure.output['overall_assessment']['priority']}")
    
    # Show factors considered
    print(f"\nRisk Factors:")
    for factor, value in risk_score.factors.items():
        print(f"  {factor}: {value:.1%}")
    print(f"\nRisk Recommendations: {', '.join(risk_score.recommendations)}")


# ===========================================================================
# Example 3: Integration with MCP Orchestrator
# ===========================================================================

async def example_mcp_orchestrator():
    """Example: Use agent via orchestrator."""
    print("\n" + "="*70)
    print("EXAMPLE 3: MCP Orchestrator Integration")
    print("="*70)

    # Create entity and signals
    entity = Entity(
        id="database-01",
        entity_type="host",
        name="production-db"
    )

    signals = [
        Signal(
            source="db_scanner",
            signal_type="VULNERABILITY",
            severity="CRITICAL",
            description="Unpatched SQL injection vulnerability",
            timestamp=datetime.utcnow()
        ),
        Signal(
            source="access_monitor",
            signal_type="OPEN_PORT",
            severity="HIGH",
            description="Database port 5432 publicly accessible",
            timestamp=datetime.utcnow()
        ),
    ]

    # Create context
    context = Context(name="db-assessment")
    context.entity = entity
    context.signals = signals

    # Get orchestrator and register agent
    orchestrator = get_orchestrator()
    summarizer = ContextSummarizer()
    orchestrator.register_agent(summarizer)

    # Execute via orchestrator
    result = await orchestrator.execute_agent(
        agent_name="context_summarizer",
        context=context,
        user="database-security-team"
    )

    print(f"\n✓ Orchestrator execution complete")
    print(f"  Priority: {result.output['overall_assessment']['priority']}")
    print(f"  Duration: {result.duration_ms:.1f}ms")

    # Show audit log
    audit_logger = get_audit_logger()
    events = audit_logger.get_events(agent_name="context_summarizer", limit=5)
    print(f"\nAudit Log ({len(events)} events):")
    for event in events[-3:]:
        print(f"  {event.timestamp.isoformat()} | {event.action} | {event.status}")


# ===========================================================================
# Example 4: Batch Analysis
# ===========================================================================

async def example_batch_analysis():
    """Example: Analyze multiple entities concurrently."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Batch Concurrent Analysis")
    print("="*70)

    # Create multiple entities with signals
    entities_data = [
        {
            "id": "web-01",
            "name": "web-server-1",
            "signals": [
                Signal(
                    source="scanner",
                    signal_type="VULNERABILITY",
                    severity="HIGH",
                    description="Web framework RCE",
                    timestamp=datetime.utcnow()
                )
            ]
        },
        {
            "id": "api-01",
            "name": "api-server-1",
            "signals": [
                Signal(
                    source="scanner",
                    signal_type="OPEN_PORT",
                    severity="MEDIUM",
                    description="Debug port exposed",
                    timestamp=datetime.utcnow()
                )
            ]
        },
        {
            "id": "db-01",
            "name": "database-1",
            "signals": [
                Signal(
                    source="scanner",
                    signal_type="CERTIFICATE",
                    severity="LOW",
                    description="Certificate expires soon",
                    timestamp=datetime.utcnow()
                )
            ]
        },
    ]

    # Prepare analysis tasks
    summarizer = ContextSummarizer()
    tasks = []

    for entity_data in entities_data:
        entity = Entity(
            id=entity_data["id"],
            entity_type="host",
            name=entity_data["name"]
        )
        
        context = Context(name=f"assessment-{entity_data['id']}")
        context.entity = entity
        context.signals = entity_data["signals"]
        
        tasks.append(summarizer.run(context, user="batch-analyzer"))

    # Execute concurrently
    print(f"\nAnalyzing {len(tasks)} entities concurrently...")
    results = await asyncio.gather(*tasks)

    # Summarize results
    print(f"\n✓ Batch analysis complete")
    print(f"Total analyses: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r.success)}")
    print(f"Failed: {sum(1 for r in results if not r.success)}")
    print(f"Average duration: {sum(r.duration_ms for r in results) / len(results):.1f}ms")

    # Show priority breakdown
    priorities = {}
    for result in results:
        if result.success:
            priority = result.output["overall_assessment"]["priority"]
            priorities[priority] = priorities.get(priority, 0) + 1

    print(f"\nPriority Breakdown:")
    for priority in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        count = priorities.get(priority, 0)
        if count > 0:
            print(f"  {priority}: {count}")


# ===========================================================================
# Example 5: Custom Configuration
# ===========================================================================

async def example_custom_configuration():
    """Example: Use custom configuration."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Custom Configuration")
    print("="*70)

    # Create customized summarizer
    summarizer = ContextSummarizer(
        name="custom_summarizer",
        version="1.1.0",
        max_risks=10,        # More risks
        max_exposures=8,     # More exposures
        max_anomalies=5      # More anomalies
    )

    # Create entity with many signals
    entity = Entity(
        id="complex-host",
        entity_type="host",
        name="complex-infrastructure"
    )

    signals = [
        Signal(
            source="scanner",
            signal_type="VULNERABILITY",
            severity="CRITICAL" if i < 3 else "HIGH",
            description=f"Vulnerability {i}",
            timestamp=datetime.utcnow()
        )
        for i in range(15)
    ]

    context = Context(name="complex-assessment")
    context.entity = entity
    context.signals = signals

    # Run with custom settings
    result = await summarizer.run(context, timeout=60.0)

    print(f"\n✓ Custom analysis complete")
    print(f"Agent: {result.agent_name} v{summarizer.version}")
    print(f"Risks included: {len(result.output['top_risks'])} (max: {summarizer.max_risks})")
    print(f"Exposures included: {len(result.output['exposure_highlights'])} (max: {summarizer.max_exposures})")
    print(f"Anomalies included: {len(result.output['configuration_anomalies'])} (max: {summarizer.max_anomalies})")


# ===========================================================================
# Example 6: Error Handling
# ===========================================================================

async def example_error_handling():
    """Example: Handle errors gracefully."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Error Handling")
    print("="*70)

    summarizer = ContextSummarizer()

    # Test 1: Missing entity
    print("\nTest 1: Missing entity")
    context_no_entity = Context(name="no-entity")
    result = await summarizer.analyze(context_no_entity)
    print(f"  Result: {'✓' if not result.success else '✗'} (Expected failure)")
    print(f"  Error: {result.error}")

    # Test 2: Empty signals
    print("\nTest 2: Empty signals")
    entity = Entity(id="test", entity_type="host", name="test")
    context_empty = Context(name="empty")
    context_empty.entity = entity
    context_empty.signals = []
    result = await summarizer.analyze(context_empty)
    print(f"  Result: {'✓' if result.success else '✗'} (Expected success)")
    print(f"  Findings: {result.output['overall_assessment']['total_findings']}")

    # Test 3: Timeout
    print("\nTest 3: Timeout handling")
    context = Context(name="test")
    context.entity = entity
    context.signals = [Signal(source="test", signal_type="VULNERABILITY", 
                             severity="LOW", description="test", 
                             timestamp=datetime.utcnow())]
    result = await summarizer.run(context, timeout=0.001)  # Very short timeout
    print(f"  Result: {'✓' if not result.success else '✗'} (Timeout may occur)")
    if not result.success:
        print(f"  Error type: {type(result.error).__name__}")


# ===========================================================================
# Main: Run All Examples
# ===========================================================================

async def main():
    """Run all examples."""
    try:
        await example_basic_usage()
        await example_with_scoring_results()
        await example_mcp_orchestrator()
        await example_batch_analysis()
        await example_custom_configuration()
        await example_error_handling()

        print("\n" + "="*70)
        print("✓ All examples completed successfully!")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
