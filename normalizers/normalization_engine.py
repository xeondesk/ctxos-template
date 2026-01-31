"""
Normalization engine for deduplication and normalization of entities and signals.
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
import hashlib
import json


@dataclass
class NormalizationConfig:
    """Configuration for normalization engine."""

    deduplication_strategy: str = "hash"  # "hash" or "field-based"
    field_weights: Dict[str, float] = field(default_factory=lambda: {})
    similarity_threshold: float = 0.95
    normalize_case: bool = True
    trim_whitespace: bool = True
    remove_duplicates: bool = True


class NormalizationEngine:
    """
    Engine for normalizing and deduplicating entities and signals.

    Capabilities:
    - Hash-based deduplication
    - Field-based similarity matching
    - Data normalization (case, whitespace, etc.)
    - Duplicate entity/signal detection
    """

    def __init__(self, config: Optional[NormalizationConfig] = None):
        """Initialize normalization engine."""
        self.config = config or NormalizationConfig()
        self.processed_hashes: Set[str] = set()
        self.entities_map: Dict[str, Dict[str, Any]] = {}
        self.signals_map: Dict[str, Dict[str, Any]] = {}

    def normalize_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize an entity by applying normalization rules.

        Args:
            entity: Entity dictionary

        Returns:
            Normalized entity
        """
        normalized = entity.copy()

        if self.config.normalize_case:
            if isinstance(normalized.get("name"), str):
                normalized["name"] = normalized["name"].lower()

        if self.config.trim_whitespace:
            for key in normalized:
                if isinstance(normalized[key], str):
                    normalized[key] = normalized[key].strip()

        return normalized

    def normalize_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a signal by applying normalization rules.

        Args:
            signal: Signal dictionary

        Returns:
            Normalized signal
        """
        normalized = signal.copy()

        # Normalize data field if it exists
        if "data" in normalized:
            if isinstance(normalized["data"], dict):
                normalized["data"] = self._normalize_dict(normalized["data"])

        return normalized

    def deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate entities based on configured strategy.

        Args:
            entities: List of entities

        Returns:
            Deduplicated entity list
        """
        if self.config.deduplication_strategy == "hash":
            return self._deduplicate_by_hash(entities)
        else:
            return self._deduplicate_by_similarity(entities)

    def deduplicate_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate signals based on configured strategy.

        Args:
            signals: List of signals

        Returns:
            Deduplicated signal list
        """
        if self.config.deduplication_strategy == "hash":
            return self._deduplicate_by_hash(signals)
        else:
            return self._deduplicate_by_similarity(signals)

    def _deduplicate_by_hash(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate items using hash-based approach."""
        unique_items = []
        seen_hashes: Set[str] = set()

        for item in items:
            item_hash = self._compute_hash(item)
            if item_hash not in seen_hashes:
                unique_items.append(item)
                seen_hashes.add(item_hash)

        return unique_items

    def _deduplicate_by_similarity(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate items using field-based similarity."""
        unique_items = []

        for item in items:
            is_duplicate = False

            for existing in unique_items:
                similarity = self._calculate_similarity(item, existing)
                if similarity >= self.config.similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_items.append(item)

        return unique_items

    def _compute_hash(self, item: Dict[str, Any]) -> str:
        """Compute hash of an item."""
        json_str = json.dumps(item, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def _calculate_similarity(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> float:
        """Calculate similarity between two items (0.0 to 1.0)."""
        matching_fields = 0
        total_fields = 0

        common_keys = set(item1.keys()) & set(item2.keys())

        for key in common_keys:
            total_fields += 1
            if item1.get(key) == item2.get(key):
                weight = self.config.field_weights.get(key, 1.0)
                matching_fields += weight

        if total_fields == 0:
            return 0.0

        return min(1.0, matching_fields / total_fields)

    def _normalize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively normalize dictionary values."""
        normalized = {}

        for key, value in data.items():
            if isinstance(value, str):
                if self.config.normalize_case:
                    value = value.lower()
                if self.config.trim_whitespace:
                    value = value.strip()
            elif isinstance(value, dict):
                value = self._normalize_dict(value)

            normalized[key] = value

        return normalized

    def merge_entities(
        self, primary: Dict[str, Any], *duplicates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge duplicate entities into a primary entity.

        Args:
            primary: Primary entity to merge into
            duplicates: Other entities to merge

        Returns:
            Merged entity
        """
        merged = primary.copy()

        for duplicate in duplicates:
            for key, value in duplicate.items():
                if key not in merged and value is not None:
                    merged[key] = value

        return merged

    def reset(self):
        """Reset internal state."""
        self.processed_hashes.clear()
        self.entities_map.clear()
        self.signals_map.clear()
