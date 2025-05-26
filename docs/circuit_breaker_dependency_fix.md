# Fixing Circuit Breaker Circular Dependencies

This document explains how the circular dependencies in the circuit breaker implementation have been resolved using a simplified implementation.

## Problem

The original circuit breaker implementation had circular dependencies:

1. `resources/monitoring/circuit_breakers.py` imported from `resources/events` modules
2. `resources/events/loop_management.py` imported from `resources/monitoring/circuit_breakers.py`
3. Circuit breakers depended on event queues, which themselves used circuit breakers for error handling

This created an import deadlock that could cause the application to fail during initialization.

## Solution

A simplified implementation of the circuit breaker pattern has been created that breaks these circular dependencies:

1. `resources/circuit_breakers_simple.py` provides:
   - `CircuitBreakerSimple` - a simplified circuit breaker implementation
   - `CircuitBreakerRegistrySimple` - a simplified registry for managing circuit breakers

### Key Features of the Simplified Implementation

1. **Minimal Dependencies**:
   - Only imports from `resources.common`, avoiding event system imports
   - Uses standard Python libraries for everything else

2. **Callback-Based Integration**:
   - Instead of direct dependencies, uses callbacks that can be set after initialization
   - Provides methods to set integration points:
     - `set_event_emitter(emit_callback)`
     - `set_health_tracker(health_tracker_callback)`
     - `set_state_manager(state_manager_callback)`

3. **Thread-Safe Synchronization**:
   - Uses `threading.RLock()` exclusively for thread safety
   - Avoids mixing asyncio and threading locks which can cause issues

4. **Full Functionality**:
   - Retains all core circuit breaker functionality
   - Supports state transitions, cascading trips, and circuit dependencies
   - Thread-safe operations for concurrent usage

## Usage

### Basic Usage

```python
from resources.circuit_breakers_simple import CircuitBreakerRegistrySimple

# Get the singleton registry instance
registry = CircuitBreakerRegistrySimple()

# Create and use a circuit breaker
async def main():
    circuit = await registry.get_or_create_circuit_breaker("my_service")
    
    # Execute an operation with circuit breaker protection
    result = await registry.circuit_execute(
        "my_service",
        lambda: my_async_operation()
    )
```

### Integration with Event Systems

```python
from resources.circuit_breakers_simple import CircuitBreakerRegistrySimple
from resources.events import EventQueue

# Get the registry and event queue
registry = CircuitBreakerRegistrySimple()
event_queue = EventQueue.get_instance()

# Set up integration AFTER both components are initialized
registry.set_event_emitter(event_queue.emit)
```

### Integration with Health Tracking

```python
from resources.circuit_breakers_simple import CircuitBreakerRegistrySimple
from resources.monitoring.health import HealthTracker

# Get the registry and health tracker
registry = CircuitBreakerRegistrySimple()
health_tracker = HealthTracker.get_instance()

# Set up integration AFTER both components are initialized
registry.set_health_tracker(health_tracker.update_health)
```

### Integration with State Management

```python
from resources.circuit_breakers_simple import CircuitBreakerRegistrySimple
from resources.state import StateManager

# Get the registry and state manager
registry = CircuitBreakerRegistrySimple()
state_manager = StateManager.get_instance()

# Set up integration AFTER both components are initialized
registry.set_state_manager(
    lambda name, state: state_manager.set_state(
        f"circuit_breaker_{name}", 
        state["state"], 
        metadata=state["metadata"]
    )
)
```

## Implementation Details

### Changes from Original Implementation

1. **Deferred Dependency Resolution**:
   - Dependencies are registered after initialization instead of at import time
   - Uses callback functions instead of direct class dependencies

2. **Event System Integration**:
   - Removed direct imports of event system classes
   - Added callback method to register event emission function

3. **State Management**:
   - Simplified state persistence with optional callback
   - State can be persisted through user-provided function

4. **Health Tracking**:
   - Optional health tracker integration through callback
   - Can be enabled/disabled based on application needs

5. **Thread Safety**:
   - Exclusively uses threading locks for thread safety
   - Careful lock management to prevent deadlocks

## Testing

A comprehensive test suite is provided in `tests/test_circuit_breaker_simple.py` that verifies:

1. Circuit breaker lifecycle (open, closed, half-open states)
2. Circuit dependency relationships and cascading trips
3. Concurrent operations and thread safety
4. Singleton registry pattern
5. Integration with mock components

An example integration is also available in `examples/circuit_breaker_integration.py` showing how to use the simplified implementation in a real application.

## Migration Guide

To migrate from the original implementation:

1. Update imports to use the simplified implementation:
   ```python
   # Before
   from resources.monitoring.circuit_breakers import CircuitBreaker, CircuitBreakerRegistry
   
   # After
   from resources.circuit_breakers_simple import CircuitBreakerSimple, CircuitBreakerRegistrySimple
   ```

2. Get the registry instance:
   ```python
   # Get singleton instance
   registry = CircuitBreakerRegistrySimple()
   ```

3. Register integration callbacks after initialization:
   ```python
   # Set up event integration
   registry.set_event_emitter(event_queue.emit)
   
   # Set up health tracking
   registry.set_health_tracker(health_tracker.update_health)
   
   # Set up state persistence
   registry.set_state_manager(lambda name, state: state_manager.save_state(f"circuit_breaker_{name}", state))
   ```

4. Use the registry as before:
   ```python
   # Create or get a circuit breaker
   circuit = await registry.get_or_create_circuit_breaker("my_service")
   
   # Execute with circuit breaker protection
   result = await registry.circuit_execute("my_service", my_async_operation)
   ```