import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
import sys
from enum import Enum, auto
from typing import Dict, Any, Optional, List, Callable

from resources.events import EventQueue, ResourceEventTypes
from resources.managers.registry import CircuitBreakerRegistry

# Simple mock circuit breaker for testing
class CircuitState(Enum):
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()

class MockCircuitBreaker:
    def __init__(self, name: str):
        self.name = name
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.state_change_listeners = []
        
    def add_state_change_listener(self, listener: Callable):
        self.state_change_listeners.append(listener)
        
    async def trip(self, reason=None):
        """Trip the circuit to OPEN state."""
        old_state = self.state
        self.state = CircuitState.OPEN
        self.failure_count += 1
        
        # Notify listeners
        for listener in self.state_change_listeners:
            await listener(self.name, old_state.name, self.state.name)
            
    async def reset(self):
        """Reset the circuit to CLOSED state."""
        old_state = self.state
        self.state = CircuitState.CLOSED
        
        # Notify listeners
        for listener in self.state_change_listeners:
            await listener(self.name, old_state.name, self.state.name)


# Tests for CircuitBreakerRegistry
class TestCircuitBreakerRegistry:
    
    @pytest_asyncio.fixture
    async def event_queue(self):
        """Create a test event queue."""
        queue = EventQueue()
        await queue.start()
        yield queue
        await queue.stop()
        
    @pytest_asyncio.fixture
    async def registry(self, event_queue):
        """Create a circuit breaker registry for testing."""
        registry = CircuitBreakerRegistry(event_queue)
        yield registry
        await registry.stop()
        
    @pytest.mark.asyncio
    async def test_register_circuit_breaker(self, registry):
        """Test registering a circuit breaker."""
        # Create test circuit
        circuit = MockCircuitBreaker("test_circuit")
        
        # Register the circuit
        await registry.register_circuit_breaker("test_circuit", circuit)
        
        # Verify it was registered
        status = await registry.get_circuit_status("test_circuit")
        assert status["name"] == "test_circuit"
        assert status["state"] == "CLOSED"
        assert status["failure_count"] == 0
        
    @pytest.mark.asyncio
    async def test_register_circuit_with_parent(self, registry):
        """Test registering a circuit breaker with a parent dependency."""
        # Create parent and child circuits
        parent_circuit = MockCircuitBreaker("parent_circuit")
        child_circuit = MockCircuitBreaker("child_circuit")
        
        # Register both circuits with relationship
        await registry.register_circuit_breaker("parent_circuit", parent_circuit)
        await registry.register_circuit_breaker("child_circuit", child_circuit, parent="parent_circuit")
        
        # Verify relationship
        parent_status = await registry.get_circuit_status("parent_circuit")
        child_status = await registry.get_circuit_status("child_circuit")
        
        assert "child_circuit" in parent_status["children"]
        assert "parent_circuit" in child_status["parents"]
        
    @pytest.mark.asyncio
    async def test_cascading_trip(self, registry):
        """Test cascading trip from parent to child circuit."""
        # Create parent and child circuits
        parent_circuit = MockCircuitBreaker("cascade_parent")
        child_circuit = MockCircuitBreaker("cascade_child")
        
        # Register both circuits with relationship
        await registry.register_circuit_breaker("cascade_parent", parent_circuit)
        await registry.register_circuit_breaker("cascade_child", child_circuit, parent="cascade_parent")
        
        # Trip the parent circuit
        await parent_circuit.trip()
        
        # Allow some time for cascading trip
        await asyncio.sleep(0.1)
        
        # Verify child was also tripped
        child_status = await registry.get_circuit_status("cascade_child")
        assert child_status["state"] == "OPEN"
        
    @pytest.mark.asyncio
    async def test_get_all_circuit_status(self, registry):
        """Test getting status of all circuit breakers."""
        # Clear any existing circuit breakers from previous tests
        registry._circuit_breakers = {}
        
        # Register multiple circuits
        for i in range(3):
            circuit = MockCircuitBreaker(f"status_circuit_{i}")
            await registry.register_circuit_breaker(f"status_circuit_{i}", circuit)
            
        # Get all statuses
        all_status = await registry.get_circuit_status()
        
        # Verify all circuits are included
        assert len([key for key in all_status.keys() if key.startswith("status_circuit_")]) == 3
        for i in range(3):
            assert f"status_circuit_{i}" in all_status
            
    @pytest.mark.asyncio
    async def test_reset_all_circuits(self, registry):
        """Test resetting all circuit breakers."""
        # Clear any existing circuit breakers from previous tests
        registry._circuit_breakers = {}
        
        # Register multiple circuits
        circuits = []
        for i in range(3):
            circuit = MockCircuitBreaker(f"reset_circuit_{i}")
            await registry.register_circuit_breaker(f"reset_circuit_{i}", circuit)
            circuits.append(circuit)
            
        # Trip all circuits
        for circuit in circuits:
            await circuit.trip()
            
        # Verify all are tripped
        all_status = await registry.get_circuit_status()
        for i in range(3):
            assert all_status[f"reset_circuit_{i}"]["state"] == "OPEN"
            
        # Reset all circuits
        reset_result = await registry.reset_all_circuits()
        
        # Verify reset metrics - count may include other circuit breakers from previous tests
        assert reset_result["reset_count"] >= 3
        assert f"reset_circuit_0" in registry._circuit_breakers
        assert f"reset_circuit_1" in registry._circuit_breakers
        assert f"reset_circuit_2" in registry._circuit_breakers
        
        # Verify all our circuits are reset
        all_status = await registry.get_circuit_status()
        for i in range(3):
            assert all_status[f"reset_circuit_{i}"]["state"] == "CLOSED"
            
    @pytest.mark.asyncio
    async def test_circuit_state_history(self, registry):
        """Test circuit state change history tracking."""
        # Clear any existing circuit breakers from previous tests that may have the same name
        if "history_circuit" in registry._circuit_breakers:
            del registry._circuit_breakers["history_circuit"]
            if "history_circuit" in registry._circuit_metadata:
                del registry._circuit_metadata["history_circuit"]
            if "history_circuit" in registry._state_history:
                del registry._state_history["history_circuit"]
            
        circuit = MockCircuitBreaker("history_circuit")
        await registry.register_circuit_breaker("history_circuit", circuit)
        
        # Trip and reset multiple times
        await circuit.trip()
        await asyncio.sleep(0.1)
        await circuit.reset()
        await asyncio.sleep(0.1)
        await circuit.trip()
        await asyncio.sleep(0.1)
        
        # Check circuit metadata
        status = await registry.get_circuit_status("history_circuit")
        assert status["metadata"]["trip_count"] == 2
        assert "last_trip" in status["metadata"]
        assert "last_reset" in status["metadata"]

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])