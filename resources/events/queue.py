"""
Core event queue implementation with priority and backpressure support.

This module provides the EventQueue class which serves as the central hub for
event-based communication throughout the FFTT system, with support for event
prioritization, batching, and reliable delivery.
"""
import asyncio
import concurrent.futures
import logging
import queue
import random
import sys
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Set, Optional, Callable, Awaitable, Tuple, Union

from .types import Event, ResourceEventTypes
from .backpressure import EventBackpressureManager
from .utils import wait_with_backoff, with_timeout

logger = logging.getLogger(__name__)

class EventQueue:
    """
    Thread-safe event queue with priority processing, backpressure, and batching.
    
    This implementation uses the actor model, where the event processor runs in a dedicated
    thread with its own event loop, and all communication with the queue is done through
    thread-safe message passing. This avoids cross-thread event loop access issues.
    """
    def __init__(self, max_size: int = 1000, queue_id: Optional[str] = None):
        # Queue configuration
        self._max_size = max_size
        self._id = queue_id or f"event_queue_{id(self)}"
        
        # Thread synchronization mechanism
        self._queue_lock = threading.RLock()
        
        # Priority queues - these are implementation details and lazily initialized
        # We use standard threading.Queue for thread-safety rather than asyncio.Queue
        self._high_priority_queue = None
        self._normal_priority_queue = None
        self._low_priority_queue = None
        
        # Async converter queue - used only by the processor thread
        self._async_high_queue = None
        self._async_normal_queue = None
        self._async_low_queue = None
        
        # Resource management
        self._subscribers: Dict[str, Set[Callable[[str, Dict[str, Any]], Awaitable[None]]]] = {}
        self._event_history: List[Event] = []
        self._processing_retries: Dict[str, int] = {}
        self._max_retries = 3
        self._retry_delay = 1.0  # seconds
        
        # State tracking
        self._running = False
        self._processor_thread = None
        self._thread_executor = None
        self._stop_event = threading.Event()
        
        # Initialize backpressure manager
        self._backpressure_manager = EventBackpressureManager()
        
        # Ensure these are preserved for consistent thread identity
        self._processor_thread_id = None
        self._creation_thread_id = threading.get_ident()
        
        logger.debug(f"EventQueue {self._id} created in thread {self._creation_thread_id}")
    
    @property
    def high_priority_queue(self):
        """Thread-safe high priority queue for cross-thread access"""
        with self._queue_lock:
            if self._high_priority_queue is None:
                self._high_priority_queue = queue.Queue(maxsize=max(10, self._max_size // 10))
            return self._high_priority_queue
    
    @property
    def normal_priority_queue(self):
        """Thread-safe normal priority queue for cross-thread access"""
        with self._queue_lock:
            if self._normal_priority_queue is None:
                self._normal_priority_queue = queue.Queue(maxsize=self._max_size)
            return self._normal_priority_queue
            
    @property
    def low_priority_queue(self):
        """Thread-safe low priority queue for cross-thread access"""
        with self._queue_lock:
            if self._low_priority_queue is None:
                self._low_priority_queue = queue.Queue(maxsize=self._max_size * 2)
            return self._low_priority_queue
    
    async def emit(self, event_type: str, data: Dict[str, Any], 
                   correlation_id: Optional[str] = None, 
                   priority: str = "normal") -> bool:
        """
        Emit an event to the queue with thread-safety.
        
        Args:
            event_type: The type of event to emit
            data: The event data payload
            correlation_id: Optional correlation ID for tracking related events
            priority: Event priority - "high", "normal", or "low"
            
        Returns:
            bool: True if event was queued, False if rejected due to back-pressure
        """
        # Convert enum if needed
        event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
        
        # Validate payload schema if available
        try:
            import inspect
            from resources.schemas import (
                ValidationEventPayload,
                ValidationStateChangedPayload, RefinementContextPayload,
                RefinementIterationPayload, AgentUpdateRequestPayload,
                # Phase Two schemas
                ComponentEventPayload, TestEventPayload, IntegrationEventPayload,
                # Phase Three schemas
                FeatureEventPayload, OptimizationEventPayload, FeatureIntegrationPayload,
                # Phase Four schemas
                CodeGenerationPayload, CompilationPayload, RefinementIterationPayloadPhase4
            )
            
            # Map event types to expected payload schemas
            event_schema_mapping = {
                # Phase 0 Earth Agent events
                ResourceEventTypes.EARTH_VALIDATION_COMPLETE.value: ValidationEventPayload,
                ResourceEventTypes.EARTH_VALIDATION_STARTED.value: ValidationEventPayload,
                ResourceEventTypes.EARTH_VALIDATION_FAILED.value: ValidationEventPayload,
                
                # Phase One validation events
                ResourceEventTypes.PHASE_ONE_VALIDATION_STATE_CHANGED.value: ValidationStateChangedPayload,
                ResourceEventTypes.PHASE_ONE_VALIDATION_COMPLETED.value: ValidationStateChangedPayload,
                ResourceEventTypes.PHASE_ONE_VALIDATION_FAILED.value: ValidationStateChangedPayload,
                
                # Phase One refinement events
                ResourceEventTypes.PHASE_ONE_REFINEMENT_CREATED.value: RefinementContextPayload,
                ResourceEventTypes.PHASE_ONE_REFINEMENT_UPDATED.value: RefinementContextPayload,
                ResourceEventTypes.PHASE_ONE_REFINEMENT_COMPLETED.value: RefinementContextPayload,
                ResourceEventTypes.PHASE_ONE_REFINEMENT_ITERATION.value: RefinementIterationPayload,
                
                # Agent update events
                ResourceEventTypes.AGENT_UPDATE_REQUEST.value: AgentUpdateRequestPayload,
                ResourceEventTypes.AGENT_UPDATE_COMPLETE.value: AgentUpdateRequestPayload,
                ResourceEventTypes.AGENT_UPDATE_FAILED.value: AgentUpdateRequestPayload,
                
                # Phase Two component events
                ResourceEventTypes.PHASE_TWO_COMPONENT_CREATED.value: ComponentEventPayload,
                ResourceEventTypes.PHASE_TWO_COMPONENT_UPDATED.value: ComponentEventPayload,
                ResourceEventTypes.PHASE_TWO_COMPONENT_DELETED.value: ComponentEventPayload,
                
                # Phase Two test events
                ResourceEventTypes.PHASE_TWO_TEST_CREATED.value: TestEventPayload,
                ResourceEventTypes.PHASE_TWO_TEST_EXECUTED.value: TestEventPayload,
                ResourceEventTypes.PHASE_TWO_TEST_FAILED.value: TestEventPayload,
                ResourceEventTypes.PHASE_TWO_TEST_PASSED.value: TestEventPayload,
                
                # Phase Two integration events
                ResourceEventTypes.PHASE_TWO_INTEGRATION_STARTED.value: IntegrationEventPayload,
                ResourceEventTypes.PHASE_TWO_INTEGRATION_COMPLETED.value: IntegrationEventPayload,
                ResourceEventTypes.PHASE_TWO_INTEGRATION_FAILED.value: IntegrationEventPayload,
                ResourceEventTypes.PHASE_TWO_SYSTEM_TEST_STARTED.value: IntegrationEventPayload,
                ResourceEventTypes.PHASE_TWO_SYSTEM_TEST_COMPLETED.value: IntegrationEventPayload,
                
                # Phase Three feature events
                ResourceEventTypes.PHASE_THREE_FEATURE_REQUESTED.value: FeatureEventPayload,
                ResourceEventTypes.PHASE_THREE_FEATURE_CREATED.value: FeatureEventPayload,
                ResourceEventTypes.PHASE_THREE_FEATURE_EVOLVED.value: FeatureEventPayload,
                ResourceEventTypes.PHASE_THREE_FEATURE_INTEGRATED.value: FeatureEventPayload,
                
                # Phase Three optimization events
                ResourceEventTypes.PHASE_THREE_OPTIMIZATION_STARTED.value: OptimizationEventPayload,
                ResourceEventTypes.PHASE_THREE_OPTIMIZATION_ITERATION.value: OptimizationEventPayload,
                ResourceEventTypes.PHASE_THREE_OPTIMIZATION_COMPLETED.value: OptimizationEventPayload,
                ResourceEventTypes.PHASE_THREE_NATURAL_SELECTION.value: OptimizationEventPayload,
                
                # Phase Four code generation events
                ResourceEventTypes.PHASE_FOUR_CODE_GENERATION_STARTED.value: CodeGenerationPayload,
                ResourceEventTypes.PHASE_FOUR_CODE_GENERATION_COMPLETED.value: CodeGenerationPayload,
                ResourceEventTypes.PHASE_FOUR_CODE_GENERATION_FAILED.value: CodeGenerationPayload,
                
                # Phase Four compilation events
                ResourceEventTypes.PHASE_FOUR_COMPILATION_STARTED.value: CompilationPayload,
                ResourceEventTypes.PHASE_FOUR_COMPILATION_PASSED.value: CompilationPayload,
                ResourceEventTypes.PHASE_FOUR_COMPILATION_FAILED.value: CompilationPayload,
                
                # Phase Four refinement events
                ResourceEventTypes.PHASE_FOUR_REFINEMENT_ITERATION.value: RefinementIterationPayloadPhase4,
                ResourceEventTypes.PHASE_FOUR_DEBUG_STARTED.value: CodeGenerationPayload,
                ResourceEventTypes.PHASE_FOUR_DEBUG_COMPLETED.value: CodeGenerationPayload,
            }
            
            # Check if event type has a schema mapping
            if event_type_str in event_schema_mapping:
                schema_class = event_schema_mapping[event_type_str]
                
                # If the payload doesn't match the schema, add required fields with defaults
                required_fields = inspect.signature(schema_class.__init__).parameters
                
                # Add any missing required fields with default values
                for field_name, param in required_fields.items():
                    if field_name not in ('self', 'args', 'kwargs') and field_name not in data:
                        # Get default value if available
                        if param.default is not inspect.Parameter.empty:
                            data[field_name] = param.default
                        elif field_name in ('timestamp', 'event_id'):
                            # Special handling for common fields
                            if field_name == 'timestamp':
                                data[field_name] = datetime.now().isoformat()
                            elif field_name == 'event_id':
                                data[field_name] = str(uuid.uuid4())
                
                logger.debug(f"Validated event {event_type_str} against schema {schema_class.__name__}")
                
                # Try to validate the completed payload against the schema
                try:
                    schema_instance = schema_class(**data)
                except Exception as validation_error:
                    logger.warning(f"Event payload for {event_type_str} does not match schema {schema_class.__name__}: {validation_error}")
        except ImportError:
            # If schemas module is not available, skip validation
            logger.debug(f"Schema validation skipped for event {event_type_str}")
        except Exception as e:
            logger.warning(f"Error validating event payload for {event_type_str}: {e}")
        
        # Create event object with priority
        try:
            event_id = str(uuid.uuid4())
        except ImportError:
            event_id = f"event_{random.randint(10000, 99999)}"
        
        # Create the event object
        event = Event(
            event_type=event_type_str,
            data=data,
            correlation_id=correlation_id,
            priority=priority,
            metadata={"event_id": event_id}
        )
        
        # Check rate limiting before queue insertion
        if not self._backpressure_manager.check_rate_limit(event.event_type, event.priority):
            return False
        
        # Adjust priority based on system load
        adjusted_priority = self._backpressure_manager.get_adjusted_priority(
            event.event_type, event.priority
        )
        
        # Check if event should be rejected due to backpressure
        if self._backpressure_manager.should_reject_event(event.event_type, adjusted_priority):
            return False
        
        # Update event priority if it was adjusted
        if adjusted_priority != event.priority:
            event.priority = adjusted_priority
        
        # The key change: thread-safe emission using standard Python queue
        try:
            # Select target queue based on priority
            if event.priority == "high":
                target_queue = self.high_priority_queue
            elif event.priority == "low":
                target_queue = self.low_priority_queue
            else:
                target_queue = self.normal_priority_queue
            
            # Thread-safe queue insertion
            target_queue.put_nowait(event)
            
            # Store event in history for debugging
            with self._queue_lock:
                self._event_history.append(event)
                if len(self._event_history) > 10000:
                    self._event_history = self._event_history[-10000:]
            
            logger.debug(f"Emitted {event.priority} priority event {event.event_type} to queue {self._id}")
            return True
            
        except queue.Full:
            logger.warning(f"Queue full, rejecting {event.priority} priority event {event.event_type}")
            return False
        except Exception as e:
            logger.error(f"Failed to emit event {event.event_type}: {e}")
            return False
    
    async def emit_with_docs(
        self, 
        event_type: str, 
        data: Dict[str, Any], 
        correlation_id: Optional[str] = None,
        priority: str = "normal",
        publisher_component: str = None
    ) -> bool:
        """
        Emit event with documentation support.
        
        This method validates the event against the registry and logs warnings if:
        1. The event type is not registered
        2. The publisher is not listed as a valid publisher for this event
        3. The payload doesn't match the expected schema
        
        Args:
            event_type: The type of event to emit
            data: The event data
            correlation_id: Optional correlation ID for tracking related events
            priority: Event priority - "high", "normal", or "low"
            publisher_component: The component emitting the event
            
        Returns:
            bool: True if event was queued, False if rejected due to back-pressure
        """
        try:
            from resources.event_registry import EventRegistry
            
            # Convert enum if needed
            event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
            
            # Check if event type is registered
            metadata = EventRegistry.get_event_metadata(event_type_str)
            if metadata is None:
                logger.warning(f"Event type '{event_type_str}' is not registered in the event registry")
            elif publisher_component and publisher_component not in metadata.publisher_components:
                logger.warning(f"Component '{publisher_component}' is not registered as a publisher for event '{event_type_str}'")
            
            # Validate against schema if available
            if metadata and metadata.schema_class:
                try:
                    schema_class = metadata.schema_class
                    schema_class(**data)
                except Exception as e:
                    logger.warning(f"Event payload does not match schema {schema_class.__name__}: {e}")
            
            # Set priority from metadata if not explicitly provided
            if metadata and priority == "normal":
                priority = metadata.priority
        except ImportError:
            # If EventRegistry is not available, log and continue
            logger.debug(f"EventRegistry not available for validation of {event_type}")
        except Exception as e:
            logger.warning(f"Error during event documentation validation: {e}")
        
        # Emit the event using the standard method
        return await self.emit(event_type, data, correlation_id, priority)
    
    def get_nowait(self):
        """
        Non-blocking get from the event queue with thread safety.
        
        This method uses thread-safe Queue.get_nowait() to retrieve events, making it
        safe to call from any thread without event loop concerns.
        
        Returns:
            The next event in the queue.
            
        Raises:
            asyncio.QueueEmpty: If the queue is empty
        """
        # First check high priority queue
        try:
            return self.high_priority_queue.get_nowait()
        except queue.Empty:
            pass
        
        # Then normal priority queue
        try:
            return self.normal_priority_queue.get_nowait()
        except queue.Empty:
            pass
        
        # Finally low priority queue
        try:
            return self.low_priority_queue.get_nowait()
        except queue.Empty:
            # Raise asyncio.QueueEmpty for API compatibility
            raise asyncio.QueueEmpty("All queues are empty")
    
    async def wait_for_processing(self, timeout=5.0):
        """
        Wait for all currently queued events to be processed.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if queues are empty, False if timed out
        """
        start_time = time.time()
        
        # Wait until all queues are empty or timeout
        while time.time() - start_time < timeout:
            try:
                high_empty = self.high_priority_queue.empty()
                normal_empty = self.normal_priority_queue.empty()
                low_empty = self.low_priority_queue.empty()
                
                if high_empty and normal_empty and low_empty:
                    # Add a small delay to allow for any in-progress processing
                    await asyncio.sleep(0.1)
                    if (self.high_priority_queue.empty() and
                        self.normal_priority_queue.empty() and
                        self.low_priority_queue.empty()):
                        return True
            except Exception:
                # If we can't check queue status, just wait
                pass
                
            await asyncio.sleep(0.05)
        
        return False  # Timed out
    
    async def start(self):
        """
        Start the event processing thread.
        
        This method starts a dedicated thread for event processing, maintaining
        a clear thread boundary for the event loop used to process events.
        """
        with self._queue_lock:
            # Check if already running
            if self._running and self._processor_thread and self._processor_thread.is_alive():
                logger.debug(f"Event processor thread for {self._id} already running")
                return
            
            # Create stop event for signaling shutdown
            self._stop_event = threading.Event()
            
            # Start processor thread
            self._running = True
            self._thread_executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=1,
                thread_name_prefix=f"event_processor_{self._id}"
            )
            
            # Submit the processor function to run in its own thread
            self._processor_thread = threading.Thread(
                target=self._processor_thread_main,
                name=f"event_processor_{self._id}",
                daemon=True  # Daemon thread will terminate when main thread exits
            )
            self._processor_thread.start()
            
            logger.info(f"Started event processor thread for queue {self._id}")
    
    def _processor_thread_main(self):
        """
        Main function for the processor thread.
        
        This runs in a dedicated thread and maintains its own event loop for
        processing events from the queue.
        """
        try:
            # Set up thread identity
            self._processor_thread_id = threading.get_ident()
            logger.debug(f"Processor thread {self._processor_thread_id} starting for queue {self._id}")
            
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Create async queues for the processor
            self._async_high_queue = asyncio.Queue(maxsize=max(10, self._max_size // 10))
            self._async_normal_queue = asyncio.Queue(maxsize=self._max_size)
            self._async_low_queue = asyncio.Queue(maxsize=self._max_size * 2)
            
            # Run the event processor coroutines in this loop
            logger.debug(f"Starting queue to async bridge for {self._id}")
            bridge_task = loop.create_task(self._queue_to_async_bridge())
            logger.debug(f"Starting event processor for {self._id}")
            processor_task = loop.create_task(self._process_events())
            
            # Wait for stop event while keeping event loop running
            while not self._stop_event.is_set():
                loop.run_until_complete(asyncio.sleep(0.1))
            
            # Cancel tasks
            bridge_task.cancel()
            processor_task.cancel()
            
            # Cleanup
            pending = asyncio.all_tasks(loop)
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
            
            logger.debug(f"Processor thread {self._processor_thread_id} for queue {self._id} stopped")
        except Exception as e:
            logger.error(f"Error in processor thread: {e}", exc_info=True)
    
    async def _queue_to_async_bridge(self):
        """
        Bridge between threading.Queue and asyncio.Queue.
        
        This coroutine runs in the processor thread and continuously pulls events from
        the thread-safe queues and puts them in the asyncio queues for async processing.
        """
        # Create a task for each priority level
        tasks = [
            asyncio.create_task(self._bridge_queue(
                self.high_priority_queue, self._async_high_queue, "high")),
            asyncio.create_task(self._bridge_queue(
                self.normal_priority_queue, self._async_normal_queue, "normal")),
            asyncio.create_task(self._bridge_queue(
                self.low_priority_queue, self._async_low_queue, "low"))
        ]
        
        # Wait for all bridge tasks to complete (should be when stop is called)
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _bridge_queue(self, thread_queue, async_queue, priority):
        """
        Bridge a specific queue from threading to asyncio.
        
        Args:
            thread_queue: Source threading.Queue
            async_queue: Target asyncio.Queue
            priority: Priority level for logging
        """
        logger.debug(f"Starting bridge for {priority} queue")
        while self._running and not self._stop_event.is_set():
            try:
                # Non-blocking check with timeout to allow for shutdown checks
                try:
                    # Using get with a timeout allows for checking stop condition
                    event = thread_queue.get(timeout=0.1)
                    logger.debug(f"Bridging {priority} event to async queue: {event.event_type}")
                    await async_queue.put(event)
                    thread_queue.task_done()
                    logger.debug(f"Bridged {priority} event type: {event.event_type}")
                except queue.Empty:
                    # No events, just wait a bit
                    await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Error in {priority} queue bridge: {e}")
                await asyncio.sleep(0.1)
    
    async def _process_events(self):
        """
        Process events with batching support and priority handling.
        
        This coroutine runs in the processor thread and processes events from
        the asyncio queues, delivering them to subscribers.
        """
        consecutive_errors = 0
        batch = []
        last_event_type = None
        max_batch_size = 5  # Max events to process in a batch
        
        logger.debug(f"Event processor started for queue {self._id} with {len(self._subscribers)} subscribers")
        
        while self._running and not self._stop_event.is_set():
            try:
                # Process high priority queue first - never batched
                try:
                    high_priority_event = await asyncio.wait_for(
                        self._async_high_queue.get(), 
                        timeout=0.1
                    )
                    logger.debug(f"Processing high priority event: {high_priority_event.event_type}")
                    await self._process_single_event(high_priority_event)
                    self._async_high_queue.task_done()
                    consecutive_errors = 0
                    continue  # Continue loop to keep checking high priority first
                except asyncio.TimeoutError:
                    # No high priority events, continue to normal priority
                    logger.debug("No high priority events")
                    
                    # Try to process normal priority events with batching
                    try:
                        if not batch:  # Start a new batch
                            normal_priority_event = await asyncio.wait_for(
                                self._async_normal_queue.get(),
                                timeout=0.1
                            )
                            logger.debug(f"Got first event for batch: {normal_priority_event.event_type}")
                            batch.append(normal_priority_event)
                            last_event_type = normal_priority_event.event_type
                            self._async_normal_queue.task_done()
                        
                        # Try to fill batch with same event type
                        batch_filled = False
                        while len(batch) < max_batch_size and not batch_filled:
                            try:
                                # Non-blocking get
                                normal_priority_event = self._async_normal_queue.get_nowait()
                                logger.debug(f"Adding to batch: {normal_priority_event.event_type}")
                                
                                # Only batch events of the same type
                                if normal_priority_event.event_type == last_event_type:
                                    batch.append(normal_priority_event)
                                    self._async_normal_queue.task_done()
                                else:
                                    # Put it back and stop batching for now
                                    logger.debug(f"Different event type, stopping batch: {normal_priority_event.event_type}")
                                    await self._async_normal_queue.put(normal_priority_event)
                                    batch_filled = True
                            except asyncio.QueueEmpty:
                                logger.debug("Normal queue empty, processing current batch")
                                batch_filled = True
                        
                        # Process the batch
                        if batch:
                            logger.debug(f"Processing batch of {len(batch)} events")
                            await self._process_event_batch(batch)
                            batch = []
                            last_event_type = None
                            consecutive_errors = 0
                    except asyncio.TimeoutError:
                        logger.debug("No normal priority events")
                        # No normal priority events, check low priority
                    pass
                except asyncio.QueueEmpty:
                    # Queue is empty, continue to normal priority
                    pass
                
                # Check if we need to process the current batch
                if batch and (len(batch) >= max_batch_size or 
                            (last_event_type is not None and batch[0].event_type != last_event_type)):
                    await self._process_event_batch(batch)
                    batch = []
                
                # Try to get event from normal priority queue
                try:
                    # Use shorter timeout to balance responsiveness
                    normal_event = await asyncio.wait_for(
                        self._async_normal_queue.get(), 
                        timeout=0.2
                    )
                    consecutive_errors = 0
                    
                    # Start or continue a batch
                    if not batch:
                        batch.append(normal_event)
                        last_event_type = normal_event.event_type
                        logger.debug(f"Started new batch with event type {last_event_type}")
                    elif normal_event.event_type == last_event_type and len(batch) < max_batch_size:
                        batch.append(normal_event)
                        logger.debug(f"Added to batch, now size {len(batch)}")
                    else:
                        # Process the existing batch
                        if batch:
                            logger.debug(f"Processing batch of {len(batch)} events of type {batch[0].event_type}")
                            await self._process_event_batch(batch)
                        # Start a new batch
                        batch = [normal_event]
                        last_event_type = normal_event.event_type
                        logger.debug(f"Started new batch with event type {last_event_type}")
                        
                    self._async_normal_queue.task_done()
                    
                except asyncio.TimeoutError:
                    # Process any pending batch before checking low priority
                    if batch:
                        logger.debug(f"Processing batch of {len(batch)} events of type {batch[0].event_type} after timeout")
                        await self._process_event_batch(batch)
                        batch = []
                    
                    # Only check low priority if normal is empty
                    try:
                        # Use longer timeout for low priority
                        low_event = await asyncio.wait_for(
                            self._async_low_queue.get(), 
                            timeout=0.5
                        )
                        await self._process_single_event(low_event)
                        self._async_low_queue.task_done()
                        consecutive_errors = 0
                    except (asyncio.TimeoutError, asyncio.QueueEmpty):
                        # No events in any queue, sleep briefly
                        await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in event processing: {e}", exc_info=True)
                consecutive_errors += 1
                # Add backoff for repeated errors
                await asyncio.sleep(min(consecutive_errors * 0.1, 5))
        
        # Process any remaining batch when shutting down
        if batch:
            try:
                await self._process_event_batch(batch)
            except Exception as e:
                logger.error(f"Error processing final batch during shutdown: {e}")
    
    async def _process_event_batch(self, batch: List[Event]):
        """
        Process a batch of events with the same event type.
        
        Args:
            batch: List of events to process as a batch
        """
        if not batch:
            return
            
        logger.debug(f"Processing batch of {len(batch)} events")
        
        # For single events, process them individually without batch wrapping
        if len(batch) == 1:
            await self._process_single_event(batch[0])
            return
        
        # All events in the batch should have the same type
        event_type = batch[0].event_type
        
        # Create a batch payload
        batch_items = []
        for event in batch:
            # Add to batch items
            batch_items.append(event.data)
            
        # Create a batch payload
        batch_payload = {
            "batch": True,
            "count": len(batch),
            "items": batch_items,
            "correlation_id": batch[0].correlation_id
        }
        
        # Find subscribers
        with self._queue_lock:
            handlers = set(self._subscribers.get(event_type, set()))
            
        logger.debug(f"Found {len(handlers)} subscribers for batch of {event_type} events")
            
        # Deliver to all subscribers
        for handler in handlers:
            try:
                # Call the handler with the batch payload
                logger.debug(f"Delivering batch to handler {handler}")
                await handler(event_type, batch_payload)
            except Exception as e:
                logger.error(f"Error in batch event handler: {e}", exc_info=True)
    
    async def _process_single_event(self, event):
        """
        Process a single event.
        
        Args:
            event: The event to process
        """
        logger.debug(f"Processing single event: {event.event_type}")
        
        # Get subscribers for this event type - thread-safe copy
        subscribers = []
        with self._queue_lock:
            if event.event_type in self._subscribers:
                subscribers = list(self._subscribers[event.event_type])
        
        if not subscribers:
            logger.debug(f"No subscribers for event type: {event.event_type}")
            return
        
        logger.debug(f"Found {len(subscribers)} subscribers for {event.event_type}")
        
        # Process event for each subscriber with error isolation
        for callback in subscribers:
            # Generate a unique event_id for retry tracking
            event_id = f"{event.event_type}_{id(callback)}_{datetime.now().timestamp()}"
            logger.debug(f"Delivering event {event_id} to callback {callback}")
            try:
                await self._deliver_event(event, callback, event_id)
                logger.debug(f"Event {event_id} delivered successfully")
            except Exception as e:
                logger.error(f"Error in event delivery for {event.event_type}: {e}")
                # Continue to next subscriber
    
    async def stop(self):
        """
        Stop event processing safely.
        
        This method signals the processor thread to stop and waits for it to
        complete, with a timeout to avoid hanging.
        """
        with self._queue_lock:
            if not self._running:
                logger.debug(f"Event queue {self._id} already stopped")
                return
            
            logger.info(f"Stopping event queue {self._id}")
            
            # Signal stop
            self._running = False
            if self._stop_event:
                self._stop_event.set()
        
        # Wait for thread to finish with timeout
        if self._processor_thread and self._processor_thread.is_alive():
            logger.debug(f"Waiting for processor thread to stop for queue {self._id}")
            self._processor_thread.join(timeout=5.0)
            
            if self._processor_thread.is_alive():
                logger.warning(f"Processor thread did not stop cleanly for queue {self._id}")
        
        # Shutdown thread executor
        if self._thread_executor:
            self._thread_executor.shutdown(wait=False)
        
        # Clear resources
        with self._queue_lock:
            subscribers_count = sum(len(subs) for subs in self._subscribers.values())
            logger.info(f"Clearing {subscribers_count} subscribers from queue {self._id}")
            self._subscribers.clear()
            
            # Clear processing retries to prevent memory leaks
            retry_count = len(self._processing_retries)
            if retry_count > 0:
                logger.debug(f"Clearing {retry_count} processing retries from queue {self._id}")
            self._processing_retries.clear()
        
        logger.info(f"Event queue {self._id} stopped")
    
    async def subscribe(self, 
                      event_type: str, 
                      callback: Callable[[str, Dict[str, Any]], Awaitable[None]]) -> None:
        """
        Add subscriber for an event type.
        
        Args:
            event_type: The event type to subscribe to
            callback: The callback function to call when the event occurs
        """
        # Input validation
        if event_type is None or callback is None or not callable(callback):
            logger.error(f"Invalid subscription parameters: event_type={event_type}, callback={callback}")
            return
        
        # Convert enum to string if needed
        if hasattr(event_type, 'value'):
            event_type = event_type.value
            
        # Thread-safe subscriber registration
        with self._queue_lock:
            # Create a set for this event type if it doesn't exist
            if event_type not in self._subscribers:
                self._subscribers[event_type] = set()
            
            # Add subscriber
            self._subscribers[event_type].add(callback)
        
        # Check if callback is a coroutine function for logging
        is_coroutine = asyncio.iscoroutinefunction(callback)
        logger.debug(f"Added subscriber for {event_type} events (coroutine={is_coroutine})")
    
    async def unsubscribe(self, 
                         event_type: str, 
                         callback: Callable[[str, Dict[str, Any]], Awaitable[None]]) -> None:
        """
        Remove a subscriber.
        
        Args:
            event_type: The event type to unsubscribe from
            callback: The callback function to remove
        """
        # Convert enum to string if needed
        if hasattr(event_type, 'value'):
            event_type = event_type.value
            
        # Thread-safe subscriber removal
        with self._queue_lock:
            if event_type in self._subscribers and callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Removed subscriber for {event_type} events")
    
    async def emit_error(self,
                       error,
                       additional_context: Optional[Dict[str, Any]] = None) -> None:
        """
        Emit error event with full context.
        
        Args:
            error: The error to emit
            additional_context: Additional context to include
        """
        event_data = {
            "severity": error.severity.name,
            "resource_id": error.resource_id,
            "operation": error.operation,
            "message": error.message,
            "timestamp": datetime.now().isoformat(),
            "recovery_strategy": error.recovery_strategy,
            "context": {
                "resource_id": error.context.resource_id,
                "operation": error.context.operation,
                "attempt": error.context.attempt,
                "recovery_attempts": error.context.recovery_attempts,
                "details": error.context.details,
                **(additional_context or {})
            }
        }
        
        await self.emit(
            ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
            event_data
        )
    
    async def _deliver_event(self, event: Event, callback, event_id: str) -> None:
        """
        Deliver event to a subscriber with retry handling.
        
        Args:
            event: The event to deliver
            callback: The callback function
            event_id: Unique ID for tracking this delivery
        """
        # Attempt delivery with retries
        for attempt in range(self._max_retries + 1):  # 0, 1, 2, 3 (4 total attempts)
            try:
                # Direct async call to the callback
                if asyncio.iscoroutinefunction(callback):
                    logger.debug(f"Calling async callback {callback} with {event.event_type}")
                    await callback(event.event_type, event.data)
                    logger.debug(f"Async callback completed for {event.event_type}")
                else:
                    # If not async, run in executor to avoid blocking
                    logger.debug(f"Calling sync callback {callback} with {event.event_type}")
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None, 
                        lambda: callback(event.event_type, event.data)
                    )
                    logger.debug(f"Sync callback completed for {event.event_type}")
                
                # Success
                logger.debug(f"Event {event_id} delivered successfully")
                return
                
            except Exception as e:
                if attempt < self._max_retries:
                    # Log error and retry
                    logger.warning(f"Error delivering event {event_id}: {e}, retry {attempt+1}/{self._max_retries}")
                    
                    # Exponential backoff with jitter
                    base_delay = self._retry_delay * (2 ** attempt)
                    jitter = random.uniform(0, base_delay * 0.1)
                    await asyncio.sleep(base_delay + jitter)
                else:
                    # Max retries reached
                    logger.error(f"Event {event_id} failed after {self._max_retries} retries: {e}")
        
        # Max retries reached, clear retry counter
        with self._queue_lock:
            if event_id in self._processing_retries:
                del self._processing_retries[event_id]
        
        logger.error(f"Max retries reached for event {event_id}")
    
    def get_queue_size(self) -> Dict[str, int]:
        """
        Get current queue sizes for all priority levels.
        
        Returns:
            Dict[str, int]: Dictionary of queue sizes by priority
        """
        try:
            return {
                "high": self.high_priority_queue.qsize(),
                "normal": self.normal_priority_queue.qsize(),
                "low": self.low_priority_queue.qsize(),
                "total": (self.high_priority_queue.qsize() + 
                          self.normal_priority_queue.qsize() + 
                          self.low_priority_queue.qsize())
            }
        except NotImplementedError:
            # Some queue implementations don't support qsize
            return {"high": -1, "normal": -1, "low": -1, "total": -1}
    
    def get_subscriber_count(self, event_type: str = None) -> Union[int, Dict[str, int]]:
        """
        Get number of subscribers.
        
        Args:
            event_type: Optional specific event type to count subscribers for
            
        Returns:
            Union[int, Dict[str, int]]: Subscriber count for specified event type
                                        or dictionary of counts by event type
        """
        with self._queue_lock:
            if event_type:
                # Convert enum to string if needed
                if hasattr(event_type, 'value'):
                    event_type = event_type.value
                return len(self._subscribers.get(event_type, set()))
            else:
                # Return counts for all event types
                return {et: len(subs) for et, subs in self._subscribers.items()}
    
    async def get_recent_events(self, 
                              event_type: Optional[str] = None,
                              limit: int = 100) -> List[Event]:
        """
        Get recent events, optionally filtered by type.
        
        Args:
            event_type: Optional event type to filter by
            limit: Maximum number of events to return
            
        Returns:
            List[Event]: List of recent events
        """
        with self._queue_lock:
            events = list(self._event_history)
            
        if event_type:
            # Convert enum to string if needed
            if hasattr(event_type, 'value'):
                event_type = event_type.value
            events = [e for e in events if e.event_type == event_type]
            
        return events[-limit:]

# Import needed for backwards compatibility 
import queue