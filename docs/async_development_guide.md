# Async Development Guide for FFTT

This guide provides best practices for async development in FFTT to prevent event loop issues and ensure qasync compatibility.

## Quick Reference

### ✅ DO Use These Patterns

```python
# Use qasync-compatible timeout
from resources.events.qasync_utils import qasync_wait_for
result = await qasync_wait_for(operation(), timeout=30.0)

# Use qasync-compatible loop detection
from resources.events.qasync_utils import get_qasync_compatible_loop
loop = get_qasync_compatible_loop()

# Use standardized async patterns
from resources.events.async_patterns import safe_async_operation
result = await safe_async_operation(operation, timeout=30.0, retry_count=2)

# Use monitoring decorator
from resources.monitoring.async_diagnostics import async_monitor
@async_monitor("agent_processing")
async def process_agent():
    # ... implementation ...
```

### ❌ DON'T Use These Patterns

```python
# DON'T: Direct asyncio.wait_for() in GUI contexts
result = await asyncio.wait_for(operation(), timeout=30.0)  # Can fail with qasync

# DON'T: Direct asyncio.get_running_loop() without fallback
loop = asyncio.get_running_loop()  # Can fail in qasync contexts

# DON'T: Assume event loop context
asyncio.create_task(operation())  # May use wrong loop
```

## Background

FFTT uses a two-loop architecture:
- **Main Thread**: qasync event loop for Qt GUI integration
- **Background Thread**: Standard asyncio loop for processing

The integration between qasync and asyncio can cause "RuntimeError: no running event loop" when standard asyncio functions are used in qasync contexts.

## Core Principles

### 1. Always Use qasync-Compatible Functions

Replace standard asyncio functions with qasync-compatible alternatives:

| Instead of | Use |
|------------|-----|
| `asyncio.wait_for()` | `qasync_wait_for()` |
| `asyncio.get_running_loop()` | `get_qasync_compatible_loop()` |
| `asyncio.create_task()` | `loop.create_task()` where `loop = get_qasync_compatible_loop()` |

### 2. Use Defensive Programming

Always handle event loop detection failures gracefully:

```python
from resources.events.qasync_utils import get_qasync_compatible_loop

try:
    loop = get_qasync_compatible_loop()
    # Use loop for operations
except Exception as e:
    logger.error(f"Failed to get compatible loop: {e}")
    # Fallback behavior
```

### 3. Monitor Async Operations

Use the monitoring utilities to track async health:

```python
from resources.monitoring.async_diagnostics import async_monitor, diagnostics

@async_monitor("my_operation")
async def my_async_function():
    # Implementation
    pass

# Later, check health
report = diagnostics.get_health_report()
```

## Common Patterns

### Timeout Operations

```python
from resources.events.async_patterns import timeout_operation

async def my_long_operation():
    await some_work()
    return "result"

# Execute with timeout
result = await timeout_operation(my_long_operation, timeout=30.0)
```

### Concurrent Operations

```python
from resources.events.async_patterns import concurrent_operations

async def task_a():
    return "a"

async def task_b():
    return "b"

# Execute concurrently
results = await concurrent_operations(task_a(), task_b())
```

### Retry Logic

```python
from resources.events.async_patterns import safe_async_operation

async def unreliable_operation():
    # May fail occasionally
    pass

# Execute with retries
result = await safe_async_operation(
    unreliable_operation,
    timeout=10.0,
    retry_count=3
)
```

### Decorators for Common Patterns

```python
from resources.events.async_patterns import qasync_compatible, with_qasync_timeout

@qasync_compatible
@with_qasync_timeout(30.0)
async def my_function():
    # Automatically gets qasync compatibility and timeout
    pass
```

## Agent Interface Patterns

When working with agent interfaces, use these patterns:

### State Transitions

```python
# Good - uses qasync-compatible methods internally
await agent_interface.set_agent_state(AgentState.PROCESSING)

# The interface now handles loop detection internally
```

### Agent Processing

```python
# Good - uses qasync-compatible timeout internally
result = await agent_interface.process_with_validation(
    request_id="req_001",
    user_prompt="process this",
    timeout=60.0
)
```

## Testing Patterns

### Testing Async Functions

```python
import pytest
from resources.events.qasync_utils import get_qasync_compatible_loop

pytestmark = pytest.mark.asyncio

async def test_my_async_function():
    # Ensure we have a compatible loop
    loop = get_qasync_compatible_loop()
    assert loop is not None
    
    # Test the function
    result = await my_async_function()
    assert result == expected_value
```

### Integration Testing

```python
# Test real async integration without over-mocking
async def test_agent_interface_integration():
    # Use real EventQueue, mock only external dependencies
    event_queue = EventQueue("test")
    await event_queue.start()
    
    # Mock only what's necessary
    state_manager = Mock()
    state_manager.initialize = AsyncMock(return_value=True)
    
    # Test real integration
    interface = AgentInterface(
        agent_id="test",
        event_queue=event_queue,  # Real
        state_manager=state_manager  # Mocked
    )
    
    await interface.initialize()
    await interface.set_agent_state(AgentState.PROCESSING)
    
    await interface.terminate()
    await event_queue.stop()
```

## Debugging Async Issues

### Enable Async Diagnostics

```python
from resources.monitoring.async_diagnostics import log_async_health_report

# In your code, periodically log health
log_async_health_report()
```

### Check for Common Issues

```python
from resources.monitoring.async_diagnostics import diagnostics

# Get diagnostic report
issues = diagnostics.diagnose_event_loop_issues()
for issue in issues:
    logger.warning(f"Async issue: {issue}")
```

### Monitor Specific Operations

```python
from resources.monitoring.async_diagnostics import async_monitor

@async_monitor("critical_operation")
async def critical_async_operation():
    # This will be tracked for diagnostics
    pass
```

## Migration Guide

### Converting Existing Async Code

1. **Find asyncio.wait_for() calls**:
   ```bash
   grep -r "asyncio.wait_for" --include="*.py" .
   ```

2. **Replace with qasync_wait_for**:
   ```python
   # Before
   result = await asyncio.wait_for(operation(), timeout=30.0)
   
   # After
   from resources.events.qasync_utils import qasync_wait_for
   result = await qasync_wait_for(operation(), timeout=30.0)
   ```

3. **Update loop detection**:
   ```python
   # Before
   try:
       loop = asyncio.get_running_loop()
   except RuntimeError:
       loop = asyncio.new_event_loop()
   
   # After
   from resources.events.qasync_utils import get_qasync_compatible_loop
   loop = get_qasync_compatible_loop()
   ```

4. **Add monitoring**:
   ```python
   # Add to critical async functions
   from resources.monitoring.async_diagnostics import async_monitor
   
   @async_monitor("operation_name")
   async def my_function():
       # ... existing code ...
   ```

## Performance Considerations

### Loop Context Switching

- Avoid unnecessary loop context switches
- Use `get_qasync_compatible_loop()` once and reuse the reference
- Be aware that qasync loops may have different performance characteristics

### Timeout Values

- Use appropriate timeout values for different operation types:
  - GUI operations: 5-10 seconds
  - Agent processing: 30-120 seconds
  - Network operations: 10-30 seconds
  - File I/O: 5-15 seconds

### Monitoring Overhead

- Async monitoring has minimal overhead but avoid in tight loops
- Use diagnostics primarily for debugging and health checks
- Consider disabling detailed monitoring in production if performance is critical

## Troubleshooting

### "RuntimeError: no running event loop"

1. Check if you're using `asyncio.wait_for()` instead of `qasync_wait_for()`
2. Verify event loop detection with `get_qasync_compatible_loop()`
3. Check the async diagnostics for loop health issues

### Timeout Issues

1. Verify timeout values are appropriate for the operation
2. Check if operations are actually hanging vs timing out too quickly
3. Use async monitoring to track operation duration patterns

### Performance Problems

1. Check loop metrics for task count and health
2. Look for excessive loop context switching
3. Monitor operation duration and success rates

## Future Improvements

This async system can be extended with:

- Automatic asyncio API detection and warnings
- Performance profiling integration
- Circuit breaker patterns for external dependencies
- Distributed tracing for complex async workflows
- Automatic retry strategies based on error patterns