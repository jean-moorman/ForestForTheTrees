"""
Utility functions for the event system.

This module provides helper functions and common utilities used by the event system
components for rate limiting, validation, and other shared functionality.
"""
import asyncio
import logging
import random
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Awaitable

logger = logging.getLogger(__name__)

async def wait_with_backoff(retry_count: int, base_delay: float = 0.1, max_delay: float = 5.0):
    """Wait with exponential backoff and jitter.
    
    Args:
        retry_count: The current retry attempt number
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    """
    # Exponential backoff with jitter
    delay = min(base_delay * (2 ** retry_count), max_delay)
    jitter = random.uniform(0, delay * 0.1)  # 10% jitter
    await asyncio.sleep(delay + jitter)

async def with_timeout(coro, timeout_seconds: float = 5.0, description: str = "operation"):
    """Run a coroutine with timeout protection.
    
    Args:
        coro: The coroutine to run
        timeout_seconds: Timeout in seconds
        description: Description for logging
        
    Returns:
        The result of the coroutine or None if timeout occurs
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning(f"Timeout in {description} after {timeout_seconds}s")
        return None

def calculate_event_rate(timestamps: List[datetime]) -> float:
    """Calculate event rate (events per second) from timestamp list.
    
    Args:
        timestamps: List of datetime objects representing event times
        
    Returns:
        Rate in events per second, or 0 if not enough data
    """
    if len(timestamps) < 2:
        return 0.0
        
    # Calculate time span
    time_span = (timestamps[-1] - timestamps[0]).total_seconds()
    if time_span <= 0:
        return 0.0
        
    # Calculate events per second
    return len(timestamps) / time_span

def get_queue_saturation(current_size: int, max_size: int) -> float:
    """Calculate queue saturation percentage.
    
    Args:
        current_size: Current queue size
        max_size: Maximum queue size
        
    Returns:
        Saturation percentage (0.0-1.0)
    """
    if max_size <= 0:
        return 0.0
    return current_size / max_size

class RateLimiter:
    """Token bucket rate limiter for event throttling.
    
    This class implements a token bucket algorithm for rate limiting events,
    allowing for bursts of events while maintaining a long-term rate limit.
    """
    
    def __init__(self, rate: float = 10.0, max_tokens: float = 10.0, initial_tokens: float = 10.0):
        """Initialize rate limiter.
        
        Args:
            rate: Token refill rate per second
            max_tokens: Maximum token capacity
            initial_tokens: Initial token count
        """
        self.rate = rate
        self.max_tokens = max_tokens
        self.tokens = initial_tokens
        self.last_refill = time.time()
        self.consumed_tokens = 0
        
    def consume(self, tokens_needed: float = 1.0) -> bool:
        """Attempt to consume tokens for an event.
        
        Args:
            tokens_needed: Number of tokens required
            
        Returns:
            True if tokens were available and consumed, False otherwise
        """
        self._refill()
        
        if self.tokens < tokens_needed:
            return False
            
        self.tokens -= tokens_needed
        self.consumed_tokens += tokens_needed
        return True
        
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.rate
        
        # Update token count and last refill time
        self.tokens = min(self.tokens + new_tokens, self.max_tokens)
        self.last_refill = now
        
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics.
        
        Returns:
            Dictionary of statistics
        """
        return {
            "rate": self.rate,
            "max_tokens": self.max_tokens,
            "current_tokens": self.tokens,
            "consumed_tokens": self.consumed_tokens
        }