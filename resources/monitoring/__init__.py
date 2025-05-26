"""
Monitoring package for FFTT - provides monitoring and resilience capabilities.

This package contains modules for:
- Circuit breaker pattern implementation
- Memory monitoring
- Health status tracking
- System-wide monitoring coordination
- Metrics collection
"""

# Re-export common classes needed by monitoring
from resources.common import CircuitBreakerConfig, HealthStatus, MemoryThresholds

# Re-export all public classes
from resources.monitoring.circuit_breakers import (
    CircuitState,
    CircuitOpenError,
    CircuitBreaker,
    CircuitMetrics,
    ReliabilityMetrics,
    CircuitBreakerRegistry,
)
from resources.monitoring.memory import MemoryMonitor
from resources.monitoring.health import HealthTracker
from resources.monitoring.system import SystemMonitor, SystemMonitorConfig
from resources.monitoring.utils import with_memory_checking

# Re-export simplified circuit breaker implementation to avoid circular dependencies
from resources.circuit_breakers_simple import (
    CircuitState as CircuitStateSimple,
    CircuitOpenError as CircuitOpenErrorSimple,
    CircuitBreakerSimple,
    CircuitMetricsSimple,
    ReliabilityMetricsSimple,
    CircuitBreakerRegistrySimple,
    get_registry,
)

# Define public exports
__all__ = [
    # Original circuit breaker classes
    'CircuitState',
    'CircuitOpenError',
    'CircuitBreaker',
    'CircuitMetrics',
    'ReliabilityMetrics',
    'CircuitBreakerRegistry',
    
    # Simplified circuit breaker classes
    'CircuitStateSimple',
    'CircuitOpenErrorSimple',
    'CircuitBreakerSimple',
    'CircuitMetricsSimple',
    'ReliabilityMetricsSimple',
    'CircuitBreakerRegistrySimple',
    'get_registry',
    
    # Other monitoring classes
    'MemoryMonitor',
    'HealthTracker',
    'SystemMonitor',
    'SystemMonitorConfig',
    'CircuitBreakerConfig',
    'HealthStatus',
    'MemoryThresholds',
    'with_memory_checking',
]