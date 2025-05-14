"""
Event loop management for consistent asyncio usage across threads.

This module provides centralized event loop management with thread-local storage, 
ensuring consistent loop usage, resource tracking, and proper cleanup.
"""
import asyncio
import concurrent.futures
import logging
import threading
import time
from typing import Dict, Any, List, Optional, Tuple, Set

logger = logging.getLogger(__name__)

class ThreadLocalEventLoopStorage:
    """Thread-local storage for event loops to ensure proper isolation with enhanced thread safety."""
    _instance = None
    _instance_lock = threading.RLock()  # Class-level lock for thread-safe singleton creation
    
    def __init__(self):
        self._storage = threading.local()
        self._global_registry = {}  # Maps loop_id to (loop, thread_id, creation_time) tuples
        self._registry_lock = threading.RLock()
        # Track active loops for cleanup
        self._active_loops = set()
        # Track loop states for debugging
        self._loop_states = {}  # Maps loop_id to state ("running", "closed", "stopping")
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance with proper thread safety"""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = ThreadLocalEventLoopStorage()
            return cls._instance
    
    def get_loop(self, thread_id=None):
        """Get event loop for current thread or specified thread with improved reliability"""
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
            # Use more efficient direct lookup by thread ID if available
            for loop_id, (loop, registered_thread_id, _) in self._global_registry.items():
                if registered_thread_id == target_thread:
                    # Verify loop is still valid
                    if loop.is_closed():
                        logger.warning(f"Found closed loop for thread {target_thread}, will be removed")
                        continue
                    return loop
        
        return None
    
    def set_loop(self, loop):
        """Store event loop for current thread with enhanced metadata"""
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
        """Clear event loop for current thread with enhanced cleanup"""
        if hasattr(self._storage, 'loop'):
            loop = self._storage.loop
            loop_id = id(loop)
            
            # Update loop state
            with self._registry_lock:
                if loop_id in self._loop_states:
                    self._loop_states[loop_id] = "closed"
                
            # Remove from global registry with proper locking
            with self._registry_lock:
                if loop_id in self._global_registry:
                    del self._global_registry[loop_id]
                    self._active_loops.discard(loop_id)
                    
            # Clear thread-local storage
            delattr(self._storage, 'loop')
            logger.debug(f"Cleared loop {loop_id} for thread {threading.get_ident()}")
            
    def get_thread_for_loop(self, loop_id):
        """Get thread ID for a loop ID with proper locking"""
        with self._registry_lock:
            if loop_id in self._global_registry:
                return self._global_registry[loop_id][1]
        return None
    
    def list_all_loops(self):
        """List all registered loops with proper locking"""
        with self._registry_lock:
            return list(self._global_registry.values())
            
    def cleanup_stale_loops(self, max_age_seconds=3600):
        """Clean up loops that haven't been used for a while"""
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
        """Get statistics about registered loops"""
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
    """Centralized event loop management with thread-local storage ensuring consistent loop usage and cleanup."""
    _instance = None
    _instance_lock = threading.RLock()  # Lock for thread-safe singleton creation
    _primary_loop = None
    _primary_thread_id = None
    _initialized = False
    _resource_registry = {}
    _loop_storage = None
    _executor = None
    _shutdown_in_progress = False
    _max_loop_age_seconds = 3600  # Default maximum loop age (1 hour)
    _cleanup_interval = 300  # Default cleanup interval (5 minutes)
    _last_cleanup_time = 0
    
    @classmethod
    def get_instance(cls):
        """Singleton pattern to ensure only one event loop manager exists with thread safety"""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = EventLoopManager()
                # Initialize thread-local storage
                cls._loop_storage = ThreadLocalEventLoopStorage.get_instance()
                # Track time of last cleanup
                cls._last_cleanup_time = time.time()
                # We'll create a thread pool executor once needed
            return cls._instance
    
    @classmethod
    def get_event_loop(cls):
        """Get the current event loop or create a new one consistently with enhanced thread safety
        
        This method will:
        1. Check if the current thread already has a loop
        2. Try to get the running loop if one exists
        3. Create a new loop if needed
        4. Periodically clean up stale loops
        
        Returns:
            asyncio.AbstractEventLoop: The event loop for the current thread
        """
        instance = cls.get_instance()
        
        # Run periodic cleanup if needed
        current_time = time.time()
        if current_time - cls._last_cleanup_time > cls._cleanup_interval:
            # Don't block the current operation, schedule cleanup
            try:
                cls._schedule_loop_cleanup()
                cls._last_cleanup_time = current_time
            except Exception as e:
                logger.warning(f"Failed to schedule loop cleanup: {e}")
        
        # First check thread-local storage
        current_thread_id = threading.get_ident()
        existing_loop = cls._loop_storage.get_loop()
        
        if existing_loop is not None:
            # Thread already has a loop, verify it's not closed
            if not existing_loop.is_closed():
                return existing_loop
            else:
                logger.warning(f"Found closed loop in thread {current_thread_id}, will create new one")
                # Continue to create a new one
            
        try:
            # Try to get the running loop
            loop = asyncio.get_running_loop()
            # Store in thread-local storage
            if not loop.is_closed():
                cls._loop_storage.set_loop(loop)
                
                # Initialize primary loop if needed
                if not cls._initialized:
                    with cls._instance_lock:
                        if not cls._initialized:  # Double-check inside lock
                            cls._primary_loop = loop
                            cls._primary_thread_id = current_thread_id
                            cls._initialized = True
                            logger.debug(f"EventLoopManager initialized with primary loop {id(loop)} on thread {current_thread_id}")
                
                return loop
            else:
                logger.warning(f"Found closed running loop in thread {current_thread_id}, will create new one")
                # Continue to create a new one
                
        except RuntimeError:
            # No running loop, create a new one
            pass  # Fall through to loop creation
            
        # Create new loop - critical section for primary loop setting
        with cls._instance_lock:
            if cls._primary_loop is None:
                # First time creating a loop, this will be the primary
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                cls._loop_storage.set_loop(loop)
                cls._primary_loop = loop
                cls._primary_thread_id = current_thread_id
                cls._initialized = True
                logger.debug(f"Created new event loop {id(loop)} as primary loop on thread {current_thread_id}")
            else:
                # Create a thread-local loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                cls._loop_storage.set_loop(loop)
                logger.debug(f"Created thread-local event loop {id(loop)} on thread {current_thread_id}")
                
            return loop
    
    @classmethod
    def ensure_event_loop(cls):
        """Ensure the current thread has a valid event loop, creating one if needed."""
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
    def _schedule_loop_cleanup(cls):
        """Schedule cleanup of stale loops without blocking the current operation"""
        # Only cleanup if not already shutting down
        if cls._shutdown_in_progress:
            return
            
        try:
            # Try to get current loop to schedule cleanup
            if cls._primary_loop and not cls._primary_loop.is_closed():
                primary_loop = cls._primary_loop
                
                # Create a task to run cleanup
                primary_loop.call_soon_threadsafe(
                    lambda: primary_loop.create_task(cls._cleanup_stale_loops())
                )
                logger.debug("Scheduled loop cleanup task")
            else:
                # No primary loop or it's closed, try current thread's loop
                try:
                    loop = asyncio.get_running_loop()
                    if not loop.is_closed():
                        loop.create_task(cls._cleanup_stale_loops())
                        logger.debug("Scheduled loop cleanup in current thread")
                except RuntimeError:
                    # No running loop, can't schedule cleanup now
                    logger.debug("Couldn't schedule loop cleanup - no running loop")
                    pass
        except Exception as e:
            logger.warning(f"Error scheduling loop cleanup: {e}")
    
    @classmethod
    async def _cleanup_stale_loops(cls):
        """Clean up stale event loops"""
        try:
            if cls._loop_storage:
                # Get stats before cleanup
                before_stats = cls._loop_storage.get_loop_stats()
                
                # Perform cleanup
                stale_loops = cls._loop_storage.cleanup_stale_loops(
                    max_age_seconds=cls._max_loop_age_seconds
                )
                
                # Get stats after cleanup
                after_stats = cls._loop_storage.get_loop_stats()
                
                if stale_loops:
                    logger.info(f"Cleaned up {len(stale_loops)} stale event loops, " +
                                f"before: {before_stats['total_loops']}, " +
                                f"after: {after_stats['total_loops']}")
        except Exception as e:
            logger.error(f"Error during loop cleanup: {e}")
    
    @classmethod
    def run_coroutine_threadsafe(cls, coro, target_loop=None):
        """Run a coroutine in a specific event loop, even from a different thread with enhanced reliability.
        
        Args:
            coro: The coroutine to run
            target_loop: The target event loop (defaults to primary loop)
            
        Returns:
            concurrent.futures.Future: A future that will contain the result
            
        Raises:
            RuntimeError: If no suitable loop is available
        """
        if target_loop is None:
            # Use primary loop as default target with validation
            if cls._primary_loop is None:
                raise RuntimeError("No primary event loop available")
                
            # Verify primary loop is still valid
            if cls._primary_loop.is_closed():
                logger.warning("Primary loop is closed, attempting to find another suitable loop")
                # Try to find another loop
                all_loops = cls._loop_storage.list_all_loops()
                for loop_info in all_loops:
                    loop, _, _ = loop_info
                    if not loop.is_closed():
                        target_loop = loop
                        break
                        
                if target_loop is None:
                    # Still no valid loop, create a new one
                    logger.warning("No valid loops found, creating a new one for threadsafe execution")
                    target_loop = asyncio.new_event_loop()
                    # Run loop in a new thread
                    thread = threading.Thread(target=cls._run_loop_in_thread, args=(target_loop,))
                    thread.daemon = True
                    thread.start()
            else:
                target_loop = cls._primary_loop
        
        # Verify target loop is valid
        if target_loop.is_closed():
            raise RuntimeError("Target loop is closed")
        
        current_thread = threading.get_ident()
        target_thread = cls._loop_storage.get_thread_for_loop(id(target_loop))
        
        if target_thread == current_thread:
            # Same thread, create a task directly with error handling
            try:
                return asyncio.create_task(coro)
            except RuntimeError as e:
                if "no current event loop" in str(e).lower():
                    # No current event loop, try another approach
                    asyncio.set_event_loop(target_loop)
                    return asyncio.create_task(coro)
                else:
                    raise
        else:
            # Different thread, use threadsafe call with retry
            try:
                return asyncio.run_coroutine_threadsafe(coro, target_loop)
            except RuntimeError as e:
                if "loop is closed" in str(e).lower():
                    # Loop was closed, create a new one
                    logger.warning(f"Loop closed during run_coroutine_threadsafe, creating new loop")
                    new_loop = asyncio.new_event_loop()
                    # Run loop in a new thread
                    thread = threading.Thread(target=cls._run_loop_in_thread, args=(new_loop,))
                    thread.daemon = True
                    thread.start()
                    # Try again with new loop
                    return asyncio.run_coroutine_threadsafe(coro, new_loop)
                else:
                    raise
    
    @classmethod
    def _run_loop_in_thread(cls, loop):
        """Run an event loop in the current thread"""
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
        """Register a resource with the event loop manager for proper cleanup with enhanced metadata"""
        if not hasattr(resource, '_creation_loop_id'):
            # Get the current event loop for this resource
            try:
                loop = cls.get_event_loop()
                resource._creation_loop_id = id(loop)
                resource._loop_thread_id = threading.get_ident()
                resource._creation_time = time.time()
                resource._resource_id = resource_id  # Store ID for better debugging
            except Exception as e:
                logger.warning(f"Could not record loop context for resource {resource_id}: {e}")
                resource._creation_loop_id = None
                resource._loop_thread_id = threading.get_ident()
                resource._creation_time = time.time()
        
        # Thread-safe registry update
        with cls._instance_lock:
            cls._resource_registry[resource_id] = resource
            
        logger.debug(f"Registered resource {resource_id} with event loop manager")
    
    @classmethod
    def unregister_resource(cls, resource_id):
        """Unregister a resource from the event loop manager with thread safety"""
        # Thread-safe registry update
        with cls._instance_lock:
            if resource_id in cls._resource_registry:
                del cls._resource_registry[resource_id]
                logger.debug(f"Unregistered resource {resource_id} from event loop manager")
    
    @classmethod
    async def validate_loop_for_resource(cls, resource_id):
        """Validate that the resource is using the correct event loop with enhanced verification"""
        # Thread-safe registry access
        with cls._instance_lock:
            # If resource not registered, consider it valid
            if resource_id not in cls._resource_registry:
                return True
            
            resource = cls._resource_registry[resource_id]
        
        # Check if resource has loop context attributes
        if hasattr(resource, '_creation_loop_id') and hasattr(resource, '_loop_thread_id'):
            try:
                current_loop = asyncio.get_running_loop()
                current_thread = threading.get_ident()
                
                # Verify if creation loop is still open
                creation_loop_closed = False
                try:
                    # Find the creation loop in registry
                    loop_info = cls._loop_storage.list_all_loops()
                    for loop, thread_id, _ in loop_info:
                        if id(loop) == resource._creation_loop_id:
                            creation_loop_closed = loop.is_closed()
                            break
                except Exception:
                    # Couldn't verify, assume it might be closed
                    creation_loop_closed = True
                
                # Check for mismatch
                if ((id(current_loop) != resource._creation_loop_id or 
                     current_thread != resource._loop_thread_id) and
                    not creation_loop_closed):
                    logger.warning(
                        f"Loop mismatch for resource {resource_id}: "
                        f"Current={id(current_loop)}/{current_thread}, "
                        f"Resource={resource._creation_loop_id}/{resource._loop_thread_id}"
                    )
                    return False
                
                # If creation loop is closed, consider current loop valid
                if creation_loop_closed:
                    logger.info(f"Creation loop for resource {resource_id} is closed, " +
                                f"updating to current loop {id(current_loop)}")
                    resource._creation_loop_id = id(current_loop)
                    resource._loop_thread_id = current_thread
                    return True
                    
            except RuntimeError:
                # No running loop, can't validate
                return False
        
        return True
    
    @classmethod
    async def submit_to_resource_loop(cls, resource_id, coro):
        """Submit a coroutine to the loop where a resource was created with enhanced reliability
        
        This method will:
        1. Check if the resource exists and has loop context
        2. Verify the target loop is still valid
        3. Submit the coroutine to the appropriate loop
        4. Handle loop failures gracefully
        
        Args:
            resource_id: The ID of the resource to submit the coroutine to
            coro: The coroutine to run
            
        Returns:
            The result of the coroutine
        """
        # Thread-safe registry access
        with cls._instance_lock:
            if resource_id not in cls._resource_registry:
                # Resource not found, run in current loop
                return await coro
            
            resource = cls._resource_registry[resource_id]
        
        # If resource doesn't have loop context, run in current loop
        if not hasattr(resource, '_creation_loop_id') or not hasattr(resource, '_loop_thread_id'):
            return await coro
            
        try:
            # Get current loop context
            try:
                current_loop = asyncio.get_running_loop()
                current_thread = threading.get_ident()
            except RuntimeError:
                # No running loop, ensure one exists
                current_loop = cls.ensure_event_loop()
                current_thread = threading.get_ident()
            
            # If already in the correct loop/thread, run directly
            if id(current_loop) == resource._creation_loop_id and current_thread == resource._loop_thread_id:
                return await coro
                
            # Find the target loop
            target_thread = resource._loop_thread_id
            target_loop_id = resource._creation_loop_id
            target_loop = None
            target_loop_closed = True
            
            # Find the target loop in the registry
            loop_list = cls._loop_storage.list_all_loops()
            for loop, thread_id, _ in loop_list:
                if id(loop) == target_loop_id:
                    target_loop = loop
                    target_loop_closed = loop.is_closed()
                    break
            
            # If target loop not found or closed, update resource to use current loop
            if target_loop is None or target_loop_closed:
                logger.warning(f"Target loop for resource {resource_id} not found or closed, updating to current loop")
                resource._creation_loop_id = id(current_loop)
                resource._loop_thread_id = current_thread
                # Run in current loop
                return await coro
            
            # Submit to the target loop with timeout protection
            try:
                future = asyncio.run_coroutine_threadsafe(coro, target_loop)
                # Wrap with a reasonable timeout for safety
                return await asyncio.wait_for(asyncio.wrap_future(future), timeout=30.0)
            except (asyncio.TimeoutError, concurrent.futures.TimeoutError) as e:
                logger.error(f"Timeout submitting to loop for resource {resource_id}")
                # Update resource to use current loop and retry
                resource._creation_loop_id = id(current_loop)
                resource._loop_thread_id = current_thread
                return await coro
            except RuntimeError as e:
                if "loop is closed" in str(e).lower():
                    logger.warning(f"Loop closed when submitting to resource {resource_id}, updating to current loop")
                    # Update resource to use current loop and retry
                    resource._creation_loop_id = id(current_loop)
                    resource._loop_thread_id = current_thread
                    return await coro
                else:
                    raise
                
        except Exception as e:
            logger.error(f"Error submitting to resource loop: {e}")
            # Always ensure we run the coroutine
            return await coro
    
    @classmethod
    async def cleanup_resources(cls):
        """Clean up all registered resources with orderly shutdown"""
        # Set shutdown flag
        cls._shutdown_in_progress = True
        logger.info("Beginning orderly shutdown of resources")
        
        # Make a copy of the keys since we'll be modifying the dict
        with cls._instance_lock:
            resource_ids = list(cls._resource_registry.keys())
        
        # Group resources by type for ordered shutdown
        resource_groups = {
            'event_queue': [],
            'manager': [],
            'monitor': [],
            'other': []
        }
        
        # Classify resources for ordered shutdown
        for resource_id in resource_ids:
            with cls._instance_lock:
                if resource_id not in cls._resource_registry:
                    continue
                resource = cls._resource_registry[resource_id]
            
            # Classify based on resource type or name pattern
            if resource_id.startswith('event_queue'):
                resource_groups['event_queue'].append((resource_id, resource))
            elif any(m in resource_id for m in ['manager', 'cache', 'context']):
                resource_groups['manager'].append((resource_id, resource))
            elif any(m in resource_id for m in ['monitor', 'tracker']):
                resource_groups['monitor'].append((resource_id, resource))
            else:
                resource_groups['other'].append((resource_id, resource))
        
        # Order matters for clean shutdown: other → monitors → managers → event queues
        shutdown_order = ['other', 'monitor', 'manager', 'event_queue']
        
        for group in shutdown_order:
            resources = resource_groups[group]
            logger.info(f"Shutting down {len(resources)} resources in group '{group}'")
            
            for resource_id, resource in resources:
                try:
                    # If resource has a specific loop, submit the stop to that loop
                    if hasattr(resource, '_creation_loop_id') and hasattr(resource, '_loop_thread_id'):
                        try:
                            # Check if the resource's loop is still valid
                            loop_valid = False
                            try:
                                loop_info = cls._loop_storage.list_all_loops()
                                for loop, thread_id, _ in loop_info:
                                    if id(loop) == resource._creation_loop_id and not loop.is_closed():
                                        loop_valid = True
                                        break
                            except Exception:
                                loop_valid = False
                            
                            if loop_valid:
                                # Submit to the resource's loop with timeout
                                future = cls.run_coroutine_threadsafe(
                                    cls._stop_resource(resource), 
                                    # Find the actual loop object
                                    next(loop for loop, _, _ in loop_info if id(loop) == resource._creation_loop_id)
                                )
                                # Wait for result with timeout
                                try:
                                    result = await asyncio.wait_for(asyncio.wrap_future(future), timeout=5.0)
                                    logger.debug(f"Resource {resource_id} stopped in its own loop")
                                except (asyncio.TimeoutError, concurrent.futures.TimeoutError):
                                    logger.warning(f"Timeout stopping resource {resource_id} in its loop, trying direct stop")
                                    await cls._stop_resource(resource)
                            else:
                                # Loop invalid, do direct stop
                                logger.info(f"Loop for resource {resource_id} is invalid, using direct stop")
                                await cls._stop_resource(resource)
                                
                        except Exception as e:
                            logger.error(f"Error stopping resource {resource_id} in its loop: {str(e)}")
                            # Fallback to direct stop
                            await cls._stop_resource(resource)
                    else:
                        # Direct stop
                        await cls._stop_resource(resource)
                    
                    # Unregister resource
                    cls.unregister_resource(resource_id)
                    logger.debug(f"Resource {resource_id} successfully cleaned up")
                    
                except Exception as e:
                    logger.error(f"Error cleaning up resource {resource_id}: {str(e)}")
        
        # Clean up all remaining resources
        with cls._instance_lock:
            remaining = list(cls._resource_registry.keys())
            cls._resource_registry.clear()
            
        if remaining:
            logger.warning(f"Some resources were not properly cleaned up: {remaining}")
            
        # Clean up loops
        try:
            if cls._loop_storage:
                # Force cleanup of all loops
                stale_loops = cls._loop_storage.cleanup_stale_loops(max_age_seconds=0)
                logger.info(f"Cleaned up {len(stale_loops)} event loops during shutdown")
        except Exception as e:
            logger.error(f"Error cleaning up event loops: {e}")
            
        # Reset shutdown flag
        cls._shutdown_in_progress = False
        logger.info("Resource cleanup completed")
    
    @classmethod
    async def _stop_resource(cls, resource):
        """Stop a resource with proper handling for different resource types and improved error handling"""
        try:
            # Different resource types might have different stop methods
            if hasattr(resource, 'stop') and callable(resource.stop):
                # Check if it's a coroutine function
                if asyncio.iscoroutinefunction(resource.stop):
                    # Use timeout to avoid hanging
                    try:
                        await asyncio.wait_for(resource.stop(), timeout=5.0)
                    except asyncio.TimeoutError:
                        logger.warning(f"Timeout stopping resource {resource}, continuing")
                else:
                    # Synchronous stop
                    resource.stop()
                    
            # Special case for closing
            elif hasattr(resource, 'close') and callable(resource.close):
                if asyncio.iscoroutinefunction(resource.close):
                    try:
                        await asyncio.wait_for(resource.close(), timeout=5.0)
                    except asyncio.TimeoutError:
                        logger.warning(f"Timeout closing resource {resource}, continuing")
                else:
                    resource.close()
                
            # Special case for shutdown
            elif hasattr(resource, 'shutdown') and callable(resource.shutdown):
                if asyncio.iscoroutinefunction(resource.shutdown):
                    try:
                        await asyncio.wait_for(resource.shutdown(), timeout=5.0)
                    except asyncio.TimeoutError:
                        logger.warning(f"Timeout shutting down resource {resource}, continuing")
                else:
                    resource.shutdown()
                    
            return True
            
        except Exception as e:
            logger.error(f"Error stopping resource: {str(e)}")
            return False
            
    @classmethod
    def get_stats(cls):
        """Get statistics about event loops and resources"""
        with cls._instance_lock:
            stats = {
                "initialized": cls._initialized,
                "primary_loop_id": id(cls._primary_loop) if cls._primary_loop else None,
                "primary_thread_id": cls._primary_thread_id,
                "resource_count": len(cls._resource_registry),
                "shutdown_in_progress": cls._shutdown_in_progress,
                "last_cleanup_time": cls._last_cleanup_time
            }
            
            # Add loop storage stats
            if cls._loop_storage:
                stats["loops"] = cls._loop_storage.get_loop_stats()
                
            # Add resource type counts
            resource_types = {}
            for resource_id in cls._resource_registry:
                # Extract resource type from ID (e.g., "event_queue_123" -> "event_queue")
                parts = resource_id.split('_')
                if len(parts) > 1:
                    resource_type = parts[0]
                    resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
                else:
                    resource_types["unknown"] = resource_types.get("unknown", 0) + 1
                    
            stats["resource_types"] = resource_types
            
            return stats