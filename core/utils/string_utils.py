"""
String and validation utilities for CtxOS.
"""

import re
from typing import Optional, List
from urllib.parse import urlparse


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def is_valid_domain(domain: str) -> bool:
    """Check if string is a valid domain name."""
    domain_pattern = r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$"
    return bool(re.match(domain_pattern, domain.lower()))


def is_valid_ip(ip: str) -> bool:
    """Check if string is a valid IPv4 address."""
    ip_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    return bool(re.match(ip_pattern, ip))


def is_valid_ipv6(ip: str) -> bool:
    """Check if string is a valid IPv6 address."""
    ipv6_pattern = r"^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4})$"
    return bool(re.match(ipv6_pattern, ip))


def is_valid_email(email: str) -> bool:
    """Check if string is a valid email address."""
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_pattern, email))


def is_valid_url(url: str) -> bool:
    """Check if string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def is_valid_uuid(uuid_str: str) -> bool:
    """Check if string is a valid UUID."""
    uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    return bool(re.match(uuid_pattern, uuid_str.lower()))


def is_valid_cidr(cidr: str) -> bool:
    """Check if string is a valid CIDR notation."""
    cidr_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/(?:3[0-2]|[1-2]?[0-9])$"
    return bool(re.match(cidr_pattern, cidr))


def normalize_domain(domain: str) -> str:
    """
    Normalize a domain name.
    
    - Convert to lowercase
    - Strip whitespace
    - Remove trailing dot
    """
    domain = domain.lower().strip()
    if domain.endswith("."):
        domain = domain[:-1]
    return domain


def normalize_email(email: str) -> str:
    """
    Normalize an email address.
    
    - Convert to lowercase
    - Strip whitespace
    """
    return email.lower().strip()


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc or None
    except:
        return None


def extract_domains(text: str) -> List[str]:
    """Extract all domains from text."""
    domain_pattern = r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}"
    matches = re.findall(domain_pattern, text.lower())
    return list(set(matches))  # Remove duplicates


def extract_emails(text: str) -> List[str]:
    """Extract all email addresses from text."""
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    matches = re.findall(email_pattern, text)
    return list(set(matches))  # Remove duplicates


def extract_ips(text: str) -> List[str]:
    """Extract all IPv4 addresses from text."""
    ip_pattern = r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
    matches = re.findall(ip_pattern, text)
    return list(set(matches))  # Remove duplicates


def extract_urls(text: str) -> List[str]:
    """Extract all URLs from text."""
    url_pattern = r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
    matches = re.findall(url_pattern, text)
    return list(set(matches))  # Remove duplicates


def truncate(text: str, length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def camel_to_snake(text: str) -> str:
    """Convert camelCase to snake_case."""
    text = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", text)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", text).lower()


def snake_to_camel(text: str) -> str:
    """Convert snake_case to camelCase."""
    components = text.split("_")
    return components[0] + "".join(x.title() for x in components[1:])
