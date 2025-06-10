"""
Standardized async operation patterns for FFTT.

This module provides standardized patterns for async operations that are
compatible with both qasync and standard asyncio environments, preventing
the "RuntimeError: no running event loop" issues that were occurring.
"""

import asyncio
import functools
import logging
from typing import Callable, Awaitable, Any, Optional, TypeVar, Union

from .qasync_utils import qasync_wait_for, get_qasync_compatible_loop

logger = logging.getLogger(__name__)

T = TypeVar('T')


class AsyncOperationError(Exception):
    """Base exception for async operation failures."""
    pass


class TimeoutOperationError(AsyncOperationError):
    """Exception for timeout-related async operation failures."""
    pass


def qasync_compatible(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """
    Decorator to make async functions qasync-compatible.
    
    This decorator ensures that async functions use qasync-compatible
    event loop detection and timeout handling.
    
    Usage:
        @qasync_compatible
        async def my_async_function():
            await some_operation()
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            # Ensure we have a qasync-compatible loop
            loop = get_qasync_compatible_loop()
            logger.debug(f"Executing {func.__name__} in loop {id(loop)}")
            
            # Execute the function
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in qasync-compatible function {func.__name__}: {e}")
            raise
    
    return wrapper


def with_qasync_timeout(timeout: float):
    """
    Decorator to add qasync-compatible timeout to async functions.
    
    Args:
        timeout: Timeout in seconds
        
    Usage:
        @with_qasync_timeout(30.0)
        async def my_long_operation():
            await some_long_task()
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await qasync_wait_for(func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError as e:
                raise TimeoutOperationError(
                    f"Operation {func.__name__} timed out after {timeout}s"
                ) from e
        
        return wrapper
    return decorator


async def safe_async_operation(
    operation: Callable[..., Awaitable[T]], 
    *args, 
    timeout: Optional[float] = None,
    retry_count: int = 0,
    **kwargs
) -> T:
    """
    Execute an async operation safely with qasync compatibility.
    
    Args:
        operation: The async operation to execute
        *args: Arguments for the operation
        timeout: Optional timeout in seconds
        retry_count: Number of retries on failure
        **kwargs: Keyword arguments for the operation
        
    Returns:
        Result of the operation
        
    Raises:
        AsyncOperationError: If operation fails after retries
        TimeoutOperationError: If operation times out
    """
    last_exception = None
    
    for attempt in range(retry_count + 1):
        try:
            if timeout:
                return await qasync_wait_for(operation(*args, **kwargs), timeout=timeout)
            else:
                return await operation(*args, **kwargs)
                
        except asyncio.TimeoutError as e:
            raise TimeoutOperationError(
                f"Operation {operation.__name__} timed out after {timeout}s"
            ) from e
        except Exception as e:
            last_exception = e
            if attempt < retry_count:
                logger.warning(f"Attempt {attempt + 1} failed for {operation.__name__}: {e}")
                await asyncio.sleep(0.1 * (attempt + 1))  # Progressive backoff
            else:
                logger.error(f"All {retry_count + 1} attempts failed for {operation.__name__}: {e}")
    
    raise AsyncOperationError(
        f"Operation {operation.__name__} failed after {retry_count + 1} attempts"
    ) from last_exception


class QAsyncOperationManager:
    """
    Manager for executing async operations with qasync compatibility.
    
    This class provides methods for common async operation patterns
    that work reliably in both qasync and standard asyncio environments.
    """
    
    def __init__(self, default_timeout: float = 30.0):
        self.default_timeout = default_timeout
        
    async def execute_with_timeout(
        self, 
        operation: Callable[..., Awaitable[T]], 
        timeout: Optional[float] = None,
        *args, 
        **kwargs
    ) -> T:
        """Execute operation with timeout using qasync-compatible methods."""
        timeout = timeout or self.default_timeout
        return await qasync_wait_for(operation(*args, **kwargs), timeout=timeout)
        
    async def execute_concurrent_operations(
        self, 
        operations: list[tuple[Callable[..., Awaitable[Any]], tuple, dict]],
        timeout: Optional[float] = None
    ) -> list[Any]:
        """
        Execute multiple operations concurrently with qasync compatibility.
        
        Args:
            operations: List of (operation, args, kwargs) tuples
            timeout: Optional timeout for the entire batch
            
        Returns:
            List of results in the same order as operations
        """
        tasks = []
        for operation, args, kwargs in operations:
            task = asyncio.create_task(operation(*args, **kwargs))
            tasks.append(task)
            
        if timeout:
            return await qasync_wait_for(asyncio.gather(*tasks), timeout=timeout)
        else:
            return await asyncio.gather(*tasks)
            
    async def execute_with_circuit_breaker(
        self,
        operation: Callable[..., Awaitable[T]],
        max_failures: int = 3,
        reset_timeout: float = 60.0,
        *args,
        **kwargs
    ) -> T:
        """
        Execute operation with simple circuit breaker pattern.
        
        This is a simplified circuit breaker for critical operations.
        """
        # For now, just execute the operation safely
        # In the future, this could be extended with full circuit breaker logic
        return await safe_async_operation(operation, *args, **kwargs)


# Global operation manager instance
operation_manager = QAsyncOperationManager()


# Convenience functions for common patterns
async def timeout_operation(operation: Callable[..., Awaitable[T]], timeout: float, *args, **kwargs) -> T:
    """Execute operation with timeout - qasync compatible."""
    return await operation_manager.execute_with_timeout(operation, timeout, *args, **kwargs)


async def concurrent_operations(*operations) -> list[Any]:
    """Execute operations concurrently - qasync compatible."""
    operation_tuples = [(op, (), {}) for op in operations]
    return await operation_manager.execute_concurrent_operations(operation_tuples)


# Pattern enforcement utilities
def check_asyncio_usage():
    """
    Check for potentially problematic asyncio usage patterns.
    
    This could be used in testing or CI to detect usage of raw
    asyncio.wait_for() in GUI contexts.
    """
    import inspect
    import ast
    
    # This is a placeholder for a more sophisticated check
    # that could scan code for asyncio.wait_for usage
    pass


def suggest_qasync_alternative(api_call: str) -> str:
    """Suggest qasync-compatible alternatives for common asyncio calls."""
    alternatives = {
        'asyncio.wait_for': 'qasync_wait_for from resources.events.qasync_utils',
        'asyncio.get_running_loop': 'get_qasync_compatible_loop from resources.events.qasync_utils',
        'asyncio.create_task': 'loop.create_task where loop = get_qasync_compatible_loop()',
    }
    
    return alternatives.get(api_call, f"No known qasync alternative for {api_call}")


__all__ = [
    'AsyncOperationError',
    'TimeoutOperationError', 
    'qasync_compatible',
    'with_qasync_timeout',
    'safe_async_operation',
    'QAsyncOperationManager',
    'operation_manager',
    'timeout_operation',
    'concurrent_operations',
    'suggest_qasync_alternative'
]