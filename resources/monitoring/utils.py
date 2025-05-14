"""
Utility functions and helpers for the monitoring package.
"""

import functools
import asyncio
from typing import Callable, Any, Awaitable

def with_memory_checking(func):
    """Decorator that provides the original function for testing."""
    @functools.wraps(func)
    async def wrapper(self):
        return await func(self)
    
    return wrapper