"""
Event system monitoring for health tracking and diagnostics.

This module provides tools for monitoring event queues, tracking health metrics,
and diagnosing issues in the event system.
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

from .types import ResourceEventTypes, Event

logger = logging.getLogger(__name__)

class EventMonitor:
    """Monitors event system health and performance"""
    def __init__(self, event_queue):
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
                
    async def _check_health(self):
        """Check event system health metrics"""
        queue_sizes = self.event_queue.get_queue_size()
        total_queue_size = queue_sizes["total"]
        max_size = self.event_queue._max_size
        queue_percentage = total_queue_size / max_size if max_size > 0 else 0
        
        logger.debug(f"Health check: queue_size={total_queue_size}, max_size={max_size}, percentage={queue_percentage:.2f}")
        
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
        
        # Import here to avoid circular import
        from ..common import HealthStatus
        
        return HealthStatus(
            status=status,
            source="event_monitor",
            description=description,
            metadata={
                "queue_size": total_queue_size,
                "queue_percentage": queue_percentage,
                "total_subscribers": total_subscribers,
                "retry_count": len(self.event_queue._processing_retries)
            }
        )