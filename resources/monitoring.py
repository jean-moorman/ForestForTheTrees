from datetime import datetime, timedelta
import threading
from typing import Dict, Any, Optional, Set, Callable, Awaitable, List
from enum import Enum, auto
import asyncio
import logging
import psutil
from dataclasses import dataclass, field
import tracemalloc
import functools

from resources.common import HealthStatus, MemoryThresholds, CircuitBreakerConfig
from resources.errors import ResourceError, ResourceExhaustionError, ResourceTimeoutError
from resources.events import ResourceEventTypes, EventQueue

tracemalloc.start()
logger = logging.getLogger(__name__)

def with_memory_checking(func):
    """Decorator that provides the original function for testing."""
    @functools.wraps(func)
    async def wrapper(self):
        return await func(self)
    
    return wrapper
class CircuitState(Enum):
    """States for the circuit breaker pattern"""
    CLOSED = auto()    # Normal operation
    OPEN = auto()      # Failing, rejecting requests
    HALF_OPEN = auto() # Testing if system has recovered

class CircuitOpenError(Exception):
    """Raised when circuit is open"""
    pass

class CircuitBreaker:
    """Implementation of the circuit breaker pattern with state change notification support"""
    def __init__(self,
                 name: str,
                 event_queue: EventQueue,
                 config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self._event_queue = event_queue
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change = datetime.now()
        self.half_open_successes = 0
        self.active_half_open_calls = 0
        
        # State change listeners
        self._state_change_listeners: List[Callable[[str, str, str], Awaitable[None]]] = []
        
        # Protected exception types
        self.PROTECTED_EXCEPTIONS = (
            ResourceError,
            ResourceExhaustionError,
            ResourceTimeoutError
        )
        
    def add_state_change_listener(self, listener: Callable[[str, str, str], Awaitable[None]]) -> None:
        """Add a listener for state changes
        
        Args:
            listener: Callable that takes (circuit_name, old_state, new_state) and returns an awaitable
        """
        if listener not in self._state_change_listeners:
            self._state_change_listeners.append(listener)
            logger.debug(f"Added state change listener to circuit {self.name}")
    
    def remove_state_change_listener(self, listener: Callable[[str, str, str], Awaitable[None]]) -> None:
        """Remove a state change listener
        
        Args:
            listener: The listener to remove
        """
        if listener in self._state_change_listeners:
            self._state_change_listeners.remove(listener)
            logger.debug(f"Removed state change listener from circuit {self.name}")
    
    async def trip(self, reason: str = "Manual trip") -> None:
        """Manually trip the circuit to OPEN state
        
        Args:
            reason: The reason for the manual trip
        """
        if self.state != CircuitState.OPEN:
            old_state = self.state.name
            await self._transition_to_open(manual_reason=reason)
            logger.warning(f"Circuit {self.name} manually tripped to OPEN: {reason}")
            return True
        return False
    
    async def reset(self) -> None:
        """Manually reset the circuit to CLOSED state"""
        if self.state != CircuitState.CLOSED:
            old_state = self.state.name
            await self._transition_to_closed(manual_reason="Manual reset")
            logger.info(f"Circuit {self.name} manually reset to CLOSED")
            return True
        return False
        
    async def execute(self, operation: Callable[[], Awaitable[Any]]) -> Any:
        """Execute operation with circuit breaker protection"""
        await self._check_state_transition()
        
        if self.state == CircuitState.OPEN:
            raise CircuitOpenError(f"Circuit {self.name} is OPEN")
            
        if self.state == CircuitState.HALF_OPEN:
            if self.active_half_open_calls >= self.config.half_open_max_tries:
                raise CircuitOpenError(f"Circuit {self.name} max half-open tries exceeded")
                
        try:
            if self.state == CircuitState.HALF_OPEN:
                self.active_half_open_calls += 1
                
            result = await operation()
            
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_successes += 1
                if self.half_open_successes >= self.config.half_open_max_tries:
                    await self._transition_to_closed()
                    
            return result
            
        except Exception as e:
            if isinstance(e, self.PROTECTED_EXCEPTIONS):
                await self._handle_failure(e)
            raise
            
        finally:
            if self.state == CircuitState.HALF_OPEN:
                self.active_half_open_calls -= 1

    async def _check_state_transition(self) -> None:
        """Check and perform any needed state transitions"""
        if self.state == CircuitState.OPEN:
            # Calculate elapsed time in seconds directly
            elapsed_seconds = (datetime.now() - self.last_state_change).total_seconds()
            if elapsed_seconds >= self.config.recovery_timeout:
                await self._transition_to_half_open()
                    
        # Clear old failures outside the window
        if self.last_failure_time:
            elapsed_failure_seconds = (datetime.now() - self.last_failure_time).total_seconds()
            if elapsed_failure_seconds >= self.config.failure_window:
                self.failure_count = 0

    async def _handle_failure(self, error: Exception) -> None:
        """Handle operation failure"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            await self._transition_to_open()
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                await self._transition_to_open()

    async def _emit_state_change(self, new_state: CircuitState, details: Dict[str, Any] = None):
        """Emit circuit state change event"""
        await self._event_queue.emit(
            ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
            {
                "component": f"circuit_breaker_{self.name}",
                "state": new_state.name,
                "failure_count": self.failure_count,
                "details": details or {}
            }
        )
        
    async def _notify_state_change_listeners(self, old_state: str, new_state: str) -> None:
        """Notify all state change listeners of the state change
        
        Args:
            old_state: Previous state name
            new_state: New state name
        """
        for listener in self._state_change_listeners:
            try:
                await listener(self.name, old_state, new_state)
            except Exception as e:
                logger.error(f"Error notifying state change listener for circuit {self.name}: {e}")

    async def _transition_to_open(self, manual_reason: str = None) -> None:
        """Transition to OPEN state"""
        old_state = self.state.name
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.now()
        
        # Prepare reason for emitting event
        details = {"reason": manual_reason} if manual_reason else {"reason": "failure_threshold_exceeded"}
        
        # Emit state change event
        await self._emit_state_change(CircuitState.OPEN, details)
        logger.warning(f"Circuit {self.name} transitioned to OPEN: {details['reason']}")
        
        # Notify listeners
        await self._notify_state_change_listeners(old_state, self.state.name)

    async def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state"""
        old_state = self.state.name
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = datetime.now()
        self.half_open_successes = 0
        self.active_half_open_calls = 0
        
        # Emit state change event
        await self._emit_state_change(
            CircuitState.HALF_OPEN,
            {"reason": "recovery_timeout_elapsed"}
        )
        logger.info(f"Circuit {self.name} transitioned to HALF_OPEN")
        
        # Notify listeners
        await self._notify_state_change_listeners(old_state, self.state.name)

    async def _transition_to_closed(self, manual_reason: str = None) -> None:
        """Transition to CLOSED state"""
        old_state = self.state.name
        self.state = CircuitState.CLOSED
        self.last_state_change = datetime.now()
        self.failure_count = 0
        
        # Prepare reason for emitting event
        details = {"reason": manual_reason} if manual_reason else {"reason": "recovery_confirmed"}
        
        # Emit state change event
        await self._emit_state_change(CircuitState.CLOSED, details)
        logger.info(f"Circuit {self.name} transitioned to CLOSED: {details['reason']}")
        
        # Notify listeners
        await self._notify_state_change_listeners(old_state, self.state.name)

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


@dataclass
class CircuitMetrics:
    """Metrics for a single circuit breaker"""
    state_durations: Dict[str, float] = field(default_factory=dict)  # state -> total duration
    error_timestamps: List[datetime] = field(default_factory=list)   # timestamps of errors
    recovery_times: List[float] = field(default_factory=list)        # time to recover in seconds
    last_state_change: Optional[datetime] = None

class ReliabilityMetrics:
    """Tracks reliability-focused metrics for all circuit breakers"""
    
    def __init__(self, metric_window: int = 3600):
        self._metric_window = metric_window  # window in seconds
        self._circuit_metrics: Dict[str, CircuitMetrics] = {}

    def update_state_duration(self, circuit_name: str, state: str, 
                            duration: float) -> None:
        """Update time spent in a given state"""
        if circuit_name not in self._circuit_metrics:
            self._circuit_metrics[circuit_name] = CircuitMetrics()
        
        metrics = self._circuit_metrics[circuit_name]
        metrics.state_durations[state] = (
            metrics.state_durations.get(state, 0) + duration
        )

    def record_error(self, circuit_name: str, error_time: datetime) -> None:
        """Record an error occurrence"""
        if circuit_name not in self._circuit_metrics:
            self._circuit_metrics[circuit_name] = CircuitMetrics()
            
        self._circuit_metrics[circuit_name].error_timestamps.append(error_time)
        self._cleanup_old_errors(circuit_name)

    def record_recovery(self, circuit_name: str, recovery_time: float) -> None:
        """Record time taken to recover from failure"""
        if circuit_name not in self._circuit_metrics:
            self._circuit_metrics[circuit_name] = CircuitMetrics()
            
        self._circuit_metrics[circuit_name].recovery_times.append(recovery_time)

    def get_error_density(self, circuit_name: str) -> float:
        """Calculate errors per minute in the current window"""
        if circuit_name not in self._circuit_metrics:
            return 0.0
            
        metrics = self._circuit_metrics[circuit_name]
        recent_errors = len(metrics.error_timestamps)
        return (recent_errors * 60) / self._metric_window if recent_errors > 0 else 0

    def get_avg_recovery_time(self, circuit_name: str) -> Optional[float]:
        """Get average recovery time for a circuit"""
        if circuit_name not in self._circuit_metrics:
            return None
            
        recovery_times = self._circuit_metrics[circuit_name].recovery_times
        return sum(recovery_times) / len(recovery_times) if recovery_times else None

    def get_state_duration(self, circuit_name: str, state: str) -> float:
        """Get total time spent in a given state"""
        if circuit_name not in self._circuit_metrics:
            return 0.0
        return self._circuit_metrics[circuit_name].state_durations.get(state, 0.0)
        
    def get_state_durations(self, circuit_name: str) -> Dict[str, float]:
        """Get complete history of time spent in each state"""
        if circuit_name not in self._circuit_metrics:
            return {}
        return dict(self._circuit_metrics[circuit_name].state_durations)

    def _cleanup_old_errors(self, circuit_name: str) -> None:
        """Remove errors outside the metric window"""
        if circuit_name not in self._circuit_metrics:
            return
            
        cutoff = datetime.now() - timedelta(seconds=self._metric_window)
        metrics = self._circuit_metrics[circuit_name]
        metrics.error_timestamps = [
            t for t in metrics.error_timestamps if t > cutoff
        ]
@dataclass
class SystemMonitorConfig:
    """Configuration for system monitor"""
    check_interval: float = 60.0  # seconds
    memory_check_threshold: float = 0.85  # 85% memory threshold ( threshold for tracked resources against total memory, not system memory pressure)
    circuit_check_interval: float = 30.0  # seconds
    metric_window: int = 600  # 1 minute in seconds

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

class CircuitBreakerRegistry:
    """Centralized registry for managing circuit breakers across the application.
    
    This class provides a singleton pattern for creating, retrieving, and managing
    circuit breakers throughout the application, ensuring consistent configuration
    and monitoring.
    
    Features:
    - Centralized management of circuit breakers
    - Component-specific configuration
    - Health status monitoring and reporting
    - Circuit breaker state persistence
    - Dependency tracking between circuit breakers
    """
    _instance = None
    _initialized = False
    _instance_lock = threading.RLock()
    
    @property
    def circuit_breakers(self) -> Dict[str, CircuitBreaker]:
        """Return a dictionary of all registered circuit breakers."""
        return dict(self._circuit_breakers)
    
    @property
    def circuit_names(self) -> List[str]:
        """Return a list of all circuit breaker names."""
        return list(self._circuit_breakers.keys())
    
    def __new__(cls, event_queue: EventQueue, health_tracker: Optional[HealthTracker] = None, state_manager=None):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, event_queue: EventQueue, health_tracker: Optional[HealthTracker] = None, state_manager=None):
        # Always update the event queue reference even if already initialized
        self._event_queue = event_queue
        self._health_tracker = health_tracker
        self._state_manager = state_manager
        
        # Only initialize other attributes once
        if not getattr(type(self), '_initialized', False):
            self._circuit_breakers: Dict[str, CircuitBreaker] = {}
            self._default_config = CircuitBreakerConfig()
            self._component_configs: Dict[str, CircuitBreakerConfig] = {}
            self._metrics = ReliabilityMetrics()
            self._lock = asyncio.Lock()
            self._monitoring_task: Optional[asyncio.Task] = None
            self._running = False
            self._check_interval = 30.0  # seconds
            
            # Circuit breaker relationships
            self._dependencies = {}  # parent -> [children]
            self._reverse_dependencies = {}  # child -> [parents]
            
            # Circuit breaker metadata and state history
            self._circuit_metadata = {}
            self._state_history = {}
            
            # Task tracking for cleanup
            self._tasks = set()
            
            # Register with EventLoopManager for proper cleanup
            try:
                from resources.events import EventLoopManager
                EventLoopManager.register_resource("circuit_breaker_registry", self)
            except Exception as e:
                logger.warning(f"Error registering with EventLoopManager: {e}")
            
            # Mark as initialized
            type(self)._initialized = True
            
            # Attempt to load persisted state
            try:
                loop = asyncio.get_event_loop()
                load_task = loop.create_task(self.load_state())
                self._tasks.add(load_task)
                load_task.add_done_callback(lambda t: self._tasks.discard(t))
            except RuntimeError:
                logger.warning("No event loop available during CircuitBreakerRegistry initialization")
    
    def set_default_config(self, config: CircuitBreakerConfig) -> None:
        """Set the default circuit breaker configuration."""
        self._default_config = config
    
    def register_component_config(self, component: str, config: CircuitBreakerConfig) -> None:
        """Register component-specific circuit breaker configuration."""
        self._component_configs[component] = config
    
    async def register_circuit_breaker(self, name: str, circuit_breaker: CircuitBreaker, parent: Optional[str] = None) -> None:
        """Register an existing circuit breaker.
        
        Args:
            name: The name of the circuit breaker
            circuit_breaker: The circuit breaker instance to register
            parent: Optional parent circuit breaker name that this one depends on
        """
        async with self._lock:
            # Register circuit breaker
            self._circuit_breakers[name] = circuit_breaker
            
            # Initialize metadata
            if name not in self._circuit_metadata:
                self._circuit_metadata[name] = {
                    "registered_time": datetime.now().isoformat(),
                    "trip_count": 0,
                    "last_trip": None,
                    "last_reset": None,
                    "component_type": circuit_breaker.__class__.__name__ if hasattr(circuit_breaker, "__class__") else "unknown"
                }
            
            # Set up parent relationship if specified
            if parent:
                if parent not in self._circuit_breakers:
                    logger.warning(f"Parent circuit {parent} not found when registering {name}")
                else:
                    # Add to parent's children
                    if parent not in self._dependencies:
                        self._dependencies[parent] = []
                    if name not in self._dependencies[parent]:
                        self._dependencies[parent].append(name)
                    
                    # Add to reverse dependency mapping
                    if name not in self._reverse_dependencies:
                        self._reverse_dependencies[name] = []
                    if parent not in self._reverse_dependencies[name]:
                        self._reverse_dependencies[name].append(parent)
                        
                    logger.info(f"Registered circuit breaker {name} with parent {parent}")
            
            # Subscribe to state changes from the circuit breaker
            if hasattr(circuit_breaker, 'add_state_change_listener') and callable(circuit_breaker.add_state_change_listener):
                circuit_breaker.add_state_change_listener(self._handle_circuit_state_change)
            
            # Register with health tracker if available
            if self._health_tracker:
                await self._health_tracker.update_health(
                    f"circuit_breaker_{name}",
                    HealthStatus(
                        status="HEALTHY",
                        source=f"circuit_breaker_{name}",
                        description=f"Circuit breaker {name} registered"
                    )
                )
            
            logger.info(f"Registered circuit breaker: {name}")
            
            # Persist the circuit state
            await self.save_state(name)
    
    async def _handle_circuit_state_change(self, circuit_name: str, old_state: str, new_state: str) -> None:
        """Handle circuit breaker state changes with cascading trip support and state persistence.
        
        Args:
            circuit_name: Name of the circuit breaker that changed state
            old_state: Previous state name
            new_state: New state name
        """
        # Store state change in history
        if circuit_name not in self._state_history:
            self._state_history[circuit_name] = []
            
        self._state_history[circuit_name].append({
            "timestamp": datetime.now().isoformat(),
            "old_state": old_state,
            "new_state": new_state
        })
        
        # Limit history size
        if len(self._state_history[circuit_name]) > 100:
            self._state_history[circuit_name] = self._state_history[circuit_name][-100:]
        
        # Update metadata for trip events
        if new_state == "OPEN":
            if circuit_name in self._circuit_metadata:
                self._circuit_metadata[circuit_name]["trip_count"] = self._circuit_metadata[circuit_name].get("trip_count", 0) + 1
                self._circuit_metadata[circuit_name]["last_trip"] = datetime.now().isoformat()
        
        # For reset events
        if old_state == "OPEN" and new_state == "CLOSED":
            if circuit_name in self._circuit_metadata:
                self._circuit_metadata[circuit_name]["last_reset"] = datetime.now().isoformat()
        
        # Emit event for state change
        if self._event_queue:
            try:
                await self._event_queue.emit(
                    ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
                    {
                        "component": "circuit_breaker",
                        "circuit": circuit_name,
                        "old_state": old_state,
                        "new_state": new_state,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Error emitting circuit state change event: {e}")
        
        # Handle cascading trips: when a parent circuit trips, trip all children
        if new_state == "OPEN" and circuit_name in self._dependencies:
            children = self._dependencies[circuit_name]
            if children:
                logger.warning(f"Cascading trip from {circuit_name} to children: {children}")
                
                # Trip all child circuits
                for child_name in children:
                    child_circuit = self._circuit_breakers.get(child_name)
                    if child_circuit and hasattr(child_circuit, 'trip') and callable(child_circuit.trip):
                        try:
                            # Create task to trip the child circuit
                            loop = asyncio.get_event_loop()
                            task = loop.create_task(
                                child_circuit.trip(f"Cascading trip from parent {circuit_name}")
                            )
                            
                            # Track the task for cleanup
                            self._tasks.add(task)
                            task.add_done_callback(lambda t: self._tasks.discard(t))
                            
                        except Exception as e:
                            logger.error(f"Error cascading trip to {child_name}: {e}")
        
        # Persist the state change
        await self.save_state(circuit_name)
    
    async def get_or_create_circuit_breaker(
        self, 
        name: str, 
        component: Optional[str] = None,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get an existing circuit breaker or create a new one if it doesn't exist.
        
        Args:
            name: The name of the circuit breaker
            component: Optional component context for config lookup
            config: Optional specific config override for this circuit breaker
            
        Returns:
            CircuitBreaker: The requested circuit breaker instance
        """
        async with self._lock:
            if name in self._circuit_breakers:
                return self._circuit_breakers[name]
            
            # Determine the configuration to use
            effective_config = config
            if effective_config is None and component is not None:
                effective_config = self._component_configs.get(component)
            if effective_config is None:
                effective_config = self._default_config
                
            # Create the circuit breaker
            circuit = CircuitBreaker(name, self._event_queue, effective_config)
            self._circuit_breakers[name] = circuit
            
            # Register with health tracker if available
            if self._health_tracker:
                await self._health_tracker.update_health(
                    f"circuit_breaker_{name}",
                    HealthStatus(
                        status="HEALTHY",
                        source=f"circuit_breaker_{name}",
                        description=f"Circuit breaker {name} initialized"
                    )
                )
            
            logger.info(f"Created circuit breaker: {name}")
            return circuit
    
    async def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get an existing circuit breaker by name.
        
        Args:
            name: The name of the circuit breaker
            
        Returns:
            CircuitBreaker or None: The requested circuit breaker or None if not found
        """
        return self._circuit_breakers.get(name)
    
    async def circuit_execute(
        self,
        circuit_name: str,
        operation: Callable[[], Awaitable[Any]],
        component: Optional[str] = None,
        config: Optional[CircuitBreakerConfig] = None
    ) -> Any:
        """Execute an operation with circuit breaker protection, creating the circuit if needed.
        
        Args:
            circuit_name: The name of the circuit breaker to use
            operation: The async operation to execute
            component: Optional component context for config lookup
            config: Optional specific config for this circuit
            
        Returns:
            Any: The result of the operation if successful
            
        Raises:
            CircuitOpenError: If the circuit is open and rejects the request
            Exception: Any exception raised by the operation
        """
        circuit = await self.get_or_create_circuit_breaker(circuit_name, component, config)
        return await circuit.execute(operation)
    
    async def trip_circuit(self, name: str, reason: str = "Manual trip") -> bool:
        """Manually trip a circuit to OPEN state.
        
        Args:
            name: The name of the circuit breaker
            reason: The reason for the manual trip
            
        Returns:
            bool: True if the circuit was tripped, False if it was already open or doesn't exist
        """
        circuit = await self.get_circuit_breaker(name)
        if circuit:
            return await circuit.trip(reason)
        return False
    
    async def reset_circuit(self, name: str) -> bool:
        """Manually reset a circuit to CLOSED state.
        
        Args:
            name: The name of the circuit breaker
            
        Returns:
            bool: True if the circuit was reset, False if it was already closed or doesn't exist
        """
        circuit = await self.get_circuit_breaker(name)
        if circuit:
            return await circuit.reset()
        return False
    
    async def reset_all_circuits(self) -> int:
        """Reset all circuit breakers to CLOSED state.
        
        Returns:
            int: Number of circuits that were reset
        """
        reset_count = 0
        for name in list(self._circuit_breakers.keys()):
            if await self.reset_circuit(name):
                reset_count += 1
        return reset_count
    
    async def start_monitoring(self) -> None:
        """Start background monitoring of circuit breakers."""
        if self._running:
            return
            
        self._running = True
        loop = asyncio.get_event_loop()
        self._monitoring_task = loop.create_task(self._monitoring_loop())
        logger.info("Circuit breaker monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop background monitoring of circuit breakers."""
        if not self._running:
            return
            
        self._running = False
        if self._monitoring_task and not self._monitoring_task.done():
            try:
                self._monitoring_task.cancel()
                await asyncio.wait_for(self._monitoring_task, timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                logger.warning("Circuit breaker monitoring task cancellation timed out or was cancelled")
        
        # Persist circuit breaker states before stopping
        await self.save_state()
                
        logger.info("Circuit breaker monitoring stopped")
        
    async def _ensure_state_manager(self) -> bool:
        """Ensure state manager is available and initialized.
        
        Returns:
            bool: True if state manager is available, False otherwise
        """
        if self._state_manager is None:
            logger.warning("State manager not provided to CircuitBreakerRegistry")
            return False
            
        # Ensure state manager is initialized
        try:
            if hasattr(self._state_manager, 'ensure_initialized'):
                await self._state_manager.ensure_initialized()
            return True
        except Exception as e:
            logger.error(f"Error initializing state manager: {e}")
            return False
            
    async def load_state(self) -> None:
        """Load circuit breaker states from StateManager."""
        if not self._state_manager:
            logger.info("No state manager provided for circuit breaker state persistence")
            return
            
        if not await self._ensure_state_manager():
            logger.warning("Cannot load circuit breaker states: StateManager not available")
            return
            
        try:
            # Check if state manager has the right methods
            if not hasattr(self._state_manager, 'get_keys_by_prefix') or not hasattr(self._state_manager, 'get_state'):
                logger.warning("StateManager lacks required methods for circuit breaker state loading")
                return
                
            # Get all circuit breaker related resources 
            circuit_ids = await self._state_manager.get_keys_by_prefix("circuit_breaker_")
            
            for circuit_id in circuit_ids:
                # Extract actual circuit name from resource_id
                circuit_name = circuit_id.replace("circuit_breaker_", "")
                
                # Load state for this circuit
                state_entry = await self._state_manager.get_state(circuit_id)
                if not state_entry or not hasattr(state_entry, 'state') or not isinstance(state_entry.state, dict):
                    logger.warning(f"Invalid state data for circuit {circuit_name}")
                    continue
                
                # Get metadata from state
                circuit_state_data = state_entry.state
                circuit_metadata = getattr(state_entry, 'metadata', {}) or {}
                
                # Check if we already have this circuit registered
                if circuit_name in self._circuit_breakers:
                    # Update existing circuit based on persisted state
                    circuit = self._circuit_breakers[circuit_name]
                    
                    # Update circuit state
                    if "state" in circuit_state_data:
                        try:
                            state_name = circuit_state_data["state"]
                            if state_name == "OPEN":
                                await circuit.trip("Restored from persisted state")
                            elif state_name == "HALF_OPEN":
                                # First trip, then transition to HALF_OPEN
                                await circuit.trip("Intermediate state for restoration")
                                circuit.state = CircuitState.HALF_OPEN
                                circuit.last_state_change = datetime.now()
                            elif state_name == "CLOSED" and circuit.state != CircuitState.CLOSED:
                                await circuit.reset()
                        except Exception as e:
                            logger.error(f"Error restoring circuit state for {circuit_name}: {e}")
                    
                    # Update other circuit properties
                    if "failure_count" in circuit_state_data:
                        circuit.failure_count = circuit_state_data["failure_count"]
                    
                    if "last_failure_time" in circuit_state_data and circuit_state_data["last_failure_time"]:
                        try:
                            circuit.last_failure_time = datetime.fromisoformat(circuit_state_data["last_failure_time"])
                        except Exception as e:
                            logger.error(f"Error parsing last_failure_time for {circuit_name}: {e}")
                
                # Store metadata
                if circuit_name not in self._circuit_metadata:
                    self._circuit_metadata[circuit_name] = {}
                    
                # Update metadata from persisted state
                self._circuit_metadata[circuit_name].update({
                    "registered_time": circuit_metadata.get("registered_time", datetime.now().isoformat()),
                    "trip_count": circuit_metadata.get("trip_count", 0),
                    "last_trip": circuit_metadata.get("last_trip"),
                    "last_reset": circuit_metadata.get("last_reset"),
                    "last_loaded": datetime.now().isoformat()
                })
                
                # Populate relationships if present
                if "children" in circuit_state_data and circuit_state_data["children"]:
                    self._dependencies[circuit_name] = circuit_state_data["children"]
                    
                    # Also update reverse dependencies
                    for child in circuit_state_data["children"]:
                        if child not in self._reverse_dependencies:
                            self._reverse_dependencies[child] = []
                        if circuit_name not in self._reverse_dependencies[child]:
                            self._reverse_dependencies[child].append(circuit_name)
                
                logger.info(f"Loaded circuit breaker state for {circuit_name}")
                
            logger.info(f"Loaded {len(circuit_ids)} circuit breaker states from persistence")
            
        except Exception as e:
            logger.error(f"Error loading circuit breaker states: {e}")
    
    async def save_state(self, circuit_name: Optional[str] = None) -> None:
        """Save circuit breaker states to StateManager.
        
        Args:
            circuit_name: Optional name of specific circuit to save, or None to save all
        """
        if not self._state_manager:
            return
            
        if not await self._ensure_state_manager():
            logger.warning("Cannot save circuit breaker states: StateManager not available")
            return
            
        try:
            # Check if state manager has the right methods
            if not hasattr(self._state_manager, 'set_state'):
                logger.warning("StateManager lacks required methods for circuit breaker state persistence")
                return
            
            # Import ResourceType if it exists
            try:
                from resources.common import ResourceType
                resource_type = ResourceType.CIRCUIT_BREAKER 
            except (ImportError, AttributeError):
                resource_type = "circuit_breaker"
                
            # Determine which circuits to save
            circuits_to_save = [circuit_name] if circuit_name else list(self._circuit_breakers.keys())
            
            for name in circuits_to_save:
                if name not in self._circuit_breakers:
                    continue
                    
                circuit = self._circuit_breakers[name]
                
                # Prepare state data
                state_data = {
                    "state": circuit.state.name,
                    "failure_count": circuit.failure_count,
                    "last_failure_time": circuit.last_failure_time.isoformat() if circuit.last_failure_time else None,
                    "children": self._dependencies.get(name, []),
                    "parents": self._reverse_dependencies.get(name, [])
                }
                
                # Prepare metadata
                metadata = dict(self._circuit_metadata.get(name, {}))
                metadata.update({
                    "last_saved": datetime.now().isoformat(),
                    "component_type": circuit.__class__.__name__ if hasattr(circuit, "__class__") else "unknown"
                })
                
                # Generate resource_id for state manager
                resource_id = f"circuit_breaker_{name}"
                
                # Save to state manager
                await self._state_manager.set_state(
                    resource_id=resource_id,
                    state=state_data,
                    resource_type=resource_type,
                    metadata=metadata
                )
                
                logger.debug(f"Saved circuit breaker state for {name}")
                
            if not circuit_name:  # Only log for bulk operations
                logger.info(f"Saved {len(circuits_to_save)} circuit breaker states to persistence")
                
        except Exception as e:
            logger.error(f"Error saving circuit breaker states: {e}")
            
    async def register_dependency(self, child_name: str, parent_name: str) -> None:
        """Register a dependency relationship between circuit breakers.
        
        This creates a parent-child relationship where if the parent trips,
        the child will automatically trip as well.
        
        Args:
            child_name: Name of the dependent circuit breaker
            parent_name: Name of the circuit breaker that child depends on
        """
        # Verify both circuits exist
        if child_name not in self._circuit_breakers:
            logger.warning(f"Cannot create dependency: Child circuit {child_name} not found")
            return
            
        if parent_name not in self._circuit_breakers:
            logger.warning(f"Cannot create dependency: Parent circuit {parent_name} not found")
            return
            
        # Add to dependencies
        if parent_name not in self._dependencies:
            self._dependencies[parent_name] = []
            
        if child_name not in self._dependencies[parent_name]:
            self._dependencies[parent_name].append(child_name)
            
        # Add to reverse dependencies
        if child_name not in self._reverse_dependencies:
            self._reverse_dependencies[child_name] = []
            
        if parent_name not in self._reverse_dependencies[child_name]:
            self._reverse_dependencies[child_name].append(parent_name)
            
        logger.info(f"Registered dependency: {child_name} depends on {parent_name}")
        
        # Save updated state
        await self.save_state(parent_name)
        await self.save_state(child_name)
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop for circuit breakers."""
        while self._running:
            try:
                await self._check_all_circuits()
                await asyncio.sleep(self._check_interval)
            except Exception as e:
                logger.error(f"Error in circuit breaker monitoring loop: {e}")
                await asyncio.sleep(self._check_interval)
    
    async def _check_all_circuits(self) -> None:
        """Check status of all circuit breakers and collect metrics."""
        if not self._health_tracker:
            return
            
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
                await self._health_tracker.update_health(
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
    
    def get_circuit_status_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get a summary of all circuit breakers and their current status.
        
        Returns:
            Dict: A dictionary mapping circuit names to their status information
        """
        status = {}
        for name, breaker in self._circuit_breakers.items():
            try:
                status[name] = {
                    "state": breaker.state.name,
                    "failure_count": breaker.failure_count,
                    "last_failure": breaker.last_failure_time.isoformat() 
                                if breaker.last_failure_time else None,
                    "error_density": self._metrics.get_error_density(name),
                    "avg_recovery_time": self._metrics.get_avg_recovery_time(name)
                }
            except Exception as e:
                status[name] = {"error": str(e)}
                
        return status
        
# Export monitoring components
__all__ = [
    'CircuitBreaker',
    'CircuitState',
    'CircuitOpenError',
    'CircuitBreakerRegistry',
    'MemoryMonitor',
    'HealthTracker',
    'SystemMonitor',
    'SystemMonitorConfig'
]