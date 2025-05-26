"""
Tests for event queue robustness across different scenarios.

This test suite focuses on validating the event queue's ability to handle:
1. Cross-thread access to the queue
2. Batch event processing and potential unpacking issues
3. Circuit breaker dictionary modification during iteration
"""

import asyncio
import concurrent.futures
import logging
import pytest
import pytest_asyncio
import threading
import time
from typing import Dict, Any, List

from resources.events import EventQueue, ResourceEventTypes
from resources.monitoring.circuit_breakers import CircuitBreakerRegistry, CircuitBreaker, HealthStatus

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Mark all tests as asyncio
pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def event_queue():
    """Create a test event queue."""
    queue = EventQueue(max_size=100, queue_id="test_event_queue")
    await queue.start()
    yield queue
    await queue.stop()

@pytest_asyncio.fixture
async def circuit_registry(event_queue):
    """Create a test circuit breaker registry."""
    # Create mock health tracker
    class MockHealthTracker:
        async def update_health(self, resource_id, health_status):
            logger.debug(f"Mock health update for {resource_id}: {health_status.status}")
            return True
    
    registry = CircuitBreakerRegistry(event_queue, health_tracker=MockHealthTracker())
    await registry.start_monitoring()
    yield registry
    await registry.stop_monitoring()

async def test_cross_thread_queue_access(event_queue):
    """Test that the queue can be accessed from different threads safely."""
    # Track received events across threads
    received_events = []
    event_lock = threading.Lock()
    
    # Define a callback that will be called from the event processor thread
    async def event_callback(event_type, data):
        logger.debug(f"Received event in callback: {event_type}, {data}")
        with event_lock:
            received_events.append((event_type, data))
    
    # Subscribe to events
    await event_queue.subscribe("test_event", event_callback)
    
    # Function to emit events from another thread
    def emit_events_from_thread():
        asyncio.run(emit_events())
    
    async def emit_events():
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Emit some events
        for i in range(5):
            test_data = {"thread_test": i}
            await event_queue.emit("test_event", test_data)
            await asyncio.sleep(0.1)
    
    # Start a thread to emit events
    thread = threading.Thread(target=emit_events_from_thread)
    thread.start()
    
    # Wait for the thread to complete
    thread.join()
    
    # Wait for events to be processed (with timeout)
    for _ in range(10):
        with event_lock:
            if len(received_events) >= 5:
                break
        await asyncio.sleep(0.2)
    
    # Verify events were received
    with event_lock:
        assert len(received_events) == 5, f"Expected 5 events, got {len(received_events)}"
        
        # Check event contents
        for i, (event_type, data) in enumerate(sorted(received_events, key=lambda x: x[1].get("thread_test", 0))):
            assert event_type == "test_event"
            assert data["thread_test"] == i

async def test_batch_event_unpacking_robustness(event_queue):
    """Test handling of batch events that might cause unpacking errors."""
    # Record received events
    received_events = []
    
    # Define a callback that expects a specific unpacking pattern
    async def tuple_unpacker_callback(event_type, data):
        """This callback would normally try to unpack data as a tuple."""
        logger.debug(f"Received batch event in unpacker: {event_type}, {data}")
        received_events.append((event_type, data))
    
    # Subscribe to a batch event type
    batch_event_type = "system_health_changed_batch"
    await event_queue.subscribe(batch_event_type, tuple_unpacker_callback)
    
    # Create batch event data that might cause unpacking issues
    batch_data = {
        "batch": True,
        "count": 2,
        "items": [
            {"component": "test1", "status": "healthy"},
            {"component": "test2", "status": "degraded"}
        ]
    }
    
    # Emit the batch event
    await event_queue.emit(batch_event_type, batch_data)
    
    # Wait for processing
    for _ in range(5):
        if received_events:
            break
        await asyncio.sleep(0.2)
    
    # Verify the event was processed without errors
    assert len(received_events) == 1, "Batch event was not processed"
    assert received_events[0][0] == batch_event_type
    assert received_events[0][1]["batch"] == True
    assert len(received_events[0][1]["items"]) == 2

async def test_circuit_breaker_registry_iteration_safety(circuit_registry):
    """Test that the circuit breaker registry handles dictionary iteration safely."""
    # Create a large number of circuit breakers in parallel
    async def create_circuit_breakers():
        tasks = []
        for i in range(20):
            task = asyncio.create_task(
                circuit_registry.get_or_create_circuit_breaker(f"test_circuit_{i}")
            )
            tasks.append(task)
        
        # Wait for all circuit breakers to be created
        await asyncio.gather(*tasks)
    
    # Run the creation
    await create_circuit_breakers()
    
    # Let the circuit breaker registry run its monitoring cycle
    await asyncio.sleep(0.5)
    
    # Now trigger many state changes in parallel while monitoring is running
    async def trigger_state_changes():
        tasks = []
        # Get half of the circuit breakers to trip
        for i in range(10):
            circuit = await circuit_registry.get_circuit_breaker(f"test_circuit_{i}")
            if circuit:
                task = asyncio.create_task(
                    circuit.trip(f"Test trip {i}")
                )
                tasks.append(task)
        
        # Wait for all trips to complete
        await asyncio.gather(*tasks)
    
    # Run the state changes
    await trigger_state_changes()
    
    # Let the monitoring run again
    await asyncio.sleep(0.5)
    
    # Verify we have the expected number of circuit breakers
    assert len(circuit_registry.circuit_names) == 20, "Expected 20 circuit breakers"
    
    # Get status summary and verify no errors
    status = circuit_registry.get_circuit_status_summary()
    assert len(status) == 20, "Status summary should contain 20 entries"
    
    # Verify that the first 10 circuits are OPEN and the rest are CLOSED
    for i in range(20):
        circuit_name = f"test_circuit_{i}"
        assert circuit_name in status, f"Circuit {circuit_name} missing from status"
        
        if i < 10:
            assert status[circuit_name]["state"] == "OPEN", f"Circuit {circuit_name} should be OPEN"
        else:
            assert status[circuit_name]["state"] == "CLOSED", f"Circuit {circuit_name} should be CLOSED"

async def test_event_queue_get_nowait_cross_context(event_queue):
    """Test that get_nowait properly handles cross-context access."""
    # Function to run in a separate thread
    def thread_func():
        # Create an event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Try to call get_nowait from this thread
        try:
            # This should not raise an exception even though it's accessed from a different context
            event_queue.get_nowait()
            # We expect a QueueEmpty exception, not any other type
            assert False, "Expected QueueEmpty exception"
        except asyncio.QueueEmpty:
            # This is expected
            logger.debug("Got QueueEmpty as expected")
            pass
        except Exception as e:
            # Any other exception is a failure
            logger.error(f"Unexpected exception: {e}")
            assert False, f"Unexpected exception: {e}"
    
    # Create and start thread
    thread = threading.Thread(target=thread_func)
    thread.start()
    thread.join()
    
    # Now emit an event and verify it can be received
    test_data = {"cross_context_test": True}
    await event_queue.emit("test_event", test_data)
    
    # Define a collector to get events from the main context
    collector = []
    
    async def collect_events():
        try:
            while True:
                # This might access from a different context than the emitter
                # but should work with our robust implementation
                event = event_queue.get_nowait()
                collector.append(event)
                # Return after getting one event
                return
        except asyncio.QueueEmpty:
            # Wait and try again
            await asyncio.sleep(0.1)
    
    # Try to collect events with timeout
    for _ in range(10):
        await collect_events()
        if collector:
            break
        await asyncio.sleep(0.2)
    
    # Verify event was received
    assert len(collector) == 1, "Event was not received"
    assert collector[0].event_type == "test_event"
    assert collector[0].data["cross_context_test"] == True

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])