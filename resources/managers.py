"""
FFTT Resource Managers
---------------------
This module is a backward compatibility interface that redirects to the modular implementation
in the managers/ directory. For new code, please import directly from resources.managers.

Provides various manager classes for handling context, caching, metrics, 
circuit breakers, and resource coordination.
"""

# Import and re-export all public classes from resources.managers
from resources.managers import (
    AgentContextType,
    AgentContext,
    AgentContextManager,
    CacheManager,
    MetricsManager,
    CircuitBreakerRegistry,
    ResourceCoordinator
)

# Define exports
__all__ = [
    'AgentContextType',
    'AgentContext',
    'AgentContextManager',
    'CacheManager',
    'MetricsManager',
    'CircuitBreakerRegistry',
    'ResourceCoordinator'
]