"""
Risk Engine - Assess risk of entities based on signals and properties.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from engines.base_engine import BaseEngine, ScoringResult, ScoringUtils
from core.models import Entity, Signal, EntityType, SignalType, SignalSeverity


@dataclass
class RiskFactors:
    """Risk assessment factors."""
    vulnerability_count: int = 0
    open_ports: int = 0
    exposed_credentials: int = 0
    suspicious_activity: int = 0
    data_breach_mentions: int = 0
    malware_indicators: int = 0
    certificate_issues: int = 0
    configuration_issues: int = 0
    age_days: int = 0  # Entity age
    last_seen_days: int = 0  # Days since last seen


class RiskEngine(BaseEngine):
    """Risk scoring engine for security entities."""

    DEFAULT_CONFIG = {
        "vulnerability_weight": 25,
        "open_ports_weight": 15,
        "exposure_weight": 20,
        "activity_weight": 15,
        "age_decay": 0.1,  # Reduce score by 10% per 100 days old
        "severity_multipliers": {
            "critical": 1.5,
            "high": 1.2,
            "medium": 1.0,
            "low": 0.8,
            "info": 0.5,
        },
    }

    def __init__(self):
        """Initialize Risk Engine."""
        super().__init__("RiskEngine", version="1.0.0")
        self.config = self.DEFAULT_CONFIG.copy()

    def score(self, entity: Entity, context: Any = None) -> ScoringResult:
        """Score entity risk.
        
        Args:
            entity: Entity to score
            context: Optional context with signals
            
        Returns:
            ScoringResult with risk score
        """
        self.run_count += 1
        self.last_run = datetime.utcnow()

        try:
            # Extract risk factors
            factors = self._extract_risk_factors(entity, context)
            
            # Calculate base scores
            scores = self._calculate_component_scores(factors)
            
            # Aggregate with weights
            base_score = self._aggregate_scores(scores)
            
            # Apply decay for old entities
            final_score = self._apply_age_decay(base_score, factors.age_days)
            
            # Determine severity
            severity = ScoringUtils.score_to_severity(final_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(factors, final_score)
            
            return ScoringResult(
                engine_name=self.name,
                entity_id=entity.id,
                score=final_score,
                severity=severity,
                details={
                    "entity_type": entity.entity_type.value,
                    "entity_name": entity.name,
                    "factors": {
                        "vulnerability_count": factors.vulnerability_count,
                        "open_ports": factors.open_ports,
                        "exposed_credentials": factors.exposed_credentials,
                        "suspicious_activity": factors.suspicious_activity,
                        "data_breach_mentions": factors.data_breach_mentions,
                        "malware_indicators": factors.malware_indicators,
                    },
                },
                metrics=scores,
                recommendations=recommendations,
            )
        except Exception as e:
            self.error_count += 1
            self.status = BaseEngine.EngineStatus.ERROR
            raise Exception(f"Risk scoring failed: {str(e)}")

    def _extract_risk_factors(self, entity: Entity, context: Any) -> RiskFactors:
        """Extract risk factors from entity and context.
        
        Args:
            entity: Entity to analyze
            context: Optional context with signals
            
        Returns:
            RiskFactors object
        """
        factors = RiskFactors()
        
        # Calculate entity age
        if entity.discovered_at:
            factors.age_days = (datetime.utcnow() - entity.discovered_at).days
        
        if entity.last_seen_at:
            factors.last_seen_days = (datetime.utcnow() - entity.last_seen_at).days
        
        # Extract signals if context provided
        if context and hasattr(context, 'get_signals_for_entity'):
            signals = context.get_signals_for_entity(entity.id)
            
            for signal in signals:
                if signal.signal_type == SignalType.VULNERABILITY:
                    factors.vulnerability_count += 1
                elif signal.signal_type == SignalType.OPEN_PORT:
                    factors.open_ports += 1
                elif signal.signal_type == SignalType.CREDENTIAL_EXPOSURE:
                    factors.exposed_credentials += 1
                elif signal.signal_type == SignalType.SUSPICIOUS_ACTIVITY:
                    factors.suspicious_activity += 1
                elif signal.signal_type == SignalType.DATA_BREACH:
                    factors.data_breach_mentions += 1
                elif signal.signal_type == SignalType.MALWARE:
                    factors.malware_indicators += 1
                elif signal.signal_type == SignalType.CERTIFICATE:
                    factors.certificate_issues += 1
                elif signal.signal_type == SignalType.CONFIGURATION:
                    factors.configuration_issues += 1
        
        return factors

    def _calculate_component_scores(self, factors: RiskFactors) -> Dict[str, float]:
        """Calculate component risk scores.
        
        Args:
            factors: RiskFactors object
            
        Returns:
            Dictionary of component scores
        """
        scores = {}
        
        # Vulnerability score (0-100)
        vuln_score = min(factors.vulnerability_count * 10, 100)
        scores["vulnerability"] = vuln_score
        
        # Open ports score (0-100)
        ports_score = min(factors.open_ports * 15, 100)
        scores["open_ports"] = ports_score
        
        # Exposure score (0-100)
        exposure_factors = (
            factors.exposed_credentials * 30 +
            factors.data_breach_mentions * 25 +
            factors.certificate_issues * 20
        )
        exposure_score = min(exposure_factors, 100)
        scores["exposure"] = exposure_score
        
        # Activity score (0-100)
        activity_factors = (
            factors.suspicious_activity * 25 +
            factors.malware_indicators * 30 +
            factors.configuration_issues * 15
        )
        activity_score = min(activity_factors, 100)
        scores["activity"] = activity_score
        
        return scores

    def _aggregate_scores(self, scores: Dict[str, float]) -> float:
        """Aggregate component scores with weights.
        
        Args:
            scores: Component scores
            
        Returns:
            Aggregated score
        """
        weighted_scores = [
            scores.get("vulnerability", 0) * (self.config["vulnerability_weight"] / 100),
            scores.get("open_ports", 0) * (self.config["open_ports_weight"] / 100),
            scores.get("exposure", 0) * (self.config["exposure_weight"] / 100),
            scores.get("activity", 0) * (self.config["activity_weight"] / 100),
        ]
        return sum(weighted_scores)

    def _apply_age_decay(self, score: float, age_days: int) -> float:
        """Apply age decay to score.
        
        Args:
            score: Base score
            age_days: Age of entity in days
            
        Returns:
            Decay-adjusted score
        """
        decay_rate = self.config["age_decay"]
        decay_factor = (age_days / 100) * decay_rate
        adjusted_score = score * (1 - min(decay_factor, 0.5))  # Max 50% decay
        return adjusted_score

    def _generate_recommendations(
        self, factors: RiskFactors, score: float
    ) -> List[str]:
        """Generate risk mitigation recommendations.
        
        Args:
            factors: RiskFactors object
            score: Final risk score
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if factors.vulnerability_count > 5:
            recommendations.append("High vulnerability count detected - prioritize patching")
        
        if factors.exposed_credentials > 0:
            recommendations.append("Exposed credentials found - rotate compromised credentials")
        
        if factors.open_ports > 3:
            recommendations.append("Multiple open ports detected - review firewall rules")
        
        if factors.malware_indicators > 0:
            recommendations.append("Malware indicators present - initiate incident response")
        
        if factors.data_breach_mentions > 0:
            recommendations.append("Data breach mention found - investigate and assess impact")
        
        if score >= 80:
            recommendations.append("CRITICAL: Immediate intervention required")
        elif score >= 60:
            recommendations.append("HIGH: Schedule remediation within 1-2 weeks")
        
        return recommendations

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate risk engine configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid
        """
        required_keys = [
            "vulnerability_weight",
            "open_ports_weight",
            "exposure_weight",
            "activity_weight",
        ]
        
        # Check required keys
        if not all(key in config for key in required_keys):
            return False
        
        # Weights should sum to ~100
        weight_sum = sum(
            config.get(f"{k}_weight", 0) for k in [
                "vulnerability",
                "open_ports",
                "exposure",
                "activity",
            ]
        )
        
        if weight_sum != 100:
            return False
        
        return True


def demo_risk():
    """Demo function for risk engine."""
    print('Risk engine calculating demo risk')

