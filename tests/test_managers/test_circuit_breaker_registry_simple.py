"""
Tests for the simplified CircuitBreakerRegistrySimple implementation.

These tests verify that the simplified registry works correctly without
introducing circular dependencies.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
import sys
from typing import Dict, Any, Optional, List, Callable

# Import the simplified implementation
from resources.circuit_breakers_simple import (
    CircuitBreakerSimple,
    CircuitBreakerRegistrySimple,
    CircuitState
)

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

# Tests for CircuitBreakerRegistrySimple
class TestCircuitBreakerRegistrySimple:
    
    @pytest_asyncio.fixture
    async def event_queue(self):
        """Create a test event queue."""
        queue = MockEventQueue()
        yield queue
        
    @pytest_asyncio.fixture
    async def registry(self, event_queue):
        """Create a circuit breaker registry for testing."""
        registry = CircuitBreakerRegistrySimple()
        registry.set_event_emitter(event_queue.emit)
        yield registry
        
    @pytest.mark.asyncio
    async def test_register_circuit_breaker(self, registry):
        """Test registering a circuit breaker."""
        # Create test circuit
        circuit = CircuitBreakerSimple("test_circuit")
        
        # Register the circuit
        await registry.register_circuit_breaker("test_circuit", circuit)
        
        # Verify it was registered
        registered_circuit = await registry.get_circuit_breaker("test_circuit")
        assert registered_circuit is not None
        assert registered_circuit.name == "test_circuit"
        assert registered_circuit.state == CircuitState.CLOSED
        
    @pytest.mark.asyncio
    async def test_register_circuit_with_parent(self, registry):
        """Test registering a circuit breaker with a parent dependency."""
        # Create parent and child circuits
        parent_circuit = CircuitBreakerSimple("parent_circuit")
        child_circuit = CircuitBreakerSimple("child_circuit")
        
        # Register both circuits with relationship
        await registry.register_circuit_breaker("parent_circuit", parent_circuit)
        await registry.register_circuit_breaker("child_circuit", child_circuit)
        
        # Register dependency
        await registry.register_dependency("child_circuit", "parent_circuit")
        
        # Get the circuit status summary
        status = registry.get_circuit_status_summary()
        
        # Verify both circuits exist in the summary
        assert "parent_circuit" in status
        assert "child_circuit" in status
        
    @pytest.mark.asyncio
    async def test_cascading_trip(self, registry):
        """Test cascading trip from parent to child circuit."""
        # Create parent and child circuits
        parent_circuit = CircuitBreakerSimple("cascade_parent")
        child_circuit = CircuitBreakerSimple("cascade_child")
        
        # Register both circuits with relationship
        await registry.register_circuit_breaker("cascade_parent", parent_circuit)
        await registry.register_circuit_breaker("cascade_child", child_circuit)
        
        # Register dependency
        await registry.register_dependency("cascade_child", "cascade_parent")
        
        # Trip the parent circuit
        await registry.trip_circuit("cascade_parent", "Testing cascading trips")
        
        # Allow some time for cascading trip
        await asyncio.sleep(0.1)
        
        # Verify child was also tripped
        child = await registry.get_circuit_breaker("cascade_child")
        assert child.state == CircuitState.OPEN
        
    @pytest.mark.asyncio
    async def test_get_all_circuit_status(self, registry):
        """Test getting status of all circuit breakers."""
        # Register multiple circuits
        for i in range(3):
            circuit = CircuitBreakerSimple(f"status_circuit_{i}")
            await registry.register_circuit_breaker(f"status_circuit_{i}", circuit)
            
        # Get all statuses
        all_status = registry.get_circuit_status_summary()
        
        # Verify all circuits are included
        assert len([key for key in all_status.keys() if key.startswith("status_circuit_")]) == 3
        for i in range(3):
            assert f"status_circuit_{i}" in all_status
            
    @pytest.mark.asyncio
    async def test_reset_all_circuits(self, registry):
        """Test resetting all circuit breakers."""
        # Register multiple circuits
        circuits = []
        for i in range(3):
            circuit = CircuitBreakerSimple(f"reset_circuit_{i}")
            await registry.register_circuit_breaker(f"reset_circuit_{i}", circuit)
            circuits.append(circuit)
            
        # Trip all circuits
        for i in range(3):
            await registry.trip_circuit(f"reset_circuit_{i}")
            
        # Verify all are tripped
        all_status = registry.get_circuit_status_summary()
        for i in range(3):
            assert all_status[f"reset_circuit_{i}"]["state"] == CircuitState.OPEN.value
            
        # Reset all circuits
        reset_count = await registry.reset_all_circuits()
        
        # Verify reset count
        assert reset_count >= 3
        
        # Verify all circuits are reset
        all_status = registry.get_circuit_status_summary()
        for i in range(3):
            assert all_status[f"reset_circuit_{i}"]["state"] == CircuitState.CLOSED.value
            
    @pytest.mark.asyncio
    async def test_circuit_state_change_tracking(self, registry, event_queue):
        """Test circuit state change events."""
        circuit = CircuitBreakerSimple("events_circuit")
        await registry.register_circuit_breaker("events_circuit", circuit)
        
        # Trip the circuit and check for events
        await registry.trip_circuit("events_circuit", "Testing events")
        
        # Verify events were emitted
        assert any(e["event_type"] == "system_health_changed" for e in event_queue.events)
        
        # Get the state change event
        state_events = [e for e in event_queue.events if e["event_type"] == "system_health_changed"]
        assert len(state_events) > 0
        
        # Verify event details
        event = state_events[-1]
        assert event["data"]["circuit"] == "events_circuit"
        assert event["data"]["old_state"] == CircuitState.CLOSED.value
        assert event["data"]["new_state"] == CircuitState.OPEN.value
        
    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        """Test that the registry is a singleton."""
        registry1 = CircuitBreakerRegistrySimple()
        registry2 = CircuitBreakerRegistrySimple()
        
        # Should be the same instance
        assert registry1 is registry2
        
        # Add a circuit to registry1
        circuit = CircuitBreakerSimple("singleton_test")
        await registry1.register_circuit_breaker("singleton_test", circuit)
        
        # Should be accessible from registry2
        circuit2 = await registry2.get_circuit_breaker("singleton_test")
        assert circuit2 is not None
        assert circuit2.name == "singleton_test"

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])