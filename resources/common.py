from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, Any, Optional

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5           # Number of failures before opening
    recovery_timeout: int = 60           # Seconds to wait before half-open
    half_open_max_tries: int = 1         # Max parallel requests in half-open
    failure_window: int = 60             # Window (seconds) for counting failures

class MemoryThresholds:
    """Memory threshold configuration"""
    def __init__(self, 
                 warning_percent: float = 0.7, 
                 critical_percent: float = 0.9,
                 per_resource_max_mb: float = 1024.0,
                 total_memory_mb: float = None):
        self.warning_percent = warning_percent
        self.critical_percent = critical_percent
        self.per_resource_max_mb = per_resource_max_mb
        
        # Get total system memory if not provided
        if total_memory_mb is None:
            import psutil
            memory = psutil.virtual_memory()
            total_memory_mb = memory.total / (1024 * 1024)  # Convert bytes to MB
        
        self.total_memory_mb = total_memory_mb
    
    def get_threshold_for_level(self, level: str) -> float:
        """Get the threshold value for the specified alert level"""
        if level == "CRITICAL":
            return self.critical_percent
        elif level == "WARNING":
            return self.warning_percent
        else:
            return 0.0  # Default

@dataclass 
class HealthStatus:
    """Internal health status representation for resources"""
    status: str  # HEALTHY, DEGRADED, UNHEALTHY, CRITICAL
    source: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

class ResourceState(Enum):
    """Core states for any managed resource"""
    ACTIVE = auto()
    PAUSED = auto() 
    FAILED = auto()
    RECOVERED = auto()
    TERMINATED = auto()

class ResourceType(Enum):
    """Types of resources that can be managed"""
    AGENT = auto()
    STATE = auto()
    EVENT = auto()
    MONITOR = auto()
    CACHE = auto()
    COMPUTE = auto()

class InterfaceState(Enum):
    """States for interface resources"""
    INITIALIZED = auto()
    ACTIVE = auto()
    DISABLED = auto()
    ERROR = auto()
    VALIDATING = auto()
    PROPAGATING = auto()

class ErrorSeverity(Enum):
    """Classification of error severity"""
    TRANSIENT = auto()
    DEGRADED = auto()
    FATAL = auto()
