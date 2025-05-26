"""
Air Agent data models and enums.

Defines the core data structures used by the Air Agent for tracking decision
events, analyzing patterns, and providing historical context.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class DecisionType(Enum):
    """Types of decisions tracked by Air Agent."""
    REFINEMENT_NECESSITY = "refinement_necessity"
    REFINEMENT_STRATEGY = "refinement_strategy"
    COMPLEXITY_INTERVENTION = "complexity_intervention"
    FEATURE_EVOLUTION = "feature_evolution"
    NATURAL_SELECTION = "natural_selection"
    ARCHITECTURAL_CHANGE = "architectural_change"
    DECOMPOSITION_STRATEGY = "decomposition_strategy"


class DecisionOutcome(Enum):
    """Possible outcomes of tracked decisions."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    DEFERRED = "deferred"
    SUPERSEDED = "superseded"
    UNKNOWN = "unknown"


class PatternConfidence(Enum):
    """Confidence levels for identified patterns."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class DecisionEvent:
    """Tracks major decision events by refinement agents."""
    event_id: str
    decision_agent: str  # "garden_foundation_refinement", "natural_selection", "evolution"
    decision_type: DecisionType
    timestamp: datetime
    
    # Decision context
    input_context: Dict[str, Any]
    decision_rationale: str
    decision_details: Dict[str, Any]
    
    # Outcome tracking
    decision_outcome: DecisionOutcome = DecisionOutcome.UNKNOWN
    effectiveness_score: Optional[float] = None  # 0.0 to 1.0, populated later
    outcome_timestamp: Optional[datetime] = None
    
    # Metadata
    operation_id: Optional[str] = None
    phase_context: Optional[str] = None  # "phase_one", "phase_two", "phase_three"
    related_events: List[str] = field(default_factory=list)
    
    # Learning data
    lessons_learned: List[str] = field(default_factory=list)
    success_factors: List[str] = field(default_factory=list)
    failure_factors: List[str] = field(default_factory=list)


@dataclass
class FireIntervention:
    """Tracks Fire agent complexity reduction interventions."""
    intervention_id: str
    intervention_context: str  # "phase_one_guideline", "phase_three_feature", etc.
    timestamp: datetime
    decomposition_strategy: str
    success: bool
    
    # Complexity details
    original_complexity_score: float
    final_complexity_score: Optional[float] = None
    complexity_reduction: Optional[float] = None
    
    # Intervention details
    intervention_duration: Optional[timedelta] = None
    
    # Learning data
    lessons_learned: List[str] = field(default_factory=list)
    effective_techniques: List[str] = field(default_factory=list)
    challenges_encountered: List[str] = field(default_factory=list)
    
    # Related context
    operation_id: Optional[str] = None
    triggering_decision: Optional[str] = None  # Reference to decision event that triggered this


@dataclass
class DecisionPattern:
    """Represents an identified pattern in decision-making."""
    pattern_id: str
    pattern_type: str  # "success_pattern", "failure_pattern", "efficiency_pattern"
    pattern_name: str
    pattern_description: str
    
    # Pattern characteristics
    decision_types: List[DecisionType]
    contexts: List[str]  # Phase contexts where pattern applies
    frequency: int  # How many times pattern was observed
    success_rate: float  # 0.0 to 1.0
    
    # Pattern conditions
    preconditions: List[str]  # Conditions that lead to this pattern
    outcomes: List[str]  # Typical outcomes when pattern occurs
    
    # Confidence and validity
    confidence_level: PatternConfidence
    first_observed: datetime
    last_observed: datetime
    
    # Actionable insights
    recommendations: List[str]
    anti_patterns: List[str]  # Patterns to avoid
    
    # Supporting evidence
    supporting_events: List[str] = field(default_factory=list)
    statistical_significance: Optional[float] = None


@dataclass
class HistoricalContext:
    """Condensed historical context for decision makers."""
    context_type: str  # "refinement", "fire_decomposition", "natural_selection", "evolution"
    requesting_agent: str
    context_timestamp: datetime
    
    # Relevant historical data
    relevant_events: List[DecisionEvent] = field(default_factory=list)
    relevant_interventions: List[FireIntervention] = field(default_factory=list)
    identified_patterns: List[DecisionPattern] = field(default_factory=list)
    
    # Actionable insights
    success_patterns: List[str] = field(default_factory=list)
    failure_patterns: List[str] = field(default_factory=list)
    recommended_approaches: List[str] = field(default_factory=list)
    cautionary_notes: List[str] = field(default_factory=list)
    
    # Context quality metrics
    confidence_level: PatternConfidence = PatternConfidence.MEDIUM
    data_completeness: float = 1.0  # 0.0 to 1.0
    recency_weight: float = 1.0  # Weight of recent vs. old data
    
    # Time scope
    lookback_period: timedelta = field(default_factory=lambda: timedelta(days=30))
    events_analyzed: int = 0
    patterns_identified: int = 0


@dataclass
class AirAgentConfig:
    """Configuration for Air Agent operations."""
    # History retention settings
    max_decision_events: int = 1000
    max_fire_interventions: int = 500
    history_retention_days: int = 90
    
    # Pattern analysis settings
    min_pattern_frequency: int = 3  # Minimum occurrences to identify a pattern
    pattern_confidence_threshold: float = 0.6  # Minimum confidence to report pattern
    success_rate_threshold: float = 0.7  # Minimum success rate for success patterns
    
    # Context provision settings
    default_lookback_days: int = 30
    max_context_events: int = 50
    max_context_patterns: int = 10
    recency_decay_factor: float = 0.9  # How much to weight recent events
    
    # Analysis intervals
    pattern_analysis_interval: timedelta = field(default_factory=lambda: timedelta(hours=6))
    cleanup_interval: timedelta = field(default_factory=lambda: timedelta(days=1))
    
    # Integration settings
    fire_coordination_enabled: bool = True
    cross_phase_analysis_enabled: bool = True
    real_time_tracking_enabled: bool = True


@dataclass
class CrossPhasePattern:
    """Patterns that span multiple phases."""
    pattern_id: str
    pattern_name: str
    phases_involved: List[str]  # ["phase_one", "phase_two", "phase_three"]
    
    # Pattern characteristics
    pattern_type: str  # "escalation", "cascade", "feedback_loop"
    description: str
    trigger_conditions: List[str]
    propagation_path: List[str]  # How pattern moves between phases
    
    # Impact assessment
    system_impact: str  # "positive", "negative", "neutral"
    mitigation_strategies: List[str]
    early_warning_signs: List[str]
    
    # Evidence
    supporting_cases: List[str] = field(default_factory=list)
    confidence: PatternConfidence = PatternConfidence.MEDIUM
    first_identified: datetime = field(default_factory=datetime.now)


@dataclass
class ContextRequest:
    """Request for historical context from a decision agent."""
    request_id: str
    requesting_agent: str
    request_timestamp: datetime
    
    # Context specification
    context_type: str
    decision_context: Dict[str, Any]
    specific_questions: List[str] = field(default_factory=list)
    
    # Filtering criteria
    lookback_period: Optional[timedelta] = None
    phase_filter: Optional[List[str]] = None
    decision_type_filter: Optional[List[DecisionType]] = None
    
    # Response requirements
    max_events: Optional[int] = None
    min_confidence: Optional[float] = None
    urgency_level: str = "normal"  # "low", "normal", "high", "critical"


@dataclass
class ContextResponse:
    """Response containing historical context for a decision agent."""
    response_id: str
    request_id: str
    response_timestamp: datetime
    
    # Provided context
    historical_context: HistoricalContext
    
    # Response metadata
    processing_time: timedelta
    data_sources_consulted: List[str]
    
    # Quality indicators
    context_completeness: float  # 0.0 to 1.0
    recommendation_confidence: float  # 0.0 to 1.0
    freshness_score: float  # 0.0 to 1.0 based on data recency
    
    # Optional fields
    limitations: List[str] = field(default_factory=list)


@dataclass
class EffectivenessTracking:
    """Tracks effectiveness of Air Agent context provision."""
    tracking_id: str
    context_response_id: str
    decision_event_id: Optional[str] = None
    
    # Effectiveness metrics
    context_used: bool = False
    decision_outcome: Optional[DecisionOutcome] = None
    improvement_measured: Optional[float] = None  # Compared to baseline
    
    # Feedback
    agent_feedback: Optional[str] = None
    context_helpfulness: Optional[int] = None  # 1-5 scale
    recommendations_followed: List[str] = field(default_factory=list)
    
    # Learning indicators
    led_to_better_outcome: Optional[bool] = None
    prevented_known_failure: Optional[bool] = None
    introduced_new_insights: Optional[bool] = None
    
    # Timestamps
    follow_up_timestamp: Optional[datetime] = None
    outcome_timestamp: Optional[datetime] = None