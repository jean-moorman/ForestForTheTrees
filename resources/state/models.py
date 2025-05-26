from typing import TypeVar, Optional

# Import the interfaces instead of concrete implementations
from resources.interfaces.state import (
    IStateEntry as StateEntry,
    IStateSnapshot as StateSnapshot,
    IStateManagerConfig as StateManagerConfig
)
from resources.interfaces.base import ICleanupConfig

# Forward reference for StateStorageBackend which will be imported by backends
StateStorageBackend = 'StateStorageBackend'

# Type variable for generic return types
T = TypeVar('T')