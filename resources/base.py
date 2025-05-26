from asyncio.log import logger
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, Any, Optional, List, Set, Union

from abc import ABC, abstractmethod
import asyncio
import logging
import random
import threading
import time
from typing import Optional, Callable, Any, Awaitable, List, Dict

# Define interface stubs to avoid circular imports
# These will be properly defined later during system initialization
from abc import ABC, abstractmethod
from typing import Protocol
from enum import Enum, auto
from dataclasses import dataclass

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

from resources.common import HealthStatus, MemoryThresholds, CircuitBreakerConfig
from resources.errors import ErrorClassification, ErrorSeverity, ResourceError, ResourceExhaustionError, ResourceOperationError, ResourceTimeoutError
from resources.events import EventQueue, ResourceEventTypes, EventLoopManager
from resources.monitoring import SystemMonitor, SystemMonitorConfig, MemoryMonitor, HealthTracker, CircuitBreaker

logger = logging.getLogger(__name__)

def ensure_event_loop(context_name: str = "unknown") -> asyncio.AbstractEventLoop:
    """Ensure there's a running event loop or create one.
    
    Args:
        context_name: Name of the context for logging purposes
        
    Returns:
        The current event loop
    """
    try:
        # Try to get the running loop
        return asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, try to get one
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            # No event loop in this thread, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.info(f"Created new event loop in {context_name}")
            return loop

class PrioritizedLockManager:
    """
    Manages read/write locks with priority support and thread safety.
    
    This implementation uses threading locks consistently for thread safety
    across both synchronous and asynchronous contexts.
    """
    def __init__(self, writer_priority=False):
        # Use threading locks for all operations to ensure consistent thread safety
        self._read_lock = threading.RLock()
        self._write_lock = threading.RLock()
        
        # Lock for counter operations
        self._counter_lock = threading.RLock()
        
        # Counters protected by the counter lock
        self._read_count = 0
        self._write_waiting = 0
        self._read_waiting = 0
        
        # Configuration
        self._writer_priority = writer_priority
        
        # Tracking and metrics
        self._last_acquire_time = {}
        self._lock_metrics = {
            "read_acquire_times": [],
            "write_acquire_times": [],
            "read_wait_count": 0,
            "write_wait_count": 0
        }
        
        # Track owner information for better debugging
        self._read_owners = set()
        self._write_owner = None
        self._owner_info = {}
    
    async def acquire_read(self, timeout=None, track_id=None, owner_info=None):
        """
        Acquire read lock with priority awareness and timeout
        
        This method is thread-safe and can be called from any context.
        
        Args:
            timeout: Maximum time to wait for lock acquisition
            track_id: Optional identifier for tracking
            owner_info: Optional information about the owner for debugging
            
        Returns:
            Lock context manager
            
        Raises:
            asyncio.TimeoutError: If acquisition times out
        """
        start_time = time.monotonic()
        
        # Thread-safe counter increment
        with self._counter_lock:
            self._read_waiting += 1
            self._lock_metrics["read_wait_count"] += 1
            
        try:
            # Use a non-blocking approach with threading locks
            async def _acquire_read_lock():
                nonlocal start_time
                
                # Check writer priority first - this avoids writer starvation
                if self._writer_priority:
                    # Thread-safe check if writers are waiting
                    with self._counter_lock:
                        has_waiting_writers = self._write_waiting > 0
                    
                    # If writers are waiting, immediately timeout for fast failure
                    if has_waiting_writers and timeout:
                        raise asyncio.TimeoutError(
                            f"Read lock acquisition timed out due to writers waiting with priority"
                        )
                
                # Try to acquire the write lock in a non-blocking way
                acquired = False
                attempt_start = time.monotonic()
                
                while not acquired:
                    # Try to acquire with timeout
                    try:
                        acquired = self._write_lock.acquire(blocking=False)
                        if acquired:
                            break
                            
                        # Check if we've timed out
                        if timeout and (time.monotonic() - attempt_start > timeout):
                            raise asyncio.TimeoutError(f"Read lock acquisition timed out after {timeout}s")
                            
                        # Yield to the event loop to avoid blocking
                        await asyncio.sleep(0.001)
                        
                    except Exception as e:
                        logger.error(f"Error acquiring read lock: {e}")
                        raise
                
                # Thread-safe counter operations
                with self._counter_lock:
                    # Record metrics
                    acquire_time = time.monotonic() - start_time
                    self._lock_metrics["read_acquire_times"].append(acquire_time)
                    if len(self._lock_metrics["read_acquire_times"]) > 100:
                        self._lock_metrics["read_acquire_times"] = self._lock_metrics["read_acquire_times"][-100:]
                    
                    # Update counters and tracking
                    self._read_count += 1
                    
                    if track_id:
                        self._last_acquire_time[f"read:{track_id}"] = time.monotonic()
                        
                    # Track owner information
                    if owner_info:
                        owner_id = id(owner_info) if not isinstance(owner_info, str) else owner_info
                        self._read_owners.add(owner_id)
                        self._owner_info[owner_id] = owner_info
                    
                    # If this is not the first reader, release the write lock
                    if self._read_count > 1:
                        self._write_lock.release()
            
            # Execute the lock acquisition with timeout
            if timeout:
                await asyncio.wait_for(_acquire_read_lock(), timeout=timeout)
            else:
                await _acquire_read_lock()
                            
        except asyncio.TimeoutError:
            # Thread-safe counter decrement on failure
            with self._counter_lock:
                self._read_waiting -= 1
            raise
        except Exception:
            # Thread-safe counter decrement on any error
            with self._counter_lock:
                self._read_waiting -= 1
            raise
        finally:
            # Thread-safe counter decrement on success or failure
            with self._counter_lock:
                self._read_waiting -= 1
                
        # Return a context manager for the read lock
        class ReadLockContext:
            def __init__(self, lock_manager):
                self.lock_manager = lock_manager
                
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                await self.lock_manager.release_read(track_id, owner_info)
                
        return ReadLockContext(self)
    
    async def release_read(self, track_id=None, owner_info=None):
        """
        Release read lock
        
        Args:
            track_id: Optional identifier for tracking
            owner_info: Optional information about the owner for validation
        """
        # Thread-safe counter operations
        with self._counter_lock:
            if track_id and f"read:{track_id}" in self._last_acquire_time:
                # Calculate hold time for metrics
                hold_time = time.monotonic() - self._last_acquire_time[f"read:{track_id}"]
                del self._last_acquire_time[f"read:{track_id}"]
            
            # Update owner tracking
            if owner_info:
                owner_id = id(owner_info) if not isinstance(owner_info, str) else owner_info
                self._read_owners.discard(owner_id)
                if owner_id in self._owner_info:
                    del self._owner_info[owner_id]
            
            # Ensure we don't decrement below zero
            if self._read_count > 0:
                self._read_count -= 1
                
                # Last reader needs to release the write lock
                if self._read_count == 0:
                    try:
                        # Release the write lock - for threading.RLock this is safe
                        # because we're tracking acquisition separately
                        self._write_lock.release()
                    except RuntimeError as e:
                        # Log but don't fail if there's a lock release issue
                        logger.warning(f"Error releasing write lock: {str(e)}")
                
    async def acquire_write(self, timeout=None, track_id=None, owner_info=None):
        """
        Acquire write lock with timeout
        
        Args:
            timeout: Maximum time to wait for lock acquisition
            track_id: Optional identifier for tracking
            owner_info: Optional information about the owner for debugging
            
        Returns:
            Lock context manager
            
        Raises:
            asyncio.TimeoutError: If acquisition times out
        """
        start_time = time.monotonic()
        
        # Thread-safe counter increment
        with self._counter_lock:
            self._write_waiting += 1
            self._lock_metrics["write_wait_count"] += 1
            
        try:
            # Use non-blocking approach with threading locks
            async def _acquire_write_lock():
                # Try to acquire the lock in a non-blocking way
                acquired = False
                attempt_start = time.monotonic()
                
                while not acquired:
                    # Try to acquire with timeout
                    try:
                        acquired = self._write_lock.acquire(blocking=False)
                        if acquired:
                            break
                            
                        # Check if we've timed out
                        if timeout and (time.monotonic() - attempt_start > timeout):
                            raise asyncio.TimeoutError(f"Write lock acquisition timed out after {timeout}s")
                            
                        # Yield to the event loop to avoid blocking
                        await asyncio.sleep(0.001)
                        
                    except Exception as e:
                        logger.error(f"Error acquiring write lock: {e}")
                        raise
                
                # Thread-safe counter and tracking updates
                with self._counter_lock:
                    # Record metrics
                    acquire_time = time.monotonic() - start_time
                    self._lock_metrics["write_acquire_times"].append(acquire_time)
                    if len(self._lock_metrics["write_acquire_times"]) > 100:
                        self._lock_metrics["write_acquire_times"] = self._lock_metrics["write_acquire_times"][-100:]
                    
                    # Update tracking
                    if track_id:
                        self._last_acquire_time[f"write:{track_id}"] = time.monotonic()
                    
                    # Update owner information
                    if owner_info:
                        owner_id = id(owner_info) if not isinstance(owner_info, str) else owner_info
                        self._write_owner = owner_id
                        self._owner_info[owner_id] = owner_info
                
                # Create a context manager for the write lock
                class WriteLockContext:
                    def __init__(self, lock_manager):
                        self.lock_manager = lock_manager
                        
                    async def __aenter__(self):
                        return self
                        
                    async def __aexit__(self, exc_type, exc_val, exc_tb):
                        await self.lock_manager.release_write(track_id, owner_info)
                
                return WriteLockContext(self)
            
            # Execute the lock acquisition operation
            if timeout:
                result = await asyncio.wait_for(_acquire_write_lock(), timeout=timeout)
            else:
                result = await _acquire_write_lock()
                
            # Decrement waiting count on success
            with self._counter_lock:
                self._write_waiting -= 1
                
            return result
                
        except asyncio.TimeoutError:
            # Thread-safe counter decrement on timeout
            with self._counter_lock:
                self._write_waiting -= 1
            raise
        except Exception:
            # Thread-safe counter decrement on any error
            with self._counter_lock:
                self._write_waiting -= 1
            raise
            
    async def release_write(self, track_id=None, owner_info=None):
        """
        Release write lock
        
        Args:
            track_id: Optional identifier for tracking
            owner_info: Optional information about the owner for validation
        """
        # Thread-safe tracking updates
        with self._counter_lock:
            if track_id and f"write:{track_id}" in self._last_acquire_time:
                # Calculate hold time for metrics
                hold_time = time.monotonic() - self._last_acquire_time[f"write:{track_id}"]
                del self._last_acquire_time[f"write:{track_id}"]
            
            # Update owner tracking
            if owner_info:
                owner_id = id(owner_info) if not isinstance(owner_info, str) else owner_info
                if self._write_owner == owner_id:
                    self._write_owner = None
                if owner_id in self._owner_info:
                    del self._owner_info[owner_id]
        
        try:
            # For threading.RLock(), simply release - it tracks its own state
            self._write_lock.release()
        except RuntimeError as e:
            # Log but don't fail if there's a lock release issue
            logger.warning(f"Error releasing write lock: {str(e)}")
    
    def get_lock_metrics(self):
        """Get metrics about lock usage"""
        # Thread-safe metrics collection
        with self._counter_lock:
            metrics = dict(self._lock_metrics)
            
            # Calculate averages
            metrics["avg_read_acquire_time"] = (
                sum(self._lock_metrics["read_acquire_times"]) / 
                max(1, len(self._lock_metrics["read_acquire_times"]))
            )
            metrics["avg_write_acquire_time"] = (
                sum(self._lock_metrics["write_acquire_times"]) / 
                max(1, len(self._lock_metrics["write_acquire_times"]))
            )
            
            # Current state
            metrics["current_read_count"] = self._read_count
            metrics["current_write_waiting"] = self._write_waiting
            metrics["current_read_waiting"] = self._read_waiting
            metrics["read_owner_count"] = len(self._read_owners)
            metrics["has_write_owner"] = self._write_owner is not None
            
            return metrics
            
    def get_owner_info(self):
        """Get information about current lock owners for debugging"""
        # Thread-safe owner information collection
        with self._counter_lock:
            return {
                "read_owners": list(self._read_owners),
                "write_owner": self._write_owner,
                "owner_details": dict(self._owner_info)
            }

# Use interfaces for configuration classes
CleanupPolicy = ICleanupPolicy
CleanupConfig = ICleanupConfig

@dataclass
class ManagerConfig:
    """Configuration for BaseManager operations including timeouts"""
    default_operation_timeout: float = 30.0    # Default timeout for generic operations
    default_read_timeout: float = 10.0         # Default timeout for read lock acquisition
    default_write_timeout: float = 15.0        # Default timeout for write lock acquisition
    writer_priority: bool = False              # Whether to prioritize writers over readers
    max_retry_count: int = 3                   # Maximum number of retries
    retry_backoff_factor: float = 1.5          # Multiplier for retry backoff

# ErrorHandler has been moved to system_error_recovery.py


# Default configurations
DEFAULT_CACHE_CIRCUIT_CONFIG = CircuitBreakerConfig(
    failure_threshold=10,
    recovery_timeout=30,
    failure_window=30
)

DEFAULT_AGENT_CIRCUIT_CONFIG = CircuitBreakerConfig(
    failure_threshold=3,
    recovery_timeout=120,
    failure_window=300
)

class BaseManager(ABC):
    """
    Abstract base class for all resource managers.
    
    This class provides core functionality for resource management including:
    - Thread safety with proper locking
    - Lifecycle management (initialization, termination)
    - Circuit breaker pattern for fault tolerance
    - Memory and health monitoring
    - Resource cleanup
    - Error recovery
    
    By implementing IBaseResource, it provides consistent resource lifecycle management
    and centralized resource tracking while avoiding circular dependencies.
    """
    def __init__(self, 
                 event_queue: 'EventQueue',
                 circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
                 cleanup_config: Optional[CleanupConfig] = None,
                 memory_thresholds: Optional[MemoryThresholds] = None,
                 system_monitor_config: Optional[SystemMonitorConfig] = None,
                 manager_config: Optional[ManagerConfig] = None,
                 resource_id: Optional[str] = None):
        
        # First validate the event queue parameter
        if event_queue is None:
            raise ValueError("event_queue cannot be None. Use centralized event queue.")
            
        # Generate a unique ID for this manager instance if not provided
        if not resource_id:
            resource_id = f"{self.__class__.__name__.lower()}_{id(self)}"
            
        # We'll initialize with our own values instead of calling BaseResource.__init__
        # This avoids the circular dependency
        self._resource_id = resource_id
        self.event_bus = event_queue
        self._tasks = set()
        self._lock = threading.RLock()
        self._initialized = False
        self._terminated = False
        self._created_at = datetime.now()
        
        # Thread-safe lock for operation concurrency
        self._manager_lock = threading.RLock()
        
        # Basic locks for read/write operations using thread-safe PrioritizedLockManager
        self._lock_manager = PrioritizedLockManager(
            writer_priority=manager_config.writer_priority if manager_config else False
        )
        
        # Store configuration
        self._cleanup_config = cleanup_config
        self._config = manager_config or ManagerConfig()
        # Store memory thresholds for direct access
        self._memory_thresholds = memory_thresholds
        
        # Set up operation-specific locks for thread safety
        self._operation_locks = {}
        
        # Resource ownership tracking
        self._owned_resources = {}
        self._resource_dependencies = {}
        
        # Initialize health tracker first
        self._health_tracker = HealthTracker(event_queue)
        
        # Initialize memory monitor (singleton)
        self._memory_monitor = MemoryMonitor(
            event_queue=event_queue,
            thresholds=memory_thresholds
        )
        
        # Initialize error recovery helper
        # Use simplified version to avoid circular dependency
        from system_error_recovery_simple import SystemErrorRecoverySimple
        self._error_recovery = SystemErrorRecoverySimple(event_queue, health_tracker=self._health_tracker)
        
        # Initialize system monitor with all dependencies
        self._system_monitor = SystemMonitor(
            event_queue=event_queue,
            memory_monitor=self._memory_monitor,
            health_tracker=self._health_tracker,
            config=system_monitor_config
        )

        # Get circuit breaker registry singleton
        try:
            # Import here to avoid circular imports
            from resources.monitoring import CircuitBreakerRegistry
            self._circuit_registry = CircuitBreakerRegistry(
                event_queue=event_queue,
                health_tracker=self._health_tracker
            )
        except ImportError:
            logger.error(f"Failed to import CircuitBreakerRegistry, using fallback initialization")
            self._circuit_registry = None
        
        # Initialize and register circuit breaker
        try:
            # Import utility function to ensure event loop
            from resources.events.utils import ensure_event_loop
            
            # Get or create event loop
            loop = ensure_event_loop()
            
            # Get component type for configuration selection
            component_type = self.__class__.__name__.lower()
            
            # Create registration task
            if self._circuit_registry:
                register_task = loop.create_task(
                    self._get_or_create_circuit_breaker(
                        component_type, 
                        circuit_breaker_config
                    )
                )
                self._add_task(register_task)
            else:
                # Fallback to direct creation if registry not available
                self._circuit_breaker = CircuitBreaker(
                    name=self.resource_id,
                    event_queue=event_queue,
                    config=circuit_breaker_config
                )
                # Register with system monitor
                register_task = loop.create_task(
                    self._system_monitor.register_circuit_breaker(
                        self.resource_id,
                        self._circuit_breaker
                    )
                )
                self._add_task(register_task)
                
        except RuntimeError:
            # Handle case when no event loop is available
            logger.warning(f"No event loop available during {self.__class__.__name__} initialization")
            # Create fallback circuit breaker for operations to work
            self._circuit_breaker = CircuitBreaker(
                name=self.resource_id,
                event_queue=event_queue,
                config=circuit_breaker_config
            )
        
        # Register this manager with memory monitor
        self._memory_monitor.register_component(
            self.resource_id,
            thresholds=memory_thresholds
        )
        
        # Register with EventLoopManager for cleanup tracking
        try:
            EventLoopManager.register_resource(self.resource_id, self)
        except Exception as e:
            logger.warning(f"Error registering with EventLoopManager: {e}")
            
    async def initialize(self) -> bool:
        """
        Initialize the manager. This extends the BaseResource initialize method
        with manager-specific initialization.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        # Check initialization status
        with self._lock:
            if self._initialized:
                return True
                
            if self._terminated:
                logger.error(f"Cannot initialize terminated resource: {self._resource_id}")
                return False
                
            self._initialized = True
            
        # Perform manager-specific initialization
        try:
            # Start monitoring systems
            await self._memory_monitor.start()
            await self._system_monitor.start()
            
            # Initialize any owned resources
            with self._manager_lock:
                for resource_id, resource in self._owned_resources.items():
                    if hasattr(resource, "initialize") and callable(resource.initialize):
                        try:
                            await resource.initialize()
                        except Exception as e:
                            logger.error(f"Error initializing owned resource {resource_id}: {e}")
                            # Continue with other resources, don't fail completely
            
            return True
        except Exception as e:
            logger.error(f"Error during manager initialization: {e}")
            return False
            
    async def terminate(self) -> bool:
        """
        Terminate the manager and all owned resources. This extends the BaseResource
        terminate method with manager-specific cleanup.
        
        Returns:
            True if termination was successful, False otherwise
        """
        try:
            # Clean up owned resources in reverse dependency order
            await self._cleanup_owned_resources(force=True)
            
            # Stop monitoring systems
            await self._memory_monitor.stop()
            await self._system_monitor.stop()
            
            # Unregister from EventLoopManager
            try:
                EventLoopManager.unregister_resource(self.resource_id)
            except Exception as e:
                logger.warning(f"Error unregistering from EventLoopManager: {e}")
                
            # Mark as terminated
            with self._lock:
                if self._terminated:
                    return True
                    
                self._terminated = True
                
                # Cancel any pending tasks
                for task in self._tasks:
                    if not task.done():
                        task.cancel()
            
            return True
        except Exception as e:
            logger.error(f"Error during manager termination: {e}")
            return False
    
    # Implement IBaseResource interface properties
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
        
    def register_owned_resource(self, resource_id: str, resource: Any,
                              depends_on: Optional[List[str]] = None) -> None:
        """
        Register a resource as owned by this manager. Owned resources will be
        automatically cleaned up when the manager is terminated.
        
        Args:
            resource_id: The unique identifier for the resource
            resource: The resource object
            depends_on: Optional list of resource IDs that this resource depends on
        """
        with self._manager_lock:
            # Register the resource
            self._owned_resources[resource_id] = resource
            
            # Register dependencies if provided
            if depends_on:
                self._resource_dependencies[resource_id] = list(depends_on)
                
            # Log registration
            logger.debug(f"Registered owned resource {resource_id} with {self.__class__.__name__}")
    
    def unregister_owned_resource(self, resource_id: str) -> bool:
        """
        Unregister a resource from this manager.
        
        Args:
            resource_id: The unique identifier for the resource
            
        Returns:
            True if the resource was unregistered, False if it wasn't found
        """
        with self._manager_lock:
            if resource_id in self._owned_resources:
                # Remove the resource
                del self._owned_resources[resource_id]
                
                # Remove any dependencies
                if resource_id in self._resource_dependencies:
                    del self._resource_dependencies[resource_id]
                    
                # Remove from other resources' dependencies
                for other_id, deps in self._resource_dependencies.items():
                    if resource_id in deps:
                        deps.remove(resource_id)
                
                # Log unregistration
                logger.debug(f"Unregistered owned resource {resource_id} from {self.__class__.__name__}")
                return True
            return False
    
    async def _cleanup_owned_resources(self, force: bool = False) -> None:
        """
        Clean up all owned resources in reverse dependency order.
        
        Args:
            force: If True, perform an aggressive cleanup regardless of resource state
        """
        # Get thread-safe copy of resources
        resources_to_clean = {}
        dependencies = {}
        
        with self._manager_lock:
            resources_to_clean = dict(self._owned_resources)
            dependencies = {k: list(v) for k, v in self._resource_dependencies.items()}
        
        # Determine cleanup order based on dependencies
        cleanup_order = self._get_reverse_dependency_order(dependencies)
        
        # Clean up resources in order
        for resource_id in cleanup_order:
            if resource_id in resources_to_clean:
                resource = resources_to_clean[resource_id]
                try:
                    # Check for terminate method
                    if hasattr(resource, "terminate") and callable(resource.terminate):
                        await resource.terminate()
                    # Check for cleanup method
                    elif hasattr(resource, "cleanup") and callable(resource.cleanup):
                        await resource.cleanup(force=force)
                    # Check for close method
                    elif hasattr(resource, "close") and callable(resource.close):
                        await resource.close()
                except Exception as e:
                    logger.error(f"Error cleaning up owned resource {resource_id}: {e}")
                    # Continue with other resources, don't fail completely
    
    def _get_reverse_dependency_order(self, dependencies: Dict[str, List[str]]) -> List[str]:
        """
        Calculate the reverse order of dependencies to ensure resources are cleaned up
        in the correct order.
        
        Args:
            dependencies: A dictionary mapping resource IDs to their dependencies
            
        Returns:
            A list of resource IDs in cleanup order (dependent resources first)
        """
        # Build a graph of resource dependencies
        graph = {}
        for resource_id in self._owned_resources:
            graph[resource_id] = set()
            
        # Add dependencies to the graph
        for resource_id, deps in dependencies.items():
            if resource_id in graph:
                graph[resource_id].update(deps)
        
        # Topological sort
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(node):
            if node in temp_visited:
                # Cyclic dependency, break it
                logger.warning(f"Cyclic dependency detected for resource {node}")
                return
            if node not in visited:
                temp_visited.add(node)
                for neighbor in graph.get(node, []):
                    if neighbor in graph:  # Only visit if it's in our resources
                        visit(neighbor)
                temp_visited.remove(node)
                visited.add(node)
                order.append(node)
        
        # Visit all nodes
        for node in graph:
            if node not in visited:
                visit(node)
        
        # Reverse for cleanup order (dependents first)
        return order
        
    async def _get_or_create_circuit_breaker(self, component_type, config=None):
        """Get or create circuit breaker using the registry"""
        if not self._circuit_registry:
            # Fallback to direct creation if registry not available
            self._circuit_breaker = CircuitBreaker(
                name=self.resource_id,
                event_queue=self.event_bus,
                config=config
            )
            return
            
        # Get or create circuit breaker using registry
        self._circuit_breaker = await self._circuit_registry.get_or_create_circuit_breaker(
            name=self.resource_id,
            component=component_type,
            config=config
        )
    
    async def start(self) -> None:
        """Start all monitoring systems"""
        await self._memory_monitor.start()
        await self._system_monitor.start()
        
    async def stop(self) -> None:
        """Stop all monitoring systems"""
        await self._memory_monitor.stop()
        await self._system_monitor.stop()

    async def handle_operation_error(self, error: Exception, operation: str) -> None:
        """Handle errors in manager operations with standardized error handling"""
        try:
            # Get base component ID
            component_id = self.__class__.__name__.lower()
            
            # Use SystemErrorRecovery to handle the error
            cleanup_callback = lambda force: self.cleanup(force=force)
            classification = await self._error_recovery.handle_operation_error(
                error=error,
                operation=operation,
                component_id=component_id,
                cleanup_callback=cleanup_callback
            )
            
            return classification
            
        except Exception as e:
            # Ensure errors in error handling don't propagate
            logger.error(f"Error handling failed: {str(e)}")
            raise error  # Re-raise original error

    async def protected_operation(self, 
                                operation: str,
                                func: Callable[[], Awaitable[Any]],
                                timeout: Optional[float] = None) -> Any:
        """Execute operation with circuit breaker and error handling with timeout"""
        try:
            # Get component type for circuit breaker identification
            component_type = self.__class__.__name__.lower()
            
            # Use registry-aware execution if available
            if hasattr(self, '_circuit_registry') and self._circuit_registry is not None:
                # Check if circuit breaker is set or needs initialization
                if not hasattr(self, '_circuit_breaker') or self._circuit_breaker is None:
                    # Initialize the circuit breaker if not done yet
                    await self._get_or_create_circuit_breaker(component_type)
                    
                # Create operation key for more granular circuit breaking
                operation_circuit_name = f"{self.resource_id}_{operation}"
                
                # Execute through registry with fallback to local circuit breaker
                try:
                    return await self._circuit_registry.circuit_execute(
                        circuit_name=operation_circuit_name,
                        operation=lambda: self._ensure_thread_safety(
                            operation, 
                            lambda: self._execute_protected(operation, func, timeout)
                        ),
                        component=component_type
                    )
                except AttributeError:
                    # Fallback to local circuit breaker if circuit_execute not available
                    return await self._circuit_breaker.execute(
                        lambda: self._ensure_thread_safety(
                            operation, 
                            lambda: self._execute_protected(operation, func, timeout)
                        )
                    )
            else:
                # Fallback to direct execution with local circuit breaker
                return await self._circuit_breaker.execute(
                    lambda: self._ensure_thread_safety(
                        operation, 
                        lambda: self._execute_protected(operation, func, timeout)
                    )
                )
        except Exception as e:
            await self.handle_operation_error(e, operation)
            raise
            
    async def _ensure_thread_safety(self, operation_key: str, operation: Callable[[], Awaitable[Any]]) -> Any:
        """Ensure thread safety for operations using operation-specific locks
        
        Args:
            operation_key: Unique key for the operation to lock
            operation: Async callable to execute with thread safety
            
        Returns:
            The result of the operation
        """
        # Get or create a lock for this specific operation
        if operation_key not in self._operation_locks:
            self._operation_locks[operation_key] = asyncio.Lock()
            
        # Execute with lock protection
        async with self._operation_locks[operation_key]:
            # Debug logging for lock acquisition in high-contention scenarios
            logger.debug(f"Acquired lock for operation {operation_key} in {self.__class__.__name__}")
            
            try:
                # Execute the operation
                return await operation()
            except Exception as e:
                # Add operation context to exception
                if hasattr(e, 'set_operation'):
                    e.set_operation(operation_key)
                elif hasattr(e, 'operation') and not e.operation:
                    e.operation = operation_key
                # Re-raise for proper error handling
                raise
            finally:
                # Debug logging only in verbose mode to reduce noise
                logger.debug(f"Released lock for operation {operation_key} in {self.__class__.__name__}")

    async def _execute_protected(self, 
                               operation: str, 
                               func: Callable[[], Awaitable[Any]],
                               timeout: Optional[float] = None) -> Any:
        """Internal execution with proper error handling and timeout protection"""
        try:
            # Use existing wait_for pattern with configurable timeout
            timeout_value = timeout or (self._config.default_operation_timeout if hasattr(self, '_config') else 30.0)
            
            try:
                # Ensure there's a running event loop for wait_for
                ensure_event_loop(f"_execute_protected for {operation}")
                
                # Wrap operation execution in asyncio.wait_for()
                result = await asyncio.wait_for(func(), timeout=timeout_value)
            except asyncio.TimeoutError:
                # Convert to ResourceTimeoutError with detailed context
                error = ResourceTimeoutError(
                    resource_id=self.__class__.__name__.lower(),
                    operation=operation,
                    timeout_seconds=timeout_value,
                    details={"timeout_seconds": timeout_value}
                )
                # Use the error recovery system to handle the timeout
                await self.handle_operation_error(error, operation)
                raise error

            # Update health status on successful operation
            await self._health_tracker.update_health(
                self.__class__.__name__.lower(),
                HealthStatus(
                    status="HEALTHY",
                    source=self.__class__.__name__.lower(),
                    description=f"Operation {operation} completed successfully"
                )
            )
            
            return result
            
        except Exception as e:
            if not isinstance(e, ResourceTimeoutError):  # Avoid duplicate error handling
                await self.handle_operation_error(e, operation)
            raise
        
    async def protected_read(self, operation: Callable[[], Awaitable[Any]], 
                         timeout: Optional[float] = None) -> Any:
        """Execute a read operation with proper locking and timeout"""
        timeout_value = timeout or (self._config.default_read_timeout if hasattr(self, '_config') else 10.0)
        try:
            # Ensure there's a running event loop
            ensure_event_loop("protected_read")
            
            # Use wait_for on lock acquisition instead of asyncio.timeout
            async def _execute_with_lock():
                async with self._read_lock:
                    return await operation()
            
            return await asyncio.wait_for(_execute_with_lock(), timeout=timeout_value)
        except asyncio.TimeoutError:
            raise ResourceTimeoutError(
                resource_id=self.__class__.__name__.lower(),
                operation="read_lock_acquisition",
                timeout_seconds=timeout_value,
                details={"lock_type": "read"}
            )
            
    async def protected_write(self, operation: Callable[[], Awaitable[Any]],
                          timeout: Optional[float] = None) -> Any:
        """Execute a write operation with proper locking and timeout"""
        timeout_value = timeout or (self._config.default_write_timeout if hasattr(self, '_config') else 15.0)
        try:
            # Ensure there's a running event loop
            ensure_event_loop("protected_write")
            
            # Use wait_for on lock acquisition instead of asyncio.timeout
            async def _execute_with_lock():
                async with self._write_lock:
                    return await operation()
            
            return await asyncio.wait_for(_execute_with_lock(), timeout=timeout_value)
        except asyncio.TimeoutError:
            raise ResourceTimeoutError(
                resource_id=self.__class__.__name__.lower(),
                operation="write_lock_acquisition",
                timeout_seconds=timeout_value,
                details={"lock_type": "write"}
            )

    # More IBaseResource interface implementations
    @classmethod
    def get_resource(cls, resource_id: str) -> Optional['IBaseResource']:
        """
        Get a resource by ID from the global registry.
        
        Args:
            resource_id: The unique resource identifier
            
        Returns:
            The resource if found, None otherwise
        """
        # For BaseManager, this would be implemented differently than BaseResource
        # This is a placeholder implementation
        return None
    
    @classmethod
    def list_resources(cls) -> Dict[str, 'IBaseResource']:
        """
        Get a copy of all registered resources.
        
        Returns:
            A dictionary mapping resource IDs to resources
        """
        # For BaseManager, this would be implemented differently than BaseResource
        # This is a placeholder implementation
        return {}
    
    @classmethod
    async def terminate_all(cls) -> int:
        """
        Terminate all registered resources. Useful for application shutdown.
        
        Returns:
            The number of resources terminated
        """
        # For BaseManager, this would be implemented differently than BaseResource
        # This is a placeholder implementation
        return 0
        
    async def cleanup(self, force: bool = False) -> None:
        """Clean up resources according to cleanup policy with standardized approach
        
        This implementation provides a common cleanup pattern for all managers.
        Subclasses should override _cleanup_resources() to implement specific cleanup logic.
        
        Args:
            force: If True, perform an aggressive cleanup regardless of policy
        """
        try:
            logger.info(f"Starting cleanup for {self.__class__.__name__} (force={force})")
            
            # Unregister from EventLoopManager if registered
            component_id = self.__class__.__name__.lower()
            # Use resource_id from BaseResource for consistency
            EventLoopManager.unregister_resource(self.resource_id)
            
            # Cancel any pending tasks if we track them
            if hasattr(self, '_tasks'):
                for task in self._tasks:
                    if not task.done():
                        logger.debug(f"Cancelling task {task}")
                        task.cancel()
                        
                        # Wait briefly for cancellation to take effect
                        try:
                            await asyncio.wait_for(asyncio.shield(task), timeout=0.5)
                        except (asyncio.CancelledError, asyncio.TimeoutError):
                            pass
                            
            # Reset circuit breaker if severe cleanup is requested
            if force and hasattr(self, '_circuit_breaker') and self._circuit_breaker:
                try:
                    await self._circuit_breaker.reset()
                    logger.info(f"Reset circuit breaker for {component_id}")
                except Exception as e:
                    logger.error(f"Error resetting circuit breaker: {e}")
                    
            # Also reset operation-specific circuit breakers if using registry
            if force and hasattr(self, '_circuit_registry') and self._circuit_registry:
                try:
                    # Get all circuit breakers for this manager
                    circuit_pattern = f"{self._id}_"
                    for name in self._circuit_registry.circuit_names:
                        if name.startswith(circuit_pattern):
                            try:
                                # Reset each operation-specific circuit breaker
                                await self._circuit_registry.reset_circuit(name)
                                logger.info(f"Reset operation circuit breaker: {name}")
                            except Exception as e:
                                logger.error(f"Error resetting operation circuit breaker {name}: {e}")
                except Exception as e:
                    logger.error(f"Error accessing circuit registry during cleanup: {e}")
            
            # Call specific cleanup implementation
            await self._cleanup_resources(force)
            
            # Emit cleanup event
            try:
                await self.event_bus.emit(
                    ResourceEventTypes.RESOURCE_CLEANUP.value,
                    {
                        "resource_id": getattr(self, '_id', component_id),
                        "component": component_id,
                        "timestamp": datetime.now().isoformat(),
                        "force": force
                    }
                )
                logger.info(f"Cleanup completed for {component_id}")
            except Exception as e:
                logger.error(f"Error emitting cleanup event: {e}")
        except Exception as e:
            logger.error(f"Error during cleanup of {self.__class__.__name__}: {e}")
            # Don't re-raise, as cleanup should be best-effort and non-blocking
    
    @abstractmethod
    async def _cleanup_resources(self, force: bool = False) -> None:
        """Clean up specific resources according to cleanup policy
        
        This method should be implemented by subclasses to perform specific cleanup logic.
        
        Args:
            force: If True, perform an aggressive cleanup regardless of policy
        """
        pass
        
    async def get_health_status(self) -> HealthStatus:
        """Get current health status of the manager"""
        component_id = self.__class__.__name__.lower()
        return self._health_tracker.get_component_health(component_id) or HealthStatus(
            status="UNKNOWN",
            source=component_id,
            description="No health data available"
        )
    
    # implement_recovery_strategy has been moved to SystemErrorRecovery class
    
# Type exports
__all__ = [
    'CleanupPolicy',
    'CleanupConfig',
    'ManagerConfig',
    'PrioritizedLockManager',
    'BaseManager',
    'DEFAULT_CACHE_CIRCUIT_CONFIG',
    'DEFAULT_AGENT_CIRCUIT_CONFIG'
]