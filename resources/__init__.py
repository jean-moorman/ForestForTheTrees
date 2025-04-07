"""
Forest For The Trees (FFTT) Resource Management System
---------------------------------------------------
Provides core resource management functionality including state management,
event handling, caching, monitoring capabilities, and phase coordination.
"""
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
)

# We'll define a simple placeholder ErrorHandler to avoid import cycles
class ErrorHandler:
    """Simple placeholder for ErrorHandler to avoid import cycles"""
    def __init__(self, event_queue):
        self._event_queue = event_queue

from .base import (
    CleanupPolicy,
    CleanupConfig,
)


from .state import (
    StateEntry,
    StateSnapshot,
    StateManager
)

from .events import (
    ResourceEventTypes,
    Event,
    EventQueue,
    EventMonitor
)

from .managers import (
    AgentContextManager,
    CacheManager,
    MetricsManager,
    AgentContext,
    AgentContextType
)

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

__version__ = '0.1.0'

__all__ = [
    # Base types
    'ResourceState',
    'ResourceType',
    'InterfaceState',
    'ErrorSeverity',
    
    # Errors
    'ResourceError',
    'ResourceExhaustionError',
    'ResourceTimeoutError',
    
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
    'PhaseCoordinationIntegration'
]