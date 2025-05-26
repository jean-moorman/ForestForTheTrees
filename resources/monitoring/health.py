"""
Health tracking module for FFTT.

This module provides functionality for tracking and reporting health status
across system components, with support for subscribing to health updates.
"""

import logging
import threading
from typing import Dict, Any, Optional, Set, Callable, Awaitable

from resources.common import HealthStatus
from resources.events import ResourceEventTypes, EventQueue

logger = logging.getLogger(__name__)

class HealthTracker:
    """Tracks health status across system components with thread safety"""
    def __init__(self, event_queue: EventQueue):
        self._event_queue = event_queue
        self._component_health: Dict[str, HealthStatus] = {}
        self._subscribers: Set[Callable[[str, HealthStatus], Awaitable[None]]] = set()
        self._lock = threading.RLock()  # Thread-safe lock for component health access
        
        # Store thread affinity for proper thread boundary enforcement
        self._creation_thread_id = threading.get_ident()
        
        # Store the event loop for this component
        import asyncio
        from resources.events.loop_management import ThreadLocalEventLoopStorage
        try:
            loop = asyncio.get_event_loop()
            ThreadLocalEventLoopStorage.get_instance().set_loop(loop)
            logger.debug(f"HealthTracker initialized in thread {self._creation_thread_id} with loop {id(loop)}")
        except Exception as e:
            logger.warning(f"Could not store event loop for HealthTracker: {e}")
        
    async def subscribe(self, callback: Callable[[str, HealthStatus], Awaitable[None]]):
        """Subscribe to health updates"""
        with self._lock:
            self._subscribers.add(callback)
        
    async def unsubscribe(self, callback: Callable[[str, HealthStatus], Awaitable[None]]):
        """Unsubscribe from health updates"""
        with self._lock:
            self._subscribers.discard(callback)
        
    async def update_health(self, component: str, status: HealthStatus):
        """Update component health status with thread boundary enforcement"""
        # Verify thread affinity
        current_thread_id = threading.get_ident()
        if hasattr(self, '_creation_thread_id') and current_thread_id != self._creation_thread_id:
            # If called from wrong thread, delegate to correct thread
            from resources.events.loop_management import EventLoopManager
            try:
                loop = EventLoopManager.get_loop_for_thread(self._creation_thread_id)
                if loop:
                    logger.debug(f"Delegating health update for {component} to tracker thread {self._creation_thread_id}")
                    future = EventLoopManager.run_coroutine_threadsafe(
                        self._update_health_in_correct_thread(component, status),
                        target_loop=loop
                    )
                    return await asyncio.wrap_future(future)
            except Exception as e:
                logger.warning(f"Failed to delegate health update to correct thread: {e}")
                # Continue with current thread as fallback, but log the warning
        
        # Make a thread-safe copy of status in case original is modified
        status_copy = HealthStatus(
            status=status.status,
            source=status.source,
            description=status.description,
            timestamp=status.timestamp,
            metadata=dict(status.metadata) if status.metadata else None
        )
        
        # Store status and get subscribers in a thread-safe way
        with self._lock:
            # Store the status with thread ID information
            self._component_health[component] = status_copy
            
            # Create a copy of subscribers to avoid modifying during iteration
            subscribers = set(self._subscribers)
        
        # Notify subscribers (outside the lock to prevent deadlocks)
        for callback in subscribers:
            try:
                await callback(component, status_copy)
            except Exception as e:
                logger.error(f"Error in health status callback: {e}")
                
        # Emit health change event with thread information for debugging
        await self._event_queue.emit(
            ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
            {
                "component": component,
                "status": status_copy.status,
                "description": status_copy.description,
                "metadata": status_copy.metadata,
                "timestamp": status_copy.timestamp.isoformat(),
                "thread_id": current_thread_id
            }
        )
        
    def get_component_health(self, component: str) -> Optional[HealthStatus]:
        """Get health status for specific component"""
        with self._lock:
            return self._component_health.get(component)
        
    def get_system_health(self) -> HealthStatus:
        """Get overall system health status with optimized thread safety"""
        # Verify thread affinity - we don't delegate but we log the issue
        current_thread_id = threading.get_ident()
        if hasattr(self, '_creation_thread_id') and current_thread_id != self._creation_thread_id:
            logger.debug(f"get_system_health called from thread {current_thread_id}, but tracker created in thread {self._creation_thread_id}")
        
        # Use a single lock acquisition to minimize contention and avoid nested locks
        with self._lock:
            if not self._component_health:
                return HealthStatus(
                    status="UNKNOWN",
                    source="health_tracker",
                    description="No component health data available",
                    metadata={"thread_id": current_thread_id}
                )
            
            # Calculate counts while still under the lock for consistency
            # Optimization: count statuses directly rather than making a copy first
            status_counts = {}
            critical_count = 0
            unhealthy_count = 0
            degraded_count = 0
            
            for health in self._component_health.values():
                status = health.status
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Track critical statuses specifically
                if status == "CRITICAL":
                    critical_count += 1
                elif status == "UNHEALTHY":
                    unhealthy_count += 1
                elif status == "DEGRADED":
                    degraded_count += 1
        
        # Determine overall status
        if critical_count > 0:
            status = "CRITICAL"
            description = f"{critical_count} components in CRITICAL state"
        elif unhealthy_count > 0:
            status = "UNHEALTHY"
            description = f"{unhealthy_count} components UNHEALTHY"
        elif degraded_count > 0:
            status = "DEGRADED"
            description = f"{degraded_count} components DEGRADED"
        else:
            status = "HEALTHY"
            description = "All components healthy"
        
        # Include more detailed metrics
        total_components = sum(status_counts.values())
        healthy_count = total_components - critical_count - unhealthy_count - degraded_count
            
        return HealthStatus(
            status=status,
            source="health_tracker",
            description=description,
            metadata={
                "status_counts": status_counts,
                "total_components": total_components,
                "critical_count": critical_count,
                "unhealthy_count": unhealthy_count,
                "degraded_count": degraded_count,
                "healthy_count": healthy_count,
                "thread_id": current_thread_id
            }
        )
    
    async def stop(self):
        """No-op method to support shutdown sequence."""
        logger.info("HealthTracker shutdown")
        pass
        
    async def _update_health_in_correct_thread(self, component: str, status: HealthStatus):
        """Helper method for thread boundary enforcement to update health from the correct thread.
        
        This method should only be called via EventLoopManager.run_coroutine_threadsafe to maintain
        proper thread boundaries.
        """
        logger.debug(f"Health update for {component} running in thread {threading.get_ident()}")
        
        # Verify we're in the correct thread
        if threading.get_ident() != self._creation_thread_id:
            logger.error(f"_update_health_in_correct_thread running in wrong thread: {threading.get_ident()}, expected {self._creation_thread_id}")
        
        # Delegate to the main update method but skip the thread check
        # Make a thread-safe copy of status in case original is modified
        status_copy = HealthStatus(
            status=status.status,
            source=status.source,
            description=status.description,
            timestamp=status.timestamp,
            metadata=dict(status.metadata) if status.metadata else None
        )
        
        # Store status and get subscribers in a thread-safe way
        with self._lock:
            self._component_health[component] = status_copy
            subscribers = set(self._subscribers)
        
        # Notify subscribers (outside the lock to prevent deadlocks)
        for callback in subscribers:
            try:
                await callback(component, status_copy)
            except Exception as e:
                logger.error(f"Error in health status callback: {e}")
                
        # Emit health change event
        await self._event_queue.emit(
            ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
            {
                "component": component,
                "status": status_copy.status,
                "description": status_copy.description,
                "metadata": status_copy.metadata,
                "timestamp": status_copy.timestamp.isoformat(),
                "thread_id": threading.get_ident(),
                "delegated": True
            }
        )