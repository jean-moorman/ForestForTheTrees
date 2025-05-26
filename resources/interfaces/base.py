"""
Base interface definitions for the resources package.

This module contains the core interfaces that define the contract for
resource objects in the system. These interfaces are used to prevent
circular dependencies in the implementation classes.
"""

from abc import ABC, abstractmethod
import asyncio
from datetime import datetime
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Dict, Any, Set, List

class IResourceLifecycle(ABC):
    """Interface defining the resource lifecycle operations."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the resource. This method should be called after construction
        to complete any async initialization steps.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def terminate(self) -> bool:
        """
        Terminate the resource, cleaning up any owned resources.
        
        Returns:
            True if termination was successful, False otherwise
        """
        pass

class IBaseResource(IResourceLifecycle):
    """
    Interface for base resource functionality.
    
    This interface defines the contract that BaseResource implementations
    must fulfill, enabling other components to depend on the interface
    rather than the concrete implementation.
    """
    
    @property
    @abstractmethod
    def resource_id(self) -> str:
        """Get the unique identifier for this resource."""
        pass
    
    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if the resource is fully initialized."""
        pass
    
    @property
    @abstractmethod
    def is_terminated(self) -> bool:
        """Check if the resource has been terminated."""
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """Get the creation timestamp for this resource."""
        pass
    
    @abstractmethod
    def _add_task(self, task: asyncio.Task) -> None:
        """
        Add a task to be tracked by this resource for cleanup.
        
        Args:
            task: The asyncio task to track
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_resource(cls, resource_id: str) -> Optional['IBaseResource']:
        """
        Get a resource by ID from the global registry.
        
        Args:
            resource_id: The unique resource identifier
            
        Returns:
            The resource if found, None otherwise
        """
        pass
    
    @classmethod
    @abstractmethod
    def list_resources(cls) -> Dict[str, 'IBaseResource']:
        """
        Get a copy of all registered resources.
        
        Returns:
            A dictionary mapping resource IDs to resources
        """
        pass
    
    @classmethod
    @abstractmethod
    async def terminate_all(cls) -> int:
        """
        Terminate all registered resources. Useful for application shutdown.
        
        Returns:
            The number of resources terminated
        """
        pass


class ICleanupPolicy(Enum):
    """Interface defining cleanup policies."""
    TTL = auto()           # Time-based expiration
    MAX_SIZE = auto()      # Size-based retention
    HYBRID = auto()        # Combination of TTL and size
    AGGRESSIVE = auto()    # Low-tolerance timeouts


@dataclass
class ICleanupConfig:
    """Interface defining cleanup configuration."""
    policy: ICleanupPolicy
    ttl_seconds: Optional[int] = None
    max_size: Optional[int] = None
    check_interval: int = 300
    batch_size: int = 100