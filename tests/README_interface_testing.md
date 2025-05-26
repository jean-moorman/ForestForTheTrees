# Testing the Interface Module

This document provides guidance on testing the `interface.py` module and `interfaces` package in the FFTT system.

## Overview

The FFTT system includes two related interface components:

1. **interfaces package** - The primary implementation of all interfaces, organized in a package structure
2. **interface.py** - A compatibility layer that re-exports classes from the interfaces package

## Test Files

The following test files are included for testing interfaces:

1. `simple_interface_test.py` - Basic import and initialization tests with simplified dependencies
2. `test_functionality_interface.py` - Tests for FunctionalityInterface and FeatureInterface
3. `test_agent_interface_state_transitions.py` - Comprehensive tests for AgentInterface state transitions
4. `test_guideline_management.py` - Tests for guideline management functionality
5. `test_error_recovery_circuit_breakers.py` - Tests for error recovery and circuit breaker integration
6. `test_interface.py` - Original comprehensive interface tests (may need updates)

## Testing Guidelines

When testing interface components, consider the following:

### 1. Dependency Management

Interface classes have complex dependencies that need to be properly handled in tests:

```python
# Create required dependencies for testing
event_queue = EventQueue()
await event_queue.start()  # Must be started before use
state_manager = StateManager(event_queue)
context_manager = AgentContextManager(event_queue)
cache_manager = CacheManager(event_queue)
metrics_manager = MetricsManager(event_queue)
error_handler = ErrorHandler(event_queue)
memory_monitor = MemoryMonitor(event_queue)

# Create interface
interface = BaseInterface(
    "test_interface", 
    event_queue,
    state_manager,
    context_manager,
    cache_manager,
    metrics_manager,
    error_handler,
    memory_monitor
)
```

For simpler tests, you may use mocks:

```python
# Mock dependencies
mock_event_queue = MagicMock()
mock_state_manager = MagicMock()

# Create interface with minimal dependencies
interface = BaseInterface(
    "test_interface",
    mock_event_queue,
    mock_state_manager,
    None,  # context_manager
    None,  # cache_manager
    None,  # metrics_manager
    None,  # error_handler
    None   # memory_monitor
)
```

### 2. Asynchronous Testing

Most interface methods are asynchronous and require proper async testing:

```python
@pytest.mark.asyncio
async def test_async_interface_method(interface):
    # Initialize the interface
    await interface.ensure_initialized()
    
    # Test async methods
    result = await interface.some_async_method()
    assert result == expected_result
```

### 3. State Management

Interface state management requires careful handling in tests:

```python
# Set state
await interface.set_state(ResourceState.ACTIVE)

# Get state
current_state = await interface.get_state()
assert current_state == ResourceState.ACTIVE
```

For AgentInterface, use the agent state methods:

```python
# Set agent state
await agent_interface.set_agent_state(AgentState.PROCESSING)

# Get agent state
assert agent_interface.agent_state == AgentState.PROCESSING

# Verify resource state mapping
resource_state = await agent_interface.get_state()
assert resource_state == ResourceState.ACTIVE
```

### 4. Event Testing

Interface operations emit events that can be tested:

```python
# Clear event history before the operation
interface._event_queue._event_history.clear()

# Perform operation that emits an event
await interface.some_operation()

# Verify events
events = interface._event_queue._event_history
specific_events = [e for e in events if e.event_type == "EXPECTED_EVENT_TYPE"]
assert len(specific_events) >= 1
```

### 5. Mocking External Operations

When testing complex interface methods like `process_with_validation`, mock the external operations:

```python
# Mock agent.get_response
async def mock_get_response(*args, **kwargs):
    return {"message": "Test response", "status": "success"}

# Save original and patch
original_get_response = agent_interface.agent.get_response
agent_interface.agent.get_response = mock_get_response

try:
    # Test the method
    result = await agent_interface.process_with_validation(...)
    
    # Verify results
    assert result["status"] == "success"
    
finally:
    # Restore original method
    agent_interface.agent.get_response = original_get_response
```

## Common Issues and Solutions

1. **Event Queue Not Started**: Always start the event queue before using interfaces.
   ```python
   await event_queue.start()
   ```

2. **State Manager Dependencies**: State Manager requires special handling and may need to be mocked.
   ```python
   mock_state_manager = MagicMock()
   mock_state_manager.get_state.return_value = mock_state
   ```

3. **Async Function Mocking**: Mock async functions properly.
   ```python
   async_mock = AsyncMock()
   async_mock.return_value = desired_result
   ```

4. **Cleanup After Tests**: Ensure cleanup at the end of tests to prevent resource leaks.
   ```python
   await interface.cleanup()
   await event_queue.stop()
   ```

5. **CircuitBreaker Integration**: When testing interfaces with circuit breakers, consider using the CircuitBreakerRegistry.

## Interface Test Hierarchy

For maximum test coverage, consider testing interfaces at different levels:

1. **Unit Tests**: Test individual interface methods in isolation.
2. **Integration Tests**: Test interfaces with their dependencies.
3. **Behavioral Tests**: Test complete workflows involving interfaces.
4. **Error Handling Tests**: Test how interfaces handle various error conditions.
5. **Performance Tests**: Test interface performance under load (if applicable).

## Further Resources

- See existing test files for examples and patterns
- Consult interfaces documentation for implementation details
- Use pytest fixtures to simplify test setup