"""
Phase Two Resource Manager Module.

This module implements the PhaseResourceManager class responsible for:
1. Memory utilization monitoring
2. Component prioritization based on system resources
3. Execution throttling for resource-intensive operations
4. Integration with system monitoring agents
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum

from resources.monitoring.memory import MemoryMonitor
from resources.monitoring.system import SystemMonitor
from resources.monitoring.health import HealthTracker
from resources.common import HealthStatus 
from resources.events.types import ResourceEventTypes
from resources.phase_coordinator.circuit_breakers import CircuitBreaker

logger = logging.getLogger(__name__)

class PhaseResourceManager:
    """
    Manager for phase two resource utilization and optimization.
    
    This class monitors system resources during phase two execution and
    optimizes resource allocation by prioritizing components, throttling
    execution when necessary, and integrating with system monitoring.
    """
    
    def __init__(
        self,
        event_queue: Any,
        memory_threshold: float = 0.85,
        cpu_threshold: float = 0.9,
        check_interval: float = 5.0,
        throttle_cooldown: float = 2.0
    ):
        """
        Initialize the PhaseResourceManager.
        
        Args:
            event_queue: Event queue for emitting resource-related events
            memory_threshold: Threshold (0.0-1.0) for memory utilization warnings
            cpu_threshold: Threshold (0.0-1.0) for CPU utilization warnings
            check_interval: Interval in seconds between resource checks
            throttle_cooldown: Cooldown time in seconds after throttling
        """
        self.event_queue = event_queue
        self.memory_threshold = memory_threshold
        self.cpu_threshold = cpu_threshold
        self.check_interval = check_interval
        self.throttle_cooldown = throttle_cooldown
        
        # Initialize monitoring components
        self.memory_monitor = MemoryMonitor()
        self.system_monitor = SystemMonitor()
        self.health_tracker = HealthTracker()
        
        # Resource throttling state
        self.throttled = False
        self.last_throttle_time = 0
        self.throttle_lock = asyncio.Lock()
        
        # Component prioritization tracking
        self.component_priorities: Dict[str, int] = {}
        self.resource_intensive_components: Set[str] = set()
        
        # Circuit breaker for resource protection
        self.resource_circuit_breaker = CircuitBreaker(
            name="phase_two_resources",
            failure_threshold=3,
            reset_timeout=30.0
        )

    async def initialize(self) -> None:
        """Initialize the resource manager and start monitoring."""
        logger.info("Initializing Phase Two resource manager")
        asyncio.create_task(self._resource_monitoring_loop())
        
    async def shutdown(self) -> None:
        """Stop the resource monitoring and shutdown the resource manager."""
        # This would require an event or flag to signal the monitoring loop to stop
        logger.info("Shutting down Phase Two resource manager")

    async def _resource_monitoring_loop(self) -> None:
        """Background task to periodically monitor system resources."""
        while True:
            try:
                # Get metrics from system monitor
                metrics = await self.system_monitor.collect_system_metrics()
                memory_usage = metrics.get("memory_usage", 0.0)
                cpu_usage = metrics.get("cpu_usage", 0.0)
                
                # Get health status
                health_result = await self.health_tracker.get_system_health()
                system_status = health_result.get("status", HealthStatus.UNKNOWN)
                
                await self._analyze_resource_metrics(memory_usage, cpu_usage, system_status)
                
                # Emit metrics event
                await self._emit_resource_metrics(memory_usage, cpu_usage, system_status)
                
            except Exception as e:
                logger.error(f"Error in resource monitoring loop: {str(e)}")
                
            await asyncio.sleep(self.check_interval)

    async def _analyze_resource_metrics(
        self, 
        memory_usage: float,
        cpu_usage: float,
        system_status: HealthStatus
    ) -> None:
        """
        Analyze current resource metrics and take appropriate actions.
        
        Args:
            memory_usage: Current memory usage as fraction (0.0-1.0)
            cpu_usage: Current CPU usage as fraction (0.0-1.0)
            system_status: Current system health status
        """
        # Check if we need to throttle based on resource usage
        if memory_usage > self.memory_threshold or cpu_usage > self.cpu_threshold:
            if not self.throttled:
                logger.warning(
                    f"Resource thresholds exceeded: memory={memory_usage:.2f}, "
                    f"CPU={cpu_usage:.2f}. Activating throttling."
                )
                await self._activate_throttling()
                
                # Trip circuit breaker if resources are critically low
                if memory_usage > 0.95 or cpu_usage > 0.95:
                    self.resource_circuit_breaker.trip()
                    
        # Reactivate if resource usage has improved and cooldown elapsed
        elif (self.throttled and 
              time.time() - self.last_throttle_time > self.throttle_cooldown):
            logger.info(
                f"Resource levels acceptable: memory={memory_usage:.2f}, "
                f"CPU={cpu_usage:.2f}. Deactivating throttling."
            )
            await self._deactivate_throttling()
            
            # Reset circuit breaker if it was tripped
            if self.resource_circuit_breaker.is_open():
                self.resource_circuit_breaker.reset()

    async def _activate_throttling(self) -> None:
        """Activate resource throttling to reduce system load."""
        async with self.throttle_lock:
            self.throttled = True
            self.last_throttle_time = time.time()
            
            # Emit throttling event
            await self.event_queue.emit(
                ResourceEventTypes.PHASE_TWO_THROTTLING_ACTIVATED.value,
                {
                    "timestamp": time.time(),
                    "reason": "Resource thresholds exceeded"
                }
            )

    async def _deactivate_throttling(self) -> None:
        """Deactivate resource throttling when system load decreases."""
        async with self.throttle_lock:
            self.throttled = False
            
            # Emit throttling deactivated event
            await self.event_queue.emit(
                ResourceEventTypes.PHASE_TWO_THROTTLING_DEACTIVATED.value,
                {
                    "timestamp": time.time()
                }
            )

    async def _emit_resource_metrics(
        self,
        memory_usage: float,
        cpu_usage: float,
        system_status: HealthStatus
    ) -> None:
        """
        Emit resource metrics as events.
        
        Args:
            memory_usage: Current memory usage as fraction (0.0-1.0)
            cpu_usage: Current CPU usage as fraction (0.0-1.0)
            system_status: Current system health status
        """
        await self.event_queue.emit(
            ResourceEventTypes.PHASE_TWO_RESOURCE_METRICS.value,
            {
                "timestamp": time.time(),
                "memory_usage": memory_usage,
                "cpu_usage": cpu_usage,
                "system_status": system_status.value,
                "throttled": self.throttled,
                "resource_circuit_breaker_status": (
                    "open" if self.resource_circuit_breaker.is_open() else "closed"
                )
            }
        )

    async def register_component(
        self, 
        component_id: str, 
        resource_intensive: bool = False,
        priority: int = 1
    ) -> None:
        """
        Register a component with the resource manager.
        
        Args:
            component_id: Unique identifier for the component
            resource_intensive: Whether this component requires significant resources
            priority: Priority level (higher means more important)
        """
        self.component_priorities[component_id] = priority
        
        if resource_intensive:
            self.resource_intensive_components.add(component_id)
            logger.info(f"Registered resource-intensive component: {component_id}")

    def should_throttle_component(self, component_id: str) -> bool:
        """
        Determine if a specific component should be throttled.
        
        Args:
            component_id: Unique identifier for the component
            
        Returns:
            True if the component should be throttled, False otherwise
        """
        # If we're not in throttling mode, no need to throttle
        if not self.throttled:
            return False
            
        # If the circuit breaker is tripped, throttle all components
        if self.resource_circuit_breaker.is_open():
            return True
            
        # If this is a high-priority component, don't throttle it
        priority = self.component_priorities.get(component_id, 1)
        if priority >= 3:  # High priority threshold
            return False
            
        # If this is a resource-intensive component, always throttle when in throttle mode
        if component_id in self.resource_intensive_components:
            return True
            
        # Default throttling behavior based on priority
        return priority < 2  # Throttle low priority components

    async def get_prioritized_components(
        self, 
        component_ids: List[str]
    ) -> List[str]:
        """
        Get a prioritized list of components based on current resource state.
        
        Args:
            component_ids: List of component IDs to prioritize
            
        Returns:
            List of component IDs sorted by priority (highest first)
        """
        # Sort components by priority (highest first)
        return sorted(
            component_ids,
            key=lambda cid: self.component_priorities.get(cid, 1),
            reverse=True
        )

    async def can_process_component(self, component_id: str = None) -> bool:
        """
        Check if a component can be processed based on current resource availability.
        
        Args:
            component_id: Optional ID of the component to check
            
        Returns:
            True if component can be processed, False if throttled
        """
        # Check current memory and CPU
        metrics = await self.system_monitor.collect_system_metrics()
        memory_usage = metrics.get("memory_usage", 0.0)
        cpu_usage = metrics.get("cpu_usage", 0.0)
        
        # If resources are critically low, don't process
        if memory_usage > 0.95 or cpu_usage > 0.95:
            logger.warning(f"Critical resource levels: memory={memory_usage:.2f}, CPU={cpu_usage:.2f}")
            return False
        
        # Check if throttled
        if self.throttled:
            # If component ID is provided and it's high priority, allow processing anyway
            if component_id and self.component_priorities.get(component_id, 1) >= 3:
                logger.info(f"Allowing high-priority component {component_id} despite throttling")
                return True
            logger.info(f"System is throttled, pausing component processing")
            return False
            
        # Check the circuit breaker
        if self.resource_circuit_breaker.is_open():
            logger.warning(f"Resource circuit breaker is open")
            return False
            
        # If we get here, component can be processed
        return True
    
    async def allocate_resources(
        self, 
        component_id: str,
        operation: str
    ) -> bool:
        """
        Attempt to allocate resources for a component operation.
        
        Args:
            component_id: ID of the component requesting resources
            operation: Description of the operation
            
        Returns:
            True if resources were allocated, False if throttled
        """
        # Check if this component should be throttled
        if self.should_throttle_component(component_id):
            logger.info(
                f"Throttling component {component_id} for operation '{operation}'"
            )
            return False
            
        # Check the circuit breaker
        if self.resource_circuit_breaker.is_open():
            logger.warning(
                f"Resource circuit breaker is open, denying resources for {component_id}"
            )
            return False
            
        # If we get here, resources can be allocated
        logger.debug(f"Resources allocated for {component_id} - {operation}")
        return True

    async def calculate_available_parallelism(self) -> int:
        """
        Calculate the current level of parallelism based on system resources.
        
        Returns:
            Integer value representing number of parallel operations possible
        """
        # Get metrics from system monitor
        metrics = await self.system_monitor.collect_system_metrics()
        memory_usage = metrics.get("memory_usage", 0.0)
        cpu_usage = metrics.get("cpu_usage", 0.0)
        
        # Base parallelism on available resources
        if memory_usage > 0.9 or cpu_usage > 0.9:
            return 1  # Critical - sequential only
        elif memory_usage > 0.75 or cpu_usage > 0.75:
            return 2  # High utilization - minimal parallelism
        elif memory_usage > 0.5 or cpu_usage > 0.5:
            return 4  # Moderate utilization
        else:
            return 8  # Low utilization - maximum parallelism
            
    async def track_resource_usage(
        self, 
        component_id: str,
        start_time: float,
        end_time: float,
        operation_type: str
    ) -> None:
        """
        Track resource usage statistics for a component operation.
        
        Args:
            component_id: ID of the component
            start_time: Start timestamp of the operation
            end_time: End timestamp of the operation
            operation_type: Type of operation performed
        """
        duration = end_time - start_time
        
        # Categorize resource-intensive components based on duration
        if duration > 10.0 and operation_type != "validation":
            self.resource_intensive_components.add(component_id)
            logger.info(
                f"Component {component_id} marked as resource-intensive "
                f"({duration:.2f}s for {operation_type})"
            )
            
        # Emit resource usage tracking event
        await self.event_queue.emit(
            ResourceEventTypes.PHASE_TWO_RESOURCE_USAGE.value,
            {
                "component_id": component_id,
                "operation_type": operation_type,
                "duration": duration,
                "start_time": start_time,
                "end_time": end_time,
                "resource_intensive": component_id in self.resource_intensive_components
            }
        )