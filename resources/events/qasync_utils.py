"""
qasync Compatibility Utilities

Provides utilities for robust event loop detection and task management
in qasync environments where standard asyncio methods may fail.
"""

import asyncio
import logging
from typing import Coroutine, Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


def get_qasync_compatible_loop() -> asyncio.AbstractEventLoop:
    """
    Get event loop with qasync compatibility.
    
    This function provides a robust method for getting the current event loop
    in qasync environments where standard asyncio.get_running_loop() may fail.
    
    Returns:
        The appropriate event loop for the current context
    """
    from resources.events.loop_management import EventLoopManager
    
    # Strategy 1: Try to get running loop (works in most qasync contexts)
    try:
        current_loop = asyncio.get_running_loop()
        logger.debug(f"Found running loop via asyncio: {id(current_loop)}")
        return current_loop
    except RuntimeError:
        pass
    
    # Strategy 2: Use EventLoopManager primary loop (qasync-aware)
    primary_loop = EventLoopManager.get_primary_loop()
    if primary_loop and not primary_loop.is_closed():
        logger.debug(f"Using EventLoopManager primary loop: {id(primary_loop)}")
        # Ensure this loop is set as the current event loop for the thread
        try:
            asyncio.set_event_loop(primary_loop)
        except Exception as e:
            logger.debug(f"Could not set primary loop as current: {e}")
        return primary_loop
    
    # Strategy 3: Get thread's default event loop
    try:
        thread_loop = asyncio.get_event_loop()
        logger.debug(f"Using thread event loop: {id(thread_loop)}")
        return thread_loop
    except RuntimeError:
        pass
    
    # Strategy 4: Last resort - create new loop
    logger.warning("No event loop found, creating new one")
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    EventLoopManager.set_primary_loop(new_loop)
    return new_loop


async def qasync_wait_for(coro_or_task, timeout: float = None) -> T:
    """
    qasync-compatible version of asyncio.wait_for().
    
    This function provides a robust alternative to asyncio.wait_for() that works
    consistently in qasync environments by avoiding the problematic internal
    event loop detection in asyncio.wait_for().
    
    Args:
        coro_or_task: Coroutine or Task to execute
        timeout: Timeout in seconds (None for no timeout)
        
    Returns:
        Result of the coroutine/task execution
        
    Raises:
        asyncio.TimeoutError: If timeout is exceeded
        Any exception raised by the coroutine/task
    """
    # Handle both coroutines and tasks
    if asyncio.iscoroutine(coro_or_task):
        # Get the loop using our robust method and create task
        loop = get_qasync_compatible_loop()
        task = loop.create_task(coro_or_task)
    elif asyncio.iscoroutinefunction(coro_or_task):
        # It's a coroutine function, call it first
        coro = coro_or_task()
        loop = get_qasync_compatible_loop()
        task = loop.create_task(coro)
    elif hasattr(coro_or_task, '__await__'):
        # It's already a task or future
        task = coro_or_task
    else:
        raise TypeError(f"Expected coroutine or task, got {type(coro_or_task)}")
    
    try:
        if timeout is None:
            # No timeout, just await the task
            return await task
        else:
            # Implement completely custom timeout that avoids ALL asyncio timeout functions
            loop = get_qasync_compatible_loop()
            
            # Create a custom timeout mechanism using loop.call_later
            timeout_occurred = False
            timeout_handle = None
            
            def timeout_callback():
                nonlocal timeout_occurred
                timeout_occurred = True
                if not task.done():
                    task.cancel()
            
            # Schedule timeout callback
            timeout_handle = loop.call_later(timeout, timeout_callback)
            
            try:
                # Wait for the task to complete
                result = await task
                
                # Cancel timeout since task completed
                if timeout_handle:
                    timeout_handle.cancel()
                
                if timeout_occurred:
                    raise asyncio.TimeoutError(f"Operation timed out after {timeout} seconds")
                
                return result
                
            except asyncio.CancelledError:
                # Task was cancelled, check if it was due to timeout
                if timeout_handle:
                    timeout_handle.cancel()
                
                if timeout_occurred:
                    raise asyncio.TimeoutError(f"Operation timed out after {timeout} seconds")
                else:
                    # Re-raise the cancellation
                    raise
                    
            except Exception:
                # Cancel timeout on any other exception
                if timeout_handle:
                    timeout_handle.cancel()
                raise
                
    except asyncio.CancelledError:
        # Ensure task is properly cancelled
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        raise
    except Exception:
        # Cancel the task on any exception
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        raise


async def qasync_sleep(delay: float) -> None:
    """
    qasync-compatible sleep function.
    
    This function provides a robust alternative to asyncio.sleep() that works
    consistently in qasync environments.
    
    Args:
        delay: Sleep duration in seconds
    """
    if delay <= 0:
        return
    
    loop = get_qasync_compatible_loop()
    future = loop.create_future()
    
    def wake_up():
        if not future.done():
            future.set_result(None)
    
    handle = loop.call_later(delay, wake_up)
    
    try:
        await future
    except asyncio.CancelledError:
        handle.cancel()
        raise
    finally:
        if not handle.cancelled():
            handle.cancel()


async def qasync_create_task(coro: Coroutine[Any, Any, T]) -> asyncio.Task[T]:
    """
    qasync-compatible task creation.
    
    Creates a task in the correct event loop context for qasync environments.
    
    Args:
        coro: Coroutine to create task for
        
    Returns:
        Created task
    """
    loop = get_qasync_compatible_loop()
    return loop.create_task(coro)


class QAsyncTaskManager:
    """Context manager for robust task management in qasync environments."""
    
    def __init__(self):
        self.tasks = []
        self.loop = None
    
    async def __aenter__(self):
        self.loop = get_qasync_compatible_loop()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cancel all pending tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for all tasks to complete cancellation
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
    
    def create_task(self, coro: Coroutine[Any, Any, T]) -> asyncio.Task[T]:
        """Create and track a task."""
        if not self.loop:
            raise RuntimeError("QAsyncTaskManager not properly initialized")
        
        task = self.loop.create_task(coro)
        self.tasks.append(task)
        return task
    
    async def wait_for(self, coro: Coroutine[Any, Any, T], timeout: float = None) -> T:
        """Execute coroutine with timeout in managed context."""
        task = self.create_task(coro)
        
        try:
            if timeout is None:
                return await task
            else:
                return await asyncio.wait_for(task, timeout=timeout)
        except asyncio.CancelledError:
            # Task will be cancelled by context manager
            raise
        except Exception:
            # Task will be cancelled by context manager
            raise