import unittest
import asyncio
import os
import shutil
import tempfile
import datetime
from unittest.mock import Mock, patch, AsyncMock
import json
import pickle
import sys
from pathlib import Path
import uuid
import time

# Import module under test
from resources.state import (
    StateEntry, 
    StateSnapshot, 
    StateTransitionValidator,
    StateManager,
    StateManagerConfig,
    MemoryStateBackend,
    FileStateBackend,
    SQLiteStateBackend,
    StateStorageBackend
)
from resources.common import ResourceState, InterfaceState, ResourceType, HealthStatus
from resources.base import CleanupConfig, CleanupPolicy
from resources.events import EventQueue

class TestStateEntry(unittest.TestCase):
    """Test StateEntry functionality"""
    
    def test_state_entry_initialization(self):
        """Test that a StateEntry can be properly initialized"""
        entry = StateEntry(
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            metadata={"region": "us-west-2"},
            previous_state=None,
            transition_reason="initial creation"
        )
        
        self.assertEqual(entry.state, ResourceState.ACTIVE)
        self.assertEqual(entry.resource_type, ResourceType.COMPUTE)
        self.assertEqual(entry.metadata, {"region": "us-west-2"})
        self.assertIsNone(entry.previous_state)
        self.assertEqual(entry.transition_reason, "initial creation")
        self.assertIsNone(entry.failure_info)
        self.assertEqual(entry.version, 1)
        
    def test_state_entry_with_dict_state(self):
        """Test that StateEntry can handle dictionary states"""
        custom_state = {"status": "initializing", "progress": 0.5}
        entry = StateEntry(
            state=custom_state,
            resource_type=ResourceType.STATE,
            metadata={}
        )
        
        self.assertEqual(entry.state, custom_state)
        self.assertEqual(entry.resource_type, ResourceType.STATE)
        
    def test_default_timestamp(self):
        """Test that timestamp defaults to current time"""
        before = datetime.datetime.now()
        entry = StateEntry(
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE
        )
        after = datetime.datetime.now()
        
        self.assertTrue(before <= entry.timestamp <= after)
        
    def test_default_metadata(self):
        """Test that metadata defaults to empty dict"""
        entry = StateEntry(
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE
        )
        
        self.assertEqual(entry.metadata, {})


class TestStateSnapshot(unittest.TestCase):
    """Test StateSnapshot functionality"""
    
    def test_snapshot_initialization(self):
        """Test that a StateSnapshot can be properly initialized"""
        state_data = {"state": ResourceState.ACTIVE, "metadata": {"region": "us-west-2"}}
        snapshot = StateSnapshot(
            state=state_data,
            resource_type=ResourceType.COMPUTE
        )
        
        self.assertEqual(snapshot.state, state_data)
        self.assertEqual(snapshot.resource_type, ResourceType.COMPUTE)
        self.assertEqual(snapshot.version, 1)
        
    def test_default_values(self):
        """Test default values for StateSnapshot"""
        state_data = {"state": ResourceState.ACTIVE}
        snapshot = StateSnapshot(state=state_data)
        
        self.assertEqual(snapshot.state, state_data)
        self.assertEqual(snapshot.resource_type, ResourceType.STATE)
        self.assertEqual(snapshot.metadata, {})
        self.assertEqual(snapshot.version, 1)


class TestStateTransitionValidator(unittest.TestCase):
    """Test StateTransitionValidator functionality"""
    
    def setUp(self):
        self.validator = StateTransitionValidator()
        
    def test_valid_resource_transitions(self):
        """Test valid resource state transitions"""
        # Test all valid transitions defined in _RESOURCE_TRANSITIONS
        valid_transitions = [
            (ResourceState.ACTIVE, ResourceState.PAUSED),
            (ResourceState.ACTIVE, ResourceState.FAILED),
            (ResourceState.ACTIVE, ResourceState.TERMINATED),
            (ResourceState.PAUSED, ResourceState.ACTIVE),
            (ResourceState.PAUSED, ResourceState.TERMINATED),
            (ResourceState.FAILED, ResourceState.RECOVERED),
            (ResourceState.FAILED, ResourceState.TERMINATED),
            (ResourceState.RECOVERED, ResourceState.ACTIVE),
            (ResourceState.RECOVERED, ResourceState.TERMINATED)
        ]
        
        for current, new in valid_transitions:
            self.assertTrue(
                self.validator.validate_transition(current, new),
                f"Transition from {current} to {new} should be valid"
            )
            
    def test_invalid_resource_transitions(self):
        """Test invalid resource state transitions"""
        invalid_transitions = [
            (ResourceState.ACTIVE, ResourceState.RECOVERED),
            (ResourceState.PAUSED, ResourceState.FAILED),
            (ResourceState.PAUSED, ResourceState.RECOVERED),
            (ResourceState.FAILED, ResourceState.ACTIVE),
            (ResourceState.FAILED, ResourceState.PAUSED),
            (ResourceState.RECOVERED, ResourceState.FAILED),
            (ResourceState.RECOVERED, ResourceState.PAUSED),
            (ResourceState.TERMINATED, ResourceState.ACTIVE),
            (ResourceState.TERMINATED, ResourceState.PAUSED),
            (ResourceState.TERMINATED, ResourceState.FAILED),
            (ResourceState.TERMINATED, ResourceState.RECOVERED)
        ]
        
        for current, new in invalid_transitions:
            self.assertFalse(
                self.validator.validate_transition(current, new),
                f"Transition from {current} to {new} should be invalid"
            )
            
    def test_valid_interface_transitions(self):
        """Test valid interface state transitions"""
        valid_transitions = [
            (InterfaceState.INITIALIZED, InterfaceState.ACTIVE),
            (InterfaceState.INITIALIZED, InterfaceState.ERROR),
            (InterfaceState.ACTIVE, InterfaceState.DISABLED),
            (InterfaceState.ACTIVE, InterfaceState.ERROR),
            (InterfaceState.ACTIVE, InterfaceState.VALIDATING),
            (InterfaceState.DISABLED, InterfaceState.ACTIVE),
            (InterfaceState.ERROR, InterfaceState.INITIALIZED),
            (InterfaceState.ERROR, InterfaceState.DISABLED),
            (InterfaceState.VALIDATING, InterfaceState.ACTIVE),
            (InterfaceState.VALIDATING, InterfaceState.ERROR),
            (InterfaceState.VALIDATING, InterfaceState.PROPAGATING),
            (InterfaceState.PROPAGATING, InterfaceState.ACTIVE),
            (InterfaceState.PROPAGATING, InterfaceState.ERROR)
        ]
        
        for current, new in valid_transitions:
            self.assertTrue(
                self.validator.validate_transition(current, new),
                f"Transition from {current} to {new} should be valid"
            )
            
    def test_invalid_interface_transitions(self):
        """Test invalid interface state transitions"""
        invalid_transitions = [
            (InterfaceState.INITIALIZED, InterfaceState.DISABLED),
            (InterfaceState.INITIALIZED, InterfaceState.VALIDATING),
            (InterfaceState.INITIALIZED, InterfaceState.PROPAGATING),
            (InterfaceState.DISABLED, InterfaceState.INITIALIZED),
            (InterfaceState.DISABLED, InterfaceState.ERROR),
            (InterfaceState.DISABLED, InterfaceState.VALIDATING),
            (InterfaceState.DISABLED, InterfaceState.PROPAGATING),
            (InterfaceState.ERROR, InterfaceState.ACTIVE),
            (InterfaceState.ERROR, InterfaceState.VALIDATING),
            (InterfaceState.ERROR, InterfaceState.PROPAGATING),
            (InterfaceState.VALIDATING, InterfaceState.INITIALIZED),
            (InterfaceState.VALIDATING, InterfaceState.DISABLED),
            (InterfaceState.PROPAGATING, InterfaceState.INITIALIZED),
            (InterfaceState.PROPAGATING, InterfaceState.DISABLED),
            (InterfaceState.PROPAGATING, InterfaceState.VALIDATING)
        ]
        
        for current, new in invalid_transitions:
            self.assertFalse(
                self.validator.validate_transition(current, new),
                f"Transition from {current} to {new} should be invalid"
            )
            
    def test_mixed_type_transitions(self):
        """Test transitions between different state types"""
        # Different enum types should not be valid transitions
        self.assertFalse(
            self.validator.validate_transition(ResourceState.ACTIVE, InterfaceState.ACTIVE)
        )
        self.assertFalse(
            self.validator.validate_transition(InterfaceState.ACTIVE, ResourceState.ACTIVE)
        )
        
    def test_dict_state_transitions(self):
        """Test transitions with dictionary states"""
        # Dictionary state transitions should be allowed
        self.assertTrue(
            self.validator.validate_transition({"status": "running"}, {"status": "stopped"})
        )
        
        # Dictionary to enum transitions should be allowed
        self.assertTrue(
            self.validator.validate_transition({"status": "running"}, ResourceState.ACTIVE)
        )
        
        # Enum to dictionary transitions should be allowed
        self.assertTrue(
            self.validator.validate_transition(ResourceState.ACTIVE, {"status": "running"})
        )
        
    def test_get_valid_transitions(self):
        """Test getting valid next states"""
        active_transitions = self.validator.get_valid_transitions(ResourceState.ACTIVE)
        self.assertEqual(
            active_transitions, 
            {ResourceState.PAUSED, ResourceState.FAILED, ResourceState.TERMINATED}
        )
        
        terminated_transitions = self.validator.get_valid_transitions(ResourceState.TERMINATED)
        self.assertEqual(terminated_transitions, set())
        
        dict_transitions = self.validator.get_valid_transitions({"status": "running"})
        self.assertEqual(dict_transitions, set())


def async_test(coro):
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


class TestMemoryStateBackend(unittest.TestCase):
    """Test in-memory state storage backend"""
    
    def setUp(self):
        self.backend = MemoryStateBackend()
        
    @async_test
    async def test_save_and_load_state(self):
        """Test saving and loading a state entry"""
        resource_id = "test-resource"
        state_entry = StateEntry(
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            metadata={"region": "us-west-2"}
        )
        
        # Save state
        result = await self.backend.save_state(resource_id, state_entry)
        self.assertTrue(result)
        
        # Load state
        loaded = await self.backend.load_state(resource_id)
        self.assertEqual(loaded.state, state_entry.state)
        self.assertEqual(loaded.resource_type, state_entry.resource_type)
        self.assertEqual(loaded.metadata, state_entry.metadata)
        
    @async_test
    async def test_save_and_load_snapshot(self):
        """Test saving and loading a snapshot"""
        resource_id = "test-resource"
        snapshot = StateSnapshot(
            state={"state": ResourceState.ACTIVE, "metadata": {"region": "us-west-2"}},
            resource_type=ResourceType.COMPUTE
        )
        
        # Save snapshot
        result = await self.backend.save_snapshot(resource_id, snapshot)
        self.assertTrue(result)
        
        # Load snapshots
        snapshots = await self.backend.load_snapshots(resource_id)
        self.assertEqual(len(snapshots), 1)
        loaded = snapshots[0]
        self.assertEqual(loaded.state, snapshot.state)
        self.assertEqual(loaded.resource_type, snapshot.resource_type)
        
    @async_test
    async def test_load_history(self):
        """Test loading history after multiple state changes"""
        resource_id = "test-resource"
        
        # Save multiple states
        for i in range(3):
            state_entry = StateEntry(
                state=ResourceState.ACTIVE if i % 2 == 0 else ResourceState.PAUSED,
                resource_type=ResourceType.COMPUTE,
                metadata={"version": i}
            )
            await self.backend.save_state(resource_id, state_entry)
        
        # Get history
        history = await self.backend.load_history(resource_id)
        self.assertEqual(len(history), 3)
        
        # Check order (should be chronological)
        self.assertEqual(history[0].metadata["version"], 0)
        self.assertEqual(history[1].metadata["version"], 1)
        self.assertEqual(history[2].metadata["version"], 2)
        
    @async_test
    async def test_get_all_resource_ids(self):
        """Test getting all resource IDs"""
        # Save states for multiple resources
        resources = ["resource1", "resource2", "resource3"]
        for resource_id in resources:
            state_entry = StateEntry(
                state=ResourceState.ACTIVE,
                resource_type=ResourceType.COMPUTE
            )
            await self.backend.save_state(resource_id, state_entry)
        
        # Get all resource IDs
        ids = await self.backend.get_all_resource_ids()
        self.assertEqual(set(ids), set(resources))
        
    @async_test
    async def test_history_with_limit(self):
        """Test loading history with a limit"""
        resource_id = "test-resource"
        
        # Save 5 states
        for i in range(5):
            state_entry = StateEntry(
                state=ResourceState.ACTIVE,
                resource_type=ResourceType.COMPUTE,
                metadata={"version": i}
            )
            await self.backend.save_state(resource_id, state_entry)
        
        # Get history with limit
        history = await self.backend.load_history(resource_id, limit=3)
        self.assertEqual(len(history), 3)
        
        # Check that we got the most recent 3
        self.assertEqual(history[0].metadata["version"], 2)
        self.assertEqual(history[1].metadata["version"], 3)
        self.assertEqual(history[2].metadata["version"], 4)


class TestFileStateBackend(unittest.TestCase):
    """Test file-based state storage backend"""
    
    def setUp(self):
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.backend = FileStateBackend(self.temp_dir)
        
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)
        
    @async_test
    async def test_save_and_load_state(self):
        """Test saving and loading a state entry to file"""
        resource_id = "test-resource"
        state_entry = StateEntry(
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            metadata={"region": "us-west-2"}
        )
        
        # Save state
        result = await self.backend.save_state(resource_id, state_entry)
        self.assertTrue(result)
        
        # Verify file was created
        state_file = os.path.join(self.backend.states_dir, f"{resource_id}.pickle")
        self.assertTrue(os.path.exists(state_file))
        
        # Load state
        loaded = await self.backend.load_state(resource_id)
        self.assertEqual(loaded.state, state_entry.state)
        self.assertEqual(loaded.resource_type, state_entry.resource_type)
        self.assertEqual(loaded.metadata, state_entry.metadata)
        
    @async_test
    async def test_save_and_load_snapshot(self):
        """Test saving and loading a snapshot to file"""
        resource_id = "test-resource"
        snapshot = StateSnapshot(
            state={"state": ResourceState.ACTIVE, "metadata": {"region": "us-west-2"}},
            resource_type=ResourceType.COMPUTE
        )
        
        # Save snapshot
        result = await self.backend.save_snapshot(resource_id, snapshot)
        self.assertTrue(result)
        
        # Verify file was created
        snapshot_file = os.path.join(self.backend.snapshots_dir, f"{resource_id}.pickle")
        self.assertTrue(os.path.exists(snapshot_file))
        
        # Load snapshots
        snapshots = await self.backend.load_snapshots(resource_id)
        self.assertEqual(len(snapshots), 1)
        loaded = snapshots[0]
        self.assertEqual(loaded.state, snapshot.state)
        self.assertEqual(loaded.resource_type, snapshot.resource_type)
        
    @async_test
    async def test_file_locking(self):
        """Test that file locks prevent race conditions"""
        resource_id = "test-resource"
        
        # Create state entries
        state1 = StateEntry(
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            metadata={"version": 1}
        )
        
        state2 = StateEntry(
            state=ResourceState.PAUSED,
            resource_type=ResourceType.COMPUTE,
            metadata={"version": 2}
        )
        
        # Save both states concurrently
        tasks = [
            self.backend.save_state(resource_id, state1),
            self.backend.save_state(resource_id, state2)
        ]
        
        # Run concurrently
        results = await asyncio.gather(*tasks)
        self.assertTrue(all(results))
        
        # Load state - should be one of the two states
        loaded = await self.backend.load_state(resource_id)
        self.assertIn(loaded.state, [ResourceState.ACTIVE, ResourceState.PAUSED])
        
        # History should have both states
        history = await self.backend.load_history(resource_id)
        self.assertEqual(len(history), 2)
        
    @async_test
    async def test_cleanup(self):
        """Test cleanup of old data"""
        # Create multiple resources with different timestamps
        now = datetime.datetime.now()
        old_timestamp = now - datetime.timedelta(days=60)
        
        # Create an old terminated resource
        old_resource = "old-resource"
        old_entry = StateEntry(
            state=ResourceState.TERMINATED,
            resource_type=ResourceType.COMPUTE,
            timestamp=old_timestamp
        )
        await self.backend.save_state(old_resource, old_entry)
        
        # Create a current resource
        current_resource = "current-resource"
        current_entry = StateEntry(
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE
        )
        await self.backend.save_state(current_resource, current_entry)
        
        # Run cleanup (older than 30 days)
        cleanup_date = now - datetime.timedelta(days=30)
        removed = await self.backend.cleanup(cleanup_date)
        
        # Old resource should be removed
        self.assertTrue(removed >= 1)
        
        # Old resource state file should be gone
        old_state_file = os.path.join(self.backend.states_dir, f"{old_resource}.pickle")
        self.assertFalse(os.path.exists(old_state_file))
        
        # Current resource should still exist
        current_state = await self.backend.load_state(current_resource)
        self.assertIsNotNone(current_state)
    
    @async_test
    async def test_corrupt_file_handling(self):
        """Test handling of corrupt files"""
        resource_id = "test-resource"
        state_entry = StateEntry(
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE
        )
        
        # Save state
        await self.backend.save_state(resource_id, state_entry)
        
        # Corrupt the state file
        state_file = os.path.join(self.backend.states_dir, f"{resource_id}.pickle")
        with open(state_file, 'w') as f:
            f.write("This is not a valid pickle file")
        
        # Try to load state (should not throw exception)
        loaded = await self.backend.load_state(resource_id)
        self.assertIsNone(loaded)  # Should return None for corrupt file
        
        # Backup file should have been created
        backup_files = list(Path(self.backend.states_dir).glob(f"{resource_id}_corrupt_*.pickle"))
        self.assertGreater(len(backup_files), 0)
    
    @async_test
    async def test_compact_history(self):
        """Test compacting history files"""
        if not hasattr(self.backend, 'compact_history'):
            self.skipTest("compact_history not implemented")
            
        resource_id = "test-resource"
        
        # Save many states to create a large history
        for i in range(200):
            state_entry = StateEntry(
                state=ResourceState.ACTIVE,
                resource_type=ResourceType.COMPUTE,
                timestamp=datetime.datetime.now() - datetime.timedelta(days=i % 30),
                metadata={"version": i}
            )
            await self.backend.save_state(resource_id, state_entry)
        
        # Compact history
        result = await self.backend.compact_history(resource_id, max_entries=50)
        self.assertTrue(result)
        
        # History should be smaller now
        history = await self.backend.load_history(resource_id)
        self.assertLess(len(history), 200)
        
        # Should still have the first entry
        self.assertEqual(history[0].metadata["version"], 0)
        
        # Should have the most recent entries
        self.assertEqual(history[-1].metadata["version"], 199)


class TestSQLiteStateBackend(unittest.TestCase):
    """Test SQLite-based state storage backend"""
    
    def setUp(self):
        # Create a temporary directory for the database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_state.db")
        self.backend = SQLiteStateBackend(self.db_path)
        
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)
        
    @async_test
    async def test_save_and_load_state(self):
        """Test saving and loading a state entry in SQLite"""
        resource_id = "test-resource"
        state_entry = StateEntry(
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            metadata={"region": "us-west-2"}
        )
        
        # Save state
        result = await self.backend.save_state(resource_id, state_entry)
        self.assertTrue(result)
        
        # Load state
        loaded = await self.backend.load_state(resource_id)
        self.assertEqual(loaded.state, state_entry.state)
        self.assertEqual(loaded.resource_type, state_entry.resource_type)
        self.assertEqual(loaded.metadata, state_entry.metadata)
        
    @async_test
    async def test_dict_state_serialization(self):
        """Test serialization/deserialization of dictionary states"""
        resource_id = "test-resource"
        custom_state = {"status": "initializing", "progress": 0.5, "nested": {"key": "value"}}
        state_entry = StateEntry(
            state=custom_state,
            resource_type=ResourceType.STATE,
            metadata={"test": True}
        )
        
        # Save state
        await self.backend.save_state(resource_id, state_entry)
        
        # Load state
        loaded = await self.backend.load_state(resource_id)
        self.assertEqual(loaded.state, custom_state)
        self.assertEqual(loaded.resource_type, state_entry.resource_type)
        self.assertEqual(loaded.metadata, state_entry.metadata)
        
    @async_test
    async def test_history_ordering(self):
        """Test that history is returned in chronological order"""
        resource_id = "test-resource"
        
        # Save multiple states with different timestamps
        timestamps = [
            datetime.datetime.now() - datetime.timedelta(days=3),
            datetime.datetime.now() - datetime.timedelta(days=2),
            datetime.datetime.now() - datetime.timedelta(days=1),
            datetime.datetime.now()
        ]
        
        # Save out of order to test sorting
        for i in [2, 0, 3, 1]:
            state_entry = StateEntry(
                state=ResourceState.ACTIVE,
                resource_type=ResourceType.COMPUTE,
                timestamp=timestamps[i],
                metadata={"index": i}
            )
            await self.backend.save_state(resource_id, state_entry)
        
        # Load history
        history = await self.backend.load_history(resource_id)
        
        # Check order (should be chronological by timestamp)
        self.assertEqual(len(history), 4)
        self.assertEqual(history[0].metadata["index"], 0)
        self.assertEqual(history[1].metadata["index"], 1)
        self.assertEqual(history[2].metadata["index"], 2)
        self.assertEqual(history[3].metadata["index"], 3)
        
    @async_test
    async def test_get_database_stats(self):
        """Test getting database statistics"""
        if not hasattr(self.backend, 'get_database_stats'):
            self.skipTest("get_database_stats not implemented")
            
        # Create some test data
        for i in range(5):
            resource_id = f"resource-{i}"
            state = ResourceState.ACTIVE if i % 2 == 0 else ResourceState.PAUSED
            state_entry = StateEntry(
                state=state,
                resource_type=ResourceType.COMPUTE
            )
            await self.backend.save_state(resource_id, state_entry)
        
        # Get stats
        stats = await self.backend.get_database_stats()
        
        # Basic validation
        self.assertIn("resources_count", stats)
        self.assertIn("history_entries_count", stats)
        self.assertIn("snapshots_count", stats)
        self.assertIn("database_size_bytes", stats)
        
        # Should have 5 resources
        self.assertEqual(stats["resources_count"], 5)
        
        # Should have state counts
        self.assertIn("resource_states", stats)
        
    @async_test
    async def test_optimize_database(self):
        """Test database optimization"""
        if not hasattr(self.backend, 'optimize_database'):
            self.skipTest("optimize_database not implemented")
            
        # Create some test data
        for i in range(20):
            resource_id = f"resource-{i}"
            state_entry = StateEntry(
                state=ResourceState.ACTIVE,
                resource_type=ResourceType.COMPUTE
            )
            await self.backend.save_state(resource_id, state_entry)
            
            # Create a snapshot too
            snapshot = StateSnapshot(
                state={"state": ResourceState.ACTIVE},
                resource_type=ResourceType.COMPUTE
            )
            await self.backend.save_snapshot(resource_id, snapshot)
        
        # Run optimization
        result = await self.backend.optimize_database()
        self.assertTrue(result)


class MockEventQueue:
    """Mock EventQueue for testing"""
    
    def __init__(self):
        self.events = []
        
    async def emit(self, event_type, data):
        self.events.append((event_type, data))
        return True


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
        event_type, data = self.event_queue.events[0]
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
    async def test_snapshots(self):
        """Test snapshot creation and recovery"""
        resource_id = "test-resource"
        
        # Set initial state
        await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            metadata={"version": 1}
        )
        
        # Create snapshot
        await self.manager._create_snapshot(resource_id)
        
        # Change state
        await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.PAUSED,
            resource_type=ResourceType.COMPUTE,
            metadata={"version": 2}
        )
        
        # Recover from snapshot
        recovered = await self.manager.recover_from_snapshot(resource_id)
        
        # Should have original state
        self.assertEqual(recovered.state, ResourceState.ACTIVE)
        self.assertEqual(recovered.metadata, {"version": 1})
        
    @async_test
    async def test_utility_methods(self):
        """Test utility methods for state management"""
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
        
        # Test get_resources_by_state
        active_resources = await self.manager.get_resources_by_state(ResourceState.ACTIVE)
        self.assertEqual(set(active_resources), {"active1", "active2"})
        
        # Test mark_as_failed
        await self.manager.mark_as_failed("active1", "Test failure")
        
        # Check state
        state = await self.manager.get_state("active1")
        self.assertEqual(state.state, ResourceState.FAILED)
        self.assertIsNotNone(state.failure_info)
        self.assertEqual(state.transition_reason, "Test failure")
        
        # Test mark_as_recovered
        await self.manager.mark_as_recovered("active1", "Recovered")
        
        # Check state
        state = await self.manager.get_state("active1")
        self.assertEqual(state.state, ResourceState.RECOVERED)
        
        # Test terminate_resource
        await self.manager.terminate_resource("active2", "Cleanup")
        
        # Check state
        state = await self.manager.get_state("active2")
        self.assertEqual(state.state, ResourceState.TERMINATED)
        
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
    async def test_metrics(self):
        """Test metrics collection"""
        # Perform some operations
        for i in range(10):
            resource_id = f"resource-{i}"
            await self.manager.set_state(
                resource_id=resource_id,
                state=ResourceState.ACTIVE,
                resource_type=ResourceType.COMPUTE
            )
            
            # Get state a few times
            for _ in range(3):
                await self.manager.get_state(resource_id)
            
            # Get history
            await self.manager.get_history(resource_id)
        
        # Get metrics
        metrics = await self.manager.get_metrics()
        
        # Basic validation
        self.assertIn("set_state_count", metrics)
        self.assertIn("get_state_count", metrics)
        self.assertIn("get_history_count", metrics)
        self.assertIn("cache_hits", metrics)
        self.assertIn("cache_misses", metrics)
        
        # Counts should match operations
        self.assertEqual(metrics["set_state_count"], 10)
        self.assertEqual(metrics["get_state_count"], 10 * 3)
        self.assertEqual(metrics["get_history_count"], 10)
        
    @async_test
    async def test_cleanup_task(self):
        """Test cleanup task scheduling"""
        # Stop the existing cleanup task
        await self.manager.stop_cleanup_task()
        
        # Create a new manager with a mock cleanup method
        original_cleanup = self.manager.cleanup
        cleanup_called = asyncio.Event()
        
        async def mock_cleanup():
            cleanup_called.set()
            return {"items_removed": 0}
        
        self.manager.cleanup = mock_cleanup
        
        # Start cleanup task with aggressive policy and immediate_for_testing=True
        self.manager._cleanup_config.policy = CleanupPolicy.AGGRESSIVE
        await self.manager.start_cleanup_task_safe(immediate_for_testing=True)
        
        # Wait for cleanup to be called (should be almost immediate now)
        try:
            # Increased timeout slightly for reliability
            await asyncio.wait_for(cleanup_called.wait(), 5)
            self.assertTrue(cleanup_called.is_set())
        finally:
            # Restore original cleanup and stop task
            self.manager.cleanup = original_cleanup
            await self.manager.stop_cleanup_task()


class TestStateManagerWithFileBackend(unittest.TestCase):
    """Test StateManager with file-based backend"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.event_queue = MockEventQueue()
        self.config = StateManagerConfig(
            cleanup_config=CleanupConfig(
                max_size=100,
                ttl_seconds=3600,
                policy=CleanupPolicy.TTL
            ),
            persistence_type="file",
            storage_dir=self.temp_dir
        )
        self.manager = StateManager(self.event_queue, self.config)
        
    def tearDown(self):
        # Stop the cleanup task but don't wait for it with run_until_complete
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self.manager.stop_cleanup_task())
        else:
            loop.run_until_complete(self.manager.stop_cleanup_task())
            
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)
        
    @async_test
    async def test_persistence_across_instances(self):
        """Test state persistence across manager instances"""
        resource_id = "test-resource"
        
        # Set state in first manager
        await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            metadata={"version": 1}
        )
        
        # Create a new manager instance
        new_manager = StateManager(self.event_queue, self.config)
        
        # Wait for initialization to complete
        await asyncio.sleep(0.1)
        
        # Get state from new manager
        state = await new_manager.get_state(resource_id)
        
        # Should have the same state
        self.assertIsNotNone(state)
        self.assertEqual(state.state, ResourceState.ACTIVE)
        self.assertEqual(state.metadata, {"version": 1})
        
        # Clean up
        await new_manager.stop_cleanup_task()
        
    @async_test
    async def test_file_backend_cleanup(self):
        """Test cleanup with file backend"""
        # Create old terminated resources
        old_timestamp = datetime.datetime.now() - datetime.timedelta(days=2)
        
        for i in range(5):
            resource_id = f"terminated-{i}"
            entry = StateEntry(
                state=ResourceState.TERMINATED,
                resource_type=ResourceType.COMPUTE,
                timestamp=old_timestamp
            )
            await self.manager._backend.save_state(resource_id, entry)
        
        # Create active resources
        for i in range(3):
            resource_id = f"active-{i}"
            await self.manager.set_state(
                resource_id=resource_id,
                state=ResourceState.ACTIVE,
                resource_type=ResourceType.COMPUTE
            )
        
        # Run cleanup with 1 day TTL
        self.manager._cleanup_config.ttl_seconds = 24 * 3600  # 1 day
        result = await self.manager.cleanup()
        
        # Should have removed the terminated resources
        self.assertGreaterEqual(result["items_removed"], 5)
        
        # Terminated resources should be gone
        for i in range(5):
            resource_id = f"terminated-{i}"
            state = await self.manager.get_state(resource_id)
            self.assertIsNone(state)
        
        # Active resources should still exist
        for i in range(3):
            resource_id = f"active-{i}"
            state = await self.manager.get_state(resource_id)
            self.assertIsNotNone(state)


class TestStateManagerWithSQLiteBackend(unittest.TestCase):
    """Test StateManager with SQLite backend"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_state.db")
        self.event_queue = MockEventQueue()
        self.config = StateManagerConfig(
            cleanup_config=CleanupConfig(
                max_size=100,
                ttl_seconds=3600,
                policy=CleanupPolicy.TTL
            ),
            persistence_type="sqlite",
            db_path=self.db_path
        )
        self.manager = StateManager(self.event_queue, self.config)
        
    def tearDown(self):
        # Stop the cleanup task but don't wait for it with run_until_complete
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self.manager.stop_cleanup_task())
        else:
            loop.run_until_complete(self.manager.stop_cleanup_task())
            
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)
        
    @async_test
    async def test_sqlite_persistence(self):
        """Test state persistence with SQLite backend"""
        resource_id = "test-resource"
        
        # Set state
        await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            metadata={"version": 1}
        )
        
        # Create a new manager instance
        new_manager = StateManager(self.event_queue, self.config)
        
        # Wait for initialization to complete
        await asyncio.sleep(0.1)
        
        # Get state from new manager
        state = await new_manager.get_state(resource_id)
        
        # Should have the same state
        self.assertIsNotNone(state)
        self.assertEqual(state.state, ResourceState.ACTIVE)
        self.assertEqual(state.metadata, {"version": 1})
        
        # Clean up
        await new_manager.stop_cleanup_task()
        
    @async_test
    async def test_concurrent_operations(self):
        """Test concurrent operations with SQLite backend"""
        # Generate unique resource IDs
        resources = [f"resource-{uuid.uuid4()}" for _ in range(10)]
        
        # Create tasks to set state for all resources concurrently
        tasks = []
        for resource_id in resources:
            task = self.manager.set_state(
                resource_id=resource_id,
                state=ResourceState.ACTIVE,
                resource_type=ResourceType.COMPUTE,
                metadata={"timestamp": time.time()}
            )
            tasks.append(task)
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
        
        # All resources should exist
        for resource_id in resources:
            state = await self.manager.get_state(resource_id)
            self.assertIsNotNone(state)
            self.assertEqual(state.state, ResourceState.ACTIVE)
            
    @async_test
    async def test_storage_compaction(self):
        """Test storage compaction for SQLite backend"""
        if not hasattr(self.manager, 'compact_storage'):
            self.skipTest("compact_storage not implemented")
            
        # Create a lot of state changes to increase database size
        resource_id = "test-resource"
        for i in range(20):
            state = ResourceState.ACTIVE if i % 2 == 0 else ResourceState.PAUSED
            await self.manager.set_state(
                resource_id=resource_id,
                state=state,
                resource_type=ResourceType.COMPUTE,
                metadata={"version": i}
            )
        
        # Run storage compaction
        result = await self.manager.compact_storage()
        
        # Should succeed
        self.assertTrue("database_optimized" in result or "compacted_test-resource" in result)


class TestStateConcurrency(unittest.TestCase):
    """Test concurrency handling in StateManager"""
    
    def setUp(self):
        self.event_queue = MockEventQueue()
        self.config = StateManagerConfig(
            cleanup_config=CleanupConfig(
                max_size=100,
                ttl_seconds=3600,
                policy=CleanupPolicy.TTL
            ),
            persistence_type="memory"
        )
        self.manager = StateManager(self.event_queue, self.config)
        
    @async_test
    async def test_concurrent_state_changes(self):
        """Test concurrent state changes for the same resource"""
        resource_id = "test-resource"
        
        # Set initial state
        await self.manager.set_state(
            resource_id=resource_id,
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE
        )
        
        # Define a task that does many state transitions
        async def state_transition_task(start_state, end_state, iterations):
            current = start_state
            next_state = end_state
            
            for _ in range(iterations):
                # Set state
                await self.manager.set_state(
                    resource_id=resource_id,
                    state=current,
                    resource_type=ResourceType.COMPUTE
                )
                
                # Swap states for next iteration
                current, next_state = next_state, current
                
            # End with the end_state
            await self.manager.set_state(
                resource_id=resource_id,
                state=end_state,
                resource_type=ResourceType.COMPUTE
            )
            
            return end_state
        
        # Create two tasks that repeatedly transition between states
        task1 = state_transition_task(ResourceState.ACTIVE, ResourceState.PAUSED, 10)
        task2 = state_transition_task(ResourceState.ACTIVE, ResourceState.PAUSED, 10)
        
        # Run concurrently
        result1, result2 = await asyncio.gather(task1, task2)
        
        # Final state should be one of the valid end states
        final_state = await self.manager.get_state(resource_id)
        self.assertIn(final_state.state, {result1, result2})
        
        # History should have all transitions
        history = await self.manager.get_history(resource_id)
        self.assertGreater(len(history), 20)  # At least 20 transitions
        
    @async_test
    async def test_concurrent_different_resources(self):
        """Test concurrent operations on different resources"""
        # Generate many resource IDs
        resources = [f"resource-{i}" for i in range(100)]
        
        # Create a task for each resource
        async def create_resource(resource_id):
            await self.manager.set_state(
                resource_id=resource_id,
                state=ResourceState.ACTIVE,
                resource_type=ResourceType.COMPUTE
            )
            return resource_id
        
        tasks = [create_resource(resource_id) for resource_id in resources]
        
        # Run all concurrently
        results = await asyncio.gather(*tasks)
        
        # All resources should be created
        self.assertEqual(set(results), set(resources))
        
        # Count resources
        counts = await self.manager.count_resources_by_state()
        self.assertEqual(counts[str(ResourceState.ACTIVE)], len(resources))


if __name__ == '__main__':
    unittest.main()