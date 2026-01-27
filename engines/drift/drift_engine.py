"""
Drift Engine - Detect and score configuration and state changes over time.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from engines.base_engine import BaseEngine, ScoringResult, ScoringUtils
from core.models import Entity, Signal, Context


@dataclass
class DriftMetrics:
    """Configuration drift metrics."""
    property_changes: int = 0
    new_properties: int = 0
    removed_properties: int = 0
    modified_signals: int = 0
    new_signals: int = 0
    removed_signals: int = 0
    days_tracked: int = 0
    change_velocity: float = 0.0  # Changes per day


class DriftEngine(BaseEngine):
    """Configuration drift detection and scoring engine."""

    DEFAULT_CONFIG = {
        "property_change_weight": 30,
        "signal_change_weight": 40,
        "unexpected_change_multiplier": 1.5,
        "drift_threshold_days": 7,
        "critical_property_list": [
            "dns_servers",
            "authentication_method",
            "firewall_rules",
            "ssl_certificate",
            "ip_address",
            "service_ports",
        ],
    }

    def __init__(self):
        """Initialize Drift Engine."""
        super().__init__("DriftEngine", version="1.0.0")
        self.config = self.DEFAULT_CONFIG.copy()
        # Store baseline snapshots for comparison
        self.baselines: Dict[str, Dict[str, Any]] = {}

    def score(self, entity: Entity, context: Any = None) -> ScoringResult:
        """Score entity drift.
        
        Args:
            entity: Entity to score
            context: Optional context with baseline for comparison
            
        Returns:
            ScoringResult with drift score
        """
        self.run_count += 1
        self.last_run = datetime.utcnow()

        try:
            # Get baseline for entity
            baseline = self.baselines.get(entity.id, {})
            
            # Calculate drift metrics
            metrics = self._calculate_drift_metrics(entity, baseline, context)
            
            # Calculate drift score
            drift_score = self._calculate_drift_score(metrics)
            
            # Determine severity
            severity = ScoringUtils.score_to_severity(drift_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(metrics, drift_score)
            
            # Update baseline
            self.baselines[entity.id] = self._create_snapshot(entity, context)
            
            return ScoringResult(
                engine_name=self.name,
                entity_id=entity.id,
                score=drift_score,
                severity=severity,
                details={
                    "entity_name": entity.name,
                    "property_changes": metrics.property_changes,
                    "new_properties": metrics.new_properties,
                    "removed_properties": metrics.removed_properties,
                    "signal_changes": metrics.modified_signals,
                    "new_signals": metrics.new_signals,
                    "change_velocity": round(metrics.change_velocity, 2),
                },
                metrics={
                    "property_drift": min(
                        (metrics.property_changes + metrics.new_properties) * 15, 100
                    ),
                    "signal_drift": min(
                        (metrics.modified_signals + metrics.new_signals) * 10, 100
                    ),
                    "change_rate": metrics.change_velocity * 10,
                    "unexpectedness_factor": (
                        self.config["unexpected_change_multiplier"] * metrics.new_properties
                    ),
                },
                recommendations=recommendations,
            )
        except Exception as e:
            self.error_count += 1
            raise Exception(f"Drift scoring failed: {str(e)}")

    def _calculate_drift_metrics(
        self, entity: Entity, baseline: Dict[str, Any], context: Any = None
    ) -> DriftMetrics:
        """Calculate drift metrics.
        
        Args:
            entity: Current entity state
            baseline: Baseline snapshot
            context: Optional context with historical data
            
        Returns:
            DriftMetrics object
        """
        metrics = DriftMetrics()
        
        if not baseline:
            return metrics
        
        baseline_properties = baseline.get("properties", {})
        baseline_signals = baseline.get("signals", [])
        
        # Compare properties
        current_props = entity.properties
        
        # Count property changes
        for key, value in current_props.items():
            if key in baseline_properties:
                if baseline_properties[key] != value:
                    metrics.property_changes += 1
            else:
                metrics.new_properties += 1
        
        # Count removed properties
        for key in baseline_properties:
            if key not in current_props:
                metrics.removed_properties += 1
        
        # Compare signals if context provided
        if context and hasattr(context, 'get_signals_for_entity'):
            current_signals = context.get_signals_for_entity(entity.id)
            current_signal_ids = {s.id for s in current_signals}
            baseline_signal_ids = set(baseline_signals)
            
            # New signals
            metrics.new_signals = len(current_signal_ids - baseline_signal_ids)
            
            # Removed signals
            metrics.removed_signals = len(baseline_signal_ids - current_signal_ids)
            
            # For simplicity, consider overlap as stable
            metrics.modified_signals = 0
        
        # Calculate change velocity
        baseline_time = baseline.get("timestamp", self.last_run)
        if baseline_time:
            time_delta = (datetime.utcnow() - baseline_time).total_seconds()
            if time_delta > 0:
                total_changes = (
                    metrics.property_changes +
                    metrics.new_properties +
                    metrics.removed_properties +
                    metrics.new_signals +
                    metrics.removed_signals
                )
                days = max(time_delta / (24 * 3600), 1)
                metrics.change_velocity = total_changes / days
                metrics.days_tracked = int(days)
        
        return metrics

    def _calculate_drift_score(self, metrics: DriftMetrics) -> float:
        """Calculate drift score from metrics.
        
        Args:
            metrics: DriftMetrics object
            
        Returns:
            Drift score 0-100
        """
        score = 0
        
        # Property drift component
        property_drift = (
            metrics.property_changes +
            metrics.new_properties * 2 +
            metrics.removed_properties * 1.5
        )
        property_score = min(property_drift * 5, 100)
        score += (property_score * self.config["property_change_weight"]) / 100
        
        # Signal drift component
        signal_drift = (
            metrics.modified_signals +
            metrics.new_signals * 1.5 +
            metrics.removed_signals
        )
        signal_score = min(signal_drift * 10, 100)
        score += (signal_score * self.config["signal_change_weight"]) / 100
        
        # Velocity component (rapid changes are concerning)
        if metrics.change_velocity > 1.0:  # More than 1 change per day
            velocity_penalty = min(metrics.change_velocity * 10, 30)
            score += velocity_penalty
        
        # Unexpectedness multiplier for new properties
        if metrics.new_properties > 0:
            score *= self.config["unexpected_change_multiplier"]
        
        return min(score, 100)

    def _create_snapshot(self, entity: Entity, context: Any = None) -> Dict[str, Any]:
        """Create snapshot of entity state for baseline.
        
        Args:
            entity: Entity to snapshot
            context: Optional context
            
        Returns:
            Snapshot dictionary
        """
        snapshot = {
            "timestamp": datetime.utcnow(),
            "properties": entity.properties.copy(),
            "tags": entity.tags.copy(),
            "severity": entity.severity.value if hasattr(entity.severity, 'value') else str(entity.severity),
            "signals": [],
        }
        
        if context and hasattr(context, 'get_signals_for_entity'):
            signals = context.get_signals_for_entity(entity.id)
            snapshot["signals"] = [s.id for s in signals]
        
        return snapshot

    def _generate_recommendations(
        self, metrics: DriftMetrics, score: float
    ) -> List[str]:
        """Generate drift recommendations.
        
        Args:
            metrics: DriftMetrics object
            score: Drift score
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if metrics.property_changes > 3:
            recommendations.append(
                "Significant property changes detected - review configuration changes"
            )
        
        if metrics.new_properties > 0:
            recommendations.append(
                f"New properties discovered ({metrics.new_properties}) - verify legitimacy"
            )
        
        if metrics.removed_properties > 0:
            recommendations.append(
                f"Properties removed ({metrics.removed_properties}) - investigate removal reason"
            )
        
        if metrics.new_signals > 5:
            recommendations.append(
                "Multiple new signals detected - may indicate scanning or exploitation"
            )
        
        if metrics.change_velocity > 2:
            recommendations.append(
                "High change velocity detected - possible automated attack or misconfiguration"
            )
        
        if score >= 70:
            recommendations.append(
                "SIGNIFICANT DRIFT: Implement configuration management and monitoring"
            )
        
        return recommendations

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate drift engine configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid
        """
        required_keys = [
            "property_change_weight",
            "signal_change_weight",
        ]
        
        if not all(key in config for key in required_keys):
            return False
        
        # Weights should sum to ~100
        weight_sum = (
            config.get("property_change_weight", 0) +
            config.get("signal_change_weight", 0)
        )
        
        # Allow some flexibility for weights (they don't have to sum to exactly 100)
        if weight_sum < 50 or weight_sum > 150:
            return False
        
        return True

    def set_baseline(self, entity_id: str, snapshot: Dict[str, Any]):
        """Manually set baseline snapshot for entity.
        
        Args:
            entity_id: Entity ID
            snapshot: Snapshot to use as baseline
        """
        self.baselines[entity_id] = snapshot

    def get_baseline(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get baseline snapshot for entity.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Baseline snapshot or None
        """
        return self.baselines.get(entity_id)
