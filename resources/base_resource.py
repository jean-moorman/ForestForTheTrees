"""
Base resource classes for the FFTT system.

This module implements the BaseResource interface defined in resources.interfaces.base.
It provides a concrete implementation of the IBaseResource interface with functionality
for resource lifecycle management and tracking.
"""

import asyncio
import logging
import threading
from typing import Optional, Dict, Any, Set
from datetime import datetime
from abc import ABC, abstractmethod

from resources.common import ResourceType, ResourceState
from resources.events import EventQueue, ResourceEventTypes
# Import the interface instead of the concrete implementation
from resources.interfaces.state import IStateManager
# Import the interface we're implementing
from resources.interfaces.base import IBaseResource

logger = logging.getLogger(__name__)


class BaseResource(ABC):
    """
    Base class for all resources in the FFTT system.
    
    This class implements the IBaseResource interface and provides common 
    functionality for state management and event emission
    that is needed by resources that don't need the full complexity of BaseManager.
    
    Features:
    - Thread-safe resource lifecycle management
    - Event emission for resource lifecycle events
    - State persistence via state manager
    - Resource cleanup tracking
    """
    
    # Class-level registry to track all created resources
    _resources: Dict[str, 'BaseResource'] = {}
    _resources_lock = threading.RLock()
    
    def __init__(self, 
                 resource_id: str,
                 state_manager: Optional[IStateManager] = None, 
                 event_bus: Optional[EventQueue] = None):
        """
        Initialize the base resource.
        
        Args:
            resource_id: Unique identifier for this resource
            state_manager: Optional state manager for persisting state
            event_bus: Optional event bus for emitting events
        """
        self._resource_id = resource_id
        self._state_manager = state_manager
        self.event_bus = event_bus
        self._tasks: Set[asyncio.Task] = set()
        self._lock = threading.RLock()
        self._initialized = False
        self._terminated = False
        self._created_at = datetime.now()
        
        # Register this resource in the global registry
        with BaseResource._resources_lock:
            BaseResource._resources[resource_id] = self
    
    @property
    def resource_id(self) -> str:
        """Get the unique identifier for this resource."""
        return self._resource_id
    
    @property
    def is_initialized(self) -> bool:
        """Check if the resource is fully initialized."""
        with self._lock:
            return self._initialized
            
    @property
    def is_terminated(self) -> bool:
        """Check if the resource has been terminated."""
        with self._lock:
            return self._terminated
            
    @property
    def created_at(self) -> datetime:
        """Get the creation timestamp for this resource."""
        return self._created_at
    
    @classmethod
    def get_resource(cls, resource_id: str) -> Optional[IBaseResource]:
        """
        Get a resource by ID from the global registry.
        
        Args:
            resource_id: The unique resource identifier
            
        Returns:
            The resource if found, None otherwise
        """
        with cls._resources_lock:
            return cls._resources.get(resource_id)
    
    @classmethod
    def list_resources(cls) -> Dict[str, IBaseResource]:
        """
        Get a copy of all registered resources.
        
        Returns:
            A dictionary mapping resource IDs to resources
        """
        with cls._resources_lock:
            return dict(cls._resources)
            
    async def initialize(self) -> bool:
        """
        Initialize the resource. This method should be called after construction
        to complete any async initialization steps.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        with self._lock:
            if self._initialized:
                return True
                
            if self._terminated:
                logger.error(f"Cannot initialize terminated resource: {self._resource_id}")
                return False
                
            self._initialized = True
            
        # Emit initialization event outside of lock
        await self._emit_lifecycle_event(ResourceEventTypes.RESOURCE_CREATED.value, {
            "status": "initialized",
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    async def terminate(self) -> bool:
        """
        Terminate the resource, cleaning up any owned resources.
        
        Returns:
            True if termination was successful, False otherwise
        """
        with self._lock:
            if self._terminated:
                return True
                
            self._terminated = True
            
            # Cancel any pending tasks
            for task in self._tasks:
                if not task.done():
                    task.cancel()
        
        # Unregister from global registry
        with BaseResource._resources_lock:
            if self._resource_id in BaseResource._resources:
                del BaseResource._resources[self._resource_id]
        
        # Emit termination event outside of lock
        await self._emit_lifecycle_event(ResourceEventTypes.RESOURCE_TERMINATED.value, {
            "status": "terminated",
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    def _add_task(self, task: asyncio.Task) -> None:
        """
        Add a task to be tracked by this resource for cleanup.
        
        Args:
            task: The asyncio task to track
        """
        with self._lock:
            if self._terminated:
                # Resource already terminated, cancel the task immediately
                if not task.done():
                    task.cancel()
                return
                
            self._tasks.add(task)
            task.add_done_callback(self._task_done_callback)
    
    def _task_done_callback(self, task: asyncio.Task) -> None:
        """
        Callback for task completion, ensuring proper cleanup.
        
        Args:
            task: The completed task
        """
        with self._lock:
            if task in self._tasks:
                self._tasks.discard(task)
                
            # Check for exceptions but don't propagate them
            try:
                exception = task.exception()
                if exception:
                    logger.error(f"Task in resource {self._resource_id} failed with error: {exception}")
            except (asyncio.CancelledError, asyncio.InvalidStateError):
                # Task was cancelled or is not done yet, ignore
                pass
    
    async def _emit_lifecycle_event(self, event_type: Any, data: Dict[str, Any]) -> None:
        """
        Emit a lifecycle event with standardized resource information.
        
        Args:
            event_type: The type of event to emit
            data: The data to include with the event
        """
        if not self.event_bus:
            return
            
        # Create standardized event data
        event_data = {
            "resource_id": self._resource_id,
            "resource_type": self.__class__.__name__,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add custom data
        event_data.update(data)
        
        # Emit the event
        await self._emit_event(event_type, event_data)
        
    async def _emit_event(self, event_type: Any, data: Dict[str, Any]) -> None:
        """
        Emit an event if an event bus is available.
        
        Args:
            event_type: The type of event to emit
            data: The data to include with the event
        """
        if self.event_bus:
            try:
                await self.event_bus.emit(event_type, data)
            except Exception as e:
                logger.error(f"Error emitting event: {str(e)}")
                
    @classmethod
    async def terminate_all(cls) -> int:
        """
        Terminate all registered resources. Useful for application shutdown.
        
        Returns:
            The number of resources terminated
        """
        # Get a thread-safe copy of all resources
        resources_copy = []
        with cls._resources_lock:
            resources_copy = list(cls._resources.values())
            
        # Terminate each resource
        terminate_count = 0
        for resource in resources_copy:
            try:
                success = await resource.terminate()
                if success:
                    terminate_count += 1
            except Exception as e:
                logger.error(f"Error terminating resource {resource.resource_id}: {e}")
                
        return terminate_count