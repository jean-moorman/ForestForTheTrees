from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import random
import sys
import threading
import time
from typing import Dict, Any, Set, Optional, List, Callable, Awaitable, Tuple
import asyncio
import logging

import concurrent
from .common import ResourceType, HealthStatus
from .errors import ResourceError, ResourceOperationError, ErrorSeverity

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

class ResourceEventTypes(Enum):
    """Unified event types for resource management"""
    # Core state events
    INTERFACE_STATE_CHANGED = "interface_state_changed"
    RESOURCE_STATE_CHANGED = "resource_state_changed"
    AGENT_CONTEXT_UPDATED = "agent_context_updated"
    
    # Validation and metrics
    VALIDATION_COMPLETED = "validation_completed"
    METRIC_RECORDED = "metric_recorded"
    MONITORING_ERROR_OCCURRED = "monitoring_error_occurred"
    
    # Resource events
    CACHE_UPDATED = "cache_updated"
    ERROR_OCCURRED = "error_occurred"
    
    # Health and monitoring
    SYSTEM_HEALTH_CHANGED = "system_health_changed"
    RESOURCE_HEALTH_CHANGED = "resource_health_changed"
    RESOURCE_METRIC_RECORDED = "resource_metric_recorded"
    RESOURCE_ALERT_CREATED = "resource_alert_created"
    RESOURCE_ALERT_UPDATED = "resource_alert_updated"
    # System alerts
    SYSTEM_ALERT = "system_alert"

    # Error-specific events
    RESOURCE_CLEANUP = "resource_cleanup"
    RESOURCE_ERROR_OCCURRED = "resource_error_occurred"
    RESOURCE_ERROR_RESOLVED = "resource_error_resolved"
    RESOURCE_ERROR_RECOVERY_STARTED = "resource_error_recovery_started"
    RESOURCE_ERROR_RECOVERY_COMPLETED = "resource_error_recovery_completed"

@dataclass
class Event:
    """Represents a single event in the system"""
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    resource_type: Optional[ResourceType] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"  # One of "high", "normal", "low"

class EventQueue:
    """Async event queue with persistence, reliability and priority"""
    def __init__(self, max_size: int = 1000, queue_id: Optional[str] = None):
        self._max_size = max_size
        self._queue = None  # Legacy queue - kept for backward compatibility
        self._high_priority_queue = None  # Lazy initialization
        self._normal_priority_queue = None  # Lazy initialization
        self._low_priority_queue = None  # Lazy initialization
        self._queue_lock = threading.RLock()  # Add a lock for queue operations
        self._subscribers: Dict[str, Set[Tuple[Callable[[str, Dict[str, Any]], Awaitable[None]], Optional[asyncio.AbstractEventLoop], Optional[int]]]] = {}
        self._event_history: List[Event] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._processing_retries: Dict[str, int] = {}
        self._max_retries = 3
        self._retry_delay = 1.0  # seconds
        self._creation_loop_id = None  # Store the ID of the loop that creates the queue
        self._loop_thread_id = None  # Store the thread ID where the queue was created
        self._id = queue_id or f"event_queue_{id(self)}"
    
        # Use centralized event loop manager
        try:
            current_loop = EventLoopManager.get_event_loop()
            self._creation_loop_id = id(current_loop)
            self._loop_thread_id = threading.get_ident()
            
            # Register with event loop manager for cleanup
            EventLoopManager.register_resource(self._id, self)
            
            logger.debug(f"EventQueue {self._id} created in loop {self._creation_loop_id} on thread {self._loop_thread_id}")
        except Exception as e:
            logger.warning(f"Error during EventQueue initialization: {str(e)}")
            self._creation_loop_id = None
            self._loop_thread_id = threading.get_ident()

    @property
    def queue(self):
        """Legacy queue property - redirects to normal_priority_queue"""
        return self.normal_priority_queue
        
    @property
    def high_priority_queue(self):
        """Lazy initialization of high priority queue"""
        if self._high_priority_queue is None:
            try:
                # Use the centralized event loop manager
                current_loop = EventLoopManager.get_event_loop()
                # High priority queue is smaller to ensure faster processing
                self._high_priority_queue = asyncio.Queue(maxsize=max(10, self._max_size // 10))
                if not hasattr(self, '_creation_loop_id') or self._creation_loop_id is None:
                    self._creation_loop_id = id(current_loop)
                    self._loop_thread_id = threading.get_ident()
                logger.debug(f"High priority queue initialized in loop {self._creation_loop_id}")
            except Exception as e:
                logger.error(f"Cannot create high priority queue: {str(e)}")
                raise RuntimeError(f"Cannot create high priority queue: {str(e)}")
        return self._high_priority_queue
        
    @property
    def normal_priority_queue(self):
        """Lazy initialization of normal priority queue"""
        if self._normal_priority_queue is None:
            try:
                # Use the centralized event loop manager
                current_loop = EventLoopManager.get_event_loop()
                self._normal_priority_queue = asyncio.Queue(maxsize=self._max_size)
                if not hasattr(self, '_creation_loop_id') or self._creation_loop_id is None:
                    self._creation_loop_id = id(current_loop)
                    self._loop_thread_id = threading.get_ident()
                # For backward compatibility
                self._queue = self._normal_priority_queue
                logger.debug(f"Normal priority queue initialized in loop {self._creation_loop_id}")
            except Exception as e:
                logger.error(f"Cannot create normal priority queue: {str(e)}")
                raise RuntimeError(f"Cannot create normal priority queue: {str(e)}")
        return self._normal_priority_queue
        
    @property
    def low_priority_queue(self):
        """Lazy initialization of low priority queue"""
        if self._low_priority_queue is None:
            try:
                # Use the centralized event loop manager
                current_loop = EventLoopManager.get_event_loop()
                # Low priority queue can be larger
                self._low_priority_queue = asyncio.Queue(maxsize=self._max_size * 2)
                if not hasattr(self, '_creation_loop_id') or self._creation_loop_id is None:
                    self._creation_loop_id = id(current_loop)
                    self._loop_thread_id = threading.get_ident()
                logger.debug(f"Low priority queue initialized in loop {self._creation_loop_id}")
            except Exception as e:
                logger.error(f"Cannot create low priority queue: {str(e)}")
                raise RuntimeError(f"Cannot create low priority queue: {str(e)}")
        return self._low_priority_queue

    async def _ensure_correct_loop(self):
        """Ensure we're running in the correct event loop or handle mismatch"""
        if self._queue is None:
            return  # Queue not created yet, no issue
            
        try:
            # Use the centralized event loop manager
            current_loop = EventLoopManager.get_event_loop()
            current_thread = threading.get_ident()
            
            # Check if we're in the correct loop
            if current_thread != self._loop_thread_id or id(current_loop) != self._creation_loop_id:
                logger.warning(f"Event queue {self._id} access from different context. "
                               f"Created in loop {self._creation_loop_id} on thread {self._loop_thread_id}, "
                               f"accessed from loop {id(current_loop)} on thread {current_thread}")
                
                # Use EventLoopManager to validate
                is_valid = await EventLoopManager.validate_loop_for_resource(self._id)
                if not is_valid:
                    logger.error(f"Event queue {self._id} used in incorrect loop context")
                    
                    # Here we could implement safe event transfer, but for now just warn
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error during loop validation: {str(e)}")
            return False
    
    async def emit(self, event_type: str, data: Dict[str, Any], 
               correlation_id: Optional[str] = None, 
               priority: str = "normal") -> bool:
        """Emit event with back-pressure support and priority
        
        Args:
            event_type: The type of event to emit
            data: The event data
            correlation_id: Optional correlation ID for tracking related events
            priority: Event priority - "high", "normal", or "low"
            
        Returns:
            bool: True if event was queued, False if rejected due to back-pressure
        """
        # Convert enum if needed
        event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
        
        # Create event object with priority
        import uuid
        event = Event(
            event_type=event_type_str,
            data=data,
            correlation_id=correlation_id,
            priority=priority,
            # Add an event_id field if it doesn't exist already in Event class
            metadata={"event_id": str(uuid.uuid4())}
        )
        
        # Use EventLoopManager to ensure we're in the right loop context
        try:
            # Submit the actual emission to the creation loop of this queue
            return await EventLoopManager.submit_to_resource_loop(self._id, self._emit_internal(event))
        except Exception as e:
            logger.error(f"Failed to emit event {event_type_str}: {e}")
            # In case of critical events, try direct emission
            if event_type_str in [
                ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
                ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                ResourceEventTypes.SYSTEM_ALERT.value
            ]:
                logger.warning(f"Critical event {event_type_str}, attempting direct emission")
                return await self._emit_internal(event)
            return False
    
    async def _emit_internal(self, event: Event) -> bool:
        """Internal implementation of emit that runs in creation loop with enhanced back-pressure"""
        # Initialize queue saturation attributes if not present
        if not hasattr(self, '_queue_saturation_metrics'):
            self._queue_saturation_metrics = {
                'high': 0.0,
                'normal': 0.0,
                'low': 0.0,
                'last_saturation_check': 0,
                'saturation_window': [],  # Track saturation over time for adaptive throttling
                'rejected_events': {}, # Track rejected events by type
                'prioritized_events': set([  # Events that should maintain their priority
                    ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
                    ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value, 
                    ResourceEventTypes.SYSTEM_ALERT.value,
                    ResourceEventTypes.RESOURCE_ERROR_RECOVERY_STARTED.value,
                    ResourceEventTypes.RESOURCE_ERROR_RECOVERY_COMPLETED.value,
                    ResourceEventTypes.RESOURCE_ERROR_RESOLVED.value
                ])
            }
            
        # Add rate limiting for event types if not present
        if not hasattr(self, '_event_rate_limits'):
            self._event_rate_limits = {}  # Maps event_type -> {last_emission, tokens, rate}
        
        # Manage history with size limit
        self._event_history.append(event)
        if len(self._event_history) > 10000:
            self._event_history = self._event_history[-10000:]
            
        # Apply rate limiting per event type
        if event.event_type not in self._event_rate_limits:
            # Initialize rate limiting for this event type
            self._event_rate_limits[event.event_type] = {
                'tokens': 10.0,  # Initial token bucket
                'last_refill': time.time(),
                'rate': 10.0,  # Tokens per second allowed
                'max_tokens': 10.0,
                'emissions': []  # Track recent emissions
            }
        
        # Apply token bucket rate limiting
        if event.event_type not in self._queue_saturation_metrics['prioritized_events']:
            rate_limit = self._event_rate_limits[event.event_type]
            now = time.time()
            
            # Refill tokens based on time elapsed
            time_elapsed = now - rate_limit['last_refill']
            new_tokens = time_elapsed * rate_limit['rate']
            rate_limit['tokens'] = min(rate_limit['tokens'] + new_tokens, rate_limit['max_tokens'])
            rate_limit['last_refill'] = now
            
            # Check if we have tokens for this event
            tokens_needed = 1.0
            if event.priority == "high":
                tokens_needed = 0.5  # High priority uses fewer tokens
            elif event.priority == "low":
                tokens_needed = 1.5  # Low priority uses more tokens
                
            # Apply rate limiting unless this is a critical event
            if rate_limit['tokens'] < tokens_needed:
                # Not enough tokens, reject event
                # Track rejection for metrics
                self._queue_saturation_metrics['rejected_events'][event.event_type] = \
                    self._queue_saturation_metrics['rejected_events'].get(event.event_type, 0) + 1
                
                logger.debug(f"Rate limiting rejected {event.event_type} event (tokens={rate_limit['tokens']:.2f})")
                return False
            
            # Consume tokens
            rate_limit['tokens'] -= tokens_needed
            
            # Record emission for frequency tracking
            rate_limit['emissions'].append(now)
            if len(rate_limit['emissions']) > 100:
                rate_limit['emissions'] = rate_limit['emissions'][-100:]
                
            # Dynamically adjust rate limit based on event frequency
            if len(rate_limit['emissions']) >= 10:
                recent_emissions = rate_limit['emissions'][-10:]
                if len(recent_emissions) >= 2:
                    time_span = recent_emissions[-1] - recent_emissions[0]
                    if time_span > 0:
                        frequency = len(recent_emissions) / time_span
                        
                        # Adjust token rate based on observed frequency
                        if frequency > rate_limit['rate'] * 1.5:
                            # Event is being emitted much faster than rate limit
                            new_rate = min(frequency * 1.2, rate_limit['rate'] * 2)
                            rate_limit['rate'] = new_rate
                            rate_limit['max_tokens'] = max(10.0, new_rate)
                        elif frequency < rate_limit['rate'] * 0.5:
                            # Event is being emitted much slower than rate limit
                            rate_limit['rate'] = max(1.0, rate_limit['rate'] * 0.9)
        
        # Select queue based on priority
        if event.priority == "high":
            target_queue = self.high_priority_queue
        elif event.priority == "low":
            target_queue = self.low_priority_queue
        else:
            target_queue = self.normal_priority_queue
        
        # Check current queue saturation levels and update metrics
        now = time.time()
        if now - self._queue_saturation_metrics['last_saturation_check'] >= 1.0:
            try:
                # Update queue saturation metrics
                high_size = self.high_priority_queue.qsize()
                high_capacity = self.high_priority_queue.maxsize
                high_saturation = high_size / high_capacity if high_capacity > 0 else 0
                
                normal_size = self.normal_priority_queue.qsize()
                normal_capacity = self.normal_priority_queue.maxsize
                normal_saturation = normal_size / normal_capacity if normal_capacity > 0 else 0
                
                low_size = self.low_priority_queue.qsize()
                low_capacity = self.low_priority_queue.maxsize
                low_saturation = low_size / low_capacity if low_capacity > 0 else 0
                
                # Update metrics
                self._queue_saturation_metrics['high'] = high_saturation
                self._queue_saturation_metrics['normal'] = normal_saturation
                self._queue_saturation_metrics['low'] = low_saturation
                self._queue_saturation_metrics['last_saturation_check'] = now
                
                # Track saturation window for trending
                saturation_entry = (now, high_saturation, normal_saturation, low_saturation)
                self._queue_saturation_metrics['saturation_window'].append(saturation_entry)
                if len(self._queue_saturation_metrics['saturation_window']) > 10:
                    self._queue_saturation_metrics['saturation_window'] = self._queue_saturation_metrics['saturation_window'][-10:]
                
                # Log warning level on high saturation
                if high_saturation >= 0.9:
                    logger.warning(f"High priority queue saturation critical at {high_saturation:.1%}")
                if normal_saturation >= 0.9:
                    logger.warning(f"Normal priority queue saturation critical at {normal_saturation:.1%}")
                    
            except (NotImplementedError, Exception) as e:
                # Some queue implementations don't support qsize()
                logger.debug(f"Error checking queue saturation: {e}")
                
        # Get current saturation metrics
        high_saturation = self._queue_saturation_metrics['high']
        normal_saturation = self._queue_saturation_metrics['normal']
        low_saturation = self._queue_saturation_metrics['low']
        
        # Determine overall system saturation level
        system_saturation = max(high_saturation, normal_saturation)
        
        # Enhanced back-pressure strategy based on system saturation and priority
        if system_saturation >= 0.95:  # Critical saturation - system-wide issue
            # For non-priority events, reject firmly
            if event.priority != "high" and event.event_type not in self._queue_saturation_metrics['prioritized_events']:
                # Track rejection for metrics
                self._queue_saturation_metrics['rejected_events'][event.event_type] = \
                    self._queue_saturation_metrics['rejected_events'].get(event.event_type, 0) + 1
                    
                logger.warning(f"System critical saturation ({system_saturation:.1%}), rejecting {event.event_type} event")
                return False
            elif event.priority == "normal" and event.event_type in self._queue_saturation_metrics['prioritized_events']:
                # Prioritized events get upgraded during critical saturation
                event.priority = "high"
                target_queue = self.high_priority_queue
                logger.info(f"Upgrading critical event {event.event_type} to high priority during saturation")
                
        elif system_saturation >= 0.85:  # Severe saturation
            # Apply priority adjustments based on event type and target queue saturation
            
            # Low priority events get rejected if low queue is saturated
            if event.priority == "low" and low_saturation >= 0.9:
                if event.event_type not in self._queue_saturation_metrics['prioritized_events']:
                    # Track rejection for metrics
                    self._queue_saturation_metrics['rejected_events'][event.event_type] = \
                        self._queue_saturation_metrics['rejected_events'].get(event.event_type, 0) + 1
                        
                    logger.warning(f"Low priority queue saturated ({low_saturation:.1%}), rejecting {event.event_type} event")
                    return False
                else:
                    # Critical events move to normal priority instead of rejection
                    event.priority = "normal"
                    target_queue = self.normal_priority_queue
            
            # Normal priority events get downgraded to low if not critical
            elif event.priority == "normal" and normal_saturation >= 0.9:
                if event.event_type not in self._queue_saturation_metrics['prioritized_events']:
                    event.priority = "low"
                    target_queue = self.low_priority_queue
                    logger.info(f"Downgrading {event.event_type} to low priority due to queue saturation")
                    
                    # If low queue is also saturated, reject
                    if low_saturation >= 0.95:
                        # Track rejection for metrics
                        self._queue_saturation_metrics['rejected_events'][event.event_type] = \
                            self._queue_saturation_metrics['rejected_events'].get(event.event_type, 0) + 1
                            
                        logger.warning(f"Both normal and low queues saturated, rejecting {event.event_type} event")
                        return False
        
        elif system_saturation >= 0.75:  # Warning saturation level
            # Mild back-pressure strategies
            if event.priority == "normal" and event.event_type not in self._queue_saturation_metrics['prioritized_events']:
                # Check if we're increasing in saturation (trending up)
                trending_up = False
                if len(self._queue_saturation_metrics['saturation_window']) >= 2:
                    prev_normal_saturation = self._queue_saturation_metrics['saturation_window'][-2][2]
                    if normal_saturation > prev_normal_saturation + 0.05:  # 5% increase
                        trending_up = True
                
                # Apply back-pressure if saturation is trending up
                if trending_up and low_saturation < 0.8:
                    # Only downgrade if low priority queue has capacity
                    event.priority = "low"
                    target_queue = self.low_priority_queue
                    logger.debug(f"Preemptively downgrading {event.event_type} due to rising saturation")
                
        # Final safety check before putting in queue
        try:
            target_saturation = 0.0
            if target_queue is self.high_priority_queue:
                target_saturation = high_saturation
            elif target_queue is self.normal_priority_queue:
                target_saturation = normal_saturation
            else:
                target_saturation = low_saturation
                
            # One final check with the actual target queue
            if target_saturation >= 0.99 and event.event_type not in self._queue_saturation_metrics['prioritized_events']:
                # Absolute last resort - reject if queue is virtually full
                # Track rejection for metrics
                self._queue_saturation_metrics['rejected_events'][event.event_type] = \
                    self._queue_saturation_metrics['rejected_events'].get(event.event_type, 0) + 1
                    
                logger.warning(f"Target queue completely saturated ({target_saturation:.1%}), rejecting {event.event_type}")
                return False
            
            # Put in queue - we should already be in the correct loop context
            await target_queue.put(event)
            logger.debug(f"Emitted {event.priority} priority event {event.event_type} to queue {self._id}")
            return True
        except Exception as e:
            logger.error(f"Failed to emit event {event.event_type}: {e}")
            return False

    def get_nowait(self):
        """Non-blocking get from the event queue with event loop safety."""
        try:
            # Check if we're in the right loop using EventLoopManager
            try:
                current_loop = EventLoopManager.get_event_loop()
                current_thread = threading.get_ident()
                
                if self._queue is not None and (id(current_loop) != self._creation_loop_id or 
                                            current_thread != self._loop_thread_id):
                    logger.warning(f"Queue.get_nowait for {self._id} from different context. "
                                f"Created in loop {self._creation_loop_id} on thread {self._loop_thread_id}, "
                                f"accessed from loop {id(current_loop)} on thread {current_thread}")
                    
                    # In a non-async context, we can't await validate_loop_for_resource
                    # Instead just log the warning and continue with best effort
            except Exception:
                # This could happen if called from a thread without an event loop
                logger.warning(f"Error checking event loop when calling get_nowait for {self._id}")
            
            # Try to get from the queue
            return self.queue.get_nowait()
            
        except asyncio.QueueEmpty:
            # Propagate QueueEmpty for normal handling
            raise
        except RuntimeError as e:
            if "different event loop" in str(e):
                logger.error(f"Event loop mismatch in get_nowait for {self._id}: {e}")
                
                # Try to recreate the queue in the current context as a last resort
                try:
                    current_loop = EventLoopManager.get_event_loop()
                    self._queue = asyncio.Queue(maxsize=self._max_size)
                    self._creation_loop_id = id(current_loop)
                    self._loop_thread_id = threading.get_ident()
                    logger.warning(f"Recreated queue for {self._id} in current loop context")
                    
                    # Try get_nowait on the new queue, but it's likely empty
                    return self._queue.get_nowait()
                except (asyncio.QueueEmpty, Exception):
                    # Simulate empty queue if recreation fails or new queue is empty
                    raise asyncio.QueueEmpty()
            else:
                # For other RuntimeErrors, log and re-raise
                logger.error(f"RuntimeError in get_nowait for {self._id}: {e}")
                raise

    async def wait_for_processing(self, timeout=5.0):
        """Wait for all currently queued events to be processed."""
        if self._queue is None:
            return True  # Queue not initialized, nothing to wait for
            
        start_time = time.time()
        
        # Wait until the queue is empty or timeout
        while time.time() - start_time < timeout:
            try:
                if self._queue.qsize() == 0:
                    # Add a small delay to allow for any in-progress processing
                    await asyncio.sleep(0.1)
                    if self._queue.qsize() == 0:  # Double check after delay
                        return True
            except NotImplementedError:
                # Some queue implementations don't support qsize()
                await asyncio.sleep(0.1)
            
            await asyncio.sleep(0.05)
        
        return False  # Timed out

    async def _process_events(self):
        """Process events with batching support and priority handling"""
        consecutive_errors = 0
        batch = []
        last_event_type = None
        max_batch_size = 5  # Max events to process in a batch (reduced for testing)
        
        while self._running:
            try:
                # Process high priority queue first - these are never batched for immediate processing
                try:
                    # Use shorter timeout for high priority check to avoid blocking
                    high_priority_event = await asyncio.wait_for(
                        self.high_priority_queue.get(), 
                        timeout=0.1
                    )
                    # Process high priority event immediately
                    await self._process_single_event(high_priority_event)
                    self.high_priority_queue.task_done()
                    consecutive_errors = 0
                    continue  # Continue loop to keep checking high priority first
                except asyncio.TimeoutError:
                    # No high priority events, continue to normal priority
                    pass
                except asyncio.QueueEmpty:
                    # Queue is empty, continue to normal priority
                    pass
                except RuntimeError as e:
                    # Handle loop mismatch for high priority queue
                    if "different event loop" in str(e):
                        with self._queue_lock:
                            self._high_priority_queue = asyncio.Queue(maxsize=max(100, self._max_size // 10))
                        consecutive_errors += 1
                        await asyncio.sleep(min(consecutive_errors * 0.1, 5))
                        continue
                    else:
                        raise
                
                # Check if we need to process the current batch
                if batch and (len(batch) >= max_batch_size or 
                             (last_event_type is not None and batch[0].event_type != last_event_type)):
                    await self._process_event_batch(batch)
                    batch = []
                
                # Try to get event from normal priority queue
                try:
                    # Use shorter timeout to balance responsiveness
                    normal_event = await asyncio.wait_for(
                        self.normal_priority_queue.get(), 
                        timeout=0.2
                    )
                    consecutive_errors = 0
                    
                    # Start or continue a batch
                    if not batch:
                        batch.append(normal_event)
                        last_event_type = normal_event.event_type
                        logger.debug(f"Started new batch with event type {last_event_type}")
                    elif normal_event.event_type == last_event_type and len(batch) < max_batch_size:
                        batch.append(normal_event)
                        logger.debug(f"Added to batch, now size {len(batch)}")
                    else:
                        # Process the existing batch
                        if batch:
                            logger.debug(f"Processing batch of {len(batch)} events of type {batch[0].event_type}")
                            await self._process_event_batch(batch)
                        # Start a new batch
                        batch = [normal_event]
                        last_event_type = normal_event.event_type
                        logger.debug(f"Started new batch with event type {last_event_type}")
                        
                    self.normal_priority_queue.task_done()
                    
                except asyncio.TimeoutError:
                    # Process any pending batch before checking low priority
                    if batch:
                        logger.debug(f"Processing batch of {len(batch)} events of type {batch[0].event_type} after timeout")
                        await self._process_event_batch(batch)
                        batch = []
                        
                    # Only check low priority if normal is empty
                    try:
                        # Use longer timeout for low priority
                        low_event = await asyncio.wait_for(
                            self.low_priority_queue.get(), 
                            timeout=0.5
                        )
                        await self._process_single_event(low_event)
                        self.low_priority_queue.task_done()
                        consecutive_errors = 0
                    except (asyncio.TimeoutError, asyncio.QueueEmpty):
                        # No events in any queue, sleep briefly
                        await asyncio.sleep(0.1)
                        
                except RuntimeError as e:
                    # Handle loop mismatch for normal priority queue
                    if "different event loop" in str(e):
                        with self._queue_lock:
                            self._normal_priority_queue = asyncio.Queue(maxsize=self._max_size)
                            # Update legacy queue reference
                            self._queue = self._normal_priority_queue
                        consecutive_errors += 1
                        await asyncio.sleep(min(consecutive_errors * 0.1, 5))
                    else:
                        raise
                
            except Exception as e:
                logger.error(f"Error in event processing: {e}", exc_info=True)
                consecutive_errors += 1
                # Add backoff for repeated errors
                await asyncio.sleep(min(consecutive_errors * 0.1, 5))
        
        # Process any remaining batch when shutting down
        if batch:
            try:
                await self._process_event_batch(batch)
            except Exception as e:
                logger.error(f"Error processing final batch during shutdown: {e}")
                
    async def _process_event_batch(self, batch: List[Event]):
        """Process a batch of events with the same event type"""
        if not batch:
            logger.debug("Attempted to process empty batch, skipping")
            return
            
        event_type = batch[0].event_type
        logger.debug(f"Processing batch of {len(batch)} events of type {event_type}")
        
        # Get subscribers for this event type
        subscribers = self._subscribers.get(event_type, set())
        
        if not subscribers:
            logger.debug(f"No subscribers for event type: {event_type}")
            return
            
        logger.debug(f"Found {len(subscribers)} subscribers for event type {event_type}")
            
        # Group events for batch processing
        batched_data = []
        for event in batch:
            batched_data.append(event.data)
            
        # Create a single batched event, preserving correlation ID
        correlation_id = batch[0].correlation_id if batch and hasattr(batch[0], 'correlation_id') and batch[0].correlation_id else None
        
        # Create a direct data dictionary instead of Event object for simpler testing
        event_data = {
            "batch": True,
            "count": len(batch),
            "items": batched_data,
            "correlation_id": correlation_id  # Add correlation ID to batch data too
        }
        
        # Create the event with simpler structure
        batched_event = Event(
            event_type=event_type,
            data=event_data,
            correlation_id=correlation_id  # Set correlation ID on Event object
        )
        
        # Process batch for each subscriber
        for subscriber_entry in subscribers:
            callback, loop_id, thread_id = subscriber_entry
            # Generate a unique event_id for retry tracking
            event_id = f"{event_type}_batch_{id(callback)}_{datetime.now().timestamp()}"
            try:
                # Only pass the required arguments to _deliver_event
                await self._deliver_event(batched_event, callback, event_id)
            except Exception as e:
                logger.error(f"Error in batch event delivery for {event_type}: {e}")
                # Continue to next subscriber

    async def _process_single_event(self, event):
        """Process a single event with better error isolation"""
        # Get subscribers for this event type
        subscribers = self._subscribers.get(event.event_type, set())
        
        if not subscribers:
            logger.debug(f"No subscribers for event type: {event.event_type}")
            return
        
        # Process event for each subscriber
        for subscriber_entry in subscribers:
            callback, loop_id, thread_id = subscriber_entry
            # Generate a unique event_id for retry tracking
            event_id = f"{event.event_type}_{id(callback)}_{datetime.now().timestamp()}"
            try:
                # Only pass the required arguments to _deliver_event
                await self._deliver_event(event, callback, event_id)
            except Exception as e:
                logger.error(f"Error in event delivery for {event.event_type}: {e}")
                # Continue to next subscriber instead of failing completely

    async def start(self):
        """Start event processing safely in the current event loop"""
        # Use EventLoopManager to submit to the creation loop
        await EventLoopManager.submit_to_resource_loop(self._id, self._start_internal())
    
    async def _start_internal(self):
        """Internal implementation for starting the queue in creation loop"""
        logger.info(f"Starting event queue {self._id} in creation loop")
        
        # Force initialization of all priority queues
        # This ensures they're all created before the event processor starts
        self.high_priority_queue  # Initialize high priority queue
        self.normal_priority_queue  # Initialize normal priority queue
        self.low_priority_queue  # Initialize low priority queue
        
        logger.debug(f"All priority queues initialized for {self._id}")
        
        # Check if already running
        if self._running and self._task and not self._task.done():
            logger.info(f"Event processor task for {self._id} already running")
            return
            
        # Create a new task in the current loop
        self._running = True
        self._task = asyncio.create_task(self._process_events())
        logger.info(f"Event processor task created for queue {self._id}")
        
        # Set name on task for better debugging if supported
        if hasattr(self._task, 'set_name'):
            self._task.set_name(f"event_processor_{self._id}")
        
        # Update registration with EventLoopManager to ensure proper resource tracking
        EventLoopManager.register_resource(self._id, self)

    async def stop(self):
        """Stop event processing safely using the creation loop"""
        # Use EventLoopManager to submit to the creation loop
        await EventLoopManager.submit_to_resource_loop(self._id, self._stop_internal())
    
    async def _stop_internal(self):
        """Internal implementation for stopping the queue in creation loop"""
        logger.info(f"Stopping event queue {self._id}")
        
        # Mark as not running to prevent new tasks
        self._running = False
        
        # Try to safely drain the queues with timeout protection
        try:
            total_items = 0
            try:
                total_items += self.high_priority_queue.qsize()
                total_items += self.normal_priority_queue.qsize()
                total_items += self.low_priority_queue.qsize()
            except NotImplementedError:
                # Some queue implementations don't support qsize
                pass
                
            if total_items > 0:
                logger.info(f"Waiting for {total_items} queued events to complete in queue {self._id}")
                
                # Use shorter timeout for faster shutdown
                try:
                    await asyncio.wait_for(self._wait_for_empty_queues(), timeout=3.0)
                    logger.info(f"Successfully drained queue {self._id}")
                except asyncio.TimeoutError:
                    logger.warning(f"Timed out waiting for queue {self._id} to drain")
            else:
                logger.info(f"Queues for {self._id} are already empty")
        except Exception as e:
            logger.warning(f"Error draining queue {self._id}: {e}")
        
        # Cancel the processor task
        if self._task and not self._task.done():
            try:
                logger.info(f"Cancelling event processor task for queue {self._id}")
                self._task.cancel()
                
                # Wait with timeout for the task to be cancelled
                try:
                    await asyncio.wait_for(asyncio.shield(self._task), timeout=2.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass
            except Exception as e:
                logger.error(f"Error cancelling event processor task: {e}")
        
        # Clear resources
        subscribers_count = sum(len(subs) for subs in self._subscribers.values())
        logger.info(f"Clearing {subscribers_count} subscribers from queue {self._id}")
        self._subscribers.clear()
        
        # Clear processing retries to prevent memory leaks
        retry_count = len(self._processing_retries)
        if retry_count > 0:
            logger.info(f"Clearing {retry_count} processing retries from queue {self._id}")
        self._processing_retries.clear()
        
        # Unregister from EventLoopManager
        EventLoopManager.unregister_resource(self._id)
        
        # Remove task reference
        self._task = None
        
        logger.info(f"Event queue {self._id} stopped successfully")
    
    async def _wait_for_empty_queues(self):
        """Wait for all queues to be empty"""
        while self._running:
            try:
                high_empty = self.high_priority_queue.empty()
                normal_empty = self.normal_priority_queue.empty()
                low_empty = self.low_priority_queue.empty()
                
                if high_empty and normal_empty and low_empty:
                    await asyncio.sleep(0.1)  # Brief pause to allow any in-progress processing
                    
                    # Double-check all are still empty
                    if (self.high_priority_queue.empty() and 
                        self.normal_priority_queue.empty() and 
                        self.low_priority_queue.empty()):
                        return True
                        
                await asyncio.sleep(0.1)
            except Exception:
                # If we can't check queue status, assume not empty
                await asyncio.sleep(0.1)

    async def subscribe(self, 
                        event_type: str, 
                        callback: Callable[[str, Dict[str, Any]], Awaitable[None]]) -> None:
        """Add subscriber for an event type with loop context tracking
        
        Args:
            event_type: The event type to subscribe to
            callback: The callback function to call when the event occurs
        """
        # Input validation
        if event_type is None or callback is None or not callable(callback):
            logger.error(f"Invalid subscription parameters: event_type={event_type}, callback={callback}")
            return
        
        # Convert enum to string if needed
        if hasattr(event_type, 'value'):
            event_type = event_type.value
            
        # Use EventLoopManager to submit to the queue's creation loop
        await EventLoopManager.submit_to_resource_loop(self._id, self._subscribe_internal(event_type, callback))
    
    async def _subscribe_internal(self, event_type: str, callback: Callable):
        """Internal implementation of subscribe that runs in creation loop"""
        # Get current thread and loop context for tracking
        thread_id = threading.get_ident()
        
        try:
            loop = asyncio.get_running_loop()
            loop_id = id(loop)
        except RuntimeError:
            logger.warning(f"No event loop when subscribing to {event_type}")
            loop_id = None
        
        # Create a set for this event type if it doesn't exist
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        
        # Add subscriber with context
        self._subscribers[event_type].add((callback, loop_id, thread_id))
        
        # Check if callback is a coroutine function for logging
        is_coroutine = asyncio.iscoroutinefunction(callback)
        logger.debug(f"Added subscriber for {event_type} events (coroutine={is_coroutine}, thread={thread_id}, loop={loop_id})")

    async def unsubscribe(self, 
                          event_type: str, 
                          callback: Callable[[str, Dict[str, Any]], Awaitable[None]]) -> None:
        """Remove a subscriber"""
        # Convert enum to string if needed
        if hasattr(event_type, 'value'):
            event_type = event_type.value
            
        # Use EventLoopManager to submit to the queue's creation loop
        await EventLoopManager.submit_to_resource_loop(self._id, self._unsubscribe_internal(event_type, callback))
    
    async def _unsubscribe_internal(self, event_type: str, callback: Callable):
        """Internal implementation of unsubscribe that runs in creation loop"""
        if event_type in self._subscribers:
            # Find the subscriber entry with matching callback
            to_remove = None
            for entry in self._subscribers[event_type]:
                subscriber_callback, _, _ = entry
                if subscriber_callback == callback:
                    to_remove = entry
                    break
            
            if to_remove:
                self._subscribers[event_type].discard(to_remove)
                logger.debug(f"Removed subscriber for {event_type} events")
    
    async def emit_error(self,
                        error: ResourceOperationError,
                        additional_context: Optional[Dict[str, Any]] = None) -> None:
        """Emit error event with full context"""
        event_data = {
            "severity": error.severity.name,
            "resource_id": error.resource_id,
            "operation": error.operation,
            "message": error.message,
            "timestamp": datetime.now().isoformat(),
            "recovery_strategy": error.recovery_strategy,
            "context": {
                "resource_id": error.context.resource_id,
                "operation": error.context.operation,
                "attempt": error.context.attempt,
                "recovery_attempts": error.context.recovery_attempts,
                "details": error.context.details,
                **(additional_context or {})
            }
        }
        
        await self.emit(
            ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
            event_data
        )

    async def _deliver_event(self, event: Event, callback, event_id: str) -> None:
        """Deliver event with proper loop context and retry handling"""
        # Initialize retry counter if needed
        if event_id not in self._processing_retries:
            self._processing_retries[event_id] = 0
        
        retry_count = self._processing_retries[event_id]
        max_retries = self._max_retries
        
        # Find the subscriber's loop and thread context
        subscriber_loop_id = None
        subscriber_thread_id = None
        
        # Extract loop and thread info from subscriber entry
        for event_type, subscribers in self._subscribers.items():
            for subscriber_entry in subscribers:
                sub_callback, sub_loop_id, sub_thread_id = subscriber_entry
                if sub_callback == callback:
                    subscriber_loop_id = sub_loop_id
                    subscriber_thread_id = sub_thread_id
                    break
            if subscriber_loop_id is not None:
                break
        
        # Attempt delivery with proper context
        while retry_count <= max_retries:
            try:
                # If we have subscriber loop context, use it for delivery
                if subscriber_loop_id is not None and subscriber_thread_id is not None:
                    # Check if any matching loop exists in registry
                    target_loop = None
                    for loop_info in EventLoopManager._loop_storage.list_all_loops():
                        loop, thread_id = loop_info
                        if id(loop) == subscriber_loop_id:
                            target_loop = loop
                            break
                    
                    if target_loop is not None:
                        # We found the subscriber's loop, submit to it
                        try:
                            # Use run_coroutine_threadsafe for cross-thread delivery
                            future = asyncio.run_coroutine_threadsafe(
                                self._call_subscriber(callback, event),
                                target_loop
                            )
                            # Wait for the result with timeout protection
                            result = await asyncio.wrap_future(future)
                            
                            # Delivery succeeded
                            self._processing_retries.pop(event_id, None)
                            return
                        except concurrent.futures.TimeoutError:
                            # Timeout, increment retry counter and continue
                            retry_count += 1
                            self._processing_retries[event_id] = retry_count
                            logger.warning(f"Timeout delivering event {event_id} to subscriber loop, retry {retry_count}/{max_retries}")
                        except Exception as e:
                            if isinstance(e, ResourceError):
                                # Retriable error
                                retry_count += 1
                                self._processing_retries[event_id] = retry_count
                                logger.warning(f"Resource error delivering event {event_id}: {e}, retry {retry_count}/{max_retries}")
                            else:
                                # Non-retriable error
                                logger.error(f"Error delivering event {event_id} to subscriber loop: {e}")
                                self._processing_retries.pop(event_id, None)
                                raise
                    else:
                        # Subscriber loop no longer exists, fall back to direct delivery
                        logger.warning(f"Subscriber loop for event {event_id} no longer exists, using direct delivery")
                        await self._call_subscriber(callback, event)
                        self._processing_retries.pop(event_id, None)
                        return
                else:
                    # No loop context info, use direct delivery
                    await self._call_subscriber(callback, event)
                    self._processing_retries.pop(event_id, None)
                    return
            except ResourceError as e:
                # Only retry for known resource errors
                retry_count += 1
                self._processing_retries[event_id] = retry_count
                
                if retry_count > max_retries:
                    logger.error(f"Max retries reached for event {event_id}")
                    self._processing_retries.pop(event_id, None)
                    raise
                
                # Exponential backoff with jitter
                base_delay = self._retry_delay * (2 ** (retry_count - 1))
                jitter = random.uniform(0, base_delay * 0.1)  # 10% jitter
                delay = base_delay + jitter
                
                logger.warning(f"Retry {retry_count}/{max_retries} for event {event_id} after error: {e}")
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error delivering event {event_id}: {e}")
                # Clean up retry counter for non-recoverable errors
                self._processing_retries.pop(event_id, None)
                raise
    
    async def _call_subscriber(self, callback, event: Event):
        """Simple wrapper to call subscriber with timing metrics"""
        start_time = time.monotonic()
        
        try:
            # Direct call with explicit tuple unpacking prevention
            # Get event_type and data directly from the event
            event_type = event.event_type
            data = event.data
            
            # Call directly with positional args
            if asyncio.iscoroutinefunction(callback):
                await callback(event_type, data)
            else:
                callback(event_type, data)
            
            delivery_time = time.monotonic() - start_time
            
            # Get a unique ID for logging (event_id may not be accessible here)
            event_id = event.metadata.get("event_id", str(id(event)))
            logger.debug(f"Delivered event {event_id} in {delivery_time:.3f}s")
        except Exception as e:
            logger.error(f"Error delivering event to subscriber: {e}")
            # Don't propagate errors from event handling to prevent event loop disruption

    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.queue.qsize()
    
    def get_subscriber_count(self, event_type: str) -> int:
        """Get number of subscribers for an event type"""
        return len(self._subscribers.get(event_type, set()))
    
    async def get_recent_events(self, 
                              event_type: Optional[str] = None,
                              limit: int = 100) -> List[Event]:
        """Get recent events, optionally filtered by type"""
        events = self._event_history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

class EventMonitor:
    """Monitors event system health and performance"""
    def __init__(self, event_queue: EventQueue):
        self.event_queue = event_queue
        self._health_check_interval = 60  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False
        
    async def start_monitoring(self):
        """Start health monitoring"""
        self._running = True
        self._health_check_task = asyncio.create_task(self._monitor_health())
        
    async def stop_monitoring(self):
        """Stop health monitoring"""
        self._running = False
        if self._health_check_task and not self._health_check_task.done():
            # Cancel the task explicitly
            self._health_check_task.cancel()
            try:
                # Wait for cancellation to complete
                await self._health_check_task
            except asyncio.CancelledError:
                # Ignore the expected cancellation error
                pass
            
    async def _monitor_health(self):
        """Periodic health check of event system"""
        while self._running:
            try:
                status = await self._check_health()
                event_data = {
                    "component": "event_system",
                    "status": status.status,
                    "description": status.description,
                    "metadata": status.metadata
                }
                
                logger.debug(f"Health check emitting status: {status.status} with queue_size={status.metadata.get('queue_size')}")
                
                # Directly call the subscriber callbacks to ensure delivery
                event_type = ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value
                subscribers = self.event_queue._subscribers.get(event_type, set())
                
                if subscribers:
                    logger.debug(f"Health check calling {len(subscribers)} subscribers directly")
                    for subscriber_entry in subscribers:
                        callback, _, _ = subscriber_entry
                        try:
                            await callback(event_type, event_data)
                            logger.debug(f"Successfully delivered health status {status.status} to subscriber")
                        except Exception as e:
                            logger.error(f"Error delivering health event to subscriber: {e}")
                else:
                    logger.warning(f"No subscribers found for health events")
                    
                # Also try normal emit for consistency
                try:
                    await self.event_queue.emit(
                        ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
                        event_data
                    )
                except Exception as e:
                    logger.error(f"Error emitting health event: {e}")
                    
            except Exception as e:
                logger.error(f"Error in event system health check: {str(e)}")
            finally:
                await asyncio.sleep(self._health_check_interval)
                
    async def _check_health(self) -> HealthStatus:
        """Check event system health metrics"""
        queue_size = self.event_queue.get_queue_size()
        max_size = self.event_queue._max_size
        queue_percentage = queue_size / max_size if max_size > 0 else 0
        
        logger.debug(f"Health check: queue_size={queue_size}, max_size={max_size}, percentage={queue_percentage:.2f}")
        
        total_subscribers = sum(
            self.event_queue.get_subscriber_count(event_type.value)
            for event_type in ResourceEventTypes
        )
        
        status = "HEALTHY"
        description = "Event system operating normally"
        
        # Use percentages based on max_size, check for degraded state first
        if queue_percentage >= 0.8:  # 80% of max size
            status = "DEGRADED"
            description = f"Event queue near capacity ({queue_percentage:.1%})"
            logger.debug(f"Health check: Detected DEGRADED state with queue at {queue_percentage:.1%}")
        
        # Then check for unhealthy state (more severe condition)
        if queue_percentage >= 0.95:  # 95% of max size
            status = "UNHEALTHY"
            description = f"Event queue at critical capacity ({queue_percentage:.1%})"
            logger.debug(f"Health check: Detected UNHEALTHY state with queue at {queue_percentage:.1%}")
        
        return HealthStatus(
            status=status,
            source="event_monitor",
            description=description,
            metadata={
                "queue_size": queue_size,
                "queue_percentage": queue_percentage,
                "total_subscribers": total_subscribers,
                "retry_count": len(self.event_queue._processing_retries)
            }
        )