"""
State management module for tracking and persisting application state.

This module is a backward compatibility interface that redirects to the modular implementation
in the state/ directory. For new code, please import directly from resources.state.
"""

# Import and re-export all public classes from resources.state
from resources.state import (
    StateManager,
    StateEntry,
    StateSnapshot,
    StateManagerConfig,
    StateTransitionValidator,
    StateStorageBackend,
    MemoryStateBackend,
    FileStateBackend,
    SQLiteStateBackend,
    ResourceState,
    InterfaceState,
    ResourceType,
    HealthStatus
)

# Define exports
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
    'HealthStatus'
]