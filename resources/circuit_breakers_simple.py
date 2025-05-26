"""
Simplified Circuit Breaker implementation to avoid circular dependencies.

This module provides a simplified version of the circuit breaker pattern
without dependencies on event systems or event loops, preventing circular imports.
All synchronization is done with threading.RLock for consistent thread safety.
"""

from datetime import datetime, timedelta
import threading
import logging
from typing import Dict, Any, Optional, List, Callable, Awaitable
from enum import Enum
from dataclasses import dataclass, field

# Import only from common to avoid circular dependencies
from resources.common import CircuitBreakerConfig, HealthStatus, ResourceType

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """States for the circuit breaker pattern"""
    CLOSED = "CLOSED"    # Normal operation
    OPEN = "OPEN"        # Failing, rejecting requests
    HALF_OPEN = "HALF_OPEN"  # Testing if system has recovered

class CircuitOpenError(Exception):
    """Raised when circuit is open"""
    pass

class CircuitBreakerSimple:
    """Simplified implementation of the circuit breaker pattern without event dependencies"""
    def __init__(self,
                name: str,
                config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change = datetime.now()
        self.half_open_successes = 0
        self.active_half_open_calls = 0
        
        # State change listeners - using callback approach instead of event system
        self._state_change_listeners: List[Callable[[str, str, str], Awaitable[None]]] = []
        
        # Thread-safe lock for state changes
        self._lock = threading.RLock()
        
        # Protected exception types
        self.PROTECTED_EXCEPTIONS = (
            Exception,  # More specific exceptions can be added later
        )
        
    def add_state_change_listener(self, listener: Callable[[str, str, str], Awaitable[None]]) -> None:
        """Add a listener for state changes
        
        Args:
            listener: Callable that takes (circuit_name, old_state, new_state) and returns an awaitable
        """
        with self._lock:
            if listener not in self._state_change_listeners:
                self._state_change_listeners.append(listener)
                logger.debug(f"Added state change listener to circuit {self.name}")
    
    def remove_state_change_listener(self, listener: Callable[[str, str, str], Awaitable[None]]) -> None:
        """Remove a state change listener
        
        Args:
            listener: The listener to remove
        """
        with self._lock:
            if listener in self._state_change_listeners:
                self._state_change_listeners.remove(listener)
                logger.debug(f"Removed state change listener from circuit {self.name}")

    async def trip(self, reason: str = "Manual trip") -> bool:
        """Manually trip the circuit to OPEN state
        
        Args:
            reason: The reason for the manual trip
            
        Returns:
            bool: True if state changed, False otherwise
        """
        with self._lock:
            if self.state != CircuitState.OPEN:
                old_state = self.state.value
                self.state = CircuitState.OPEN
                self.last_state_change = datetime.now()
                logger.warning(f"Circuit {self.name} manually tripped to OPEN: {reason}")
                
                # Call listeners outside the lock
                listeners = list(self._state_change_listeners)
        
        # Notify listeners outside of lock
        for listener in listeners:
            try:
                await listener(self.name, old_state, CircuitState.OPEN.value)
            except Exception as e:
                logger.error(f"Error notifying state change listener for circuit {self.name}: {e}")
                
        return True
    
    async def reset(self) -> bool:
        """Manually reset the circuit to CLOSED state
        
        Returns:
            bool: True if state changed, False otherwise
        """
        listeners = []
        old_state = None
        state_changed = False
        
        with self._lock:
            if self.state != CircuitState.CLOSED:
                old_state = self.state.value
                self.state = CircuitState.CLOSED
                self.last_state_change = datetime.now()
                self.failure_count = 0
                logger.info(f"Circuit {self.name} manually reset to CLOSED")
                
                # Copy listeners inside lock
                listeners = list(self._state_change_listeners)
                state_changed = True
        
        # Notify listeners outside of lock
        if state_changed:
            for listener in listeners:
                try:
                    await listener(self.name, old_state, CircuitState.CLOSED.value)
                except Exception as e:
                    logger.error(f"Error notifying state change listener for circuit {self.name}: {e}")
                
        return state_changed
    
    async def execute(self, operation: Callable[[], Awaitable[Any]]) -> Any:
        """Execute operation with circuit breaker protection
        
        Args:
            operation: Async function to execute with circuit breaker protection
            
        Returns:
            Any: Result of the operation if successful
            
        Raises:
            CircuitOpenError: If the circuit is open and rejects the request
            Exception: Any exception raised by the operation
        """
        # Check state transitions with thread safety
        await self._check_state_transition()
        
        # Check if we should allow the operation (thread-safe)
        with self._lock:
            if self.state == CircuitState.OPEN:
                raise CircuitOpenError(f"Circuit {self.name} is OPEN")
                
            if self.state == CircuitState.HALF_OPEN:
                if self.active_half_open_calls >= self.config.half_open_max_tries:
                    raise CircuitOpenError(f"Circuit {self.name} max half-open tries exceeded")
            
            # Track active calls in half-open state
            if self.state == CircuitState.HALF_OPEN:
                self.active_half_open_calls += 1
        
        try:
            # Execute the operation outside the lock to avoid deadlocks
            result = await operation()
            
            # Update state based on success
            with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    self.half_open_successes += 1
                    if self.half_open_successes >= self.config.half_open_max_tries:
                        old_state = self.state.value
                        self.state = CircuitState.CLOSED
                        self.last_state_change = datetime.now()
                        self.failure_count = 0
                        
                        # Copy listeners
                        listeners = list(self._state_change_listeners)
            
            # Notify listeners outside lock if state changed to CLOSED
            if self.state == CircuitState.CLOSED and self.half_open_successes >= self.config.half_open_max_tries:
                for listener in listeners:
                    try:
                        await listener(self.name, old_state, CircuitState.CLOSED.value)
                    except Exception as e:
                        logger.error(f"Error notifying state change listener for circuit {self.name}: {e}")
                
            return result
            
        except Exception as e:
            # For test cases, we also handle ValueError
            if isinstance(e, self.PROTECTED_EXCEPTIONS) or isinstance(e, ValueError):
                await self._handle_failure(e)
            raise
            
        finally:
            # Always decrement active calls counter if in half-open state
            with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    self.active_half_open_calls = max(0, self.active_half_open_calls - 1)

    async def _check_state_transition(self) -> None:
        """Check and perform any needed state transitions with thread safety"""
        should_transition_to_half_open = False
        
        with self._lock:
            if self.state == CircuitState.OPEN:
                # Calculate elapsed time in seconds directly
                elapsed_seconds = (datetime.now() - self.last_state_change).total_seconds()
                if elapsed_seconds >= self.config.recovery_timeout:
                    should_transition_to_half_open = True
            
            # Clear old failures outside the window
            if self.last_failure_time:
                elapsed_failure_seconds = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed_failure_seconds >= self.config.failure_window:
                    self.failure_count = 0
        
        # If we need to transition, do it outside the lock
        if should_transition_to_half_open:
            old_state = CircuitState.OPEN.value
            
            with self._lock:
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = datetime.now()
                self.half_open_successes = 0
                self.active_half_open_calls = 0
                
                # Copy listeners
                listeners = list(self._state_change_listeners)
            
            # Notify listeners outside of lock
            for listener in listeners:
                try:
                    await listener(self.name, old_state, CircuitState.HALF_OPEN.value)
                except Exception as e:
                    logger.error(f"Error notifying state change listener for circuit {self.name}: {e}")

    async def _handle_failure(self, error: Exception) -> None:
        """Handle operation failure with thread safety"""
        transition_needed = False
        old_state = None
        
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                transition_needed = True
                old_state = self.state.value
            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    transition_needed = True
                    old_state = self.state.value
        
            # If transition is needed, do it within the lock
            if transition_needed:
                self.state = CircuitState.OPEN
                self.last_state_change = datetime.now()
                
                # Copy listeners
                listeners = list(self._state_change_listeners)
        
        # Notify listeners outside of lock
        if transition_needed:
            for listener in listeners:
                try:
                    await listener(self.name, old_state, CircuitState.OPEN.value)
                except Exception as e:
                    logger.error(f"Error notifying state change listener for circuit {self.name}: {e}")

@dataclass
class CircuitMetricsSimple:
    """Simplified metrics for a single circuit breaker"""
    state_durations: Dict[str, float] = field(default_factory=dict)  # state -> total duration
    error_timestamps: List[datetime] = field(default_factory=list)   # timestamps of errors
    recovery_times: List[float] = field(default_factory=list)        # time to recover in seconds
    last_state_change: Optional[datetime] = None

class ReliabilityMetricsSimple:
    """Simplified tracking of reliability-focused metrics for circuit breakers"""
    
    def __init__(self, metric_window: int = 3600):
        self._metric_window = metric_window  # window in seconds
        self._circuit_metrics: Dict[str, CircuitMetricsSimple] = {}
        self._lock = threading.RLock()  # Thread-safe lock

    def update_state_duration(self, circuit_name: str, state: str, 
                          duration: float) -> None:
        """Update time spent in a given state"""
        with self._lock:
            if circuit_name not in self._circuit_metrics:
                self._circuit_metrics[circuit_name] = CircuitMetricsSimple()
            
            metrics = self._circuit_metrics[circuit_name]
            metrics.state_durations[state] = (
                metrics.state_durations.get(state, 0) + duration
            )

    def record_error(self, circuit_name: str, error_time: datetime) -> None:
        """Record an error occurrence"""
        with self._lock:
            if circuit_name not in self._circuit_metrics:
                self._circuit_metrics[circuit_name] = CircuitMetricsSimple()
                
            self._circuit_metrics[circuit_name].error_timestamps.append(error_time)
            self._cleanup_old_errors(circuit_name)

    def record_recovery(self, circuit_name: str, recovery_time: float) -> None:
        """Record time taken to recover from failure"""
        with self._lock:
            if circuit_name not in self._circuit_metrics:
                self._circuit_metrics[circuit_name] = CircuitMetricsSimple()
                
            self._circuit_metrics[circuit_name].recovery_times.append(recovery_time)

    def get_error_density(self, circuit_name: str) -> float:
        """Calculate errors per minute in the current window"""
        with self._lock:
            if circuit_name not in self._circuit_metrics:
                return 0.0
                
            metrics = self._circuit_metrics[circuit_name]
            recent_errors = len(metrics.error_timestamps)
            return (recent_errors * 60) / self._metric_window if recent_errors > 0 else 0

    def get_avg_recovery_time(self, circuit_name: str) -> Optional[float]:
        """Get average recovery time for a circuit"""
        with self._lock:
            if circuit_name not in self._circuit_metrics:
                return None
                
            recovery_times = self._circuit_metrics[circuit_name].recovery_times
            return sum(recovery_times) / len(recovery_times) if recovery_times else None

    def get_state_duration(self, circuit_name: str, state: str) -> float:
        """Get total time spent in a given state"""
        with self._lock:
            if circuit_name not in self._circuit_metrics:
                return 0.0
            return self._circuit_metrics[circuit_name].state_durations.get(state, 0.0)
        
    def get_state_durations(self, circuit_name: str) -> Dict[str, float]:
        """Get complete history of time spent in each state"""
        with self._lock:
            if circuit_name not in self._circuit_metrics:
                return {}
            return dict(self._circuit_metrics[circuit_name].state_durations)

    def _cleanup_old_errors(self, circuit_name: str) -> None:
        """Remove errors outside the metric window"""
        # Lock already acquired by caller
        if circuit_name not in self._circuit_metrics:
            return
            
        cutoff = datetime.now() - timedelta(seconds=self._metric_window)
        metrics = self._circuit_metrics[circuit_name]
        metrics.error_timestamps = [
            t for t in metrics.error_timestamps if t > cutoff
        ]

class CircuitBreakerRegistrySimple:
    """
    Simplified registry for managing circuit breakers without event dependencies.
    
    This class provides a singleton pattern for creating, retrieving, and managing
    circuit breakers throughout the application. Unlike the full implementation,
    this simplified version avoids dependencies on the event system and other
    components that could create circular imports.
    """
    _instance = None
    _initialized = False
    _instance_lock = threading.RLock()
    
    @property
    def circuit_breakers(self) -> Dict[str, CircuitBreakerSimple]:
        """Return a dictionary of all registered circuit breakers."""
        with self._registry_lock:
            return dict(self._circuit_breakers)
    
    @property
    def circuit_names(self) -> List[str]:
        """Return a list of all circuit breaker names."""
        with self._registry_lock:
            return list(self._circuit_breakers.keys())
    
    def __new__(cls):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        with self._instance_lock:
            # Only update attributes if not initialized
            if not self._initialized:
                # Initialize with minimal dependencies
                self._circuit_breakers: Dict[str, CircuitBreakerSimple] = {}
                self._default_config = CircuitBreakerConfig()
                self._component_configs: Dict[str, CircuitBreakerConfig] = {}
                self._metrics = ReliabilityMetricsSimple()
                
                # Use threading.RLock() for thread safety
                self._registry_lock = threading.RLock()
                
                # Circuit breaker relationships
                self._dependencies = {}  # parent -> [children]
                self._reverse_dependencies = {}  # child -> [parents]
                
                # Circuit breaker metadata and state history
                self._circuit_metadata = {}
                self._state_history = {}
                
                # Event emitter callback - can be set later to avoid circular deps
                self._emit_event_callback = None
                self._health_tracker_callback = None
                self._state_manager_callback = None
                
                # Mark as initialized at the end once everything is ready
                self._initialized = True
                logger.debug("CircuitBreakerRegistrySimple initialized")
            else:
                # For already initialized instances, just log a debug message
                logger.debug("Reusing existing CircuitBreakerRegistrySimple instance")
    
    def set_event_emitter(self, emit_callback):
        """Set the event emitter callback to use for notifications"""
        self._emit_event_callback = emit_callback
    
    def set_health_tracker(self, health_tracker_callback):
        """Set the health tracker callback to use for health updates"""
        self._health_tracker_callback = health_tracker_callback
    
    def set_state_manager(self, state_manager_callback):
        """Set the state manager callback to use for persistence"""
        self._state_manager_callback = state_manager_callback
    
    def set_default_config(self, config: CircuitBreakerConfig) -> None:
        """Set the default circuit breaker configuration."""
        with self._registry_lock:
            self._default_config = config
    
    def register_component_config(self, component: str, config: CircuitBreakerConfig) -> None:
        """Register component-specific circuit breaker configuration."""
        with self._registry_lock:
            self._component_configs[component] = config
    
    async def register_circuit_breaker(self, name: str, circuit_breaker: CircuitBreakerSimple, parent: Optional[str] = None) -> None:
        """Register an existing circuit breaker.
        
        Args:
            name: The name of the circuit breaker
            circuit_breaker: The circuit breaker instance to register
            parent: Optional parent circuit breaker name that this one depends on
        """
        # Use thread-safe lock for registration
        with self._registry_lock:
            # Check if circuit breaker already exists with this name, avoiding duplicates
            if name in self._circuit_breakers:
                logger.warning(f"Circuit breaker with name '{name}' already registered. Skipping registration.")
                return
                
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
                        
                    logger.info(f"Registered dependency: {name} depends on {parent}")
        
        # Subscribe to state changes from the circuit breaker
        if hasattr(circuit_breaker, 'add_state_change_listener') and callable(circuit_breaker.add_state_change_listener):
            # First remove any existing listeners to avoid duplicate notifications
            if hasattr(circuit_breaker, 'remove_state_change_listener') and callable(circuit_breaker.remove_state_change_listener):
                circuit_breaker.remove_state_change_listener(self._handle_circuit_state_change)
            # Add our listener
            circuit_breaker.add_state_change_listener(self._handle_circuit_state_change)
        
        # Update health if callback is available
        if self._health_tracker_callback:
            await self._health_tracker_callback(
                f"circuit_breaker_{name}",
                HealthStatus(
                    status="HEALTHY",
                    source=f"circuit_breaker_{name}",
                    description=f"Circuit breaker {name} registered"
                )
            )
        
        logger.info(f"Registered circuit breaker: {name}")
        
        # Persist the circuit state if state manager callback is available
        if self._state_manager_callback:
            await self._state_manager_callback(name, self._get_circuit_state(name))
    
    async def _handle_circuit_state_change(self, circuit_name: str, old_state: str, new_state: str) -> None:
        """Handle circuit breaker state changes with cascading trip support.
        
        Args:
            circuit_name: Name of the circuit breaker that changed state
            old_state: Previous state name
            new_state: New state name
        """
        # Thread-safe update of state history
        with self._registry_lock:
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
            
            # Get list of children for cascading trips
            children = list(self._dependencies.get(circuit_name, []))
        
        # Emit event if callback is available
        if self._emit_event_callback:
            try:
                await self._emit_event_callback(
                    "system_health_changed",
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
        
        # Handle cascading trips outside of lock
        if new_state == "OPEN" and children:
            logger.warning(f"Cascading trip from {circuit_name} to children: {children}")
            
            # Trip child circuits
            for child_name in children:
                # Thread-safe access to circuit breaker
                child_circuit = None
                with self._registry_lock:
                    child_circuit = self._circuit_breakers.get(child_name)
                    
                if child_circuit and hasattr(child_circuit, 'trip') and callable(child_circuit.trip):
                    try:
                        await child_circuit.trip(f"Cascading trip from parent {circuit_name}")
                    except Exception as e:
                        logger.error(f"Error cascading trip to {child_name}: {e}")
        
        # Persist the state change if state manager callback is available
        if self._state_manager_callback:
            await self._state_manager_callback(circuit_name, self._get_circuit_state(circuit_name))
    
    def _get_circuit_state(self, circuit_name: str) -> Dict[str, Any]:
        """Get the current state of a circuit breaker for persistence"""
        with self._registry_lock:
            if circuit_name not in self._circuit_breakers:
                return {}
                
            circuit = self._circuit_breakers[circuit_name]
            
            # Prepare state data with thread safety
            with circuit._lock:
                state_data = {
                    "state": circuit.state.value,
                    "failure_count": circuit.failure_count,
                    "last_failure_time": circuit.last_failure_time.isoformat() if circuit.last_failure_time else None,
                }
                
            # Add dependency data
            state_data["children"] = self._dependencies.get(circuit_name, [])
            state_data["parents"] = self._reverse_dependencies.get(circuit_name, [])
            
            # Prepare metadata
            metadata = dict(self._circuit_metadata.get(circuit_name, {}))
            metadata.update({
                "last_saved": datetime.now().isoformat(),
                "component_type": circuit.__class__.__name__ if hasattr(circuit, "__class__") else "unknown"
            })
            
            return {
                "state": state_data,
                "metadata": metadata
            }
    
    async def get_or_create_circuit_breaker(
        self, 
        name: str, 
        component: Optional[str] = None,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreakerSimple:
        """Get an existing circuit breaker or create a new one if it doesn't exist.
        
        Args:
            name: The name of the circuit breaker
            component: Optional component context for config lookup
            config: Optional specific config override for this circuit breaker
            
        Returns:
            CircuitBreakerSimple: The requested circuit breaker instance
        """
        # First check if circuit already exists - thread safe
        with self._registry_lock:
            if name in self._circuit_breakers:
                return self._circuit_breakers[name]
            
            # Determine the configuration to use
            effective_config = config
            if effective_config is None and component is not None:
                effective_config = self._component_configs.get(component)
            if effective_config is None:
                effective_config = self._default_config
                
            # Create the circuit breaker
            circuit = CircuitBreakerSimple(name, effective_config)
            logger.info(f"Created circuit breaker: {name}")
        
        # Register the circuit breaker with listeners and callbacks (this will also add to _circuit_breakers)
        await self.register_circuit_breaker(name, circuit)
        
        return circuit
    
    async def get_circuit_breaker(self, name: str) -> Optional[CircuitBreakerSimple]:
        """Get an existing circuit breaker by name.
        
        Args:
            name: The name of the circuit breaker
            
        Returns:
            CircuitBreakerSimple or None: The requested circuit breaker or None if not found
        """
        # Thread-safe access to circuit breakers
        with self._registry_lock:
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
        # Get thread-safe copy of circuit names
        with self._registry_lock:
            circuit_names = list(self._circuit_breakers.keys())
        
        # Reset each circuit
        reset_count = 0
        for name in circuit_names:
            if await self.reset_circuit(name):
                reset_count += 1
        return reset_count
    
    async def register_dependency(self, child_name: str, parent_name: str) -> None:
        """Register a dependency relationship between circuit breakers.
        
        This creates a parent-child relationship where if the parent trips,
        the child will automatically trip as well.
        
        Args:
            child_name: Name of the dependent circuit breaker
            parent_name: Name of the circuit breaker that child depends on
        """
        # Thread-safe verification of circuit existence
        with self._registry_lock:
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
        
        # Save updated state if state manager callback is available
        if self._state_manager_callback:
            await self._state_manager_callback(parent_name, self._get_circuit_state(parent_name))
            await self._state_manager_callback(child_name, self._get_circuit_state(child_name))
    
    def get_circuit_status_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get a summary of all circuit breakers and their current status.
        
        Returns:
            Dict: A dictionary mapping circuit names to their status information
        """
        status = {}
        
        # Thread-safe access to circuit breakers
        with self._registry_lock:
            circuit_breakers_copy = dict(self._circuit_breakers)
            
        for name, breaker in circuit_breakers_copy.items():
            try:
                # Thread-safe access to circuit state
                with breaker._lock:
                    state_name = breaker.state.value
                    failure_count = breaker.failure_count
                    last_failure_time = breaker.last_failure_time
                
                # Get metrics with thread safety
                error_density = self._metrics.get_error_density(name)
                avg_recovery_time = self._metrics.get_avg_recovery_time(name)
                
                status[name] = {
                    "state": state_name,
                    "failure_count": failure_count,
                    "last_failure": last_failure_time.isoformat() 
                                if last_failure_time else None,
                    "error_density": error_density,
                    "avg_recovery_time": avg_recovery_time
                }
            except Exception as e:
                status[name] = {"error": str(e)}
                
        return status

# Convenient singleton access
def get_registry() -> CircuitBreakerRegistrySimple:
    """Get the singleton circuit breaker registry instance"""
    return CircuitBreakerRegistrySimple()