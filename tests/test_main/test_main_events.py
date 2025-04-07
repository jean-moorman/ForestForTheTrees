import pytest
import asyncio
import sys
import time
from datetime import datetime
from collections import defaultdict

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

import qasync

# Import the modules we want to test
from resources import EventQueue, ResourceEventTypes

# Test timeout constants
SHORT_TIMEOUT = 0.5
NORMAL_TIMEOUT = 2.0

class TestSignals(QObject):
    """Test signals for async operations"""
    event_received = pyqtSignal(str, object)

@pytest.fixture
def qapp():
    """Fixture to create a Qt application instance"""
    app = QApplication.instance() or QApplication(sys.argv)
    yield app
    app.processEvents()

@pytest.fixture
def event_loop(qapp):
    """Fixture to create an event loop that works with Qt"""
    loop = qasync.QEventLoop(qapp)
    asyncio.set_event_loop(loop)
    yield loop
    
    # Clean up pending tasks
    pending_tasks = asyncio.all_tasks(loop)
    for task in pending_tasks:
        if not task.done():
            task.cancel()
    
    # Run loop until tasks are cancelled
    loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
    loop.close()

@pytest.fixture
async def event_queue(event_loop):
    """Create and initialize an event queue"""
    queue = EventQueue()
    await queue.start()
    yield queue
    # Stop queue after test
    await queue.stop()

@pytest.fixture
def signals():
    """Create test signals for tracking events"""
    return TestSignals()

@pytest.mark.asyncio
class TestEventQueue:
    """Tests for the EventQueue class"""
    
    async def test_emit_event(self, event_queue, signals):
        """Test that events can be emitted and received"""
        # Set up receiving data
        received_events = []
        
        # Set up event handler
        async def handle_event(event_type, data):
            received_events.append((event_type, data))
        
        # Subscribe to test event
        test_event_type = ResourceEventTypes.METRIC_RECORDED
        await event_queue.subscribe(test_event_type, handle_event)
        
        # Emit event
        test_data = {"metric": "memory", "value": 50, "timestamp": datetime.now().isoformat()}
        await event_queue.emit(test_event_type, test_data)
        
        # Wait for event processing
        await asyncio.sleep(SHORT_TIMEOUT)
        
        # Check received event
        assert len(received_events) == 1
        assert received_events[0][0] == test_event_type
        assert received_events[0][1]["metric"] == "memory"
        assert received_events[0][1]["value"] == 50
    
    async def test_multiple_subscribers(self, event_queue):
        """Test that multiple subscribers receive the same event"""
        # Set up receiving data
        subscriber1_received = []
        subscriber2_received = []
        
        # Set up event handlers
        async def handle_event1(event_type, data):
            subscriber1_received.append((event_type, data))
        
        async def handle_event2(event_type, data):
            subscriber2_received.append((event_type, data))
        
        # Subscribe to test event
        test_event_type = ResourceEventTypes.SYSTEM_HEALTH_CHANGED
        await event_queue.subscribe(test_event_type, handle_event1)
        await event_queue.subscribe(test_event_type, handle_event2)
        
        # Emit event
        test_data = {"component": "system", "status": "DEGRADED", "timestamp": datetime.now().isoformat()}
        await event_queue.emit(test_event_type, test_data)
        
        # Wait for event processing
        await asyncio.sleep(SHORT_TIMEOUT)
        
        # Check both subscribers received the event
        assert len(subscriber1_received) == 1
        assert len(subscriber2_received) == 1
        assert subscriber1_received[0][1]["status"] == "DEGRADED"
        assert subscriber2_received[0][1]["status"] == "DEGRADED"
    
    async def test_unsubscribe(self, event_queue):
        """Test that unsubscribing stops events from being received"""
        # Set up receiving data
        received_events = []
        
        # Set up event handler
        async def handle_event(event_type, data):
            received_events.append((event_type, data))
        
        # Subscribe to test event
        test_event_type = ResourceEventTypes.ERROR_OCCURRED
        await event_queue.subscribe(test_event_type, handle_event)
        
        # Emit first event
        test_data1 = {"error": "Test error 1", "source": "test", "timestamp": datetime.now().isoformat()}
        await event_queue.emit(test_event_type, test_data1)
        
        # Wait for event processing
        await asyncio.sleep(SHORT_TIMEOUT)
        
        # Unsubscribe
        await event_queue.unsubscribe(test_event_type, handle_event)
        
        # Emit second event
        test_data2 = {"error": "Test error 2", "source": "test", "timestamp": datetime.now().isoformat()}
        await event_queue.emit(test_event_type, test_data2)
        
        # Wait for event processing
        await asyncio.sleep(SHORT_TIMEOUT)
        
        # Check only first event was received
        assert len(received_events) == 1
        assert received_events[0][1]["error"] == "Test error 1"
    
    async def test_multiple_event_types(self, event_queue):
        """Test handling multiple event types with different handlers"""
        # Track events by type
        received_events = defaultdict(list)
        
        # Set up event handlers for different types
        async def handle_metrics(event_type, data):
            received_events["metrics"].append(data)
        
        async def handle_errors(event_type, data):
            received_events["errors"].append(data)
        
        async def handle_health(event_type, data):
            received_events["health"].append(data)
        
        # Subscribe to different event types
        await event_queue.subscribe(ResourceEventTypes.METRIC_RECORDED, handle_metrics)
        await event_queue.subscribe(ResourceEventTypes.ERROR_OCCURRED, handle_errors)
        await event_queue.subscribe(ResourceEventTypes.SYSTEM_HEALTH_CHANGED, handle_health)
        
        # Emit various events
        await event_queue.emit(ResourceEventTypes.METRIC_RECORDED, {"metric": "cpu", "value": 30})
        await event_queue.emit(ResourceEventTypes.ERROR_OCCURRED, {"error": "Test error"})
        await event_queue.emit(ResourceEventTypes.SYSTEM_HEALTH_CHANGED, {"status": "HEALTHY"})
        await event_queue.emit(ResourceEventTypes.METRIC_RECORDED, {"metric": "memory", "value": 45})
        
        # Wait for event processing
        await asyncio.sleep(SHORT_TIMEOUT)
        
        # Check event distribution
        assert len(received_events["metrics"]) == 2
        assert len(received_events["errors"]) == 1
        assert len(received_events["health"]) == 1
        
        # Check specific events
        assert any(e["metric"] == "cpu" for e in received_events["metrics"])
        assert any(e["metric"] == "memory" for e in received_events["metrics"])
        assert received_events["errors"][0]["error"] == "Test error"
        assert received_events["health"][0]["status"] == "HEALTHY"
    
    async def test_emit_get_nowait(self, event_queue):
        """Test emitting events and retrieving them with get_nowait"""
        # Emit some events
        await event_queue.emit(ResourceEventTypes.METRIC_RECORDED, {"metric": "test1"})
        await event_queue.emit(ResourceEventTypes.METRIC_RECORDED, {"metric": "test2"})
        await event_queue.emit(ResourceEventTypes.METRIC_RECORDED, {"metric": "test3"})
        
        # Get events without waiting
        events = []
        try:
            while True:
                event = event_queue.get_nowait()
                if event:
                    events.append(event)
                else:
                    break
        except asyncio.QueueEmpty:
            pass  # Expected when queue is empty
        
        # Check retrieved events
        assert len(events) == 3
        assert [e.data["metric"] for e in events] == ["test1", "test2", "test3"]
    
    async def test_event_ordering(self, event_queue):
        """Test that events are processed in order"""
        # Set up receiving data with timestamps
        received_events = []
        
        # Set up event handler that tracks reception time
        async def handle_event(event_type, data):
            received_events.append((datetime.now(), data))
            # Add a small delay to test ordering
            await asyncio.sleep(0.05)
        
        # Subscribe to test event
        await event_queue.subscribe(ResourceEventTypes.METRIC_RECORDED, handle_event)
        
        # Emit events in rapid succession
        for i in range(5):
            await event_queue.emit(ResourceEventTypes.METRIC_RECORDED, {"sequence": i})
            # No sleep here - we want to test the queue's ordering
        
        # Wait for all events to be processed
        await asyncio.sleep(NORMAL_TIMEOUT)  # Enough time for all events with their delays
        
        # Check events were received in order
        assert len(received_events) == 5
        sequences = [data[1]["sequence"] for data in received_events]
        assert sequences == [0, 1, 2, 3, 4]
    
    async def test_high_volume_events(self, event_queue):
        """Test handling a high volume of events"""
        # Number of events to test with
        NUM_EVENTS = 100
        
        # Set up receiving counter
        received_count = 0
        
        # Set up event handler
        async def handle_event(event_type, data):
            nonlocal received_count
            received_count += 1
        
        # Subscribe to test event
        await event_queue.subscribe(ResourceEventTypes.METRIC_RECORDED, handle_event)
        
        # Emit many events quickly
        for i in range(NUM_EVENTS):
            await event_queue.emit(ResourceEventTypes.METRIC_RECORDED, {"id": i})
        
        # Wait for event processing with a longer timeout
        # This might need adjustment based on system performance
        max_wait = NORMAL_TIMEOUT * 2
        start_time = time.time()
        while received_count < NUM_EVENTS and time.time() - start_time < max_wait:
            await asyncio.sleep(0.1)
        
        # Check all events were received
        assert received_count == NUM_EVENTS, f"Only received {received_count}/{NUM_EVENTS} events"

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])