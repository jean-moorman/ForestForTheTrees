"""
Agent interface module for the FFTT system.
Provides interfaces for agent communication and state management.
"""

from enum import Enum, auto
from typing import Dict, Any, Optional, List, Tuple

from .interface import AgentInterface
from .validation import ValidationManager
from .cache import InterfaceCache
from .metrics import InterfaceMetrics


class AgentState(Enum):
    """States that an agent can be in during its lifecycle."""
    READY = auto()
    PROCESSING = auto()
    VALIDATING = auto()
    FAILED_VALIDATION = auto()
    COMPLETE = auto()
    ERROR = auto()
    COORDINATING = auto()
    CLARIFYING = auto()


__all__ = [
    'AgentInterface',
    'AgentState',
    'ValidationManager',
    'InterfaceCache',
    'InterfaceMetrics'
]