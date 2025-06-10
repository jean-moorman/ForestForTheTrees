"""
Event Loop and Background Thread Management for Phase One GUI

Handles event loop coordination, background processing threads, health monitoring,
and async task management for the Qt-based Phase One application.
"""

import asyncio
import logging
import threading
import time
from typing import Set, Dict, Any, Optional

from PyQt6.QtCore import QTimer

logger = logging.getLogger(__name__)


class EventManager:
    """Manages event loops, background threads, and async task coordination."""
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._tasks: Set[asyncio.Task] = set()
        self._initialized = False
        self._background_thread: Optional[threading.Thread] = None
        self._shutdown_background = False
        self._last_loop_health_check = time.time()
        self._healthcheck_timer: Optional[QTimer] = None
        
    def setup_event_loop(self):
        """Set up and configure the main event loop."""
        from resources.events.utils import ensure_event_loop
        from resources.events.loop_management import EventLoopManager
        
        # Ensure we have a valid event loop
        self.loop = ensure_event_loop()
        current_thread_id = threading.get_ident()
        is_main_thread = threading.current_thread() is threading.main_thread()
        logger.info(f"Initialized event loop {id(self.loop)} on {'main' if is_main_thread else 'worker'} thread {current_thread_id}")
        
        # Register this loop as primary if we're in the main thread
        if is_main_thread:
            primary_loop = EventLoopManager.get_primary_loop()
            if not primary_loop or id(primary_loop) != id(self.loop):
                result = EventLoopManager.set_primary_loop(self.loop)
                if result:
                    self.app._loop_registered_as_primary = True
                    logger.info(f"Registered application loop {id(self.loop)} as primary in main thread")
        
        # Make sure this loop is set as the current event loop
        asyncio.set_event_loop(self.loop)
        
        # Initialize health check tracking
        self._last_loop_health_check = time.time()
        self._healthcheck_timer = QTimer()
        self._healthcheck_timer.timeout.connect(self._check_event_loop_health)
        # Run health check every 30 seconds
        self._healthcheck_timer.start(30000)
    
    def setup_background_thread(self):
        """Set up dedicated background thread for monitoring and processing."""
        from resources.events.loop_management import EventLoopManager
        
        def background_worker():
            """Background thread worker for monitoring systems."""
            # Create dedicated event loop for background processing
            background_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(background_loop)
            
            # Register this as the background loop
            EventLoopManager.set_background_loop(background_loop)
            
            logger.info(f"Started background processing thread with loop {id(background_loop)}")
            
            async def run_monitoring():
                """Run monitoring systems in background thread."""
                # Verify we're in the correct background loop context
                current_loop = asyncio.get_running_loop()
                expected_loop = EventLoopManager.get_background_loop()
                
                if current_loop != expected_loop:
                    logger.error(f"Background monitoring in wrong loop context: {id(current_loop)} vs {id(expected_loop)}")
                    raise RuntimeError("Background operations must stay in background loop")
                
                logger.info(f"Background monitoring starting in correct loop context: {id(current_loop)}")
                
                try:
                    # Start circuit breaker monitoring
                    if hasattr(self.app, 'circuit_registry'):
                        await self.app.circuit_registry.start_monitoring()
                    
                    # Start system monitoring
                    if hasattr(self.app, 'system_monitor'):
                        # System monitor starts its own monitoring loop
                        pass
                    
                    # Keep the background loop running
                    while not getattr(self, '_shutdown_background', False):
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    logger.error(f"Error in background monitoring: {e}", exc_info=True)
                finally:
                    logger.info("Background monitoring stopped")
            
            try:
                background_loop.run_until_complete(run_monitoring())
            except Exception as e:
                logger.error(f"Background thread error: {e}", exc_info=True)
            finally:
                background_loop.close()
                logger.info("Background thread terminated")
        
        # Start background thread
        self._background_thread = threading.Thread(target=background_worker, daemon=True)
        self._background_thread.start()
        self._shutdown_background = False
        
        logger.info("Background processing thread started")
    
    def register_task(self, coro) -> asyncio.Task:
        """Register and track an asyncio task with improved event loop handling."""
        try:
            # Try to get the running loop
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, get or create one
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop in this thread, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                logger.info(f"Created new event loop in thread {threading.get_ident()}")
        
        if isinstance(coro, asyncio.Task):
            task = coro
        else:
            task = loop.create_task(coro)
            
        # Add task lifecycle management
        def _on_task_complete(task):
            self._tasks.discard(task)
            # Check health after task completion
            if hasattr(self, "_last_loop_health_check") and time.time() - self._last_loop_health_check > 10:
                self._check_event_loop_health()
        
        task.add_done_callback(_on_task_complete)
        self._tasks.add(task)
        return task
    
    def _check_event_loop_health(self) -> Dict[str, Any]:
        """Perform health check on the event loop."""
        try:
            self._last_loop_health_check = time.time()
            current_thread = threading.get_ident()
            
            # Try to get the current event loop
            try:
                loop = asyncio.get_running_loop()
                loop_status = "running"
            except RuntimeError:
                try:
                    loop = asyncio.get_event_loop()
                    loop_status = "available"
                except RuntimeError:
                    logger.warning(f"No event loop available in thread {current_thread}")
                    # Create a new event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop_status = "created"
                    logger.info(f"Created new event loop in thread {current_thread} during health check")
            
            # Check if loop is closed
            if loop.is_closed():
                logger.warning(f"Event loop is closed in thread {current_thread}, creating new one")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop_status = "recreated"
            
            # Check number of pending tasks
            try:
                pending_tasks = len(asyncio.all_tasks(loop))
            except RuntimeError:
                pending_tasks = len(self._tasks)
                
            logger.debug(f"Event loop health: status={loop_status}, thread={current_thread}, "
                        f"pending_tasks={pending_tasks}, app_tasks={len(self._tasks)}")
            
            # Ensure event queue has a valid loop
            if hasattr(self.app, 'event_queue'):
                if not hasattr(self.app.event_queue, '_creation_thread_id'):
                    logger.warning("Event queue missing thread context attributes")
                elif self.app.event_queue._creation_thread_id != current_thread:
                    logger.debug(f"Event queue thread mismatch: queue={self.app.event_queue._creation_thread_id}, "
                                f"current={current_thread}")
            
            return {
                "status": loop_status,
                "thread_id": current_thread,
                "loop_id": id(loop),
                "pending_tasks": pending_tasks,
                "app_tasks": len(self._tasks),
                "timestamp": time.time()
            }
                
        except Exception as e:
            logger.error(f"Error checking event loop health: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def cleanup(self):
        """Clean up event management resources."""
        logger.info("Event manager cleanup initiated")
        
        # Stop background processing thread
        if hasattr(self, '_background_thread') and self._background_thread.is_alive():
            logger.info("Stopping background processing thread")
            self._shutdown_background = True
            self._background_thread.join(timeout=5.0)
            
        # Stop health check timer
        if hasattr(self, '_healthcheck_timer') and self._healthcheck_timer.isActive():
            self._healthcheck_timer.stop()
            
        # Cancel all async tasks
        for task in list(self._tasks):
            if not task.done() and not task.cancelled():
                task.cancel()
        
        logger.info("Event manager cleanup complete")