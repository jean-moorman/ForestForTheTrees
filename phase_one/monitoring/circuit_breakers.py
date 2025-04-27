"""
Circuit breaker configuration and management for phase one agents.
"""
from dataclasses import dataclass

@dataclass
class CircuitBreakerDefinition:
    """Configuration for a circuit breaker."""
    name: str
    failure_threshold: int = 3
    recovery_timeout: int = 30
    failure_window: int = 120