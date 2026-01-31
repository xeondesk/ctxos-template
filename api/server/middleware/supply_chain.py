"""
Supply chain verification and dependency security.
"""
import os
import json
import hashlib
import subprocess
import tempfile
import requests
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import logging
import time
import yaml
import toml
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

logger = logging.getLogger(__name__)


class VulnerabilitySeverity(str, Enum):
    """Vulnerability severity levels."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VerificationStatus(str, Enum):
    """Verification status."""

    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    WARNING = "warning"
    UNKNOWN = "unknown"


@dataclass
class Dependency:
    """Dependency information."""

    name: str
    version: str
    package_type: str  # pip, npm, cargo, etc.
    source: str
    checksum: str = ""
    license: str = ""
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    risk_score: int = 0

    def __post_init__(self):
        if not self.checksum and self.source:
            self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate checksum for dependency source."""
        try:
            if os.path.isfile(self.source):
                with open(self.source, "rb") as f:
                    return hashlib.sha256(f.read()).hexdigest()
            else:
                # For remote dependencies, use name+version as identifier
                return hashlib.sha256(f"{self.name}:{self.version}".encode()).hexdigest()
        except Exception:
            return hashlib.sha256(f"{self.name}:{self.version}".encode()).hexdigest()


@dataclass
class Vulnerability:
    """Security vulnerability information."""

    id: str
    severity: VulnerabilitySeverity
    title: str
    description: str
    affected_versions: List[str]
    fixed_version: Optional[str]
    references: List[str] = field(default_factory=list)
    cvss_score: Optional[float] = None
    cwe_id: Optional[str] = None
    published_date: Optional[str] = None


@dataclass
class VerificationResult:
    """Result of supply chain verification."""

    status: VerificationStatus
    dependencies_checked: int
    vulnerabilities_found: int
    critical_vulnerabilities: int
    high_vulnerabilities: int
    medium_vulnerabilities: int
    low_vulnerabilities: int
    license_issues: List[str] = field(default_factory=list)
    checksum_mismatches: List[str] = field(default_factory=list)
    unsigned_packages: List[str] = field(default_factory=list)
    risk_score: int = 0
    verification_time: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)


class VulnerabilityDatabase:
    """Interface to vulnerability databases."""

    def __init__(self):
        self.osv_api_url = "https://api.osv.dev/v1/query"
        self.github_advisory_url = "https://api.github.com/advisories"
        self.nvd_api_url = "https://services.nvd.nist.gov/rest/json/cves/1.0"

    def query_vulnerabilities(
        self, package_name: str, package_version: str, ecosystem: str
    ) -> List[Vulnerability]:
        """Query vulnerabilities for a package."""
        vulnerabilities = []

        try:
            # Query OSV database
            osv_vulns = self._query_osv(package_name, package_version, ecosystem)
            vulnerabilities.extend(osv_vulns)

            # Query GitHub Advisory (for npm, pip, etc.)
            if ecosystem in ["npm", "pip", "cargo"]:
                github_vulns = self._query_github_advisory(package_name, ecosystem)
                vulnerabilities.extend(github_vulns)

        except Exception as e:
            logger.error(f"Failed to query vulnerabilities for {package_name}: {e}")

        return vulnerabilities

    def _query_osv(
        self, package_name: str, package_version: str, ecosystem: str
    ) -> List[Vulnerability]:
        """Query OSV database."""
        try:
            payload = {
                "package": {
                    "name": package_name,
                    "ecosystem": ecosystem,
                    "version": package_version,
                }
            }

            response = requests.post(self.osv_api_url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            vulnerabilities = []

            for vuln in data.get("vulns", []):
                severity = self._determine_severity(vuln)

                vulnerability = Vulnerability(
                    id=vuln.get("id", ""),
                    severity=severity,
                    title=vuln.get("summary", ""),
                    description=vuln.get("details", ""),
                    affected_versions=self._extract_affected_versions(vuln),
                    fixed_version=self._extract_fixed_version(vuln),
                    references=[ref.get("url", "") for ref in vuln.get("references", [])],
                    cvss_score=self._extract_cvss_score(vuln),
                    published_date=vuln.get("published"),
                )

                vulnerabilities.append(vulnerability)

            return vulnerabilities

        except Exception as e:
            logger.error(f"OSV query failed: {e}")
            return []

    def _query_github_advisory(self, package_name: str, ecosystem: str) -> List[Vulnerability]:
        """Query GitHub Advisory database."""
        try:
            # GitHub Advisory requires authentication for higher rate limits
            headers = {}
            github_token = os.getenv("GITHUB_TOKEN")
            if github_token:
                headers["Authorization"] = f"token {github_token}"

            url = f"{self.github_advisory_url}"
            params = {
                "ecosystem": ecosystem,
                "package": package_name,
                "state": "published",
                "per_page": 100,
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            vulnerabilities = []

            for item in data:
                severity = self._determine_github_severity(item.get("severity", ""))

                vulnerability = Vulnerability(
                    id=item.get("ghsa_id", ""),
                    severity=severity,
                    title=item.get("summary", ""),
                    description=item.get("description", ""),
                    affected_versions=self._extract_github_affected_versions(item),
                    fixed_version=self._extract_github_fixed_version(item),
                    references=[ref.get("url", "") for ref in item.get("references", [])],
                    cvss_score=item.get("cvss", {}).get("score"),
                    published_date=item.get("published_at"),
                )

                vulnerabilities.append(vulnerability)

            return vulnerabilities

        except Exception as e:
            logger.error(f"GitHub Advisory query failed: {e}")
            return []

    def _determine_severity(self, vuln_data: Dict[str, Any]) -> VulnerabilitySeverity:
        """Determine vulnerability severity."""
        # Check for CVSS score first
        cvss_score = self._extract_cvss_score(vuln_data)
        if cvss_score:
            if cvss_score >= 9.0:
                return VulnerabilitySeverity.CRITICAL
            elif cvss_score >= 7.0:
                return VulnerabilitySeverity.HIGH
            elif cvss_score >= 4.0:
                return VulnerabilitySeverity.MEDIUM
            else:
                return VulnerabilitySeverity.LOW

        # Fallback to database-specific severity
        severity = vuln_data.get("severity", "").lower()
        if severity in ["critical", "high"]:
            return (
                VulnerabilitySeverity.HIGH if severity == "high" else VulnerabilitySeverity.CRITICAL
            )
        elif severity in ["medium", "moderate"]:
            return VulnerabilitySeverity.MEDIUM
        elif severity == "low":
            return VulnerabilitySeverity.LOW

        return VulnerabilitySeverity.MEDIUM  # Default

    def _extract_cvss_score(self, vuln_data: Dict[str, Any]) -> Optional[float]:
        """Extract CVSS score from vulnerability data."""
        # Try different CVSS score fields
        for field in ["cvss_score", "score", "cvss"]:
            if field in vuln_data:
                try:
                    return float(vuln_data[field])
                except (ValueError, TypeError):
                    continue

        # Check in severity field
        severity_data = vuln_data.get("severity", [])
        if isinstance(severity_data, list):
            for item in severity_data:
                if isinstance(item, dict) and "score" in item:
                    try:
                        return float(item["score"])
                    except (ValueError, TypeError):
                        continue

        return None

    def _extract_affected_versions(self, vuln_data: Dict[str, Any]) -> List[str]:
        """Extract affected versions from vulnerability data."""
        affected = []

        # Try different version fields
        for field in ["affected", "versions"]:
            if field in vuln_data:
                versions = vuln_data[field]
                if isinstance(versions, list):
                    for version_info in versions:
                        if isinstance(version_info, dict):
                            version = version_info.get("version") or version_info.get("range")
                            if version:
                                affected.append(version)
                        elif isinstance(version_info, str):
                            affected.append(version_info)

        return affected

    def _extract_fixed_version(self, vuln_data: Dict[str, Any]) -> Optional[str]:
        """Extract fixed version from vulnerability data."""
        # Try different fixed version fields
        for field in ["fixed_version", "patched_versions", "fixed"]:
            if field in vuln_data:
                fixed = vuln_data[field]
                if isinstance(fixed, list) and fixed:
                    return fixed[0]
                elif isinstance(fixed, str):
                    return fixed

        return None

    def _determine_github_severity(self, severity: str) -> VulnerabilitySeverity:
        """Determine severity from GitHub Advisory."""
        severity_map = {
            "critical": VulnerabilitySeverity.CRITICAL,
            "high": VulnerabilitySeverity.HIGH,
            "moderate": VulnerabilitySeverity.MEDIUM,
            "low": VulnerabilitySeverity.LOW,
        }
        return severity_map.get(severity.lower(), VulnerabilitySeverity.MEDIUM)

    def _extract_github_affected_versions(self, item: Dict[str, Any]) -> List[str]:
        """Extract affected versions from GitHub Advisory."""
        affected = []

        vulnerabilities = item.get("vulnerabilities", [])
        for vuln in vulnerabilities:
            package = vuln.get("package", {})
            ecosystem = package.get("ecosystem", "")

            if ecosystem in ["pip", "npm", "cargo"]:
                severity_info = vuln.get("severity", [])
                for severity_item in severity_info:
                    ranges = severity_item.get("ranges", [])
                    for range_info in ranges:
                        events = range_info.get("events", [])
                        for event in events:
                            if "introduced" in event:
                                affected.append(event["introduced"])
                            if "fixed" in event:
                                affected.append(event["fixed"])

        return affected

    def _extract_github_fixed_version(self, item: Dict[str, Any]) -> Optional[str]:
        """Extract fixed version from GitHub Advisory."""
        vulnerabilities = item.get("vulnerabilities", [])
        for vuln in vulnerabilities:
            severity_info = vuln.get("severity", [])
            for severity_item in severity_info:
                ranges = severity_item.get("ranges", [])
                for range_info in ranges:
                    events = range_info.get("events", [])
                    for event in events:
                        if "fixed" in event:
                            return event["fixed"]

        return None


class DependencyScanner:
    """Scanner for project dependencies."""

    def __init__(self):
        self.supported_files = {
            "requirements.txt": self._scan_requirements_txt,
            "Pipfile": self._scan_pipfile,
            "pyproject.toml": self._scan_pyproject_toml,
            "package.json": self._scan_package_json,
            "yarn.lock": self._scan_yarn_lock,
            "Cargo.toml": self._scan_cargo_toml,
            "go.mod": self._scan_go_mod,
            "composer.json": self._scan_composer_json,
        }

    def scan_project(self, project_path: str) -> List[Dependency]:
        """Scan project for dependencies."""
        dependencies = []
        project_path = Path(project_path)

        if not project_path.exists():
            logger.error(f"Project path {project_path} does not exist")
            return dependencies

        # Scan for dependency files
        for filename, scanner in self.supported_files.items():
            file_path = project_path / filename
            if file_path.exists():
                try:
                    file_deps = scanner(file_path)
                    dependencies.extend(file_deps)
                    logger.info(f"Scanned {filename}, found {len(file_deps)} dependencies")
                except Exception as e:
                    logger.error(f"Failed to scan {filename}: {e}")

        return dependencies

    def _scan_requirements_txt(self, file_path: Path) -> List[Dependency]:
        """Scan requirements.txt file."""
        dependencies = []

        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Parse requirement: package==version or package>=version
                    parts = line.split("==")
                    if len(parts) == 2:
                        name, version = parts[0].strip(), parts[1].strip()
                    else:
                        # Handle other specifiers
                        name = (
                            line.split(">=")[0].split("<=")[0].split("~=")[0].split("!=")[0].strip()
                        )
                        version = "latest"

                    dependencies.append(
                        Dependency(
                            name=name, version=version, package_type="pip", source=str(file_path)
                        )
                    )

        return dependencies

    def _scan_pipfile(self, file_path: Path) -> List[Dependency]:
        """Scan Pipfile."""
        dependencies = []

        with open(file_path, "r") as f:
            data = toml.load(f)

        # Scan packages
        packages = data.get("packages", {})
        for name, version_info in packages.items():
            if isinstance(version_info, str):
                version = version_info
            elif isinstance(version_info, dict):
                version = version_info.get("version", "latest")
            else:
                version = "latest"

            dependencies.append(
                Dependency(name=name, version=version, package_type="pip", source=str(file_path))
            )

        # Scan dev-packages
        dev_packages = data.get("dev-packages", {})
        for name, version_info in dev_packages.items():
            if isinstance(version_info, str):
                version = version_info
            elif isinstance(version_info, dict):
                version = version_info.get("version", "latest")
            else:
                version = "latest"

            dependencies.append(
                Dependency(name=name, version=version, package_type="pip", source=str(file_path))
            )

        return dependencies

    def _scan_pyproject_toml(self, file_path: Path) -> List[Dependency]:
        """Scan pyproject.toml."""
        dependencies = []

        with open(file_path, "r") as f:
            data = toml.load(f)

        # Scan dependencies
        deps = data.get("project", {}).get("dependencies", [])
        for dep in deps:
            if isinstance(dep, str):
                name, version = self._parse_pep_508(dep)
                dependencies.append(
                    Dependency(
                        name=name, version=version, package_type="pip", source=str(file_path)
                    )
                )

        # Scan optional dependencies
        optional_deps = data.get("project", {}).get("optional-dependencies", {})
        for group, deps in optional_deps.items():
            for dep in deps:
                if isinstance(dep, str):
                    name, version = self._parse_pep_508(dep)
                    dependencies.append(
                        Dependency(
                            name=name, version=version, package_type="pip", source=str(file_path)
                        )
                    )

        return dependencies

    def _parse_pep_508(self, dependency: str) -> Tuple[str, str]:
        """Parse PEP 508 dependency specification."""
        # Simple parsing for name==version
        if "==" in dependency:
            return dependency.split("==", 1)
        elif ">=" in dependency:
            return dependency.split(">=", 1)
        elif "<=" in dependency:
            return dependency.split("<=", 1)
        elif "~=" in dependency:
            return dependency.split("~=~", 1)
        else:
            return dependency, "latest"

    def _scan_package_json(self, file_path: Path) -> List[Dependency]:
        """Scan package.json."""
        dependencies = []

        with open(file_path, "r") as f:
            data = json.load(f)

        # Scan dependencies
        deps = data.get("dependencies", {})
        for name, version in deps.items():
            dependencies.append(
                Dependency(name=name, version=version, package_type="npm", source=str(file_path))
            )

        # Scan devDependencies
        dev_deps = data.get("devDependencies", {})
        for name, version in dev_deps.items():
            dependencies.append(
                Dependency(name=name, version=version, package_type="npm", source=str(file_path))
            )

        return dependencies

    def _scan_yarn_lock(self, file_path: Path) -> List[Dependency]:
        """Scan yarn.lock."""
        dependencies = []

        with open(file_path, "r") as f:
            content = f.read()

        # Parse yarn.lock format
        current_package = None
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                if line.endswith(":"):
                    # Package name line
                    current_package = line[:-1].strip('"')
                elif current_package and line.startswith("version"):
                    # Version line
                    version = line.split('"')[1] if '"' in line else "latest"
                    name = current_package.split("@")[-1]  # Remove @npm/ prefix

                    dependencies.append(
                        Dependency(
                            name=name, version=version, package_type="npm", source=str(file_path)
                        )
                    )

        return dependencies

    def _scan_cargo_toml(self, file_path: Path) -> List[Dependency]:
        """Scan Cargo.toml."""
        dependencies = []

        with open(file_path, "r") as f:
            data = toml.load(f)

        # Scan dependencies
        deps = data.get("dependencies", {})
        for name, version_info in deps.items():
            if isinstance(version_info, str):
                version = version_info
            elif isinstance(version_info, dict):
                version = version_info.get("version", "latest")
            else:
                version = "latest"

            dependencies.append(
                Dependency(name=name, version=version, package_type="cargo", source=str(file_path))
            )

        return dependencies

    def _scan_go_mod(self, file_path: Path) -> List[Dependency]:
        """Scan go.mod."""
        dependencies = []

        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("require "):
                    # Parse require line
                    parts = line.split()
                    if len(parts) >= 2:
                        module = parts[1].strip('"')
                        version = parts[2].strip('"') if len(parts) > 2 else "latest"

                        dependencies.append(
                            Dependency(
                                name=module,
                                version=version,
                                package_type="go",
                                source=str(file_path),
                            )
                        )

        return dependencies

    def _scan_composer_json(self, file_path: Path) -> List[Dependency]:
        """Scan composer.json."""
        dependencies = []

        with open(file_path, "r") as f:
            data = json.load(f)

        # Scan require
        deps = data.get("require", {})
        for name, version in deps.items():
            dependencies.append(
                Dependency(
                    name=name, version=version, package_type="composer", source=str(file_path)
                )
            )

        # Scan require-dev
        dev_deps = data.get("require-dev", {})
        for name, version in dev_deps.items():
            dependencies.append(
                Dependency(
                    name=name, version=version, package_type="composer", source=str(file_path)
                )
            )

        return dependencies


class LicenseChecker:
    """Check for license compliance."""

    def __init__(self):
        self.allowed_licenses = {
            "MIT",
            "Apache-2.0",
            "BSD-2-Clause",
            "BSD-3-Clause",
            "ISC",
            "Unlicense",
        }
        self.restricted_licenses = {"GPL-3.0", "AGPL-3.0", "LGPL-3.0", "GPL-2.0", "AGPL-1.0"}

    def check_dependency_license(self, dependency: Dependency) -> Tuple[str, str]:
        """Check if dependency license is allowed."""
        if not dependency.license:
            return "unknown", "License not specified"

        license_name = dependency.license.upper()

        if license_name in self.restricted_licenses:
            return "restricted", f"Restricted license: {license_name}"
        elif license_name in self.allowed_licenses:
            return "allowed", f"Allowed license: {license_name}"
        else:
            return "warning", f"Unknown license: {license_name}"

    def get_license_info(self, package_name: str, package_type: str) -> Optional[str]:
        """Get license information for a package."""
        try:
            if package_type == "pip":
                return self._get_pip_license(package_name)
            elif package_type == "npm":
                return self._get_npm_license(package_name)
            elif package_type == "cargo":
                return self._get_cargo_license(package_name)
        except Exception as e:
            logger.error(f"Failed to get license for {package_name}: {e}")

        return None

    def _get_pip_license(self, package_name: str) -> Optional[str]:
        """Get license for Python package."""
        try:
            # Try to get license from PyPI
            url = f"https://pypi.org/pypi/{package_name}/json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            info = data.get("info", {})
            return info.get("license")
        except Exception:
            return None

    def _get_npm_license(self, package_name: str) -> Optional[str]:
        """Get license for npm package."""
        try:
            url = f"https://registry.npmjs.org/{package_name}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            latest = data.get("latest", {})
            return latest.get("license")
        except Exception:
            return None

    def _get_cargo_license(self, package_name: str) -> Optional[str]:
        """Get license for Rust package."""
        try:
            url = f"https://crates.io/api/v1/crates/{package_name}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            crate = data.get("crate", {})
            return crate.get("license")
        except Exception:
            return None


class SupplyChainVerifier:
    """Main supply chain verifier."""

    def __init__(self):
        self.scanner = DependencyScanner()
        self.vuln_db = VulnerabilityDatabase()
        self.license_checker = LicenseChecker()

    def verify_project(
        self, project_path: str, config: Optional[Dict[str, Any]] = None
    ) -> VerificationResult:
        """Verify entire project supply chain."""
        start_time = time.time()

        # Get configuration
        config = config or {}
        max_risk_score = config.get("max_risk_score", 70)
        check_licenses = config.get("check_licenses", True)
        check_vulnerabilities = config.get("check_vulnerabilities", True)

        # Scan dependencies
        dependencies = self.scanner.scan_project(project_path)

        if not dependencies:
            return VerificationResult(
                status=VerificationStatus.WARNING,
                dependencies_checked=0,
                vulnerabilities_found=0,
                critical_vulnerabilities=0,
                high_vulnerabilities=0,
                medium_vulnerabilities=0,
                low_vulnerabilities=0,
                risk_score=0,
                details={"message": "No dependencies found"},
            )

        # Check vulnerabilities
        critical_vulns = high_vulns = medium_vulns = low_vulns = 0
        total_vulnerabilities = 0

        if check_vulnerabilities:
            for dep in dependencies:
                ecosystem = self._get_ecosystem_for_package_type(dep.package_type)
                vulns = self.vuln_db.query_vulnerabilities(dep.name, dep.version, ecosystem)
                dep.vulnerabilities = vulns

                for vuln in vulns:
                    total_vulnerabilities += 1
                    if vuln.severity == VulnerabilitySeverity.CRITICAL:
                        critical_vulns += 1
                    elif vuln.severity == VulnerabilitySeverity.HIGH:
                        high_vulns += 1
                    elif vuln.severity == VulnerabilitySeverity.MEDIUM:
                        medium_vulns += 1
                    elif vuln.severity == VulnerabilitySeverity.LOW:
                        low_vulns += 1

        # Check licenses
        license_issues = []
        if check_licenses:
            for dep in dependencies:
                # Get license if not already known
                if not dep.license:
                    dep.license = (
                        self.license_checker.get_license_info(dep.name, dep.package_type)
                        or "Unknown"
                    )

                status, message = self.license_checker.check_dependency_license(dep)
                if status == "restricted":
                    license_issues.append(f"{dep.name}: {message}")
                elif status == "warning":
                    license_issues.append(f"{dep.name}: {message}")

        # Calculate risk scores
        total_risk_score = 0
        for dep in dependencies:
            dep.risk_score = self._calculate_dependency_risk(dep)
            total_risk_score += dep.risk_score

        # Determine overall status
        status = VerificationStatus.VERIFIED
        if critical_vulns > 0:
            status = VerificationStatus.FAILED
        elif high_vulns > 5 or total_risk_score > max_risk_score:
            status = VerificationStatus.WARNING
        elif license_issues:
            status = VerificationStatus.WARNING

        # Create result
        result = VerificationResult(
            status=status,
            dependencies_checked=len(dependencies),
            vulnerabilities_found=total_vulnerabilities,
            critical_vulnerabilities=critical_vulns,
            high_vulnerabilities=high_vulns,
            medium_vulnerabilities=medium_vulns,
            low_vulnerabilities=low_vulns,
            license_issues=license_issues,
            risk_score=total_risk_score,
            verification_time=time.time() - start_time,
            details={
                "dependencies": [
                    {
                        "name": dep.name,
                        "version": dep.version,
                        "type": dep.package_type,
                        "risk_score": dep.risk_score,
                        "vulnerabilities": len(dep.vulnerabilities),
                        "license": dep.license,
                    }
                    for dep in dependencies
                ]
            },
        )

        return result

    def _get_ecosystem_for_package_type(self, package_type: str) -> str:
        """Map package type to OSV ecosystem."""
        mapping = {
            "pip": "PyPI",
            "npm": "npm",
            "cargo": "crates.io",
            "go": "Go",
            "composer": "Packagist",
        }
        return mapping.get(package_type, "PyPI")

    def _calculate_dependency_risk(self, dependency: Dependency) -> int:
        """Calculate risk score for a dependency."""
        risk_score = 0

        # Base risk
        risk_score += 10

        # Vulnerability risk
        for vuln in dependency.vulnerabilities:
            if vuln.severity == VulnerabilitySeverity.CRITICAL:
                risk_score += 50
            elif vuln.severity == VulnerabilitySeverity.HIGH:
                risk_score += 30
            elif vuln.severity == VulnerabilitySeverity.MEDIUM:
                risk_score += 15
            elif vuln.severity == VulnerabilitySeverity.LOW:
                risk_score += 5

        # License risk
        if dependency.license:
            license_status, _ = self.license_checker.check_dependency_license(dependency)
            if license_status == "restricted":
                risk_score += 25
            elif license_status == "unknown":
                risk_score += 10

        # Popularity risk (unknown packages are riskier)
        # This is a simplified check - in practice, you'd check download counts, etc.
        if dependency.name.startswith("test-") or dependency.name.startswith("dev-"):
            risk_score += 5

        return min(risk_score, 100)


# Global supply chain verifier
supply_chain_verifier = SupplyChainVerifier()
