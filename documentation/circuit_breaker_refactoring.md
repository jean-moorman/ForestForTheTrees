# Circuit Breaker Refactoring

## Problem: Circular Dependencies

The original circuit breaker implementation had circular dependencies between several components:

1. **resources/monitoring/circuit_breakers.py**
   - Imported from events system for event emission
   - Used by event system components including loop management

2. **resources/events/loop_management.py**
   - Depended on circuit breakers for error handling
   - Used by circuit breakers for thread safety

3. **system_error_recovery.py**
   - Imported circuit breakers from monitoring
   - Used by monitoring for system health

This created initialization issues and deadlocks, especially in multi-threaded environments, due to:
- Lock incompatibilities (threading vs asyncio locks)
- Import cycles preventing proper initialization
- Deadlocks during concurrent operations

## Solution: Simplified Circuit Breaker Implementation

The solution was to create a simplified circuit breaker implementation that:

1. **Avoids circular dependencies** by:
   - Using only basic Python imports (threading, logging, etc.)
   - Using callbacks instead of direct imports for integration
   - Maintaining consistent locking mechanisms

2. **Provides backward compatibility** by:
   - Maintaining the same interface as the original implementation
   - Re-exporting classes through the monitoring module
   - Supporting the same API with minimal changes

3. **Improves thread safety** by:
   - Using consistent threading.RLock() for all synchronization
   - Proper locking around state changes
   - Thread-safe singleton implementation

## Implementation Details

### New Files:

- **resources/circuit_breakers_simple.py**: Simplified implementation without circular dependencies
- **tests/test_circuit_breaker_simple.py**: Tests for the simplified implementation
- **tests/test_managers/test_circuit_breaker_registry_simple.py**: Registry tests for the simplified implementation

### Modified Files:

- **resources/monitoring/__init__.py**: Updated to re-export simplified classes
- **system_error_recovery.py**: Updated to use simplified implementation
- **resources/events/loop_management.py**: Updated to avoid circuit breaker dependencies

### Callback-Based Integration:

Instead of direct imports, the simplified implementation uses callbacks for integration:

```python
# Set callbacks instead of direct imports
registry = CircuitBreakerRegistrySimple()
registry.set_event_emitter(event_queue.emit)
registry.set_health_tracker(health_tracker.update_health)
registry.set_state_manager(state_manager.set_state)
```

### Thread Safety Improvements:

The simplified implementation uses consistent locking mechanisms:

```python
# Thread-safe lock for synchronization
self._lock = threading.RLock()

# Thread-safe singleton implementation
@classmethod
def __new__(cls):
    with cls._instance_lock:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
    return cls._instance
```

## Usage Example

```python
from resources.circuit_breakers_simple import (
    CircuitBreakerSimple,
    CircuitBreakerRegistrySimple,
    CircuitState
)

# Get the singleton registry
registry = CircuitBreakerRegistrySimple()

# Set callbacks
registry.set_event_emitter(event_queue.emit)

# Create or get a circuit breaker
circuit = await registry.get_or_create_circuit_breaker("my_circuit")

# Use with the execute method
result = await circuit.execute(my_async_operation)
```

## Testing

Tests have been added to verify the functionality of the simplified implementation:

1. Basic circuit breaker lifecycle
2. Thread safety and concurrent operations
3. Dependency relationships and cascading trips
4. Registry singleton behavior
5. Thread-safe operations

## Benefits

1. **Eliminated circular dependencies**: No more import cycles or initialization issues
2. **Improved thread safety**: Consistent locking mechanisms across the system
3. **Better maintainability**: Clearer separation of concerns with callback-based integration
4. **Backward compatibility**: Minimal changes required to existing code
5. **Simplified testing**: Easier to test in isolation without complex dependencies