"""
Base engine class for CtxOS scoring engines.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class EngineStatus(Enum):
    """Engine operational status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PAUSED = "paused"


@dataclass
class ScoringResult:
    """Result from engine scoring operation."""
    engine_name: str
    entity_id: str
    score: float  # 0-100
    severity: str  # critical, high, medium, low, info
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "engine_name": self.engine_name,
            "entity_id": self.entity_id,
            "score": self.score,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "metrics": self.metrics,
            "recommendations": self.recommendations,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScoringResult":
        """Create from dictionary."""
        return cls(
            engine_name=data["engine_name"],
            entity_id=data["entity_id"],
            score=data["score"],
            severity=data["severity"],
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
            details=data.get("details", {}),
            metrics=data.get("metrics", {}),
            recommendations=data.get("recommendations", []),
            id=data.get("id", str(uuid4())),
        )


class BaseEngine(ABC):
    """Abstract base class for scoring engines."""

    def __init__(self, name: str, version: str = "1.0.0", enabled: bool = True):
        """Initialize engine.
        
        Args:
            name: Engine name
            version: Engine version
            enabled: Whether engine is enabled
        """
        self.name = name
        self.version = version
        self.enabled = enabled
        self.status = EngineStatus.ACTIVE
        self.created_at = datetime.utcnow()
        self.last_run: Optional[datetime] = None
        self.run_count = 0
        self.error_count = 0
        self.config: Dict[str, Any] = {}

    @abstractmethod
    def score(self, entity: Any, context: Any = None) -> ScoringResult:
        """Score an entity.
        
        Args:
            entity: Entity to score
            context: Optional context for additional data
            
        Returns:
            ScoringResult with score and analysis
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate engine configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass

    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure engine with provided config.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if configuration successful
        """
        if self.validate_config(config):
            self.config = config
            return True
        return False

    def enable(self):
        """Enable engine."""
        self.enabled = True
        self.status = EngineStatus.ACTIVE

    def disable(self):
        """Disable engine."""
        self.enabled = False
        self.status = EngineStatus.INACTIVE

    def get_status(self) -> Dict[str, Any]:
        """Get engine status."""
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status.value,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "run_count": self.run_count,
            "error_count": self.error_count,
        }


class ScoringUtils:
    """Utility functions for scoring engines."""

    @staticmethod
    def normalize_score(value: float, min_val: float = 0, max_val: float = 100) -> float:
        """Normalize value to 0-100 scale.
        
        Args:
            value: Value to normalize
            min_val: Minimum expected value
            max_val: Maximum expected value
            
        Returns:
            Normalized score 0-100
        """
        if max_val == min_val:
            return 50.0
        normalized = ((value - min_val) / (max_val - min_val)) * 100
        return max(0, min(100, normalized))

    @staticmethod
    def score_to_severity(score: float) -> str:
        """Convert score to severity level.
        
        Args:
            score: Score 0-100
            
        Returns:
            Severity level: critical, high, medium, low, info
        """
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        elif score >= 20:
            return "low"
        else:
            return "info"

    @staticmethod
    def aggregate_scores(scores: List[float], weights: Optional[List[float]] = None) -> float:
        """Aggregate multiple scores.
        
        Args:
            scores: List of scores
            weights: Optional weights for each score
            
        Returns:
            Aggregated score
        """
        if not scores:
            return 0.0
        
        if weights is None:
            return sum(scores) / len(scores)
        
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0
        
        return sum(s * w for s, w in zip(scores, weights)) / total_weight

    @staticmethod
    def calculate_confidence(data_points: int, max_points: int = 100) -> float:
        """Calculate confidence score based on data points.
        
        Args:
            data_points: Number of data points
            max_points: Maximum data points for full confidence
            
        Returns:
            Confidence 0-1
        """
        confidence = min(data_points / max_points, 1.0)
        return confidence
