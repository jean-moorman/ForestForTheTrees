import unittest
import asyncio
import os
import shutil
import tempfile
import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import time
from pathlib import Path
import logging

# Imports from modules under test
from resources.state import (
    StateManager,
    StateEntry,
    StateSnapshot, 
    StateManagerConfig,
    StateTransitionValidator,
    MemoryStateBackend,
    FileStateBackend,
    SQLiteStateBackend
)
from resources.common import ResourceState, InterfaceState, ResourceType, HealthStatus
from resources.base import CleanupConfig, CleanupPolicy
from resources.events import EventQueue


class MockEventQueue:
    """Mock EventQueue for testing"""
    
    def __init__(self):
        self.events = []
        
    async def emit(self, event_type, data, priority="normal"):
        self.events.append((event_type, data, priority))
        return True
        
    async def start(self):
        pass
        
    async def stop(self):
        pass


def async_test(coro):
    """Helper decorator to run async tests"""
    def wrapper(*args, **kwargs):
        # Get the current event loop if it exists and is running
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            # No event loop in this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        # If the test case has a StateManager, make sure its cleanup task is started
        # This needs to be done in a running event loop
        self_arg = args[0] if args else None
        if self_arg and hasattr(self_arg, 'manager') and hasattr(self_arg.manager, 'start_cleanup_task_safe'):
            loop.run_until_complete(self_arg.manager.start_cleanup_task_safe())
            
        try:
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            # Don't close the loop to allow further async operations
            pass
    return wrapper


class TestStateManager(unittest.TestCase):
    """Test StateManager functionality"""
    
    def setUp(self):
        self.event_queue = MockEventQueue()
        self.cleanup_config = CleanupConfig(
            max_size=100,
            ttl_seconds=3600,
            policy=CleanupPolicy.TTL
        )
        self.config = StateManagerConfig(
            cleanup_config=self.cleanup_config,
            persistence_type="memory",
            enable_metrics=True
        )
        self.manager = StateManager(self.event_queue, self.config)
        
    @async_test
    async def test_set_and_get_state(self):
        """Test setting and getting state"""
        resource_id = "test-resource"
        
        # Set initial state
        entry = await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            metadata={"region": "us-west-2"},
            transition_reason="initial creation"
        )
        
        self.assertEqual(entry.state, ResourceState.ACTIVE)
        
        # Get state
        state = await self.manager.get_state(resource_id)
        self.assertEqual(state.state, ResourceState.ACTIVE)
        self.assertEqual(state.metadata, {"region": "us-west-2"})
        
        # Event should have been emitted
        self.assertEqual(len(self.event_queue.events), 1)
        event_type, data, _ = self.event_queue.events[0]
        self.assertEqual(event_type, "resource_state_changed")
        self.assertEqual(data["resource_id"], resource_id)
        
    @async_test
    async def test_state_transitions(self):
        """Test state transitions with validation"""
        resource_id = "test-resource"
        
        # Set initial state
        await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE
        )
        
        # Valid transition
        await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.PAUSED,
            resource_type=ResourceType.COMPUTE,
            transition_reason="maintenance"
        )
        
        state = await self.manager.get_state(resource_id)
        self.assertEqual(state.state, ResourceState.PAUSED)
        
        # Invalid transition should raise ValueError
        with self.assertRaises(ValueError):
            await self.manager.set_state(
                resource_id=resource_id,
                state=ResourceState.RECOVERED,
                resource_type=ResourceType.COMPUTE
            )
        
        # State should still be PAUSED
        state = await self.manager.get_state(resource_id)
        self.assertEqual(state.state, ResourceState.PAUSED)

    @async_test
    async def test_get_history(self):
        """Test getting state history"""
        resource_id = "test-resource"
        
        # Set multiple states
        states = [ResourceState.ACTIVE, ResourceState.PAUSED, ResourceState.ACTIVE]
        for state in states:
            await self.manager.set_state(
                resource_id=resource_id,
                state=state,
                resource_type=ResourceType.COMPUTE
            )
        
        # Get history
        history = await self.manager.get_history(resource_id)
        
        # Should have all states in order
        self.assertEqual(len(history), len(states))
        for i, state in enumerate(states):
            self.assertEqual(history[i].state, state)

    @async_test
    async def test_count_resources_by_state(self):
        """Test counting resources by state"""
        # Create resources in different states
        resources = {
            "active1": ResourceState.ACTIVE,
            "active2": ResourceState.ACTIVE,
            "paused1": ResourceState.PAUSED,
            "failed1": ResourceState.FAILED
        }
        
        for resource_id, state in resources.items():
            await self.manager.set_state(
                resource_id=resource_id,
                state=state,
                resource_type=ResourceType.COMPUTE
            )
        
        # Test count_resources_by_state
        counts = await self.manager.count_resources_by_state()
        self.assertEqual(counts[str(ResourceState.ACTIVE)], 2)
        self.assertEqual(counts[str(ResourceState.PAUSED)], 1)
        self.assertEqual(counts[str(ResourceState.FAILED)], 1)

    @async_test
    async def test_get_resources_by_state(self):
        """Test getting resources by state"""
        # Create resources in different states
        resources = {
            "active1": ResourceState.ACTIVE,
            "active2": ResourceState.ACTIVE,
            "paused1": ResourceState.PAUSED,
            "failed1": ResourceState.FAILED
        }
        
        for resource_id, state in resources.items():
            await self.manager.set_state(
                resource_id=resource_id,
                state=state,
                resource_type=ResourceType.COMPUTE
            )
        
        # Test get_resources_by_state
        active_resources = await self.manager.get_resources_by_state(ResourceState.ACTIVE)
        self.assertEqual(set(active_resources), {"active1", "active2"})
        
        # Test for a state with only one resource
        paused_resources = await self.manager.get_resources_by_state(ResourceState.PAUSED)
        self.assertEqual(set(paused_resources), {"paused1"})
        
        # Test for a state with no resources
        terminated_resources = await self.manager.get_resources_by_state(ResourceState.TERMINATED)
        self.assertEqual(set(terminated_resources), set())

    @async_test
    async def test_mark_as_failed(self):
        """Test marking a resource as failed"""
        resource_id = "test-resource"
        
        # Set initial state
        await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE
        )
        
        # Mark as failed
        await self.manager.mark_as_failed(resource_id, "Test failure")
        
        # Check state
        state = await self.manager.get_state(resource_id)
        self.assertEqual(state.state, ResourceState.FAILED)
        self.assertIsNotNone(state.failure_info)
        self.assertEqual(state.transition_reason, "Test failure")

    @async_test
    async def test_mark_as_recovered(self):
        """Test marking a resource as recovered"""
        resource_id = "test-resource"
        
        # Set initial state to FAILED
        await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.FAILED,
            resource_type=ResourceType.COMPUTE
        )
        
        # Mark as recovered
        await self.manager.mark_as_recovered(resource_id, "Recovery successful")
        
        # Check state
        state = await self.manager.get_state(resource_id)
        self.assertEqual(state.state, ResourceState.RECOVERED)
        self.assertEqual(state.transition_reason, "Recovery successful")

    @async_test
    async def test_terminate_resource(self):
        """Test terminating a resource"""
        resource_id = "test-resource"
        
        # Set initial state
        await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE
        )
        
        # Terminate resource
        await self.manager.terminate_resource(resource_id, "Cleanup")
        
        # Check state
        state = await self.manager.get_state(resource_id)
        self.assertEqual(state.state, ResourceState.TERMINATED)
        self.assertEqual(state.transition_reason, "Cleanup")

    @async_test
    async def test_get_health_status(self):
        """Test health status reporting"""
        # Add some resources
        for i in range(5):
            await self.manager.set_state(
                resource_id=f"resource-{i}",
                state=ResourceState.ACTIVE,
                resource_type=ResourceType.COMPUTE
            )
        
        # Get health status
        health = await self.manager.get_health_status()
        
        # Basic validation
        self.assertEqual(health.status, "HEALTHY")
        self.assertEqual(health.source, "state_manager")
        self.assertIsNotNone(health.description)
        self.assertIsNotNone(health.metadata)

    @async_test
    async def test_get_keys_by_prefix(self):
        """Test getting keys by prefix"""
        # Create resources with different prefixes
        prefixes = {
            "compute-1": ResourceState.ACTIVE,
            "compute-2": ResourceState.ACTIVE,
            "storage-1": ResourceState.ACTIVE,
            "network-1": ResourceState.ACTIVE
        }
        
        for resource_id, state in prefixes.items():
            await self.manager.set_state(
                resource_id=resource_id,
                state=state,
                resource_type=ResourceType.COMPUTE
            )
        
        # Get by prefix
        compute_keys = await self.manager.get_keys_by_prefix("compute-")
        self.assertEqual(set(compute_keys), {"compute-1", "compute-2"})
        
        storage_keys = await self.manager.get_keys_by_prefix("storage-")
        self.assertEqual(set(storage_keys), {"storage-1"})
        
        # Nonexistent prefix should return empty list
        missing_keys = await self.manager.get_keys_by_prefix("missing-")
        self.assertEqual(missing_keys, [])

    @async_test
    async def test_get_metrics(self):
        """Test metrics collection"""
        # Perform some operations
        for i in range(3):
            resource_id = f"resource-{i}"
            await self.manager.set_state(
                resource_id=resource_id,
                state=ResourceState.ACTIVE,
                resource_type=ResourceType.COMPUTE
            )
            
            # Get state a few times
            for _ in range(2):
                await self.manager.get_state(resource_id)
            
            # Get history
            await self.manager.get_history(resource_id)
        
        # Get metrics
        metrics = await self.manager.get_metrics()
        
        # Basic validation
        self.assertIn("set_state_count", metrics)
        self.assertIn("get_state_count", metrics)
        self.assertIn("get_history_count", metrics)
        
        # Counts should match operations
        self.assertEqual(metrics["set_state_count"], 3)
        self.assertEqual(metrics["get_state_count"], 6)  # 3 resources x 2 gets each
        self.assertEqual(metrics["get_history_count"], 3)


class TestStateManagerErrorRecovery(unittest.TestCase):
    """Test error recovery in the StateManager"""
    
    def setUp(self):
        self.event_queue = MockEventQueue()
        self.config = StateManagerConfig(
            cleanup_config=CleanupConfig(
                max_size=100,
                ttl_seconds=3600,
                policy=CleanupPolicy.TTL
            ),
            persistence_type="memory",
            enable_metrics=True
        )
        self.manager = StateManager(self.event_queue, self.config)
        
    @async_test
    async def test_recover_from_corrupt_state(self):
        """Test recovery from corrupt state file by using history"""
        # Create a custom backend with mock functionality
        backend = MemoryStateBackend()
        original_load_state = backend.load_state
        
        # Make a state entry
        resource_id = "test-resource"
        state_entry = StateEntry(
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            metadata={"version": 1}
        )
        
        # Save state - this will go to history too
        await backend.save_state(resource_id, state_entry)
        
        # Update with a new state
        state_entry2 = StateEntry(
            state=ResourceState.PAUSED,
            resource_type=ResourceType.COMPUTE,
            metadata={"version": 2}
        )
        await backend.save_state(resource_id, state_entry2)
        
        # Mock the load_state method to simulate corruption
        async def mock_corrupt_state(res_id):
            if res_id == resource_id:
                # First call simulates corruption
                backend.load_state = original_load_state  # Restore for subsequent calls
                return None
            return await original_load_state(res_id)
        
        backend.load_state = mock_corrupt_state
        
        # Replace manager's backend
        self.manager._backend = backend
        
        # Try to get state - should recover from history
        state = await self.manager.get_state(resource_id)
        
        # Should get the most recent state from history
        self.assertIsNotNone(state)
        self.assertEqual(state.state, ResourceState.PAUSED)
        self.assertEqual(state.metadata["version"], 2)
        
    @async_test
    async def test_backend_failure_handling(self):
        """Test that StateManager handles backend failures gracefully"""
        # Create a state manager with a backend that sometimes fails
        backend = MemoryStateBackend()
        original_save_state = backend.save_state
        
        resource_id = "test-resource"
        fail_count = 0
        
        # Mock save_state to fail every other call
        async def failing_save_state(res_id, entry):
            nonlocal fail_count
            fail_count += 1
            if fail_count % 2 == 0:
                return False  # Simulate failure
            return await original_save_state(res_id, entry)
        
        backend.save_state = failing_save_state
        self.manager._backend = backend
        
        # Try to set state multiple times
        states = []
        for i in range(4):  # Even calls will fail, odd calls will succeed
            result = await self.manager.set_state(
                resource_id=resource_id,
                state=ResourceState.ACTIVE,
                resource_type=ResourceType.COMPUTE,
                metadata={"attempt": i}
            )
            states.append(result)
        
        # Half should fail (return None), half should succeed
        succeeded = [s for s in states if s is not None]
        self.assertEqual(len(succeeded), 2)
        
        # Metrics should record backend errors
        metrics = await self.manager.get_metrics()
        self.assertGreater(metrics["backend_errors"], 0)
        
    @async_test
    async def test_invalid_state_transition(self):
        """Test that invalid state transitions are rejected"""
        resource_id = "test-resource"
        
        # Set initial state to FAILED
        await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.FAILED,
            resource_type=ResourceType.COMPUTE,
            transition_reason="initial failure"
        )
        
        # Try an invalid transition from FAILED to ACTIVE (should be rejected)
        with self.assertRaises(ValueError):
            await self.manager.set_state(
                resource_id=resource_id,
                state=ResourceState.ACTIVE,
                resource_type=ResourceType.COMPUTE,
                transition_reason="direct recovery"  # This violates the state machine rules
            )
            
        # Verify state wasn't changed
        state = await self.manager.get_state(resource_id)
        self.assertEqual(state.state, ResourceState.FAILED)
        
        # Now try a valid transition to RECOVERED
        result = await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.RECOVERED,
            resource_type=ResourceType.COMPUTE,
            transition_reason="proper recovery"
        )
        
        # Should succeed
        self.assertIsNotNone(result)
        self.assertEqual(result.state, ResourceState.RECOVERED)
        
        # Now ACTIVE is a valid transition
        result = await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            transition_reason="back to active"
        )
        
        self.assertEqual(result.state, ResourceState.ACTIVE)
    
    @async_test
    async def test_mark_as_failed_utility(self):
        """Test the utility method to mark resources as failed"""
        resource_id = "test-resource"
        
        # Set initial state
        await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            metadata={"region": "us-west-2"}
        )
        
        # Mark as failed
        error_info = {
            "error_code": "ERR-1234",
            "description": "Connectivity lost"
        }
        
        result = await self.manager.mark_as_failed(
            resource_id=resource_id,
            reason="Network error",
            error_info=error_info
        )
        
        # Should be marked as failed
        self.assertIsNotNone(result)
        self.assertEqual(result.state, ResourceState.FAILED)
        self.assertEqual(result.transition_reason, "Network error")
        self.assertIsNotNone(result.failure_info)
        self.assertEqual(result.failure_info["error_code"], "ERR-1234")
        
        # Try to mark a non-existent resource as failed
        result = await self.manager.mark_as_failed(
            resource_id="nonexistent",
            reason="Test failure"
        )
        
        # Should return None
        self.assertIsNone(result)
        
    @async_test
    async def test_mark_as_recovered_utility(self):
        """Test the utility method to mark resources as recovered"""
        resource_id = "test-resource"
        
        # Set initial state to FAILED
        await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.FAILED,
            resource_type=ResourceType.COMPUTE,
            metadata={"region": "us-west-2"}
        )
        
        # Mark as recovered
        result = await self.manager.mark_as_recovered(
            resource_id=resource_id,
            reason="System restored"
        )
        
        # Should be marked as recovered
        self.assertIsNotNone(result)
        self.assertEqual(result.state, ResourceState.RECOVERED)
        self.assertEqual(result.transition_reason, "System restored")
        
        # Try to recover a resource that's not in FAILED state
        resource_id2 = "test-resource2"
        await self.manager.set_state(
            resource_id=resource_id2,
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE
        )
        
        result = await self.manager.mark_as_recovered(
            resource_id=resource_id2,
            reason="Attempted recovery"
        )
        
        # Should return None since resource wasn't in FAILED state
        self.assertIsNone(result)
        
    @async_test
    async def test_snapshot_recovery(self):
        """Test recovery from snapshots"""
        resource_id = "test-resource"
        
        # Create initial state
        initial_state = await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            metadata={"version": 1}
        )
        
        # Create snapshot
        await self.manager._create_snapshot(resource_id, initial_state)
        
        # Change state multiple times
        for i in range(2, 5):
            await self.manager.set_state(
                resource_id=resource_id,
                state=ResourceState.ACTIVE if i % 2 == 0 else ResourceState.PAUSED,
                resource_type=ResourceType.COMPUTE,
                metadata={"version": i}
            )
            
        # Get current state
        current = await self.manager.get_state(resource_id)
        self.assertEqual(current.metadata["version"], 4)
        
        # Recover from the snapshot (which should contain version 1)
        recovered = await self.manager.recover_from_snapshot(resource_id)
        
        # Should be back to version 1
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered.metadata["version"], 1)
        
        # Current state should now reflect the recovered state
        current = await self.manager.get_state(resource_id)
        self.assertEqual(current.metadata["version"], 1)
        
        # History should include all the changes plus the recovery
        history = await self.manager.get_history(resource_id)
        self.assertEqual(len(history), 5)  # 4 original states + 1 recovery
        
        # The latest history entry should be the recovery
        self.assertEqual(history[-1].transition_reason, "recovered_from_snapshot")
        
        
class TestCustomStateTypes(unittest.TestCase):
    """Test handling of custom state types"""
    
    def setUp(self):
        self.event_queue = MockEventQueue()
        self.config = StateManagerConfig(
            persistence_type="memory"
        )
        self.manager = StateManager(self.event_queue, self.config)
        
    @async_test
    async def test_custom_dict_state(self):
        """Test using a dictionary state instead of enum"""
        resource_id = "custom-state-resource"
        
        # Create a custom state with nested structure
        custom_state = {
            "status": "initializing",
            "progress": 0.5,
            "components": {
                "network": "connected",
                "storage": "pending",
                "compute": {
                    "status": "active",
                    "utilization": 0.75
                }
            },
            "tags": ["test", "development"]
        }
        
        # Save state
        result = await self.manager.set_state(
            resource_id=resource_id,
            state=custom_state,
            resource_type=ResourceType.COMPUTE,
            metadata={"custom": True}
        )
        
        # Verify it saved correctly
        self.assertIsNotNone(result)
        
        # Load state
        loaded = await self.manager.get_state(resource_id)
        
        # Verify all nested structure is preserved
        self.assertEqual(loaded.state, custom_state)
        self.assertEqual(loaded.state["components"]["compute"]["utilization"], 0.75)
        self.assertEqual(loaded.state["tags"], ["test", "development"])
        
        # Update with a new state
        custom_state["progress"] = 0.75
        custom_state["components"]["storage"] = "active"
        
        # Update state
        await self.manager.set_state(
            resource_id=resource_id,
            state=custom_state,
            resource_type=ResourceType.COMPUTE,
            metadata={"custom": True, "updated": True}
        )
        
        # Verify update worked
        updated = await self.manager.get_state(resource_id)
        self.assertEqual(updated.state["progress"], 0.75)
        self.assertEqual(updated.state["components"]["storage"], "active")
        self.assertTrue(updated.metadata["updated"])
        
    @async_test
    async def test_mixed_state_transitions(self):
        """Test transitions between enum states and dict states"""
        resource_id = "mixed-state-resource"
        
        # Start with enum state
        await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE
        )
        
        # Switch to dict state
        custom_state = {"status": "special-mode", "details": {"mode": "diagnostic"}}
        await self.manager.set_state(
            resource_id=resource_id,
            state=custom_state,
            resource_type=ResourceType.COMPUTE
        )
        
        # Back to enum state
        await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.PAUSED,
            resource_type=ResourceType.COMPUTE
        )
        
        # Verify history shows all transitions
        history = await self.manager.get_history(resource_id)
        self.assertEqual(len(history), 3)
        
        # First was enum
        self.assertEqual(history[0].state, ResourceState.ACTIVE)
        
        # Second was dict
        self.assertEqual(history[1].state["status"], "special-mode")
        
        # Third was enum again
        self.assertEqual(history[2].state, ResourceState.PAUSED)
        
    @async_test
    async def test_null_and_empty_values(self):
        """Test handling of null and empty values in custom states"""
        resource_id = "empty-value-resource"
        
        # Create state with various empty/null values
        custom_state = {
            "null_value": None,
            "empty_string": "",
            "empty_list": [],
            "empty_dict": {},
            "zero_value": 0,
            "false_value": False,
            "nested": {
                "null_nested": None,
                "empty_nested": ""
            }
        }
        
        # Save state
        await self.manager.set_state(
            resource_id=resource_id,
            state=custom_state,
            resource_type=ResourceType.COMPUTE
        )
        
        # Load state and verify all values preserved
        loaded = await self.manager.get_state(resource_id)
        
        self.assertIsNone(loaded.state["null_value"])
        self.assertEqual(loaded.state["empty_string"], "")
        self.assertEqual(loaded.state["empty_list"], [])
        self.assertEqual(loaded.state["empty_dict"], {})
        self.assertEqual(loaded.state["zero_value"], 0)
        self.assertEqual(loaded.state["false_value"], False)
        self.assertIsNone(loaded.state["nested"]["null_nested"])
        self.assertEqual(loaded.state["nested"]["empty_nested"], "")


if __name__ == '__main__':
    unittest.main()