"""
Water Agent package for the FFTT system.

This package provides classes and functions for the Water Agent, which facilitates
coordination between sequential agents to resolve misunderstandings and smooth
system operations during agent hand-offs.
"""

# Import WaterAgentCoordinator and related classes to make them available through the package
from resources.water_agent.coordinator import (
    WaterAgentCoordinator,
    AmbiguitySeverity,
    MisunderstandingDetector,
    QuestionResponseHandler,
    AmbiguityResolutionTracker
)

# Import Context Manager components
from resources.water_agent.context_manager import (
    CoordinationContext,
    WaterAgentContextManager
)

# Export all public classes
__all__ = [
    'CoordinationContext',
    'WaterAgentContextManager',
    'AmbiguitySeverity',
    'WaterAgentCoordinator',
    'MisunderstandingDetector',
    'QuestionResponseHandler',
    'AmbiguityResolutionTracker'
]