from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Literal, Optional, Union, TypeVar

from resources.common import (
    ResourceState, 
    ResourceType,
    InterfaceState,
)
from resources.base import CleanupConfig

T = TypeVar('T')

@dataclass
class StateEntry:
    """Represents a single state entry with metadata"""
    state: Union[ResourceState, InterfaceState, Dict[str, Any]]
    resource_type: ResourceType
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = field(default=1)
    previous_state: Optional[str] = None
    transition_reason: Optional[str] = None
    failure_info: Optional[Dict[str, Any]] = None

@dataclass
class StateSnapshot:
    """Point-in-time capture of state"""
    state: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    resource_type: ResourceType = field(default=ResourceType.STATE)
    version: int = field(default=1)

@dataclass
class StateManagerConfig:
    """Configuration for StateManager"""
    cleanup_config: Optional[CleanupConfig] = None
    
    # Persistence configuration
    persistence_type: Literal["memory", "file", "sqlite", "custom"] = "memory"
    
    # For file persistence
    storage_dir: Optional[str] = None
    
    # For SQLite persistence
    db_path: Optional[str] = None
    
    # For custom backend
    custom_backend: Optional['StateStorageBackend'] = None
    
    # Performance tuning
    cache_size: int = 1000  # Number of state entries to cache in memory
    
    # Recovery options
    auto_repair: bool = True  # Automatically attempt to repair corrupt files
    
    # Monitoring
    enable_metrics: bool = True  # Whether to collect metrics on operations