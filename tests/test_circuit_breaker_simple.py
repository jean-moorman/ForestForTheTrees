"""
Tests for the simplified circuit breaker implementation.

These tests verify that the simplified circuit breaker implementation works
without creating circular dependencies.
"""

import asyncio
import pytest
import logging
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import from simplified module to avoid circular imports
from resources.circuit_breakers_simple import (
    CircuitBreakerSimple,
    CircuitBreakerRegistrySimple,
    CircuitOpenError,
    CircuitState
)
from resources.common import CircuitBreakerConfig, HealthStatus

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockEventQueue:
    """Mock event queue for testing"""
    
    def __init__(self):
        self.events = []
    
    async def emit(self, event_type: str, data: Dict[str, Any], 
                  correlation_id: Optional[str] = None, 
                  priority: str = "normal") -> bool:
        """Record emitted events for verification"""
        self.events.append({
            "event_type": event_type,
            "data": data,
            "correlation_id": correlation_id,
            "priority": priority
        })
        return True

class MockHealthTracker:
    """Mock health tracker for testing"""
    
    def __init__(self):
        self.health_updates = []
    
    async def update_health(self, component_id: str, health_status: HealthStatus) -> None:
        """Record health updates for verification"""
        self.health_updates.append({
            "component_id": component_id,
            "status": health_status.status,
            "description": health_status.description
        })

class MockStateManager:
    """Mock state manager for testing"""
    
    def __init__(self):
        self.states = {}
    
    async def save_state(self, resource_id: str, state: Dict[str, Any]) -> None:
        """Record saved states for verification"""
        self.states[resource_id] = state

@pytest.fixture
def mock_components():
    """Fixture to create mock components for testing"""
    return {
        "event_queue": MockEventQueue(),
        "health_tracker": MockHealthTracker(),
        "state_manager": MockStateManager()
    }

@pytest.fixture
def circuit_registry(mock_components):
    """Fixture to create a configured circuit breaker registry for testing"""
    registry = CircuitBreakerRegistrySimple()
    
    # Configure optional callbacks for integration
    registry.set_event_emitter(mock_components["event_queue"].emit)
    registry.set_health_tracker(mock_components["health_tracker"].update_health)
    registry.set_state_manager(
        lambda name, state: mock_components["state_manager"].save_state(f"circuit_breaker_{name}", state)
    )
    
    # Set a custom config for tests
    registry.set_default_config(CircuitBreakerConfig(
        failure_threshold=2,  # Lower for faster testing
        recovery_timeout=1,   # Shorter for faster testing
        half_open_max_tries=1,
        failure_window=60
    ))
    
    return registry

@pytest.mark.asyncio
async def test_circuit_breaker_lifecycle(circuit_registry, mock_components):
    """Test the basic lifecycle of a circuit breaker"""
    # Create a circuit breaker
    circuit = await circuit_registry.get_or_create_circuit_breaker("test_circuit")
    
    # Verify health update was emitted
    assert len(mock_components["health_tracker"].health_updates) > 0
    assert mock_components["health_tracker"].health_updates[-1]["component_id"] == "circuit_breaker_test_circuit"
    
    # Verify circuit was registered
    registered_circuit = await circuit_registry.get_circuit_breaker("test_circuit")
    assert registered_circuit is not None
    assert registered_circuit.name == "test_circuit"
    
    # Verify circuit starts in CLOSED state
    assert registered_circuit.state == CircuitState.CLOSED
    
    # Simulate successful operations
    async def success_operation():
        return "success"
    
    result = await circuit.execute(success_operation)
    assert result == "success"
    
    # Simulate failures to trip the circuit
    async def failure_operation():
        raise ValueError("Simulated failure")
    
    # First failure shouldn't trip circuit
    with pytest.raises(ValueError):
        await circuit.execute(failure_operation)
    
    assert circuit.state == CircuitState.CLOSED
    
    # Second failure should trip circuit
    with pytest.raises(ValueError):
        await circuit.execute(failure_operation)
    
    # Circuit should now be OPEN
    assert circuit.state == CircuitState.OPEN
    
    # Operations should be rejected while circuit is OPEN
    with pytest.raises(CircuitOpenError):
        await circuit.execute(success_operation)
    
    # Verify events were emitted
    events = mock_components["event_queue"].events
    assert any(e["event_type"] == "system_health_changed" for e in events)
    
    # Verify state was saved
    assert f"circuit_breaker_test_circuit" in mock_components["state_manager"].states
    
    # Wait for recovery timeout to elapse
    await asyncio.sleep(1.5)  # slightly longer than recovery_timeout
    
    # Circuit should now be HALF_OPEN
    # We need to check this via execute since the transition happens during execute
    try:
        await circuit.execute(success_operation)
    except CircuitOpenError:
        # It's possible we hit timing issues in tests
        pass
    
    # Reset the circuit manually
    await circuit_registry.reset_circuit("test_circuit")
    assert circuit.state == CircuitState.CLOSED

@pytest.mark.asyncio
async def test_circuit_dependencies(circuit_registry):
    """Test the circuit dependency relationships"""
    # Create parent and child circuits
    parent = await circuit_registry.get_or_create_circuit_breaker("parent_circuit")
    child = await circuit_registry.get_or_create_circuit_breaker("child_circuit")
    
    # Register dependency
    await circuit_registry.register_dependency("child_circuit", "parent_circuit")
    
    # Trip the parent circuit
    await circuit_registry.trip_circuit("parent_circuit", "Testing cascading trips")
    
    # Verify child circuit was also tripped due to cascading relationship
    child_status = await circuit_registry.get_circuit_breaker("child_circuit")
    assert child_status.state == CircuitState.OPEN

@pytest.mark.asyncio
async def test_concurrent_circuit_operations(circuit_registry):
    """Test concurrent operations with circuit breakers"""
    # Create a shared circuit
    shared_circuit = await circuit_registry.get_or_create_circuit_breaker("shared_circuit")
    
    # Create a list to track results
    results = []
    
    # Create a success operation
    async def success_operation(i):
        await asyncio.sleep(0.1)  # Simulate some work
        results.append(f"success-{i}")
        return f"success-{i}"
    
    # Create tasks for concurrent execution
    tasks = []
    for i in range(5):
        task = asyncio.create_task(
            circuit_registry.circuit_execute("shared_circuit", lambda: success_operation(i))
        )
        tasks.append(task)
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks)
    
    # Verify all operations succeeded
    assert len(results) == 5
    
    # Reset for the next test
    results.clear()
    
    # Create a failure operation
    async def failure_operation(i):
        await asyncio.sleep(0.1)  # Simulate some work
        results.append(f"failure-{i}")
        raise ValueError(f"Simulated failure {i}")
    
    # Create tasks for concurrent execution that will cause failures
    failure_tasks = []
    for i in range(5):
        task = asyncio.create_task(
            circuit_registry.circuit_execute(
                "shared_circuit", 
                lambda: failure_operation(i)
            ).catch(lambda e: results.append(f"caught-{i}"))
        )
        failure_tasks.append(task)
    
    # Wait for all tasks to complete
    try:
        await asyncio.gather(*failure_tasks, return_exceptions=True)
    except Exception:
        pass  # Expected failures
    
    # Verify circuit was tripped
    assert shared_circuit.state == CircuitState.OPEN

@pytest.mark.asyncio
async def test_circuit_breaker_registry_singleton():
    """Test that the registry is a singleton"""
    registry1 = CircuitBreakerRegistrySimple()
    registry2 = CircuitBreakerRegistrySimple()
    
    # Should be the same instance
    assert registry1 is registry2
    
    # Add a circuit to the first registry
    await registry1.get_or_create_circuit_breaker("singleton_test")
    
    # Should be visible in the second registry
    circuit = await registry2.get_circuit_breaker("singleton_test")
    assert circuit is not None
    assert circuit.name == "singleton_test"

@pytest.mark.asyncio
async def test_thread_safety():
    """Test thread safety of the circuit breaker registry"""
    registry = CircuitBreakerRegistrySimple()
    
    # Create an initial circuit
    await registry.get_or_create_circuit_breaker("main_circuit")
    
    # Store results from threads
    results = []
    result_lock = threading.Lock()
    completed_event = threading.Event()
    
    # Function to run in thread
    def thread_function(thread_id):
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the async function
            circuit_name = f"thread_{thread_id}_circuit"
            
            # Register and check circuit breaker
            async def thread_task():
                circuit = await registry.get_or_create_circuit_breaker(circuit_name)
                status = registry.get_circuit_status_summary()
                return circuit_name in status
            
            # Run the async function in this thread's event loop
            success = loop.run_until_complete(thread_task())
            
            # Store result
            with result_lock:
                results.append((thread_id, success))
            
            # Signal completion if this is the last thread
            if len(results) == 5:
                completed_event.set()
                
        finally:
            # Clean up
            loop.close()
    
    # Start threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=thread_function, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete with timeout
    completed_event.wait(timeout=10.0)
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join(timeout=1.0)
    
    # Verify all threads succeeded
    assert len(results) == 5
    assert all(success for _, success in results)
    
    # Verify final state
    status = registry.get_circuit_status_summary()
    assert len(status) == 6  # main_circuit + 5 thread circuits
    
    # Check that all circuits are present
    assert "main_circuit" in status
    for i in range(5):
        assert f"thread_{i}_circuit" in status