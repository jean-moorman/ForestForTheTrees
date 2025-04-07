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

from resources.common import HealthStatus, MemoryThresholds, CircuitBreakerConfig
from resources.errors import ErrorClassification, ErrorSeverity, ResourceError, ResourceExhaustionError, ResourceOperationError, ResourceTimeoutError
from resources.events import EventQueue, ResourceEventTypes, EventLoopManager
from resources.monitoring import SystemMonitor, SystemMonitorConfig, MemoryMonitor, HealthTracker, CircuitBreaker

class PrioritizedLockManager:
    """Manages read/write locks with priority support"""
    def __init__(self, writer_priority=False):
        self._read_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()
        self._counter_lock = asyncio.Lock()
        self._read_count = 0
        self._write_waiting = 0
        self._read_waiting = 0
        self._writer_priority = writer_priority
        self._last_acquire_time = {}
        self._lock_metrics = {
            "read_acquire_times": [],
            "write_acquire_times": [],
            "read_wait_count": 0,
            "write_wait_count": 0
        }
    
    async def acquire_read(self, timeout=None, track_id=None):
        """Acquire read lock with priority awareness and timeout
        
        Args:
            timeout: Maximum time to wait for lock acquisition
            track_id: Optional identifier for tracking
            
        Returns:
            Lock context manager
            
        Raises:
            asyncio.TimeoutError: If acquisition times out
        """
        start_time = time.monotonic()
        async with self._counter_lock:
            self._read_waiting += 1
            self._lock_metrics["read_wait_count"] += 1
            
        try:
            # Use asyncio.wait_for instead of asyncio.timeout for Python 3.10 compatibility
            async def _acquire_read_lock():
                # Check writer priority first - this avoids a deadlock situation
                if self._writer_priority:
                    # See if any writers are waiting without holding the counter lock
                    has_waiting_writers = False
                    async with self._counter_lock:
                        has_waiting_writers = self._write_waiting > 0
                
                    # If writers are waiting, immediately timeout for fast failure
                    if has_waiting_writers:
                        if timeout:
                            raise asyncio.TimeoutError(
                                f"Read lock acquisition timed out after {timeout}s due to writers waiting with priority"
                            )
                
                # Now proceed with normal acquisition
                async with self._counter_lock:
                    
                    # Record metrics
                    acquire_time = time.monotonic() - start_time
                    self._lock_metrics["read_acquire_times"].append(acquire_time)
                    if len(self._lock_metrics["read_acquire_times"]) > 100:
                        self._lock_metrics["read_acquire_times"] = self._lock_metrics["read_acquire_times"][-100:]
                    
                    self._read_count += 1
                    if track_id:
                        self._last_acquire_time[f"read:{track_id}"] = time.monotonic()
                    
                    if self._read_count == 1:
                        # First reader needs to acquire write lock
                        write_lock_acquired = False
                        try:
                            # Use wait_for for timeout
                            await asyncio.wait_for(self._write_lock.acquire(), timeout=timeout)
                            write_lock_acquired = True
                        except asyncio.TimeoutError:
                            # Cleanup - decrement read count since we failed
                            self._read_count -= 1
                            if track_id and f"read:{track_id}" in self._last_acquire_time:
                                del self._last_acquire_time[f"read:{track_id}"]
                            raise
            
            # Wait for the lock acquisition with timeout
            if timeout:
                await asyncio.wait_for(_acquire_read_lock(), timeout=timeout)
            else:
                await _acquire_read_lock()
                            
        finally:
            async with self._counter_lock:
                self._read_waiting -= 1
                
        # Return read lock object
        return self._read_lock
    
    async def release_read(self, track_id=None):
        """Release read lock"""
        async with self._counter_lock:
            if track_id and f"read:{track_id}" in self._last_acquire_time:
                # Calculate hold time for metrics
                hold_time = time.monotonic() - self._last_acquire_time[f"read:{track_id}"]
                del self._last_acquire_time[f"read:{track_id}"]
            
            # Ensure we don't decrement below zero
            if self._read_count > 0:
                self._read_count -= 1
                if self._read_count == 0:
                    # Last reader releases write lock
                    try:
                        # Only release if we're locked to avoid RuntimeError
                        if self._write_lock.locked():
                            self._write_lock.release()
                    except RuntimeError as e:
                        # Log but don't fail if there's a lock release issue
                        logger.warning(f"Error releasing write lock: {str(e)}")
                
    async def acquire_write(self, timeout=None, track_id=None):
        """Acquire write lock with timeout
        
        Args:
            timeout: Maximum time to wait for lock acquisition
            track_id: Optional identifier for tracking
            
        Returns:
            Lock context manager
            
        Raises:
            asyncio.TimeoutError: If acquisition times out
        """
        start_time = time.monotonic()
        async with self._counter_lock:
            self._write_waiting += 1
            self._lock_metrics["write_wait_count"] += 1
            
        try:
            # Use asyncio.wait_for instead of asyncio.timeout for Python 3.10 compatibility
            async def _acquire_write_lock():
                await self._write_lock.acquire()
                
                # Record metrics
                acquire_time = time.monotonic() - start_time
                self._lock_metrics["write_acquire_times"].append(acquire_time)
                if len(self._lock_metrics["write_acquire_times"]) > 100:
                    self._lock_metrics["write_acquire_times"] = self._lock_metrics["write_acquire_times"][-100:]
                
                if track_id:
                    self._last_acquire_time[f"write:{track_id}"] = time.monotonic()
                
                async with self._counter_lock:
                    self._write_waiting -= 1
                
                return self._write_lock
            
            # Wait for the lock acquisition with timeout
            if timeout:
                return await asyncio.wait_for(_acquire_write_lock(), timeout=timeout)
            else:
                return await _acquire_write_lock()
                
        except asyncio.TimeoutError:
            async with self._counter_lock:
                self._write_waiting -= 1
            raise
            
    async def release_write(self, track_id=None):
        """Release write lock"""
        if track_id and f"write:{track_id}" in self._last_acquire_time:
            # Calculate hold time for metrics
            hold_time = time.monotonic() - self._last_acquire_time[f"write:{track_id}"]
            del self._last_acquire_time[f"write:{track_id}"]
        
        try:
            # Only release if we're locked to avoid RuntimeError
            if self._write_lock.locked():
                self._write_lock.release()
        except RuntimeError as e:
            # Log but don't fail if there's a lock release issue
            logger.warning(f"Error releasing write lock: {str(e)}")
    
    def get_lock_metrics(self):
        """Get metrics about lock usage"""
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
        
        return metrics

# Configuration Enums and Classes
class CleanupPolicy(Enum):
    """Policy for resource cleanup"""
    TTL = auto()           # Time-based expiration
    MAX_SIZE = auto()      # Size-based retention
    HYBRID = auto()        # Combination of TTL and size
    AGGRESSIVE = auto()    # Low-tolerance timeouts

@dataclass
class CleanupConfig:
    """Configuration for cleanup behavior"""
    policy: CleanupPolicy
    ttl_seconds: Optional[int] = None          # For TTL and HYBRID policies
    max_size: Optional[int] = None             # For MAX_SIZE and HYBRID policies
    check_interval: int = 300                  # Seconds between cleanup checks
    batch_size: int = 100   

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
    """Abstract base class for all resource managers"""
    def __init__(self, 
                 event_queue: 'EventQueue',
                 circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
                 cleanup_config: Optional[CleanupConfig] = None,
                 memory_thresholds: Optional[MemoryThresholds] = None,
                 system_monitor_config: Optional[SystemMonitorConfig] = None,
                 manager_config: Optional[ManagerConfig] = None):
        
        # First validate the event queue parameter
        if event_queue is None:
            raise ValueError("event_queue cannot be None. Use centralized event queue.")
            
        # Generate a unique ID for this manager instance
        self._id = f"{self.__class__.__name__.lower()}_{id(self)}"
        
        # Basic locks for read/write operations
        self._read_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()
        
        # Store configuration
        self._event_queue = event_queue
        self._cleanup_config = cleanup_config
        self._config = manager_config or ManagerConfig()

        # Set up operation-specific locks for thread safety
        self._operation_locks = {}
        
        # Track tasks for proper cleanup
        self._tasks = set()

        # Initialize error recovery helper
        # Use delayed import to avoid circular dependency
        from system_error_recovery import SystemErrorRecovery
        self._error_recovery = SystemErrorRecovery(event_queue, health_tracker=self._health_tracker)

        # Initialize memory monitor (singleton)
        self._memory_monitor = MemoryMonitor(
            event_queue=event_queue,
            thresholds=memory_thresholds
        )
        
        # Initialize health tracker
        self._health_tracker = HealthTracker(event_queue)
        
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
            # Get event loop and create registration task
            loop = asyncio.get_event_loop()
            
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
                self._tasks.add(register_task)
                register_task.add_done_callback(lambda t: self._tasks.discard(t))
            else:
                # Fallback to direct creation if registry not available
                self._circuit_breaker = CircuitBreaker(
                    name=self._id,
                    event_queue=event_queue,
                    config=circuit_breaker_config
                )
                # Register with system monitor
                register_task = loop.create_task(
                    self._system_monitor.register_circuit_breaker(
                        self._id,
                        self._circuit_breaker
                    )
                )
                self._tasks.add(register_task)
                register_task.add_done_callback(lambda t: self._tasks.discard(t))
                
        except RuntimeError:
            # Handle case when no event loop is available
            logger.warning(f"No event loop available during {self.__class__.__name__} initialization")
            # Create fallback circuit breaker for operations to work
            self._circuit_breaker = CircuitBreaker(
                name=self._id,
                event_queue=event_queue,
                config=circuit_breaker_config
            )
        
        # Register this manager with memory monitor
        self._memory_monitor.register_component(
            self._id,
            thresholds=memory_thresholds
        )
        
        # Register with EventLoopManager for cleanup tracking
        EventLoopManager.register_resource(self._id, self)
        
    async def _get_or_create_circuit_breaker(self, component_type, config=None):
        """Get or create circuit breaker using the registry"""
        if not self._circuit_registry:
            # Fallback to direct creation if registry not available
            self._circuit_breaker = CircuitBreaker(
                name=self._id,
                event_queue=self._event_queue,
                config=config
            )
            return
            
        # Get or create circuit breaker using registry
        self._circuit_breaker = await self._circuit_registry.get_or_create_circuit_breaker(
            name=self._id,
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
                operation_circuit_name = f"{self._id}_{operation}"
                
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
            if hasattr(self, '_id'):
                EventLoopManager.unregister_resource(self._id)
            else:
                EventLoopManager.unregister_resource(component_id)
            
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
                await self._event_queue.emit(
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