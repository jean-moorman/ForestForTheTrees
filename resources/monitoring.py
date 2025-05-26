"""
Monitoring module for FFTT - provides monitoring and resilience capabilities.

This module is a backward compatibility interface that redirects to the modular implementation
in the monitoring/ directory. For new code, please import directly from resources.monitoring.
"""

# Import and re-export all public classes from resources.monitoring
from resources.monitoring import (
    CircuitState,
    CircuitOpenError,
    CircuitBreaker,
    CircuitMetrics,
    ReliabilityMetrics,
    CircuitBreakerRegistry,
    MemoryMonitor,
    HealthTracker,
    SystemMonitor,
    SystemMonitorConfig,
    CircuitBreakerConfig,
    HealthStatus,
    MemoryThresholds,
    with_memory_checking
)

# Define exports
__all__ = [
    'CircuitState',
    'CircuitOpenError',
    'CircuitBreaker',
    'CircuitMetrics',
    'ReliabilityMetrics',
    'CircuitBreakerRegistry',
    'MemoryMonitor',
    'HealthTracker',
    'SystemMonitor',
    'SystemMonitorConfig',
    'CircuitBreakerConfig',
    'HealthStatus',
    'MemoryThresholds',
    'with_memory_checking'
]