import unittest
import asyncio
import os
import shutil
import tempfile
import datetime
import time
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Import from state module
from resources.state.models import StateEntry, StateSnapshot
from resources.state.backends.memory import MemoryStateBackend
from resources.state.backends.file import FileStateBackend
from resources.state.backends.sqlite import SQLiteStateBackend
from resources.common import ResourceState, ResourceType
from resources.events import EventQueue

def async_test(coro):
    """Decorator for async test methods"""
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
            
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper

class TestFileBackendConcurrency(unittest.TestCase):
    """Test concurrency handling in FileStateBackend"""
    
    def setUp(self):
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.backend = FileStateBackend(self.temp_dir)
        
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)
        
    @async_test
    async def test_concurrent_save_same_resource(self):
        """Test concurrent save operations on the same resource"""
        resource_id = "test-resource"
        
        # Number of concurrent operations
        concurrency = 20
        
        # Create a list of state entries with different timestamps
        state_entries = []
        for i in range(concurrency):
            state_entries.append(StateEntry(
                state=ResourceState.ACTIVE if i % 2 == 0 else ResourceState.PAUSED,
                resource_type=ResourceType.COMPUTE,
                metadata={"operation": i, "timestamp": time.time()}
            ))
            
        # Launch concurrent save operations
        tasks = []
        for entry in state_entries:
            tasks.append(self.backend.save_state(resource_id, entry))
            
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        
        # All operations should succeed
        self.assertTrue(all(results))
        
        # Load the state - should be one of the entries
        state = await self.backend.load_state(resource_id)
        self.assertIsNotNone(state)
        self.assertIn("operation", state.metadata)
        
        # Get history - should include all entries
        history = await self.backend.load_history(resource_id)
        self.assertEqual(len(history), concurrency)
        
        # Verify that each operation is in the history
        operations = set(entry.metadata["operation"] for entry in history)
        self.assertEqual(len(operations), concurrency)
        
    @async_test
    async def test_concurrent_save_different_resources(self):
        """Test concurrent save operations on different resources"""
        concurrency = 50
        resource_ids = [f"resource-{i}" for i in range(concurrency)]
        
        # Create async tasks to save state for each resource
        tasks = []
        for i, resource_id in enumerate(resource_ids):
            entry = StateEntry(
                state=ResourceState.ACTIVE,
                resource_type=ResourceType.COMPUTE,
                metadata={"resource_index": i}
            )
            tasks.append(self.backend.save_state(resource_id, entry))
            
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # All operations should succeed
        self.assertTrue(all(results))
        
        # Verify that each resource has a state
        for i, resource_id in enumerate(resource_ids):
            state = await self.backend.load_state(resource_id)
            self.assertIsNotNone(state)
            self.assertEqual(state.metadata["resource_index"], i)
            
    @async_test
    async def test_concurrent_read_write(self):
        """Test concurrent read and write operations"""
        resource_id = "test-resource"
        
        # Initial state
        initial_state = StateEntry(
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            metadata={"version": 0}
        )
        await self.backend.save_state(resource_id, initial_state)
        
        # Number of read and write operations
        num_reads = 20
        num_writes = 10
        
        # Create read tasks
        read_tasks = [self.backend.load_state(resource_id) for _ in range(num_reads)]
        
        # Create write tasks
        write_tasks = []
        for i in range(num_writes):
            entry = StateEntry(
                state=ResourceState.PAUSED if i % 2 == 0 else ResourceState.ACTIVE,
                resource_type=ResourceType.COMPUTE,
                metadata={"version": i + 1}
            )
            write_tasks.append(self.backend.save_state(resource_id, entry))
            
        # Combine all tasks and run concurrently
        all_tasks = read_tasks + write_tasks
        random.shuffle(all_tasks)  # Randomize order of execution
        
        # Run all tasks
        results = await asyncio.gather(*all_tasks)
        
        # All tasks should complete
        self.assertEqual(len(results), num_reads + num_writes)
        
        # Final state should be one of the written states
        final_state = await self.backend.load_state(resource_id)
        self.assertIsNotNone(final_state)
        self.assertIn("version", final_state.metadata)
        
        # History should include all writes plus initial
        history = await self.backend.load_history(resource_id)
        self.assertEqual(len(history), num_writes + 1)
        
    @async_test
    async def test_file_locking_stress(self):
        """Stress test file locking mechanism"""
        resource_id = "test-resource"
        num_operations = 50
        
        # Function to update state with retries
        async def update_state(index):
            # Add some random delay to increase contention
            await asyncio.sleep(random.random() * 0.01)
            
            # Get current state
            current = await self.backend.load_state(resource_id)
            version = 0 if current is None else (current.metadata.get("version", 0) + 1)
            
            # Create new state
            new_state = StateEntry(
                state=ResourceState.ACTIVE,
                resource_type=ResourceType.COMPUTE,
                metadata={"version": version, "updater": index}
            )
            
            # Save the state
            return await self.backend.save_state(resource_id, new_state)
        
        # Create concurrent update tasks
        tasks = [update_state(i) for i in range(num_operations)]
        
        # Run all tasks
        results = await asyncio.gather(*tasks)
        
        # All operations should succeed
        self.assertTrue(all(results))
        
        # Check the history
        history = await self.backend.load_history(resource_id)
        
        # Should have the correct number of history entries
        self.assertEqual(len(history), num_operations)
        
        # Check for monotonically increasing versions
        versions = [entry.metadata.get("version", 0) for entry in history]
        self.assertEqual(sorted(versions), versions)
        
    @async_test
    async def test_snapshot_concurrency(self):
        """Test concurrent snapshot operations"""
        resource_id = "test-resource"
        num_snapshots = 15
        
        # Create snapshot tasks
        tasks = []
        for i in range(num_snapshots):
            snapshot = StateSnapshot(
                state={"state": ResourceState.ACTIVE, "index": i},
                resource_type=ResourceType.COMPUTE,
                metadata={"snapshot_index": i}
            )
            tasks.append(self.backend.save_snapshot(resource_id, snapshot))
            
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # All operations should succeed
        self.assertTrue(all(results))
        
        # Load snapshots
        snapshots = await self.backend.load_snapshots(resource_id)
        
        # Should have all snapshots
        self.assertEqual(len(snapshots), num_snapshots)
        
        # Each snapshot should be present
        indices = set(snapshot.metadata.get("snapshot_index") for snapshot in snapshots)
        self.assertEqual(len(indices), num_snapshots)
        

class TestSQLiteBackendConcurrency(unittest.TestCase):
    """Test concurrency handling in SQLiteStateBackend"""
    
    def setUp(self):
        # Create a temporary directory for database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_state.db")
        self.backend = SQLiteStateBackend(self.db_path)
        
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)
        
    @async_test
    async def test_concurrent_save_same_resource(self):
        """Test concurrent save operations on the same resource"""
        resource_id = "test-resource"
        
        # Number of concurrent operations
        concurrency = 20
        
        # Create a list of state entries with different timestamps
        state_entries = []
        for i in range(concurrency):
            state_entries.append(StateEntry(
                state=ResourceState.ACTIVE if i % 2 == 0 else ResourceState.PAUSED,
                resource_type=ResourceType.COMPUTE,
                metadata={"operation": i, "timestamp": time.time()}
            ))
            
        # Launch concurrent save operations
        tasks = []
        for entry in state_entries:
            tasks.append(self.backend.save_state(resource_id, entry))
            
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        
        # All operations should succeed
        self.assertTrue(all(results))
        
        # Load the state - should be one of the entries
        state = await self.backend.load_state(resource_id)
        self.assertIsNotNone(state)
        self.assertIn("operation", state.metadata)
        
        # Get history - should include all entries
        history = await self.backend.load_history(resource_id)
        self.assertEqual(len(history), concurrency)
        
        # Verify that each operation is in the history
        operations = set(entry.metadata["operation"] for entry in history)
        self.assertEqual(len(operations), concurrency)
        
    @async_test
    async def test_database_stats(self):
        """Test database statistics functionality"""
        # Create multiple resources
        num_resources = 10
        for i in range(num_resources):
            resource_id = f"resource-{i}"
            state = ResourceState.ACTIVE if i % 2 == 0 else ResourceState.PAUSED
            await self.backend.save_state(resource_id, StateEntry(
                state=state,
                resource_type=ResourceType.COMPUTE,
                metadata={"index": i}
            ))
            
            # Add snapshots for even-numbered resources
            if i % 2 == 0:
                await self.backend.save_snapshot(resource_id, StateSnapshot(
                    state={"state": state, "metadata": {"index": i}},
                    resource_type=ResourceType.COMPUTE
                ))
        
        # Get database stats
        stats = await self.backend.get_database_stats()
        
        # Verify stats
        self.assertEqual(stats["resources_count"], num_resources)
        self.assertEqual(stats["history_entries_count"], num_resources)
        self.assertEqual(stats["snapshots_count"], num_resources // 2)
        self.assertGreater(stats["database_size_bytes"], 0)
        
        # Resource states count
        active_count = stats["resource_states"].get("ResourceState:ACTIVE", 0)
        paused_count = stats["resource_states"].get("ResourceState:PAUSED", 0)
        self.assertEqual(active_count + paused_count, num_resources)
        
    @async_test
    async def test_database_optimization(self):
        """Test database optimization functionality"""
        # Create many resources to increase database size
        num_resources = 20
        for i in range(num_resources):
            resource_id = f"resource-{i}"
            for j in range(5):  # Multiple states per resource
                await self.backend.save_state(resource_id, StateEntry(
                    state=ResourceState.ACTIVE,
                    resource_type=ResourceType.COMPUTE,
                    metadata={"index": i, "update": j}
                ))
        
        # Get initial database size
        initial_stats = await self.backend.get_database_stats()
        initial_size = initial_stats["database_size_bytes"]
        
        # Run optimization
        result = await self.backend.optimize_database()
        self.assertTrue(result)
        
        # Get new size
        final_stats = await self.backend.get_database_stats()
        final_size = final_stats["database_size_bytes"]
        
        # Size should not increase significantly (might decrease or stay similar)
        self.assertLessEqual(final_size, initial_size * 1.1)  # Allow slight increase due to page allocation


if __name__ == '__main__':
    unittest.main()