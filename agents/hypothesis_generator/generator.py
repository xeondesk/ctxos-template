"""
Hypothesis Generator Agent - Suggest likely security issues and attack scenarios.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import random

from core.models.context import Context
from core.models.entity import Entity
from core.models.signal import Signal
from core.scoring.risk import ScoringResult
from agents.base_agent_async import BaseAgentAsync, AgentResult
from agents.audit_system.audit_logger import AuditLevel


class HypothesisType(Enum):
    """Types of security hypotheses."""
    VULNERABILITY_EXPLOITATION = "vulnerability_exploitation"
    LATERAL_MOVEMENT = "lateral_movement"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    PERSISTENCE_MECHANISM = "persistence_mechanism"
    SUPPLY_CHAIN = "supply_chain"
    MISCONFIGURATION = "misconfiguration"
    INSIDER_THREAT = "insider_threat"
    ADVANCED_PERSISTENT_THREAT = "advanced_persistent_threat"
    RANSOMWARE = "ransomware"


class ConfidenceLevel(Enum):
    """Confidence levels for hypotheses."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class Hypothesis:
    """Security hypothesis with supporting evidence."""
    id: str
    title: str
    description: str
    hypothesis_type: HypothesisType
    confidence: ConfidenceLevel
    likelihood: float  # 0.0-1.0
    impact: str  # critical/high/medium/low
    supporting_signals: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)
    attack_steps: List[str] = field(default_factory=list)
    mitigations: List[str] = field(default_factory=list)
    related_entities: List[str] = field(default_factory=list)
    time_to_compromise: Optional[str] = None
    detection_difficulty: str = "medium"  # easy/medium/hard
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "hypothesis_type": self.hypothesis_type.value,
            "confidence": self.confidence.value,
            "likelihood": self.likelihood,
            "impact": self.impact,
            "supporting_signals": self.supporting_signals,
            "missing_evidence": self.missing_evidence,
            "attack_steps": self.attack_steps,
            "mitigations": self.mitigations,
            "related_entities": self.related_entities,
            "time_to_compromise": self.time_to_compromise,
            "detection_difficulty": self.detection_difficulty,
        }


@dataclass
class HypothesisAnalysis:
    """Complete hypothesis analysis result."""
    total_hypotheses: int = 0
    high_confidence: int = 0
    medium_confidence: int = 0
    low_confidence: int = 0
    critical_impact: int = 0
    high_impact: int = 0
    hypotheses: List[Hypothesis] = field(default_factory=list)
    attack_surface_score: float = 0.0
    threat_landscape: Dict[str, int] = field(default_factory=dict)
    recommended_investigations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_hypotheses": self.total_hypotheses,
            "high_confidence": self.high_confidence,
            "medium_confidence": self.medium_confidence,
            "low_confidence": self.low_confidence,
            "critical_impact": self.critical_impact,
            "high_impact": self.high_impact,
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "attack_surface_score": self.attack_surface_score,
            "threat_landscape": self.threat_landscape,
            "recommended_investigations": self.recommended_investigations,
        }


class HypothesisGenerator(BaseAgentAsync):
    """Agent that generates security hypotheses based on available data."""
    
    def __init__(
        self,
        name: str = "HypothesisGenerator",
        version: str = "1.0.0",
        max_hypotheses: int = 10,
        min_confidence_threshold: float = 0.3,
        enable_creative_hypotheses: bool = True,
        threat_intelligence_weight: float = 0.3,
    ):
        """Initialize hypothesis generator.
        
        Args:
            name: Agent name
            version: Agent version
            max_hypotheses: Maximum hypotheses to generate
            min_confidence_threshold: Minimum confidence for hypotheses
            enable_creative_hypotheses: Enable creative/advanced hypotheses
            threat_intelligence_weight: Weight for threat intelligence
        """
        super().__init__(name, version)
        self.max_hypotheses = max_hypotheses
        self.min_confidence_threshold = min_confidence_threshold
        self.enable_creative_hypotheses = enable_creative_hypotheses
        self.threat_intelligence_weight = threat_intelligence_weight
        
        # Hypothesis generation rules
        self.hypothesis_rules = self._initialize_hypothesis_rules()
        
        # Attack patterns and TTPs
        self.attack_patterns = self._initialize_attack_patterns()
        
        # Confidence thresholds
        self.confidence_thresholds = {
            ConfidenceLevel.VERY_HIGH: 0.9,
            ConfidenceLevel.HIGH: 0.7,
            ConfidenceLevel.MEDIUM: 0.5,
            ConfidenceLevel.LOW: 0.3,
            ConfidenceLevel.VERY_LOW: 0.1,
        }
    
    async def analyze(
        self,
        context: Context,
        scoring_result: Optional[ScoringResult] = None,
    ) -> AgentResult:
        """Analyze context and generate security hypotheses.
        
        Args:
            context: Input context with entity and signals
            scoring_result: Optional scoring result from engines
            
        Returns:
            AgentResult with hypothesis analysis
        """
        try:
            # Generate hypotheses
            analysis = await self._generate_hypotheses(context, scoring_result)
            
            # Create agent result
            result = AgentResult(
                agent_name=self.name,
                success=True,
                output={
                    "hypothesis_analysis": analysis.to_dict(),
                    "summary": {
                        "total_hypotheses": analysis.total_hypotheses,
                        "high_confidence": analysis.high_confidence,
                        "critical_impact": analysis.critical_impact,
                        "attack_surface_score": analysis.attack_surface_score,
                    }
                }
            )
            
            return result
            
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                success=False,
                error=f"Failed to generate hypotheses: {str(e)}"
            )
    
    async def _generate_hypotheses(
        self,
        context: Context,
        scoring_result: Optional[ScoringResult] = None,
    ) -> HypothesisAnalysis:
        """Generate comprehensive security hypotheses."""
        analysis = HypothesisAnalysis()
        
        if not context.entity:
            return analysis
        
        # Generate hypotheses from different sources
        await self._generate_signal_based_hypotheses(context, analysis)
        await self._generate_entity_based_hypotheses(context, analysis)
        await self._generate_scoring_based_hypotheses(scoring_result, analysis)
        
        if self.enable_creative_hypotheses:
            await self._generate_creative_hypotheses(context, analysis)
        
        # Sort and filter hypotheses
        analysis.hypotheses = self._filter_and_sort_hypotheses(analysis.hypotheses)
        
        # Calculate analysis metrics
        self._calculate_analysis_metrics(analysis)
        
        # Generate recommended investigations
        analysis.recommended_investigations = self._generate_investigations(analysis)
        
        return analysis
    
    async def _generate_signal_based_hypotheses(self, context: Context, analysis: HypothesisAnalysis) -> None:
        """Generate hypotheses based on signal patterns."""
        if not context.signals:
            return
        
        # Group signals by type and severity
        signal_groups = self._group_signals(context.signals)
        
        # Generate hypotheses for each signal pattern
        for signal_type, signals in signal_groups.items():
            hypotheses = await self._analyze_signal_pattern(signal_type, signals, context)
            analysis.hypotheses.extend(hypotheses)
        
        # Generate correlation hypotheses
        correlation_hypotheses = await self._generate_correlation_hypotheses(context.signals, context)
        analysis.hypotheses.extend(correlation_hypotheses)
    
    async def _generate_entity_based_hypotheses(self, context: Context, analysis: HypothesisAnalysis) -> None:
        """Generate hypotheses based on entity characteristics."""
        entity = context.entity
        
        if not entity:
            return
        
        # Entity type-based hypotheses
        entity_hypotheses = await self._analyze_entity_characteristics(entity, context)
        analysis.hypotheses.extend(entity_hypotheses)
        
        # Entity property-based hypotheses
        if entity.properties:
            property_hypotheses = await self._analyze_entity_properties(entity, context)
            analysis.hypotheses.extend(property_hypotheses)
    
    async def _generate_scoring_based_hypotheses(
        self,
        scoring_result: Optional[ScoringResult],
        analysis: HypothesisAnalysis,
    ) -> None:
        """Generate hypotheses based on scoring results."""
        if not scoring_result:
            return
        
        # High score hypotheses
        if scoring_result.score >= 70:
            hypothesis = Hypothesis(
                id=f"high_score_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                title=f"High Risk Score Indicates Active Threat",
                description=f"Entity scored {scoring_result.score}/100 suggesting active security issues requiring immediate attention",
                hypothesis_type=HypothesisType.ADVANCED_PERSISTENT_THREAT,
                confidence=self._score_to_confidence(scoring_result.score),
                likelihood=scoring_result.score / 100.0,
                impact=scoring_result.severity,
                supporting_signals=["scoring_result"],
                attack_steps=[
                    "Attacker has likely compromised the entity",
                    "Security controls may be bypassed or ineffective",
                    "Immediate investigation and containment required",
                ],
                mitigations=[
                    "Isolate affected systems",
                    "Conduct forensic analysis",
                    "Review and strengthen security controls",
                ],
                time_to_compromise="Unknown - likely already compromised",
                detection_difficulty="hard",
            )
            analysis.hypotheses.append(hypothesis)
    
    async def _generate_creative_hypotheses(self, context: Context, analysis: HypothesisAnalysis) -> None:
        """Generate creative/advanced security hypotheses."""
        creative_patterns = [
            {
                "type": HypothesisType.SUPPLY_CHAIN,
                "triggers": ["DEPENDENCY", "THIRD_PARTY"],
                "title": "Supply Chain Compromise",
                "description": "Entity may be compromised through trusted supply chain relationships",
            },
            {
                "type": HypothesisType.INSIDER_THREAT,
                "triggers": ["ACCESS_LOG", "PRIVILEGE_ESCALATION"],
                "title": "Potential Insider Threat",
                "description": "Unusual access patterns suggest potential insider threat activity",
            },
            {
                "type": HypothesisType.RANSOMWARE,
                "triggers": ["ENCRYPTION", "FILE_ACCESS"],
                "title": "Ransomware Attack Preparation",
                "description": "Signals indicate potential ransomware attack preparation phase",
            },
        ]
        
        for pattern in creative_patterns:
            if self._has_trigger_signals(context.signals, pattern["triggers"]):
                hypothesis = Hypothesis(
                    id=f"creative_{pattern['type'].value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    title=pattern["title"],
                    description=pattern["description"],
                    hypothesis_type=pattern["type"],
                    confidence=ConfidenceLevel.MEDIUM,
                    likelihood=0.4,
                    impact="high",
                    supporting_signals=pattern["triggers"],
                    attack_steps=self._generate_attack_steps(pattern["type"]),
                    mitigations=self._generate_mitigations(pattern["type"]),
                    detection_difficulty="medium",
                )
                analysis.hypotheses.append(hypothesis)
    
    def _group_signals(self, signals: List[Signal]) -> Dict[str, List[Signal]]:
        """Group signals by type."""
        groups = {}
        for signal in signals:
            if signal.signal_type not in groups:
                groups[signal.signal_type] = []
            groups[signal.signal_type].append(signal)
        return groups
    
    async def _analyze_signal_pattern(
        self,
        signal_type: str,
        signals: List[Signal],
        context: Context,
    ) -> List[Hypothesis]:
        """Analyze specific signal pattern for hypotheses."""
        hypotheses = []
        
        # Get hypothesis rules for this signal type
        rules = self.hypothesis_rules.get(signal_type, [])
        
        for rule in rules:
            if self._matches_rule(signals, rule):
                hypothesis = await self._create_hypothesis_from_rule(rule, signals, context)
                if hypothesis:
                    hypotheses.append(hypothesis)
        
        return hypotheses
    
    async def _generate_correlation_hypotheses(
        self,
        signals: List[Signal],
        context: Context,
    ) -> List[Hypothesis]:
        """Generate hypotheses from signal correlations."""
        hypotheses = []
        
        # Look for attack chains
        attack_chains = self._identify_attack_chains(signals)
        
        for chain in attack_chains:
            hypothesis = Hypothesis(
                id=f"attack_chain_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                title=f"Attack Chain Detected: {chain['name']}",
                description=f"Signals indicate progression through attack chain: {chain['description']}",
                hypothesis_type=HypothesisType.ADVANCED_PERSISTENT_THREAT,
                confidence=ConfidenceLevel.HIGH,
                likelihood=0.8,
                impact="critical",
                supporting_signals=[s.id for s in chain['signals']],
                attack_steps=chain['steps'],
                mitigations=[
                    "Break the attack chain at earliest possible step",
                    "Implement detection for each attack stage",
                    "Strengthen controls at transition points",
                ],
                time_to_compromise=chain.get('time_to_compromise', 'hours'),
                detection_difficulty="hard",
            )
            hypotheses.append(hypothesis)
        
        return hypotheses
    
    async def _analyze_entity_characteristics(self, entity: Entity, context: Context) -> List[Hypothesis]:
        """Analyze entity characteristics for hypotheses."""
        hypotheses = []
        
        # Critical entity hypotheses
        if entity.entity_type in {"host", "application", "database"}:
            hypothesis = Hypothesis(
                id=f"critical_entity_{entity.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                title=f"Critical Asset Targeting",
                description=f"{entity.entity_type} '{entity.name}' is a critical asset likely to be targeted by attackers",
                hypothesis_type=HypothesisType.ADVANCED_PERSISTENT_THREAT,
                confidence=ConfidenceLevel.MEDIUM,
                likelihood=0.6,
                impact="critical",
                supporting_signals=[f"entity_type:{entity.entity_type}"],
                attack_steps=[
                    "Reconnaissance of critical asset",
                    "Vulnerability identification",
                    "Exploitation and compromise",
                    "Establish persistence",
                ],
                mitigations=[
                    "Enhanced monitoring of critical assets",
                    "Regular vulnerability assessments",
                    "Network segmentation",
                    "Zero-trust access controls",
                ],
                related_entities=[entity.id],
                time_to_compromise="days",
                detection_difficulty="medium",
            )
            hypotheses.append(hypothesis)
        
        return hypotheses
    
    async def _analyze_entity_properties(self, entity: Entity, context: Context) -> List[Hypothesis]:
        """Analyze entity properties for hypotheses."""
        hypotheses = []
        
        props = entity.properties or {}
        
        # Public-facing assets
        if props.get("public", False) or props.get("exposed", False):
            hypothesis = Hypothesis(
                id=f"public_exposure_{entity.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                title="Public-Facing Asset Attack Surface",
                description="Public-facing exposure increases attack surface and risk of direct attacks",
                hypothesis_type=HypothesisType.VULNERABILITY_EXPLOITATION,
                confidence=ConfidenceLevel.HIGH,
                likelihood=0.7,
                impact="high",
                supporting_signals=["public_exposure"],
                attack_steps=[
                    "Internet reconnaissance",
                    "Vulnerability scanning",
                    "Exploitation of exposed services",
                ],
                mitigations=[
                    "Implement web application firewall",
                    "Regular security testing",
                    "Reduce exposed attack surface",
                    "Implement rate limiting",
                ],
                related_entities=[entity.id],
                time_to_compromise="hours",
                detection_difficulty="medium",
            )
            hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _matches_rule(self, signals: List[Signal], rule: Dict[str, Any]) -> bool:
        """Check if signals match hypothesis rule."""
        # Check signal count
        if "min_signals" in rule and len(signals) < rule["min_signals"]:
            return False
        
        # Check severity requirements
        if "min_severity" in rule:
            severity_levels = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
            max_severity = max(severity_levels.get(s.severity.lower(), 0) for s in signals)
            required_level = severity_levels.get(rule["min_severity"], 0)
            if max_severity < required_level:
                return False
        
        # Check specific patterns
        if "pattern" in rule:
            pattern = rule["pattern"]
            for signal in signals:
                if pattern in signal.description.lower():
                    return True
            return False
        
        return True
    
    async def _create_hypothesis_from_rule(
        self,
        rule: Dict[str, Any],
        signals: List[Signal],
        context: Context,
    ) -> Optional[Hypothesis]:
        """Create hypothesis from matching rule."""
        hypothesis_type = HypothesisType(rule["hypothesis_type"])
        
        hypothesis = Hypothesis(
            id=f"{hypothesis_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            title=rule["title"],
            description=rule["description"],
            hypothesis_type=hypothesis_type,
            confidence=self._calculate_confidence(rule, signals),
            likelihood=rule.get("likelihood", 0.5),
            impact=rule.get("impact", "medium"),
            supporting_signals=[s.id for s in signals],
            attack_steps=rule.get("attack_steps", []),
            mitigations=rule.get("mitigations", []),
            time_to_compromise=rule.get("time_to_compromise"),
            detection_difficulty=rule.get("detection_difficulty", "medium"),
        )
        
        return hypothesis
    
    def _has_trigger_signals(self, signals: List[Signal], triggers: List[str]) -> bool:
        """Check if context has trigger signals."""
        signal_types = {s.signal_type for s in signals}
        return any(trigger in signal_types for trigger in triggers)
    
    def _identify_attack_chains(self, signals: List[Signal]) -> List[Dict[str, Any]]:
        """Identify potential attack chains from signals."""
        chains = []
        
        # Common attack chain patterns
        chain_patterns = [
            {
                "name": "Reconnaissance to Exploitation",
                "description": "Discovery followed by vulnerability exploitation",
                "signal_sequence": ["DNS", "SUBDOMAIN", "PORT", "VULNERABILITY"],
                "steps": [
                    "DNS reconnaissance",
                    "Subdomain enumeration", 
                    "Port scanning",
                    "Vulnerability discovery",
                    "Exploitation",
                ],
                "time_to_compromise": "hours",
            },
            {
                "name": "Lateral Movement",
                "description": "Movement between compromised systems",
                "signal_sequence": ["AUTHENTICATION", "PRIVILEGE_ESCALATION", "LATERAL"],
                "steps": [
                    "Initial compromise",
                    "Credential theft",
                    "Privilege escalation",
                    "Lateral movement",
                ],
                "time_to_compromise": "days",
            },
        ]
        
        for pattern in chain_patterns:
            if self._matches_attack_chain(signals, pattern):
                chain_signals = [s for s in signals if s.signal_type in pattern["signal_sequence"]]
                chains.append({
                    **pattern,
                    "signals": chain_signals,
                })
        
        return chains
    
    def _matches_attack_chain(self, signals: List[Signal], pattern: Dict[str, Any]) -> bool:
        """Check if signals match attack chain pattern."""
        signal_types = {s.signal_type for s in signals}
        required_types = set(pattern["signal_sequence"])
        
        # Check if we have at least 3 of the required signal types
        overlap = len(signal_types & required_types)
        return overlap >= 3
    
    def _calculate_confidence(self, rule: Dict[str, Any], signals: List[Signal]) -> ConfidenceLevel:
        """Calculate confidence level for hypothesis."""
        base_confidence = rule.get("base_confidence", 0.5)
        
        # Boost confidence based on signal quality
        signal_boost = min(0.3, len(signals) * 0.1)
        
        # Boost confidence based on severity
        severity_levels = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
        max_severity = max(severity_levels.get(s.severity.lower(), 0) for s in signals)
        severity_boost = max_severity * 0.1
        
        total_confidence = base_confidence + signal_boost + severity_boost
        
        # Convert to confidence level
        if total_confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif total_confidence >= 0.7:
            return ConfidenceLevel.HIGH
        elif total_confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif total_confidence >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _score_to_confidence(self, score: float) -> ConfidenceLevel:
        """Convert numeric score to confidence level."""
        if score >= 90:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 80:
            return ConfidenceLevel.HIGH
        elif score >= 60:
            return ConfidenceLevel.MEDIUM
        elif score >= 40:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _generate_attack_steps(self, hypothesis_type: HypothesisType) -> List[str]:
        """Generate attack steps for hypothesis type."""
        step_templates = {
            HypothesisType.SUPPLY_CHAIN: [
                "Compromise trusted supplier",
                "Inject malicious code/components",
                "Distribute through legitimate channels",
                "Exploit trust relationships",
            ],
            HypothesisType.INSIDER_THREAT: [
                "Abuse legitimate access",
                "Exfiltrate sensitive data",
                "Cover tracks or maintain access",
                "Escalate privileges if needed",
            ],
            HypothesisType.RANSOMWARE: [
                "Initial access through phishing/vulnerability",
                "Deploy ransomware payload",
                "Encrypt critical files",
                "Demand ransom payment",
            ],
        }
        
        return step_templates.get(hypothesis_type, ["Attack steps not specified"])
    
    def _generate_mitigations(self, hypothesis_type: HypothesisType) -> List[str]:
        """Generate mitigations for hypothesis type."""
        mitigation_templates = {
            HypothesisType.SUPPLY_CHAIN: [
                "Implement software composition analysis",
                "Verify supplier security practices",
                "Monitor third-party dependencies",
                "Establish secure development practices",
            ],
            HypothesisType.INSIDER_THREAT: [
                "Implement principle of least privilege",
                "Monitor user behavior analytics",
                "Conduct regular access reviews",
                "Implement data loss prevention",
            ],
            HypothesisType.RANSOMWARE: [
                "Regular offline backups",
                "Network segmentation",
                "Email security and awareness training",
                "Endpoint detection and response",
            ],
        }
        
        return mitigation_templates.get(hypothesis_type, ["Implement security controls"])
    
    def _filter_and_sort_hypotheses(self, hypotheses: List[Hypothesis]) -> List[Hypothesis]:
        """Filter and sort hypotheses by confidence and impact."""
        # Filter by confidence threshold
        confidence_values = {
            ConfidenceLevel.VERY_HIGH: 1.0,
            ConfidenceLevel.HIGH: 0.8,
            ConfidenceLevel.MEDIUM: 0.6,
            ConfidenceLevel.LOW: 0.4,
            ConfidenceLevel.VERY_LOW: 0.2,
        }
        
        filtered = [
            h for h in hypotheses
            if confidence_values[h.confidence] >= self.min_confidence_threshold
        ]
        
        # Sort by confidence and impact
        impact_weights = {"critical": 3, "high": 2, "medium": 1, "low": 0}
        
        def sort_key(h):
            conf_weight = confidence_values[h.confidence]
            impact_weight = impact_weights.get(h.impact, 0)
            return (conf_weight, impact_weight, h.likelihood)
        
        filtered.sort(key=sort_key, reverse=True)
        
        return filtered[:self.max_hypotheses]
    
    def _calculate_analysis_metrics(self, analysis: HypothesisAnalysis) -> None:
        """Calculate analysis metrics."""
        analysis.total_hypotheses = len(analysis.hypotheses)
        
        # Count confidence levels
        for hypothesis in analysis.hypotheses:
            if hypothesis.confidence in {ConfidenceLevel.VERY_HIGH, ConfidenceLevel.HIGH}:
                analysis.high_confidence += 1
            elif hypothesis.confidence == ConfidenceLevel.MEDIUM:
                analysis.medium_confidence += 1
            else:
                analysis.low_confidence += 1
            
            # Count impact levels
            if hypothesis.impact == "critical":
                analysis.critical_impact += 1
            elif hypothesis.impact == "high":
                analysis.high_impact += 1
            
            # Track threat landscape
            h_type = hypothesis.hypothesis_type.value
            analysis.threat_landscape[h_type] = analysis.threat_landscape.get(h_type, 0) + 1
        
        # Calculate attack surface score
        if analysis.total_hypotheses > 0:
            high_impact_ratio = (analysis.critical_impact + analysis.high_impact) / analysis.total_hypotheses
            high_conf_ratio = analysis.high_confidence / analysis.total_hypotheses
            analysis.attack_surface_score = (high_impact_ratio * 0.6 + high_conf_ratio * 0.4) * 100
    
    def _generate_investigations(self, analysis: HypothesisAnalysis) -> List[str]:
        """Generate recommended investigations."""
        investigations = []
        
        # Priority investigations based on high-impact hypotheses
        critical_hypotheses = [h for h in analysis.hypotheses if h.impact == "critical"]
        if critical_hypotheses:
            investigations.append(
                f"URGENT: Investigate {len(critical_hypotheses)} critical threat hypotheses"
            )
        
        # High-confidence hypotheses
        high_conf_hypotheses = [h for h in analysis.hypotheses if h.confidence in {ConfidenceLevel.VERY_HIGH, ConfidenceLevel.HIGH}]
        if high_conf_hypotheses:
            investigations.append(
                f"HIGH: Validate {len(high_conf_hypotheses)} high-confidence threat scenarios"
            )
        
        # Most common threat types
        if analysis.threat_landscape:
            top_threat = max(analysis.threat_landscape.items(), key=lambda x: x[1])
            investigations.append(
                f"Focus on {top_threat[0]} threats ({top_threat[1]} hypotheses detected)"
            )
        
        return investigations[:5]  # Limit to top 5
    
    def _initialize_hypothesis_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize hypothesis generation rules."""
        return {
            "VULNERABILITY": [
                {
                    "hypothesis_type": "vulnerability_exploitation",
                    "title": "Vulnerability Exploitation Attempt",
                    "description": "Critical vulnerabilities may be actively exploited",
                    "min_severity": "critical",
                    "likelihood": 0.8,
                    "impact": "critical",
                    "attack_steps": [
                        "Vulnerability discovery",
                        "Exploit development/acquisition",
                        "Exploitation attempt",
                        "Post-exploitation activities",
                    ],
                    "mitigations": [
                        "Immediate patching",
                        "Virtual patching",
                        "Network isolation",
                        "Increased monitoring",
                    ],
                    "time_to_compromise": "hours",
                    "detection_difficulty": "medium",
                },
            ],
            "PORT": [
                {
                    "hypothesis_type": "lateral_movement",
                    "title": "Lateral Movement Pathway",
                    "description": "Open ports may facilitate lateral movement",
                    "min_signals": 3,
                    "likelihood": 0.6,
                    "impact": "high",
                    "attack_steps": [
                        "Network reconnaissance",
                        "Port scanning",
                        "Service identification",
                        "Exploitation",
                        "Lateral movement",
                    ],
                    "mitigations": [
                        "Close unnecessary ports",
                        "Implement network segmentation",
                        "Port knocking",
                        "Intrusion detection",
                    ],
                    "time_to_compromise": "days",
                    "detection_difficulty": "medium",
                },
            ],
            "DNS": [
                {
                    "hypothesis_type": "data_exfiltration",
                    "title": "DNS-based Data Exfiltration",
                    "description": "DNS queries may be used for data exfiltration",
                    "pattern": "exfil",
                    "likelihood": 0.5,
                    "impact": "high",
                    "attack_steps": [
                        "Establish C2 via DNS",
                        "Encode data in DNS queries",
                        "Exfiltrate data slowly",
                        "Avoid detection",
                    ],
                    "mitigations": [
                        "DNS monitoring",
                        "Query analysis",
                        "DNS filtering",
                        "Traffic analysis",
                    ],
                    "time_to_compromise": "weeks",
                    "detection_difficulty": "hard",
                },
            ],
        }
    
    def _initialize_attack_patterns(self) -> Dict[str, List[str]]:
        """Initialize attack patterns and TTPs."""
        return {
            "reconnaissance": ["dns_query", "port_scan", "service_enum"],
            "initial_access": ["phishing", "exploit", "valid_accounts"],
            "execution": ["command_line", "scripts", "signed_binary"],
            "persistence": ["scheduled_tasks", "services", "registry"],
            "privilege_escalation": ["process_injection", "access_token_manipulation"],
            "defense_evasion": ["obfuscation", "rootkit", "code_signing"],
            "credential_access": ["brute_force", "credential_dumping"],
            "discovery": ["system_info", "network_shares", "process_discovery"],
            "lateral_movement": ["remote_services", "remote_execution", "smb"],
            "collection": ["data_from_local_system", "data_staged"],
            "exfiltration": ["exfiltration_over_c2", "exfiltration_over_web"],
            "impact": ["data_encryption", "service_stop", "data_destruction"],
        }
