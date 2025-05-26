"""
Thread and event loop management with clear ownership boundaries.

This module provides simplified event loop management with a focus on thread
ownership and actor-based design, ensuring consistent loop usage, resource
tracking, and proper cleanup.

This module has been refactored to eliminate circular dependencies by removing
direct imports from the circuit breaker modules. Instead, it uses simple thread-based
locking mechanisms without dependencies on other components of the system.
"""
import asyncio
import concurrent.futures
import logging
import threading
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple, Set, Callable, Awaitable

logger = logging.getLogger(__name__)

class ThreadLocalEventLoopStorage:
    """
    Thread-local storage for event loops with clear thread ownership.
    
    This class implements a singleton that tracks event loops per thread,
    ensuring proper isolation and preventing cross-thread access issues.
    """
    _instance = None
    _instance_lock = threading.RLock()  # Class-level lock for thread-safe singleton creation
    
    def __init__(self):
        # Thread-local storage for event loops
        self._storage = threading.local()
        
        # Global registry of all loops with thread ownership information
        # Maps loop_id -> (loop, thread_id, creation_time)
        self._global_registry = {}
        self._registry_lock = threading.RLock()
        
        # State tracking
        self._active_loops = set()
        self._loop_states = {}  # Maps loop_id to state
        
    @classmethod
    def get_instance(cls):
        """Get singleton instance with thread safety."""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = ThreadLocalEventLoopStorage()
            return cls._instance
    
    def get_loop(self, thread_id=None):
        """
        Get event loop for current thread or specified thread.
        
        Args:
            thread_id: Optional thread ID to get loop for
            
        Returns:
            asyncio.AbstractEventLoop or None: The event loop for the thread
        """
        target_thread = thread_id or threading.get_ident()
        
        # Always use this thread's loop if requested from this thread
        if target_thread == threading.get_ident():
            if not hasattr(self._storage, 'loop'):
                return None
                
            # Verify loop is still valid before returning
            loop = self._storage.loop
            if loop.is_closed():
                logger.warning(f"Found closed loop in thread {threading.get_ident()}, creating new one")
                # Remove closed loop reference
                self.clear_loop()
                return None
                
            return loop
            
        # Otherwise look in global registry for specified thread with proper locking
        with self._registry_lock:
            # Direct lookup by thread ID
            for loop_id, (loop, registered_thread_id, _) in self._global_registry.items():
                if registered_thread_id == target_thread:
                    # Verify loop is still valid
                    if loop.is_closed():
                        logger.warning(f"Found closed loop for thread {target_thread}, will be removed")
                        continue
                    return loop
        
        return None
    
    def set_loop(self, loop):
        """
        Store event loop for current thread.
        
        Args:
            loop: The event loop to store
            
        Returns:
            asyncio.AbstractEventLoop: The stored loop
        """
        if loop.is_closed():
            logger.warning("Attempted to store closed event loop")
            return None
            
        self._storage.loop = loop
        thread_id = threading.get_ident()
        creation_time = time.time()
        
        # Also register in global registry with proper locking
        with self._registry_lock:
            loop_id = id(loop)
            self._global_registry[loop_id] = (loop, thread_id, creation_time)
            self._active_loops.add(loop_id)
            self._loop_states[loop_id] = "running"
            
        logger.debug(f"Set loop {loop_id} for thread {thread_id}")
        return loop
    
    def clear_loop(self):
        """Clear event loop for current thread with enhanced cleanup."""
        if hasattr(self._storage, 'loop'):
            loop = self._storage.loop
            loop_id = id(loop)
            
            # Update loop state
            with self._registry_lock:
                if loop_id in self._loop_states:
                    self._loop_states[loop_id] = "closed"
                
                # Remove from global registry
                if loop_id in self._global_registry:
                    del self._global_registry[loop_id]
                    self._active_loops.discard(loop_id)
                    
            # Clear thread-local storage
            delattr(self._storage, 'loop')
            logger.debug(f"Cleared loop {loop_id} for thread {threading.get_ident()}")
            
    def get_thread_for_loop(self, loop_id):
        """
        Get thread ID for a loop ID.
        
        Args:
            loop_id: The ID of the loop to get thread for
            
        Returns:
            int or None: The thread ID for the loop
        """
        with self._registry_lock:
            if loop_id in self._global_registry:
                return self._global_registry[loop_id][1]
        return None
        
    def get_loop_for_thread(self, thread_id):
        """
        Get the event loop associated with a specific thread.
        
        Args:
            thread_id: The thread ID to find the loop for
            
        Returns:
            asyncio.AbstractEventLoop or None: The event loop for the thread
        """
        with self._registry_lock:
            for loop_id, (loop, registered_thread_id, _) in self._global_registry.items():
                if registered_thread_id == thread_id:
                    # Verify loop is still valid
                    if not loop.is_closed():
                        return loop
                    else:
                        logger.warning(f"Found closed loop for thread {thread_id}, removing from registry")
                        # Remove closed loop reference
                        del self._global_registry[loop_id]
                        self._active_loops.discard(loop_id)
                        self._loop_states[loop_id] = "removed"
        return None
    
    def list_all_loops(self):
        """
        List all registered loops.
        
        Returns:
            List[Tuple[asyncio.AbstractEventLoop, int, float]]: List of (loop, thread_id, creation_time)
        """
        with self._registry_lock:
            return list(self._global_registry.values())
            
    def cleanup_stale_loops(self, max_age_seconds=3600):
        """
        Clean up loops that haven't been used for a while.
        
        Args:
            max_age_seconds: Maximum age in seconds for loops to keep
            
        Returns:
            List[int]: List of loop IDs that were cleaned up
        """
        current_time = time.time()
        stale_loops = []
        
        with self._registry_lock:
            for loop_id, (loop, thread_id, creation_time) in list(self._global_registry.items()):
                # Check if loop is closed
                try:
                    if loop.is_closed():
                        stale_loops.append(loop_id)
                        continue
                except Exception:
                    # If we can't check loop status, consider it stale
                    stale_loops.append(loop_id)
                    continue
                    
                # Check age
                if current_time - creation_time > max_age_seconds:
                    stale_loops.append(loop_id)
            
            # Remove stale loops
            for loop_id in stale_loops:
                if loop_id in self._global_registry:
                    loop, thread_id, _ = self._global_registry[loop_id]
                    del self._global_registry[loop_id]
                    self._active_loops.discard(loop_id)
                    self._loop_states[loop_id] = "removed"
                    logger.info(f"Removed stale loop {loop_id} for thread {thread_id}")
        
        return stale_loops
        
    def get_loop_stats(self):
        """
        Get statistics about registered loops.
        
        Returns:
            Dict[str, Any]: Dictionary of statistics
        """
        with self._registry_lock:
            stats = {
                "total_loops": len(self._global_registry),
                "active_loops": len(self._active_loops),
                "loop_states": dict(self._loop_states),
                "thread_loops": {}
            }
            
            # Count loops per thread
            thread_counts = {}
            for _, (_, thread_id, _) in self._global_registry.items():
                thread_counts[thread_id] = thread_counts.get(thread_id, 0) + 1
                
            stats["thread_loops"] = thread_counts
            
            return stats


class EventLoopManager:
    """
    Simplified event loop management with focus on thread boundaries.
    
    This class manages event loops with a clear focus on thread ownership,
    minimizing cross-thread access, and providing utilities for running 
    code in the proper context.
    """
    _instance = None
    _instance_lock = threading.RLock()
    _primary_loop = None
    _primary_thread_id = None
    _initialized = False
    _resource_registry = {}
    _loop_storage = ThreadLocalEventLoopStorage.get_instance()  # Initialize at class definition
    _executor = None
    _shutdown_in_progress = False
    
    @classmethod
    def get_instance(cls):
        """Singleton pattern to ensure only one event loop manager exists."""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = EventLoopManager()
                # Ensure thread-local storage is initialized
                if cls._loop_storage is None:
                    cls._loop_storage = ThreadLocalEventLoopStorage.get_instance()
            return cls._instance
    
    @classmethod
    def set_primary_loop(cls, loop):
        """
        Explicitly set the primary event loop for the application.
        
        Args:
            loop: The event loop to use as the primary loop
            
        Returns:
            bool: True if the loop was set successfully, False otherwise
        """
        with cls._instance_lock:
            if loop.is_closed():
                logger.warning("Attempted to set closed event loop as primary")
                return False
                
            cls._primary_loop = loop
            cls._primary_thread_id = threading.get_ident()
            cls._initialized = True
            
            # Store in thread-local storage
            if cls._loop_storage is None:
                cls._loop_storage = ThreadLocalEventLoopStorage.get_instance()
            cls._loop_storage.set_loop(loop)
            
            logger.info(f"Explicitly set primary loop {id(loop)} on thread {threading.get_ident()}")
            return True
    
    @classmethod
    def get_primary_loop(cls):
        """
        Get the primary event loop for the application.
        
        Returns:
            asyncio.AbstractEventLoop or None: The primary event loop or None if not initialized
        """
        with cls._instance_lock:
            if not cls._initialized or cls._primary_loop is None:
                return None
                
            # Verify the loop is still valid
            if cls._primary_loop.is_closed():
                logger.warning("Primary loop is closed, returning None")
                return None
                
            return cls._primary_loop
    
    @classmethod
    def get_loop_for_thread(cls, thread_id):
        """
        Get the event loop associated with a specific thread.
        
        Args:
            thread_id: The thread ID to find the loop for
            
        Returns:
            asyncio.AbstractEventLoop or None: The event loop for the thread
        """
        # Initialize if needed
        if cls._loop_storage is None:
            cls._loop_storage = ThreadLocalEventLoopStorage.get_instance()
            
        # Delegate to thread local storage
        return cls._loop_storage.get_loop_for_thread(thread_id)
        
    @classmethod
    def get_event_loop(cls):
        """
        Get the current event loop or create a new one.
        
        This method prioritizes proper thread ownership, creating a new event loop
        per thread rather than sharing loops across threads.
        
        Returns:
            asyncio.AbstractEventLoop: The event loop for the current thread
        """
        # Initialize if needed
        instance = cls.get_instance()
        
        # First check thread-local storage
        current_thread_id = threading.get_ident()
        existing_loop = cls._loop_storage.get_loop()
        
        if existing_loop is not None and not existing_loop.is_closed():
            # Thread already has a valid loop
            return existing_loop
            
        try:
            # Try to get the running loop
            loop = asyncio.get_running_loop()
            
            # Store in thread-local storage if it's valid
            if not loop.is_closed():
                cls._loop_storage.set_loop(loop)
                
                # Initialize primary loop if needed
                if not cls._initialized:
                    with cls._instance_lock:
                        if not cls._initialized:  # Double-check inside lock
                            cls._primary_loop = loop
                            cls._primary_thread_id = current_thread_id
                            cls._initialized = True
                            logger.debug(f"Initialized with primary loop {id(loop)} on thread {current_thread_id}")
                
                return loop
                
        except RuntimeError:
            # No running loop, create a new one
            pass
            
        # Create a new loop
        with cls._instance_lock:
            # Set primary loop if not set
            if cls._primary_loop is None:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                cls._loop_storage.set_loop(loop)
                cls._primary_loop = loop
                cls._primary_thread_id = current_thread_id
                cls._initialized = True
                logger.debug(f"Created new primary loop {id(loop)} on thread {current_thread_id}")
            else:
                # Create a thread-local loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                cls._loop_storage.set_loop(loop)
                logger.debug(f"Created thread-local loop {id(loop)} on thread {current_thread_id}")
                
        return loop
    
    @classmethod
    def ensure_event_loop(cls):
        """
        Ensure the current thread has a valid event loop, creating one if needed.
        
        Returns:
            asyncio.AbstractEventLoop: The event loop for the current thread
        """
        try:
            # First try getting existing running loop
            loop = asyncio.get_running_loop()
            
            # Verify it's not closed
            if loop.is_closed():
                logger.warning(f"Found closed running loop in thread {threading.get_ident()}, creating new one")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            # Store in thread-local storage
            cls._loop_storage.set_loop(loop)
            return loop
            
        except RuntimeError:
            # No running loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Store in thread-local storage
            cls._loop_storage.set_loop(loop)
            return loop
    
    @classmethod
    def run_coroutine_threadsafe(cls, coro, target_loop=None):
        """
        Run a coroutine in a specific event loop, even from a different thread.
        
        This is a key method for safe cross-thread communication between actors.
        
        Args:
            coro: The coroutine to run
            target_loop: The target event loop (defaults to primary loop)
            
        Returns:
            concurrent.futures.Future: A future that will contain the result
        """
        # Ensure loop storage is initialized
        if cls._loop_storage is None:
            cls._loop_storage = ThreadLocalEventLoopStorage.get_instance()
            
        if target_loop is None:
            # Try to get the event loop from the current thread first
            target_loop = cls._loop_storage.get_loop()
            
            # If no loop in current thread, use primary loop as default target
            if target_loop is None:
                # Initialize if needed
                if cls._primary_loop is None:
                    # Create a new primary loop if none exists
                    cls._primary_loop = asyncio.new_event_loop()
                    cls._primary_thread_id = threading.get_ident()
                    cls._initialized = True
                    thread = threading.Thread(target=cls._run_loop_in_thread, args=(cls._primary_loop,))
                    thread.daemon = True
                    thread.start()
                    logger.debug(f"Created new primary loop {id(cls._primary_loop)} in background thread")
                
                # Verify primary loop is still valid
                if cls._primary_loop.is_closed():
                    logger.warning("Primary loop is closed, creating a new one for operation")
                    # Create a new loop and run it in a new thread
                    new_loop = asyncio.new_event_loop()
                    thread = threading.Thread(target=cls._run_loop_in_thread, args=(new_loop,))
                    thread.daemon = True
                    thread.start()
                    cls._primary_loop = new_loop
                    cls._primary_thread_id = thread.ident
                    target_loop = new_loop
                else:
                    target_loop = cls._primary_loop
        
        # Verify target loop is valid
        if target_loop.is_closed():
            logger.warning("Target loop is closed, creating a new one for operation")
            new_loop = asyncio.new_event_loop()
            thread = threading.Thread(target=cls._run_loop_in_thread, args=(new_loop,))
            thread.daemon = True
            thread.start()
            target_loop = new_loop
        
        # Check if we're in the same thread as the target loop
        current_thread = threading.get_ident()
        target_thread = cls._loop_storage.get_thread_for_loop(id(target_loop))
        
        if target_thread == current_thread:
            # Same thread, create a task directly
            try:
                return asyncio.create_task(coro)
            except RuntimeError as e:
                if "no current event loop" in str(e).lower():
                    # No current event loop, set it
                    asyncio.set_event_loop(target_loop)
                    return asyncio.create_task(coro)
                else:
                    raise
        else:
            # Different thread, use threadsafe call
            try:
                future = asyncio.run_coroutine_threadsafe(coro, target_loop)
                return future
            except RuntimeError as e:
                if "loop is closed" in str(e).lower():
                    # Loop was closed, create a new one
                    logger.warning("Loop closed during run_coroutine_threadsafe, creating new loop")
                    new_loop = asyncio.new_event_loop()
                    thread = threading.Thread(target=cls._run_loop_in_thread, args=(new_loop,))
                    thread.daemon = True
                    thread.start()
                    # Try again with new loop
                    return asyncio.run_coroutine_threadsafe(coro, new_loop)
                else:
                    raise
    
    @classmethod
    def _run_loop_in_thread(cls, loop):
        """
        Run an event loop in the current thread.
        
        Args:
            loop: The event loop to run
        """
        asyncio.set_event_loop(loop)
        cls._loop_storage.set_loop(loop)
        logger.debug(f"Started event loop {id(loop)} in thread {threading.get_ident()}")
        
        try:
            loop.run_forever()
        finally:
            # Clean up when loop stops
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            # Run loop until all tasks complete with cancellation
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
            logger.debug(f"Event loop {id(loop)} in thread {threading.get_ident()} closed")
    
    @classmethod
    def register_resource(cls, resource_id, resource):
        """
        Register a resource with the event loop manager for proper tracking.
        
        Args:
            resource_id: The ID of the resource
            resource: The resource to register
        """
        # Record thread and loop context
        loop = cls.get_event_loop()
        resource._creation_loop_id = id(loop)
        resource._loop_thread_id = threading.get_ident()
        resource._creation_time = time.time()
        resource._resource_id = resource_id
        
        # Store in registry
        with cls._instance_lock:
            cls._resource_registry[resource_id] = resource
            
        logger.debug(f"Registered resource {resource_id}")
    
    @classmethod
    def unregister_resource(cls, resource_id):
        """
        Unregister a resource from the event loop manager.
        
        Args:
            resource_id: The ID of the resource to unregister
        """
        with cls._instance_lock:
            if resource_id in cls._resource_registry:
                del cls._resource_registry[resource_id]
                logger.debug(f"Unregistered resource {resource_id}")
    
    @classmethod
    async def submit_to_resource_loop(cls, resource_id, coro):
        """
        Submit a coroutine to the loop where a resource was created.
        
        This method is DEPRECATED and should not be used. Instead, use the
        actor model with explicit thread ownership and message passing.
        
        Args:
            resource_id: The ID of the resource
            coro: The coroutine to run
            
        Returns:
            Any: The result of the coroutine
        """
        logger.warning("submit_to_resource_loop is deprecated - use actor model instead")
        
        # For backward compatibility, just run the coroutine in the current loop
        return await coro
    
    @classmethod
    async def run_in_executor(cls, func, *args, **kwargs):
        """
        Run a blocking function in the thread pool executor.
        
        Args:
            func: The function to run
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Any: The result of the function
        """
        # Create thread pool executor if needed
        if cls._executor is None:
            cls._executor = concurrent.futures.ThreadPoolExecutor()
        
        # Get the event loop
        loop = asyncio.get_running_loop()
        
        # Run the function in the executor
        return await loop.run_in_executor(cls._executor, lambda: func(*args, **kwargs))
    
    @classmethod
    async def cleanup_resources(cls):
        """Clean up all registered resources for orderly shutdown."""
        # Signal shutdown in progress
        cls._shutdown_in_progress = True
        logger.info("Beginning orderly shutdown of resources")
        
        # Get a copy of resource IDs
        with cls._instance_lock:
            resource_ids = list(cls._resource_registry.keys())
        
        # Categorize resources for ordered shutdown
        resource_categories = {
            "event_queue": [],
            "manager": [],
            "monitor": [],
            "other": []
        }
        
        # Classify resources for ordered shutdown
        for resource_id in resource_ids:
            with cls._instance_lock:
                if resource_id not in cls._resource_registry:
                    continue
                resource = cls._resource_registry[resource_id]
            
            # Categorize based on name patterns
            if resource_id.startswith('event_queue'):
                resource_categories['event_queue'].append((resource_id, resource))
            elif any(m in resource_id for m in ['manager', 'cache', 'context']):
                resource_categories['manager'].append((resource_id, resource))
            elif any(m in resource_id for m in ['monitor', 'tracker']):
                resource_categories['monitor'].append((resource_id, resource))
            else:
                resource_categories['other'].append((resource_id, resource))
        
        # Shutdown order: other → monitors → managers → event queues
        shutdown_order = ['other', 'monitor', 'manager', 'event_queue']
        
        for category in shutdown_order:
            resources = resource_categories[category]
            logger.info(f"Shutting down {len(resources)} resources in group '{category}'")
            
            for resource_id, resource in resources:
                try:
                    # Just call stop method if available
                    if hasattr(resource, 'stop') and callable(resource.stop):
                        if asyncio.iscoroutinefunction(resource.stop):
                            try:
                                await asyncio.wait_for(resource.stop(), timeout=5.0)
                            except asyncio.TimeoutError:
                                logger.warning(f"Timeout stopping resource {resource_id}")
                        else:
                            resource.stop()
                    
                    # Try close method if stop not available
                    elif hasattr(resource, 'close') and callable(resource.close):
                        if asyncio.iscoroutinefunction(resource.close):
                            try:
                                await asyncio.wait_for(resource.close(), timeout=5.0)
                            except asyncio.TimeoutError:
                                logger.warning(f"Timeout closing resource {resource_id}")
                        else:
                            resource.close()
                    
                    # Try shutdown method as last resort
                    elif hasattr(resource, 'shutdown') and callable(resource.shutdown):
                        if asyncio.iscoroutinefunction(resource.shutdown):
                            try:
                                await asyncio.wait_for(resource.shutdown(), timeout=5.0)
                            except asyncio.TimeoutError:
                                logger.warning(f"Timeout shutting down resource {resource_id}")
                        else:
                            resource.shutdown()
                    
                    # Unregister resource
                    cls.unregister_resource(resource_id)
                    logger.debug(f"Resource {resource_id} cleaned up")
                    
                except Exception as e:
                    logger.error(f"Error cleaning up resource {resource_id}: {e}")
        
        # Clean up any remaining resources
        with cls._instance_lock:
            remaining = list(cls._resource_registry.keys())
            cls._resource_registry.clear()
            
        if remaining:
            logger.warning(f"Some resources were not properly cleaned up: {remaining}")
            
        # Clean up loops
        if cls._loop_storage:
            stale_loops = cls._loop_storage.cleanup_stale_loops(max_age_seconds=0)
            logger.info(f"Cleaned up {len(stale_loops)} event loops during shutdown")
            
        # Clean up executor
        if cls._executor:
            cls._executor.shutdown(wait=False)
            
        # Reset shutdown flag
        cls._shutdown_in_progress = False
        logger.info("Resource cleanup completed")
        
    @classmethod
    def get_stats(cls):
        """
        Get statistics about event loops and resources.
        
        Returns:
            Dict[str, Any]: Dictionary of statistics
        """
        with cls._instance_lock:
            stats = {
                "initialized": cls._initialized,
                "primary_loop_id": id(cls._primary_loop) if cls._primary_loop else None,
                "primary_thread_id": cls._primary_thread_id,
                "resource_count": len(cls._resource_registry),
                "shutdown_in_progress": cls._shutdown_in_progress,
            }
            
            # Add loop storage stats
            if cls._loop_storage:
                stats["loops"] = cls._loop_storage.get_loop_stats()
                
            # Categorize resources by type
            resource_types = {}
            for resource_id in cls._resource_registry:
                # Extract resource type from ID
                parts = resource_id.split('_')
                if len(parts) > 1:
                    resource_type = parts[0]
                    resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
                else:
                    resource_types["unknown"] = resource_types.get("unknown", 0) + 1
                    
            stats["resource_types"] = resource_types
            
            return stats