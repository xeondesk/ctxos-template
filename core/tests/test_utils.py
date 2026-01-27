"""
Unit tests for core utilities.
"""

import pytest
from datetime import datetime

from core.utils import (
    generate_hash, merge_dicts, flatten_dict, unflatten_dict,
    sanitize_dict, filter_by_keys, get_nested, set_nested,
    convert_timestamps, sort_dict, compact_dict, diff_dicts,
    json_encode, json_decode,
    is_valid_domain, is_valid_ip, is_valid_email, is_valid_url,
    is_valid_uuid, is_valid_cidr, is_valid_ipv6,
    normalize_domain, normalize_email,
    extract_domain, extract_domains, extract_emails, extract_ips, extract_urls,
    truncate, slugify, camel_to_snake, snake_to_camel
)


class TestDictUtils:
    """Tests for dictionary utilities."""
    
    def test_generate_hash(self):
        """Test hash generation."""
        data1 = {"key": "value"}
        data2 = {"key": "value"}
        data3 = {"key": "different"}
        
        hash1 = generate_hash(data1)
        hash2 = generate_hash(data2)
        hash3 = generate_hash(data3)
        
        assert hash1 == hash2
        assert hash1 != hash3
    
    def test_merge_dicts(self):
        """Test dictionary merging."""
        dict1 = {"a": 1, "b": {"c": 2}}
        dict2 = {"b": {"d": 3}, "e": 4}
        
        merged = merge_dicts(dict1, dict2)
        
        assert merged["a"] == 1
        assert merged["b"]["c"] == 2
        assert merged["b"]["d"] == 3
        assert merged["e"] == 4
    
    def test_flatten_dict(self):
        """Test dictionary flattening."""
        data = {
            "user": {
                "name": "John",
                "address": {
                    "city": "NYC"
                }
            },
            "age": 30
        }
        
        flat = flatten_dict(data)
        
        assert flat["user.name"] == "John"
        assert flat["user.address.city"] == "NYC"
        assert flat["age"] == 30
    
    def test_unflatten_dict(self):
        """Test dictionary unflattening."""
        flat = {
            "user.name": "John",
            "user.address.city": "NYC",
            "age": 30
        }
        
        unflat = unflatten_dict(flat)
        
        assert unflat["user"]["name"] == "John"
        assert unflat["user"]["address"]["city"] == "NYC"
        assert unflat["age"] == 30
    
    def test_sanitize_dict(self):
        """Test dictionary sanitization."""
        data = {
            "username": "john",
            "password": "secret123",
            "email": "john@example.com",
            "api_key": "key123",
            "api_secret": "secret456"
        }
        
        sanitized = sanitize_dict(data)
        
        assert "username" in sanitized
        assert "password" not in sanitized
        assert "api_key" not in sanitized
        assert "email" in sanitized
    
    def test_filter_by_keys(self):
        """Test filtering dictionary by keys."""
        data = {
            "name": "John",
            "age": 30,
            "email": "john@example.com",
            "password": "secret"
        }
        
        # Include only
        filtered = filter_by_keys(data, include=["name", "age"])
        assert filtered == {"name": "John", "age": 30}
        
        # Exclude
        filtered = filter_by_keys(data, exclude=["password"])
        assert "password" not in filtered
    
    def test_get_nested(self):
        """Test getting nested value."""
        data = {
            "user": {
                "profile": {
                    "name": "John"
                }
            }
        }
        
        value = get_nested(data, "user.profile.name")
        assert value == "John"
        
        missing = get_nested(data, "user.missing.path")
        assert missing is None
    
    def test_set_nested(self):
        """Test setting nested value."""
        data = {}
        set_nested(data, "user.profile.name", "John")
        
        assert data["user"]["profile"]["name"] == "John"
    
    def test_sort_dict(self):
        """Test dictionary sorting."""
        data = {"z": 1, "a": 2, "m": 3}
        sorted_dict = sort_dict(data)
        
        keys = list(sorted_dict.keys())
        assert keys == ["a", "m", "z"]
    
    def test_compact_dict(self):
        """Test removing None/empty values."""
        data = {
            "name": "John",
            "age": None,
            "email": "",
            "tags": [],
            "city": "NYC"
        }
        
        compacted = compact_dict(data)
        
        assert "name" in compacted
        assert "age" not in compacted
        assert "email" not in compacted
        assert "tags" not in compacted
        assert "city" in compacted
    
    def test_diff_dicts(self):
        """Test dictionary difference."""
        dict1 = {"a": 1, "b": 2, "c": 3}
        dict2 = {"a": 1, "b": 20, "d": 4}
        
        diff = diff_dicts(dict1, dict2)
        
        assert "b" in diff["modified"]
        assert "c" in diff["removed"]
        assert "d" in diff["added"]
    
    def test_json_encode_decode(self):
        """Test JSON encoding/decoding with datetime."""
        now = datetime.utcnow()
        data = {
            "name": "John",
            "timestamp": now
        }
        
        encoded = json_encode(data)
        decoded = json_decode(encoded)
        
        assert decoded["name"] == "John"


class TestStringValidation:
    """Tests for string validation functions."""
    
    def test_is_valid_domain(self):
        """Test domain validation."""
        assert is_valid_domain("example.com") is True
        assert is_valid_domain("sub.example.com") is True
        assert is_valid_domain("example.co.uk") is True
        assert is_valid_domain("invalid..com") is False
        assert is_valid_domain("notadomain") is False
    
    def test_is_valid_email(self):
        """Test email validation."""
        assert is_valid_email("user@example.com") is True
        assert is_valid_email("user.name@example.com") is True
        assert is_valid_email("invalid@") is False
        assert is_valid_email("@example.com") is False
    
    def test_is_valid_ip(self):
        """Test IPv4 validation."""
        assert is_valid_ip("192.168.1.1") is True
        assert is_valid_ip("10.0.0.0") is True
        assert is_valid_ip("256.1.1.1") is False
        assert is_valid_ip("192.168.1") is False
    
    def test_is_valid_ipv6(self):
        """Test IPv6 validation."""
        assert is_valid_ipv6("2001:db8::1") is True
        assert is_valid_ipv6("::1") is True
        assert is_valid_ipv6("gggg::1") is False
    
    def test_is_valid_url(self):
        """Test URL validation."""
        assert is_valid_url("https://example.com") is True
        assert is_valid_url("http://example.com/path") is True
        assert is_valid_url("example.com") is False
        assert is_valid_url("ftp://invalid") is False
    
    def test_is_valid_uuid(self):
        """Test UUID validation."""
        assert is_valid_uuid("550e8400-e29b-41d4-a716-446655440000") is True
        assert is_valid_uuid("invalid-uuid") is False
    
    def test_is_valid_cidr(self):
        """Test CIDR validation."""
        assert is_valid_cidr("192.168.0.0/24") is True
        assert is_valid_cidr("10.0.0.0/8") is True
        assert is_valid_cidr("192.168.1") is False


class TestStringNormalization:
    """Tests for string normalization functions."""
    
    def test_normalize_domain(self):
        """Test domain normalization."""
        assert normalize_domain("Example.COM") == "example.com"
        assert normalize_domain("  example.com  ") == "example.com"
        assert normalize_domain("example.com.") == "example.com"
    
    def test_normalize_email(self):
        """Test email normalization."""
        assert normalize_email("User@Example.COM") == "user@example.com"
        assert normalize_email("  user@example.com  ") == "user@example.com"


class TestStringExtraction:
    """Tests for string extraction functions."""
    
    def test_extract_domain(self):
        """Test domain extraction."""
        domain = extract_domain("https://example.com/path")
        assert domain == "example.com"
    
    def test_extract_domains(self):
        """Test extracting multiple domains."""
        text = "Check example.com and test.org for issues"
        domains = extract_domains(text)
        
        assert "example.com" in domains
        assert "test.org" in domains
    
    def test_extract_emails(self):
        """Test extracting emails."""
        text = "Contact user@example.com or admin@test.org"
        emails = extract_emails(text)
        
        assert "user@example.com" in emails
        assert "admin@test.org" in emails
    
    def test_extract_ips(self):
        """Test extracting IP addresses."""
        text = "Server 1.2.3.4 and 192.168.1.1 are down"
        ips = extract_ips(text)
        
        assert "1.2.3.4" in ips
        assert "192.168.1.1" in ips
    
    def test_extract_urls(self):
        """Test extracting URLs."""
        text = "Visit https://example.com and http://test.org"
        urls = extract_urls(text)
        
        assert "https://example.com" in urls
        assert "http://test.org" in urls


class TestStringTransformers:
    """Tests for string transformation functions."""
    
    def test_truncate(self):
        """Test string truncation."""
        text = "This is a long string"
        truncated = truncate(text, 10)
        
        assert len(truncated) <= 13  # 10 + "..."
        assert truncated.endswith("...")
    
    def test_slugify(self):
        """Test slug generation."""
        slug = slugify("My Test String")
        assert slug == "my-test-string"
        
        slug = slugify("Special!@# Characters")
        assert "@" not in slug and "#" not in slug
    
    def test_camel_to_snake(self):
        """Test camelCase to snake_case conversion."""
        assert camel_to_snake("myVariableName") == "my_variable_name"
        assert camel_to_snake("HTTPResponse") == "h_t_t_p_response"
    
    def test_snake_to_camel(self):
        """Test snake_case to camelCase conversion."""
        assert snake_to_camel("my_variable_name") == "myVariableName"
        assert snake_to_camel("my_var") == "myVar"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
