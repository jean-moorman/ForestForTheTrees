"""
State management module for tracking and persisting application state.

This module provides a robust state management system with different storage backends
and supports state transitions, history tracking, and snapshots.
"""

# Import and re-export classes for backward compatibility
from resources.state.models import StateEntry, StateSnapshot, StateManagerConfig
from resources.state.validators import StateTransitionValidator
from resources.state.manager import StateManager
from resources.state.backends import (
    StateStorageBackend,
    MemoryStateBackend,
    FileStateBackend,
    SQLiteStateBackend
)
from resources.common import ResourceState, InterfaceState, ResourceType, HealthStatus

# Define public API
__all__ = [
    'StateManager',
    'StateEntry',
    'StateSnapshot',
    'StateManagerConfig',
    'StateTransitionValidator',
    'StateStorageBackend',
    'MemoryStateBackend',
    'FileStateBackend',
    'SQLiteStateBackend',
    'ResourceState',
    'InterfaceState',
    'ResourceType',
    'HealthStatus',
]