"""
Fire Agent data models and enums.

Defines the core data structures used by the Fire Agent for complexity analysis
and decomposition operations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime


class ComplexityLevel(Enum):
    """Enumeration of complexity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplexityCause(Enum):
    """Types of complexity causes that Fire Agent can identify."""
    MULTIPLE_RESPONSIBILITIES = "multiple_responsibilities"
    HIGH_DEPENDENCY_COUNT = "high_dependency_count"
    CROSS_CUTTING_CONCERNS = "cross_cutting_concerns"
    BROAD_IMPLEMENTATION_SCOPE = "broad_implementation_scope"
    CONFLICTING_REQUIREMENTS = "conflicting_requirements"
    UNCLEAR_BOUNDARIES = "unclear_boundaries"
    NESTED_COMPLEXITY = "nested_complexity"
    INTEGRATION_COMPLEXITY = "integration_complexity"


class DecompositionStrategy(Enum):
    """Decomposition strategies available to Fire Agent."""
    FUNCTIONAL_SEPARATION = "functional_separation"
    RESPONSIBILITY_EXTRACTION = "responsibility_extraction"
    DEPENDENCY_REDUCTION = "dependency_reduction"
    LAYER_SEPARATION = "layer_separation"
    CONCERN_ISOLATION = "concern_isolation"
    SCOPE_NARROWING = "scope_narrowing"


@dataclass
class ComplexityThreshold:
    """Configuration for complexity thresholds."""
    low_threshold: float = 30.0
    medium_threshold: float = 55.0  # Lowered to catch more cases as medium
    high_threshold: float = 70.0   # Lowered to catch more cases as high
    critical_threshold: float = 90.0
    
    # Context-specific thresholds
    feature_low_threshold: float = 25.0
    feature_medium_threshold: float = 45.0  # More sensitive for features
    feature_high_threshold: float = 60.0    # Lower threshold for feature complexity
    feature_critical_threshold: float = 75.0
    
    def get_level(self, score: float, context: str = "general") -> ComplexityLevel:
        """Get complexity level for a given score with context-aware thresholds."""
        if context == "phase_three_feature":
            # Use feature-specific thresholds
            if score >= self.feature_critical_threshold:
                return ComplexityLevel.CRITICAL
            elif score >= self.feature_high_threshold:
                return ComplexityLevel.HIGH
            elif score >= self.feature_medium_threshold:
                return ComplexityLevel.MEDIUM
            else:
                return ComplexityLevel.LOW
        else:
            # Use general thresholds for guidelines and components
            if score >= self.critical_threshold:
                return ComplexityLevel.CRITICAL
            elif score >= self.high_threshold:
                return ComplexityLevel.HIGH
            elif score >= self.medium_threshold:
                return ComplexityLevel.MEDIUM
            else:
                return ComplexityLevel.LOW


@dataclass
class ComplexityAnalysis:
    """Result of complexity analysis by Fire Agent."""
    complexity_score: float
    complexity_level: ComplexityLevel
    exceeds_threshold: bool
    complexity_causes: List[ComplexityCause]
    analysis_context: str  # "phase_one", "phase_two_component", "phase_three_feature"
    
    # Decomposition recommendations
    recommended_strategy: Optional[DecompositionStrategy] = None
    decomposition_opportunities: List[str] = field(default_factory=list)
    
    # Analysis metadata
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    confidence_level: float = 1.0  # 0.0 to 1.0
    
    # Additional details
    affected_components: List[str] = field(default_factory=list)
    risk_assessment: str = ""
    intervention_urgency: str = "normal"  # "low", "normal", "high", "critical"


@dataclass
class DecompositionResult:
    """Result of decomposition operation by Fire Agent."""
    success: bool
    original_complexity_score: float
    new_complexity_score: Optional[float] = None
    complexity_reduction: Optional[float] = None
    
    # Decomposition details
    strategy_used: Optional[DecompositionStrategy] = None
    decomposed_elements: List[Dict[str, Any]] = field(default_factory=list)
    
    # For guidelines
    simplified_architecture: Optional[Dict[str, Any]] = None
    
    # For features
    decomposed_features: List[Dict[str, Any]] = field(default_factory=list)
    
    # For components
    simplified_components: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    decomposition_timestamp: datetime = field(default_factory=datetime.now)
    lessons_learned: List[str] = field(default_factory=list)
    success_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Warnings and recommendations
    warnings: List[str] = field(default_factory=list)
    follow_up_recommendations: List[str] = field(default_factory=list)


@dataclass
class SystemComplexitySnapshot:
    """System-wide complexity analysis snapshot."""
    total_complexity_score: float
    phase_complexity_scores: Dict[str, float]
    complexity_hotspots: List[Dict[str, Any]]
    trending_complexity: str  # "increasing", "stable", "decreasing"
    
    # Recommendations
    recommended_interventions: List[Dict[str, Any]] = field(default_factory=list)
    priority_areas: List[str] = field(default_factory=list)
    
    # Metadata
    snapshot_timestamp: datetime = field(default_factory=datetime.now)
    confidence_level: float = 1.0


@dataclass
class FireAgentConfig:
    """Configuration for Fire Agent operations."""
    complexity_thresholds: ComplexityThreshold = field(default_factory=ComplexityThreshold)
    
    # Intervention settings
    auto_decomposition_enabled: bool = True
    max_decomposition_attempts: int = 3
    decomposition_timeout: float = 300.0  # 5 minutes
    
    # Analysis settings
    system_monitoring_interval: float = 3600.0  # 1 hour
    complexity_history_retention: int = 100  # Keep last 100 analyses
    
    # Coordination settings
    coordination_with_air_agent: bool = True
    historical_context_weight: float = 0.3  # How much to weight historical patterns