"""Simple test for event queue functionality."""

import asyncio
import logging
import pytest
import pytest_asyncio
from typing import Dict, Any

from resources.events import EventQueue, ResourceEventTypes

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Mark all tests as asyncio
pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def event_queue():
    """Create a test event queue."""
    queue = EventQueue()
    await queue.start()
    yield queue
    await queue.stop()

async def test_simple_subscription(event_queue):
    """Test a simple subscription with direct event tracking."""
    # Set up received events
    received_events = []
    
    # Define a callback that logs events
    async def capture_event(event_type, data):
        logger.info(f"Capture callback received: {event_type}, {data}")
        received_events.append((event_type, data))
    
    # Subscribe to the event
    test_event_type = "test_event"
    await event_queue.subscribe(test_event_type, capture_event)
    
    # Emit an event
    test_data = {"test": "data", "value": 123}
    await event_queue.emit(test_event_type, test_data)
    
    # Give some time for events to be processed
    for _ in range(5):  # Try up to 5 times with increasing delays
        if received_events:
            break
        await asyncio.sleep(0.2)  # Start with 0.2s, increasing each time
    
    # Assert that we received the event
    assert len(received_events) > 0, "No events received"
    assert received_events[0][0] == test_event_type
    assert received_events[0][1]["test"] == "data"
    assert received_events[0][1]["value"] == 123

async def test_resource_alert_subscription(event_queue):
    """Test subscription to resource alert events."""
    # Set up received events
    received_alerts = []
    
    # Define a callback
    async def capture_alert(event_type, data):
        logger.info(f"Alert callback received: {event_type}, {data}")
        received_alerts.append((event_type, data))
    
    # Subscribe to resource alerts
    alert_event_type = ResourceEventTypes.RESOURCE_ALERT_CREATED.value
    logger.info(f"Subscribing to event type: {alert_event_type}")
    await event_queue.subscribe(alert_event_type, capture_alert)
    
    # Emit a resource alert
    alert_data = {
        "alert_type": "test_alert",
        "level": "WARNING",
        "resource_id": "test_resource",
        "timestamp": "2023-01-01T00:00:00Z"
    }
    logger.info(f"Emitting alert event: {alert_event_type}, {alert_data}")
    await event_queue.emit(alert_event_type, alert_data)
    
    # Give some time for events to be processed
    for attempt in range(1, 6):  # Try up to 5 times with increasing delays
        logger.info(f"Waiting for alerts (attempt {attempt}/5)...")
        if received_alerts:
            break
        await asyncio.sleep(0.2 * attempt)  # Gradually increase wait time
    
    logger.info(f"Received alerts: {received_alerts}")
    
    # Assert that we received the alert
    assert len(received_alerts) > 0, "No alerts received"
    assert received_alerts[0][0] == alert_event_type
    assert received_alerts[0][1]["alert_type"] == "test_alert"

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])