"""
Engine Manager - Orchestrate and manage scoring engines.
"""

import yaml
from typing import Any, Dict, List, Optional
from pathlib import Path

from engines.base_engine import BaseEngine, ScoringResult, ScoringUtils
from engines.risk.risk_engine import RiskEngine
from engines.exposure.exposure_engine import ExposureEngine
from engines.drift.drift_engine import DriftEngine


class EngineManager:
    """Manage and coordinate scoring engines."""

    def __init__(self, config_path: str = "configs/engines.yml"):
        """Initialize Engine Manager.

        Args:
            config_path: Path to engines configuration file
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.engines: Dict[str, BaseEngine] = {}
        self._load_config()
        self._initialize_engines()

    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"Warning: Config file not found at {self.config_path}")
            self.config = {"engines": {}}

    def _initialize_engines(self):
        """Initialize all configured engines."""
        engines_config = self.config.get("engines", {})

        # Risk Engine
        if engines_config.get("risk", {}).get("enabled", True):
            risk_engine = RiskEngine()
            risk_config = engines_config.get("risk", {}).get("weights", {})
            if risk_config:
                risk_engine.configure(risk_config)
            self.engines["risk"] = risk_engine

        # Exposure Engine
        if engines_config.get("exposure", {}).get("enabled", True):
            exposure_engine = ExposureEngine()
            exposure_config = engines_config.get("exposure", {}).get("weights", {})
            if exposure_config:
                exposure_engine.configure(exposure_config)
            self.engines["exposure"] = exposure_engine

        # Drift Engine
        if engines_config.get("drift", {}).get("enabled", True):
            drift_engine = DriftEngine()
            drift_config = engines_config.get("drift", {}).get("weights", {})
            if drift_config:
                drift_engine.configure(drift_config)
            self.engines["drift"] = drift_engine

    def score_entity(
        self, entity: Any, context: Any = None, engine_name: Optional[str] = None
    ) -> Dict[str, ScoringResult]:
        """Score entity with specified engine(s).

        Args:
            entity: Entity to score
            context: Optional context for additional data
            engine_name: Specific engine to use, or None for all

        Returns:
            Dictionary of engine results
        """
        results = {}

        if engine_name:
            # Score with specific engine
            if engine_name in self.engines:
                engine = self.engines[engine_name]
                if engine.enabled:
                    results[engine_name] = engine.score(entity, context)
        else:
            # Score with all enabled engines
            for name, engine in self.engines.items():
                if engine.enabled:
                    results[name] = engine.score(entity, context)

        return results

    def aggregate_results(self, results: Dict[str, ScoringResult]) -> Dict[str, Any]:
        """Aggregate results from multiple engines.

        Args:
            results: Dictionary of engine results

        Returns:
            Aggregated scoring result
        """
        if not results:
            return {}

        orch_config = self.config.get("orchestration", {})
        method = orch_config.get("result_combination", {}).get("method", "average")
        weights = orch_config.get("result_combination", {}).get("weights", {})

        scores = []
        severity_scores = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
        severities = []

        for engine_name, result in results.items():
            scores.append(result.score)
            severities.append(severity_scores.get(result.severity, 0))

        if method == "average":
            aggregated_score = sum(scores) / len(scores) if scores else 0
        elif method == "max":
            aggregated_score = max(scores) if scores else 0
        elif method == "weighted_average":
            weight_list = [weights.get(name, 1.0 / len(results)) for name in results.keys()]
            total_weight = sum(weight_list)
            aggregated_score = (
                sum(s * w for s, w in zip(scores, weight_list)) / total_weight
                if total_weight > 0
                else 0
            )
        else:
            aggregated_score = sum(scores) / len(scores) if scores else 0

        # Determine aggregated severity
        avg_severity_score = sum(severities) / len(severities) if severities else 0
        if avg_severity_score >= 3.5:
            aggregated_severity = "critical"
        elif avg_severity_score >= 2.5:
            aggregated_severity = "high"
        elif avg_severity_score >= 1.5:
            aggregated_severity = "medium"
        elif avg_severity_score >= 0.5:
            aggregated_severity = "low"
        else:
            aggregated_severity = "info"

        # Combine recommendations
        all_recommendations = []
        for result in results.values():
            all_recommendations.extend(result.recommendations)

        return {
            "aggregated_score": aggregated_score,
            "aggregated_severity": aggregated_severity,
            "individual_results": {name: result.to_dict() for name, result in results.items()},
            "combined_recommendations": list(set(all_recommendations)),
            "engines_used": list(results.keys()),
        }

    def enable_engine(self, engine_name: str):
        """Enable a specific engine.

        Args:
            engine_name: Name of engine to enable
        """
        if engine_name in self.engines:
            self.engines[engine_name].enable()

    def disable_engine(self, engine_name: str):
        """Disable a specific engine.

        Args:
            engine_name: Name of engine to disable
        """
        if engine_name in self.engines:
            self.engines[engine_name].disable()

    def get_engine_status(self, engine_name: Optional[str] = None) -> Dict[str, Any]:
        """Get status of engine(s).

        Args:
            engine_name: Specific engine, or None for all

        Returns:
            Status dictionary
        """
        if engine_name:
            if engine_name in self.engines:
                return self.engines[engine_name].get_status()
            return {}

        return {name: engine.get_status() for name, engine in self.engines.items()}

    def reload_config(self):
        """Reload configuration from file."""
        self._load_config()
        self._initialize_engines()

    def list_engines(self) -> List[str]:
        """List all available engines.

        Returns:
            List of engine names
        """
        return list(self.engines.keys())
