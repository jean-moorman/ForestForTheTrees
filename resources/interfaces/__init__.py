"""
Interface definitions for the resources package.

This module contains interface definitions (abstract base classes) that help
prevent circular dependencies in the resources package. These interfaces
define the contracts that implementations must adhere to without containing
implementation details themselves.
"""

# Re-export interfaces
from resources.interfaces.base import (
    IBaseResource,
    IResourceLifecycle,
    ICleanupPolicy,
    ICleanupConfig
)

from resources.interfaces.state import (
    IStateEntry,
    IStateSnapshot,
    IStateManagerConfig,
    IStateManager
)

# Define public API
__all__ = [
    'IBaseResource',
    'IResourceLifecycle',
    'ICleanupPolicy',
    'ICleanupConfig',
    'IStateEntry',
    'IStateSnapshot',
    'IStateManagerConfig',
    'IStateManager'
]