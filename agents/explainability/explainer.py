"""
Explainability Agent - Explain why scores are what they are.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import math

from core.models.context import Context
from core.models.entity import Entity
from core.models.signal import Signal
from core.scoring.risk import ScoringResult
from agents.base_agent_async import BaseAgentAsync, AgentResult
from agents.audit_system.audit_logger import AuditLevel


class ExplanationType(Enum):
    """Types of explanations."""

    SCORE_BREAKDOWN = "score_breakdown"
    FACTOR_ANALYSIS = "factor_analysis"
    TEMPORAL_ANALYSIS = "temporal_analysis"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    ROOT_CAUSE = "root_cause"
    RECOMMENDATION_RATIONALE = "recommendation_rationale"


class ConfidenceLevel(Enum):
    """Confidence levels for explanations."""

    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


@dataclass
class ExplanationFactor:
    """Single factor in score explanation."""

    name: str
    value: Union[str, float, int]
    weight: float
    contribution: float  # How much this factor contributed to final score
    direction: str  # "positive" or "negative"
    description: str
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "weight": self.weight,
            "contribution": self.contribution,
            "direction": self.direction,
            "description": self.description,
            "evidence": self.evidence,
        }


@dataclass
class ScoreExplanation:
    """Comprehensive score explanation."""

    explanation_type: ExplanationType
    title: str
    summary: str
    final_score: float
    severity: str
    confidence: ConfidenceLevel
    factors: List[ExplanationFactor] = field(default_factory=list)
    key_drivers: List[str] = field(default_factory=list)
    mitigating_factors: List[str] = field(default_factory=list)
    risk_drivers: List[str] = field(default_factory=list)
    temporal_trends: Dict[str, Any] = field(default_factory=dict)
    comparisons: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "explanation_type": self.explanation_type.value,
            "title": self.title,
            "summary": self.summary,
            "final_score": self.final_score,
            "severity": self.severity,
            "confidence": self.confidence.value,
            "factors": [f.to_dict() for f in self.factors],
            "key_drivers": self.key_drivers,
            "mitigating_factors": self.mitigating_factors,
            "risk_drivers": self.risk_drivers,
            "temporal_trends": self.temporal_trends,
            "comparisons": self.comparisons,
            "recommendations": self.recommendations,
            "next_steps": self.next_steps,
        }


@dataclass
class ExplainabilityResult:
    """Complete explainability analysis result."""

    entity_id: str
    score: float
    severity: str
    explanations: List[ScoreExplanation] = field(default_factory=list)
    overall_confidence: float = 0.0
    explanation_coverage: float = 0.0
    actionable_insights: int = 0
    key_findings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_id": self.entity_id,
            "score": self.score,
            "severity": self.severity,
            "explanations": [e.to_dict() for e in self.explanations],
            "overall_confidence": self.overall_confidence,
            "explanation_coverage": self.explanation_coverage,
            "actionable_insights": self.actionable_insights,
            "key_findings": self.key_findings,
        }


class ExplainabilityAgent(BaseAgentAsync):
    """Agent that explains scoring decisions and provides rationale."""

    def __init__(
        self,
        name: str = "ExplainabilityAgent",
        version: str = "1.0.0",
        min_factor_weight: float = 0.05,
        max_explanations: int = 5,
        include_comparisons: bool = True,
        temporal_analysis_days: int = 30,
    ):
        """Initialize explainability agent.

        Args:
            name: Agent name
            version: Agent version
            min_factor_weight: Minimum weight for factors to include
            max_explanations: Maximum explanations to generate
            include_comparisons: Include comparative analysis
            temporal_analysis_days: Days for temporal analysis
        """
        super().__init__(name, version)
        self.min_factor_weight = min_factor_weight
        self.max_explanations = max_explanations
        self.include_comparisons = include_comparisons
        self.temporal_analysis_days = temporal_analysis_days

        # Factor weight mappings
        self.factor_weights = {
            "vulnerability": 0.3,
            "exposure": 0.25,
            "drift": 0.2,
            "configuration": 0.15,
            "activity": 0.1,
        }

        # Severity mappings
        self.severity_thresholds = {
            "critical": 90,
            "high": 70,
            "medium": 40,
            "low": 20,
            "info": 0,
        }

    async def analyze(
        self,
        context: Context,
        scoring_result: Optional[ScoringResult] = None,
    ) -> AgentResult:
        """Analyze context and provide score explanations.

        Args:
            context: Input context with entity and signals
            scoring_result: Optional scoring result from engines

        Returns:
            AgentResult with explainability analysis
        """
        try:
            # Generate explanations
            result = await self._generate_explanations(context, scoring_result)

            # Create agent result
            agent_result = AgentResult(
                agent_name=self.name,
                success=True,
                output={
                    "explainability_result": result.to_dict(),
                    "summary": {
                        "total_explanations": len(result.explanations),
                        "overall_confidence": result.overall_confidence,
                        "actionable_insights": result.actionable_insights,
                        "explanation_coverage": result.explanation_coverage,
                    },
                },
            )

            return agent_result

        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                success=False,
                error=f"Failed to generate explanations: {str(e)}",
            )

    async def _generate_explanations(
        self,
        context: Context,
        scoring_result: Optional[ScoringResult] = None,
    ) -> ExplainabilityResult:
        """Generate comprehensive score explanations."""
        if not scoring_result:
            # Create default result if no scoring result
            return ExplainabilityResult(
                entity_id=context.entity.id if context.entity else "unknown",
                score=0.0,
                severity="info",
                key_findings=["No scoring result available for explanation"],
            )

        result = ExplainabilityResult(
            entity_id=context.entity.id if context.entity else "unknown",
            score=scoring_result.score,
            severity=scoring_result.severity,
        )

        # Generate different types of explanations
        await self._generate_score_breakdown(scoring_result, context, result)
        await self._generate_factor_analysis(scoring_result, context, result)
        await self._generate_root_cause_analysis(scoring_result, context, result)

        if context.signals:
            await self._generate_temporal_analysis(scoring_result, context, result)

        if self.include_comparisons:
            await self._generate_comparative_analysis(scoring_result, context, result)

        # Calculate overall metrics
        self._calculate_overall_metrics(result)

        # Extract key findings
        result.key_findings = self._extract_key_findings(result)

        return result

    async def _generate_score_breakdown(
        self,
        scoring_result: ScoringResult,
        context: Context,
        result: ExplainabilityResult,
    ) -> None:
        """Generate detailed score breakdown explanation."""
        factors = []

        # Analyze different scoring components
        if hasattr(scoring_result, "metrics") and scoring_result.metrics:
            for metric_name, metric_value in scoring_result.metrics.items():
                factor = ExplanationFactor(
                    name=metric_name,
                    value=metric_value,
                    weight=self.factor_weights.get(metric_name, 0.1),
                    contribution=self._calculate_contribution(
                        metric_name, metric_value, scoring_result.score
                    ),
                    direction="negative" if metric_value > 0 else "positive",
                    description=self._describe_factor(metric_name, metric_value),
                    evidence=self._get_factor_evidence(metric_name, context),
                )
                factors.append(factor)

        # Generate key drivers and mitigating factors
        key_drivers = [f.name for f in factors if f.contribution > 0.1]
        mitigating_factors = [f.name for f in factors if f.contribution < -0.05]

        explanation = ScoreExplanation(
            explanation_type=ExplanationType.SCORE_BREAKDOWN,
            title="Score Breakdown Analysis",
            summary=f"The final score of {scoring_result.score} is calculated from {len(factors)} contributing factors",
            final_score=scoring_result.score,
            severity=scoring_result.severity,
            confidence=self._calculate_explanation_confidence(factors),
            factors=factors,
            key_drivers=key_drivers,
            mitigating_factors=mitigating_factors,
            recommendations=self._generate_score_recommendations(factors),
            next_steps=self._generate_next_steps(factors),
        )

        result.explanations.append(explanation)

    async def _generate_factor_analysis(
        self,
        scoring_result: ScoringResult,
        context: Context,
        result: ExplainabilityResult,
    ) -> None:
        """Generate detailed factor analysis explanation."""
        factors = []

        # Analyze signal-based factors
        if context.signals:
            signal_factors = await self._analyze_signal_factors(
                context.signals, scoring_result.score
            )
            factors.extend(signal_factors)

        # Analyze entity-based factors
        if context.entity:
            entity_factors = await self._analyze_entity_factors(
                context.entity, scoring_result.score
            )
            factors.extend(entity_factors)

        # Identify risk drivers
        risk_drivers = [f.name for f in factors if f.direction == "negative" and f.weight > 0.2]

        explanation = ScoreExplanation(
            explanation_type=ExplanationType.FACTOR_ANALYSIS,
            title="Contributing Factor Analysis",
            summary=f"Analysis of {len(factors)} factors that influenced the scoring decision",
            final_score=scoring_result.score,
            severity=scoring_result.severity,
            confidence=self._calculate_explanation_confidence(factors),
            factors=factors,
            risk_drivers=risk_drivers,
            recommendations=self._generate_factor_recommendations(factors),
            next_steps=self._generate_factor_next_steps(factors),
        )

        result.explanations.append(explanation)

    async def _generate_root_cause_analysis(
        self,
        scoring_result: ScoringResult,
        context: Context,
        result: ExplainabilityResult,
    ) -> None:
        """Generate root cause analysis explanation."""
        factors = []

        # Identify root causes based on signals and entity properties
        root_causes = self._identify_root_causes(context, scoring_result)

        for cause in root_causes:
            factor = ExplanationFactor(
                name=cause["name"],
                value=cause["value"],
                weight=cause["weight"],
                contribution=cause["contribution"],
                direction=cause["direction"],
                description=cause["description"],
                evidence=cause["evidence"],
            )
            factors.append(factor)

        explanation = ScoreExplanation(
            explanation_type=ExplanationType.ROOT_CAUSE,
            title="Root Cause Analysis",
            summary=f"Identified {len(factors)} root causes contributing to the current risk level",
            final_score=scoring_result.score,
            severity=scoring_result.severity,
            confidence=self._calculate_explanation_confidence(factors),
            factors=factors,
            key_drivers=[f.name for f in factors if f.contribution > 0.15],
            recommendations=self._generate_root_cause_recommendations(factors),
            next_steps=self._generate_root_cause_next_steps(factors),
        )

        result.explanations.append(explanation)

    async def _generate_temporal_analysis(
        self,
        scoring_result: ScoringResult,
        context: Context,
        result: ExplainabilityResult,
    ) -> None:
        """Generate temporal trend analysis explanation."""
        temporal_data = self._analyze_temporal_trends(context.signals)

        factors = []
        for trend_name, trend_data in temporal_data.items():
            factor = ExplanationFactor(
                name=f"temporal_{trend_name}",
                value=trend_data["value"],
                weight=0.15,
                contribution=trend_data["contribution"],
                direction=trend_data["direction"],
                description=trend_data["description"],
                evidence=trend_data["evidence"],
            )
            factors.append(factor)

        explanation = ScoreExplanation(
            explanation_type=ExplanationType.TEMPORAL_ANALYSIS,
            title="Temporal Trend Analysis",
            summary=f"Analysis of {len(temporal_data)} temporal trends over the last {self.temporal_analysis_days} days",
            final_score=scoring_result.score,
            severity=scoring_result.severity,
            confidence=self._calculate_explanation_confidence(factors),
            factors=factors,
            temporal_trends=temporal_data,
            recommendations=self._generate_temporal_recommendations(temporal_data),
            next_steps=self._generate_temporal_next_steps(temporal_data),
        )

        result.explanations.append(explanation)

    async def _generate_comparative_analysis(
        self,
        scoring_result: ScoringResult,
        context: Context,
        result: ExplainabilityResult,
    ) -> None:
        """Generate comparative analysis explanation."""
        comparisons = self._generate_comparisons(scoring_result, context)

        factors = []
        for comparison_name, comparison_data in comparisons.items():
            factor = ExplanationFactor(
                name=f"comparison_{comparison_name}",
                value=comparison_data["value"],
                weight=0.1,
                contribution=comparison_data["contribution"],
                direction=comparison_data["direction"],
                description=comparison_data["description"],
                evidence=comparison_data["evidence"],
            )
            factors.append(factor)

        explanation = ScoreExplanation(
            explanation_type=ExplanationType.COMPARATIVE_ANALYSIS,
            title="Comparative Analysis",
            summary=f"Comparison with similar entities and historical baselines",
            final_score=scoring_result.score,
            severity=scoring_result.severity,
            confidence=self._calculate_explanation_confidence(factors),
            factors=factors,
            comparisons=comparisons,
            recommendations=self._generate_comparative_recommendations(comparisons),
            next_steps=self._generate_comparative_next_steps(comparisons),
        )

        result.explanations.append(explanation)

    async def _analyze_signal_factors(
        self,
        signals: List[Signal],
        final_score: float,
    ) -> List[ExplanationFactor]:
        """Analyze signal-based factors."""
        factors = []

        # Group signals by type and severity
        signal_groups = {}
        for signal in signals:
            key = f"{signal.signal_type}:{signal.severity}"
            if key not in signal_groups:
                signal_groups[key] = []
            signal_groups[key].append(signal)

        for signal_key, group_signals in signal_groups.items():
            signal_type, severity = signal_key.split(":")

            # Calculate factor contribution
            count = len(group_signals)
            severity_weight = self._get_severity_weight(severity)
            contribution = (count * severity_weight) / 100.0

            if abs(contribution) >= self.min_factor_weight:
                factor = ExplanationFactor(
                    name=f"{signal_type}_{severity.lower()}",
                    value=count,
                    weight=severity_weight,
                    contribution=contribution,
                    direction="negative" if severity_weight > 0 else "positive",
                    description=f"{count} {severity.lower()} {signal_type} signals detected",
                    evidence=[s.id for s in group_signals[:3]],  # Top 3 as evidence
                )
                factors.append(factor)

        return factors

    async def _analyze_entity_factors(
        self,
        entity: Entity,
        final_score: float,
    ) -> List[ExplanationFactor]:
        """Analyze entity-based factors."""
        factors = []

        # Entity type factor
        entity_type_weight = self._get_entity_type_weight(entity.entity_type)
        factor = ExplanationFactor(
            name="entity_type",
            value=entity.entity_type,
            weight=entity_type_weight,
            contribution=entity_type_weight * 0.1,
            direction="negative" if entity_type_weight > 0.5 else "positive",
            description=f"Entity type '{entity.entity_type}' has inherent risk characteristics",
            evidence=[f"entity:{entity.id}"],
        )
        factors.append(factor)

        # Entity properties factors
        if entity.properties:
            for prop_name, prop_value in entity.properties.items():
                prop_weight = self._get_property_weight(prop_name, prop_value)
                if prop_weight >= self.min_factor_weight:
                    factor = ExplanationFactor(
                        name=f"property_{prop_name}",
                        value=prop_value,
                        weight=prop_weight,
                        contribution=prop_weight * 0.05,
                        direction="negative" if prop_weight > 0.5 else "positive",
                        description=f"Property '{prop_name}' with value '{prop_value}' affects risk",
                        evidence=[f"property:{prop_name}"],
                    )
                    factors.append(factor)

        return factors

    def _identify_root_causes(
        self,
        context: Context,
        scoring_result: ScoringResult,
    ) -> List[Dict[str, Any]]:
        """Identify root causes of current score."""
        root_causes = []

        # Analyze signals for root causes
        if context.signals:
            # Critical vulnerabilities
            critical_vulns = [
                s
                for s in context.signals
                if s.signal_type == "VULNERABILITY" and s.severity == "critical"
            ]
            if critical_vulns:
                root_causes.append(
                    {
                        "name": "critical_vulnerabilities",
                        "value": len(critical_vulns),
                        "weight": 0.4,
                        "contribution": len(critical_vulns) * 0.15,
                        "direction": "negative",
                        "description": f"{len(critical_vulns)} critical vulnerabilities present",
                        "evidence": [s.id for s in critical_vulns],
                    }
                )

            # Open ports
            open_ports = [s for s in context.signals if s.signal_type == "PORT"]
            if open_ports:
                root_causes.append(
                    {
                        "name": "exposed_services",
                        "value": len(open_ports),
                        "weight": 0.3,
                        "contribution": len(open_ports) * 0.05,
                        "direction": "negative",
                        "description": f"{len(open_ports)} exposed services/ports detected",
                        "evidence": [s.id for s in open_ports[:3]],
                    }
                )

        # Entity-based root causes
        if context.entity:
            if context.entity.properties and context.entity.properties.get("public", False):
                root_causes.append(
                    {
                        "name": "public_exposure",
                        "value": True,
                        "weight": 0.35,
                        "contribution": 0.2,
                        "direction": "negative",
                        "description": "Entity is publicly exposed, increasing attack surface",
                        "evidence": ["entity:public:true"],
                    }
                )

        return root_causes

    def _analyze_temporal_trends(self, signals: List[Signal]) -> Dict[str, Any]:
        """Analyze temporal trends in signals."""
        trends = {}

        if not signals:
            return trends

        cutoff_date = datetime.utcnow() - timedelta(days=self.temporal_analysis_days)
        recent_signals = [s for s in signals if s.timestamp and s.timestamp >= cutoff_date]

        # Signal frequency trend
        if recent_signals:
            trends["signal_frequency"] = {
                "value": len(recent_signals),
                "contribution": min(0.2, len(recent_signals) * 0.02),
                "direction": "negative" if len(recent_signals) > 10 else "positive",
                "description": f"{len(recent_signals)} signals in last {self.temporal_analysis_days} days",
                "evidence": [s.id for s in recent_signals[:3]],
            }

            # Severity trend
            severity_trend = self._calculate_severity_trend(recent_signals)
            trends["severity_trend"] = severity_trend

        return trends

    def _generate_comparisons(
        self,
        scoring_result: ScoringResult,
        context: Context,
    ) -> Dict[str, Any]:
        """Generate comparative analysis."""
        comparisons = {}

        # Compare with entity type average
        entity_type_avg = self._get_entity_type_average(
            context.entity.entity_type if context.entity else "unknown"
        )
        if entity_type_avg:
            diff = scoring_result.score - entity_type_avg
            comparisons["entity_type_average"] = {
                "value": entity_type_avg,
                "contribution": diff / 100.0,
                "direction": "negative" if diff > 0 else "positive",
                "description": f"Score is {diff:+.1f} points compared to {context.entity.entity_type} average",
                "evidence": ["benchmark:entity_type_average"],
            }

        # Compare with historical baseline
        historical_avg = self._get_historical_average(
            context.entity.id if context.entity else "unknown"
        )
        if historical_avg:
            diff = scoring_result.score - historical_avg
            comparisons["historical_average"] = {
                "value": historical_avg,
                "contribution": diff / 100.0,
                "direction": "negative" if diff > 0 else "positive",
                "description": f"Score is {diff:+.1f} points compared to historical average",
                "evidence": ["benchmark:historical_average"],
            }

        return comparisons

    def _calculate_contribution(
        self,
        metric_name: str,
        metric_value: Union[float, int],
        final_score: float,
    ) -> float:
        """Calculate contribution of a factor to final score."""
        if final_score == 0:
            return 0.0

        # Simple contribution calculation
        weight = self.factor_weights.get(metric_name, 0.1)
        normalized_value = (
            min(1.0, abs(metric_value) / 100.0) if isinstance(metric_value, (int, float)) else 0.5
        )

        return weight * normalized_value

    def _describe_factor(self, metric_name: str, metric_value: Union[float, int]) -> str:
        """Generate description for a factor."""
        descriptions = {
            "vulnerability": f"Vulnerability score of {metric_value} indicates security weaknesses",
            "exposure": f"Exposure score of {metric_value} reflects attack surface size",
            "drift": f"Drift score of {metric_value} shows configuration changes",
            "configuration": f"Configuration score of {metric_value} indicates setup issues",
            "activity": f"Activity score of {metric_value} reflects recent security events",
        }

        return descriptions.get(metric_name, f"Factor {metric_name} with value {metric_value}")

    def _get_factor_evidence(self, metric_name: str, context: Context) -> List[str]:
        """Get evidence for a factor."""
        evidence = []

        if context.signals:
            relevant_signals = [
                s for s in context.signals if metric_name.lower() in s.signal_type.lower()
            ]
            evidence.extend([s.id for s in relevant_signals[:3]])

        if context.entity:
            evidence.append(f"entity:{context.entity.id}")

        return evidence

    def _calculate_explanation_confidence(
        self, factors: List[ExplanationFactor]
    ) -> ConfidenceLevel:
        """Calculate confidence level for explanation."""
        if not factors:
            return ConfidenceLevel.VERY_LOW

        # Calculate average weight and evidence
        avg_weight = sum(f.weight for f in factors) / len(factors)
        avg_evidence = sum(len(f.evidence) for f in factors) / len(factors)

        # Combine factors for confidence
        confidence_score = (avg_weight * 0.6) + (min(1.0, avg_evidence / 3.0) * 0.4)

        if confidence_score >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif confidence_score >= 0.7:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif confidence_score >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def _generate_score_recommendations(self, factors: List[ExplanationFactor]) -> List[str]:
        """Generate recommendations based on score factors."""
        recommendations = []

        # High-impact factors
        high_impact = [f for f in factors if f.contribution > 0.15]
        if high_impact:
            recommendations.append(
                f"Address {len(high_impact)} high-impact factors: {', '.join([f.name for f in high_impact])}"
            )

        # Vulnerability factors
        vuln_factors = [f for f in factors if "vulnerability" in f.name.lower()]
        if vuln_factors:
            recommendations.append("Prioritize vulnerability remediation to reduce score")

        # Exposure factors
        exp_factors = [f for f in factors if "exposure" in f.name.lower()]
        if exp_factors:
            recommendations.append("Reduce attack surface by addressing exposure factors")

        return recommendations[:3]

    def _generate_next_steps(self, factors: List[ExplanationFactor]) -> List[str]:
        """Generate next steps based on factors."""
        steps = []

        # Sort factors by contribution
        sorted_factors = sorted(factors, key=lambda f: abs(f.contribution), reverse=True)

        for factor in sorted_factors[:3]:
            if factor.direction == "negative":
                steps.append(
                    f"Investigate and mitigate {factor.name} (contribution: {factor.contribution:.2f})"
                )

        return steps

    def _generate_factor_recommendations(self, factors: List[ExplanationFactor]) -> List[str]:
        """Generate recommendations based on factor analysis."""
        recommendations = []

        # Risk drivers
        risk_factors = [f for f in factors if f.direction == "negative" and f.weight > 0.2]
        if risk_factors:
            recommendations.append(f"Focus on {len(risk_factors)} primary risk drivers")

        # Positive factors
        positive_factors = [f for f in factors if f.direction == "positive"]
        if positive_factors:
            recommendations.append(f"Maintain {len(positive_factors)} positive security factors")

        return recommendations

    def _generate_factor_next_steps(self, factors: List[ExplanationFactor]) -> List[str]:
        """Generate next steps for factor analysis."""
        steps = []

        # Top risk factors
        risk_factors = sorted(
            [f for f in factors if f.direction == "negative"],
            key=lambda f: f.contribution,
            reverse=True,
        )

        for factor in risk_factors[:2]:
            steps.append(f"Analyze {factor.name} in detail for remediation options")

        return steps

    def _generate_root_cause_recommendations(self, factors: List[ExplanationFactor]) -> List[str]:
        """Generate recommendations for root causes."""
        recommendations = []

        for factor in factors:
            if factor.name == "critical_vulnerabilities":
                recommendations.append("Immediate patching of critical vulnerabilities")
            elif factor.name == "exposed_services":
                recommendations.append("Review and secure exposed services")
            elif factor.name == "public_exposure":
                recommendations.append("Evaluate necessity of public exposure")

        return recommendations

    def _generate_root_cause_next_steps(self, factors: List[ExplanationFactor]) -> List[str]:
        """Generate next steps for root causes."""
        steps = []

        for factor in factors:
            if factor.name == "critical_vulnerabilities":
                steps.append("Conduct vulnerability assessment and create remediation plan")
            elif factor.name == "exposed_services":
                steps.append("Perform port scan and service inventory")
            elif factor.name == "public_exposure":
                steps.append("Review access controls and network segmentation")

        return steps

    def _generate_temporal_recommendations(self, temporal_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on temporal analysis."""
        recommendations = []

        if "signal_frequency" in temporal_data:
            freq = temporal_data["signal_frequency"]["value"]
            if freq > 20:
                recommendations.append(
                    "Investigate high signal frequency - may indicate active issues"
                )

        if "severity_trend" in temporal_data:
            trend = temporal_data["severity_trend"]
            if trend.get("direction") == "increasing":
                recommendations.append("Address increasing severity trend")

        return recommendations

    def _generate_temporal_next_steps(self, temporal_data: Dict[str, Any]) -> List[str]:
        """Generate next steps for temporal analysis."""
        steps = []

        if "signal_frequency" in temporal_data:
            steps.append("Monitor signal frequency trends over time")

        if "severity_trend" in temporal_data:
            steps.append("Analyze root causes of severity changes")

        return steps

    def _generate_comparative_recommendations(self, comparisons: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on comparative analysis."""
        recommendations = []

        for comp_name, comp_data in comparisons.items():
            if comp_data["direction"] == "negative":
                recommendations.append(f"Address deviation in {comp_name}")

        return recommendations

    def _generate_comparative_next_steps(self, comparisons: Dict[str, Any]) -> List[str]:
        """Generate next steps for comparative analysis."""
        steps = []

        for comp_name, comp_data in comparisons.items():
            if comp_data["direction"] == "negative":
                steps.append(f"Investigate why score exceeds {comp_name} benchmark")

        return steps

    def _calculate_overall_metrics(self, result: ExplainabilityResult) -> None:
        """Calculate overall explainability metrics."""
        if not result.explanations:
            return

        # Overall confidence (average of all explanations)
        conf_values = {
            ConfidenceLevel.VERY_HIGH: 1.0,
            ConfidenceLevel.HIGH: 0.8,
            ConfidenceLevel.MEDIUM: 0.6,
            ConfidenceLevel.LOW: 0.4,
            ConfidenceLevel.VERY_LOW: 0.2,
        }

        total_confidence = sum(conf_values[e.confidence] for e in result.explanations)
        result.overall_confidence = total_confidence / len(result.explanations)

        # Explanation coverage (number of explanation types)
        explanation_types = {e.explanation_type for e in result.explanations}
        result.explanation_coverage = len(explanation_types) / len(ExplanationType)

        # Actionable insights (explanations with recommendations)
        result.actionable_insights = sum(1 for e in result.explanations if e.recommendations)

    def _extract_key_findings(self, result: ExplainabilityResult) -> List[str]:
        """Extract key findings from explanations."""
        findings = []

        # High score findings
        if result.score >= 70:
            findings.append(f"High risk score ({result.score}) requires immediate attention")

        # Key drivers from all explanations
        all_key_drivers = []
        for explanation in result.explanations:
            all_key_drivers.extend(explanation.key_drivers)

        if all_key_drivers:
            # Count frequency of drivers
            driver_counts = {}
            for driver in all_key_drivers:
                driver_counts[driver] = driver_counts.get(driver, 0) + 1

            # Top drivers
            top_drivers = sorted(driver_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            findings.extend([f"Key driver: {driver}" for driver, count in top_drivers])

        return findings[:5]  # Limit to top 5 findings

    def _get_severity_weight(self, severity: str) -> float:
        """Get weight for severity level."""
        weights = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4,
            "info": 0.2,
        }
        return weights.get(severity.lower(), 0.3)

    def _get_entity_type_weight(self, entity_type: str) -> float:
        """Get weight for entity type."""
        weights = {
            "host": 0.8,
            "application": 0.9,
            "database": 0.85,
            "domain": 0.6,
            "network": 0.7,
        }
        return weights.get(entity_type.lower(), 0.5)

    def _get_property_weight(self, prop_name: str, prop_value: Any) -> float:
        """Get weight for entity property."""
        # High-risk properties
        if prop_name.lower() in {"public", "exposed", "critical", "production"}:
            if prop_value in {True, "true", "yes", "production"}:
                return 0.8

        # Medium-risk properties
        if prop_name.lower() in {"internet_facing", "external", "dmz"}:
            if prop_value in {True, "true", "yes"}:
                return 0.6

        return 0.1

    def _get_entity_type_average(self, entity_type: str) -> Optional[float]:
        """Get average score for entity type (mock implementation)."""
        # Mock averages - in real implementation, this would query historical data
        averages = {
            "host": 45.0,
            "application": 55.0,
            "database": 50.0,
            "domain": 35.0,
            "network": 40.0,
        }
        return averages.get(entity_type.lower())

    def _get_historical_average(self, entity_id: str) -> Optional[float]:
        """Get historical average score for entity (mock implementation)."""
        # Mock implementation - in real system, would query time-series data
        return 42.0

    def _calculate_severity_trend(self, signals: List[Signal]) -> Dict[str, Any]:
        """Calculate severity trend over time."""
        if not signals:
            return {}

        # Group by week and calculate average severity
        severity_values = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}

        recent_avg = sum(severity_values.get(s.severity.lower(), 1) for s in signals[-10:]) / min(
            10, len(signals)
        )
        older_avg = sum(severity_values.get(s.severity.lower(), 1) for s in signals[:10]) / min(
            10, len(signals)
        )

        direction = (
            "increasing"
            if recent_avg > older_avg
            else "decreasing"
            if recent_avg < older_avg
            else "stable"
        )

        return {
            "value": recent_avg,
            "contribution": abs(recent_avg - older_avg) * 0.1,
            "direction": direction,
            "description": f"Severity trend is {direction} (recent: {recent_avg:.1f}, older: {older_avg:.1f})",
            "evidence": [f"signals:{len(signals)}"],
        }
