"""
Circuit breaker pattern implementation for preventing cascading failures.

This module provides classes for implementing the circuit breaker pattern,
tracking reliability metrics, and managing circuit breakers through a centralized registry.
"""

from datetime import datetime, timedelta
import threading
from typing import Dict, Any, Optional, List, Callable, Awaitable
from enum import Enum, auto
import asyncio
import logging
from dataclasses import dataclass, field

from resources.common import CircuitBreakerConfig, HealthStatus, ResourceType
from resources.errors import ResourceError, ResourceExhaustionError, ResourceTimeoutError
from resources.events import ResourceEventTypes, EventQueue, EventLoopManager

logger = logging.getLogger(__name__)

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
    
    def __new__(cls, event_queue: EventQueue, health_tracker=None, state_manager=None):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, event_queue: EventQueue, health_tracker=None, state_manager=None):
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
            
            # Determine resource type
            try:
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