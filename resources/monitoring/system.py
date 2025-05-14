"""
System-wide monitoring coordination module for FFTT.

This module provides the SystemMonitor class that coordinates various monitoring
components and provides a unified system health view.
"""

import asyncio
import logging
import psutil
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from resources.common import HealthStatus
from resources.events import ResourceEventTypes, EventQueue
from resources.monitoring.memory import MemoryMonitor
from resources.monitoring.health import HealthTracker
from resources.monitoring.circuit_breakers import CircuitBreakerRegistry, CircuitBreaker, ReliabilityMetrics

logger = logging.getLogger(__name__)

@dataclass
class SystemMonitorConfig:
    """Configuration for system monitor"""
    check_interval: float = 60.0  # seconds
    memory_check_threshold: float = 0.85  # 85% memory threshold
    circuit_check_interval: float = 30.0  # seconds
    metric_window: int = 600  # 10 minutes in seconds

class SystemMonitor:
    """Coordinates CircuitBreaker, MemoryMonitor, and HealthTracker components"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 memory_monitor: MemoryMonitor,
                 health_tracker: HealthTracker,
                 config: Optional[SystemMonitorConfig] = None):
        self.event_queue = event_queue
        self.memory_monitor = memory_monitor
        self.health_tracker = health_tracker
        self.config = config or SystemMonitorConfig()
        
        # Use CircuitBreakerRegistry for managing circuit breakers
        self._circuit_registry = CircuitBreakerRegistry(event_queue, health_tracker)
        self._circuit_breakers: Dict[str, 'CircuitBreaker'] = {}  # For backwards compatibility
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        self._metrics = ReliabilityMetrics(self.config.metric_window)
        self._shutdown = False  # Initialize _shutdown flag
        self._tasks: List[asyncio.Task] = []  # Initialize tasks list

    async def register_circuit_breaker(self, name: str, circuit_breaker: 'CircuitBreaker') -> None:
        """Register a circuit breaker for monitoring
        
        This method maintains backwards compatibility while integrating with CircuitBreakerRegistry.
        """
        # Keep reference in local dictionary for backwards compatibility
        self._circuit_breakers[name] = circuit_breaker
        
        # Make sure event queue is started
        if not hasattr(self.event_queue, '_running') or not self.event_queue._running:
            await self.event_queue.start()
            
        # Also register with the circuit breaker registry
        await self._circuit_registry.register_circuit_breaker(name, circuit_breaker)
        
        # Give the event processor a chance to process the emitted event
        await asyncio.sleep(0.1)

    async def _check_circuit_breakers(self) -> None:
        """Check status of all circuit breakers and collect reliability metrics
        
        Now uses the CircuitBreakerRegistry while maintaining backwards compatibility.
        """
        # Delegate circuit breaker checking to the registry if available
        if hasattr(self, '_circuit_registry') and self._circuit_registry:
            try:
                # Start registry monitoring if not already running
                if not self._circuit_registry._running:
                    await self._circuit_registry.start_monitoring()
                
                # Registry handles checking all circuit breakers
                return
            except Exception as e:
                logger.error(f"Error delegating to circuit registry: {e}")
                
        # Fallback to legacy behavior if registry fails or is unavailable
        current_time = datetime.now()
        
        for name, breaker in self._circuit_breakers.items():
            try:
                # Calculate time in current state
                duration = (current_time - breaker.last_state_change).total_seconds()
                self._metrics.update_state_duration(name, breaker.state.name, duration)

                # Record any new errors
                if breaker.last_failure_time:
                    self._metrics.record_error(name, breaker.last_failure_time)

                # Record recovery if transitioned to CLOSED
                if breaker.state.name == "CLOSED" and breaker.last_failure_time:
                    recovery_time = (current_time - breaker.last_failure_time).total_seconds()
                    self._metrics.record_recovery(name, recovery_time)

                # Determine health status
                status = "HEALTHY" if breaker.state.name == "CLOSED" else "DEGRADED"
                description = f"Circuit {name} is {breaker.state.name}"
                
                if breaker.state.name == "OPEN":
                    status = "CRITICAL"
                    description = (f"Circuit {name} is OPEN with {breaker.failure_count} "
                                 f"failures as of {breaker.last_failure_time}")

                # Update health with metrics
                await self.health_tracker.update_health(
                    f"circuit_breaker_{name}",
                    HealthStatus(
                        status=status,
                        source=f"circuit_breaker_{name}",
                        description=description,
                        metadata={
                            "state": breaker.state.name,
                            "failure_count": breaker.failure_count,
                            "last_failure": breaker.last_failure_time.isoformat() 
                                          if breaker.last_failure_time else None,
                            "error_density": self._metrics.get_error_density(name),
                            "time_in_state": duration,
                            "state_durations": self._metrics.get_state_durations(name),
                            "avg_recovery_time": self._metrics.get_avg_recovery_time(name)
                        }
                    )
                )
            except Exception as e:
                logger.error(f"Error checking circuit breaker {name}: {e}")

    async def start(self) -> None:
        """Start system monitoring"""
        if self._running:
            return

        self._running = True
        loop = asyncio.get_event_loop()
        self._monitoring_task = loop.create_task(self._monitoring_loop())
        logger.info("System monitoring started")

    async def stop(self) -> None:
        """Stop system monitoring"""
        if not self._running:
            return

        # Set running flag to False to stop the monitoring loop
        self._running = False

        # Flag to prevent processing new events during shutdown
        self._shutdown = True
        
        logger.info("Stopping SystemMonitor components")

        if self._monitoring_task and not self._monitoring_task.done():
            try:
                self._monitoring_task.cancel()
                try:
                    await asyncio.wait_for(self._monitoring_task, timeout=2.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    logger.warning("Monitoring task cancellation timed out or was cancelled")
            except Exception as e:
                logger.error(f"Error cancelling monitoring task: {e}")

        # Stop circuit breaker registry
        if hasattr(self, '_circuit_registry') and self._circuit_registry:
            try:
                logger.info("Stopping circuit breaker registry")
                await self._circuit_registry.stop_monitoring()
            except Exception as e:
                logger.error(f"Error stopping circuit breaker registry: {e}")

        # Stop memory monitor
        if hasattr(self, 'memory_monitor'):
            logger.info("Stopping memory monitor")
            await self.memory_monitor.stop()
        
        # Stop health tracker
        if hasattr(self, 'health_tracker'):
            logger.info("Stopping health tracker")
            await self.health_tracker.stop()
        
        # Cancel any pending tasks
        for task in getattr(self, '_tasks', []):
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete cancellation
        if hasattr(self, '_tasks'):
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        logger.info("SystemMonitor stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self._running:
            try:
                # Check memory status
                await self._check_memory_status()
                
                # Check circuit breakers
                await self._check_circuit_breakers()
                
                # Update overall system health
                await self._update_system_health()
                
                # Emit monitoring status
                await self._emit_monitoring_status()
                
                # Wait for next check interval
                await asyncio.sleep(self.config.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                # Emit error event but keep monitoring
                await self.event_queue.emit(
                    ResourceEventTypes.MONITORING_ERROR_OCCURRED.value,
                    {
                        "error": str(e),
                        "component": "system_monitor",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                await asyncio.sleep(self.config.check_interval)

    async def _check_memory_status(self) -> None:
        """Check tracked resource memory status"""
        try:
            # Use memory monitor to check status
            memory_status = await self._get_memory_status()
            
            # Update health tracker with memory status
            await self.health_tracker.update_health(
                "tracked_resource_memory",
                HealthStatus(
                    status="CRITICAL" if memory_status > self.config.memory_check_threshold else "HEALTHY",
                    source="memory_monitor",
                    description=f"Memory usage at {memory_status:.1%}",
                    metadata={"usage_percentage": memory_status}
                )
            )
        except Exception as e:
            logger.error(f"Error checking memory status: {e}")
            await self.health_tracker.update_health(
                "tracked_resource_memory",
                HealthStatus(
                    status="ERROR",
                    source="memory_monitor",
                    description=f"Failed to check memory: {str(e)}"
                )
            )

    async def _update_system_health(self) -> None:
        """Update overall system health status"""
        # Health tracker will aggregate component health statuses
        system_health = self.health_tracker.get_system_health()
        
        # Emit system health event
        await self.event_queue.emit(
            ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
            {
                "status": system_health.status,
                "description": system_health.description,
                "timestamp": datetime.now().isoformat(),
                "metadata": system_health.metadata
            }
        )

    async def collect_system_metrics(self) -> Dict[str, Any]:
        """
        Collect comprehensive system metrics.
        
        Returns:
            Dict with keys:
                - timestamp: ISO format timestamp
                - memory: Memory usage metrics
                - health: System health status 
                - circuits: Circuit breaker status
                - resources: Resource usage metrics
        """
        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "memory": {},
                "health": {},
                "circuits": {},
                "resources": {}
            }
            
            # Collect memory metrics
            try:
                memory_usage = await self._get_memory_status()
                system_memory = None
                
                if hasattr(psutil, 'virtual_memory'):
                    try:
                        vm = psutil.virtual_memory()
                        system_memory = {
                            "total_mb": vm.total / (1024 * 1024),
                            "available_mb": vm.available / (1024 * 1024),
                            "used_mb": vm.used / (1024 * 1024),
                            "percent": vm.percent / 100.0  # Convert to decimal
                        }
                    except Exception as e:
                        logger.error(f"Error getting system memory: {e}")
                
                metrics["memory"] = {
                    "tracked_usage": memory_usage,
                    "system": system_memory,
                    "resources_count": len(self.memory_monitor._resource_sizes) if hasattr(self, "memory_monitor") else 0,
                    "tracked_mb": sum(self.memory_monitor._resource_sizes.values()) if hasattr(self, "memory_monitor") else 0
                }
            except Exception as e:
                logger.error(f"Error collecting memory metrics: {e}")
                metrics["memory"] = {"error": str(e)}
            
            # Collect health metrics
            try:
                if hasattr(self, 'health_tracker'):
                    system_health = self.health_tracker.get_system_health()
                    metrics["health"] = {
                        "status": system_health.status,
                        "description": system_health.description,
                        "component_count": len(self.health_tracker._component_health) if hasattr(self.health_tracker, "_component_health") else 0,
                        "components": {
                            component: status.status
                            for component, status in self.health_tracker._component_health.items()
                        } if hasattr(self.health_tracker, "_component_health") else {}
                    }
                else:
                    metrics["health"] = {"status": "UNKNOWN", "description": "Health tracker not available"}
            except Exception as e:
                logger.error(f"Error collecting health metrics: {e}")
                metrics["health"] = {"error": str(e)}
            
            # Collect circuit breaker metrics
            try:
                if hasattr(self, '_circuit_registry') and self._circuit_registry:
                    metrics["circuits"] = self._circuit_registry.get_circuit_status_summary()
                elif hasattr(self, '_circuit_breakers'):
                    metrics["circuits"] = {
                        name: {
                            "state": breaker.state.name,
                            "failure_count": breaker.failure_count,
                            "last_failure": breaker.last_failure_time.isoformat() if breaker.last_failure_time else None
                        }
                        for name, breaker in self._circuit_breakers.items()
                    }
                else:
                    metrics["circuits"] = {"status": "No circuit breakers registered"}
            except Exception as e:
                logger.error(f"Error collecting circuit metrics: {e}")
                metrics["circuits"] = {"error": str(e)}
            
            # Collect resource metrics if available
            try:
                if hasattr(self, 'memory_monitor') and hasattr(self.memory_monitor, '_resource_sizes'):
                    # Group resources by component/category
                    by_component = {}
                    for resource_id, size in self.memory_monitor._resource_sizes.items():
                        component = resource_id.split(':')[0] if ':' in resource_id else 'other'
                        if component not in by_component:
                            by_component[component] = {"count": 0, "total_mb": 0}
                        by_component[component]["count"] += 1
                        by_component[component]["total_mb"] += size
                    
                    metrics["resources"] = by_component
                else:
                    metrics["resources"] = {"status": "No resource tracking available"}
            except Exception as e:
                logger.error(f"Error collecting resource metrics: {e}")
                metrics["resources"] = {"error": str(e)}
            
            # Emit metrics data via event system
            try:
                await self.event_queue.emit(
                    ResourceEventTypes.METRIC_RECORDED.value,
                    {
                        "metric": "system_metrics",
                        "timestamp": metrics["timestamp"],
                        "value": 1.0,  # Always record this was collected
                        "data": {  # Only include summary data in event
                            "memory_usage": metrics["memory"].get("tracked_usage", 0),
                            "health_status": metrics["health"].get("status", "UNKNOWN"),
                            "circuit_count": len(metrics["circuits"]) if isinstance(metrics["circuits"], dict) and "error" not in metrics["circuits"] else 0,
                            "resource_count": metrics["memory"].get("resources_count", 0)
                        }
                    }
                )
            except Exception as e:
                logger.error(f"Error emitting metrics event: {e}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}", exc_info=True)
            # Return minimal metrics in case of error
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "memory": {},
                "health": {},
                "circuits": {}
            }

    async def _emit_monitoring_status(self) -> None:
        """Emit overall monitoring status"""
        if not hasattr(self.event_queue, '_running') or not self.event_queue._running:
            await self.event_queue.start()

        try:
            # Use collect_system_metrics to get consistent data
            status = await self.collect_system_metrics()
            
            # Use SYSTEM_HEALTH_CHANGED instead of MONITORING_STATUS
            try:
                await self.event_queue.emit(
                    ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
                    {
                        "component": "system_monitor", 
                        "status": "monitoring_data",
                        "data": status
                    }
                )
            except Exception as emit_error:
                # Detailed error logging
                logger.error(f"Error emitting monitoring status: {emit_error}", exc_info=True)
                logger.error(f"Failed status data: {status}")
                
        except Exception as e:
            # Use ERROR_OCCURRED instead of SYSTEM_ERROR
            logger.error(f"Error preparing monitoring status: {e}", exc_info=True)
            try:
                await self.event_queue.emit(
                    ResourceEventTypes.MONITORING_ERROR_OCCURRED.value,
                    {
                        "error": str(e),
                        "component": "system_monitor",
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as emit_error:
                logger.error(f"Failed to emit error event: {emit_error}", exc_info=True)

    async def _get_memory_status(self) -> Optional[float]:
        """Get current memory usage as a percentage of tracked resources against total available memory.
        
        This maintains a consistent resource-centric approach where:
        - The numerator is always the sum of tracked application resources
        - The denominator is either configured total memory or system total memory
        
        Returns:
            float: Percentage (as decimal) of tracked resources against total memory,
                or None if an error occurs
        """
        try:
            # Calculate total of tracked application resources
            tracked_mb = sum(self.memory_monitor._resource_sizes.values())
            
            # If no resources are tracked, return 0%
            if not tracked_mb:
                return 0.0
            
            # Try to get total memory from configuration
            total_memory_mb = getattr(self.memory_monitor._thresholds, 'total_memory_mb', None)
            
            # If total memory is not configured or is zero, get it from the system
            if not total_memory_mb:
                memory = psutil.virtual_memory()
                # Convert total system memory from bytes to MB
                total_memory_mb = memory.total / (1024 * 1024)
            
            # Protect against division by zero
            if total_memory_mb <= 0:
                logger.warning("Total memory calculation resulted in zero or negative value")
                return 0.0
                
            # Calculate percentage of tracked resources against total memory
            return tracked_mb / total_memory_mb
                
        except Exception as e:
            logger.error(f"Error getting memory status: {e}", exc_info=True)
            return None