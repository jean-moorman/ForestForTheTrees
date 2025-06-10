from datetime import datetime
from typing import Dict, Any, Optional, List, Set
import asyncio
import logging
import threading

from resources.events import ResourceEventTypes, EventQueue

# Import qasync utilities for event loop compatibility
try:
    from resources.events.qasync_utils import qasync_wait_for
except ImportError:
    qasync_wait_for = asyncio.wait_for

logger = logging.getLogger(__name__)

class CircuitBreakerRegistry:
    """Centralized registry for circuit breakers with relationship tracking and cascading failures."""
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls, event_queue=None):
        """Singleton implementation with thread safety."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CircuitBreakerRegistry, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
            
    def __init__(self, event_queue=None):
        """Initialize circuit breaker registry."""
        # Only initialize once
        if self._initialized:
            return
            
        with self._lock:
            if not self._initialized:
                # Store event queue
                self._event_queue = event_queue
                
                # Circuit breaker storage
                self._circuit_breakers = {}
                self._relationships = {}  # parent -> [children]
                self._reverse_dependencies = {}  # child -> [parents]
                
                # Circuit breaker metadata
                self._circuit_metadata = {}
                
                # Circuit state changes
                self._state_history = {}
                
                # Task tracking for cleanup
                self._tasks = set()
                
                # Track registry in EventLoopManager for proper cleanup
                from resources.events import EventLoopManager
                EventLoopManager.register_resource("circuit_breaker_registry", self)
                
                self._initialized = True
                logger.debug("CircuitBreakerRegistry initialized")
    
    async def register_circuit_breaker(self, name: str, circuit, parent=None):
        """Register a circuit breaker with optional dependency on parent.
        
        Args:
            name: Unique identifier for the circuit breaker
            circuit: The CircuitBreaker instance
            parent: Optional parent circuit breaker name that this one depends on
        """
        # Import here to avoid circular imports
        from resources.monitoring import CircuitBreaker
        with self._lock:
            # Register circuit breaker
            self._circuit_breakers[name] = circuit
            
            # Store metadata
            self._circuit_metadata[name] = {
                "registered_time": datetime.now().isoformat(),
                "trip_count": 0,
                "last_trip": None,
                "last_reset": None,
                "component_type": circuit.__class__.__name__ if hasattr(circuit, "__class__") else "unknown"
            }
            
            # Set up parent relationship if specified
            if parent:
                # Add to parent's children
                if parent not in self._relationships:
                    self._relationships[parent] = []
                if name not in self._relationships[parent]:
                    self._relationships[parent].append(name)
                
                # Add to reverse dependency mapping
                if name not in self._reverse_dependencies:
                    self._reverse_dependencies[name] = []
                if parent not in self._reverse_dependencies[name]:
                    self._reverse_dependencies[name].append(parent)
            
            # Subscribe to state changes from the circuit breaker
            if hasattr(circuit, 'add_state_change_listener') and callable(circuit.add_state_change_listener):
                circuit.add_state_change_listener(self._handle_circuit_state_change)
            
            logger.info(f"Registered circuit breaker {name}" + (f" with parent {parent}" if parent else ""))
            
            # If event queue is available, emit registration event
            if self._event_queue:
                try:
                    await self._event_queue.emit(
                        ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
                        {
                            "component": "circuit_breaker_registry",
                            "status": "circuit_registered",
                            "circuit": name,
                            "parent": parent,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                except Exception as e:
                    logger.error(f"Error emitting circuit registration event: {e}")
    
    async def _handle_circuit_state_change(self, circuit_name, old_state, new_state):
        """Handle circuit breaker state changes with cascading trip support."""
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
                self._circuit_metadata[circuit_name]["trip_count"] += 1
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
        if new_state == "OPEN" and circuit_name in self._relationships:
            children = self._relationships[circuit_name]
            if children:
                logger.warning(f"Cascading trip from {circuit_name} to children: {children}")
                
                # Trip all child circuits
                for child_name in children:
                    child_circuit = self._circuit_breakers.get(child_name)
                    if child_circuit and hasattr(child_circuit, 'trip') and callable(child_circuit.trip):
                        try:
                            # Create task to trip the child circuit
                            task = asyncio.create_task(
                                child_circuit.trip(f"Cascading trip from parent {circuit_name}")
                            )
                            
                            # Track the task for cleanup
                            self._tasks.add(task)
                            task.add_done_callback(lambda t: self._tasks.discard(t))
                            
                        except Exception as e:
                            logger.error(f"Error cascading trip to {child_name}: {e}")
        
        # For recovery, we don't cascade automatically - each circuit follows its own recovery timeout
    
    async def get_circuit_status(self, name=None):
        """Get status of one or all circuit breakers.
        
        Args:
            name: Optional circuit breaker name, or None for all circuits
            
        Returns:
            Dictionary with circuit status information
        """
        if name:
            # Return status for specific circuit
            circuit = self._circuit_breakers.get(name)
            if not circuit:
                return {"error": f"Circuit {name} not found"}
                
            return {
                "name": name,
                "state": circuit.state.name if hasattr(circuit, 'state') else "UNKNOWN",
                "failure_count": circuit.failure_count if hasattr(circuit, 'failure_count') else 0,
                "metadata": self._circuit_metadata.get(name, {}),
                "parents": self._reverse_dependencies.get(name, []),
                "children": self._relationships.get(name, [])
            }
        else:
            # Return status for all circuits
            result = {}
            for circuit_name, circuit in self._circuit_breakers.items():
                result[circuit_name] = {
                    "state": circuit.state.name if hasattr(circuit, 'state') else "UNKNOWN",
                    "failure_count": circuit.failure_count if hasattr(circuit, 'failure_count') else 0,
                    "metadata": self._circuit_metadata.get(circuit_name, {}),
                    "parents": self._reverse_dependencies.get(circuit_name, []),
                    "children": self._relationships.get(circuit_name, [])
                }
            return result
    
    async def reset_all_circuits(self):
        """Reset all circuit breakers to CLOSED state."""
        reset_count = 0
        
        for name, circuit in self._circuit_breakers.items():
            if hasattr(circuit, 'reset') and callable(circuit.reset):
                try:
                    await circuit.reset()
                    reset_count += 1
                    
                    # Update metadata
                    if name in self._circuit_metadata:
                        self._circuit_metadata[name]["last_reset"] = datetime.now().isoformat()
                        
                except Exception as e:
                    logger.error(f"Error resetting circuit {name}: {e}")
        
        # Emit event for reset operation
        if self._event_queue:
            try:
                await self.event_bus.emit(
                    ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
                    {
                        "component": "circuit_breaker_registry",
                        "operation": "reset_all",
                        "reset_count": reset_count,
                        "total_circuits": len(self._circuit_breakers),
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Error emitting circuit reset event: {e}")
                
        return {"reset_count": reset_count, "total_circuits": len(self._circuit_breakers)}
    
    async def start_monitoring(self):
        """Start circuit breaker monitoring in background loop context."""
        from resources.events.loop_management import EventLoopManager
        
        # Ensure we're in the correct loop context
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None
        
        # Get the background loop
        background_loop = EventLoopManager.get_background_loop()
        
        # If we're not in the background loop, submit to it
        if current_loop != background_loop and background_loop:
            logger.info("Delegating start_monitoring to background loop")
            return await asyncio.wrap_future(
                asyncio.run_coroutine_threadsafe(self.start_monitoring(), background_loop)
            )
        
        # We're in the correct loop context, start monitoring
        if hasattr(self, '_monitoring_task') and self._monitoring_task and not self._monitoring_task.done():
            logger.debug("Circuit breaker monitoring already running")
            return
        
        try:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            self._tasks.add(self._monitoring_task)
            logger.info("Circuit breaker monitoring started")
        except Exception as e:
            logger.error(f"Error starting circuit breaker monitoring: {e}", exc_info=True)
            raise
    
    async def _monitoring_loop(self):
        """Background monitoring loop for circuit breakers."""
        try:
            while not getattr(self, '_shutdown_monitoring', False):
                try:
                    # Check circuit breaker health
                    await self._check_circuit_health()
                    
                    # Check for cascade failures
                    await self._check_cascade_conditions()
                    
                    # Sleep between checks
                    await asyncio.sleep(5.0)  # Check every 5 seconds
                    
                except asyncio.CancelledError:
                    logger.debug("Circuit breaker monitoring cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in circuit breaker monitoring loop: {e}", exc_info=True)
                    await asyncio.sleep(1.0)  # Brief pause before retry
                    
        finally:
            logger.info("Circuit breaker monitoring loop stopped")
    
    async def _check_circuit_health(self):
        """Check health of all registered circuit breakers."""
        with self._lock:
            circuits_to_check = list(self._circuit_breakers.items())
        
        for name, circuit in circuits_to_check:
            try:
                # Basic health check - ensure circuit is responsive
                if hasattr(circuit, 'is_healthy') and callable(circuit.is_healthy):
                    is_healthy = await circuit.is_healthy()
                    if not is_healthy:
                        logger.warning(f"Circuit breaker {name} health check failed")
                        
                        # Emit health change event
                        if self._event_queue:
                            await self._event_queue.emit(
                                ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
                                {
                                    "component": f"circuit_breaker_{name}",
                                    "status": "unhealthy",
                                    "timestamp": datetime.now().isoformat()
                                }
                            )
            except Exception as e:
                logger.error(f"Error checking health of circuit breaker {name}: {e}")
    
    async def _check_cascade_conditions(self):
        """Check for conditions that might trigger cascade failures."""
        with self._lock:
            # Check for multiple related circuits in OPEN state
            open_circuits = []
            for name, circuit in self._circuit_breakers.items():
                if hasattr(circuit, 'state') and circuit.state == "OPEN":
                    open_circuits.append(name)
            
            # If we have multiple open circuits, emit cascade warning
            if len(open_circuits) >= 2:
                if self._event_queue:
                    await self._event_queue.emit(
                        ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
                        {
                            "component": "circuit_breaker_registry",
                            "status": "cascade_risk",
                            "open_circuits": open_circuits,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
    
    async def stop_monitoring(self):
        """Stop circuit breaker monitoring."""
        self._shutdown_monitoring = True
        
        if hasattr(self, '_monitoring_task') and self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            
        logger.info("Circuit breaker monitoring stopped")
    
    async def stop(self):
        """Clean up resources."""
        # Cancel any pending tasks
        for task in list(self._tasks):
            if not task.done():
                task.cancel()
                
        # Wait for tasks to complete with timeout
        if self._tasks:
            try:
                await qasync_wait_for(
                    asyncio.gather(*self._tasks, return_exceptions=True),
                    timeout=2.0
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for circuit breaker tasks to cancel")
        
        # Simplified cleanup - no need to unregister in simplified architecture
        logger.debug("CircuitBreakerRegistry cleanup complete")
        
        logger.info("CircuitBreakerRegistry stopped")