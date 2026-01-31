"""
Context Summarizer Agent - Reduce complexity to key findings.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re

from core.models.context import Context
from core.models.entity import Entity
from core.models.signal import Signal
from core.scoring.risk import ScoringResult
from agents.base_agent_async import BaseAgentAsync, AgentResult
from agents.audit_system.audit_logger import AuditLevel


@dataclass
class SummaryItem:
    """Single summary item."""

    category: str
    title: str
    description: str
    severity: str
    confidence: float
    source: str
    entity_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "confidence": self.confidence,
            "source": self.source,
            "entity_id": self.entity_id,
        }


@dataclass
class ContextSummary:
    """Complete context summary."""

    entity_summary: Dict[str, Any]
    key_findings: List[SummaryItem] = field(default_factory=list)
    risk_highlights: List[SummaryItem] = field(default_factory=list)
    exposure_highlights: List[SummaryItem] = field(default_factory=list)
    anomaly_highlights: List[SummaryItem] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    summary_score: float = 0.0
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_summary": self.entity_summary,
            "key_findings": [item.to_dict() for item in self.key_findings],
            "risk_highlights": [item.to_dict() for item in self.risk_highlights],
            "exposure_highlights": [item.to_dict() for item in self.exposure_highlights],
            "anomaly_highlights": [item.to_dict() for item in self.anomaly_highlights],
            "recommendations": self.recommendations,
            "summary_score": self.summary_score,
            "confidence": self.confidence,
        }


class ContextSummarizer(BaseAgentAsync):
    """Agent that summarizes complex context into key findings."""

    def __init__(
        self,
        name: str = "ContextSummarizer",
        version: str = "1.0.0",
        max_risks: int = 5,
        max_exposures: int = 5,
        max_anomalies: int = 3,
        min_confidence: float = 0.3,
    ):
        """Initialize context summarizer.

        Args:
            name: Agent name
            version: Agent version
            max_risks: Maximum risk items to include
            max_exposures: Maximum exposure items to include
            max_anomalies: Maximum anomaly items to include
            min_confidence: Minimum confidence threshold
        """
        super().__init__(name, version)
        self.max_risks = max_risks
        self.max_exposures = max_exposures
        self.max_anomalies = max_anomalies
        self.min_confidence = min_confidence

        # Severity weights for scoring
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
        """Analyze context and generate summary.

        Args:
            context: Input context with entity and signals
            scoring_result: Optional scoring result from engines

        Returns:
            AgentResult with context summary
        """
        try:
            # Generate summary
            summary = await self._generate_summary(context, scoring_result)

            # Create result
            result = AgentResult(
                agent_name=self.name,
                success=True,
                output={
                    "summary": summary.to_dict(),
                    "stats": {
                        "total_signals": len(context.signals) if context.signals else 0,
                        "risk_items": len(summary.risk_highlights),
                        "exposure_items": len(summary.exposure_highlights),
                        "anomaly_items": len(summary.anomaly_highlights),
                        "recommendations": len(summary.recommendations),
                    },
                },
            )

            return result

        except Exception as e:
            return AgentResult(
                agent_name=self.name, success=False, error=f"Failed to generate summary: {str(e)}"
            )

    async def _generate_summary(
        self,
        context: Context,
        scoring_result: Optional[ScoringResult] = None,
    ) -> ContextSummary:
        """Generate comprehensive context summary."""
        summary = ContextSummary(
            entity_summary=self._summarize_entity(context.entity),
            confidence=self._calculate_confidence(context, scoring_result),
        )

        # Process signals
        if context.signals:
            await self._process_signals(context.signals, summary)

        # Process scoring results
        if scoring_result:
            await self._process_scoring_result(scoring_result, summary)

        # Generate recommendations
        summary.recommendations = self._generate_recommendations(summary)

        # Calculate overall summary score
        summary.summary_score = self._calculate_summary_score(summary)

        return summary

    def _summarize_entity(self, entity: Optional[Entity]) -> Dict[str, Any]:
        """Summarize entity information."""
        if not entity:
            return {"status": "no_entity"}

        return {
            "id": entity.id,
            "type": entity.entity_type,
            "name": entity.name,
            "description": entity.description,
            "properties": entity.properties or {},
            "criticality": self._assess_entity_criticality(entity),
        }

    def _assess_entity_criticality(self, entity: Entity) -> str:
        """Assess entity criticality based on type and properties."""
        # Critical entity types
        critical_types = {"domain", "host", "application", "database"}

        if entity.entity_type in critical_types:
            # Check for critical properties
            props = entity.properties or {}

            # Production indicators
            if props.get("environment") == "production":
                return "critical"

            # Public-facing indicators
            if props.get("public", False) or props.get("exposed", False):
                return "high"

            # High-value indicators
            if props.get("tier") in {"primary", "core", "essential"}:
                return "high"

            return "medium"

        return "low"

    async def _process_signals(self, signals: List[Signal], summary: ContextSummary) -> None:
        """Process and categorize signals."""
        risk_signals = []
        exposure_signals = []
        anomaly_signals = []

        for signal in signals:
            # Categorize by signal type and severity
            if signal.signal_type in {"VULNERABILITY", "THREAT", "INCIDENT"}:
                risk_signals.append(signal)
            elif signal.signal_type in {"EXPOSURE", "SERVICE", "PORT"}:
                exposure_signals.append(signal)
            elif signal.signal_type in {"ANOMALY", "DRIFT", "CHANGE"}:
                anomaly_signals.append(signal)

        # Process each category
        summary.risk_highlights = self._process_risk_signals(risk_signals)
        summary.exposure_highlights = self._process_exposure_signals(exposure_signals)
        summary.anomaly_highlights = self._process_anomaly_signals(anomaly_signals)

        # Add key findings from all signals
        all_signals = risk_signals + exposure_signals + anomaly_signals
        summary.key_findings = self._extract_key_findings(all_signals)

    def _process_risk_signals(self, signals: List[Signal]) -> List[SummaryItem]:
        """Process risk-related signals."""
        items = []

        # Sort by severity
        severity_order = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
        signals.sort(key=lambda s: severity_order.get(s.severity.lower(), 0), reverse=True)

        for signal in signals[: self.max_risks]:
            confidence = self._calculate_signal_confidence(signal)
            if confidence >= self.min_confidence:
                item = SummaryItem(
                    category="risk",
                    title=self._create_signal_title(signal),
                    description=signal.description or "",
                    severity=signal.severity,
                    confidence=confidence,
                    source=signal.source,
                    entity_id=signal.entity_id,
                )
                items.append(item)

        return items

    def _process_exposure_signals(self, signals: List[Signal]) -> List[SummaryItem]:
        """Process exposure-related signals."""
        items = []

        # Sort by exposure level
        signals.sort(key=lambda s: self._calculate_exposure_score(s), reverse=True)

        for signal in signals[: self.max_exposures]:
            confidence = self._calculate_signal_confidence(signal)
            if confidence >= self.min_confidence:
                item = SummaryItem(
                    category="exposure",
                    title=self._create_signal_title(signal),
                    description=signal.description or "",
                    severity=signal.severity,
                    confidence=confidence,
                    source=signal.source,
                    entity_id=signal.entity_id,
                )
                items.append(item)

        return items

    def _process_anomaly_signals(self, signals: List[Signal]) -> List[SummaryItem]:
        """Process anomaly-related signals."""
        items = []

        # Sort by anomaly severity
        signals.sort(key=lambda s: self._calculate_anomaly_score(s), reverse=True)

        for signal in signals[: self.max_anomalies]:
            confidence = self._calculate_signal_confidence(signal)
            if confidence >= self.min_confidence:
                item = SummaryItem(
                    category="anomaly",
                    title=self._create_signal_title(signal),
                    description=signal.description or "",
                    severity=signal.severity,
                    confidence=confidence,
                    source=signal.source,
                    entity_id=signal.entity_id,
                )
                items.append(item)

        return items

    def _extract_key_findings(self, signals: List[Signal]) -> List[SummaryItem]:
        """Extract most important findings from all signals."""
        findings = []

        # Look for patterns and critical issues
        critical_signals = [s for s in signals if s.severity.lower() == "critical"]
        if critical_signals:
            finding = SummaryItem(
                category="critical_finding",
                title=f"{len(critical_signals)} Critical Issues Detected",
                description=f"Immediate attention required for {len(critical_signals)} critical security issues",
                severity="critical",
                confidence=1.0,
                source="context_summarizer",
            )
            findings.append(finding)

        # Look for multiple sources indicating same issue
        source_counts = {}
        for signal in signals:
            key = f"{signal.signal_type}:{signal.severity}"
            source_counts[key] = source_counts.get(key, 0) + 1

        for (sig_type, severity), count in source_counts.items():
            if count >= 3:  # Multiple sources
                finding = SummaryItem(
                    category="pattern",
                    title=f"Multiple {severity} {sig_type} Indicators",
                    description=f"Found {count} indicators of {severity} {sig_type} from multiple sources",
                    severity=severity,
                    confidence=min(0.9, 0.3 + (count * 0.1)),
                    source="context_summarizer",
                )
                findings.append(finding)

        return findings[:5]  # Limit key findings

    async def _process_scoring_result(
        self,
        scoring_result: ScoringResult,
        summary: ContextSummary,
    ) -> None:
        """Process scoring results into summary."""
        # Add scoring insights to key findings
        if scoring_result.score >= 80:
            finding = SummaryItem(
                category="scoring",
                title=f"High Risk Score: {scoring_result.score}",
                description=f"Entity scored {scoring_result.score}/100 indicating severe risk",
                severity=scoring_result.severity,
                confidence=0.9,
                source="scoring_engine",
            )
            summary.key_findings.append(finding)

        # Add recommendations from scoring
        if scoring_result.recommendations:
            summary.recommendations.extend(scoring_result.recommendations)

    def _create_signal_title(self, signal: Signal) -> str:
        """Create descriptive title for signal."""
        # Clean up signal type
        signal_type = signal.signal_type.replace("_", " ").title()

        # Extract key info from description
        description = signal.description or ""

        # Look for specific patterns
        if "port" in description.lower():
            port_match = re.search(r"port\s*(\d+)", description.lower())
            if port_match:
                return f"{signal_type} on Port {port_match.group(1)}"

        if "vulnerability" in description.lower():
            vuln_match = re.search(r"(CVE-\d{4}-\d+)", description.upper())
            if vuln_match:
                return f"{signal_type}: {vuln_match.group(1)}"

        # Default title
        return f"{signal_type} Detected"

    def _calculate_signal_confidence(self, signal: Signal) -> float:
        """Calculate confidence score for signal."""
        base_confidence = 0.5

        # Boost confidence based on severity
        severity_boost = self.severity_weights.get(signal.severity.lower(), 0.3)

        # Boost confidence based on source reliability
        source_boost = {
            "vulnerability_scanner": 0.3,
            "siem": 0.25,
            "ids": 0.2,
            "manual": 0.15,
            "automated": 0.1,
        }.get(signal.source.lower(), 0.1)

        # Time decay (recent signals are more reliable)
        if signal.timestamp:
            age_hours = (datetime.utcnow() - signal.timestamp).total_seconds() / 3600
            time_decay = max(0, 1 - (age_hours / 168))  # 1 week decay
        else:
            time_decay = 0.5

        confidence = base_confidence + severity_boost + source_boost + (time_decay * 0.1)
        return min(1.0, confidence)

    def _calculate_exposure_score(self, signal: Signal) -> float:
        """Calculate exposure score for signal."""
        score = 0.0

        # Signal type weights
        type_weights = {
            "EXPOSURE": 1.0,
            "SERVICE": 0.8,
            "PORT": 0.6,
            "SUBDOMAIN": 0.4,
        }

        score += type_weights.get(signal.signal_type, 0.3)

        # Severity weight
        score += self.severity_weights.get(signal.severity.lower(), 0.3)

        return score

    def _calculate_anomaly_score(self, signal: Signal) -> float:
        """Calculate anomaly score for signal."""
        score = 0.0

        # Anomaly type weights
        type_weights = {
            "ANOMALY": 1.0,
            "DRIFT": 0.9,
            "CHANGE": 0.7,
            "UNUSUAL": 0.5,
        }

        score += type_weights.get(signal.signal_type, 0.3)

        # Severity weight
        score += self.severity_weights.get(signal.severity.lower(), 0.3)

        return score

    def _calculate_confidence(
        self,
        context: Context,
        scoring_result: Optional[ScoringResult] = None,
    ) -> float:
        """Calculate overall summary confidence."""
        confidence = 0.3  # Base confidence

        # Signal count contribution
        if context.signals:
            signal_confidence = min(0.4, len(context.signals) * 0.05)
            confidence += signal_confidence

        # Scoring result contribution
        if scoring_result:
            confidence += 0.3

        # Entity information contribution
        if context.entity:
            confidence += 0.2

        return min(1.0, confidence)

    def _generate_recommendations(self, summary: ContextSummary) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Risk-based recommendations
        critical_risks = [r for r in summary.risk_highlights if r.severity == "critical"]
        if critical_risks:
            recommendations.append(
                f"URGENT: Address {len(critical_risks)} critical security risks immediately"
            )

        high_risks = [r for r in summary.risk_highlights if r.severity == "high"]
        if high_risks:
            recommendations.append(
                f"HIGH: Review and remediate {len(high_risks)} high-severity risks within 7 days"
            )

        # Exposure-based recommendations
        if summary.exposure_highlights:
            recommendations.append("Review attack surface exposure and implement security controls")

        # Anomaly-based recommendations
        if summary.anomaly_highlights:
            recommendations.append(
                "Investigate detected anomalies for potential security incidents"
            )

        # General recommendations
        if summary.summary_score >= 70:
            recommendations.append(
                "Consider implementing additional security monitoring and controls"
            )

        return recommendations[:5]  # Limit recommendations

    def _calculate_summary_score(self, summary: ContextSummary) -> float:
        """Calculate overall summary score (0-100)."""
        score = 0.0

        # Risk contribution (40% weight)
        if summary.risk_highlights:
            risk_score = sum(
                self.severity_weights.get(r.severity.lower(), 0.3) * r.confidence
                for r in summary.risk_highlights
            )
            score += (risk_score / len(summary.risk_highlights)) * 40

        # Exposure contribution (30% weight)
        if summary.exposure_highlights:
            exposure_score = sum(
                self.severity_weights.get(e.severity.lower(), 0.3) * e.confidence
                for e in summary.exposure_highlights
            )
            score += (exposure_score / len(summary.exposure_highlights)) * 30

        # Anomaly contribution (20% weight)
        if summary.anomaly_highlights:
            anomaly_score = sum(
                self.severity_weights.get(a.severity.lower(), 0.3) * a.confidence
                for a in summary.anomaly_highlights
            )
            score += (anomaly_score / len(summary.anomaly_highlights)) * 20

        # Entity criticality contribution (10% weight)
        entity_crit = summary.entity_summary.get("criticality", "low")
        crit_weights = {"critical": 10, "high": 8, "medium": 5, "low": 2}
        score += crit_weights.get(entity_crit, 2)

        return min(100.0, score)
