"""
Memory monitoring functionality for FFTT.

This module provides a centralized memory monitoring system that tracks resource
sizes and emits alerts when configurable thresholds are exceeded.
"""

import asyncio
import logging
import threading
import psutil
from datetime import datetime
from typing import Dict, Any, Optional, Set

from resources.common import MemoryThresholds
from resources.events import ResourceEventTypes, EventQueue
from resources.monitoring.utils import with_memory_checking

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """Centralized memory monitoring system"""
    _instance = None
    _initialized = False
    _instance_lock = threading.RLock()
    
    @property
    def components(self):
        """Return a set of all registered component IDs."""
        return set(self._component_thresholds.keys())
    
    def __new__(cls, event_queue: EventQueue, thresholds: Optional[MemoryThresholds] = None):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance
        
    def __init__(self, event_queue: EventQueue, thresholds: Optional[MemoryThresholds] = None):
        # Always update the event queue reference even if already initialized
        self._event_queue = event_queue
        
        # Only initialize other attributes once
        if not getattr(type(self), '_initialized', False):
            self._thresholds = thresholds or MemoryThresholds()
            self._resource_sizes: Dict[str, float] = {}
            self._component_thresholds: Dict[str, MemoryThresholds] = {}
            self._monitoring_task: Optional[asyncio.Task] = None
            self._running = False
            self._check_interval = 60
            type(self)._initialized = True
        
        self._lock = asyncio.Lock()  # Add a lock for thread safety
    
    def register_component(self, component_id: str, thresholds: Optional[MemoryThresholds] = None):
        """Register component-specific thresholds"""
        self._component_thresholds[component_id] = thresholds or self._thresholds
    
    async def track_resource(self, resource_id: str, size_mb: float, component_id: str):
        """Track resource memory with component context"""
        async with self._lock:  # Use lock to prevent race conditions
            # Ensure event queue is processing events
            if not hasattr(self._event_queue, '_running') or not self._event_queue._running:
                await self._event_queue.start()
            
            old_size = self._resource_sizes.get(resource_id, 0)
            self._resource_sizes[resource_id] = size_mb
            
            # Check component-specific thresholds
            thresholds = self._component_thresholds.get(component_id, self._thresholds)
            if size_mb > thresholds.per_resource_max_mb:
                await self._emit_resource_alert(resource_id, size_mb, component_id)
                
            # Track component total memory
            await self._check_component_memory(component_id)
    
    async def untrack_resource(self, resource_id: str, component_id: str = None):
        """Async wrapper for remove_resource"""
        async with self._lock:  # Use lock to prevent race conditions
            logger.debug(f"Untracking resource {resource_id}")
            self.remove_resource(resource_id)

    async def _check_component_memory(self, component_id: str):
        """Check memory usage for specific component"""
        total_mb = sum(
            size for res_id, size in self._resource_sizes.items()
            if res_id.startswith(f"{component_id}:")
        )
        
        thresholds = self._component_thresholds.get(component_id, self._thresholds)
        if total_mb > thresholds.critical_percent:
            await self._emit_component_alert(component_id, total_mb, "CRITICAL")
        elif total_mb > thresholds.warning_percent:
            await self._emit_component_alert(component_id, total_mb, "WARNING")
            
    async def start(self):
        """Start memory monitoring"""
        self._running = True
        loop = asyncio.get_event_loop()
        self._monitoring_task = loop.create_task(self._monitor_memory())
        
    async def stop(self):
        """Stop memory monitoring"""
        self._running = False
        if self._monitoring_task:
            await self._monitoring_task
    
    async def _check_memory_once(self):
        """Check memory usage once"""
        try:
            # Get system memory usage using psutil
            memory = psutil.virtual_memory()
            used_percent = memory.percent / 100  # Convert to decimal
            total_mb = memory.total / (1024 * 1024)  # Convert to MB
            used_mb = memory.used / (1024 * 1024)    # Convert to MB
            
            # Check against configured thresholds
            if used_percent >= self._thresholds.critical_percent:
                await self._emit_memory_alert("CRITICAL", used_percent, used_mb)
                logger.warning(f"Memory usage CRITICAL: {used_percent:.1%}")
            elif used_percent >= self._thresholds.warning_percent:
                await self._emit_memory_alert("WARNING", used_percent, used_mb)
                logger.info(f"Memory usage WARNING: {used_percent:.1%}")
            
            # Check component-specific resource usage
            for component_id in self._component_thresholds.keys():
                await self._check_component_memory(component_id)
                
            try:
                # Emit regular memory status update
                await self._event_queue.emit(
                    ResourceEventTypes.METRIC_RECORDED,
                    {
                        "metric": "system_memory",
                        "total_mb": total_mb,
                        "used_mb": used_mb,
                        "used_percent": used_percent,
                        "resource_count": len(self._resource_sizes),
                        "tracked_mb": sum(self._resource_sizes.values()),
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as emit_error:
                logger.error(f"Error emitting memory metrics: {emit_error}", exc_info=True)
        except Exception as e:
            logger.error(f"Error in memory monitoring: {str(e)}")
            raise

    @with_memory_checking
    async def _monitor_memory(self):
        """Monitor overall system memory usage periodically"""
        logger.info(f"Memory monitoring started with {self._check_interval}s interval")
        
        # Allow direct testing by running the check once immediately
        await self._check_memory_once()
        
        while self._running:
            try:
                await self._check_memory_once()
            except Exception as e:
                logger.error(f"Error in memory monitoring: {str(e)}")
                # Continue monitoring despite errors
                
            # Wait for next check interval
            await asyncio.sleep(self._check_interval)
            
        logger.info("Memory monitoring stopped")

    async def _emit_component_alert(self, component_id: str, total_mb: float, level: str):
        """Emit component-specific memory alert using standardized method"""
        # Prepare event data
        event_data = {
            "alert_type": "component_memory",
            "component_id": component_id,
            "level": level,
            "total_mb": total_mb,
            "threshold_mb": self._component_thresholds.get(
                component_id, self._thresholds
            ).get_threshold_for_level(level),
            "timestamp": datetime.now().isoformat()
        }
        
        # Use standardized emission method
        await self._safe_emit_event(
            ResourceEventTypes.RESOURCE_ALERT_CREATED.value, 
            event_data,
            f"Component {component_id} memory {level}: {total_mb:.1f}MB"
        )
        
        # Log the alert
        logger.warning(f"Component {component_id} memory {level}: {total_mb:.1f}MB")
    
    async def _safe_emit_event(self, event_type: str, event_data: dict, context_msg: str):
        """Centralized event emission with consistent error handling"""
        try:
            logger.debug(f"Emitting {event_type} event: {context_msg}")
            await self._event_queue.emit(event_type, event_data)
            logger.debug(f"Successfully emitted {event_type} event: {context_msg}")
        except Exception as e:
            logger.error(f"Error emitting {event_type} event ({context_msg}): {str(e)}", exc_info=True)
            # Log but don't re-raise to maintain stability

    def register_resource_size(self, resource_id: str, size_mb: float):
        """Register or update resource size"""
        self._resource_sizes[resource_id] = size_mb
        
    def remove_resource(self, resource_id: str):
        """Remove resource from monitoring"""
        self._resource_sizes.pop(resource_id, None)
        
    async def _emit_memory_alert(self, level: str, percent: float, total_mb: float):
        """Emit memory alert event"""
        await self._event_queue.emit(
            ResourceEventTypes.RESOURCE_ALERT_CREATED.value,
            {
                "alert_type": "memory",
                "level": level,
                "percent": percent,
                "total_mb": total_mb,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    async def _emit_resource_alert(self, resource_id: str, size_mb: float, component_id: str):
        """Emit resource-specific memory alert using standardized method"""
        # Get component-specific thresholds
        thresholds = self._component_thresholds.get(component_id, self._thresholds)
        
        # Create the event payload
        event_data = {
            "alert_type": "resource_memory",
            "resource_id": resource_id,
            "size_mb": size_mb,
            "component_id": component_id,
            "threshold_mb": thresholds.per_resource_max_mb,
            "timestamp": datetime.now().isoformat()
        }
        
        # Use standardized emission method
        await self._safe_emit_event(
            ResourceEventTypes.RESOURCE_ALERT_CREATED.value,
            event_data,
            f"Resource {resource_id} memory exceeds threshold: {size_mb:.1f}MB > {thresholds.per_resource_max_mb:.1f}MB"
        )
        
        # Log the alert
        logger.warning(
            f"Resource {resource_id} memory exceeds threshold: {size_mb:.1f}MB > {thresholds.per_resource_max_mb:.1f}MB"
        )