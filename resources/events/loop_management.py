"""
Simplified event loop management with clear ownership boundaries.

This module provides a minimal event loop registry for the two-loop architecture:
- Main thread: qasync loop for GUI integration
- Background thread: dedicated loop for processing and monitoring
"""
import asyncio
import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)


class SimpleEventLoopRegistry:
    """
    Minimal event loop registry for two-loop architecture.
    
    Maintains references to:
    - Main thread loop (qasync for GUI)
    - Background processing loop (for workflows and monitoring)
    """
    
    def __init__(self):
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        self._background_loop: Optional[asyncio.AbstractEventLoop] = None
        self._lock = threading.RLock()
        
        # Track registration history to prevent spam
        self._registration_history = set()  # Track (loop_id, thread_id, loop_type) tuples
        self._last_registration_time = {}  # Track timing for rate limiting
    
    def set_main_loop(self, loop: asyncio.AbstractEventLoop) -> bool:
        """Set the main thread event loop (qasync)."""
        with self._lock:
            if threading.current_thread() is not threading.main_thread():
                logger.warning("Main loop should only be set from main thread")
                return False
            
            loop_id = id(loop)
            thread_id = threading.get_ident()
            registration_key = (loop_id, thread_id, "main")
            
            # CRITICAL: Check if this loop is already registered as background loop
            if self._background_loop and id(self._background_loop) == loop_id:
                logger.error(f"Loop {loop_id} is already registered as background loop - cannot register as main loop")
                return False
            
            # Check for duplicate registration
            if registration_key in self._registration_history:
                logger.debug(f"Main loop {loop_id} already registered for thread {thread_id}")
                return True
            
            self._main_loop = loop
            self._registration_history.add(registration_key)
            self._last_registration_time[registration_key] = time.time()
            logger.info(f"Registered main loop {loop_id} in main thread")
            return True
    
    def set_background_loop(self, loop: asyncio.AbstractEventLoop) -> bool:
        """Set the background processing loop."""
        with self._lock:
            loop_id = id(loop)
            thread_id = threading.get_ident()
            registration_key = (loop_id, thread_id, "background")
            
            # CRITICAL: Check if this loop is already registered as main loop
            if self._main_loop and id(self._main_loop) == loop_id:
                # Reduce spam by only logging the first few violations, then switch to debug
                violation_count = getattr(self, '_violation_count', 0) + 1
                self._violation_count = violation_count
                
                if violation_count <= 3:
                    logger.error(f"Loop {loop_id} is already registered as main loop - cannot register as background loop (violation #{violation_count})")
                elif violation_count == 4:
                    logger.warning(f"Loop ownership violation spam detected - further violations will be logged at DEBUG level")
                else:
                    logger.debug(f"Loop {loop_id} ownership violation #{violation_count} (main->background)")
                return False
            
            # Check for duplicate registration
            if registration_key in self._registration_history:
                logger.debug(f"Background loop {loop_id} already registered for thread {thread_id}")
                return True
            
            self._background_loop = loop
            self._registration_history.add(registration_key)
            self._last_registration_time[registration_key] = time.time()
            logger.info(f"Registered background loop {loop_id} in thread {thread_id}")
            return True
    
    def get_main_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        """Get the main thread event loop."""
        with self._lock:
            return self._main_loop
    
    def get_background_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        """Get the background processing loop."""
        with self._lock:
            return self._background_loop
    
    def clear_loops(self) -> None:
        """Clear all loop references (for cleanup)."""
        with self._lock:
            self._main_loop = None
            self._background_loop = None
            logger.info("Cleared all event loop references")
    
    def set_loop(self, loop_id_or_loop, loop=None) -> bool:
        """Legacy compatibility method for setting loops - handles both parameter patterns with thread awareness."""
        import threading
        
        with self._lock:
            # Handle the case where only one argument is passed (just the loop)
            if loop is None:
                # Only one argument passed, treat it as the loop and use thread-aware logic
                actual_loop = loop_id_or_loop
                current_thread = threading.current_thread()
                
                if current_thread is threading.main_thread():
                    logger.debug(f"Legacy set_loop call with single parameter (loop {id(actual_loop)}) from main thread, treating as main loop")
                    return self.set_main_loop(actual_loop)
                else:
                    logger.debug(f"Legacy set_loop call with single parameter (loop {id(actual_loop)}) from thread {threading.get_ident()}, treating as background loop")
                    return self.set_background_loop(actual_loop)
            
            # Two arguments passed - traditional (loop_id, loop) pattern  
            loop_id = loop_id_or_loop
            if loop_id == "main" or loop_id.startswith("main"):
                return self.set_main_loop(loop)
            elif loop_id == "background" or loop_id.startswith("background"):
                return self.set_background_loop(loop)
            else:
                # For unknown loop IDs, use thread-aware logic
                current_thread = threading.current_thread()
                if current_thread is threading.main_thread():
                    logger.debug(f"Legacy set_loop call with unknown ID '{loop_id}' from main thread, treating as main loop")
                    return self.set_main_loop(loop)
                else:
                    logger.debug(f"Legacy set_loop call with unknown ID '{loop_id}' from thread {threading.get_ident()}, treating as background loop")
                    return self.set_background_loop(loop)


# Global registry instance
_registry = SimpleEventLoopRegistry()


class EventLoopManager:
    """
    Compatibility wrapper for existing code.
    
    Provides simplified interface matching existing API but with
    clean two-loop architecture underneath.
    """
    
    @staticmethod
    def set_primary_loop(loop: asyncio.AbstractEventLoop) -> bool:
        """Set primary loop (maps to main loop)."""
        return _registry.set_main_loop(loop)
    
    @staticmethod
    def get_primary_loop() -> Optional[asyncio.AbstractEventLoop]:
        """Get primary loop (maps to main loop)."""
        return _registry.get_main_loop()
    
    @staticmethod
    def set_background_loop(loop: asyncio.AbstractEventLoop) -> bool:
        """Set background processing loop."""
        return _registry.set_background_loop(loop)
    
    @staticmethod
    def get_background_loop() -> Optional[asyncio.AbstractEventLoop]:
        """Get background processing loop."""
        return _registry.get_background_loop()
    
    @staticmethod
    def get_loop_for_thread(thread_id: Optional[int] = None) -> asyncio.AbstractEventLoop:
        """
        Route to correct loop based on thread context.
        
        Args:
            thread_id: Optional thread ID to check (defaults to current thread)
            
        Returns:
            The appropriate event loop for the thread context
        """
        current_thread = threading.current_thread()
        
        if current_thread is threading.main_thread():
            # Main thread: return qasync loop or create one
            main_loop = _registry.get_main_loop()
            if main_loop and not main_loop.is_closed():
                return main_loop
            else:
                # Create and register main loop if needed
                return EventLoopManager.ensure_event_loop()
        else:
            # Background thread: return dedicated background loop or create one
            background_loop = _registry.get_background_loop()
            if background_loop and not background_loop.is_closed():
                return background_loop
            else:
                # Create new background loop for this thread
                try:
                    return asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    _registry.set_background_loop(loop)
                    return loop
    
    @staticmethod
    def submit_to_correct_loop(coro, thread_context="current"):
        """
        Submit coroutine to appropriate loop based on thread context.
        
        Args:
            coro: Coroutine to execute
            thread_context: "main", "background", or "current" (default)
            
        Returns:
            Future that can be awaited
        """
        if thread_context == "main":
            target_loop = EventLoopManager.get_primary_loop()
        elif thread_context == "background":
            target_loop = EventLoopManager.get_background_loop()
        else:
            target_loop = EventLoopManager.get_loop_for_thread()
        
        if not target_loop:
            raise RuntimeError(f"No event loop available for thread context: {thread_context}")
        
        try:
            current_loop = asyncio.get_running_loop()
            if current_loop == target_loop:
                # Already in correct loop, create task directly
                return asyncio.create_task(coro)
            else:
                # Submit to different loop
                return asyncio.run_coroutine_threadsafe(coro, target_loop)
        except RuntimeError:
            # No running loop, submit to target loop
            return asyncio.run_coroutine_threadsafe(coro, target_loop)
    
    @staticmethod
    def run_coroutine_threadsafe(coro, target_loop=None):
        """
        Compatibility method for legacy code - delegates to asyncio.run_coroutine_threadsafe.
        
        Args:
            coro: Coroutine to execute
            target_loop: Target event loop (if None, uses appropriate loop from registry)
            
        Returns:
            Future that can be awaited
        """
        if target_loop is None:
            # Use the simplified architecture to find appropriate loop
            target_loop = EventLoopManager.get_loop_for_thread()
        
        return asyncio.run_coroutine_threadsafe(coro, target_loop)
    
    @staticmethod
    def ensure_event_loop() -> asyncio.AbstractEventLoop:
        """
        Simplified event loop creation.
        
        Returns the appropriate loop for current thread:
        - Main thread: returns main loop or creates one
        - Other threads: creates new loop for that thread
        """
        if threading.current_thread() is threading.main_thread():
            # Main thread - return existing main loop or create one
            main_loop = _registry.get_main_loop()
            if main_loop and not main_loop.is_closed():
                return main_loop
            
            # Create new main thread loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            _registry.set_main_loop(loop)
            return loop
        else:
            # Background thread - create dedicated loop
            try:
                return asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop
    
    @staticmethod
    def cleanup() -> None:
        """Clean up all loop references."""
        _registry.clear_loops()
    
    @staticmethod
    def get_event_loop() -> asyncio.AbstractEventLoop:
        """Legacy compatibility method - returns current or creates new event loop."""
        try:
            # Try to get the running loop first
            return asyncio.get_running_loop()
        except RuntimeError:
            try:
                # Try to get the thread's default loop
                return asyncio.get_event_loop()
            except RuntimeError:
                # Create new loop as fallback
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                logger.debug(f"Created new event loop {id(loop)} for legacy get_event_loop() call")
                return loop
    
    @staticmethod
    def register_resource(name: str, resource) -> bool:
        """Legacy compatibility method - no-op in simplified architecture."""
        logger.debug(f"Legacy register_resource call for {name} - ignoring in simplified architecture")
        return True
    
    @staticmethod
    def set_loop(loop_id_or_loop, loop=None) -> bool:
        """Legacy compatibility method - delegates to registry with flexible parameters."""
        return _registry.set_loop(loop_id_or_loop, loop)


# Legacy compatibility - remove complex classes
class ThreadLocalEventLoopStorage:
    """Legacy compatibility class - redirects to simplified registry."""
    
    @classmethod
    def get_instance(cls):
        """Legacy compatibility method."""
        return _registry
    
    def set_loop(self, loop):
        """Legacy compatibility method - takes just loop parameter with thread-aware registration."""
        import threading
        current_thread = threading.current_thread()
        
        if current_thread is threading.main_thread():
            # Main thread should use main loop registration
            logger.debug(f"Legacy set_loop call with loop {id(loop)} from main thread - registering as main loop")
            return _registry.set_main_loop(loop)
        else:
            # Non-main threads use background loop registration
            logger.debug(f"Legacy set_loop call with loop {id(loop)} from thread {threading.get_ident()} - registering as background loop")
            return _registry.set_background_loop(loop)