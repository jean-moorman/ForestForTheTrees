"""
Tests for resource lifecycle management.

This module provides test cases for the resource lifecycle management features
implemented in BaseResource and BaseManager classes.
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

from resources.base_resource import BaseResource
from resources.base import BaseManager, CleanupConfig, CleanupPolicy, ManagerConfig
from resources.events import EventQueue
from resources.common import ResourceType
from resources.monitoring import HealthTracker, MemoryMonitor, SystemMonitor, CircuitBreakerConfig

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test fixtures
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

# Test classes
class TestResource(BaseResource):
    """Test implementation of BaseResource for testing resource lifecycle."""
    
    def __init__(self, resource_id: str, event_bus: Optional[EventQueue] = None):
        super().__init__(resource_id=resource_id, event_bus=event_bus)
        self.initialize_called = False
        self.terminate_called = False
        self.custom_cleanup_called = False
        
    async def initialize(self) -> bool:
        """Test implementation of initialize."""
        await super().initialize()
        self.initialize_called = True
        return True
        
    async def terminate(self) -> bool:
        """Test implementation of terminate."""
        await super().terminate()
        self.terminate_called = True
        return True
        
    async def custom_cleanup(self) -> None:
        """Custom cleanup method for testing."""
        self.custom_cleanup_called = True


class TestManager(BaseManager):
    """Test implementation of BaseManager for testing resource lifecycle."""
    
    def __init__(self, event_queue: EventQueue, resource_id: str = "test_manager"):
        super().__init__(
            event_queue=event_queue,
            resource_id=resource_id,
            cleanup_config=CleanupConfig(policy=CleanupPolicy.TTL),
            manager_config=ManagerConfig()
        )
        self.owned_resources_cleaned = []
        
    async def _cleanup_resources(self, force: bool = False) -> None:
        """Implementation of abstract method."""
        # Track owned resources that were cleaned
        with self._manager_lock:
            self.owned_resources_cleaned = list(self._owned_resources.keys())


class ResourceLifecycleTest:
    """Utility class for testing resource lifecycle management."""
    
    @staticmethod
    async def create_resource_tree(event_queue: EventQueue) -> Dict[str, Any]:
        """
        Create a tree of resources with dependencies for testing.
        
        Args:
            event_queue: The event queue to use for resources
            
        Returns:
            Dict containing the created resources
        """
        # Create a root manager
        root_manager = TestManager(event_queue, resource_id="root_manager")
        
        # Create child resources
        child_resources = {}
        for i in range(5):
            resource_id = f"resource_{i}"
            resource = TestResource(resource_id, event_queue)
            child_resources[resource_id] = resource
            
            # Register with root manager
            root_manager.register_owned_resource(resource_id, resource)
            
        # Create some dependencies between resources
        root_manager.register_owned_resource("dependent_resource", 
                                         TestResource("dependent_resource", event_queue),
                                         depends_on=["resource_0", "resource_1"])
        
        # Return all resources for testing
        return {
            "root_manager": root_manager,
            "child_resources": child_resources,
            "dependent_resource": root_manager._owned_resources.get("dependent_resource")
        }
        
    @staticmethod
    async def test_concurrent_access(resource: BaseResource, num_threads: int = 10, 
                                  operations_per_thread: int = 100) -> Dict[str, Any]:
        """
        Test concurrent access to a resource from multiple threads.
        
        Args:
            resource: The resource to test
            num_threads: Number of threads to use
            operations_per_thread: Number of operations per thread
            
        Returns:
            Dict containing test results
        """
        # Counters for tracking operations
        successful_operations = 0
        failed_operations = 0
        thread_errors = []
        lock = threading.RLock()
        
        # Create an event loop for each thread
        loop = asyncio.get_event_loop()
        
        # Define worker function
        def worker(thread_id: int):
            nonlocal successful_operations, failed_operations
            
            # Set up event loop for this thread
            asyncio.set_event_loop(loop)
            
            local_success = 0
            local_errors = []
            
            for i in range(operations_per_thread):
                try:
                    # Perform some operation on the resource
                    task = asyncio.run_coroutine_threadsafe(
                        resource._emit_lifecycle_event(
                            f"test_event_{thread_id}_{i}",
                            {"thread_id": thread_id, "operation": i}
                        ),
                        loop
                    )
                    
                    # Wait for the result
                    task.result(timeout=5)
                    local_success += 1
                    
                except Exception as e:
                    local_errors.append((thread_id, i, str(e)))
            
            # Update shared counters
            with lock:
                successful_operations += local_success
                failed_operations += len(local_errors)
                thread_errors.extend(local_errors)
        
        # Start worker threads
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            
            # Wait for all threads to complete
            for future in futures:
                future.result()
        
        # Return results
        return {
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "thread_errors": thread_errors,
            "expected_operations": num_threads * operations_per_thread
        }

    @staticmethod
    async def test_resource_ownership_cascade(manager: BaseManager) -> Dict[str, Any]:
        """
        Test that resources are properly cleaned up when their owner is terminated.
        
        Args:
            manager: The manager to test
            
        Returns:
            Dict containing test results
        """
        # Initialize the manager
        await manager.initialize()
        
        # Get owned resources before termination
        with manager._manager_lock:
            owned_resource_ids = set(manager._owned_resources.keys())
            owned_resources = {k: v for k, v in manager._owned_resources.items()}
        
        # Terminate the manager
        await manager.terminate()
        
        # Check that all owned resources were terminated
        resources_terminated = []
        resources_not_terminated = []
        
        for resource_id, resource in owned_resources.items():
            if isinstance(resource, TestResource):
                if resource.terminate_called:
                    resources_terminated.append(resource_id)
                else:
                    resources_not_terminated.append(resource_id)
        
        # Return results
        return {
            "owned_resource_ids": owned_resource_ids,
            "resources_terminated": resources_terminated,
            "resources_not_terminated": resources_not_terminated,
            "manager_cleaned_resources": manager.owned_resources_cleaned if isinstance(manager, TestManager) else []
        }


# Test cases
class TestResourceLifecycle(unittest.TestCase):
    """Test cases for resource lifecycle management."""
    
    @pytest.mark.asyncio
    async def test_basic_resource_lifecycle(self, event_queue):
        """Test basic resource lifecycle with initialization and termination."""
        # Create a test resource
        resource = TestResource("test_resource", event_queue)
        
        # Verify initial state
        self.assertFalse(resource.is_initialized)
        self.assertFalse(resource.is_terminated)
        self.assertFalse(resource.initialize_called)
        self.assertFalse(resource.terminate_called)
        
        # Initialize the resource
        success = await resource.initialize()
        self.assertTrue(success)
        self.assertTrue(resource.is_initialized)
        self.assertTrue(resource.initialize_called)
        
        # Terminate the resource
        success = await resource.terminate()
        self.assertTrue(success)
        self.assertTrue(resource.is_terminated)
        self.assertTrue(resource.terminate_called)
        
        # Check that the resource was unregistered from global registry
        self.assertIsNone(BaseResource.get_resource("test_resource"))
    
    @pytest.mark.asyncio
    async def test_manager_resource_ownership(self, event_queue):
        """Test resource ownership with cascade termination."""
        # Create a resource tree
        resources = await ResourceLifecycleTest.create_resource_tree(event_queue)
        root_manager = resources["root_manager"]
        
        # Test resource cascade
        cascade_results = await ResourceLifecycleTest.test_resource_ownership_cascade(root_manager)
        
        # Verify all resources were properly terminated
        self.assertEqual(len(cascade_results["resources_not_terminated"]), 0)
        self.assertGreater(len(cascade_results["resources_terminated"]), 0)
        
        # Verify dependency order was respected
        if "dependent_resource" in cascade_results["resources_terminated"]:
            dep_idx = cascade_results["resources_terminated"].index("dependent_resource")
            res0_idx = cascade_results["resources_terminated"].index("resource_0")
            res1_idx = cascade_results["resources_terminated"].index("resource_1")
            
            # Dependent resource should be cleaned up before its dependencies
            self.assertLess(dep_idx, res0_idx)
            self.assertLess(dep_idx, res1_idx)
    
    @pytest.mark.asyncio
    async def test_concurrent_resource_access(self, event_queue):
        """Test concurrent access to resources from multiple threads."""
        # Create a test resource
        resource = TestResource("concurrent_test", event_queue)
        await resource.initialize()
        
        # Test concurrent access
        concurrency_results = await ResourceLifecycleTest.test_concurrent_access(
            resource, num_threads=5, operations_per_thread=20
        )
        
        # Verify all operations succeeded
        self.assertEqual(concurrency_results["failed_operations"], 0)
        self.assertEqual(concurrency_results["successful_operations"], 
                     concurrency_results["expected_operations"])
        
        # Clean up
        await resource.terminate()
    
    @pytest.mark.asyncio
    async def test_resource_registry(self, event_queue):
        """Test the global resource registry."""
        # Create multiple resources
        resources = []
        for i in range(10):
            resource = TestResource(f"registry_test_{i}", event_queue)
            await resource.initialize()
            resources.append(resource)
            
        # Verify all resources are in the registry
        for i in range(10):
            resource_id = f"registry_test_{i}"
            self.assertIsNotNone(BaseResource.get_resource(resource_id))
            
        # Get a list of all resources
        all_resources = BaseResource.list_resources()
        self.assertGreaterEqual(len(all_resources), 10)
        
        # Terminate some resources
        for i in range(5):
            await resources[i].terminate()
            
        # Verify they're no longer in the registry
        for i in range(5):
            resource_id = f"registry_test_{i}"
            self.assertIsNone(BaseResource.get_resource(resource_id))
            
        # Verify the remaining resources are still in the registry
        for i in range(5, 10):
            resource_id = f"registry_test_{i}"
            self.assertIsNotNone(BaseResource.get_resource(resource_id))
            
        # Clean up remaining resources
        for i in range(5, 10):
            await resources[i].terminate()
    
    @pytest.mark.asyncio
    async def test_terminate_all_resources(self, event_queue):
        """Test the terminate_all class method."""
        # Create multiple resources
        resources = []
        for i in range(5):
            resource = TestResource(f"terminate_all_test_{i}", event_queue)
            await resource.initialize()
            resources.append(resource)
            
        # Terminate all resources
        terminated_count = await BaseResource.terminate_all()
        
        # Verify all resources are terminated
        self.assertGreaterEqual(terminated_count, 5)
        
        # Verify they're no longer in the registry
        for i in range(5):
            resource_id = f"terminate_all_test_{i}"
            self.assertIsNone(BaseResource.get_resource(resource_id))
            
    @pytest.mark.asyncio
    async def test_resource_reinitialization(self, event_queue):
        """Test that terminated resources cannot be reinitialized."""
        # Create a test resource
        resource = TestResource("reinit_test", event_queue)
        
        # Initialize
        success = await resource.initialize()
        self.assertTrue(success)
        
        # Terminate
        await resource.terminate()
        
        # Try to reinitialize
        success = await resource.initialize()
        self.assertFalse(success)
        
    @pytest.mark.asyncio
    async def test_manager_initialize_terminate(self, event_queue):
        """Test the complete initialization and termination cycle of a manager."""
        # Create a manager
        manager = TestManager(event_queue)
        
        # Initialize
        success = await manager.initialize()
        self.assertTrue(success)
        self.assertTrue(manager.is_initialized)
        
        # Terminate
        success = await manager.terminate()
        self.assertTrue(success)
        self.assertTrue(manager.is_terminated)
        
        # Verify it's no longer in the registry
        self.assertIsNone(BaseResource.get_resource(manager.resource_id))


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])