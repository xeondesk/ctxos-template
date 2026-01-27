"""
Normalization rules module for applying business logic rules to entities and signals.
"""

from typing import Dict, Any, List, Optional, Callable


class NormalizationRule:
    """Base class for normalization rules."""
    
    def __init__(self, name: str, description: str = ""):
        """Initialize rule."""
        self.name = name
        self.description = description
    
    def apply(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Apply rule to item. Should be implemented by subclasses."""
        raise NotImplementedError


class FieldRemovalRule(NormalizationRule):
    """Rule to remove specific fields from items."""
    
    def __init__(self, fields_to_remove: List[str]):
        """Initialize field removal rule."""
        super().__init__("field_removal", "Remove specified fields")
        self.fields_to_remove = fields_to_remove
    
    def apply(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Remove specified fields from item."""
        result = item.copy()
        for field in self.fields_to_remove:
            result.pop(field, None)
        return result


class FieldRenameRule(NormalizationRule):
    """Rule to rename fields in items."""
    
    def __init__(self, rename_map: Dict[str, str]):
        """Initialize field rename rule."""
        super().__init__("field_rename", "Rename specified fields")
        self.rename_map = rename_map
    
    def apply(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Rename fields in item."""
        result = item.copy()
        for old_name, new_name in self.rename_map.items():
            if old_name in result:
                result[new_name] = result.pop(old_name)
        return result


class DefaultValueRule(NormalizationRule):
    """Rule to set default values for missing fields."""
    
    def __init__(self, defaults: Dict[str, Any]):
        """Initialize default value rule."""
        super().__init__("default_values", "Set default values for missing fields")
        self.defaults = defaults
    
    def apply(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Add default values for missing fields."""
        result = item.copy()
        for field, default_value in self.defaults.items():
            if field not in result:
                result[field] = default_value
        return result


class ConditionalRule(NormalizationRule):
    """Rule that applies transformations based on conditions."""
    
    def __init__(
        self, name: str, condition: Callable, transform: Callable
    ):
        """Initialize conditional rule."""
        super().__init__(name, "Apply transformation based on condition")
        self.condition = condition
        self.transform = transform
    
    def apply(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Apply transformation if condition is met."""
        if self.condition(item):
            return self.transform(item)
        return item


class RuleEngine:
    """Engine for applying a sequence of normalization rules."""
    
    def __init__(self):
        """Initialize rule engine."""
        self.rules: Dict[str, NormalizationRule] = {}
        self.rule_order: List[str] = []
    
    def register_rule(self, rule: NormalizationRule) -> None:
        """Register a normalization rule."""
        self.rules[rule.name] = rule
        if rule.name not in self.rule_order:
            self.rule_order.append(rule.name)
    
    def apply_rules(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Apply all registered rules in order."""
        result = item.copy()
        for rule_name in self.rule_order:
            if rule_name in self.rules:
                result = self.rules[rule_name].apply(result)
        return result
    
    def apply_rules_to_batch(
        self, items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply rules to a batch of items."""
        return [self.apply_rules(item) for item in items]
    
    def get_rules(self) -> Dict[str, NormalizationRule]:
        """Get all registered rules."""
        return self.rules.copy()
    
    def clear(self) -> None:
        """Clear all rules."""
        self.rules.clear()
        self.rule_order.clear()
