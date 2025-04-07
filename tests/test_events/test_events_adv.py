import pytest
import asyncio
import pytest_asyncio
import threading
import time
from datetime import datetime
import random
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
logger = logging.getLogger("test_events_advanced")

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

# Advanced test scenarios
class TestAdvancedEventQueue:
    """Advanced tests for the EventQueue class."""
    
    @pytest.mark.asyncio
    async def test_non_coroutine_subscriber(self, event_queue):
        """Test subscribing a non-coroutine function."""
        # Create a list to store received events
        received_events = []
        
        # Define a non-async subscriber
        def sync_subscriber(event_type, data):
            received_events.append((event_type, data))
        
        # Subscribe the non-async function
        await event_queue.subscribe("sync_event", sync_subscriber)
        
        # Emit an event
        test_data = {"message": "Sync subscriber test"}
        await event_queue.emit("sync_event", test_data)
        
        # Wait for event processing
        await asyncio.sleep(0.2)
        
        # Verify the event was received
        assert len(received_events) == 1
        assert received_events[0][0] == "sync_event"
        assert received_events[0][1] == test_data
    
    @pytest.mark.asyncio
    async def test_max_retries_exhaustion(self, event_queue):
        """Test behavior when max retries are exhausted."""
        # Set retry parameters for testing
        event_queue._max_retries = 2
        event_queue._retry_delay = 0.1
        
        # Track retry attempts
        attempts = 0
        
        # Define a persistently failing subscriber
        async def failing_subscriber(event_type, data):
            nonlocal attempts
            attempts += 1
            # Always fail
            raise ResourceError(
                message="Persistent failure",
                resource_id="test-resource",
                severity=ErrorSeverity.TRANSIENT
            )
        
        # Create a success tracking subscriber
        success_events = []
        async def success_tracker(event_type, data):
            success_events.append((event_type, data))
        
        # Subscribe both handlers
        await event_queue.subscribe("retry_test", failing_subscriber)
        await event_queue.subscribe("retry_test", success_tracker)
        
        # Emit a test event
        await event_queue.emit("retry_test", {"message": "Should retry and fail"})
        
        # Wait for event processing and all retries
        await asyncio.sleep(1.0)
        
        # Verify retries occurred the expected number of times
        assert attempts == 3  # Initial attempt + 2 retries
        
        # Verify the successful subscriber still got the event
        assert len(success_events) == 1
    
    @pytest.mark.asyncio
    async def test_event_with_enum_type(self, event_queue):
        """Test emitting an event with an Enum as event type."""
        # Create a list to store received events
        received_events = []
        
        # Define a subscriber
        async def enum_subscriber(event_type, data):
            received_events.append((event_type, data))
        
        # Subscribe to the ResourceEventTypes Enum value
        await event_queue.subscribe(ResourceEventTypes.CACHE_UPDATED.value, enum_subscriber)
        
        # Emit an event using the Enum directly
        test_data = {"cache_key": "test_key"}
        await event_queue.emit(ResourceEventTypes.CACHE_UPDATED, test_data)
        
        # Wait for event processing
        await asyncio.sleep(0.2)
        
        # Verify the event was received
        assert len(received_events) == 1
        assert received_events[0][0] == ResourceEventTypes.CACHE_UPDATED.value
        assert received_events[0][1] == test_data
    
    @pytest.mark.asyncio
    async def test_invalid_subscription_inputs(self, event_queue):
        """Test handling of invalid subscription inputs."""
        # Try to subscribe with None event type
        await event_queue.subscribe(None, lambda e, d: None)
        
        # Try to subscribe with None callback
        await event_queue.subscribe("test_event", None)
        
        # Try to subscribe with non-callable
        await event_queue.subscribe("test_event", "not_a_function")
        
        # These shouldn't raise exceptions, but should log errors
        # Verify no subscribers were added
        assert event_queue.get_subscriber_count("test_event") == 0
    
    @pytest.mark.asyncio
    async def test_high_load_handling(self, event_queue):
        """Test handling a high load of events."""
        # Number of events to emit
        num_events = 100
        
        # Track received events
        received_events = 0
        
        # Define a subscriber that tracks received events
        async def counter_subscriber(event_type, data):
            nonlocal received_events
            received_events += 1
            # Add small delay to simulate processing
            await asyncio.sleep(0.001)
        
        # Subscribe to test event
        await event_queue.subscribe("high_load", counter_subscriber)
        
        # Emit many events
        for i in range(num_events):
            await event_queue.emit("high_load", {"index": i})
        
        # Wait for event processing
        max_wait = 5  # Maximum seconds to wait
        start_time = time.time()
        
        while received_events < num_events:
            await asyncio.sleep(0.1)
            if time.time() - start_time > max_wait:
                break
        
        # Verify all events were processed
        assert received_events == num_events
    
    @pytest.mark.asyncio
    async def test_concurrent_emit_and_subscribe(self, event_queue):
        """Test concurrent emit and subscribe operations."""
        # Number of concurrent operations
        num_concurrent = 20
        
        # Track subscriber counts
        subscription_results = []
        emission_results = []
        
        # Define functions for concurrent execution
        async def do_subscribe(idx):
            # Define a unique subscriber
            async def unique_subscriber(event_type, data):
                pass
            
            try:
                # Subscribe to a unique event type
                event_type = f"concurrent_event_{idx}"
                await event_queue.subscribe(event_type, unique_subscriber)
                return {"success": True, "event_type": event_type}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        async def do_emit(idx):
            try:
                # Emit to a random event type
                event_type = f"concurrent_event_{random.randint(0, num_concurrent-1)}"
                await event_queue.emit(event_type, {"index": idx})
                return {"success": True, "event_type": event_type}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Create tasks for concurrent subscription
        subscribe_tasks = [do_subscribe(i) for i in range(num_concurrent)]
        subscription_results = await asyncio.gather(*subscribe_tasks)
        
        # Create tasks for concurrent emission
        emit_tasks = [do_emit(i) for i in range(num_concurrent)]
        emission_results = await asyncio.gather(*emit_tasks)
        
        # Verify all operations succeeded
        assert all(result["success"] for result in subscription_results)
        assert all(result["success"] for result in emission_results)
        
        # Verify subscriber counts
        for i in range(num_concurrent):
            event_type = f"concurrent_event_{i}"
            assert event_queue.get_subscriber_count(event_type) == 1
    
    @pytest.mark.asyncio
    async def test_subscriber_exception_isolation(self, event_queue):
        """Test that exceptions in one subscriber don't affect others."""
        # Track received events
        received_by_good = []
        exception_occurred = False
        
        # Define a subscriber that raises an exception
        async def bad_subscriber(event_type, data):
            nonlocal exception_occurred
            exception_occurred = True
            raise Exception("Deliberate exception for testing")
        
        # Define a well-behaved subscriber
        async def good_subscriber(event_type, data):
            received_by_good.append((event_type, data))
        
        # Subscribe both to the same event type
        await event_queue.subscribe("isolation_test", bad_subscriber)
        await event_queue.subscribe("isolation_test", good_subscriber)
        
        # Emit a test event
        test_data = {"message": "Isolation test"}
        await event_queue.emit("isolation_test", test_data)
        
        # Wait for event processing
        await asyncio.sleep(0.2)
        
        # Verify the good subscriber still received the event
        assert exception_occurred is True
        assert len(received_by_good) == 1
        assert received_by_good[0][1] == test_data
    
    @pytest.mark.asyncio
    async def test_event_history(self, event_queue):
        """Test that events are properly recorded in history."""
        # Initial history length
        initial_history = len(event_queue._event_history)
        
        # Emit several events
        num_events = 5
        for i in range(num_events):
            await event_queue.emit(f"history_test_{i}", {"index": i})
        
        # Wait for event processing
        await asyncio.sleep(0.2)
        
        # Verify history length increased
        assert len(event_queue._event_history) == initial_history + num_events
        
        # Verify last events match what we emitted
        for i in range(num_events):
            # Check in reverse order
            idx = num_events - i - 1
            event = event_queue._event_history[-(i+1)]
            assert event.event_type == f"history_test_{idx}"
            assert event.data == {"index": idx}

class TestMultithreadedScenarios:
    """Tests for multithreaded scenarios."""
    
    @pytest.mark.asyncio
    async def test_emit_from_multiple_threads(self, event_queue):
        """Test emitting events from multiple threads."""
        # Number of threads and events per thread
        num_threads = 5
        events_per_thread = 10
        
        # Track received events
        received_events = {}
        
        # Create an event for thread coordination
        ready_event = threading.Event()
        
        # Define a subscriber that tracks events
        async def tracking_subscriber(event_type, data):
            thread_id = data.get("thread_id")
            if thread_id not in received_events:
                received_events[thread_id] = []
            received_events[thread_id].append(data)
        
        # Subscribe to the event
        await event_queue.subscribe("thread_test", tracking_subscriber)
        
        # Function to run in each thread
        def emit_from_thread(thread_id):
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Wait for all threads to be ready
            ready_event.wait()
            
            # Emit events
            for i in range(events_per_thread):
                async def do_emit():
                    await event_queue.emit("thread_test", {
                        "thread_id": thread_id,
                        "event_index": i
                    })
                
                loop.run_until_complete(do_emit())
            
            loop.close()
        
        # Create and start threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=emit_from_thread, args=(i,))
            thread.start()
            threads.append(thread)
        
        # Signal threads to start emitting
        ready_event.set()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Wait for event processing
        await asyncio.sleep(1.0)
        
        # Verify events from all threads were received
        assert len(received_events) == num_threads
        
        # Verify correct number of events per thread
        for thread_id in range(num_threads):
            assert len(received_events[thread_id]) == events_per_thread
            
            # Verify event indices
            indices = sorted(event["event_index"] for event in received_events[thread_id])
            assert indices == list(range(events_per_thread))
    
    @pytest.mark.asyncio
    async def test_cross_thread_event_delivery(self, event_queue):
        """Enhanced test for event delivery across threads with better synchronization."""
        # Events for thread coordination with more precise control
        subscriber_registered = threading.Event()
        event_emitted = threading.Event()
        event_received = threading.Event()
        thread_can_exit = threading.Event()
        thread_results = {}
        
        # Function to run in a separate thread
        def run_in_thread():
            # Create a thread-local event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            thread_results["thread_id"] = threading.get_ident()
            
            # Define an event that will be set when the subscriber is called
            async def thread_subscriber(event_type, data):
                logger.info(f"Subscriber received event: {event_type} with data: {data}")
                thread_results["received"] = [(event_type, data)]
                event_received.set()
            
            async def thread_task():
                try:
                    # Subscribe to event
                    logger.info("Thread subscribing to 'cross_thread' event")
                    await event_queue.subscribe("cross_thread", thread_subscriber)
                    
                    # Signal that we've subscribed
                    logger.info("Thread signaling that subscriber is registered")
                    subscriber_registered.set()
                    
                    # Wait for the event to be emitted from the main thread
                    logger.info("Thread waiting for event to be emitted")
                    event_emitted.wait()
                    logger.info("Thread notified that event was emitted")
                    
                    # Wait for the event to be received or timeout
                    start_time = time.time()
                    timeout = 5.0  # Longer timeout for reliability
                    
                    logger.info("Thread waiting to receive the event")
                    while not event_received.is_set() and (time.time() - start_time) < timeout:
                        # Process events in this loop but don't block for too long
                        await asyncio.sleep(0.1)
                    
                    if event_received.is_set():
                        logger.info("Thread successfully received the event")
                        thread_results["success"] = True
                    else:
                        logger.info("Thread timed out waiting for event")
                        thread_results["success"] = False
                        thread_results["timeout"] = True
                    
                    # Wait for main thread to allow us to exit
                    logger.info("Thread waiting for permission to exit")
                    thread_can_exit.wait()
                    logger.info("Thread received permission to exit")
                    
                except Exception as e:
                    logger.error(f"Exception in thread_task: {e}")
                    thread_results["error"] = str(e)
                    thread_results["success"] = False
            
            try:
                # Run the task in the thread's event loop
                logger.info("Thread starting event loop")
                loop.run_until_complete(thread_task())
                
                # Keep the event loop running for a bit longer to process any pending events
                # but don't close it yet - that will happen when we exit the function
                logger.info("Thread task completed")
                
            except Exception as e:
                logger.error(f"Exception in run_in_thread: {e}")
                thread_results["error"] = str(e)
            finally:
                # Now it's safe to close the loop
                logger.info("Thread closing event loop")
                loop.close()
        
        # Start the thread
        logger.info("Main thread starting worker thread")
        thread = threading.Thread(target=run_in_thread)
        thread.start()
        
        try:
            # Wait for thread to subscribe
            logger.info("Main thread waiting for subscriber to register")
            if not subscriber_registered.wait(timeout=5.0):
                logger.error("Timed out waiting for subscriber to register")
                assert False, "Timed out waiting for subscriber to register"
            logger.info("Main thread confirmed subscriber registration")
            
            # Small delay to ensure subscription is fully processed
            await asyncio.sleep(0.2)
            
            # Emit event from main thread
            logger.info("Main thread emitting event")
            test_data = {"message": "Cross-thread test", "source_thread": threading.get_ident()}
            await event_queue.emit("cross_thread", test_data)
            logger.info("Main thread emitted event")
            
            # Signal that event has been emitted
            event_emitted.set()
            
            # Wait for event to be received or timeout
            logger.info("Main thread waiting for event to be received")
            received_timeout = 5.0
            start_time = time.time()
            
            while not event_received.is_set() and (time.time() - start_time) < received_timeout:
                await asyncio.sleep(0.1)
            
            # Check if event was received
            if not event_received.is_set():
                logger.error("Timed out waiting for event to be received")
            
        finally:
            # Allow thread to exit
            logger.info("Main thread signaling thread can exit")
            thread_can_exit.set()
            
            # Wait for thread to complete
            logger.info("Main thread waiting for worker thread to complete")
            thread.join(timeout=5.0)
            logger.info("Main thread: worker thread completed")
        
        # Verify we have results from the thread
        assert "success" in thread_results, "Thread did not complete properly"
        
        # Check if there was an error in the thread
        if "error" in thread_results:
            logger.error(f"Thread encountered an error: {thread_results['error']}")
        
        # Verify events were received in the other thread
        assert thread_results.get("success", False), "Thread did not successfully receive the event"
        assert "received" in thread_results, "Thread did not track received events"
        assert len(thread_results["received"]) == 1, "Expected exactly one event to be received"
        
        # Verify the event data
        received_event = thread_results["received"][0]
        assert received_event[0] == "cross_thread", f"Wrong event type: {received_event[0]}"
        assert received_event[1] == test_data, f"Wrong event data: {received_event[1]}"

    @pytest.mark.asyncio
    async def test_event_queue_cross_thread_delivery_mechanism(self, event_queue):
        """Test specifically focused on the cross-thread delivery mechanism."""
        
        # Create a flag to track delivery method
        delivery_method_used = {"direct": 0, "cross_thread": 0}
        actual_subscriber_called = threading.Event()
        
        # Create a custom event queue with instrumented delivery methods for testing
        class InstrumentedEventQueue(EventQueue):
            async def _deliver_event_direct(self, event, subscriber, subscriber_is_coroutine):
                delivery_method_used["direct"] += 1
                logger.info(f"Using _deliver_event_direct for {event.event_type}")
                return await super()._deliver_event_direct(event, subscriber, subscriber_is_coroutine)
                
            async def _deliver_event_cross_thread(self, event, subscriber, subscriber_loop, subscriber_thread):
                delivery_method_used["cross_thread"] += 1
                logger.info(f"Using _deliver_event_cross_thread for {event.event_type}")
                return await super()._deliver_event_cross_thread(
                    event, subscriber, subscriber_loop, subscriber_thread)
        
        # Replace the event queue with our instrumented version
        instrumented_queue = InstrumentedEventQueue(max_size=100)
        await instrumented_queue.start()
        
        try:
            # Thread synchronization objects
            thread_started = threading.Event()
            thread_can_emit = threading.Event()
            thread_emitted = threading.Event()
            thread_can_exit = threading.Event()
            
            # Thread function
            def thread_function():
                # Set up a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def setup_and_wait():
                    nonlocal actual_subscriber_called
                    
                    # Define a subscriber function that will be called in main thread
                    async def subscriber(event_type, data):
                        logger.info(f"Subscriber called with {event_type}: {data}")
                        actual_subscriber_called.set()
                    
                    # Subscribe from this thread but specify it should run in main thread
                    logger.info("Thread subscribing to 'cross_thread_test'")
                    await instrumented_queue.subscribe("cross_thread_test", subscriber)
                    
                    # Signal that we're ready
                    thread_started.set()
                    
                    # Wait until told to emit
                    logger.info("Thread waiting for permission to emit")
                    thread_can_emit.wait()
                    
                    # Emit an event from this thread
                    logger.info("Thread emitting event")
                    await instrumented_queue.emit("cross_thread_test", {
                        "thread_id": threading.get_ident(),
                        "message": "From worker thread"
                    })
                    
                    # Signal that we've emitted
                    thread_emitted.set()
                    
                    # Wait until told to exit
                    logger.info("Thread waiting for permission to exit")
                    thread_can_exit.wait()
                    logger.info("Thread exiting")
                    
                # Run the async function and then close the loop
                loop.run_until_complete(setup_and_wait())
                loop.close()
            
            # Start the thread
            thread = threading.Thread(target=thread_function)
            thread.start()
            
            # Wait for thread to start and subscribe
            logger.info("Main thread waiting for worker thread to start")
            if not thread_started.wait(timeout=5.0):
                assert False, "Thread did not start in time"
            
            # Give a moment for subscription to fully process
            await asyncio.sleep(0.2)
            
            # Signal thread to emit event
            logger.info("Main thread signaling worker thread to emit event")
            thread_can_emit.set()
            
            # Wait for thread to emit
            logger.info("Main thread waiting for worker thread to emit event")
            if not thread_emitted.wait(timeout=5.0):
                assert False, "Thread did not emit event in time"
            
            # Wait a bit to allow event to be processed
            logger.info("Main thread waiting for event processing")
            start_time = time.time()
            timeout = 5.0
            
            while time.time() - start_time < timeout:
                if actual_subscriber_called.is_set() or (
                    delivery_method_used["direct"] > 0 or 
                    delivery_method_used["cross_thread"] > 0
                ):
                    break
                await asyncio.sleep(0.1)
            
            # Log the delivery methods that were used
            logger.info(f"Delivery methods used: {delivery_method_used}")
            
            # Assert that some delivery method was used
            assert delivery_method_used["direct"] > 0 or delivery_method_used["cross_thread"] > 0, \
                "No delivery method was used"
            
            # If direct delivery was used, cross-thread should be too
            if delivery_method_used["direct"] > 0:
                logger.info("Direct delivery was used - check if this was intentional")
            
            # Verify that the subscriber was actually called
            assert actual_subscriber_called.is_set(), "Subscriber was never called"
            
        finally:
            # Allow the thread to exit
            thread_can_exit.set()
            thread.join(timeout=5.0)
            
            # Stop the instrumented queue
            await instrumented_queue.stop()

    @pytest.mark.asyncio
    async def test_event_delivery_with_delayed_loop_closing(self, event_queue):
        """Test specifically focused on ensuring the event loop stays open during event delivery."""
        
        # Create tracking variables
        thread_results = {"received_events": []}
        
        # Events for thread coordination
        subscriber_registered = threading.Event()
        emission_complete = threading.Event()
        event_received = threading.Event()
        safe_to_close_loop = threading.Event()
        thread_loop_closed = threading.Event()
        
        # Define a custom lock class that logs when it's acquired and released
        class LoggingLock:
            def __init__(self, name):
                self.lock = threading.Lock()
                self.name = name
                
            def acquire(self, *args, **kwargs):
                logger.info(f"Attempting to acquire {self.name} lock")
                result = self.lock.acquire(*args, **kwargs)
                logger.info(f"Acquired {self.name} lock: {result}")
                return result
                
            def release(self):
                logger.info(f"Releasing {self.name} lock")
                return self.lock.release()
                
            def __enter__(self):
                self.acquire()
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.release()
        
        # Create a lock to synchronize subscriber access
        subscriber_lock = LoggingLock("subscriber")
        
        # Thread function
        def thread_function():
            # Initialize thread-local data
            thread_id = threading.get_ident()
            thread_results["thread_id"] = thread_id
            
            logger.info(f"Worker thread {thread_id} starting")
            
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Store the loop for reference
            thread_results["loop"] = loop
            
            # Define the subscriber function
            async def thread_subscriber(event_type, data):
                with subscriber_lock:
                    logger.info(f"Subscriber in thread {thread_id} received event: {event_type}")
                    thread_results["received_events"].append((event_type, data))
                    event_received.set()
            
            # Create a task to handle subscription and event processing
            async def setup_and_process():
                try:
                    # Subscribe to the event
                    logger.info(f"Thread {thread_id} subscribing to 'thread_test'")
                    await event_queue.subscribe("thread_test", thread_subscriber)
                    logger.info(f"Thread {thread_id} subscription complete")
                    
                    # Signal that we've subscribed
                    subscriber_registered.set()
                    
                    # Wait for emission to complete
                    logger.info(f"Thread {thread_id} waiting for emission to complete")
                    while not emission_complete.is_set():
                        await asyncio.sleep(0.1)
                    logger.info(f"Thread {thread_id} detected emission complete")
                    
                    # Process events for a while to make sure we receive anything pending
                    for _ in range(50):  # Process for 5 seconds max
                        if event_received.is_set():
                            logger.info(f"Thread {thread_id} received event, breaking wait loop")
                            break
                        await asyncio.sleep(0.1)
                    
                    # Wait for permission to close the loop
                    logger.info(f"Thread {thread_id} waiting for permission to close loop")
                    while not safe_to_close_loop.is_set():
                        await asyncio.sleep(0.1)
                    logger.info(f"Thread {thread_id} received permission to close loop")
                    
                except Exception as exc:
                    logger.error(f"Error in thread {thread_id}: {exc}")
                    thread_results["error"] = str(exc)
            
            try:
                # Run the setup and processing task
                logger.info(f"Thread {thread_id} running setup and process task")
                loop.run_until_complete(setup_and_process())
                
                # Log loop closure
                logger.info(f"Thread {thread_id} closing event loop")
                loop.close()
                thread_loop_closed.set()
                logger.info(f"Thread {thread_id} closed event loop")
                
            except Exception as exc:
                logger.error(f"Error in thread_function for thread {thread_id}: {exc}")
                thread_results["error"] = str(exc)
        
        # Start the thread
        logger.info("Main thread starting worker thread")
        thread = threading.Thread(target=thread_function)
        thread.start()
        
        try:
            # Wait for subscription to complete
            logger.info("Main thread waiting for subscription")
            if not subscriber_registered.wait(timeout=5.0):
                assert False, "Subscription did not complete in time"
            logger.info("Main thread detected subscription complete")
            
            # Allow a moment for the subscription to fully process
            await asyncio.sleep(0.5)
            
            # Emit the event
            logger.info("Main thread emitting event")
            await event_queue.emit("thread_test", {
                "message": "Test from main thread",
                "timestamp": datetime.now().isoformat()
            })
            logger.info("Main thread emission complete")
            
            # Signal that emission is complete
            emission_complete.set()

            # wait for event processing to complete
            await event_queue.wait_for_processing(timeout=2.0)
            
            # Wait for event to be received or timeout
            logger.info("Main thread waiting for event receipt")
            received = event_received.wait(timeout=5.0)
            logger.info(f"Main thread detected event received: {received}")
            
            if not received:
                logger.error("Event was not received in time")
                
                # Get extra debugging information
                logger.info(f"Thread results so far: {thread_results}")
                logger.info(f"Loop closed: {thread_loop_closed.is_set()}")
                
                # Check internal event queue state
                subscriber_count = event_queue.get_subscriber_count("thread_test")
                logger.info(f"Subscriber count for 'thread_test': {subscriber_count}")
            
            # Now it's safe to close the loop
            logger.info("Main thread signaling it's safe to close loop")
            safe_to_close_loop.set()
            
            # Wait for loop to close
            logger.info("Main thread waiting for loop to close")
            loop_closed = thread_loop_closed.wait(timeout=5.0)
            logger.info(f"Loop closed: {loop_closed}")
            
        finally:
            # Make sure thread can exit even if test fails
            safe_to_close_loop.set()
            
            # Join the thread
            logger.info("Main thread joining worker thread")
            thread.join(timeout=5.0)
            logger.info("Main thread joined worker thread")
        
        # Verify that the event was received
        assert len(thread_results["received_events"]) > 0, "No events were received in thread"
        
        # Verify the event data
        event_data = thread_results["received_events"][0]
        assert event_data[0] == "thread_test", f"Unexpected event type: {event_data[0]}"
        assert "message" in event_data[1], "Event data missing 'message' field"
        assert event_data[1]["message"] == "Test from main thread", f"Unexpected message content: {event_data[1]}"

    @pytest.mark.asyncio
    async def test_event_queue_handles_closed_loops(self):
        """Test how EventQueue handles delivery to subscribers with closed loops."""
        
        # Create a custom event queue with inspection capabilities
        class InspectableEventQueue(EventQueue):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.delivery_attempts = []
                self.delivery_failures = []
                
            async def _deliver_event_cross_thread(self, event, callback, event_id, subscriber_loop, subscriber_thread):
                """Override to track cross-thread delivery attempts."""
                result = {
                    "type": "cross_thread",
                    "event": event,
                    "subscriber_loop_closed": subscriber_loop.is_closed() if subscriber_loop else True,
                    "current_thread": threading.get_ident(),
                    "subscriber_thread": subscriber_thread,
                    "timestamp": datetime.now().isoformat()
                }
                self.delivery_attempts.append(result)
                
                try:
                    return await super()._deliver_event_cross_thread(
                        event, callback, subscriber_loop, subscriber_thread)
                except Exception as e:
                    failure = {
                        "type": "cross_thread",
                        "event": event,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    self.delivery_failures.append(failure)
                    raise
                    
            async def _deliver_event_direct(self, event, callback, event_id):
                """Override to track direct delivery attempts."""
                result = {
                    "type": "direct",
                    "event": event,
                    "current_thread": threading.get_ident(),
                    "timestamp": datetime.now().isoformat()
                }
                self.delivery_attempts.append(result)
                
                try:
                    return await super()._deliver_event_direct(event, callback, event_id)
                except Exception as e:
                    failure = {
                        "type": "direct",
                        "event": event,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    self.delivery_failures.append(failure)
                    raise
        
        # Create our inspectable event queue
        queue = InspectableEventQueue(max_size=100)
        await queue.start()
        
        try:
            # Thread control events
            thread_started = threading.Event()
            loop_ready = threading.Event()
            ok_to_close_loop = threading.Event()
            loop_closed = threading.Event()
            thread_complete = threading.Event()
            
            # Thread results
            thread_info = {}
            
            # Thread function
            def thread_worker():
                thread_info["thread_id"] = threading.get_ident()
                
                # Create a new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                thread_info["loop_id"] = id(loop)
                
                async def subscriber(event_type, data):
                    # This likely won't be called, but we'll track it anyway
                    thread_info["received_event"] = (event_type, data)
                
                async def setup_task():
                    # Subscribe to an event
                    await queue.subscribe("test_event", subscriber)
                    
                    # Signal that we're ready
                    loop_ready.set()
                    thread_started.set()
                    
                    # Wait until told to close the loop
                    while not ok_to_close_loop.is_set():
                        await asyncio.sleep(0.1)
                
                # Run the setup task
                loop.run_until_complete(setup_task())
                
                # Explicitly close the loop
                logger.info("Thread closing event loop")
                loop.close()
                loop_closed.set()
                
                # Wait until the main thread says we're done
                thread_complete.wait()
            
            # Start the thread
            thread = threading.Thread(target=thread_worker)
            thread.start()
            
            # Wait for thread to start and subscribe
            assert thread_started.wait(timeout=5.0), "Thread did not start in time"
            assert loop_ready.wait(timeout=5.0), "Event loop was not ready in time"
            
            # Allow time for subscription to be fully processed
            await asyncio.sleep(0.5)
            
            # Signal thread to close its loop
            ok_to_close_loop.set()
            
            # Wait for loop to be closed
            assert loop_closed.wait(timeout=5.0), "Loop was not closed in time"
            
            # Now emit an event - this should still work but delivery will fail
            await queue.emit("test_event", {"message": "After loop closed"})
            
            # Wait for event processing attempts
            await asyncio.sleep(1.0)
            
            # Complete the thread
            thread_complete.set()
            thread.join(timeout=5.0)
            
            # Check the delivery attempts and failures
            logger.info(f"Delivery attempts: {len(queue.delivery_attempts)}")
            for i, attempt in enumerate(queue.delivery_attempts):
                logger.info(f"Attempt {i+1}: type={attempt.get('type', 'unknown')}")
            
            logger.info(f"Delivery failures: {len(queue.delivery_failures)}")
            for i, failure in enumerate(queue.delivery_failures):
                logger.info(f"Failure {i+1}: {failure.get('error', 'unknown')}")
            
            # Verify that some delivery attempt was made (either direct or cross-thread)
            assert len(queue.delivery_attempts) > 0, "No delivery attempts were made"
            
            # Verify the type of delivery that was attempted
            delivery_types = [attempt.get('type') for attempt in queue.delivery_attempts]
            logger.info(f"Delivery types used: {delivery_types}")
            
            # There should be at least one direct delivery attempt
            assert 'direct' in delivery_types, "No direct delivery attempts were made"
            
        finally:
            # Clean up
            ok_to_close_loop.set()
            thread_complete.set()
            await queue.stop()

    @pytest.mark.asyncio
    async def test_event_delivery_with_queue_draining(self, event_queue):
        """Test ensuring that event queue is properly drained before closing loops."""
        
        # Event for tracking
        event_processed = asyncio.Event()
        event_received = threading.Event()
        thread_info = {"received": False}
        
        # Create a function to drain the event queue
        async def drain_event_queue(queue, timeout=5.0):
            """Wait for the event queue to process all pending events."""
            # Get the current queue size
            if hasattr(queue, "_queue"):
                initial_size = queue._queue.qsize()
                logger.info(f"Initial queue size: {initial_size}")
                
                # Wait for queue to empty
                start_time = time.time()
                while time.time() - start_time < timeout:
                    current_size = queue._queue.qsize()
                    if current_size == 0:
                        logger.info("Queue is empty")
                        # But also wait a bit to ensure processing completes
                        await asyncio.sleep(0.5)
                        return True
                    logger.info(f"Waiting for queue to drain: {current_size} items remaining")
                    await asyncio.sleep(0.1)
                
                logger.warning(f"Timeout waiting for queue to drain, {queue._queue.qsize()} items remaining")
                return False
            else:
                # If we can't access the queue, just wait a reasonable time
                logger.info("Queue not accessible, using fixed delay")
                await asyncio.sleep(1.0)
                return True
        
        # Thread function that processes events
        def thread_func():
            # Create a new loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Keep track of when the loop is created and closed
            thread_info["loop_created_at"] = time.time()
            thread_info["thread_id"] = threading.get_ident()
            
            async def subscriber(event_type, data):
                logger.info(f"Subscriber received event: {event_type} with data: {data}")
                thread_info["received"] = True
                thread_info["event_type"] = event_type
                thread_info["event_data"] = data
                event_received.set()
            
            async def thread_task():
                # Subscribe to events
                logger.info("Thread subscribing to event")
                await event_queue.subscribe("drain_test", subscriber)
                
                # Signal that event was processed
                event_processed.set()
                
                # Keep the loop running long enough for events to be processed
                # Wait for event to be received or timeout
                start_time = time.time()
                while time.time() - start_time < 10.0:
                    if event_received.is_set():
                        logger.info("Event received, breaking wait loop")
                        break
                    await asyncio.sleep(0.1)
                    
                # Wait a bit longer to make sure all processing completes
                await asyncio.sleep(0.5)
            
            # Run the task
            try:
                loop.run_until_complete(thread_task())
            finally:
                # Record when loop is being closed
                thread_info["loop_closed_at"] = time.time()
                logger.info(f"Thread closing loop after {thread_info['loop_closed_at'] - thread_info['loop_created_at']} seconds")
                loop.close()
        
        # Start the thread
        thread = threading.Thread(target=thread_func)
        thread.start()
        
        # Wait for subscription to be processed
        try:
            await asyncio.wait_for(event_processed.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            assert False, "Timed out waiting for subscription"
        
        # Wait a bit for the subscription to be fully processed
        await asyncio.sleep(0.5)
        
        # Emit the event
        logger.info("Emitting event")
        await event_queue.emit("drain_test", {"message": "Test drain functionality"})
        
        # Monitor and log queue size
        queue_empty = await drain_event_queue(event_queue)
        logger.info(f"Queue drained: {queue_empty}")
        
        # Wait for thread to complete
        thread.join(timeout=10.0)
        
        # Log timings
        if "loop_created_at" in thread_info and "loop_closed_at" in thread_info:
            loop_lifetime = thread_info["loop_closed_at"] - thread_info["loop_created_at"]
            logger.info(f"Loop lifetime: {loop_lifetime:.2f} seconds")
        
        # Verify event was received
        assert thread_info["received"], "Event was not received in subscriber thread"
        assert thread_info["event_type"] == "drain_test", f"Wrong event type: {thread_info.get('event_type')}"
        assert thread_info["event_data"]["message"] == "Test drain functionality", "Wrong event data"


# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])