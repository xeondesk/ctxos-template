"""
Comprehensive unit tests for Exposure Engine scoring.
"""

import pytest
from datetime import datetime

from core.models import Entity, EntityType, Signal, SignalType, SignalSeverity, Context
from engines import ExposureEngine, ScoringResult


class TestExposureEngine:
    """Comprehensive tests for Exposure Engine."""
    
    @pytest.fixture
    def engine(self):
        """Create Exposure Engine instance."""
        return ExposureEngine()
    
    @pytest.fixture
    def domain_entity(self):
        """Create sample domain entity."""
        return Entity(
            name="example.com",
            entity_type=EntityType.DOMAIN,
            source="test"
        )
    
    @pytest.fixture
    def ip_entity(self):
        """Create sample IP entity."""
        return Entity(
            name="192.0.2.1",
            entity_type=EntityType.IP_ADDRESS,
            source="test"
        )
    
    @pytest.fixture
    def service_entity(self):
        """Create sample service entity."""
        return Entity(
            name="web-service",
            entity_type=EntityType.SERVICE,
            source="test"
        )
    
    # ========== Initialization Tests ==========
    
    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine.name == "ExposureEngine"
        assert engine.version == "1.0.0"
        assert engine.enabled is True
        assert engine.config == engine.DEFAULT_CONFIG
    
    def test_engine_configuration(self, engine):
        """Test engine configuration."""
        new_config = {
            "public_weight": 40,
            "service_weight": 30,
        }
        assert engine.configure(new_config) is True
        assert engine.config["public_weight"] == 40
    
    # ========== Entity Type Tests ==========
    
    def test_exposable_entity_types(self, engine):
        """Test only exposable entity types are scored."""
        exposable = [EntityType.DOMAIN, EntityType.IP_ADDRESS, EntityType.SERVICE, EntityType.URL]
        
        for etype in exposable:
            entity = Entity(
                name=f"test-{etype.value}",
                entity_type=etype,
                source="test"
            )
            result = engine.score(entity)
            
            # Should produce valid score
            assert isinstance(result, ScoringResult)
    
    def test_non_exposable_entity_types(self, engine):
        """Test non-exposable entity types return zero score."""
        non_exposable = [EntityType.EMAIL, EntityType.PERSON, EntityType.FILE]
        
        for etype in non_exposable:
            entity = Entity(
                name=f"test-{etype.value}",
                entity_type=etype,
                source="test"
            )
            result = engine.score(entity)
            
            # Should return 0 score for non-exposable types
            assert result.score == 0
            assert result.severity == "info"
    
    # ========== Public Exposure Tests ==========
    
    def test_public_domain_scoring(self, engine, domain_entity):
        """Test scoring of public domain."""
        result = engine.score(domain_entity)
        
        assert isinstance(result, ScoringResult)
        assert result.engine_name == "ExposureEngine"
        assert result.entity_id == domain_entity.id
        assert 0 <= result.score <= 100
    
    def test_public_ip_scoring(self, engine, ip_entity):
        """Test scoring of public IP."""
        result = engine.score(ip_entity)
        
        assert isinstance(result, ScoringResult)
        assert 0 <= result.score <= 100
    
    # ========== Service Exposure Tests ==========
    
    def test_service_exposure_single_port(self, engine, service_entity):
        """Test service exposure with single port."""
        context = Context("test")
        context.add_entity(service_entity)
        
        # Add HTTP service signal
        signal = Signal(
            source="scanner",
            signal_type=SignalType.OPEN_PORT,
            data={"port": 80, "service": "http"},
            entity_id=service_entity.id,
            severity=SignalSeverity.MEDIUM
        )
        context.add_signal(signal)
        
        result = engine.score(service_entity, context)
        
        assert result.score > 0
        assert "service_exposure" in result.metrics
    
    def test_service_exposure_multiple_ports(self, engine, service_entity):
        """Test service exposure with multiple ports."""
        context = Context("test")
        context.add_entity(service_entity)
        
        # Add multiple service signals
        ports = [(80, "http"), (443, "https"), (22, "ssh"), (3306, "mysql")]
        for port, service in ports:
            signal = Signal(
                source="scanner",
                signal_type=SignalType.OPEN_PORT,
                data={"port": port, "service": service},
                entity_id=service_entity.id,
                severity=SignalSeverity.MEDIUM
            )
            context.add_signal(signal)
        
        result = engine.score(service_entity, context)
        
        assert result.score > 20  # Multiple services increase exposure
        assert result.metrics.get("service_exposure", 0) > 0
    
    def test_critical_service_exposure(self, engine, service_entity):
        """Test exposure of critical services."""
        context = Context("test")
        context.add_entity(service_entity)
        
        # Add critical service signals
        critical_services = [
            (3306, "mysql"),  # Database
            (5432, "postgres"),  # Database
            (27017, "mongodb"),  # NoSQL
        ]
        
        for port, service in critical_services:
            signal = Signal(
                source="scanner",
                signal_type=SignalType.OPEN_PORT,
                data={"port": port, "service": service},
                entity_id=service_entity.id,
                severity=SignalSeverity.HIGH
            )
            context.add_signal(signal)
        
        result = engine.score(service_entity, context)
        
        # Databases exposed should have high exposure score
        assert result.score >= 60
        assert result.severity in ["critical", "high"]
    
    # ========== Protocol Exposure Tests ==========
    
    def test_protocol_exposure_http(self, engine, domain_entity):
        """Test HTTP protocol exposure."""
        context = Context("test")
        context.add_entity(domain_entity)
        
        signal = Signal(
            source="scanner",
            signal_type=SignalType.HTTP_HEADER,
            data={"protocol": "http"},
            entity_id=domain_entity.id,
            severity=SignalSeverity.MEDIUM
        )
        context.add_signal(signal)
        
        result = engine.score(domain_entity, context)
        
        assert result.score > 0
    
    def test_protocol_exposure_multiple(self, engine, domain_entity):
        """Test multiple protocol exposure."""
        context = Context("test")
        context.add_entity(domain_entity)
        
        protocols = ["http", "https", "ftp", "smtp"]
        for protocol in protocols:
            signal = Signal(
                source="scanner",
                signal_type=SignalType.HTTP_HEADER if protocol in ["http", "https"] else SignalType.OPEN_PORT,
                data={"protocol": protocol},
                entity_id=domain_entity.id,
                severity=SignalSeverity.LOW
            )
            context.add_signal(signal)
        
        result = engine.score(domain_entity, context)
        
        assert result.score > 0
        assert result.severity in ["critical", "high", "medium", "low"]
    
    # ========== Subdomain Tests ==========
    
    def test_subdomain_exposure(self, engine, domain_entity):
        """Test subdomain exposure scoring."""
        context = Context("test")
        context.add_entity(domain_entity)
        
        # Add subdomain signals
        for i in range(5):
            signal = Signal(
                source="scanner",
                signal_type=SignalType.DOMAIN_REGISTRATION,
                data={"subdomain": f"sub{i}.example.com"},
                entity_id=domain_entity.id,
                severity=SignalSeverity.LOW
            )
            context.add_signal(signal)
        
        result = engine.score(domain_entity, context)
        
        assert "subdomain_exposure" in result.metrics
    
    def test_subdomain_with_services(self, engine, domain_entity):
        """Test subdomain exposure with services."""
        context = Context("test")
        context.add_entity(domain_entity)
        
        # Add subdomain with service
        signal = Signal(
            source="scanner",
            signal_type=SignalType.DOMAIN_REGISTRATION,
            data={"subdomain": "api.example.com", "service": "rest-api"},
            entity_id=domain_entity.id,
            severity=SignalSeverity.MEDIUM
        )
        context.add_signal(signal)
        
        result = engine.score(domain_entity, context)
        
        assert result.score > 0
    
    # ========== Certificate Tests ==========
    
    def test_certificate_exposure(self, engine, domain_entity):
        """Test certificate exposure scoring."""
        context = Context("test")
        context.add_entity(domain_entity)
        
        signal = Signal(
            source="ct_monitor",
            signal_type=SignalType.CERTIFICATE,
            data={"issuer": "Let's Encrypt", "valid": True},
            entity_id=domain_entity.id,
            severity=SignalSeverity.LOW
        )
        context.add_signal(signal)
        
        result = engine.score(domain_entity, context)
        
        assert result.score > 0
    
    def test_certificate_issues(self, engine, domain_entity):
        """Test exposure of certificate issues."""
        context = Context("test")
        context.add_entity(domain_entity)
        
        signal = Signal(
            source="scanner",
            signal_type=SignalType.CERTIFICATE,
            data={"issue": "expired", "days_since_expiry": 30},
            entity_id=domain_entity.id,
            severity=SignalSeverity.HIGH
        )
        context.add_signal(signal)
        
        result = engine.score(domain_entity, context)
        
        assert result.score > 20
    
    # ========== Security Controls Tests ==========
    
    def test_security_controls_waf_detected(self, engine, domain_entity):
        """Test exposure reduction with WAF."""
        context = Context("test")
        context.add_entity(domain_entity)
        
        # Add signal indicating WAF protection
        signal = Signal(
            source="scanner",
            signal_type=SignalType.HTTP_HEADER,
            data={"security_control": "waf", "vendor": "CloudFlare"},
            entity_id=domain_entity.id,
            severity=SignalSeverity.INFO
        )
        context.add_signal(signal)
        
        result = engine.score(domain_entity, context)
        
        # Score should reflect security controls
        assert 0 <= result.score <= 100
    
    def test_security_controls_cdn_detected(self, engine, domain_entity):
        """Test exposure reduction with CDN."""
        context = Context("test")
        context.add_entity(domain_entity)
        
        signal = Signal(
            source="scanner",
            signal_type=SignalType.HTTP_HEADER,
            data={"security_control": "cdn", "vendor": "Akamai"},
            entity_id=domain_entity.id,
            severity=SignalSeverity.INFO
        )
        context.add_signal(signal)
        
        result = engine.score(domain_entity, context)
        
        assert 0 <= result.score <= 100
    
    def test_missing_security_headers(self, engine, domain_entity):
        """Test exposure increase with missing security headers."""
        context = Context("test")
        context.add_entity(domain_entity)
        
        # Add signal for missing security headers
        signal = Signal(
            source="scanner",
            signal_type=SignalType.HTTP_HEADER,
            data={"missing_headers": ["X-Frame-Options", "Content-Security-Policy", "X-Content-Type-Options"]},
            entity_id=domain_entity.id,
            severity=SignalSeverity.MEDIUM
        )
        context.add_signal(signal)
        
        result = engine.score(domain_entity, context)
        
        assert result.score > 0
    
    # ========== Severity Tests ==========
    
    def test_exposure_severity_levels(self, engine, domain_entity):
        """Test exposure severity level determination."""
        context = Context("test")
        context.add_entity(domain_entity)
        
        # Add high-exposure signal
        signal = Signal(
            source="scanner",
            signal_type=SignalType.OPEN_PORT,
            data={"port": 3306, "service": "database"},
            entity_id=domain_entity.id,
            severity=SignalSeverity.HIGH
        )
        context.add_signal(signal)
        
        result = engine.score(domain_entity, context)
        
        assert result.severity in ["critical", "high", "medium", "low", "info"]
    
    # ========== Serialization Tests ==========
    
    def test_exposure_result_serialization(self, engine, domain_entity):
        """Test exposure result serialization."""
        result = engine.score(domain_entity)
        
        result_dict = result.to_dict()
        
        assert result_dict["engine_name"] == "ExposureEngine"
        assert result_dict["entity_id"] == domain_entity.id
        assert "score" in result_dict
        assert "severity" in result_dict
    
    def test_exposure_result_deserialization(self, engine, domain_entity):
        """Test exposure result deserialization."""
        result = engine.score(domain_entity)
        result_dict = result.to_dict()
        
        restored = ScoringResult.from_dict(result_dict)
        
        assert restored.engine_name == result.engine_name
        assert restored.score == result.score
    
    # ========== Edge Cases ==========
    
    def test_score_domain_no_signals(self, engine, domain_entity):
        """Test scoring domain with no signals."""
        result = engine.score(domain_entity)
        
        assert 0 <= result.score <= 100
    
    def test_score_ip_no_signals(self, engine, ip_entity):
        """Test scoring IP with no signals."""
        result = engine.score(ip_entity)
        
        assert 0 <= result.score <= 100
    
    def test_empty_context(self, engine, domain_entity):
        """Test scoring with empty context."""
        context = Context("empty")
        
        result = engine.score(domain_entity, context)
        
        assert isinstance(result, ScoringResult)
