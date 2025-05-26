"""
Tests for error recovery and circuit breaker functionality in the interface module.
"""

import pytest
import asyncio
import pytest_asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import logging
import sys
import time
from datetime import datetime, timedelta
import json
import random

# Import real implementations instead of creating mocks
from resources import (
    ResourceType, 
    ResourceState, 
    CircuitBreakerConfig, 
    EventQueue, 
    StateManager, 
    AgentContextManager,
    CacheManager,
    MetricsManager,
    ErrorHandler,
    MemoryMonitor
)

from resources.monitoring.circuit_breakers import (
    CircuitState,
    CircuitBreaker,
    CircuitOpenError,
    CircuitBreakerRegistry
)

from interfaces.agent.cache import InterfaceCache
from interfaces.agent.interface import AgentInterface
from agent import Agent

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define fixtures for testing
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def event_queue():
    """Create and start an event queue for testing."""
    queue = EventQueue()
    await queue.start()
    yield queue
    await queue.stop()

@pytest.fixture
def state_manager(event_queue):
    """Create a state manager for testing."""
    return StateManager(event_queue)

@pytest.fixture
def cache_manager(event_queue):
    """Create a cache manager for testing."""
    return CacheManager(event_queue)

@pytest.fixture
def metrics_manager(event_queue):
    """Create a metrics manager for testing."""
    return MetricsManager(event_queue)

@pytest.fixture
def error_handler(event_queue):
    """Create an error handler for testing."""
    return ErrorHandler(event_queue)

@pytest.fixture
def agent_context_manager(event_queue):
    """Create an agent context manager for testing."""
    return AgentContextManager(event_queue)

@pytest.fixture
def memory_monitor(event_queue):
    """Create a memory monitor for testing."""
    return MemoryMonitor(event_queue)

@pytest.fixture
def circuit_breaker(event_queue):
    """Create a circuit breaker for testing."""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=1,  # Short timeout for testing
        half_open_max_tries=1
    )
    return CircuitBreaker("test_circuit", event_queue, config)

@pytest.fixture
def circuit_breaker_registry(event_queue, state_manager):
    """Create a circuit breaker registry for testing."""
    registry = CircuitBreakerRegistry(event_queue, None, state_manager)
    return registry

@pytest.fixture
def interface_cache(event_queue, cache_manager, memory_monitor):
    """Create an interface cache for testing."""
    return InterfaceCache(event_queue, "test_cache", cache_manager, memory_monitor)

# Tests for CircuitBreaker
@pytest.mark.asyncio
async def test_circuit_breaker_initialization(circuit_breaker):
    """Test circuit breaker initialization."""
    assert circuit_breaker.name == "test_circuit"
    assert circuit_breaker.state == CircuitState.CLOSED
    assert circuit_breaker.failure_count == 0
    assert circuit_breaker.last_failure_time is None

@pytest.mark.asyncio
async def test_circuit_breaker_execute_success(circuit_breaker):
    """Test successful execution with circuit breaker."""
    # Create a test operation that succeeds
    async def success_operation():
        return "Success"
    
    # Execute the operation
    result = await circuit_breaker.execute(success_operation)
    
    # Verify the result
    assert result == "Success"
    assert circuit_breaker.state == CircuitState.CLOSED
    assert circuit_breaker.failure_count == 0

@pytest.mark.asyncio
async def test_circuit_breaker_trip_on_failures(circuit_breaker):
    """Test circuit breaker tripping after reaching failure threshold."""
    # Create a test operation that fails
    async def fail_operation():
        raise ValueError("Test failure")
    
    # Execute the operation multiple times, expecting failures
    for i in range(3):  # Threshold is 3
        with pytest.raises(ValueError):
            await circuit_breaker.execute(fail_operation)
    
    # Verify the circuit breaker is now open
    assert circuit_breaker.state == CircuitState.OPEN
    assert circuit_breaker.failure_count == 3
    assert circuit_breaker.last_failure_time is not None
    
    # Attempt to execute another operation
    with pytest.raises(CircuitOpenError):
        await circuit_breaker.execute(fail_operation)

@pytest.mark.asyncio
async def test_circuit_breaker_half_open_recovery(circuit_breaker):
    """Test circuit breaker recovery through half-open state."""
    # First trip the circuit
    await circuit_breaker.trip("Manual trip for testing")
    assert circuit_breaker.state == CircuitState.OPEN
    
    # Wait for the recovery timeout
    await asyncio.sleep(1.1)  # Just over the 1 second recovery timeout
    
    # Create a test operation that succeeds
    async def success_operation():
        return "Success"
    
    # Execute should go through now and transition to half-open
    result = await circuit_breaker.execute(success_operation)
    
    # Verify results
    assert result == "Success"
    assert circuit_breaker.state == CircuitState.CLOSED  # Success transitions to closed

@pytest.mark.asyncio
async def test_circuit_breaker_half_open_failure(circuit_breaker):
    """Test circuit breaker failure in half-open state."""
    # First trip the circuit
    await circuit_breaker.trip("Manual trip for testing")
    assert circuit_breaker.state == CircuitState.OPEN
    
    # Wait for the recovery timeout
    await asyncio.sleep(1.1)  # Just over the 1 second recovery timeout
    
    # Force transition to half-open (without calling execute)
    await circuit_breaker._transition_to_half_open()
    assert circuit_breaker.state == CircuitState.HALF_OPEN
    
    # Create a test operation that fails
    async def fail_operation():
        raise ValueError("Test failure in half-open")
    
    # Execute should fail and transition back to open
    with pytest.raises(ValueError):
        await circuit_breaker.execute(fail_operation)
    
    # Verify results
    assert circuit_breaker.state == CircuitState.OPEN

@pytest.mark.asyncio
async def test_circuit_breaker_reset(circuit_breaker):
    """Test manually resetting a circuit breaker."""
    # First trip the circuit
    await circuit_breaker.trip("Manual trip for testing")
    assert circuit_breaker.state == CircuitState.OPEN
    
    # Reset the circuit
    await circuit_breaker.reset()
    
    # Verify the circuit is now closed
    assert circuit_breaker.state == CircuitState.CLOSED
    assert circuit_breaker.failure_count == 0

@pytest.mark.asyncio
async def test_circuit_breaker_state_change_listener(circuit_breaker):
    """Test circuit breaker state change listener."""
    # Create a mock listener
    listener_calls = []
    
    async def test_listener(name, old_state, new_state):
        listener_calls.append((name, old_state, new_state))
    
    # Add the listener
    circuit_breaker.add_state_change_listener(test_listener)
    
    # Trip the circuit
    await circuit_breaker.trip("Test state change listener")
    
    # Verify the listener was called
    assert len(listener_calls) == 1
    assert listener_calls[0][0] == "test_circuit"
    assert listener_calls[0][1] == "CLOSED"
    assert listener_calls[0][2] == "OPEN"
    
    # Reset the circuit
    await circuit_breaker.reset()
    
    # Verify the listener was called again
    assert len(listener_calls) == 2
    assert listener_calls[1][0] == "test_circuit"
    assert listener_calls[1][1] == "OPEN"
    assert listener_calls[1][2] == "CLOSED"
    
    # Remove the listener
    circuit_breaker.remove_state_change_listener(test_listener)
    
    # Trip the circuit again
    await circuit_breaker.trip("Test listener removal")
    
    # Verify the listener wasn't called
    assert len(listener_calls) == 2

# Tests for CircuitBreakerRegistry
@pytest.mark.asyncio
async def test_circuit_breaker_registry_initialization(circuit_breaker_registry):
    """Test circuit breaker registry initialization."""
    assert isinstance(circuit_breaker_registry, CircuitBreakerRegistry)
    # There may be some circuit breakers already registered by the StateManager
    # so we don't check for an empty dictionary
    assert isinstance(circuit_breaker_registry.circuit_breakers, dict)
    assert isinstance(circuit_breaker_registry.circuit_names, list)

@pytest.mark.asyncio
async def test_get_or_create_circuit_breaker(circuit_breaker_registry):
    """Test getting or creating a circuit breaker."""
    # Get a circuit breaker that doesn't exist yet
    circuit = await circuit_breaker_registry.get_or_create_circuit_breaker("new_circuit")
    
    # Verify the circuit was created
    assert circuit.name == "new_circuit"
    assert circuit.state == CircuitState.CLOSED
    assert "new_circuit" in circuit_breaker_registry.circuit_names
    
    # Get the same circuit again
    circuit2 = await circuit_breaker_registry.get_or_create_circuit_breaker("new_circuit")
    
    # Verify we got the same circuit
    assert circuit is circuit2

@pytest.mark.asyncio
async def test_circuit_execute(circuit_breaker_registry):
    """Test executing an operation through the registry."""
    # Create a test operation that succeeds
    async def success_operation():
        return "Registry success"
    
    # Execute the operation through the registry
    result = await circuit_breaker_registry.circuit_execute("registry_circuit", success_operation)
    
    # Verify the result
    assert result == "Registry success"
    assert "registry_circuit" in circuit_breaker_registry.circuit_names
    
@pytest.mark.asyncio
async def test_circuit_breaker_registry_thread_safety(circuit_breaker_registry, event_queue):
    """Test thread safety of circuit breaker registry with concurrent access from multiple threads."""
    import threading
    import time
    from concurrent.futures import ThreadPoolExecutor
    
    # Create a single event loop for async operations
    loop = asyncio.get_event_loop()
    
    # Number of concurrent threads to use
    num_threads = 10
    operations_per_thread = 5
    
    # Create a shared circuit breaker
    shared_circuit = await circuit_breaker_registry.get_or_create_circuit_breaker("shared_test_circuit")
    
    # Counters for tracking operations (thread-safe)
    successful_operations = 0
    failed_operations = 0
    errors = []
    counter_lock = threading.RLock()
    
    # Define worker function
    def worker(thread_id):
        nonlocal successful_operations, failed_operations
        
        local_success = 0
        local_failed = 0
        local_errors = []
        
        for i in range(operations_per_thread):
            # Create unique circuit name for this operation
            circuit_name = f"thread_{thread_id}_op_{i}"
            
            try:
                # Create a new circuit breaker
                future = asyncio.run_coroutine_threadsafe(
                    circuit_breaker_registry.get_or_create_circuit_breaker(circuit_name),
                    loop
                )
                circuit = future.result(timeout=5)
                
                # Try to trip the circuit
                future = asyncio.run_coroutine_threadsafe(
                    circuit.trip(f"Thread {thread_id} tripping circuit"),
                    loop
                )
                future.result(timeout=5)
                
                # Check if the circuit is open
                if circuit.state.name == "OPEN":
                    local_success += 1
                else:
                    local_failed += 1
                    local_errors.append(f"Circuit {circuit_name} not open after trip")
                
            except Exception as e:
                local_failed += 1
                local_errors.append(f"Thread {thread_id} operation {i} failed: {str(e)}")
                
        # Update shared counters with thread safety
        with counter_lock:
            successful_operations += local_success
            failed_operations += local_failed
            errors.extend(local_errors)
    
    # Start worker threads
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, i) for i in range(num_threads)]
        
        # Wait for all threads to complete
        for future in futures:
            future.result()
    
    # Make one more operation on the shared circuit to verify it still works
    await shared_circuit.reset()
    result = await shared_circuit.execute(lambda: asyncio.sleep(0.1) or "Success")
    
    # Verify results
    assert result == "Success"
    assert successful_operations + failed_operations == num_threads * operations_per_thread
    assert failed_operations == 0, f"Thread safety failures: {errors}"
    
    # Check that all circuits were created
    all_circuits = circuit_breaker_registry.circuit_names
    assert len(all_circuits) >= num_threads * operations_per_thread

@pytest.mark.asyncio
async def test_circuit_breaker_registry_trip_reset(circuit_breaker_registry):
    """Test tripping and resetting circuits through the registry."""
    # First create a circuit
    await circuit_breaker_registry.get_or_create_circuit_breaker("trip_reset_circuit")
    
    # Trip the circuit
    result = await circuit_breaker_registry.trip_circuit("trip_reset_circuit", "Registry trip test")
    
    # Verify the circuit was tripped
    assert result == True
    circuit = await circuit_breaker_registry.get_circuit_breaker("trip_reset_circuit")
    assert circuit.state == CircuitState.OPEN
    
    # Reset the circuit
    result = await circuit_breaker_registry.reset_circuit("trip_reset_circuit")
    
    # Verify the circuit was reset
    assert result == True
    assert circuit.state == CircuitState.CLOSED

@pytest.mark.asyncio
async def test_cascading_failures(circuit_breaker_registry):
    """Test cascading failures between parent and child circuits."""
    # Create parent and child circuits
    parent = await circuit_breaker_registry.get_or_create_circuit_breaker("parent_circuit")
    child = await circuit_breaker_registry.get_or_create_circuit_breaker("child_circuit")
    
    # Register dependency
    await circuit_breaker_registry.register_dependency("child_circuit", "parent_circuit")
    
    # Verify both circuits are closed
    assert parent.state == CircuitState.CLOSED
    assert child.state == CircuitState.CLOSED
    
    # Trip the parent circuit
    await circuit_breaker_registry.trip_circuit("parent_circuit", "Cascading test")
    
    # Small delay to allow event processing
    await asyncio.sleep(0.1)
    
    # Verify the child circuit was also tripped
    child = await circuit_breaker_registry.get_circuit_breaker("child_circuit")
    assert child.state == CircuitState.OPEN

@pytest.mark.asyncio
async def test_circuit_breaker_registry_save_load_state(circuit_breaker_registry, state_manager):
    """Test saving and loading circuit breaker state."""
    # Create and trip a circuit
    circuit = await circuit_breaker_registry.get_or_create_circuit_breaker("persistence_test")
    await circuit_breaker_registry.trip_circuit("persistence_test", "Persistence test")
    
    # Save the state
    await circuit_breaker_registry.save_state("persistence_test")
    
    # Create a new registry instance
    new_registry = CircuitBreakerRegistry(circuit_breaker_registry._event_queue, None, state_manager)
    
    # Manually create the circuit in the new registry, as load_state doesn't create missing circuits
    new_circuit = await new_registry.get_or_create_circuit_breaker("persistence_test")
    
    # Load the state
    await new_registry.load_state()
    
    # Verify the circuit state was loaded
    assert new_circuit.state == CircuitState.OPEN

# Tests for InterfaceCache with circuit breakers
@pytest.mark.asyncio
async def test_interface_cache_with_circuit_breaker(interface_cache, event_queue):
    """Test interface cache with circuit breaker integration."""
    # Patch the cache_manager to simulate circuit breaker integration
    async def mock_get_value(key, circuit_config=None):
        if key == "failing_key":
            raise ValueError("Simulated cache error")
        return "test_value"
    
    # Replace the actual method with our mock
    original_get_value = interface_cache._cache_manager.get_value
    interface_cache._cache_manager.get_value = mock_get_value
    
    try:
        # Test successful cache retrieval
        result = await interface_cache.get_cache("success_key")
        assert result == "test_value"
        
        # Expect an exception for the failing key
        with pytest.raises(ValueError):
            await interface_cache.get_cache("failing_key")
            
    finally:
        # Restore the original method
        interface_cache._cache_manager.get_value = original_get_value

@pytest.mark.asyncio
async def test_agent_interface_with_circuit_breaker(event_queue, state_manager, agent_context_manager, 
                                                 cache_manager, metrics_manager, error_handler, 
                                                 memory_monitor, circuit_breaker_registry):
    """Test AgentInterface integration with circuit breakers."""
    # Create an agent interface
    agent_interface = AgentInterface(
        "test_agent",
        event_queue,
        state_manager,
        agent_context_manager,
        cache_manager,
        metrics_manager,
        error_handler,
        memory_monitor
    )
    
    # Initialize the interface
    await agent_interface.ensure_initialized()
    
    # Register a circuit breaker for this agent
    await circuit_breaker_registry.get_or_create_circuit_breaker(
        "agent:test_agent", 
        config=CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1)
    )
    
    # Mock the agent's get_response to simulate failures
    async def mock_get_response(*args, **kwargs):
        if kwargs.get("operation_id", "").startswith("failing"):
            raise ValueError("Simulated agent error")
        return {"message": "Test response", "status": "success"}
    
    # Replace the agent's get_response method
    original_get_response = agent_interface.agent.get_response
    agent_interface.agent.get_response = mock_get_response
    
    try:
        # Test successful processing
        result = await agent_interface.process_with_validation(
            "Test conversation",
            system_prompt_info=("test_dir", "test_prompt"),
            operation_id="success_op"
        )
        
        assert result["status"] == "success"
        assert "message" in result
        
        # Test failing processing that should trip the circuit breaker
        for i in range(2):  # Threshold is 2
            result = await agent_interface.process_with_validation(
                "Test conversation",
                system_prompt_info=("test_dir", "test_prompt"),
                operation_id=f"failing_op_{i}"
            )
            assert "error" in result
            assert result["status"] == "error"
        
        # Verify the agent is in ERROR state
        assert agent_interface.agent_state.name == "ERROR"
        
    finally:
        # Restore the original method
        agent_interface.agent.get_response = original_get_response

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])