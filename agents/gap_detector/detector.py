"""
Gap Detector Agent - Identify missing data/signals and coverage gaps.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re

from core.models.context import Context
from core.models.entity import Entity
from core.models.signal import Signal
from core.scoring.risk import ScoringResult
from agents.base_agent_async import BaseAgentAsync, AgentResult
from agents.audit_system.audit_logger import AuditLevel


class GapType(Enum):
    """Types of gaps that can be detected."""

    MISSING_SIGNAL = "missing_signal"
    OUTDATED_DATA = "outdated_data"
    COVERAGE_GAP = "coverage_gap"
    INCOMPLETE_SCAN = "incomplete_scan"
    MONITORING_GAP = "monitoring_gap"
    CORRELATION_GAP = "correlation_gap"


@dataclass
class DataGap:
    """Represents a detected data gap."""

    gap_type: GapType
    title: str
    description: str
    severity: str
    confidence: float
    entity_id: Optional[str] = None
    missing_source: Optional[str] = None
    expected_signals: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    impact_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gap_type": self.gap_type.value,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "confidence": self.confidence,
            "entity_id": self.entity_id,
            "missing_source": self.missing_source,
            "expected_signals": self.expected_signals,
            "recommendations": self.recommendations,
            "impact_score": self.impact_score,
        }


@dataclass
class GapAnalysisResult:
    """Complete gap analysis result."""

    total_gaps: int = 0
    critical_gaps: int = 0
    high_gaps: int = 0
    medium_gaps: int = 0
    low_gaps: int = 0
    gaps: List[DataGap] = field(default_factory=list)
    coverage_score: float = 0.0
    data_freshness_score: float = 0.0
    monitoring_completeness: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_gaps": self.total_gaps,
            "critical_gaps": self.critical_gaps,
            "high_gaps": self.high_gaps,
            "medium_gaps": self.medium_gaps,
            "low_gaps": self.low_gaps,
            "gaps": [gap.to_dict() for gap in self.gaps],
            "coverage_score": self.coverage_score,
            "data_freshness_score": self.data_freshness_score,
            "monitoring_completeness": self.monitoring_completeness,
        }


class GapDetector(BaseAgentAsync):
    """Agent that identifies missing data and coverage gaps."""

    def __init__(
        self,
        name: str = "GapDetector",
        version: str = "1.0.0",
        max_data_age_hours: int = 168,  # 1 week
        min_coverage_threshold: float = 0.7,
        critical_sources: Optional[Set[str]] = None,
        entity_type_requirements: Optional[Dict[str, List[str]]] = None,
    ):
        """Initialize gap detector.

        Args:
            name: Agent name
            version: Agent version
            max_data_age_hours: Maximum age for data before considered stale
            min_coverage_threshold: Minimum coverage threshold
            critical_sources: Set of critical data sources
            entity_type_requirements: Required signals per entity type
        """
        super().__init__(name, version)
        self.max_data_age_hours = max_data_age_hours
        self.min_coverage_threshold = min_coverage_threshold

        # Default critical sources
        self.critical_sources = critical_sources or {
            "vulnerability_scanner",
            "asset_inventory",
            "network_scanner",
            "siem",
            "ids",
        }

        # Default entity type requirements
        self.entity_type_requirements = entity_type_requirements or {
            "host": [
                "VULNERABILITY",
                "PORT",
                "SERVICE",
                "CONFIGURATION",
            ],
            "domain": [
                "DNS",
                "SUBDOMAIN",
                "SSL_CERTIFICATE",
                "WHOIS",
            ],
            "application": [
                "VULNERABILITY",
                "DEPENDENCY",
                "CONFIGURATION",
                "ACCESS_LOG",
            ],
            "network": [
                "PORT",
                "SERVICE",
                "TRAFFIC",
                "FIREWALL",
            ],
        }

        # Severity weights
        self.severity_weights = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4,
            "info": 0.2,
        }

    async def analyze(
        self,
        context: Context,
        scoring_result: Optional[ScoringResult] = None,
    ) -> AgentResult:
        """Analyze context for data gaps.

        Args:
            context: Input context with entity and signals
            scoring_result: Optional scoring result from engines

        Returns:
            AgentResult with gap analysis
        """
        try:
            # Perform gap analysis
            result = await self._detect_gaps(context, scoring_result)

            # Create agent result
            agent_result = AgentResult(
                agent_name=self.name,
                success=True,
                output={
                    "gap_analysis": result.to_dict(),
                    "summary": {
                        "total_gaps": result.total_gaps,
                        "critical_gaps": result.critical_gaps,
                        "coverage_score": result.coverage_score,
                        "data_freshness": result.data_freshness_score,
                        "monitoring_completeness": result.monitoring_completeness,
                    },
                },
            )

            return agent_result

        except Exception as e:
            return AgentResult(
                agent_name=self.name, success=False, error=f"Failed to detect gaps: {str(e)}"
            )

    async def _detect_gaps(
        self,
        context: Context,
        scoring_result: Optional[ScoringResult] = None,
    ) -> GapAnalysisResult:
        """Perform comprehensive gap analysis."""
        result = GapAnalysisResult()

        if not context.entity:
            # No entity to analyze
            return result

        # Detect different types of gaps
        await self._detect_missing_signals(context, result)
        await self._detect_outdated_data(context, result)
        await self._detect_coverage_gaps(context, result)
        await self._detect_monitoring_gaps(context, result)
        await self._detect_correlation_gaps(context, result)

        # Calculate scores
        result.coverage_score = self._calculate_coverage_score(context, result)
        result.data_freshness_score = self._calculate_freshness_score(context)
        result.monitoring_completeness = self._calculate_monitoring_score(context, result)

        # Update gap counts
        self._update_gap_counts(result)

        return result

    async def _detect_missing_signals(self, context: Context, result: GapAnalysisResult) -> None:
        """Detect missing expected signals."""
        if not context.entity or not context.signals:
            return

        entity_type = context.entity.entity_type
        required_signals = self.entity_type_requirements.get(entity_type, [])

        if not required_signals:
            return

        # Get current signal types
        current_types = {s.signal_type for s in context.signals}

        # Find missing signal types
        missing_types = set(required_signals) - current_types

        for signal_type in missing_types:
            # Determine likely sources for this signal type
            likely_sources = self._get_likely_sources(signal_type)

            gap = DataGap(
                gap_type=GapType.MISSING_SIGNAL,
                title=f"Missing {signal_type} Data",
                description=f"Entity {context.entity.id} lacks {signal_type} signals which are expected for {entity_type} entities",
                severity=self._assess_missing_signal_severity(signal_type, entity_type),
                confidence=0.8,
                entity_id=context.entity.id,
                missing_source=likely_sources[0] if likely_sources else None,
                expected_signals=[signal_type],
                recommendations=self._generate_missing_signal_recommendations(
                    signal_type, likely_sources
                ),
                impact_score=self._calculate_missing_impact(signal_type, entity_type),
            )

            result.gaps.append(gap)

    async def _detect_outdated_data(self, context: Context, result: GapAnalysisResult) -> None:
        """Detect outdated data signals."""
        if not context.signals:
            return

        cutoff_time = datetime.utcnow() - timedelta(hours=self.max_data_age_hours)

        for signal in context.signals:
            if not signal.timestamp:
                # No timestamp - assume outdated
                gap = DataGap(
                    gap_type=GapType.OUTDATED_DATA,
                    title=f"Untimestamped {signal.signal_type} Data",
                    description=f"{signal.signal_type} signal from {signal.source} lacks timestamp - cannot assess freshness",
                    severity="medium",
                    confidence=0.9,
                    entity_id=signal.entity_id,
                    missing_source=signal.source,
                    recommendations=[
                        f"Configure {signal.source} to include timestamps",
                        "Implement data freshness monitoring",
                    ],
                    impact_score=0.5,
                )
                result.gaps.append(gap)
                continue

            if signal.timestamp < cutoff_time:
                age_hours = (datetime.utcnow() - signal.timestamp).total_seconds() / 3600

                gap = DataGap(
                    gap_type=GapType.OUTDATED_DATA,
                    title=f"Stale {signal.signal_type} Data",
                    description=f"{signal.signal_type} data is {age_hours:.1f} hours old (threshold: {self.max_data_age_hours}h)",
                    severity=self._assess_staleness_severity(age_hours, signal.signal_type),
                    confidence=0.8,
                    entity_id=signal.entity_id,
                    missing_source=signal.source,
                    recommendations=[
                        f"Update {signal.source} scanning frequency",
                        f"Schedule more frequent {signal.signal_type} scans",
                    ],
                    impact_score=min(1.0, age_hours / (self.max_data_age_hours * 2)),
                )
                result.gaps.append(gap)

    async def _detect_coverage_gaps(self, context: Context, result: GapAnalysisResult) -> None:
        """Detect coverage gaps in data sources."""
        if not context.signals:
            # No signals at all - major coverage gap
            gap = DataGap(
                gap_type=GapType.COVERAGE_GAP,
                title="No Data Coverage",
                description="Entity has no signals - complete lack of visibility",
                severity="critical",
                confidence=1.0,
                entity_id=context.entity.id if context.entity else None,
                missing_source="all",
                expected_signals=["VULNERABILITY", "ASSET", "NETWORK"],
                recommendations=[
                    "Deploy vulnerability scanner",
                    "Implement asset inventory",
                    "Add network monitoring",
                ],
                impact_score=1.0,
            )
            result.gaps.append(gap)
            return

        # Check for missing critical sources
        current_sources = {s.source for s in context.signals}
        missing_critical = self.critical_sources - current_sources

        for source in missing_critical:
            gap = DataGap(
                gap_type=GapType.COVERAGE_GAP,
                title=f"Missing {source} Coverage",
                description=f"Critical data source {source} is not providing data for this entity",
                severity="high",
                confidence=0.9,
                entity_id=context.entity.id if context.entity else None,
                missing_source=source,
                recommendations=[
                    f"Integrate {source} with CtxOS",
                    f"Configure {source} to monitor this entity",
                ],
                impact_score=0.8,
            )
            result.gaps.append(gap)

    async def _detect_monitoring_gaps(self, context: Context, result: GapAnalysisResult) -> None:
        """Detect monitoring completeness gaps."""
        if not context.entity:
            return

        entity_type = context.entity.entity_type

        # Check for basic monitoring requirements
        monitoring_requirements = {
            "host": ["availability", "performance", "security"],
            "domain": ["dns", "ssl", "reputation"],
            "application": ["availability", "security", "performance"],
            "network": ["traffic", "security", "availability"],
        }

        required_monitoring = monitoring_requirements.get(entity_type, [])

        # Infer current monitoring from signals
        current_monitoring = self._infer_monitoring_from_signals(context.signals)

        missing_monitoring = set(required_monitoring) - current_monitoring

        for monitoring_type in missing_monitoring:
            gap = DataGap(
                gap_type=GapType.MONITORING_GAP,
                title=f"Missing {monitoring_type.title()} Monitoring",
                description=f"{entity_type} entity lacks {monitoring_type} monitoring",
                severity="medium",
                confidence=0.7,
                entity_id=context.entity.id,
                recommendations=self._generate_monitoring_recommendations(
                    monitoring_type, entity_type
                ),
                impact_score=0.6,
            )
            result.gaps.append(gap)

    async def _detect_correlation_gaps(self, context: Context, result: GapAnalysisResult) -> None:
        """Detect correlation gaps between related signals."""
        if not context.signals or len(context.signals) < 2:
            return

        # Look for signals that should be correlated but aren't
        correlation_rules = [
            {
                "trigger_types": ["VULNERABILITY"],
                "expected_types": ["PORT", "SERVICE"],
                "description": "vulnerability with service context",
            },
            {
                "trigger_types": ["PORT"],
                "expected_types": ["SERVICE", "VULNERABILITY"],
                "description": "open port with service/vulnerability context",
            },
            {
                "trigger_types": ["SSL_CERTIFICATE"],
                "expected_types": ["DOMAIN", "SUBDOMAIN"],
                "description": "SSL certificate with domain context",
            },
        ]

        current_types = {s.signal_type for s in context.signals}

        for rule in correlation_rules:
            if any(t in current_types for t in rule["trigger_types"]):
                missing_correlations = set(rule["expected_types"]) - current_types

                if missing_correlations:
                    gap = DataGap(
                        gap_type=GapType.CORRELATION_GAP,
                        title=f"Missing {rule['description']} Correlation",
                        description=f"Found {rule['trigger_types']} signals but missing {rule['expected_types']} for complete analysis",
                        severity="low",
                        confidence=0.6,
                        entity_id=context.entity.id if context.entity else None,
                        recommendations=[
                            f"Enable {', '.join(missing_correlations)} data collection",
                            "Configure signal correlation rules",
                        ],
                        impact_score=0.3,
                    )
                    result.gaps.append(gap)

    def _get_likely_sources(self, signal_type: str) -> List[str]:
        """Get likely data sources for signal type."""
        source_mapping = {
            "VULNERABILITY": ["vulnerability_scanner", "nessus", "qualys"],
            "PORT": ["network_scanner", "nmap", "masscan"],
            "SERVICE": ["network_scanner", "asset_inventory"],
            "DNS": ["dns_monitor", "passive_dns"],
            "SSL_CERTIFICATE": ["ssl_monitor", "certificate_transparency"],
            "SUBDOMAIN": ["subdomain_scanner", "asset_inventory"],
            "WHOIS": ["whois_monitor", "domain_registrar"],
            "CONFIGURATION": ["config_scanner", "compliance_monitor"],
            "DEPENDENCY": ["dependency_scanner", "sca_tool"],
            "ACCESS_LOG": ["web_server", "siem", "log_analyzer"],
            "TRAFFIC": ["network_monitor", "ids", "firewall"],
            "FIREWALL": ["firewall", "network_monitor"],
        }

        return source_mapping.get(signal_type, ["unknown_source"])

    def _assess_missing_signal_severity(self, signal_type: str, entity_type: str) -> str:
        """Assess severity of missing signal type."""
        # Critical signal types for any entity
        critical_signals = {"VULNERABILITY", "ASSET", "CONFIGURATION"}
        if signal_type in critical_signals:
            return "critical"

        # High importance signals
        high_signals = {"PORT", "SERVICE", "DNS", "SSL_CERTIFICATE"}
        if signal_type in high_signals:
            return "high"

        # Entity-specific critical signals
        entity_critical = {
            "host": {"VULNERABILITY", "PORT", "SERVICE"},
            "domain": {"DNS", "SSL_CERTIFICATE", "SUBDOMAIN"},
            "application": {"VULNERABILITY", "DEPENDENCY", "ACCESS_LOG"},
        }

        if signal_type in entity_critical.get(entity_type, set()):
            return "high"

        return "medium"

    def _assess_staleness_severity(self, age_hours: float, signal_type: str) -> str:
        """Assess severity based on data staleness."""
        # Critical signal types get severe faster
        if signal_type in {"VULNERABILITY", "THREAT", "INCIDENT"}:
            if age_hours > 48:  # 2 days
                return "critical"
            elif age_hours > 24:  # 1 day
                return "high"

        # General staleness assessment
        if age_hours > 336:  # 2 weeks
            return "critical"
        elif age_hours > 168:  # 1 week
            return "high"
        elif age_hours > 72:  # 3 days
            return "medium"

        return "low"

    def _generate_missing_signal_recommendations(
        self,
        signal_type: str,
        likely_sources: List[str],
    ) -> List[str]:
        """Generate recommendations for missing signals."""
        recommendations = []

        if likely_sources and likely_sources[0] != "unknown_source":
            for source in likely_sources[:2]:  # Top 2 sources
                recommendations.append(f"Integrate {source} for {signal_type} data")

        # General recommendations
        recommendations.extend(
            [
                f"Configure {signal_type} scanning for this entity",
                "Review data collection schedules",
            ]
        )

        return recommendations

    def _generate_monitoring_recommendations(
        self,
        monitoring_type: str,
        entity_type: str,
    ) -> List[str]:
        """Generate monitoring recommendations."""
        recommendations = []

        monitoring_solutions = {
            "availability": [
                "Deploy uptime monitoring",
                "Configure health checks",
                "Set up alerting for downtime",
            ],
            "performance": [
                "Implement performance monitoring",
                "Track response times and resource usage",
                "Set performance baselines and alerts",
            ],
            "security": [
                "Deploy security monitoring",
                "Configure intrusion detection",
                "Set up security event logging",
            ],
            "dns": [
                "Configure DNS monitoring",
                "Track DNS resolution and changes",
                "Monitor for DNS attacks",
            ],
            "ssl": [
                "Implement SSL certificate monitoring",
                "Track certificate expiration",
                "Monitor for SSL misconfigurations",
            ],
            "reputation": [
                "Configure reputation monitoring",
                "Track blacklisting status",
                "Monitor threat intelligence feeds",
            ],
        }

        return monitoring_solutions.get(
            monitoring_type, [f"Implement {monitoring_type} monitoring"]
        )

    def _calculate_missing_impact(self, signal_type: str, entity_type: str) -> float:
        """Calculate impact score for missing signal."""
        base_impact = {
            "VULNERABILITY": 1.0,
            "THREAT": 0.9,
            "INCIDENT": 0.9,
            "PORT": 0.7,
            "SERVICE": 0.6,
            "CONFIGURATION": 0.6,
            "DNS": 0.5,
            "SSL_CERTIFICATE": 0.5,
        }

        impact = base_impact.get(signal_type, 0.3)

        # Entity type modifier
        entity_modifiers = {
            "host": 1.0,
            "application": 0.9,
            "domain": 0.8,
            "network": 0.7,
        }

        modifier = entity_modifiers.get(entity_type, 0.5)

        return min(1.0, impact * modifier)

    def _infer_monitoring_from_signals(self, signals: List[Signal]) -> Set[str]:
        """Infer current monitoring from available signals."""
        monitoring_types = set()

        for signal in signals:
            if signal.signal_type in {"VULNERABILITY", "THREAT", "INCIDENT"}:
                monitoring_types.add("security")
            elif signal.signal_type in {"PORT", "SERVICE", "TRAFFIC"}:
                monitoring_types.add("availability")
            elif signal.signal_type in {"PERFORMANCE", "RESPONSE_TIME"}:
                monitoring_types.add("performance")
            elif signal.signal_type in {"DNS", "DOMAIN"}:
                monitoring_types.add("dns")
            elif signal.signal_type in {"SSL_CERTIFICATE"}:
                monitoring_types.add("ssl")
            elif signal.signal_type in {"REPUTATION", "BLACKLIST"}:
                monitoring_types.add("reputation")

        return monitoring_types

    def _calculate_coverage_score(self, context: Context, result: GapAnalysisResult) -> float:
        """Calculate data coverage score (0-100)."""
        if not context.entity:
            return 0.0

        entity_type = context.entity.entity_type
        required_signals = self.entity_type_requirements.get(entity_type, [])

        if not required_signals:
            return 100.0  # No requirements = full coverage

        if not context.signals:
            return 0.0

        current_types = {s.signal_type for s in context.signals}
        coverage = len(current_types & set(required_signals)) / len(required_signals)

        return coverage * 100.0

    def _calculate_freshness_score(self, context: Context) -> float:
        """Calculate data freshness score (0-100)."""
        if not context.signals:
            return 0.0

        cutoff_time = datetime.utcnow() - timedelta(hours=self.max_data_age_hours)
        fresh_signals = 0

        for signal in context.signals:
            if signal.timestamp and signal.timestamp >= cutoff_time:
                fresh_signals += 1

        return (fresh_signals / len(context.signals)) * 100.0

    def _calculate_monitoring_score(self, context: Context, result: GapAnalysisResult) -> float:
        """Calculate monitoring completeness score (0-100)."""
        if not context.entity:
            return 0.0

        # Base score on coverage and freshness
        coverage_weight = 0.5
        freshness_weight = 0.3
        gap_weight = 0.2

        coverage_score = result.coverage_score / 100.0
        freshness_score = result.data_freshness_score / 100.0

        # Penalty for gaps (inverse of gap ratio)
        gap_penalty = min(1.0, result.total_gaps / 10.0)  # Normalize to 0-1
        gap_score = 1.0 - gap_penalty

        total_score = (
            coverage_score * coverage_weight
            + freshness_score * freshness_weight
            + gap_score * gap_weight
        )

        return total_score * 100.0

    def _update_gap_counts(self, result: GapAnalysisResult) -> None:
        """Update gap count statistics."""
        result.total_gaps = len(result.gaps)

        for gap in result.gaps:
            if gap.severity == "critical":
                result.critical_gaps += 1
            elif gap.severity == "high":
                result.high_gaps += 1
            elif gap.severity == "medium":
                result.medium_gaps += 1
            elif gap.severity == "low":
                result.low_gaps += 1
