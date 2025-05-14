"""
Health tracking module for FFTT.

This module provides functionality for tracking and reporting health status
across system components, with support for subscribing to health updates.
"""

import logging
from typing import Dict, Any, Optional, Set, Callable, Awaitable

from resources.common import HealthStatus
from resources.events import ResourceEventTypes, EventQueue

logger = logging.getLogger(__name__)

class HealthTracker:
    """Tracks health status across system components"""
    def __init__(self, event_queue: EventQueue):
        self._event_queue = event_queue
        self._component_health: Dict[str, HealthStatus] = {}
        self._subscribers: Set[Callable[[str, HealthStatus], Awaitable[None]]] = set()
        
    async def subscribe(self, callback: Callable[[str, HealthStatus], Awaitable[None]]):
        """Subscribe to health updates"""
        self._subscribers.add(callback)
        
    async def unsubscribe(self, callback: Callable[[str, HealthStatus], Awaitable[None]]):
        """Unsubscribe from health updates"""
        self._subscribers.discard(callback)
        
    async def update_health(self, component: str, status: HealthStatus):
        """Update component health status"""
        self._component_health[component] = status
        
        # Notify subscribers
        for callback in self._subscribers:
            try:
                await callback(component, status)
            except Exception as e:
                logger.error(f"Error in health status callback: {str(e)}")
                
        # Emit health change event
        await self._event_queue.emit(
            ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
            {
                "component": component,
                "status": status.status,
                "description": status.description,
                "metadata": status.metadata,
                "timestamp": status.timestamp.isoformat()
            }
        )
        
    def get_component_health(self, component: str) -> Optional[HealthStatus]:
        """Get health status for specific component"""
        return self._component_health.get(component)
        
    def get_system_health(self) -> HealthStatus:
        """Get overall system health status"""
        if not self._component_health:
            return HealthStatus(
                status="UNKNOWN",
                source="health_tracker",
                description="No component health data available"
            )
            
        # Count components in each status
        status_counts = {}
        for health in self._component_health.values():
            status_counts[health.status] = status_counts.get(health.status, 0) + 1
            
        # Determine overall status
        if "CRITICAL" in status_counts:
            status = "CRITICAL"
            description = "One or more components in CRITICAL state"
        elif "UNHEALTHY" in status_counts:
            status = "UNHEALTHY"
            description = "One or more components UNHEALTHY"
        elif "DEGRADED" in status_counts:
            status = "DEGRADED"
            description = "One or more components DEGRADED"
        else:
            status = "HEALTHY"
            description = "All components healthy"
            
        return HealthStatus(
            status=status,
            source="health_tracker",
            description=description,
            metadata={"status_counts": status_counts}
        )
    
    async def stop(self):
        """No-op method to support shutdown sequence."""
        logger.info("HealthTracker shutdown")
        pass