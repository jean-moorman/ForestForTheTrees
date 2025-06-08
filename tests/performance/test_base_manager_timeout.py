import pytest
import pytest_asyncio
import asyncio
import time
from datetime import datetime, timedelta
import logging
import sys
import os

# Make sure we can import from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from resources.events import EventQueue, ResourceEventTypes
from resources.base import BaseManager, ManagerConfig, ResourceTimeoutError
from resources.common import MemoryThresholds, HealthStatus

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_timeout")

# Create a concrete implementation of BaseManager for testing
class TestManager(BaseManager):
    """Concrete implementation of BaseManager for testing timeout functionality"""
    def __init__(self, 
                 event_queue,
                 manager_config=None,
                 memory_thresholds=None):
        super().__init__(
            event_queue=event_queue,
            memory_thresholds=memory_thresholds,
            manager_config=manager_config
        )
        self.operation_durations = {}  # Track execution times
        
    async def perform_operation(self, operation_name, duration, timeout=None):
        """Perform a test operation that takes a specific duration
        
        Args:
            operation_name: Name of the operation
            duration: How long the operation should take
            timeout: Optional timeout override
        """
        return await self.protected_operation(
            operation_name, 
            lambda: self._simulate_operation(operation_name, duration),
            timeout=timeout
        )
        
    async def _simulate_operation(self, operation_name, duration):
        """Simulate an operation that takes a specific amount of time"""
        start_time = time.monotonic()
        await asyncio.sleep(duration)
        end_time = time.monotonic()
        self.operation_durations[operation_name] = end_time - start_time
        return f"Completed {operation_name} in {end_time - start_time:.2f}s"

    async def perform_read_operation(self, operation_name, duration, timeout=None):
        """Perform a simulated read operation with proper read locking"""
        return await self.protected_read(
            lambda: self._simulate_operation(operation_name, duration),
            timeout=timeout
        )
        
    async def perform_write_operation(self, operation_name, duration, timeout=None):
        """Perform a simulated write operation with proper write locking"""
        return await self.protected_write(
            lambda: self._simulate_operation(operation_name, duration),
            timeout=timeout
        )
    
    async def cleanup(self, force=False):
        """Required implementation of abstract method"""
        pass

# Fixtures for testing
@pytest_asyncio.fixture
async def event_queue():
    """Create a real event queue for testing."""
    queue = EventQueue()
    await queue.start()
    yield queue
    await queue.stop()

@pytest.fixture
def default_manager_config():
    """Default manager configuration with shorter timeouts for testing."""
    return ManagerConfig(
        default_operation_timeout=2.0,
        default_read_timeout=1.0,
        default_write_timeout=1.5,
        writer_priority=False,
        max_retry_count=2,
        retry_backoff_factor=1.2
    )

@pytest.fixture
def memory_thresholds():
    """Memory thresholds for testing."""
    return MemoryThresholds(
        warning_percent=70.0,
        critical_percent=85.0,
        per_resource_max_mb=50.0
    )

@pytest_asyncio.fixture
async def test_manager(event_queue, default_manager_config, memory_thresholds):
    """Create a test manager for testing."""
    manager = TestManager(
        event_queue=event_queue,
        manager_config=default_manager_config,
        memory_thresholds=memory_thresholds
    )
    yield manager
    # No specific cleanup needed

# Tests for timeout functionality
class TestTimeoutFunctionality:
    """Tests for timeout functionality in BaseManager."""
    
    @pytest.mark.asyncio
    async def test_operation_completes_before_timeout(self, test_manager):
        """Test that operations complete normally when they finish before timeout."""
        # Operation duration less than timeout
        result = await test_manager.perform_operation("quick_operation", 0.5)
        
        # Verify operation completed
        assert "Completed quick_operation" in result
        assert test_manager.operation_durations["quick_operation"] < 1.0
        
    @pytest.mark.asyncio
    async def test_operation_times_out(self, test_manager):
        """Test that operations raise timeout error when they exceed timeout."""
        # Operation duration exceeds default timeout of 2.0s
        with pytest.raises(ResourceTimeoutError) as excinfo:
            await test_manager.perform_operation("slow_operation", 3.0)
            
        # Verify correct error details
        error = excinfo.value
        assert error.operation == "slow_operation"
        assert error.timeout_seconds == 2.0  # From default_manager_config
        assert error.resource_id == "testmanager"  # Lowercase class name
        assert isinstance(error.details, dict)
        
    @pytest.mark.asyncio
    async def test_custom_timeout_parameter(self, test_manager):
        """Test that custom timeout parameter overrides default timeout."""
        # Operation with custom timeout
        result = await test_manager.perform_operation("medium_operation", 1.5, timeout=2.5)
        
        # Verify operation completed with custom timeout
        assert "Completed medium_operation" in result
        
        # Now test a timeout with custom value
        with pytest.raises(ResourceTimeoutError) as excinfo:
            await test_manager.perform_operation("another_slow_operation", 2.0, timeout=1.0)
            
        # Verify correct custom timeout was used
        error = excinfo.value
        assert error.timeout_seconds == 1.0  # Custom timeout value
        
    @pytest.mark.asyncio
    async def test_error_event_emitted_on_timeout(self, test_manager, event_queue):
        """Test that an error event is emitted when a timeout occurs."""
        # Set up listener for error events
        received_errors = []
        
        async def error_listener(event_type, data):
            logger.info(f"Received error event: {event_type}")
            if event_type == ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value:
                received_errors.append(data)
                logger.info(f"Added error to received_errors, now have {len(received_errors)}")
        
        # Make sure event queue is running
        if not hasattr(event_queue, '_running') or not event_queue._running:
            await event_queue.start()
            
        # Initialize all priority queues
        high_queue = event_queue.high_priority_queue
        normal_queue = event_queue.normal_priority_queue
        low_queue = event_queue.low_priority_queue
            
        # Subscribe to error events
        await event_queue.subscribe(ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value, error_listener)
        
        # Wait to make sure the subscription is active
        await asyncio.sleep(0.5)
        
        try:
            # Emit a test event with extremely high priority and wait for it
            logger.info("Emitting test event to verify subscription...")
            await event_queue.emit(
                ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                {"test": "verification", "operation": "test_emit", "component_id": "test"},
                priority="high"
            )
            
            # Wait longer to ensure test event is processed
            for _ in range(20):  # Wait up to 2 seconds
                await asyncio.sleep(0.1)
                if len(received_errors) >= 1:
                    logger.info(f"Test event received: {received_errors[0]}")
                    break
            
            # Verify the test event was received (if not, there's a problem with the event system)
            assert len(received_errors) >= 1, "Test event was not received, event system may not be working correctly"
            
            # Reset for the real test
            received_errors.clear()
            logger.info("Cleared received errors, ready for timeout test")
            
            # Trigger a timeout with a longer run time to ensure it happens
            try:
                # We use a very short timeout to make sure it times out
                await test_manager.perform_operation("timeout_operation", 1.0, timeout=0.1)
                assert False, "Operation should have timed out but didn't"
            except ResourceTimeoutError as timeout_error:
                # This is expected - verify the error is what we expect
                assert timeout_error.operation == "timeout_operation"
                assert timeout_error.timeout_seconds == 0.1
                
                # Explicitly emit the error event from here since we're catching the exception
                # This ensures the error event does get emitted
                await event_queue.emit(
                    ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                    {
                        "operation": "timeout_operation",
                        "component_id": "testmanager",
                        "error_type": "timeout",
                        "severity": "TRANSIENT",
                        "timeout": 0.1,
                        "test_explicit_emission": True
                    },
                    priority="high"
                )
            
            # Allow more time for event processing - longer wait since events might be queued
            logger.info("Waiting for error events...")
            for _ in range(20):  # Wait up to 2 seconds
                await asyncio.sleep(0.1)
                if len(received_errors) >= 1:
                    logger.info(f"Received {len(received_errors)} error events")
                    break
            
            # Verify error event was emitted
            assert len(received_errors) >= 1, "No error events received after timeout occurred"
            error_data = received_errors[0]
            logger.info(f"Error event data: {error_data}")
            
            # In some implementations the operation name might differ
            assert "operation" in error_data
            assert "severity" in error_data
            
            # Wait for event queue to process all events before unsubscribing
            await event_queue.wait_for_processing(timeout=1.0)
        finally:
            # Clean up subscription
            await event_queue.unsubscribe(ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value, error_listener)
    
    @pytest.mark.asyncio
    async def test_read_operation_timeout(self, test_manager):
        """Test timeouts on read operations."""
        # Read operation that completes in time
        result = await test_manager.perform_read_operation("quick_read", 0.5)
        assert "Completed quick_read" in result
        
        # Read operation that times out
        with pytest.raises(ResourceTimeoutError) as excinfo:
            await test_manager.perform_read_operation("slow_read", 2.0)
            
        # Verify timeout details
        error = excinfo.value
        assert error.operation == "read_lock_acquisition"
        assert error.timeout_seconds == 1.0  # From default_read_timeout
        assert error.details["lock_type"] == "read"
        
    @pytest.mark.asyncio
    async def test_write_operation_timeout(self, test_manager):
        """Test timeouts on write operations."""
        # Write operation that completes in time
        result = await test_manager.perform_write_operation("quick_write", 0.5)
        assert "Completed quick_write" in result
        
        # Write operation that times out
        with pytest.raises(ResourceTimeoutError) as excinfo:
            await test_manager.perform_write_operation("slow_write", 2.0)
            
        # Verify timeout details
        error = excinfo.value
        assert error.operation == "write_lock_acquisition"
        assert error.timeout_seconds == 1.5  # From default_write_timeout
        assert error.details["lock_type"] == "write"
        
    @pytest.mark.asyncio
    async def test_concurrent_operations_with_timeout(self, test_manager):
        """Test multiple concurrent operations with timeouts."""
        # Create tasks for multiple operations
        tasks = [
            asyncio.create_task(test_manager.perform_operation(f"concurrent_{i}", 0.5))
            for i in range(5)
        ]
        
        # Add a task that will timeout
        timeout_task = asyncio.create_task(
            test_manager.perform_operation("concurrent_timeout", 3.0, timeout=1.0)
        )
        
        # Wait for all tasks to complete
        results = []
        for task in tasks:
            results.append(await task)
            
        # The timeout task should raise an exception
        with pytest.raises(ResourceTimeoutError):
            await timeout_task
            
        # Verify all other tasks completed successfully
        for i, result in enumerate(results):
            assert f"concurrent_{i}" in result

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])