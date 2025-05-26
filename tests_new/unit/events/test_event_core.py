import pytest
import asyncio
import pytest_asyncio
import threading
import time
from datetime import datetime
from enum import Enum
import logging
import os

# Import the modules being tested
from resources.events import Event, EventQueue, EventMonitor, ResourceEventTypes
from resources.common import ResourceType, HealthStatus, ErrorSeverity
from resources.errors import ResourceOperationError, ResourceError

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_events")

# Test data
class TestEventTypes(Enum):
    TEST_EVENT = "test_event"
    ERROR_EVENT = "error_event"
    SYSTEM_EVENT = "system_event"

# Helper class for operation context
class OperationContext:
    def __init__(self, resource_id, operation, attempt=1, recovery_attempts=0, details=None):
        self.resource_id = resource_id
        self.operation = operation
        self.attempt = attempt
        self.recovery_attempts = recovery_attempts
        self.details = details or {}

# Fixtures for async testing
@pytest_asyncio.fixture
async def event_queue():
    """Create a new event queue for each test."""
    queue = EventQueue(max_size=100)
    await queue.start()
    yield queue
    await queue.stop()

@pytest_asyncio.fixture
async def event_monitor(event_queue):
    """Create a new event monitor for each test."""
    monitor = EventMonitor(event_queue)
    await monitor.start_monitoring()
    yield monitor
    await monitor.stop_monitoring()

# Test classes
class TestEvent:
    """Tests for the Event class."""
    
    def test_event_creation(self):
        """Test that events can be created with the expected attributes."""
        event_type = "test_event"
        data = {"key": "value"}
        event = Event(event_type=event_type, data=data)
        
        assert event.event_type == event_type
        assert event.data == data
        assert isinstance(event.timestamp, datetime)
        assert event.resource_type is None
        assert event.correlation_id is None
        assert "event_id" in event.metadata
        assert len(event.metadata) == 1
    
    def test_event_with_all_attributes(self):
        """Test that events can be created with all attributes."""
        event_type = "test_event"
        data = {"key": "value"}
        resource_type = ResourceType.AGENT
        correlation_id = "correlation-123"
        metadata = {"source": "test"}
        
        event = Event(
            event_type=event_type,
            data=data,
            resource_type=resource_type,
            correlation_id=correlation_id,
            metadata=metadata
        )
        
        assert event.event_type == event_type
        assert event.data == data
        assert isinstance(event.timestamp, datetime)
        assert event.resource_type == resource_type
        assert event.correlation_id == correlation_id
        assert event.metadata == metadata

class TestEventQueue:
    """Tests for the EventQueue class."""
    
    @pytest.mark.asyncio
    async def test_queue_initialization(self):
        """Test that the queue initializes properly."""
        queue = EventQueue(max_size=100)
        assert queue._max_size == 100
        assert queue._subscribers == {}
        assert queue._event_history == []
        assert queue._running is False
        assert queue._processor_thread is None
    
    @pytest.mark.asyncio
    async def test_queue_property_lazy_initialization(self):
        """Test that the priority queues initialize lazily."""
        queue = EventQueue()
        # Priority queues should be None initially
        assert queue._high_priority_queue is None
        assert queue._normal_priority_queue is None
        assert queue._low_priority_queue is None
        
        # Accessing the queue properties should initialize them
        high_queue = queue.high_priority_queue
        normal_queue = queue.normal_priority_queue
        low_queue = queue.low_priority_queue
        assert high_queue is not None
        assert normal_queue is not None
        assert low_queue is not None
    
    @pytest.mark.asyncio
    async def test_emit_and_basic_subscription(self, event_queue):
        """Test emitting an event and basic subscription."""
        # Create a list to store received events
        received_events = []
        
        # Define a subscriber
        async def subscriber(event_type, data):
            received_events.append((event_type, data))
        
        # Subscribe to test event
        await event_queue.subscribe(TestEventTypes.TEST_EVENT.value, subscriber)
        
        # Emit a test event
        test_data = {"message": "Hello, World!"}
        await event_queue.emit(TestEventTypes.TEST_EVENT.value, test_data)
        
        # Wait for event processing (processor thread startup time)
        await asyncio.sleep(1.0)
        
        # Verify the event was received
        assert len(received_events) == 1
        assert received_events[0][0] == TestEventTypes.TEST_EVENT.value
        assert received_events[0][1] == test_data
    
    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, event_queue):
        """Test that multiple subscribers receive the same event."""
        # Create lists to store received events for each subscriber
        received_events_1 = []
        received_events_2 = []
        
        # Define subscribers
        async def subscriber_1(event_type, data):
            received_events_1.append((event_type, data))
        
        async def subscriber_2(event_type, data):
            received_events_2.append((event_type, data))
        
        # Subscribe both to test event
        await event_queue.subscribe(TestEventTypes.TEST_EVENT.value, subscriber_1)
        await event_queue.subscribe(TestEventTypes.TEST_EVENT.value, subscriber_2)
        
        # Emit a test event
        test_data = {"message": "Hello, Subscribers!"}
        await event_queue.emit(TestEventTypes.TEST_EVENT.value, test_data)
        
        # Wait for event processing (processor thread startup time)
        await asyncio.sleep(1.0)
        
        # Verify both subscribers received the event
        assert len(received_events_1) == 1
        assert len(received_events_2) == 1
        assert received_events_1[0][1] == test_data
        assert received_events_2[0][1] == test_data
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, event_queue):
        """Test that unsubscribing removes a subscriber."""
        # Create a list to store received events
        received_events = []
        
        # Define a subscriber
        async def subscriber(event_type, data):
            received_events.append((event_type, data))
        
        # Subscribe to test event
        await event_queue.subscribe(TestEventTypes.TEST_EVENT.value, subscriber)
        
        # Emit a test event
        await event_queue.emit(TestEventTypes.TEST_EVENT.value, {"message": "First"})
        
        # Wait for event processing (processor thread startup time)
        await asyncio.sleep(1.0)
        
        # Verify the event was received
        assert len(received_events) == 1
        
        # Unsubscribe
        await event_queue.unsubscribe(TestEventTypes.TEST_EVENT.value, subscriber)
        
        # Emit another test event
        await event_queue.emit(TestEventTypes.TEST_EVENT.value, {"message": "Second"})
        
        # Wait for event processing
        await asyncio.sleep(1.0)
        
        # Verify no new events were received
        assert len(received_events) == 1
    
    @pytest.mark.asyncio
    async def test_event_delivery_retries(self, event_queue):
        """Test that event delivery is retried when it fails."""
        # Success tracking
        retry_count = 0
        success = False
        
        # Define a subscriber that fails initially but succeeds after retries
        async def failing_subscriber(event_type, data):
            nonlocal retry_count, success
            retry_count += 1
            
            if retry_count < 2:
                # Fail the first attempt
                raise ResourceError(
                    message="Test failure",
                    resource_id="test",
                    severity=ErrorSeverity.TRANSIENT
                )
            else:
                # Succeed on second attempt
                success = True
        
        # Subscribe to test event
        await event_queue.subscribe(TestEventTypes.ERROR_EVENT.value, failing_subscriber)
        
        # Lower retry delay for testing
        event_queue._retry_delay = 0.1
        
        # Emit a test event
        await event_queue.emit(TestEventTypes.ERROR_EVENT.value, {"message": "Should retry"})
        
        # Wait for event processing and retries (need more time for multiple retry attempts)
        await asyncio.sleep(2.0)
        
        # Verify retries occurred and eventually succeeded
        assert retry_count >= 2
        assert success is True
    
    @pytest.mark.asyncio
    async def test_emit_error(self, event_queue):
        """Test emitting a resource error event."""
        # Create a list to store received errors
        received_errors = []
        
        # Define an error subscriber
        async def error_subscriber(event_type, data):
            received_errors.append((event_type, data))
        
        # Subscribe to error event
        await event_queue.subscribe(ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value, error_subscriber)
        
        # Create a resource error
        error_context = OperationContext(
            resource_id="test-resource", 
            operation="test-operation"
        )
        
        error = ResourceOperationError(
            message="Test error",
            resource_id="test-resource",
            severity=ErrorSeverity.TRANSIENT,
            operation="test-operation",
            recovery_strategy="retry",
            details={"source": "test"}
        )
        error.context = error_context
        
        # Emit the error
        await event_queue.emit_error(
            error=error,
            additional_context={"test_key": "test_value"}
        )
        
        # Wait for event processing (processor thread startup time)
        await asyncio.sleep(1.0)
        
        # Verify error was received
        assert len(received_errors) == 1
        assert received_errors[0][0] == ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value
        assert received_errors[0][1]["severity"] == "TRANSIENT"
        assert received_errors[0][1]["resource_id"] == "test-resource"
        assert received_errors[0][1]["operation"] == "test-operation"
        assert received_errors[0][1]["context"]["test_key"] == "test_value"
    
    @pytest.mark.asyncio
    async def test_get_recent_events(self, event_queue):
        """Test retrieving recent events."""
        # Emit multiple events
        for i in range(5):
            await event_queue.emit(
                TestEventTypes.TEST_EVENT.value,
                {"index": i}
            )
            await event_queue.emit(
                TestEventTypes.SYSTEM_EVENT.value,
                {"index": i}
            )
        
        # Wait for event processing (processor thread startup time)
        await asyncio.sleep(1.0)
        
        # Get all recent events
        all_events = await event_queue.get_recent_events()
        assert len(all_events) >= 10
        
        # Get filtered events
        test_events = await event_queue.get_recent_events(TestEventTypes.TEST_EVENT.value)
        assert len(test_events) >= 5
        for event in test_events:
            assert event.event_type == TestEventTypes.TEST_EVENT.value
    
    @pytest.mark.asyncio
    async def test_queue_metrics(self, event_queue):
        """Test retrieving queue metrics."""
        # Subscribe to events
        async def dummy_subscriber(event_type, data):
            pass
        
        await event_queue.subscribe(TestEventTypes.TEST_EVENT.value, dummy_subscriber)
        await event_queue.subscribe(TestEventTypes.SYSTEM_EVENT.value, dummy_subscriber)
        
        # Get metrics
        queue_sizes = event_queue.get_queue_size()
        assert isinstance(queue_sizes, dict)
        assert queue_sizes["total"] >= 0
        assert queue_sizes["high"] >= 0
        assert queue_sizes["normal"] >= 0
        assert queue_sizes["low"] >= 0
        
        subscriber_count = event_queue.get_subscriber_count(TestEventTypes.TEST_EVENT.value)
        assert subscriber_count == 1
        
        subscriber_count = event_queue.get_subscriber_count(TestEventTypes.SYSTEM_EVENT.value)
        assert subscriber_count == 1
        
        subscriber_count = event_queue.get_subscriber_count("non_existent_event")
        assert subscriber_count == 0

class TestEventMonitor:
    """Tests for the EventMonitor class."""
    
    @pytest.mark.asyncio
    async def test_monitor_health_check(self, event_queue, event_monitor):
        """Test that the monitor performs health checks."""
        # Create a list to store health events
        health_events = []
        
        # Define a health subscriber
        async def health_subscriber(event_type, data):
            health_events.append((event_type, data))

        try:
            # Subscribe to health event
            await event_queue.subscribe(ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value, health_subscriber)
            
            event_monitor._health_check_interval = 0.1
            
            # Wait for at least one health check
            await asyncio.sleep(1.0)
            
            # Verify at least one health event was emitted
            assert len(health_events) >= 1
            
            # Verify health event structure
            health_event = health_events[0]
            assert health_event[0] == ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value
            assert "component" in health_event[1]
            assert "status" in health_event[1]
            assert "description" in health_event[1]
            assert "metadata" in health_event[1]
            
            # Verify health status
            status_data = health_event[1]
            assert status_data["component"] == "event_system"
            assert status_data["status"] in ["HEALTHY", "DEGRADED", "UNHEALTHY"]
            assert isinstance(status_data["metadata"], dict)
            
            # Verify metadata contains expected metrics
            metadata = status_data["metadata"]
            assert "queue_size" in metadata
            assert "total_subscribers" in metadata
            assert "retry_count" in metadata

        finally:
            # Ensure proper cleanup
            await event_queue.unsubscribe(ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value, health_subscriber)
            
            # Stop the monitor if it has a stop method
            if hasattr(event_monitor, 'stop'):
                await event_monitor.stop()
                
            # Ensure all tasks are completed
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            for task in tasks:
                task.cancel()

class TestCrossLoopBehavior:
    """Tests for cross-event-loop behavior."""
    
    @pytest.mark.asyncio
    async def test_create_queue_in_different_loop(self, event_queue):
        """Test creating a queue in a different event loop."""
        # Create a future to communicate between threads
        result_future = asyncio.Future()
        
        # Function to run in a separate thread
        def run_in_thread():
            async def async_task():
                # Create a new event loop for this thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                
                try:
                    # Create a new queue in this loop
                    thread_queue = EventQueue(max_size=50)
                    
                    # Start the queue
                    await thread_queue.start()
                    
                    # Create a list to store received events
                    received_events = []
                    
                    # Define a subscriber
                    async def thread_subscriber(event_type, data):
                        received_events.append((event_type, data))
                    
                    # Subscribe to test event
                    await thread_queue.subscribe(TestEventTypes.TEST_EVENT.value, thread_subscriber)
                    
                    # Emit a test event
                    test_data = {"thread": "secondary"}
                    await thread_queue.emit(TestEventTypes.TEST_EVENT.value, test_data)
                    
                    # Wait for event processing (processor thread startup time)
                    await asyncio.sleep(1.0)
                    
                    # Stop the queue
                    await thread_queue.stop()
                    
                    # Return results
                    return {
                        "queue_created": hasattr(thread_queue, '_id') and thread_queue._id is not None,
                        "events_received": len(received_events),
                        "event_data": received_events[0][1] if received_events else None
                    }
                except Exception as e:
                    logger.error(f"Error in thread: {e}")
                    return {"error": str(e)}
                finally:
                    new_loop.close()
            
            # Run the async task and set the result
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(async_task())
            result_future.set_result(result)
        
        # Create and start the thread
        thread = threading.Thread(target=run_in_thread)
        thread.start()
        thread.join()
        
        # Get the result
        result = await result_future
        
        # Verify queue was created and worked in the other thread
        assert result["queue_created"] is True
        assert result["events_received"] == 1
        assert result["event_data"] == {"thread": "secondary"}

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])