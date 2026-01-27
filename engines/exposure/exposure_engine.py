"""
Exposure Engine - Score asset exposure and attack surface.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from engines.base_engine import BaseEngine, ScoringResult, ScoringUtils
from core.models import Entity, Signal, EntityType, SignalType


@dataclass
class ExposureFactors:
    """Asset exposure assessment factors."""
    is_public: bool = False
    services_exposed: int = 0
    protocols_exposed: List[str] = field(default_factory=list)
    dns_records: int = 0
    certificates_found: int = 0
    subdomains: int = 0
    hosted_services: int = 0
    http_headers: int = 0
    cdn_used: bool = False
    waf_detected: bool = False
    authentication_required: bool = False
    sensitive_headers_missing: int = 0


class ExposureEngine(BaseEngine):
    """Asset exposure scoring engine."""

    DEFAULT_CONFIG = {
        "public_weight": 30,
        "service_weight": 25,
        "protocol_weight": 20,
        "subdomain_weight": 15,
        "security_controls_factor": 0.8,  # Reduction factor for security controls
        "exposure_type_scores": {
            "dns": 10,
            "certificate": 15,
            "http": 25,
            "https": 15,
            "ftp": 30,
            "ssh": 20,
            "rdp": 35,
            "smtp": 25,
            "dns_server": 35,
            "web_service": 30,
            "database": 40,
            "api": 25,
        },
    }

    def __init__(self):
        """Initialize Exposure Engine."""
        super().__init__("ExposureEngine", version="1.0.0")
        self.config = self.DEFAULT_CONFIG.copy()

    def score(self, entity: Entity, context: Any = None) -> ScoringResult:
        """Score entity exposure.
        
        Args:
            entity: Entity to score
            context: Optional context with signals
            
        Returns:
            ScoringResult with exposure score
        """
        self.run_count += 1
        self.last_run = datetime.utcnow()

        try:
            # Check if entity is exposable
            if entity.entity_type not in [
                EntityType.DOMAIN,
                EntityType.IP_ADDRESS,
                EntityType.SERVICE,
                EntityType.URL,
            ]:
                return ScoringResult(
                    engine_name=self.name,
                    entity_id=entity.id,
                    score=0,
                    severity="info",
                    details={"reason": "Entity type not exposable"},
                )

            # Extract exposure factors
            factors = self._extract_exposure_factors(entity, context)
            
            # Calculate base exposure score
            base_score = self._calculate_exposure_score(factors)
            
            # Apply security controls reduction
            final_score = self._apply_security_controls(base_score, factors)
            
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
                    "is_public": factors.is_public,
                    "services_exposed": factors.services_exposed,
                    "protocols": factors.protocols_exposed,
                    "subdomains": factors.subdomains,
                },
                metrics={
                    "public_exposure": 30 if factors.is_public else 0,
                    "service_exposure": min(factors.services_exposed * 10, 100),
                    "protocol_risk": min(len(factors.protocols_exposed) * 15, 100),
                    "infrastructure_footprint": min(
                        (factors.subdomains + factors.dns_records) * 5, 100
                    ),
                },
                recommendations=recommendations,
            )
        except Exception as e:
            self.error_count += 1
            raise Exception(f"Exposure scoring failed: {str(e)}")

    def _extract_exposure_factors(self, entity: Entity, context: Any) -> ExposureFactors:
        """Extract exposure factors from entity.
        
        Args:
            entity: Entity to analyze
            context: Optional context with signals
            
        Returns:
            ExposureFactors object
        """
        factors = ExposureFactors()
        
        # Determine if public
        if entity.entity_type == EntityType.DOMAIN:
            factors.is_public = True
        elif entity.entity_type == EntityType.IP_ADDRESS:
            ip_str = entity.name
            # Simple check for private ranges
            if not (
                ip_str.startswith("10.") or
                ip_str.startswith("192.168.") or
                ip_str.startswith("172.")
            ):
                factors.is_public = True
        
        # Extract signals if context provided
        if context and hasattr(context, 'get_signals_for_entity'):
            signals = context.get_signals_for_entity(entity.id)
            
            for signal in signals:
                if signal.signal_type == SignalType.OPEN_PORT:
                    factors.services_exposed += 1
                    port_data = signal.data.get("port")
                    protocol = signal.data.get("protocol", "unknown")
                    if protocol not in factors.protocols_exposed:
                        factors.protocols_exposed.append(protocol)
                
                elif signal.signal_type == SignalType.DNS_RECORD:
                    factors.dns_records += 1
                
                elif signal.signal_type == SignalType.CERTIFICATE:
                    factors.certificates_found += 1
                
                elif signal.signal_type == SignalType.HTTP_HEADER:
                    factors.http_headers += 1
                    headers = signal.data.get("headers", {})
                    # Check for security headers
                    security_headers = [
                        "Strict-Transport-Security",
                        "X-Content-Type-Options",
                        "X-Frame-Options",
                        "Content-Security-Policy",
                    ]
                    for header in security_headers:
                        if header not in headers:
                            factors.sensitive_headers_missing += 1
        
        # Extract properties
        if "subdomains" in entity.properties:
            factors.subdomains = entity.properties["subdomains"]
        
        if "services" in entity.properties:
            factors.hosted_services = len(entity.properties["services"])
        
        if entity.properties.get("cdn_used"):
            factors.cdn_used = True
        
        if entity.properties.get("waf_detected"):
            factors.waf_detected = True
        
        if entity.properties.get("authentication_required"):
            factors.authentication_required = True
        
        return factors

    def _calculate_exposure_score(self, factors: ExposureFactors) -> float:
        """Calculate exposure score.
        
        Args:
            factors: ExposureFactors object
            
        Returns:
            Exposure score 0-100
        """
        score = 0
        
        # Public exposure
        if factors.is_public:
            score += self.config["public_weight"]
        
        # Service exposure
        service_score = min(factors.services_exposed * 5, 100)
        score += (service_score * self.config["service_weight"]) / 100
        
        # Protocol risk
        protocol_score = min(len(factors.protocols_exposed) * 15, 100)
        score += (protocol_score * self.config["protocol_weight"]) / 100
        
        # Infrastructure footprint
        footprint = (factors.subdomains + factors.dns_records) * 5
        footprint_score = min(footprint, 100)
        score += (footprint_score * self.config["subdomain_weight"]) / 100
        
        return min(score, 100)

    def _apply_security_controls(self, score: float, factors: ExposureFactors) -> float:
        """Apply security controls reduction to score.
        
        Args:
            score: Base score
            factors: ExposureFactors object
            
        Returns:
            Adjusted score
        """
        reduction = 1.0
        
        if factors.waf_detected:
            reduction *= 0.7
        
        if factors.cdn_used:
            reduction *= 0.8
        
        if factors.authentication_required:
            reduction *= 0.75
        
        if factors.http_headers >= 2:
            reduction *= 0.85
        
        return score * reduction

    def _generate_recommendations(
        self, factors: ExposureFactors, score: float
    ) -> List[str]:
        """Generate exposure mitigation recommendations.
        
        Args:
            factors: ExposureFactors object
            score: Final exposure score
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if factors.is_public and score > 50:
            recommendations.append("Asset is publicly exposed - review access controls")
        
        if factors.services_exposed > 3:
            recommendations.append("Multiple services exposed - disable unnecessary services")
        
        if factors.subdomains > 10:
            recommendations.append("Large subdomain footprint - audit for forgotten subdomains")
        
        if factors.sensitive_headers_missing > 2:
            recommendations.append("Security headers missing - implement security headers")
        
        if not factors.waf_detected and factors.is_public:
            recommendations.append("No WAF detected - consider implementing WAF")
        
        if not factors.authentication_required and factors.is_public:
            recommendations.append("No authentication required - add authentication layer")
        
        if score >= 70:
            recommendations.append("HIGH EXPOSURE: Implement defense-in-depth strategy")
        
        return recommendations

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate exposure engine configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid
        """
        required_keys = [
            "public_weight",
            "service_weight",
            "protocol_weight",
            "subdomain_weight",
        ]
        
        if not all(key in config for key in required_keys):
            return False
        
        # Weights should sum to ~100
        weight_sum = (
            config["public_weight"] +
            config["service_weight"] +
            config["protocol_weight"] +
            config["subdomain_weight"]
        )
        
        if weight_sum != 100:
            return False
        
        return True
