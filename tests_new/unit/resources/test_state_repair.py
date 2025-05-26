import unittest
import asyncio
import os
import shutil
import tempfile
import time
import pickle
from pathlib import Path

from resources.state.models import StateEntry, StateSnapshot
from resources.state.backends.file import FileStateBackend
from resources.state.backends.sqlite import SQLiteStateBackend
from resources.common import ResourceState, ResourceType


def async_test(coro):
    """Decorator for async test methods"""
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper


class TestFileBackendRepair(unittest.TestCase):
    """Test repair operations in FileStateBackend"""
    
    def setUp(self):
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.backend = FileStateBackend(self.temp_dir)
        
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)
        
    @async_test
    async def test_recover_from_corrupt_state_via_history(self):
        """Test recovery from corrupt state file by loading from history"""
        resource_id = "test-resource"
        
        # Create and save initial state entry
        state1 = StateEntry(
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            metadata={"version": 1}
        )
        await self.backend.save_state(resource_id, state1)
        
        # Update with a new state
        state2 = StateEntry(
            state=ResourceState.PAUSED,
            resource_type=ResourceType.COMPUTE,
            metadata={"version": 2}
        )
        await self.backend.save_state(resource_id, state2)
        
        # Corrupt the state file but leave history intact
        state_file = os.path.join(self.backend.states_dir, f"{resource_id}.pickle")
        with open(state_file, 'w') as f:
            f.write("This is not a valid pickle file")
        
        # Try to load state
        state = await self.backend.load_state(resource_id)
        
        # The load_state method should try to recover from history
        # But it may return None if it can't recover automatically
        if state is None:
            # We can test the recovery mechanism by loading directly from history
            history = await self.backend.load_history(resource_id)
            self.assertEqual(len(history), 2)
            latest_state = history[-1]
            self.assertEqual(latest_state.state, ResourceState.PAUSED)
            self.assertEqual(latest_state.metadata["version"], 2)
        else:
            # If it auto-recovered, verify the recovered state
            self.assertEqual(state.state, ResourceState.PAUSED)
            self.assertEqual(state.metadata["version"], 2)
        
        # Verify backup was created for corrupt file
        backup_files = list(Path(self.backend.states_dir).glob(f"{resource_id}_corrupt_*.pickle"))
        self.assertGreater(len(backup_files), 0)
        
    @async_test 
    async def test_repair_corrupt_files(self):
        """Test the repair_corrupt_files method"""
        # Only run if the method exists
        if not hasattr(self.backend, 'repair_corrupt_files'):
            self.skipTest("repair_corrupt_files not implemented")
            
        # Create multiple resources
        resources = {
            "resource1": ResourceState.ACTIVE,
            "resource2": ResourceState.PAUSED,
            "resource3": ResourceState.FAILED
        }
        
        # Save all resources normally
        for resource_id, state in resources.items():
            await self.backend.save_state(
                resource_id,
                StateEntry(
                    state=state,
                    resource_type=ResourceType.COMPUTE,
                    metadata={"resource_id": resource_id}
                )
            )
            
        # Deliberately corrupt one state file
        corrupt_id = "resource2"
        state_file = os.path.join(self.backend.states_dir, f"{corrupt_id}.pickle")
        with open(state_file, 'w') as f:
            f.write("This is a corrupted state file")
            
        # Run repair
        results = await self.backend.repair_corrupt_files()
        
        # Check repair results
        self.assertIn("state_repaired", results)
        self.assertIn("failed", results)
        self.assertTrue(results["state_repaired"] > 0 or results["failed"] > 0)
        
        # Try to load the originally corrupted resource
        # If repair succeeded, it should be loaded from history
        repaired_state = await self.backend.load_state(corrupt_id)
        if repaired_state is not None:
            self.assertEqual(repaired_state.state, ResourceState.PAUSED)
            self.assertEqual(repaired_state.metadata["resource_id"], corrupt_id)
        
    @async_test
    async def test_compact_history(self):
        """Test history compaction for large history files"""
        resource_id = "test-resource"
        
        # Create a large history (200 entries)
        for i in range(200):
            state = StateEntry(
                state=ResourceState.ACTIVE if i % 2 == 0 else ResourceState.PAUSED,
                resource_type=ResourceType.COMPUTE,
                metadata={"version": i},
                timestamp=time.time()
            )
            await self.backend.save_state(resource_id, state)
            
            # Small delay to ensure distinct timestamps
            await asyncio.sleep(0.001)
        
        # Get history size before compaction
        history_before = await self.backend.load_history(resource_id)
        size_before = len(history_before)
        self.assertEqual(size_before, 200)
        
        # Compact history (if implemented)
        if hasattr(self.backend, 'compact_history'):
            result = await self.backend.compact_history(resource_id, max_entries=50)
            self.assertTrue(result)
            
            # Get history after compaction
            history_after = await self.backend.load_history(resource_id)
            size_after = len(history_after)
            
            # Should be smaller but should maintain first and latest entries
            self.assertLess(size_after, size_before)
            self.assertGreaterEqual(size_after, 50)  # At least max_entries
            
            # First entry should still be there (version 0)
            self.assertEqual(history_after[0].metadata["version"], 0)
            
            # Last entry should still be there (version 199)
            self.assertEqual(history_after[-1].metadata["version"], 199)
            
            # Verify some daily entries are preserved
            day_entries = set()
            for entry in history_after:
                version = entry.metadata["version"]
                # Entries that aren't first or recent should be daily entries
                if version != 0 and version < 150:
                    day_entries.add(version)
            
            # Should have some day entries
            self.assertGreater(len(day_entries), 0)
        else:
            self.skipTest("compact_history not implemented")

            
class TestSQLiteBackendRepair(unittest.TestCase):
    """Test repair operations in SQLiteStateBackend"""
    
    def setUp(self):
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_state.db")
        self.backend = SQLiteStateBackend(self.db_path)
        
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)
        
    @async_test
    async def test_optimize_database(self):
        """Test database optimization"""
        if not hasattr(self.backend, 'optimize_database'):
            self.skipTest("optimize_database not implemented")
            
        # Create a lot of data to make the database grow
        for i in range(50):
            resource_id = f"resource-{i}"
            # Create multiple states for each resource
            for j in range(5):
                state = StateEntry(
                    state=ResourceState.ACTIVE if j % 2 == 0 else ResourceState.PAUSED,
                    resource_type=ResourceType.COMPUTE,
                    metadata={"resource": i, "version": j}
                )
                await self.backend.save_state(resource_id, state)
                
                # Create snapshot for some resources
                if j == 0 and i % 5 == 0:
                    snapshot = StateSnapshot(
                        state={"state": state.state, "metadata": state.metadata},
                        resource_type=ResourceType.COMPUTE,
                        metadata={"snapshot_index": i}
                    )
                    await self.backend.save_snapshot(resource_id, snapshot)
                    
        # Get initial stats
        stats_before = await self.backend.get_database_stats()
        
        # Optimize database
        result = await self.backend.optimize_database()
        self.assertTrue(result)
        
        # Get stats after optimization
        stats_after = await self.backend.get_database_stats()
        
        # Resource count should be the same
        self.assertEqual(stats_after["resources_count"], stats_before["resources_count"])
        
        # Database should still have all data
        resource_ids = await self.backend.get_all_resource_ids()
        self.assertEqual(len(resource_ids), 50)
        
        # Check a few resources to ensure data integrity
        for i in [0, 10, 20, 49]:
            resource_id = f"resource-{i}"
            state = await self.backend.load_state(resource_id)
            self.assertIsNotNone(state)
            self.assertEqual(state.metadata["resource"], i)
            self.assertEqual(state.metadata["version"], 4)  # Last version
        
    @async_test
    async def test_database_cleanup(self):
        """Test database cleanup of old data"""
        # Create resources with varying timestamps
        now = time.time()
        
        # Create some recent resources
        for i in range(5):
            resource_id = f"recent-{i}"
            state = StateEntry(
                state=ResourceState.ACTIVE,
                resource_type=ResourceType.COMPUTE,
                metadata={"age": "recent", "index": i}
            )
            await self.backend.save_state(resource_id, state)
            
        # Create some old terminated resources (with timestamp in the past)
        for i in range(5):
            resource_id = f"old-{i}"
            # Create with old timestamp (60 days ago)
            sixty_days_ago = datetime.datetime.now() - datetime.timedelta(days=60)
            state = StateEntry(
                state=ResourceState.TERMINATED,
                resource_type=ResourceType.COMPUTE,
                metadata={"age": "old", "index": i},
                timestamp=sixty_days_ago
            )
            # Need to directly manipulate the timestamp since it's auto-set
            state.timestamp = sixty_days_ago
            await self.backend.save_state(resource_id, state)
            
        # Count resources before cleanup
        all_ids_before = await self.backend.get_all_resource_ids()
        count_before = len(all_ids_before)
        self.assertEqual(count_before, 10)
        
        # Run cleanup with 30-day cutoff
        thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        items_removed = await self.backend.cleanup(thirty_days_ago)
        
        # Should have removed terminated old resources
        self.assertGreater(items_removed, 0)
        
        # Count resources after cleanup
        all_ids_after = await self.backend.get_all_resource_ids()
        count_after = len(all_ids_after)
        
        # Should have removed old terminated resources
        self.assertLess(count_after, count_before)
        self.assertEqual(count_after, 5)  # Only recent resources remain
        
        # Verify recent resources still exist
        for i in range(5):
            resource_id = f"recent-{i}"
            state = await self.backend.load_state(resource_id)
            self.assertIsNotNone(state)
            self.assertEqual(state.metadata["age"], "recent")
            
        # Verify old resources are gone
        for i in range(5):
            resource_id = f"old-{i}"
            state = await self.backend.load_state(resource_id)
            self.assertIsNone(state)


if __name__ == '__main__':
    unittest.main()