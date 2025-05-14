"""
Forest For The Trees (FFTT) Phase Coordination System - Constants
---------------------------------------------------
Contains enums and constants used by the phase coordination system.
"""
from enum import Enum, auto
from typing import Dict, Any, List, Optional

class PhaseState(Enum):
    """States for phase lifecycle"""
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    ABORTED = auto()

class PhaseType(Enum):
    """Base types of phases in the system"""
    ZERO = "phase_zero"
    ONE = "phase_one"
    TWO = "phase_two"
    THREE = "phase_three"
    FOUR = "phase_four"
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Get all phase type values"""
        return [member.value for member in cls]
    
    @classmethod
    def from_string(cls, value: str) -> Optional['PhaseType']:
        """Convert string to PhaseType if valid"""
        for member in cls:
            if member.value == value:
                return member
        return None

# Global registry for custom phase types
_CUSTOM_PHASE_TYPES: Dict[str, Dict[str, Any]] = {}

# Default circuit breaker configurations for different phase types
DEFAULT_CIRCUIT_BREAKER_CONFIGS = {
    "phase_zero": {"failure_threshold": 3, "recovery_timeout": 60, "failure_window": 300},
    "phase_one": {"failure_threshold": 3, "recovery_timeout": 60, "failure_window": 300},
    "phase_two": {"failure_threshold": 5, "recovery_timeout": 120, "failure_window": 600},
    "phase_three": {"failure_threshold": 4, "recovery_timeout": 90, "failure_window": 450},
    "phase_four": {"failure_threshold": 3, "recovery_timeout": 60, "failure_window": 300},
    "transition": {"failure_threshold": 3, "recovery_timeout": 60, "failure_window": 300},
}