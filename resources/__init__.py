"""
Forest For The Trees (FFTT) Resource Management System
---------------------------------------------------
Provides core resource management functionality including state management,
event handling, caching, monitoring capabilities, and phase coordination.
"""
# Start with common and base types that have minimal dependencies
from .common import (
    ResourceState,
    ResourceType,
    InterfaceState,
    CircuitBreakerConfig,
    MemoryThresholds,
    HealthStatus
)

from .errors import (
    ErrorClassification,
    ErrorSeverity,
    ResourceError,
    ResourceExhaustionError,
    ResourceTimeoutError,
    CoordinationError,
    MisunderstandingDetectionError,
    ErrorHandler,
)

# Import the base resource before importing base.py which depends on it
from .base_resource import (
    BaseResource,
)

# Now we can safely import from base.py which depends on BaseResource
from .base import (
    CleanupPolicy,
    CleanupConfig,
)

# State system has fewer dependencies
from .state import (
    StateEntry,
    StateSnapshot,
    StateManager
)

# Events should be imported after state to avoid circular dependencies
from .events import (
    ResourceEventTypes,
    Event,
    EventQueue,
    EventMonitor
)

# These depend on the above imports
from .managers import (
    AgentContextManager,
    CacheManager,
    MetricsManager,
    AgentContext,
    AgentContextType
)

# Monitoring depends on events and base
from .monitoring import (
    CircuitBreaker,
    CircuitState,
    MemoryMonitor,
    HealthTracker,
    SystemMonitor,
    SystemMonitorConfig,
    ReliabilityMetrics
)


from .phase_coordinator import (
    PhaseState,
    PhaseType,
    PhaseContext,
    NestedPhaseExecution,
    PhaseTransitionHandler,
    PhaseCoordinator
)

from .phase_coordination_integration import (
    PhaseCoordinationIntegration,
    PhaseOneToTwoTransitionHandler,
    PhaseTwoToThreeTransitionHandler,
    PhaseThreeToFourTransitionHandler
)

# Fire Agent - System-wide complexity detection and reduction
from .fire_agent import (
    analyze_guideline_complexity,
    analyze_feature_complexity,
    analyze_component_complexity,
    decompose_complex_guideline,
    decompose_complex_feature,
    simplify_component_architecture,
    calculate_complexity_score,
    identify_complexity_causes,
    assess_decomposition_impact
)

# Air Agent - Historical context provider for decision makers
from .air_agent import (
    provide_refinement_context,
    provide_fire_context,
    provide_natural_selection_context,
    provide_evolution_context,
    track_decision_event,
    track_refinement_cycle,
    track_fire_intervention,
    get_decision_history,
    analyze_cross_phase_patterns
)

# Temporarily disabled to break circular import - will re-enable after fixing
# from .water_agent import (
#     CoordinationContext,
#     WaterAgentContextManager
# )

__version__ = '0.1.0'

__all__ = [
    # Base types
    'ResourceState',
    'ResourceType',
    'InterfaceState',
    'ErrorSeverity',
    'BaseResource',
    
    # Errors
    'ResourceError',
    'ResourceExhaustionError',
    'ResourceTimeoutError',
    'CoordinationError',
    'MisunderstandingDetectionError',
    
    # Configuration
    'MemoryThresholds',
    'CleanupPolicy',
    'CleanupConfig',
    'CircuitBreakerConfig',
    
    # Core components
    'StateManager',
    'EventQueue',
    'EventMonitor',
    'ErrorHandler',
    
    # Resource managers
    'AgentContextManager',
    'CacheManager',
    'MetricsManager',
    
    # Monitoring
    'CircuitBreaker',
    'CircuitState',
    'MemoryMonitor',
    'HealthTracker',
    
    # Data structures
    'StateEntry',
    'StateSnapshot',
    'Event',
    'HealthStatus',
    
    # Event types
    'ResourceEventTypes',
    
    # Phase coordination
    'PhaseState',
    'PhaseType',
    'PhaseContext',
    'PhaseTransitionHandler',
    'PhaseCoordinator',
    'PhaseCoordinationIntegration',
    
    # Water Agent
    'AmbiguitySeverity',
    'WaterAgentCoordinator',
    'MisunderstandingDetector',
    'QuestionResponseHandler',
    'AmbiguityResolutionTracker',
    'CoordinationContext',
    'WaterAgentContextManager',
    
    # Fire Agent - Complexity analysis and decomposition
    'analyze_guideline_complexity',
    'analyze_feature_complexity',
    'analyze_component_complexity',
    'decompose_complex_guideline',
    'decompose_complex_feature',
    'simplify_component_architecture',
    'calculate_complexity_score',
    'identify_complexity_causes',
    'assess_decomposition_impact',
    
    # Air Agent - Historical context and decision tracking
    'provide_refinement_context',
    'provide_fire_context',
    'provide_natural_selection_context',
    'provide_evolution_context',
    'track_decision_event',
    'track_refinement_cycle',
    'track_fire_intervention',
    'get_decision_history',
    'analyze_cross_phase_patterns',
    ]