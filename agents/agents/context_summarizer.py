"""
Context Summarizer Agent - Extracts key findings from entity/signal data.

Analyzes collected entities and signals to produce structured summaries
highlighting top risks, exposure patterns, and configuration anomalies.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.models.context import Context
from core.models.entity import Entity
from core.scoring.risk import ScoringResult
from agents.base_agent_async import BaseAgentAsync, AgentResult


class ContextSummarizer(BaseAgentAsync):
    """Summarizes context data into actionable insights."""

    def __init__(
        self,
        name: str = "context_summarizer",
        version: str = "1.0.0",
        max_risks: int = 5,
        max_exposures: int = 5,
        max_anomalies: int = 3,
    ):
        """Initialize Context Summarizer.

        Args:
            name: Agent name
            version: Agent version
            max_risks: Maximum risks to include
            max_exposures: Maximum exposures to include
            max_anomalies: Maximum anomalies to include
        """
        super().__init__(name, version)
        self.max_risks = max_risks
        self.max_exposures = max_exposures
        self.max_anomalies = max_anomalies

    async def analyze(
        self,
        context: Context,
        scoring_result: Optional[ScoringResult] = None,
    ) -> AgentResult:
        """Analyze context and generate summary.

        Args:
            context: Input context with entities and signals
            scoring_result: Optional scoring result from engines

        Returns:
            AgentResult with summary data
        """
        try:
            # Extract entity information
            entity = context.entity
            if not entity:
                return AgentResult(
                    agent_name=self.name,
                    success=False,
                    error="No entity in context",
                )

            # Get signals for this entity
            signals = context.signals if context.signals else []

            # Generate summary sections
            summary = {
                "entity_id": entity.id,
                "entity_type": entity.entity_type,
                "entity_name": entity.name,
                "summary_timestamp": datetime.utcnow().isoformat(),
            }

            # Top risks
            top_risks = await self._extract_top_risks(entity, signals, scoring_result)
            summary["top_risks"] = top_risks

            # Exposure highlights
            exposure_highlights = await self._extract_exposure_highlights(
                entity, signals, scoring_result
            )
            summary["exposure_highlights"] = exposure_highlights

            # Configuration anomalies
            anomalies = await self._extract_anomalies(entity, signals, scoring_result)
            summary["configuration_anomalies"] = anomalies

            # Overall assessment
            assessment = await self._generate_assessment(top_risks, exposure_highlights, anomalies)
            summary["overall_assessment"] = assessment

            # Signal statistics
            summary["signal_statistics"] = {
                "total_signals": len(signals),
                "signal_types": self._count_signal_types(signals),
                "critical_count": sum(1 for s in signals if s.severity == "CRITICAL"),
                "high_count": sum(1 for s in signals if s.severity == "HIGH"),
            }

            return AgentResult(
                agent_name=self.name,
                success=True,
                output=summary,
            )

        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                success=False,
                error=f"Summarization failed: {str(e)}",
            )

    async def _extract_top_risks(
        self,
        entity: Entity,
        signals: List[Any],
        scoring_result: Optional[ScoringResult],
    ) -> List[Dict[str, Any]]:
        """Extract top risks from entity/signals.

        Args:
            entity: Entity to analyze
            signals: List of signals
            scoring_result: Optional scoring result

        Returns:
            List of top risks (limited by max_risks)
        """
        risks = []

        # Include scoring result risk if available
        if scoring_result and scoring_result.engine_name == "risk":
            risks.append(
                {
                    "source": "risk_engine",
                    "severity": scoring_result.severity,
                    "score": scoring_result.score,
                    "description": f"Risk score: {scoring_result.score:.0f}",
                    "timestamp": scoring_result.timestamp.isoformat(),
                }
            )

        # Extract critical/high severity signals
        for signal in signals:
            if signal.severity in ["CRITICAL", "HIGH"]:
                risks.append(
                    {
                        "source": signal.source,
                        "signal_type": signal.signal_type,
                        "severity": signal.severity,
                        "description": signal.description or str(signal.signal_type),
                        "timestamp": signal.timestamp.isoformat(),
                    }
                )

        # Sort by severity and return top N
        severity_order = {"CRITICAL": 0, "HIGH": 1}
        risks.sort(key=lambda x: severity_order.get(x["severity"], 2))

        return risks[: self.max_risks]

    async def _extract_exposure_highlights(
        self,
        entity: Entity,
        signals: List[Any],
        scoring_result: Optional[ScoringResult],
    ) -> List[Dict[str, Any]]:
        """Extract exposure highlights.

        Args:
            entity: Entity to analyze
            signals: List of signals
            scoring_result: Optional scoring result

        Returns:
            List of exposure highlights
        """
        exposures = []

        # Include exposure engine score if available
        if scoring_result and scoring_result.engine_name == "exposure":
            exposures.append(
                {
                    "type": "public_exposure",
                    "severity": scoring_result.severity,
                    "score": scoring_result.score,
                    "description": f"Exposure score: {scoring_result.score:.0f}",
                    "factors": scoring_result.factors or {},
                }
            )

        # Look for exposure-related signals
        exposure_signal_types = {
            "OPEN_PORT": "Open Network Port",
            "DOMAIN_REGISTRATION": "Registered Domain",
            "CERTIFICATE": "Public Certificate",
            "HTTP_HEADER": "Web Service Headers",
        }

        for signal in signals:
            if signal.signal_type in exposure_signal_types:
                exposures.append(
                    {
                        "type": exposure_signal_types.get(signal.signal_type, signal.signal_type),
                        "source": signal.source,
                        "description": signal.description or "",
                        "timestamp": signal.timestamp.isoformat(),
                    }
                )

        return exposures[: self.max_exposures]

    async def _extract_anomalies(
        self,
        entity: Entity,
        signals: List[Any],
        scoring_result: Optional[ScoringResult],
    ) -> List[Dict[str, Any]]:
        """Extract configuration anomalies.

        Args:
            entity: Entity to analyze
            signals: List of signals
            scoring_result: Optional scoring result

        Returns:
            List of anomalies
        """
        anomalies = []

        # Include drift engine score if available
        if scoring_result and scoring_result.engine_name == "drift":
            if scoring_result.score > 50:  # High drift = anomaly
                anomalies.append(
                    {
                        "type": "configuration_drift",
                        "severity": scoring_result.severity,
                        "score": scoring_result.score,
                        "description": f"Configuration has drifted from baseline",
                        "factors": scoring_result.factors or {},
                    }
                )

        # Look for anomaly-related signals
        anomaly_signal_types = {
            "CONFIGURATION": "Configuration Change",
            "DNS_RECORD": "DNS Configuration",
        }

        for signal in signals:
            if signal.signal_type in anomaly_signal_types:
                anomalies.append(
                    {
                        "type": anomaly_signal_types.get(signal.signal_type, signal.signal_type),
                        "source": signal.source,
                        "description": signal.description or "",
                        "timestamp": signal.timestamp.isoformat(),
                    }
                )

        return anomalies[: self.max_anomalies]

    async def _generate_assessment(
        self,
        top_risks: List[Dict[str, Any]],
        exposures: List[Dict[str, Any]],
        anomalies: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate overall assessment.

        Args:
            top_risks: List of top risks
            exposures: List of exposures
            anomalies: List of anomalies

        Returns:
            Assessment with priority level
        """
        # Determine priority based on findings
        priority = "LOW"
        critical_count = sum(
            1 for risk in top_risks if risk.get("severity") in ["CRITICAL", "HIGH"]
        )

        if critical_count >= 3:
            priority = "CRITICAL"
        elif critical_count >= 2:
            priority = "HIGH"
        elif critical_count >= 1 or len(exposures) >= 3 or len(anomalies) >= 2:
            priority = "MEDIUM"

        # Generate recommendation
        recommendation = self._get_recommendation(
            priority, critical_count, len(exposures), len(anomalies)
        )

        return {
            "priority": priority,
            "critical_findings": critical_count,
            "total_findings": len(top_risks) + len(exposures) + len(anomalies),
            "recommendation": recommendation,
        }

    def _get_recommendation(
        self,
        priority: str,
        critical_count: int,
        exposure_count: int,
        anomaly_count: int,
    ) -> str:
        """Generate recommendation based on findings.

        Args:
            priority: Priority level
            critical_count: Count of critical findings
            exposure_count: Count of exposures
            anomaly_count: Count of anomalies

        Returns:
            Recommendation text
        """
        if priority == "CRITICAL":
            return "Immediate investigation and remediation required. Address all critical findings within 24 hours."
        elif priority == "HIGH":
            if critical_count > 0:
                return f"Urgent attention needed. {critical_count} critical finding(s) require immediate action."
            return "High priority assessment. Review and prioritize remediation within 48 hours."
        elif priority == "MEDIUM":
            return "Schedule assessment and remediation within one week."
        else:
            return "Continue routine monitoring. No immediate action required."

    def _count_signal_types(self, signals: List[Any]) -> Dict[str, int]:
        """Count signals by type.

        Args:
            signals: List of signals

        Returns:
            Dictionary with signal type counts
        """
        counts = {}
        for signal in signals:
            signal_type = signal.signal_type if hasattr(signal, "signal_type") else "unknown"
            counts[signal_type] = counts.get(signal_type, 0) + 1
        return counts
