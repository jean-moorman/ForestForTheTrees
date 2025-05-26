"""
Tests for PrioritizedLockManager with resource lifecycle management.
"""

import unittest
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any, List, Set
import logging
import pytest
import pytest_asyncio

from resources.base import PrioritizedLockManager
from resources.base_resource import BaseResource
from resources.events import EventQueue

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Fixtures
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

class LockManagerResource(BaseResource):
    """Resource that uses PrioritizedLockManager for testing."""
    
    def __init__(self, resource_id: str, event_queue: Optional[EventQueue] = None):
        super().__init__(resource_id, None, event_queue)
        self._lock_manager = PrioritizedLockManager(writer_priority=True)
        self._shared_data = {}
        self._access_count = 0
        self._access_errors = []
        
    async def initialize(self) -> bool:
        """Initialize the resource."""
        return await super().initialize()
        
    async def write_data(self, key: str, value: Any, timeout: float = 5.0) -> bool:
        """Write data with lock protection."""
        try:
            # Acquire write lock
            async with await self._lock_manager.acquire_write(
                timeout=timeout, 
                track_id=f"write_{key}",
                owner_info=f"write_{key}_{value}"
            ):
                # Update shared data
                self._shared_data[key] = value
                # Track access
                self._access_count += 1
                # Simulate some work
                await asyncio.sleep(0.01)
                return True
        except Exception as e:
            self._access_errors.append(f"Write error for {key}: {str(e)}")
            return False
            
    async def read_data(self, key: str, timeout: float = 5.0) -> Any:
        """Read data with lock protection."""
        try:
            # Acquire read lock
            async with await self._lock_manager.acquire_read(
                timeout=timeout, 
                track_id=f"read_{key}",
                owner_info=f"read_{key}"
            ):
                # Read shared data
                value = self._shared_data.get(key)
                # Track access
                self._access_count += 1
                # Simulate some work
                await asyncio.sleep(0.01)
                return value
        except Exception as e:
            self._access_errors.append(f"Read error for {key}: {str(e)}")
            return None
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get lock metrics and access statistics."""
        return {
            "lock_metrics": self._lock_manager.get_lock_metrics(),
            "access_count": self._access_count,
            "access_errors": self._access_errors,
            "data_size": len(self._shared_data),
            "owner_info": self._lock_manager.get_owner_info()
        }


class TestPrioritizedLockManager(unittest.TestCase):
    """Test cases for PrioritizedLockManager."""
    
    @pytest.mark.asyncio
    async def test_basic_lock_operations(self):
        """Test basic lock operations."""
        # Create a lock manager
        lock_manager = PrioritizedLockManager()
        
        # Acquire read lock
        read_lock = await lock_manager.acquire_read(track_id="test_read")
        self.assertTrue(read_lock.locked())
        
        # Release read lock
        await lock_manager.release_read(track_id="test_read")
        
        # Acquire write lock
        write_lock = await lock_manager.acquire_write(track_id="test_write")
        self.assertTrue(write_lock.locked())
        
        # Release write lock
        await lock_manager.release_write(track_id="test_write")
        
        # Check metrics
        metrics = lock_manager.get_lock_metrics()
        self.assertEqual(metrics["read_wait_count"], 1)
        self.assertEqual(metrics["write_wait_count"], 1)
    
    @pytest.mark.asyncio
    async def test_lock_manager_resource(self, event_queue):
        """Test resource using lock manager for thread safety."""
        # Create a resource
        resource = LockManagerResource("lock_test_resource", event_queue)
        await resource.initialize()
        
        # Write some data
        success = await resource.write_data("key1", "value1")
        self.assertTrue(success)
        
        # Read the data
        value = await resource.read_data("key1")
        self.assertEqual(value, "value1")
        
        # Check metrics
        metrics = resource.get_metrics()
        self.assertEqual(metrics["access_count"], 2)
        self.assertEqual(len(metrics["access_errors"]), 0)
        
        # Clean up
        await resource.terminate()
    
    @pytest.mark.asyncio
    async def test_concurrent_lock_access(self, event_queue):
        """Test concurrent access to locks."""
        # Create a resource
        resource = LockManagerResource("concurrent_lock_resource", event_queue)
        await resource.initialize()
        
        # Set up async operations
        async def write_operation(key, value):
            return await resource.write_data(key, value)
            
        async def read_operation(key):
            return await resource.read_data(key)
        
        # Run multiple operations concurrently
        tasks = []
        for i in range(5):
            key = f"concurrent_key_{i}"
            # Add write task
            tasks.append(asyncio.create_task(write_operation(key, f"value_{i}")))
            # Add read tasks (multiple readers can access simultaneously)
            for j in range(3):
                tasks.append(asyncio.create_task(read_operation(key)))
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check results
        for result in results:
            # Ensure no exceptions were raised
            self.assertNotIsInstance(result, Exception)
        
        # Check metrics
        metrics = resource.get_metrics()
        self.assertEqual(metrics["access_count"], 20)  # 5 writes + 15 reads
        self.assertEqual(len(metrics["access_errors"]), 0)
        
        # Clean up
        await resource.terminate()
    
    @pytest.mark.asyncio
    async def test_lock_timeout(self):
        """Test lock timeout behavior."""
        # Create a lock manager
        lock_manager = PrioritizedLockManager(writer_priority=True)
        
        # Acquire write lock (blocking)
        write_lock = await lock_manager.acquire_write(track_id="blocker")
        
        # Try to acquire read lock with short timeout (should fail)
        with self.assertRaises(asyncio.TimeoutError):
            await lock_manager.acquire_read(timeout=0.1, track_id="timeout_read")
        
        # Release write lock
        await lock_manager.release_write(track_id="blocker")
    
    @pytest.mark.asyncio
    async def test_concurrent_threads(self, event_queue):
        """Test access to locks from multiple threads."""
        # Create a resource
        resource = LockManagerResource("multithreaded_resource", event_queue)
        await resource.initialize()
        
        # Create an event loop for threads to use
        loop = asyncio.get_event_loop()
        
        # Number of threads and operations
        num_threads = 5
        operations_per_thread = 10
        
        # Counters for tracking operations (thread-safe)
        success_count = 0
        failure_count = 0
        counter_lock = threading.RLock()
        
        # Define worker function
        def worker(thread_id):
            nonlocal success_count, failure_count
            
            thread_success = 0
            thread_failure = 0
            
            for i in range(operations_per_thread):
                # Alternate between read and write operations
                if i % 2 == 0:
                    # Write operation
                    key = f"thread_{thread_id}_key_{i}"
                    future = asyncio.run_coroutine_threadsafe(
                        resource.write_data(key, f"thread_{thread_id}_value_{i}"),
                        loop
                    )
                    try:
                        result = future.result(timeout=5)
                        if result:
                            thread_success += 1
                        else:
                            thread_failure += 1
                    except Exception:
                        thread_failure += 1
                else:
                    # Read operation
                    key = f"thread_{thread_id}_key_{i-1}"  # Read previous key
                    future = asyncio.run_coroutine_threadsafe(
                        resource.read_data(key),
                        loop
                    )
                    try:
                        result = future.result(timeout=5)
                        if result == f"thread_{thread_id}_value_{i-1}":
                            thread_success += 1
                        else:
                            thread_failure += 1
                    except Exception:
                        thread_failure += 1
            
            # Update shared counters with thread safety
            with counter_lock:
                success_count += thread_success
                failure_count += thread_failure
        
        # Start worker threads
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            
            # Wait for all threads to complete
            for future in futures:
                future.result()
        
        # Verify results
        metrics = resource.get_metrics()
        
        self.assertEqual(success_count + failure_count, num_threads * operations_per_thread)
        self.assertEqual(failure_count, 0, f"Thread failures detected: {metrics['access_errors']}")
        
        # Check owner tracking
        owner_info = metrics["owner_info"]
        self.assertEqual(len(owner_info["read_owners"]), 0)  # All locks should be released
        self.assertIsNone(owner_info["write_owner"])  # No active writer
        
        # Clean up
        await resource.terminate()
        

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])