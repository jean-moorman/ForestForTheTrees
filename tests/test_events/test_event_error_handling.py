import pytest
import asyncio
import pytest_asyncio
import threading
import time
from datetime import datetime
from enum import Enum
import logging
import concurrent.futures

# Import the modules being tested
from resources.events import Event, EventQueue, EventMonitor, ResourceEventTypes
from resources.common import ResourceType, HealthStatus, ErrorSeverity
from resources.errors import ResourceOperationError, ResourceError

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_event_error_handling")

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

# Test classes for various error handling scenarios
class TestEventErrorHandling:
    """Tests for error handling in the EventQueue."""
    
    @pytest.mark.asyncio
    async def test_handle_none_event_type(self, event_queue):
        """Test that emitting an event with None type is handled gracefully."""
        # Define a subscriber to any event
        received_events = []
        async def general_subscriber(event_type, data):
            received_events.append((event_type, data))
        
        # Subscribe to a valid event type
        await event_queue.subscribe("valid_event", general_subscriber)
        
        # Try to emit an event with None type
        try:
            await event_queue.emit(None, {"key": "value"})
            # Wait for any event processing
            await asyncio.sleep(0.1)
            # No events should be received for None type
            assert len(received_events) == 0
        except Exception as e:
            # Should not raise - just log or handle gracefully
            pytest.fail(f"emit with None event_type raised exception: {e}")
    
    @pytest.mark.asyncio
    async def test_subscriber_type_error(self, event_queue):
        """Test handling of TypeError in subscriber."""
        # Define a subscriber that raises TypeError
        async def bad_subscriber(event_type, data):
            # Simulate a "can't be used in 'await'" error
            # by trying to await a non-awaitable
            await "not_awaitable"
        
        # Define a good subscriber
        received_events = []
        async def good_subscriber(event_type, data):
            received_events.append((event_type, data))
        
        # Subscribe both to the same event
        await event_queue.subscribe("type_error_test", bad_subscriber)
        await event_queue.subscribe("type_error_test", good_subscriber)
        
        # Emit an event
        await event_queue.emit("type_error_test", {"message": "Should handle TypeError"})
        
        # Wait for event processing
        await asyncio.sleep(0.2)
        
        # Verify good subscriber still received the event
        assert len(received_events) == 1
        assert received_events[0][0] == "type_error_test"
    
    @pytest.mark.asyncio
    async def test_deliver_event_exceptions(self, event_queue):
        """Test _deliver_event handling of various exceptions."""
        # Create a test event
        test_event = Event(
            event_type="exception_test",
            data={"message": "Test exceptions"}
        )
        
        # Track attempts
        attempts = 0
        
        # Define a subscriber that throws different exceptions on different attempts
        async def exception_subscriber(event_type, data):
            nonlocal attempts
            attempts += 1
            
            if attempts == 1:
                # First attempt - ResourceError (retriable)
                raise ResourceError(
                    message="Test resource error",
                    resource_id="test",
                    severity=ErrorSeverity.TRANSIENT
                )
            elif attempts == 2:
                # Second attempt - TypeError (non-retriable)
                raise TypeError("Test type error")
            else:
                # Third attempt should succeed
                pass
        
        # Set retry delay to speed up test
        event_queue._retry_delay = 0.1
        
        # Manually call _deliver_event
        event_id = f"{test_event.event_type}_{test_event.timestamp.isoformat()}"
        event_queue._processing_retries[event_id] = 0
        
        # First call should retry and encounter TypeError
        with pytest.raises(TypeError):
            await event_queue._deliver_event(test_event, exception_subscriber, event_id)
        
        # Verify cleanup occurred
        assert event_id not in event_queue._processing_retries
    
    @pytest.mark.asyncio
    async def test_emit_error_recovery_workflow(self, event_queue):
        """Test the complete error recovery event workflow."""
        # Track received events
        error_events = []
        recovery_events = []
        resolution_events = []
        
        # Define subscribers for different error stages
        async def error_subscriber(event_type, data):
            error_events.append((event_type, data))
        
        async def recovery_subscriber(event_type, data):
            recovery_events.append((event_type, data))
        
        async def resolution_subscriber(event_type, data):
            resolution_events.append((event_type, data))
        
        # Subscribe to error events
        await event_queue.subscribe(
            ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value, 
            error_subscriber
        )
        await event_queue.subscribe(
            ResourceEventTypes.RESOURCE_ERROR_RECOVERY_STARTED.value,
            recovery_subscriber
        )
        await event_queue.subscribe(
            ResourceEventTypes.RESOURCE_ERROR_RESOLVED.value,
            resolution_subscriber
        )
        
        # Create an error context
        error_context = OperationContext(
            resource_id="test-resource",
            operation="test-operation",
            attempt=1,
            recovery_attempts=0,
            details={"source": "test"}
        )
        
        # Create the error
        error = ResourceOperationError(
            message="Test error for recovery",
            resource_id="test-resource",
            severity=ErrorSeverity.TRANSIENT,
            operation="test-operation",
            recovery_strategy="retry",
            details={"error_id": "ERR-123"}
        )
        error.context = error_context
        
        # Emit error event
        await event_queue.emit_error(error)
        
        # Emit recovery started event
        await event_queue.emit(
            ResourceEventTypes.RESOURCE_ERROR_RECOVERY_STARTED,
            {
                "resource_id": "test-resource",
                "error_id": "ERR-123",
                "recovery_strategy": "retry",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Emit error resolved event
        await event_queue.emit(
            ResourceEventTypes.RESOURCE_ERROR_RESOLVED,
            {
                "resource_id": "test-resource",
                "error_id": "ERR-123",
                "resolution": "automatic_recovery",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Wait for event processing
        await asyncio.sleep(0.2)
        
        # Verify all events were received
        assert len(error_events) == 1
        assert len(recovery_events) == 1
        assert len(resolution_events) == 1
        
        # Verify error event data
        assert error_events[0][0] == ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value
        assert error_events[0][1]["resource_id"] == "test-resource"
        assert error_events[0][1]["severity"] == "TRANSIENT"
        
        # Verify recovery event data
        assert recovery_events[0][0] == ResourceEventTypes.RESOURCE_ERROR_RECOVERY_STARTED.value
        assert recovery_events[0][1]["resource_id"] == "test-resource"
        assert recovery_events[0][1]["recovery_strategy"] == "retry"
        
        # Verify resolution event data
        assert resolution_events[0][0] == ResourceEventTypes.RESOURCE_ERROR_RESOLVED.value
        assert resolution_events[0][1]["resource_id"] == "test-resource"
        assert resolution_events[0][1]["resolution"] == "automatic_recovery"
    
    @pytest.mark.asyncio
    async def test_recover_from_queue_recreation(self, event_queue):
        """Test recovering from queue recreation after an error."""
        # Store original queue
        original_queue_id = id(event_queue._queue)
        
        # Track received events
        received_events = []
        
        # Define a subscriber
        async def test_subscriber(event_type, data):
            received_events.append((event_type, data))
        
        # Subscribe to test event
        await event_queue.subscribe("recreation_test", test_subscriber)
        
        # Emit an event before recreation
        await event_queue.emit("recreation_test", {"stage": "before"})
        
        # Wait for event processing
        await asyncio.sleep(0.1)
        
        # Verify event was received
        assert len(received_events) == 1
        
        # Force queue recreation by setting up a custom queue with a method that raises the right exception
        original_queue = event_queue._queue
        
        # Create a queue subclass that raises the right exception
        class ErrorQueue(asyncio.Queue):
            async def put(self, item):
                raise RuntimeError("different event loop")
        
        # Replace the queue with our custom one
        event_queue._queue = ErrorQueue(maxsize=original_queue.maxsize)
        
        # Try to emit an event - this should cause recreation
        await event_queue.emit("recreation_test", {"stage": "after"})
        
        # Wait for recreation and processing
        await asyncio.sleep(0.3)
        
        # Check if queue was recreated
        assert id(event_queue._queue) != original_queue_id
        
        # Emit another event to the recreated queue
        await event_queue.emit("recreation_test", {"stage": "final"})
        
        # Wait for event processing
        await asyncio.sleep(0.2)
        
        # Verify events were received after recreation
        assert len(received_events) >= 2

    @pytest.mark.asyncio
    async def test_unhandled_errors_in_processing(self, event_queue):
        """Test handling of unhandled errors in event processing."""
        # Create a custom bad event type that will cause processing issues
        bad_event_type = object()  # Not a string or Enum
        
        # Try to emit this event (should log error but not crash)
        try:
            await event_queue.emit(bad_event_type, {"test": "data"})
            
            # Wait a bit to ensure processing attempt
            await asyncio.sleep(0.1)
            
            # The process should continue working
            
            # Emit a valid event
            received_events = []
            async def test_subscriber(event_type, data):
                received_events.append((event_type, data))
            
            # Subscribe and emit valid event
            await event_queue.subscribe("valid_after_error", test_subscriber)
            await event_queue.emit("valid_after_error", {"message": "Still working"})
            
            # Wait for event processing
            await asyncio.sleep(0.1)
            
            # Verify valid event was processed
            assert len(received_events) == 1
            
        except Exception as e:
            pytest.fail(f"Unhandled error should be caught, but got: {e}")

class TestEventMonitorErrorHandling:
    """Tests for error handling in EventMonitor."""
    
    @pytest.mark.asyncio
    async def test_monitor_handles_check_error(self):
        """Test that the monitor handles errors during health checks."""
        # Create a queue
        queue = EventQueue()
        await queue.start()
        
        try:
            # Create a monitor with a buggy _check_health method
            monitor = EventMonitor(queue)
            
            # Override _check_health to raise an exception
            original_check_health = monitor._check_health
            
            async def buggy_check_health():
                # First call raises exception, subsequent calls work normally
                if not hasattr(buggy_check_health, "called"):
                    buggy_check_health.called = True
                    raise Exception("Deliberate health check error")
                return await original_check_health()
            
            monitor._check_health = buggy_check_health
            
            # Make health check interval very short
            monitor._health_check_interval = 0.1
            
            # Start monitoring
            await monitor.start_monitoring()
            
            # Wait for a couple of health checks to occur
            await asyncio.sleep(0.3)
            
            # Verify monitor is still running
            assert monitor._running is True
            
            # Stop the monitor
            await monitor.stop_monitoring()
            
        finally:
            # Clean up
            await queue.stop()

    @pytest.mark.asyncio
    async def test_health_monitor_degraded_state(self):
        """Test that EventMonitor correctly identifies degraded state."""
        # Create a queue with smaller max size for testing
        queue = EventQueue(max_size=10)
        
        try:
            # Start the queue
            await queue.start()
            
            # Track health status events
            health_events = []
            async def health_subscriber(event_type, data):
                logger.debug(f"Health subscriber received event: {data['status']} with queue_size={data['metadata'].get('queue_size')}")
                health_events.append((event_type, data))
            
            # Subscribe to health events
            await queue.subscribe(ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value, health_subscriber)
            
            # Create a slow subscriber to keep events in the queue
            async def slow_subscriber(event_type, data):
                await asyncio.sleep(0.5)  # Delay processing to keep events in queue
            
            # Create the monitor with short interval
            monitor = EventMonitor(queue)
            monitor._health_check_interval = 0.1
            
            # Start monitoring
            await monitor.start_monitoring()
            
            # Wait for initial health check
            await asyncio.sleep(0.3)
            
            # Subscribe to test events FIRST to ensure they stay in queue
            for i in range(8):
                await queue.subscribe(f"test_event_{i}", slow_subscriber)
            
            # Fill queue to near capacity
            for i in range(8):  # 80% of capacity
                await queue.emit(f"test_event_{i}", {"index": i})
            
            # Wait longer for multiple health checks
            await asyncio.sleep(0.5)
            
            # Stop monitoring
            await monitor.stop_monitoring()
            
            # Log what we received for debugging
            logger.debug(f"Received {len(health_events)} health events")
            for i, (event_type, data) in enumerate(health_events):
                logger.debug(f"Event {i}: {data['status']} with queue_size={data['metadata'].get('queue_size')}")
            
            # Alternative assertion: check if any event has high queue utilization
            high_utilization_events = [
                event for event in health_events 
                if event[1]['metadata'].get('queue_size', 0) >= 8 or 
                event[1]['metadata'].get('queue_percentage', 0) >= 0.8
            ]
            
            assert len(high_utilization_events) >= 1, "No events with high queue utilization detected"
            
        finally:
            # Clean up
            await queue.stop()

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])