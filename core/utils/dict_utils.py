"""
Utility functions for CtxOS core.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib


def generate_hash(data: Dict[str, Any]) -> str:
    """Generate SHA256 hash of data."""
    json_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode()).hexdigest()


def merge_dicts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Update dict values override base dict values.
    """
    result = base.copy()

    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def flatten_dict(data: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    Flatten nested dictionary.

    Example:
        {"a": {"b": 1}} -> {"a.b": 1}
    """
    items = []

    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key

        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep).items())
        else:
            items.append((new_key, value))

    return dict(items)


def unflatten_dict(data: Dict[str, Any], sep: str = ".") -> Dict[str, Any]:
    """
    Unflatten a dictionary.

    Example:
        {"a.b": 1} -> {"a": {"b": 1}}
    """
    result = {}

    for key, value in data.items():
        parts = key.split(sep)
        current = result

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    return result


def sanitize_dict(data: Dict[str, Any], keys_to_remove: List[str] = None) -> Dict[str, Any]:
    """
    Remove sensitive or unwanted keys from dictionary.

    Args:
        data: Dictionary to sanitize
        keys_to_remove: Keys to remove (default: common sensitive keys)

    Returns:
        Sanitized dictionary
    """
    if keys_to_remove is None:
        keys_to_remove = [
            "password",
            "token",
            "secret",
            "api_key",
            "private_key",
            "credential",
            "auth",
            "access_token",
            "refresh_token",
            "_internal",
            "_debug",
        ]

    result = {}

    for key, value in data.items():
        # Skip sensitive keys
        if any(sensitive in key.lower() for sensitive in keys_to_remove):
            continue

        # Recursively sanitize nested dicts
        if isinstance(value, dict):
            result[key] = sanitize_dict(value, keys_to_remove)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            result[key] = [
                sanitize_dict(item, keys_to_remove) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result


def filter_by_keys(data: Dict[str, Any], keys: List[str], include: bool = True) -> Dict[str, Any]:
    """
    Filter dictionary by keys.

    Args:
        data: Dictionary to filter
        keys: List of keys
        include: If True, include only specified keys; if False, exclude them

    Returns:
        Filtered dictionary
    """
    result = {}

    if include:
        # Include only specified keys
        for key in keys:
            if key in data:
                result[key] = data[key]
    else:
        # Exclude specified keys
        for key, value in data.items():
            if key not in keys:
                result[key] = value

    return result


def get_nested(data: Dict[str, Any], path: str, default: Any = None, sep: str = ".") -> Any:
    """
    Get value from nested dictionary using dot notation.

    Example:
        get_nested({"a": {"b": 1}}, "a.b") -> 1
    """
    keys = path.split(sep)
    current = data

    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
            if current is None:
                return default
        else:
            return default

    return current


def set_nested(data: Dict[str, Any], path: str, value: Any, sep: str = ".") -> Dict[str, Any]:
    """
    Set value in nested dictionary using dot notation.

    Example:
        set_nested({}, "a.b", 1) -> {"a": {"b": 1}}
    """
    keys = path.split(sep)
    current = data

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value
    return data


def convert_timestamps(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert ISO format timestamp strings to datetime objects.
    """
    result = {}

    for key, value in data.items():
        if isinstance(value, str):
            try:
                result[key] = datetime.fromisoformat(value)
            except (ValueError, TypeError):
                result[key] = value
        elif isinstance(value, dict):
            result[key] = convert_timestamps(value)
        elif isinstance(value, list):
            result[key] = [
                convert_timestamps(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            result[key] = value

    return result


def sort_dict(data: Dict[str, Any], recursive: bool = False) -> Dict[str, Any]:
    """
    Sort dictionary keys.

    Args:
        data: Dictionary to sort
        recursive: If True, recursively sort nested dicts

    Returns:
        Dictionary with sorted keys
    """
    result = {}

    for key in sorted(data.keys()):
        value = data[key]

        if recursive and isinstance(value, dict):
            result[key] = sort_dict(value, recursive=True)
        else:
            result[key] = value

    return result


def compact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove None and empty values from dictionary.
    """
    result = {}

    for key, value in data.items():
        if value is None or value == "" or value == {} or value == []:
            continue

        if isinstance(value, dict):
            result[key] = compact_dict(value)
        else:
            result[key] = value

    return result


def diff_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate difference between two dictionaries.

    Returns:
        {
            "added": {},      # Keys in dict2 but not dict1
            "removed": {},    # Keys in dict1 but not dict2
            "modified": {},   # Keys with different values
        }
    """
    result = {"added": {}, "removed": {}, "modified": {}}

    # Find added and modified
    for key, value in dict2.items():
        if key not in dict1:
            result["added"][key] = value
        elif dict1[key] != value:
            result["modified"][key] = {"old": dict1[key], "new": value}

    # Find removed
    for key, value in dict1.items():
        if key not in dict2:
            result["removed"][key] = value

    return result


def json_encode(obj: Any) -> str:
    """
    JSON encode with support for datetime objects.
    """

    def default_handler(o):
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o)} is not JSON serializable")

    return json.dumps(obj, default=default_handler, indent=2)


def json_decode(data: str) -> Dict[str, Any]:
    """
    JSON decode string.
    """
    return json.loads(data)
