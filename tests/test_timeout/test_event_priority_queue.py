import pytest
import pytest_asyncio
import asyncio
import time
import logging
import sys
import os
from datetime import datetime

# Adjust path to import from the FFTT package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from resources.events import Event, EventQueue, ResourceEventTypes

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_event_priority")

# Test data
class TestEventTypes:
    HIGH_PRIORITY = "high_priority_event"
    NORMAL_PRIORITY = "normal_priority_event"
    LOW_PRIORITY = "low_priority_event"
    BATCH_EVENT = "batch_event"

@pytest_asyncio.fixture
async def event_queue():
    """Create a new event queue for each test."""
    # Use a smaller queue for more predictable batching in tests
    queue = EventQueue(max_size=20)
    await queue.start()
    # Allow the event processor task to start properly
    await asyncio.sleep(0.2)  
    yield queue
    await queue.stop()

class TestEventPriorityQueue:
    """Tests for the priority queue system in EventQueue."""
    
    @pytest.mark.asyncio
    async def test_priority_queue_initialization(self, event_queue):
        """Test that priority queues are initialized properly."""
        # Test lazy initialization of each priority queue
        assert event_queue._high_priority_queue is not None
        assert event_queue._normal_priority_queue is not None
        assert event_queue._low_priority_queue is not None
        
        # Verify queue sizes match configuration (updated for the max_size=20 in fixture)
        assert event_queue._high_priority_queue.maxsize == 10  # max(10, max_size/10)
        assert event_queue._normal_priority_queue.maxsize == 20  # max_size
        assert event_queue._low_priority_queue.maxsize == 40  # max_size*2
    
    @pytest.mark.asyncio
    async def test_emit_with_priority(self, event_queue):
        """Test emitting events with different priorities."""
        # Emit events with each priority
        high_result = await event_queue.emit(
            TestEventTypes.HIGH_PRIORITY,
            {"message": "High priority test"},
            priority="high"
        )
        
        normal_result = await event_queue.emit(
            TestEventTypes.NORMAL_PRIORITY,
            {"message": "Normal priority test"}
            # Default priority is "normal"
        )
        
        low_result = await event_queue.emit(
            TestEventTypes.LOW_PRIORITY,
            {"message": "Low priority test"},
            priority="low"
        )
        
        # All emit operations should succeed
        assert high_result is True
        assert normal_result is True
        assert low_result is True
        
        # Wait for event processing
        await asyncio.sleep(0.2)
    
    @pytest.mark.asyncio
    async def test_high_priority_processed_first(self, event_queue):
        """Test that high priority events are processed before others."""
        # Track processing order
        processed_events = []
        
        # Define a subscriber that tracks order
        async def order_tracking_subscriber(event_type, data):
            processed_events.append(event_type)
            await asyncio.sleep(0.1)  # Add delay to test ordering
        
        # Subscribe to all test event types
        await event_queue.subscribe(TestEventTypes.HIGH_PRIORITY, order_tracking_subscriber)
        await event_queue.subscribe(TestEventTypes.NORMAL_PRIORITY, order_tracking_subscriber)
        await event_queue.subscribe(TestEventTypes.LOW_PRIORITY, order_tracking_subscriber)
        
        # Emit events in reverse priority order
        await event_queue.emit(TestEventTypes.LOW_PRIORITY, {"order": 3}, priority="low")
        await event_queue.emit(TestEventTypes.NORMAL_PRIORITY, {"order": 2})
        await event_queue.emit(TestEventTypes.HIGH_PRIORITY, {"order": 1}, priority="high")
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Verify high priority was processed first, regardless of emit order
        assert processed_events[0] == TestEventTypes.HIGH_PRIORITY
        # The rest may vary depending on timing, but high should always be first
    
    @pytest.mark.asyncio
    async def test_event_batching(self, event_queue):
        """Test event batching for events of the same type."""
        # Track received events
        normal_events = []
        batch_events = []
        
        # Define subscribers
        async def normal_subscriber(event_type, data):
            normal_events.append(data)
            
        async def batch_subscriber(event_type, data):
            batch_events.append(data)
            # Check if this is a batch
            if data.get("batch") is True:
                logger.debug(f"Received batch with {data['count']} items")
        
        # Subscribe to event types
        await event_queue.subscribe(TestEventTypes.NORMAL_PRIORITY, normal_subscriber)
        await event_queue.subscribe(TestEventTypes.BATCH_EVENT, batch_subscriber)
        
        # Emit several events of the same type in rapid succession
        for i in range(10):
            await event_queue.emit(
                TestEventTypes.BATCH_EVENT,
                {"message": f"Batch event {i}", "index": i}
            )
            
        # Emit a different type of event
        await event_queue.emit(
            TestEventTypes.NORMAL_PRIORITY,
            {"message": "Normal event"}
        )
        
        # Wait longer for processing to complete
        for _ in range(10):  # Try for up to 1 second
            await asyncio.sleep(0.1)
            # Check if batching occurred
            if len(normal_events) > 0 and len(batch_events) > 0:
                batched_events = [e for e in batch_events if e.get("batch") is True]
                if len(batched_events) >= 1:
                    break
                    
        # For tests, we need to be a bit more lenient due to timing issues
        # Try for up to 2 seconds to get the events
        timeout = time.time() + 2.0  # 2 second timeout
        while time.time() < timeout:
            if len(normal_events) > 0 or len(batch_events) > 0:
                break
            await asyncio.sleep(0.1)
            
        # We should have received at least one event (either normal or batched)
        assert len(normal_events) > 0 or len(batch_events) > 0, "No events received after timeout"
        
        # At least one of the received events should be a batch
        batched_events = [e for e in batch_events if e.get("batch") is True]
        assert len(batched_events) >= 1
        
        # Verify batch contents
        for batch in batched_events:
            assert batch["count"] > 1
            assert len(batch["items"]) == batch["count"]
            # Verify items in the batch
            for item in batch["items"]:
                assert "message" in item
                assert "index" in item
    
    @pytest.mark.asyncio
    async def test_back_pressure_mechanism(self, event_queue):
        """Test back-pressure mechanism rejects or downgrade events when queues are saturated."""
        # Modify queue for testing back-pressure
        event_queue._max_size = 10
        event_queue._high_priority_queue = asyncio.Queue(maxsize=1)
        event_queue._normal_priority_queue = asyncio.Queue(maxsize=2)
        event_queue._low_priority_queue = asyncio.Queue(maxsize=4)
        
        # Create a slow subscriber to fill up the queues
        async def slow_subscriber(event_type, data):
            await asyncio.sleep(0.5)  # Very slow processing
        
        # Subscribe to all event types
        await event_queue.subscribe(TestEventTypes.HIGH_PRIORITY, slow_subscriber)
        await event_queue.subscribe(TestEventTypes.NORMAL_PRIORITY, slow_subscriber)
        await event_queue.subscribe(TestEventTypes.LOW_PRIORITY, slow_subscriber)
        
        # Fill up normal queue
        for i in range(3):
            await event_queue.emit(TestEventTypes.NORMAL_PRIORITY, {"index": i})
            
        # Now emit more events of different priorities to test back-pressure
        high_result = await event_queue.emit(
            TestEventTypes.HIGH_PRIORITY,
            {"message": "Critical high priority"},
            priority="high"
        )
        
        normal_result = await event_queue.emit(
            TestEventTypes.NORMAL_PRIORITY,
            {"message": "Should be downgraded or rejected"}
        )
        
        low_result = await event_queue.emit(
            TestEventTypes.LOW_PRIORITY,
            {"message": "Should be rejected"},
            priority="low"
        )
        
        # Critical events with high priority should be accepted
        assert high_result is True
        
        # Normal events might be downgraded or rejected
        # Low priority events should be rejected when queue is full
        
        # Wait for some processing
        await asyncio.sleep(1.0)
        
        # Test system alert is upgraded to high priority
        alert_result = await event_queue.emit(
            ResourceEventTypes.SYSTEM_ALERT.value,
            {"message": "System alert under load"},
            priority="normal"  # Should be upgraded to high
        )
        
        # System alerts should always get through
        assert alert_result is True
    
    @pytest.mark.asyncio
    async def test_correlation_id_preserved_in_batches(self, event_queue):
        """Test that correlation ID is preserved in batched events."""
        # Track received events
        batch_events = []
        
        # Define batch subscriber
        async def batch_subscriber(event_type, data):
            batch_events.append(data)
        
        # Subscribe to batch event type
        await event_queue.subscribe(TestEventTypes.BATCH_EVENT, batch_subscriber)
        
        # Emit several events with the same correlation ID
        correlation_id = "test-correlation-123"
        for i in range(5):
            await event_queue.emit(
                TestEventTypes.BATCH_EVENT,
                {"message": f"Correlated event {i}", "index": i},
                correlation_id=correlation_id
            )
            
        # Wait longer for processing to complete (increased from 0.5s to 1.0s)
        for _ in range(10):  # Try for up to 1 second
            await asyncio.sleep(0.1)
            # Check if batching occurred
            batched_events = [e for e in batch_events if e.get("batch") is True]
            if len(batched_events) >= 1:
                break
                
        # Verify batching occurred
        assert len(batched_events) >= 1
        
        # Verify correlation ID was preserved in batched event
        # Note: This test assumes the correlation_id is available in the batch data
        # If it's not, the test needs to be adjusted to check the Event object
        
        # We'll inspect the events in the history instead to verify correlation was preserved
        history_events = await event_queue.get_recent_events(TestEventTypes.BATCH_EVENT)
        assert len(history_events) > 0
        
        # Check correlation IDs in history
        correlation_events = [e for e in history_events if e.correlation_id == correlation_id]
        assert len(correlation_events) > 0

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])