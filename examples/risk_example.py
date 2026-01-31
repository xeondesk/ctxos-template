#!/usr/bin/env python3
"""
Risk Engine Example - Demonstrates risk assessment and scoring workflows.

This example shows how to:
1. Create and configure risk engines
2. Assess risk for different entities
3. Calculate risk scores based on various factors
4. Generate risk reports
5. Apply risk mitigation strategies
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.models import Entity, EntityType, EntitySeverity, Signal, SignalType, SignalSeverity, SignalConfidence
from engines.risk.risk_engine import RiskEngine, RiskFactors


class MockRiskEngine(RiskEngine):
    """Mock risk engine for demonstration purposes."""
    
    def __init__(self):
        super().__init__()
        self.risk_factors_db = {}
    
    def assess_entity_risk(self, entity: Entity) -> Dict[str, Any]:
        """Assess risk for a single entity."""
        # Generate mock risk factors based on entity type and properties
        risk_factors = self._generate_risk_factors(entity)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(risk_factors)
        
        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(risk_factors, risk_level)
        
        return {
            'entity_id': entity.id,
            'entity_name': entity.name,
            'entity_type': entity.entity_type.value,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors.__dict__,
            'recommendations': recommendations,
            'assessed_at': datetime.now().isoformat()
        }
    
    def assess_portfolio_risk(self, entities: List[Entity]) -> Dict[str, Any]:
        """Assess risk for a portfolio of entities."""
        individual_assessments = []
        
        for entity in entities:
            assessment = self.assess_entity_risk(entity)
            individual_assessments.append(assessment)
        
        # Calculate portfolio-level metrics
        total_entities = len(entities)
        high_risk_count = len([a for a in individual_assessments if a['risk_level'] == 'HIGH'])
        medium_risk_count = len([a for a in individual_assessments if a['risk_level'] == 'MEDIUM'])
        low_risk_count = len([a for a in individual_assessments if a['risk_level'] == 'LOW'])
        
        avg_risk_score = sum(a['risk_score'] for a in individual_assessments) / total_entities if total_entities > 0 else 0
        
        # Identify top risks
        top_risks = sorted(individual_assessments, key=lambda x: x['risk_score'], reverse=True)[:5]
        
        return {
            'portfolio_summary': {
                'total_entities': total_entities,
                'high_risk_entities': high_risk_count,
                'medium_risk_entities': medium_risk_count,
                'low_risk_entities': low_risk_count,
                'average_risk_score': round(avg_risk_score, 2)
            },
            'top_risks': top_risks,
            'all_assessments': individual_assessments,
            'assessed_at': datetime.now().isoformat()
        }
    
    def _generate_risk_factors(self, entity: Entity) -> RiskFactors:
        """Generate mock risk factors for an entity."""
        # Base risk factors by entity type
        if entity.entity_type == EntityType.DOMAIN:
            return RiskFactors(
                vulnerability_count=random.randint(0, 10),
                open_ports=random.randint(0, 20),
                exposed_credentials=random.randint(0, 5),
                suspicious_activity=random.randint(0, 15),
                data_breach_mentions=random.randint(0, 3),
                malware_indicators=random.randint(0, 2),
                certificate_issues=random.randint(0, 3),
                configuration_issues=random.randint(0, 8),
                age_days=random.randint(30, 3650),
                last_seen_days=random.randint(0, 30)
            )
        elif entity.entity_type == EntityType.IP_ADDRESS:
            return RiskFactors(
                vulnerability_count=random.randint(0, 15),
                open_ports=random.randint(1, 50),
                exposed_credentials=random.randint(0, 8),
                suspicious_activity=random.randint(0, 25),
                data_breach_mentions=random.randint(0, 5),
                malware_indicators=random.randint(0, 7),
                certificate_issues=0,
                configuration_issues=random.randint(0, 10),
                age_days=random.randint(1, 3650),
                last_seen_days=random.randint(0, 7)
            )
        else:
            return RiskFactors(
                vulnerability_count=random.randint(0, 5),
                open_ports=random.randint(0, 10),
                exposed_credentials=random.randint(0, 3),
                suspicious_activity=random.randint(0, 10),
                data_breach_mentions=random.randint(0, 2),
                malware_indicators=random.randint(0, 3),
                certificate_issues=random.randint(0, 1),
                configuration_issues=random.randint(0, 5),
                age_days=random.randint(1, 1825),
                last_seen_days=random.randint(0, 14)
            )
    
    def _calculate_risk_score(self, factors: RiskFactors) -> float:
        """Calculate risk score from risk factors."""
        config = self.config
        
        # Base score calculation
        score = (
            factors.vulnerability_count * config["vulnerability_weight"] +
            factors.open_ports * config["open_ports_weight"] +
            factors.exposed_credentials * config["exposure_weight"] +
            factors.suspicious_activity * config["activity_weight"]
        )
        
        # Apply age decay
        age_factor = max(0.1, 1.0 - (factors.age_days / 100) * config["age_decay"])
        score *= age_factor
        
        # Apply recency factor
        recency_factor = max(0.5, 1.0 - (factors.last_seen_days / 30) * 0.5)
        score *= recency_factor
        
        # Normalize to 0-100 scale
        normalized_score = min(100, max(0, score))
        
        return round(normalized_score, 2)
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from risk score."""
        if risk_score >= 70:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_recommendations(self, factors: RiskFactors, risk_level: str) -> List[str]:
        """Generate risk mitigation recommendations."""
        recommendations = []
        
        if factors.vulnerability_count > 5:
            recommendations.append("🔧 Patch critical vulnerabilities immediately")
        elif factors.vulnerability_count > 0:
            recommendations.append("🔧 Review and patch identified vulnerabilities")
        
        if factors.open_ports > 20:
            recommendations.append("🚪 Close unnecessary open ports")
        elif factors.open_ports > 10:
            recommendations.append("🚪 Review and secure open ports")
        
        if factors.exposed_credentials > 0:
            recommendations.append("🔑 Rotate exposed credentials immediately")
        
        if factors.suspicious_activity > 10:
            recommendations.append("🚨 Investigate suspicious activity patterns")
        elif factors.suspicious_activity > 0:
            recommendations.append("🔍 Monitor for suspicious activity")
        
        if factors.certificate_issues > 0:
            recommendations.append("🛡️ Update or replace expired certificates")
        
        if factors.configuration_issues > 5:
            recommendations.append("⚙️ Review and fix configuration issues")
        
        if risk_level == "HIGH":
            recommendations.append("⚠️ IMMEDIATE ACTION REQUIRED: High risk detected")
        elif risk_level == "MEDIUM":
            recommendations.append("📋 Schedule risk mitigation activities")
        
        return recommendations if recommendations else ["✅ No immediate actions required"]


def create_sample_entities() -> List[Entity]:
    """Create sample entities for risk assessment."""
    entities = []
    
    # Domain entities
    entities.append(Entity(
        name="critical-bank.com",
        entity_type=EntityType.DOMAIN,
        source="dns_collector",
        severity=EntitySeverity.HIGH,
        confidence=0.95
    ))
    
    entities.append(Entity(
        name="marketing-site.com",
        entity_type=EntityType.DOMAIN,
        source="dns_collector",
        severity=EntitySeverity.LOW,
        confidence=0.80
    ))
    
    # IP entities
    entities.append(Entity(
        name="192.168.1.100",
        entity_type=EntityType.IP_ADDRESS,
        source="network_scanner",
        severity=EntitySeverity.MEDIUM,
        confidence=0.90
    ))
    
    entities.append(Entity(
        name="10.0.0.50",
        entity_type=EntityType.IP_ADDRESS,
        source="internal_network",
        severity=EntitySeverity.LOW,
        confidence=0.85
    ))
    
    # Email entities
    entities.append(Entity(
        name="admin@critical-bank.com",
        entity_type=EntityType.EMAIL,
        source="email_collector",
        severity=EntitySeverity.HIGH,
        confidence=0.95
    ))
    
    entities.append(Entity(
        name="info@marketing-site.com",
        entity_type=EntityType.EMAIL,
        source="email_collector",
        severity=EntitySeverity.LOW,
        confidence=0.70
    ))
    
    return entities


def example_1_individual_risk_assessment():
    """Example 1: Assess risk for individual entities."""
    print("\n" + "="*60)
    print("Example 1: Individual Entity Risk Assessment")
    print("="*60)
    
    # Create risk engine
    risk_engine = MockRiskEngine()
    
    # Create sample entities
    entities = create_sample_entities()
    
    # Assess risk for each entity
    for entity in entities:
        print(f"\n🔍 Assessing risk for: {entity.name} ({entity.entity_type.value})")
        assessment = risk_engine.assess_entity_risk(entity)
        
        print(f"  📊 Risk Score: {assessment['risk_score']}/100")
        print(f"  🎯 Risk Level: {assessment['risk_level']}")
        
        # Show top 3 risk factors
        factors = assessment['risk_factors']
        top_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"  ⚠️ Top Risk Factors:")
        for factor, value in top_factors:
            if value > 0:
                print(f"    - {factor.replace('_', ' ').title()}: {value}")
        
        # Show recommendations
        if assessment['recommendations']:
            print(f"  💡 Recommendations:")
            for rec in assessment['recommendations'][:3]:
                print(f"    {rec}")


def example_2_portfolio_risk_assessment():
    """Example 2: Assess risk for a portfolio of entities."""
    print("\n" + "="*60)
    print("Example 2: Portfolio Risk Assessment")
    print("="*60)
    
    # Create risk engine and entities
    risk_engine = MockRiskEngine()
    entities = create_sample_entities()
    
    # Assess portfolio risk
    print("📊 Assessing portfolio risk...")
    portfolio_assessment = risk_engine.assess_portfolio_risk(entities)
    
    # Display portfolio summary
    summary = portfolio_assessment['portfolio_summary']
    print(f"\n📈 Portfolio Summary:")
    print(f"  Total Entities: {summary['total_entities']}")
    print(f"  High Risk Entities: {summary['high_risk_entities']}")
    print(f"  Medium Risk Entities: {summary['medium_risk_entities']}")
    print(f"  Low Risk Entities: {summary['low_risk_entities']}")
    print(f"  Average Risk Score: {summary['average_risk_score']}/100")
    
    # Display top risks
    print(f"\n🚨 Top Risk Entities:")
    for i, risk in enumerate(portfolio_assessment['top_risks'], 1):
        print(f"  {i}. {risk['entity_name']} ({risk['entity_type']})")
        print(f"     Risk Score: {risk['risk_score']}/100 ({risk['risk_level']})")
    
    # Risk distribution
    print(f"\n📊 Risk Distribution:")
    total = summary['total_entities']
    if total > 0:
        high_pct = (summary['high_risk_entities'] / total) * 100
        medium_pct = (summary['medium_risk_entities'] / total) * 100
        low_pct = (summary['low_risk_entities'] / total) * 100
        
        print(f"  🔴 High Risk: {high_pct:.1f}%")
        print(f"  🟡 Medium Risk: {medium_pct:.1f}%")
        print(f"  🟢 Low Risk: {low_pct:.1f}%")


def example_3_risk_trends():
    """Example 3: Analyze risk trends over time."""
    print("\n" + "="*60)
    print("Example 3: Risk Trend Analysis")
    print("="*60)
    
    # Create risk engine
    risk_engine = MockRiskEngine()
    
    # Create a test entity
    test_entity = Entity(
        name="trend-analysis.com",
        entity_type=EntityType.DOMAIN,
        source="dns_collector",
        severity=EntitySeverity.MEDIUM,
        confidence=0.85
    )
    
    # Simulate risk assessments over time
    print("📈 Simulating risk assessments over 30 days...")
    
    risk_scores = []
    dates = []
    
    for days_ago in range(30, 0, -1):
        # Simulate changing risk factors over time
        assessment_date = datetime.now() - timedelta(days=days_ago)
        
        # Vary risk factors to simulate changes
        mock_factors = RiskFactors(
            vulnerability_count=random.randint(2, 8),
            open_ports=random.randint(5, 25),
            exposed_credentials=random.randint(0, 3),
            suspicious_activity=random.randint(0, 10),
            data_breach_mentions=random.randint(0, 2),
            malware_indicators=random.randint(0, 2),
            certificate_issues=random.randint(0, 2),
            configuration_issues=random.randint(2, 8),
            age_days=days_ago,
            last_seen_days=random.randint(0, 7)
        )
        
        risk_score = risk_engine._calculate_risk_score(mock_factors)
        risk_scores.append(risk_score)
        dates.append(assessment_date.strftime("%Y-%m-%d"))
    
    # Calculate trend statistics
    avg_score = sum(risk_scores) / len(risk_scores)
    min_score = min(risk_scores)
    max_score = max(risk_scores)
    
    # Find trend direction
    recent_avg = sum(risk_scores[-7:]) / 7  # Last 7 days
    earlier_avg = sum(risk_scores[:7]) / 7   # First 7 days
    
    if recent_avg > earlier_avg + 5:
        trend = "📈 Increasing"
    elif recent_avg < earlier_avg - 5:
        trend = "📉 Decreasing"
    else:
        trend = "➡️ Stable"
    
    print(f"\n📊 Risk Trend Analysis for {test_entity.name}:")
    print(f"  Average Risk Score: {avg_score:.2f}/100")
    print(f"  Risk Score Range: {min_score:.2f} - {max_score:.2f}")
    print(f"  Trend: {trend}")
    
    # Show sample data points
    print(f"\n📅 Sample Risk Scores:")
    sample_points = list(zip(dates[::5], risk_scores[::5]))  # Every 5th point
    for date, score in sample_points:
        risk_level = risk_engine._determine_risk_level(score)
        print(f"  {date}: {score:.1f}/100 ({risk_level})")


def example_4_risk_mitigation():
    """Example 4: Risk mitigation scenario."""
    print("\n" + "="*60)
    print("Example 4: Risk Mitigation Scenario")
    print("="*60)
    
    # Create risk engine
    risk_engine = MockRiskEngine()
    
    # Create a high-risk entity
    high_risk_entity = Entity(
        name="vulnerable-server.com",
        entity_type=EntityType.DOMAIN,
        source="dns_collector",
        severity=EntitySeverity.HIGH,
        confidence=0.95
    )
    
    # Initial risk assessment
    print("🔍 Initial Risk Assessment:")
    initial_assessment = risk_engine.assess_entity_risk(high_risk_entity)
    
    print(f"  Risk Score: {initial_assessment['risk_score']}/100")
    print(f"  Risk Level: {initial_assessment['risk_level']}")
    
    # Show initial risk factors
    factors = initial_assessment['risk_factors']
    print(f"\n⚠️ Initial Risk Factors:")
    for factor, value in factors.items():
        if value > 0:
            print(f"  - {factor.replace('_', ' ').title()}: {value}")
    
    # Simulate mitigation actions
    print(f"\n🔧 Applying Mitigation Actions...")
    
    # Create improved risk factors (after mitigation)
    mitigated_factors = RiskFactors(
        vulnerability_count=max(0, factors['vulnerability_count'] - 8),  # Patched vulnerabilities
        open_ports=max(0, factors['open_ports'] - 15),  # Closed ports
        exposed_credentials=0,  # Rotated credentials
        suspicious_activity=max(0, factors['suspicious_activity'] - 5),  # Reduced activity
        data_breach_mentions=factors['data_breach_mentions'],
        malware_indicators=max(0, factors['malware_indicators'] - 1),  # Cleaned malware
        certificate_issues=0,  # Updated certificates
        configuration_issues=max(0, factors['configuration_issues'] - 6),  # Fixed configs
        age_days=factors['age_days'],
        last_seen_days=0  # Recently seen
    )
    
    # Calculate post-mitigation risk score
    post_mitigation_score = risk_engine._calculate_risk_score(mitigated_factors)
    post_mitigation_level = risk_engine._determine_risk_level(post_mitigation_score)
    
    print(f"\n✅ Post-Mitigation Risk Assessment:")
    print(f"  Risk Score: {post_mitigation_score}/100")
    print(f"  Risk Level: {post_mitigation_level}")
    
    # Calculate improvement
    score_improvement = initial_assessment['risk_score'] - post_mitigation_score
    improvement_percentage = (score_improvement / initial_assessment['risk_score']) * 100
    
    print(f"\n📈 Mitigation Results:")
    print(f"  Score Improvement: {score_improvement:.2f} points")
    print(f"  Improvement Percentage: {improvement_percentage:.1f}%")
    
    if initial_assessment['risk_level'] != post_mitigation_level:
        print(f"  Risk Level Changed: {initial_assessment['risk_level']} → {post_mitigation_level}")
    else:
        print(f"  Risk Level: {post_mitigation_level} (unchanged)")
    
    # Show remaining recommendations
    remaining_recommendations = risk_engine._generate_recommendations(mitigated_factors, post_mitigation_level)
    if remaining_recommendations:
        print(f"\n💡 Remaining Recommendations:")
        for rec in remaining_recommendations[:3]:
            print(f"  {rec}")


def main():
    """Run all risk assessment examples."""
    print("CtxOS Risk Engine Examples")
    print("=" * 60)
    
    # Run all examples
    example_1_individual_risk_assessment()
    example_2_portfolio_risk_assessment()
    example_3_risk_trends()
    example_4_risk_mitigation()
    
    print("\n" + "="*60)
    print("✅ All risk assessment examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()