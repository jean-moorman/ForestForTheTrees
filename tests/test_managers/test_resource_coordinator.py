import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
import sys
from typing import Dict, Any, Optional, List

# Create a mock EventQueue to avoid issues with the real one
class MockEventQueue:
    """Mock event queue for testing."""
    
    def __init__(self):
        self.events = []
        self.started = False
        
    async def start(self):
        """Start the queue."""
        self.started = True
        
    async def stop(self):
        """Stop the queue."""
        self.started = False
        
    async def emit(self, event_type, data, correlation_id=None, priority="normal"):
        """Record emitted events for inspection."""
        self.events.append({
            "event_type": event_type,
            "data": data,
            "correlation_id": correlation_id,
            "priority": priority
        })
        return True
        
    async def subscribe(self, event_type, callback):
        """Mock subscribe."""
        pass
        
    async def unsubscribe(self, event_type, callback):
        """Mock unsubscribe."""
        pass

from resources.managers.coordinator import ResourceCoordinator

# Mock resource manager for testing
class MockResourceManager:
    def __init__(self, name: str, should_fail=False):
        self.name = name
        self.initialized = False
        self.started = False
        self.stopped = False
        self.should_fail = should_fail
        self.start_called = 0
        self.stop_called = 0
        
    async def start(self):
        """Initialize the manager."""
        self.start_called += 1
        if self.should_fail:
            raise ValueError(f"Simulated failure for {self.name}")
        self.started = True
        self.initialized = True
        
    async def stop(self):
        """Stop the manager."""
        self.stop_called += 1
        self.stopped = True
        
    def get_status(self):
        """Get manager status."""
        return {
            "name": self.name,
            "initialized": self.initialized,
            "started": self.started,
            "stopped": self.stopped
        }

# Tests for ResourceCoordinator
class TestResourceCoordinator:
    
    @pytest_asyncio.fixture
    async def event_queue(self):
        """Create a test event queue."""
        queue = MockEventQueue()
        await queue.start()
        yield queue
        await queue.stop()
        
    @pytest_asyncio.fixture
    async def coordinator(self, event_queue):
        """Create a resource coordinator for testing."""
        coordinator = ResourceCoordinator(event_queue)
        # Reset singleton between tests
        coordinator._initialized = False
        coordinator._shutting_down = False
        coordinator._managers = {}
        coordinator._dependencies = {}
        coordinator._initialization_order = []
        coordinator._shutdown_order = []
        coordinator._dependency_graph = {}
        coordinator._optional_dependencies = {}
        coordinator._required_dependencies = {}
        coordinator._component_metadata = {}
        coordinator._initialization_state = {}
        yield coordinator
        
    @pytest.mark.asyncio
    async def test_register_manager(self, coordinator):
        """Test registering a manager with the coordinator."""
        # Create test manager
        manager = MockResourceManager("test_manager")
        
        # Register the manager
        coordinator.register_manager("test_manager", manager)
        
        # Verify it was registered
        assert "test_manager" in coordinator._managers
        assert coordinator._managers["test_manager"] == manager
        assert coordinator._initialization_state["test_manager"] == "not_started"
        
    @pytest.mark.asyncio
    async def test_register_with_dependencies(self, coordinator):
        """Test registering a manager with dependencies."""
        # Create test managers
        manager1 = MockResourceManager("dep_manager")
        manager2 = MockResourceManager("test_manager")
        
        # Register with dependencies
        coordinator.register_manager("dep_manager", manager1)
        coordinator.register_manager("test_manager", manager2, 
                                    dependencies=["dep_manager"], 
                                    optional_dependencies=["optional_dep"])
        
        # Verify dependencies were registered
        assert "dep_manager" in coordinator._required_dependencies["test_manager"]
        assert "optional_dep" in coordinator._optional_dependencies["test_manager"]
        assert "dep_manager" in coordinator._dependencies["test_manager"]
        
        # Verify dependency graph
        assert coordinator._dependency_graph["test_manager"]["required"] == ["dep_manager"]
        assert coordinator._dependency_graph["test_manager"]["optional"] == ["optional_dep"]
        
    @pytest.mark.asyncio
    async def test_calculate_initialization_order(self, coordinator):
        """Test calculating initialization order based on dependencies."""
        # Create managers with dependencies
        # A depends on nothing
        # B depends on A
        # C depends on B
        # D depends on A
        managerA = MockResourceManager("A")
        managerB = MockResourceManager("B")
        managerC = MockResourceManager("C")
        managerD = MockResourceManager("D")
        
        # Register with dependencies
        coordinator.register_manager("A", managerA)
        coordinator.register_manager("B", managerB, dependencies=["A"])
        coordinator.register_manager("C", managerC, dependencies=["B"])
        coordinator.register_manager("D", managerD, dependencies=["A"])
        
        # Calculate initialization order
        order = coordinator._calculate_initialization_order()
        
        # Verify order respects dependencies
        # A must come before B, C, D
        # B must come before C
        a_index = order.index("A")
        b_index = order.index("B")
        c_index = order.index("C")
        d_index = order.index("D")
        
        assert a_index < b_index < c_index  # A before B before C
        assert a_index < d_index  # A before D
        
    @pytest.mark.asyncio
    async def test_initialize_all(self, coordinator):
        """Test initializing all managers in dependency order."""
        # Create managers with dependencies
        managerA = MockResourceManager("A")
        managerB = MockResourceManager("B")
        managerC = MockResourceManager("C")
        
        # Register with dependencies
        coordinator.register_manager("A", managerA)
        coordinator.register_manager("B", managerB, dependencies=["A"])
        coordinator.register_manager("C", managerC, dependencies=["B"])
        
        # Initialize all
        await coordinator.initialize_all()
        
        # Verify all managers were initialized in correct order
        assert coordinator._initialization_order == ["A", "B", "C"]
        assert managerA.started
        assert managerB.started
        assert managerC.started
        assert coordinator._initialized
        
    @pytest.mark.asyncio
    async def test_initialization_failure_handling(self, coordinator):
        """Test handling of initialization failures."""
        # Create managers with one that will fail
        managerA = MockResourceManager("A")
        managerB = MockResourceManager("B", should_fail=True)  # This one will fail
        managerC = MockResourceManager("C")
        
        # Register managers
        coordinator.register_manager("A", managerA)
        coordinator.register_manager("B", managerB, dependencies=["A"])
        coordinator.register_manager("C", managerC, dependencies=["B"])
        
        # Initialize all (should handle B's failure)
        await coordinator.initialize_all()
        
        # Verify states
        assert managerA.started  # A should initialize successfully
        assert not managerB.started  # B should fail
        assert coordinator._initialization_state["B"] == "failed"
        # C might be skipped or attempted depending on implementation
        if "C" in coordinator._initialization_state:
            assert coordinator._initialization_state["C"] in ["skipped_dep_failure", "failed"]
        
    @pytest.mark.asyncio
    async def test_shutdown(self, coordinator):
        """Test shutting down all managers in reverse initialization order."""
        # Create and register managers
        managerA = MockResourceManager("A")
        managerB = MockResourceManager("B")
        managerC = MockResourceManager("C")
        
        coordinator.register_manager("A", managerA)
        coordinator.register_manager("B", managerB, dependencies=["A"])
        coordinator.register_manager("C", managerC, dependencies=["B"])
        
        # First initialize them
        await coordinator.initialize_all()
        
        # Then shut them down
        await coordinator.shutdown()
        
        # Verify shutdown order is reverse of initialization
        assert coordinator._shutdown_order == ["C", "B", "A"]
        
        # Verify all were stopped
        assert managerA.stopped
        assert managerB.stopped
        assert managerC.stopped
        assert not coordinator._shutting_down  # Flag should be reset
        assert not coordinator._initialized  # Flag should be reset
        
    @pytest.mark.asyncio
    async def test_get_manager(self, coordinator):
        """Test getting a specific manager by ID."""
        # Register a manager
        manager = MockResourceManager("get_test")
        coordinator.register_manager("get_test", manager)
        
        # Get the manager
        result = coordinator.get_manager("get_test")
        assert result == manager
        
        # Try getting a non-existent manager
        result = coordinator.get_manager("nonexistent")
        assert result is None
        
    @pytest.mark.asyncio
    async def test_get_status(self, coordinator):
        """Test getting detailed status of all managers."""
        # Register managers
        managerA = MockResourceManager("A")
        managerB = MockResourceManager("B")
        
        coordinator.register_manager("A", managerA)
        coordinator.register_manager("B", managerB, dependencies=["A"])
        
        # Initialize one manager and manually set its state
        await coordinator._initialize_manager("A")
        # Need to manually update the initialization_state since mock EventQueue 
        # doesn't trigger the right events in ResourceCoordinator
        coordinator._initialization_state["A"] = "complete"
        
        # Get status
        status = coordinator.get_status()
        
        # Verify status contains expected information
        assert status["initialized"] == coordinator._initialized
        assert status["shutting_down"] == coordinator._shutting_down
        assert "A" in status["managers"]
        assert "B" in status["managers"]
        assert "component_states" in status
        assert status["component_states"]["A"]["initialization_state"] == "complete"
        assert status["component_states"]["B"]["initialization_state"] == "not_started"

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])