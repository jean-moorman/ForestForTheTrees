"""
Base interface class for the FFTT system.
Contains the core functionality shared by all interfaces.
"""

from asyncio import Lock
import asyncio
from contextlib import contextmanager
from datetime import datetime
import logging
from typing import Dict, List, Any, Optional, Set, Tuple, Type, TypeVar, Union

from resources import (
    ResourceType,
    ResourceState,
    EventQueue,
    StateManager,
    CacheManager,
    AgentContextManager,
    MetricsManager,
    ErrorHandler,
    MemoryMonitor
)

from .errors import InitializationError, StateTransitionError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar('T', bound='BaseInterface')


class BaseInterface:
    """
    Base class for all interfaces in the FFTT system.
    Provides core functionality for state management, event handling, and resource management.
    """
    def __init__(
        self, 
        interface_id: str, 
        event_queue: EventQueue,
        state_manager: StateManager,
        context_manager: AgentContextManager,
        cache_manager: CacheManager,
        metrics_manager: MetricsManager,
        error_handler: ErrorHandler,
        memory_monitor: MemoryMonitor
    ):
        """
        Initialize the base interface.
        
        Args:
            interface_id: Unique identifier for this interface
            event_queue: Queue for handling events
            state_manager: Manager for state persistence
            context_manager: Manager for agent context
            cache_manager: Manager for caching
            metrics_manager: Manager for metrics collection
            error_handler: Handler for errors
            memory_monitor: Monitor for memory usage
        """
        self.interface_id = interface_id
        self._event_queue = event_queue
        
        # Store manager references directly
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        self._memory_monitor = memory_monitor
        
        # Defer lock creation to async initialization
        self._state_lock = None
        self._initialized = False
    
    async def ensure_initialized(self) -> None:
        """
        Ensure the interface is properly initialized with running event loop with race condition protection.
        """
        # Lazy initialize init_lock if needed
        if not hasattr(self, '_init_lock') or self._init_lock is None:
            self._init_lock = asyncio.Lock()
        
        async with self._init_lock:
            if not self._initialized:  # Check inside the lock
                logger.debug(f"Initializing interface {self.interface_id}")
                
                # Ensure event queue is running
                await self._ensure_event_queue_running()
                        
                # Create state lock now that event queue is started
                self._state_lock = asyncio.Lock()
                self._initialized = True
                
                # Register with memory monitor if not already registered
                if hasattr(self, '_memory_monitor') and self._memory_monitor:
                    try:
                        # Check if register_component is a coroutine function
                        if hasattr(self._memory_monitor, 'register_component'):
                            if asyncio.iscoroutinefunction(self._memory_monitor.register_component):
                                await self._memory_monitor.register_component(self.interface_id)
                            else:
                                self._memory_monitor.register_component(self.interface_id)
                    except Exception as e:
                        logger.warning(f"Failed to register with memory monitor: {str(e)}")

                logger.debug(f"Interface {self.interface_id} initialized successfully")

    @contextmanager
    def ensure_event_loop(self):
        """
        Context manager to ensure a running event loop using EventLoopManager.
        
        Returns:
            Running event loop
        """
        from resources.events import EventLoopManager
        
        created_new_loop = False
        loop = None
        
        try:
            try:
                # Use EventLoopManager to get a consistent loop
                loop = EventLoopManager.get_event_loop()
                logger.debug(f"Using existing event loop for {self.interface_id}")
            except RuntimeError:
                logger.debug(f"Creating new event loop for {self.interface_id}")
                
                # Let EventLoopManager create a new loop
                loop = EventLoopManager.get_event_loop()
                created_new_loop = True
                
            yield loop
            
        finally:
            # Only stop the loop if we created it and it's still running
            if created_new_loop and loop and loop.is_running():
                logger.debug(f"Stopping event loop created for {self.interface_id}")
                loop.stop()

    async def _ensure_event_queue_running(self) -> None:
        """
        Ensure event queue is running, with improved error handling and using EventLoopManager.
        """
        from resources.events import EventLoopManager
        
        max_retries = 3
        retry_count = 0
        
        # Get the queue ID for better logging
        queue_id = getattr(self._event_queue, '_id', 'unknown')
        
        while retry_count < max_retries:
            try:
                # Ensure we're in the correct event loop context
                loop = EventLoopManager.get_event_loop()
                
                # Check if EventQueue has running state
                if hasattr(self._event_queue, '_running'):
                    if not self._event_queue._running:
                        logger.debug(f"Starting event queue {queue_id} for interface {self.interface_id}")
                        
                        # Start the event queue
                        await self._event_queue.start()
                        
                        # Verify it's now running with explicit check
                        if not self._event_queue._running:
                            raise InitializationError(f"Failed to start event queue {queue_id} for {self.interface_id}")
                
                # Queue is running
                logger.debug(f"Event queue {queue_id} running for {self.interface_id}")
                
                # Add a small delay to allow for queue task to initialize
                await asyncio.sleep(0.05)
                
                return
                
            except Exception as e:
                retry_count += 1
                logger.warning(f"Event queue start attempt {retry_count}/{max_retries} for {queue_id} failed: {str(e)}")
                
                if retry_count >= max_retries:
                    logger.error(f"Failed to start event queue {queue_id} after {max_retries} attempts")
                    if isinstance(e, InitializationError):
                        raise
                    raise InitializationError(f"Failed to initialize event queue {queue_id}: {str(e)}")
                
                # Wait before retrying with exponential backoff
                await asyncio.sleep(0.1 * (2 ** retry_count))

    @classmethod
    async def create(cls: Type[T], interface_id: str) -> T:
        """
        Factory method to create interface with proper event queue setup using EventLoopManager.
        
        Args:
            interface_id: Unique identifier for the interface
            
        Returns:
            Initialized interface instance
        """
        from resources.events import EventLoopManager
        
        # Use EventLoopManager to get a consistent event loop
        loop = EventLoopManager.get_event_loop()
        
        # Create event queue with an ID for better tracking
        event_queue = EventQueue(queue_id=f"interface_{interface_id}_queue")
        
        # Start event queue in the managed loop
        await event_queue.start()
        
        # Create and return the interface instance
        return cls(interface_id, event_queue)

    async def cleanup(self) -> bool:
        """
        Coordinated cleanup with retries and detailed error reporting.
        
        Returns:
            True if successful, False otherwise
        """
        cleanup_successful = True
        cleanup_errors = []
        
        try:
            # Clean up memory monitor
            if hasattr(self, '_memory_monitor') and self._memory_monitor:
                try:
                    # Check if unregister_component exists
                    if hasattr(self._memory_monitor, 'unregister_component'):
                        if asyncio.iscoroutinefunction(self._memory_monitor.unregister_component):
                            await self._memory_monitor.unregister_component(self.interface_id)
                        else:
                            self._memory_monitor.unregister_component(self.interface_id)
                        logger.debug(f"Successfully unregistered {self.interface_id} from memory monitor")
                    else:
                        logger.debug(f"MemoryMonitor does not have unregister_component method - skipping")
                except Exception as e:
                    cleanup_errors.append(f"Memory monitor cleanup error: {str(e)}")
                    cleanup_successful = False
                    logger.warning(f"Failed to unregister from memory monitor: {str(e)}")

            # Clean up state if state manager exists
            if hasattr(self, '_state_manager') and self._state_manager:
                try:
                    # Set terminal state
                    await self._state_manager.set_state(
                        f"cleanup:{self.interface_id}",
                        {"status": "completed", "timestamp": datetime.now().isoformat()},
                        resource_type=ResourceType.STATE
                    )
                    logger.debug(f"Successfully set terminal state for {self.interface_id}")
                except Exception as e:
                    cleanup_errors.append(f"State cleanup error: {str(e)}")
                    cleanup_successful = False
                    logger.warning(f"Failed to set terminal state: {str(e)}")
            
            # Emit cleanup event if event queue exists
            if hasattr(self, '_event_queue') and self._event_queue:
                try:
                    if hasattr(self._event_queue, 'stop') and self._event_queue._running:
                        if asyncio.iscoroutinefunction(self._event_queue.stop):
                            await self._event_queue.stop()
                        else:
                            self._event_queue.stop()
                        logger.debug(f"Successfully stopped event queue for {self.interface_id}")
                except Exception as e:
                    cleanup_errors.append(f"Event queue cleanup error: {str(e)}")
                    cleanup_successful = False
                    logger.warning(f"Failed to stop event queue: {str(e)}")
                
                try:
                    from resources.events import ResourceEventTypes
                    await self._event_queue.emit(
                        ResourceEventTypes.RESOURCE_CLEANUP.value,
                        {
                            "interface_id": self.interface_id,
                            "status": "success" if cleanup_successful else "partial_failure",
                            "errors": cleanup_errors,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to emit cleanup event: {str(e)}")
                    # Don't fail the cleanup just because we couldn't emit an event
                
            # Log cleanup status
            if cleanup_errors:
                logger.warning(f"Cleanup completed with errors for {self.interface_id}: {'; '.join(cleanup_errors)}")
            else:
                logger.info(f"Cleanup completed successfully for {self.interface_id}")
                
            return cleanup_successful
        except Exception as e:
            logger.error(f"Critical error during interface cleanup: {str(e)}")
            # Try to emit critical failure event
            if hasattr(self, '_event_queue') and self._event_queue:
                try:
                    from resources.events import ResourceEventTypes
                    await self._event_queue.emit(
                        ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                        {
                            "interface_id": self.interface_id,
                            "error": str(e),
                            "error_type": "cleanup_failure",
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                except Exception:
                    pass  # Ignore failures here
            return False

    async def get_state(self) -> ResourceState:
        """
        Get current interface state asynchronously.
        
        Returns:
            Current state of the interface
        """
        state_entry = await self._state_manager.get_state(f"interface:{self.interface_id}")
        
        # If state_entry has a 'state' attribute (i.e., it's a StateEntry object), extract and return the state
        if hasattr(state_entry, 'state'):
            return state_entry.state
            
        # Otherwise, assume it's already a ResourceState enum or None
        return state_entry
        
    async def set_state(self, new_state: ResourceState, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Set interface state with improved error handling and retries.
        
        Args:
            new_state: New state to set
            metadata: Additional metadata to store with the state
        
        Raises:
            StateTransitionError: If state transition fails
        """
        if not isinstance(new_state, ResourceState):
            raise ValueError(f"Invalid state type: {type(new_state)}")
        
        # Ensure initialization
        await self.ensure_initialized()
        
        # Enhanced metadata
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "timestamp": datetime.now().isoformat(),
            "interface_id": self.interface_id
        })
        
        # Check if state lock exists
        if self._state_lock is None:
            logger.warning(f"State lock is None for {self.interface_id}, creating new lock")
            self._state_lock = asyncio.Lock()
        
        # Try with lock first (happy path)
        try:
            async with self._state_lock:
                # Double-check current state within lock
                current_state = None
                try:
                    current_state = await self.get_state()
                    if current_state == new_state:
                        return
                except Exception:
                    # Continue with state update even if we can't get current state
                    pass
                    
                # Update state
                await self._state_manager.set_state(
                    f"interface:{self.interface_id}",
                    new_state,
                    metadata=metadata,
                    resource_type=ResourceType.STATE
                )
                
                # Emit state change event
                try:
                    from resources.events import ResourceEventTypes
                    await self._event_queue.emit(
                        ResourceEventTypes.INTERFACE_STATE_CHANGED.value,
                        {
                            "interface_id": self.interface_id,
                            "old_state": current_state.name if current_state else "UNKNOWN",
                            "new_state": new_state.name,
                            "metadata": metadata
                        }
                    )
                except Exception as event_error:
                    logger.warning(f"Failed to emit state change event: {str(event_error)}")
                
                logger.debug(f"State for {self.interface_id} updated to {new_state}")
                return
        except Exception as e:
            logger.error(f"Error setting state for {self.interface_id}: {str(e)}")
        
        # Fall back to direct state setting without lock
        logger.warning(f"Falling back to lockless state update for {self.interface_id}")
        try:
            err_metadata = {**metadata, "error": "State lock acquisition failed"}
            await self._state_manager.set_state(
                f"interface:{self.interface_id}",
                new_state,
                metadata=err_metadata,
                resource_type=ResourceType.STATE
            )
            
            # Still try to emit the event
            try:
                from resources.events import ResourceEventTypes
                await self._event_queue.emit(
                    ResourceEventTypes.INTERFACE_STATE_CHANGED.value,
                    {
                        "interface_id": self.interface_id,
                        "old_state": "UNKNOWN",  # We couldn't check within lock
                        "new_state": new_state.name,
                        "metadata": err_metadata
                    }
                )
            except Exception:
                pass  # Ignore event emission errors in fallback path
                
            logger.debug(f"State for {self.interface_id} updated to {new_state} (without lock)")
        except Exception as inner_e:
            logger.error(f"Failed direct state setting for {self.interface_id}: {str(inner_e)}")
            raise StateTransitionError(f"Failed to set state to {new_state.name}: {str(inner_e)}")