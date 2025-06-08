import unittest
import pytest
import asyncio
import os
import shutil
import tempfile
import datetime
import time
from pathlib import Path

from resources.state import (
    StateEntry,
    StateSnapshot,
    MemoryStateBackend,
    FileStateBackend,
    SQLiteStateBackend,
    StateStorageBackend,
)
from resources.common import ResourceState, ResourceType


def async_test(coro):
    """Helper decorator to run async tests"""
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper


class TestMemoryStateBackend(unittest.TestCase):
    """Tests for in-memory state storage backend"""
    
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
    async def test_nonexistent_state(self):
        """Test loading a state that doesn't exist"""
        loaded = await self.backend.load_state("nonexistent")
        self.assertIsNone(loaded)
        
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

    @async_test
    async def test_update_existing_state(self):
        """Test updating an existing state"""
        resource_id = "test-update"
        
        # Create initial state
        initial_state = StateEntry(
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            metadata={"version": 1}
        )
        await self.backend.save_state(resource_id, initial_state)
        
        # Update with new state
        updated_state = StateEntry(
            state=ResourceState.PAUSED,
            resource_type=ResourceType.COMPUTE,
            metadata={"version": 2}
        )
        await self.backend.save_state(resource_id, updated_state)
        
        # Load the current state
        current = await self.backend.load_state(resource_id)
        
        # Verify it's the updated state
        self.assertEqual(current.state, ResourceState.PAUSED)
        self.assertEqual(current.metadata["version"], 2)
        
        # Verify history contains both states
        history = await self.backend.load_history(resource_id)
        self.assertEqual(len(history), 2)


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


# Run this class only if this file is executed directly
if __name__ == '__main__':
    unittest.main()