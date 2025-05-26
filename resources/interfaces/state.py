"""
State management interfaces for the resources package.

This module contains interfaces for the state management components,
allowing other modules to depend on these interfaces without creating
circular dependencies with the implementation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Literal, Optional, Union, TypeVar, List

# Import common types without causing circular dependencies
from resources.common import ResourceState, ResourceType, InterfaceState
from resources.interfaces.base import ICleanupConfig

T = TypeVar('T')

@dataclass
class IStateEntry:
    """Interface defining a single state entry with metadata."""
    state: Union[ResourceState, InterfaceState, Dict[str, Any]]
    resource_type: ResourceType
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = field(default=1)
    previous_state: Optional[str] = None
    transition_reason: Optional[str] = None
    failure_info: Optional[Dict[str, Any]] = None


@dataclass
class IStateSnapshot:
    """Interface defining a point-in-time capture of state."""
    state: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    resource_type: ResourceType = field(default=ResourceType.STATE)
    version: int = field(default=1)


@dataclass
class IStateManagerConfig:
    """Interface defining configuration for StateManager."""
    cleanup_config: Optional[ICleanupConfig] = None
    
    # Persistence configuration
    persistence_type: Literal["memory", "file", "sqlite", "custom"] = "memory"
    
    # For file persistence
    storage_dir: Optional[str] = None
    
    # For SQLite persistence
    db_path: Optional[str] = None
    
    # Performance tuning
    cache_size: int = 1000  # Number of state entries to cache in memory
    
    # Recovery options
    auto_repair: bool = True  # Automatically attempt to repair corrupt files
    
    # Monitoring
    enable_metrics: bool = True  # Whether to collect metrics on operations


class IStateManager(ABC):
    """Interface defining the contract for state managers."""
    
    @abstractmethod
    async def set_state(self, 
                      resource_id: str, 
                      state: Union[str, Dict[str, Any]],
                      metadata: Optional[Dict[str, Any]] = None,
                      resource_type: Optional[ResourceType] = None) -> bool:
        """
        Set state for a resource.
        
        Args:
            resource_id: Unique identifier for the resource
            state: The state to set
            metadata: Optional metadata to associate with the state
            resource_type: Optional resource type
            
        Returns:
            True if the state was set successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_state(self, 
                      resource_id: str, 
                      default: Optional[T] = None) -> Union[T, IStateEntry]:
        """
        Get current state for a resource.
        
        Args:
            resource_id: Unique identifier for the resource
            default: Default value to return if no state exists
            
        Returns:
            The state entry or default value if not found
        """
        pass
    
    @abstractmethod
    async def get_state_history(self,
                             resource_id: str,
                             limit: Optional[int] = None,
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None) -> List[IStateEntry]:
        """
        Get state history for a resource.
        
        Args:
            resource_id: Unique identifier for the resource
            limit: Maximum number of entries to return
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            
        Returns:
            List of state entries sorted by timestamp (newest first)
        """
        pass
    
    @abstractmethod
    async def get_snapshot(self) -> IStateSnapshot:
        """
        Get a snapshot of all current state.
        
        Returns:
            A snapshot of all current state
        """
        pass
    
    @abstractmethod
    async def restore_snapshot(self, snapshot: IStateSnapshot) -> bool:
        """
        Restore state from a snapshot.
        
        Args:
            snapshot: The snapshot to restore from
            
        Returns:
            True if the snapshot was restored successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def clear_state(self, resource_id: Optional[str] = None) -> bool:
        """
        Clear state for a resource or all resources.
        
        Args:
            resource_id: Optional resource ID to clear, or None to clear all
            
        Returns:
            True if the state was cleared successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def list_resources(self) -> List[str]:
        """
        List all resource IDs with state.
        
        Returns:
            List of resource IDs
        """
        pass