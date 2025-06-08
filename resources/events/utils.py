"""
Utility functions for the event system with actor model support.

This module provides helper functions for working with events in a thread-safe
manner, supporting the actor model with clear thread boundaries and reliable
message passing between threads.
"""
import asyncio
import concurrent.futures
import functools
import json
import logging
import random
import threading
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Awaitable, TypeVar, Union, Generic

logger = logging.getLogger(__name__)

# Type variable for return types
T = TypeVar('T')

async def wait_with_backoff(retry_count: int, base_delay: float = 0.1, max_delay: float = 5.0):
    """
    Wait with exponential backoff and jitter.
    
    Args:
        retry_count: The current retry attempt number
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    """
    delay = min(base_delay * (2 ** retry_count), max_delay)
    jitter = random.uniform(0, delay * 0.1)  # 10% jitter
    await asyncio.sleep(delay + jitter)

async def with_timeout(coro, timeout_seconds: float = 5.0, description: str = "operation"):
    """
    Run a coroutine with timeout protection.
    
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

class ThreadSafeCounter:
    """Thread-safe counter for event tracking."""
    
    def __init__(self, initial_value: int = 0):
        """
        Initialize counter.
        
        Args:
            initial_value: Initial counter value
        """
        self._value = initial_value
        self._lock = threading.RLock()
    
    @property
    def value(self) -> int:
        """
        Get current value as a property.
        
        Returns:
            Current counter value
        """
        with self._lock:
            return self._value
        
    def increment(self, amount: int = 1) -> int:
        """
        Increment counter.
        
        Args:
            amount: Amount to increment by
            
        Returns:
            New counter value
        """
        with self._lock:
            self._value += amount
            return self._value
            
    def decrement(self, amount: int = 1) -> int:
        """
        Decrement counter.
        
        Args:
            amount: Amount to decrement by
            
        Returns:
            New counter value
        """
        with self._lock:
            self._value -= amount
            return self._value
            
    def get(self) -> int:
        """
        Get current value.
        
        Returns:
            Current counter value
        """
        with self._lock:
            return self._value
            
    def reset(self, value: int = 0) -> None:
        """
        Reset counter to specified value.
        
        Args:
            value: Value to reset to
        """
        with self._lock:
            self._value = value

class RateLimiter:
    """
    Token bucket rate limiter for event throttling.
    
    This class implements a token bucket algorithm for rate limiting events,
    allowing for bursts of events while maintaining a long-term rate limit.
    Thread-safe for use across multiple threads.
    """
    
    def __init__(self, rate: float = 10.0, max_tokens: float = 10.0, initial_tokens: float = 10.0,
                 max_rate: float = None, window_size: float = 1.0):
        """
        Initialize rate limiter.
        
        Args:
            rate: Token refill rate per second
            max_tokens: Maximum token capacity
            initial_tokens: Initial token count
            max_rate: Maximum operations per window_size (alternative configuration)
            window_size: Time window for max_rate in seconds
        """
        # Use a lock for thread safety
        self._lock = threading.RLock()
        
        with self._lock:
            if max_rate is not None:
                # Configure using max_rate and window_size
                self.rate = max_rate / window_size
                self.max_tokens = max_rate
                self.tokens = max_rate
            else:
                # Configure using traditional token bucket parameters
                self.rate = rate
                self.max_tokens = max_tokens
                self.tokens = initial_tokens
            
            self.last_refill = time.time()
            self.consumed_tokens = 0
        
    def consume(self, tokens_needed: float = 1.0) -> bool:
        """
        Attempt to consume tokens for an event.
        
        Args:
            tokens_needed: Number of tokens required
            
        Returns:
            True if tokens were available and consumed, False otherwise
        """
        with self._lock:
            self._refill()
            
            if self.tokens < tokens_needed:
                return False
                
            self.tokens -= tokens_needed
            self.consumed_tokens += tokens_needed
            return True
    
    def allow_operation(self, tokens_needed: float = 1.0) -> bool:
        """
        Determine if an operation should be allowed under rate limiting.
        Alias for consume() to provide a more intuitive API.
        
        Args:
            tokens_needed: Number of tokens required for this operation
            
        Returns:
            True if operation is allowed, False if it should be rate limited
        """
        return self.consume(tokens_needed)
        
    def _refill(self):
        """
        Refill tokens based on elapsed time.
        
        Note: This method must be called with the lock held.
        """
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.rate
        
        # Update token count and last refill time
        self.tokens = min(self.tokens + new_tokens, self.max_tokens)
        self.last_refill = now
    
    def get_available_tokens(self) -> float:
        """
        Get the current number of available tokens.
        
        Returns:
            float: Current available tokens
        """
        with self._lock:
            self._refill()
            return self.tokens
    
    def get_tokens_per_second(self) -> float:
        """
        Get the token refill rate per second.
        
        Returns:
            float: Token refill rate
        """
        with self._lock:
            return self.rate
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Get rate limiter statistics.
        
        Returns:
            Dictionary of statistics
        """
        with self._lock:
            self._refill()  # Update tokens before reporting
            return {
                "rate": self.rate,
                "max_tokens": self.max_tokens,
                "current_tokens": self.tokens,
                "consumed_tokens": self.consumed_tokens,
                "last_refill": self.last_refill
            }

def ensure_event_loop() -> asyncio.AbstractEventLoop:
    """
    Simplified event loop creation using new two-loop architecture.
    
    Returns:
        The appropriate event loop for current thread
    """
    from resources.events.loop_management import EventLoopManager
    return EventLoopManager.ensure_event_loop()

class ThreadPoolExecutorManager:
    """
    Manager for thread pool executors with graceful shutdown support.
    
    This class provides a singleton for managing thread pool executors used by
    the event system, ensuring proper cleanup on shutdown.
    """
    _instance = None
    _lock = threading.RLock()
    
    def __init__(self):
        """Initialize manager."""
        self._executors = {}
        self._shutdown_in_progress = False
        
    @classmethod
    def get_instance(cls):
        """Get singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = ThreadPoolExecutorManager()
            return cls._instance
            
    def get_executor(self, name: str, max_workers: Optional[int] = None) -> concurrent.futures.ThreadPoolExecutor:
        """
        Get or create thread pool executor.
        
        Args:
            name: Name of the executor
            max_workers: Maximum number of worker threads
            
        Returns:
            ThreadPoolExecutor: The thread pool executor
        """
        with self._lock:
            if name in self._executors:
                return self._executors[name]
                
            # Create new executor
            executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers,
                thread_name_prefix=name
            )
            self._executors[name] = executor
            return executor
            
    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown all executors.
        
        Args:
            wait: Whether to wait for executor shutdown
        """
        with self._lock:
            self._shutdown_in_progress = True
            
            for name, executor in list(self._executors.items()):
                try:
                    executor.shutdown(wait=wait)
                    logger.debug(f"Executor {name} shut down")
                except Exception as e:
                    logger.error(f"Error shutting down executor {name}: {e}")
                    
            self._executors.clear()
            self._shutdown_in_progress = False

def run_in_executor(func: Callable[..., T], *args, **kwargs) -> T:
    """
    Run a blocking function in a thread pool executor.
    
    This function can be used to run blocking operations from the main thread
    without blocking the event loop.
    
    Args:
        func: Function to execute
        *args: Args to pass to func
        **kwargs: Kwargs to pass to func
        
    Returns:
        Result of the function execution
    """
    executor = ThreadPoolExecutorManager.get_instance().get_executor("default")
    return executor.submit(func, *args, **kwargs).result()

async def run_async_in_thread(coro: Awaitable[T]) -> T:
    """
    Run an async function in a separate thread with a new event loop.
    
    This is useful for running async code from a synchronous context or when
    you need to run async code in a fresh event loop.
    
    Args:
        coro: Coroutine to run
        
    Returns:
        Result of the coroutine execution
    """
    def run_in_new_loop(coro):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
            
    # Get the executor
    executor = ThreadPoolExecutorManager.get_instance().get_executor("async_thread")
    
    # Run the coroutine in a new thread with a new event loop
    return await asyncio.get_event_loop().run_in_executor(executor, run_in_new_loop, coro)

class MessageBroker:
    """
    Thread-safe message broker for actor model communication.
    
    This class provides a simple message broker for passing messages between
    actors in different threads, ensuring thread safety and proper event
    delivery.
    """
    _instance = None
    _lock = threading.RLock()
    
    def __init__(self):
        """Initialize broker."""
        self._handlers = {}
        self._message_counts = {}
        
    @classmethod
    def get_instance(cls):
        """Get singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = MessageBroker()
            return cls._instance
            
    def register_handler(self, message_type: str, handler: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Register a message handler.
        
        Args:
            message_type: Type of message to handle
            handler: Function to call when message is received
        """
        with self._lock:
            if message_type not in self._handlers:
                self._handlers[message_type] = set()
                self._message_counts[message_type] = 0
                
            self._handlers[message_type].add(handler)
            
    def unregister_handler(self, message_type: str, handler: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Unregister a message handler.
        
        Args:
            message_type: Type of message
            handler: Handler to unregister
        """
        with self._lock:
            if message_type in self._handlers:
                self._handlers[message_type].discard(handler)
                
    def send_message(self, message_type: str, message: Dict[str, Any]) -> None:
        """
        Send a message to all registered handlers.
        
        This method is thread-safe and can be called from any thread. The message
        will be delivered to handlers in the thread that calls this method.
        
        Args:
            message_type: Type of message
            message: Message data
        """
        handlers = set()
        
        # Get handlers with lock
        with self._lock:
            if message_type in self._handlers:
                handlers = set(self._handlers[message_type])
                self._message_counts[message_type] += 1
                
        # Call handlers without lock to avoid deadlocks
        for handler in handlers:
            try:
                # Support both handler signatures: (message) and (message_type, message)
                try:
                    # Try the new signature first
                    handler(message_type, message)
                except TypeError:
                    # Fall back to old signature
                    handler(message)
            except Exception as e:
                logger.error(f"Error in message handler for {message_type}: {e}")
                
    def get_message_counts(self) -> Dict[str, int]:
        """
        Get message count statistics.
        
        Returns:
            Dict[str, int]: Count of messages by type
        """
        with self._lock:
            return dict(self._message_counts)

class ActorRef:
    """
    Reference to an actor for thread-safe message passing.
    
    This class provides a way to send messages to an actor running in a different
    thread without directly calling methods on the actor, maintaining proper
    thread boundaries.
    """
    
    def __init__(self, actor_id: str, executor: concurrent.futures.ThreadPoolExecutor = None):
        """
        Initialize actor reference.
        
        Args:
            actor_id: ID of the actor
            executor: Thread pool executor for this actor
        """
        self.actor_id = actor_id
        self._executor = executor or ThreadPoolExecutorManager.get_instance().get_executor("actor")
        self._mailbox = []
        self._lock = threading.RLock()
        self._processing = False
        self._message_processor = None
        
    def set_message_processor(self, processor: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Set a direct message processor for this actor.
        
        This provides an alternative to using the MessageBroker for processing
        messages when direct processing is needed.
        
        Args:
            processor: Function that takes message_type and message as arguments
        """
        with self._lock:
            self._message_processor = processor
        
    def tell(self, message_type: str, message: Dict[str, Any]) -> None:
        """
        Send a message to the actor.
        
        Args:
            message_type: Type of message
            message: Message data
        """
        with self._lock:
            self._mailbox.append((message_type, message))
            
            # Start processing if not already doing so
            if not self._processing:
                self._processing = True
                self._executor.submit(self._process_mailbox)
                
    def _process_mailbox(self) -> None:
        """Process messages in the mailbox."""
        try:
            # Get the message broker
            broker = MessageBroker.get_instance()
            
            while True:
                # Get next message with lock
                with self._lock:
                    if not self._mailbox:
                        self._processing = False
                        break
                        
                    message_type, message = self._mailbox.pop(0)
                    # Check if we have a direct processor
                    message_processor = self._message_processor
                    
                # Add actor_id to message
                message["actor_id"] = self.actor_id
                
                # Process the message
                if message_processor:
                    # Use direct processor if available
                    try:
                        message_processor(message_type, message)
                    except Exception as e:
                        logger.error(f"Error in message processor for actor {self.actor_id}: {e}")
                else:
                    # Otherwise use message broker
                    broker.send_message(message_type, message)
                
        except Exception as e:
            logger.error(f"Error processing mailbox for actor {self.actor_id}: {e}")
            # Ensure we reset processing flag
            with self._lock:
                self._processing = False

async def get_llm_client():
    """
    Get or create an LLM client for API calls.
    
    This function is used to get a shared LLM client instance throughout the system.
    It ensures proper initialization of the client with API keys and configuration.
    
    Returns:
        An initialized LLM client instance for making API calls
    """
    logger.debug("Initializing LLM client")
    
    try:
        # Try to import from the agent module
        from api import AnthropicAPI
        import os
        from dotenv import load_dotenv
        
        # Load environment variables for API keys
        load_dotenv()
        
        # Get the API key from environment
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            logger.warning("ANTHROPIC_API_KEY not found in environment variables")
            # Return a mock client for testing when API key is not available
            return _MockLLMClient()
            
        # Create and return the client
        api_client = AnthropicAPI(
            model="claude-3-7-sonnet-20250219",
            key=anthropic_api_key
        )
        
        logger.debug("LLM client initialized successfully")
        return api_client
        
    except ImportError as e:
        logger.error(f"Failed to import required modules for LLM client: {e}")
        # Return a mock client in case of import failure
        return _MockLLMClient()
    except Exception as e:
        logger.error(f"Error initializing LLM client: {e}")
        # Return a mock client in case of any other error
        return _MockLLMClient()


class _MockLLMClient:
    """Mock LLM client implementation for testing or when API is unavailable."""
    
    async def call(self, conversation, system_prompt_info, schema=None, current_phase=None, max_tokens=None):
        """Mock implementation of the call method."""
        logger.warning("Using mock LLM client - this is only for testing/development")
        return json.dumps({
            "status": "success",
            "message": "This is a mock response from the LLM client",
            "data": {}
        })