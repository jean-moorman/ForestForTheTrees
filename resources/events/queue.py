"""
Core event queue implementation with priority and backpressure support.

This module provides the EventQueue class which serves as the central hub for
event-based communication throughout the FFTT system, with support for event
prioritization, batching, and reliable delivery.
"""
import asyncio
import logging
import random
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Set, Optional, Callable, Awaitable, Tuple

from .types import Event, ResourceEventTypes
from .loop_management import EventLoopManager
from .backpressure import EventBackpressureManager
from .utils import wait_with_backoff, with_timeout

logger = logging.getLogger(__name__)

class EventQueue:
    """Async event queue with persistence, reliability and priority"""
    def __init__(self, max_size: int = 1000, queue_id: Optional[str] = None):
        self._max_size = max_size
        self._queue = None  # Legacy queue - kept for backward compatibility
        self._high_priority_queue = None  # Lazy initialization
        self._normal_priority_queue = None  # Lazy initialization
        self._low_priority_queue = None  # Lazy initialization
        self._queue_lock = threading.RLock()  # Add a lock for queue operations
        self._subscribers: Dict[str, Set[Tuple[Callable[[str, Dict[str, Any]], Awaitable[None]], Optional[asyncio.AbstractEventLoop], Optional[int]]]] = {}
        self._event_history: List[Event] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._processing_retries: Dict[str, int] = {}
        self._max_retries = 3
        self._retry_delay = 1.0  # seconds
        self._creation_loop_id = None  # Store the ID of the loop that creates the queue
        self._loop_thread_id = None  # Store the thread ID where the queue was created
        self._id = queue_id or f"event_queue_{id(self)}"
        
        # Initialize backpressure manager
        self._backpressure_manager = EventBackpressureManager()
    
        # Use centralized event loop manager
        try:
            current_loop = EventLoopManager.get_event_loop()
            self._creation_loop_id = id(current_loop)
            self._loop_thread_id = threading.get_ident()
            
            # Register with event loop manager for cleanup
            EventLoopManager.register_resource(self._id, self)
            
            logger.debug(f"EventQueue {self._id} created in loop {self._creation_loop_id} on thread {self._loop_thread_id}")
        except Exception as e:
            logger.warning(f"Error during EventQueue initialization: {str(e)}")
            self._creation_loop_id = None
            self._loop_thread_id = threading.get_ident()

    @property
    def queue(self):
        """Legacy queue property - redirects to normal_priority_queue"""
        return self.normal_priority_queue
        
    @property
    def high_priority_queue(self):
        """Lazy initialization of high priority queue"""
        if self._high_priority_queue is None:
            try:
                # Use the centralized event loop manager
                current_loop = EventLoopManager.get_event_loop()
                # High priority queue is smaller to ensure faster processing
                self._high_priority_queue = asyncio.Queue(maxsize=max(10, self._max_size // 10))
                if not hasattr(self, '_creation_loop_id') or self._creation_loop_id is None:
                    self._creation_loop_id = id(current_loop)
                    self._loop_thread_id = threading.get_ident()
                logger.debug(f"High priority queue initialized in loop {self._creation_loop_id}")
            except Exception as e:
                logger.error(f"Cannot create high priority queue: {str(e)}")
                raise RuntimeError(f"Cannot create high priority queue: {str(e)}")
        return self._high_priority_queue
        
    @property
    def normal_priority_queue(self):
        """Lazy initialization of normal priority queue"""
        if self._normal_priority_queue is None:
            try:
                # Use the centralized event loop manager
                current_loop = EventLoopManager.get_event_loop()
                self._normal_priority_queue = asyncio.Queue(maxsize=self._max_size)
                if not hasattr(self, '_creation_loop_id') or self._creation_loop_id is None:
                    self._creation_loop_id = id(current_loop)
                    self._loop_thread_id = threading.get_ident()
                # For backward compatibility
                self._queue = self._normal_priority_queue
                logger.debug(f"Normal priority queue initialized in loop {self._creation_loop_id}")
            except Exception as e:
                logger.error(f"Cannot create normal priority queue: {str(e)}")
                raise RuntimeError(f"Cannot create normal priority queue: {str(e)}")
        return self._normal_priority_queue
        
    @property
    def low_priority_queue(self):
        """Lazy initialization of low priority queue"""
        if self._low_priority_queue is None:
            try:
                # Use the centralized event loop manager
                current_loop = EventLoopManager.get_event_loop()
                # Low priority queue can be larger
                self._low_priority_queue = asyncio.Queue(maxsize=self._max_size * 2)
                if not hasattr(self, '_creation_loop_id') or self._creation_loop_id is None:
                    self._creation_loop_id = id(current_loop)
                    self._loop_thread_id = threading.get_ident()
                logger.debug(f"Low priority queue initialized in loop {self._creation_loop_id}")
            except Exception as e:
                logger.error(f"Cannot create low priority queue: {str(e)}")
                raise RuntimeError(f"Cannot create low priority queue: {str(e)}")
        return self._low_priority_queue

    async def _ensure_correct_loop(self):
        """Ensure we're running in the correct event loop or handle mismatch"""
        if self._queue is None:
            return  # Queue not created yet, no issue
            
        try:
            # Use the centralized event loop manager
            current_loop = EventLoopManager.get_event_loop()
            current_thread = threading.get_ident()
            
            # Check if we're in the correct loop
            if current_thread != self._loop_thread_id or id(current_loop) != self._creation_loop_id:
                logger.warning(f"Event queue {self._id} access from different context. "
                               f"Created in loop {self._creation_loop_id} on thread {self._loop_thread_id}, "
                               f"accessed from loop {id(current_loop)} on thread {current_thread}")
                
                # Use EventLoopManager to validate
                is_valid = await EventLoopManager.validate_loop_for_resource(self._id)
                if not is_valid:
                    logger.error(f"Event queue {self._id} used in incorrect loop context")
                    
                    # Here we could implement safe event transfer, but for now just warn
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error during loop validation: {str(e)}")
            return False
    
    async def emit(self, event_type: str, data: Dict[str, Any], 
               correlation_id: Optional[str] = None, 
               priority: str = "normal") -> bool:
        """Emit event with back-pressure support, priority, and payload validation
        
        Args:
            event_type: The type of event to emit
            data: The event data
            correlation_id: Optional correlation ID for tracking related events
            priority: Event priority - "high", "normal", or "low"
            
        Returns:
            bool: True if event was queued, False if rejected due to back-pressure
        """
        # Convert enum if needed
        event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
        
        # Validate payload schema if needed
        try:
            import inspect
            from resources.schemas import (
                ValidationEventPayload, PropagationEventPayload, 
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
                
                # Phase 0 Water Agent events
                ResourceEventTypes.WATER_PROPAGATION_COMPLETE.value: PropagationEventPayload,
                ResourceEventTypes.WATER_PROPAGATION_STARTED.value: PropagationEventPayload,
                ResourceEventTypes.WATER_PROPAGATION_REJECTED.value: PropagationEventPayload,
                ResourceEventTypes.WATER_PROPAGATION_FAILED.value: PropagationEventPayload,
                
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
                                from datetime import datetime
                                data[field_name] = datetime.now().isoformat()
                            elif field_name == 'event_id':
                                import uuid
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
        event_id = str(uuid.uuid4())
        event = Event(
            event_type=event_type_str,
            data=data,
            correlation_id=correlation_id,
            priority=priority,
            # Add an event_id field if it doesn't exist already in Event class
            metadata={"event_id": event_id}
        )
        
        # Use EventLoopManager to ensure we're in the right loop context
        try:
            # Submit the actual emission to the creation loop of this queue
            return await EventLoopManager.submit_to_resource_loop(self._id, self._emit_internal(event))
        except Exception as e:
            logger.error(f"Failed to emit event {event_type_str}: {e}")
            # In case of critical events, try direct emission
            if event_type_str in [
                ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
                ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                ResourceEventTypes.SYSTEM_ALERT.value
            ]:
                logger.warning(f"Critical event {event_type_str}, attempting direct emission")
                return await self._emit_internal(event)
            return False
            
    async def emit_with_docs(
        self, 
        event_type: str, 
        data: Dict[str, Any], 
        correlation_id: Optional[str] = None,
        priority: str = "normal",
        publisher_component: str = None
    ) -> bool:
        """Emit event with documentation support.
        
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
    
    async def _emit_internal(self, event: Event) -> bool:
        """Internal implementation of emit that runs in creation loop with enhanced back-pressure"""
        # Update backpressure metrics
        try:
            # Check queue saturation
            high_size = self.high_priority_queue.qsize()
            high_capacity = self.high_priority_queue.maxsize
            
            normal_size = self.normal_priority_queue.qsize()
            normal_capacity = self.normal_priority_queue.maxsize
            
            low_size = self.low_priority_queue.qsize()
            low_capacity = self.low_priority_queue.maxsize
            
            # Update backpressure manager
            self._backpressure_manager.update_saturation(
                high_size, high_capacity,
                normal_size, normal_capacity,
                low_size, low_capacity
            )
        except (NotImplementedError, Exception) as e:
            # Some queue implementations don't support qsize()
            logger.debug(f"Error checking queue saturation: {e}")

        # Manage history with size limit
        self._event_history.append(event)
        if len(self._event_history) > 10000:
            self._event_history = self._event_history[-10000:]
            
        # Apply rate limiting
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
        
        # Select queue based on priority
        if event.priority == "high":
            target_queue = self.high_priority_queue
        elif event.priority == "low":
            target_queue = self.low_priority_queue
        else:
            target_queue = self.normal_priority_queue
        
        # Put in queue - we should already be in the correct loop context
        try:
            await target_queue.put(event)
            logger.debug(f"Emitted {event.priority} priority event {event.event_type} to queue {self._id}")
            return True
        except Exception as e:
            logger.error(f"Failed to emit event {event.event_type}: {e}")
            return False

    def get_nowait(self):
        """Non-blocking get from the event queue with event loop safety."""
        try:
            # Check if we're in the right loop using EventLoopManager
            try:
                current_loop = EventLoopManager.get_event_loop()
                current_thread = threading.get_ident()
                
                if self._queue is not None and (id(current_loop) != self._creation_loop_id or 
                                            current_thread != self._loop_thread_id):
                    logger.warning(f"Queue.get_nowait for {self._id} from different context. "
                                f"Created in loop {self._creation_loop_id} on thread {self._loop_thread_id}, "
                                f"accessed from loop {id(current_loop)} on thread {current_thread}")
                    
                    # In a non-async context, we can't await validate_loop_for_resource
                    # Instead just log the warning and continue with best effort
            except Exception:
                # This could happen if called from a thread without an event loop
                logger.warning(f"Error checking event loop when calling get_nowait for {self._id}")
            
            # Try to get from the queue
            return self.queue.get_nowait()
            
        except asyncio.QueueEmpty:
            # Propagate QueueEmpty for normal handling
            raise
        except RuntimeError as e:
            if "different event loop" in str(e):
                logger.error(f"Event loop mismatch in get_nowait for {self._id}: {e}")
                
                # Try to recreate the queue in the current context as a last resort
                try:
                    current_loop = EventLoopManager.get_event_loop()
                    self._queue = asyncio.Queue(maxsize=self._max_size)
                    self._creation_loop_id = id(current_loop)
                    self._loop_thread_id = threading.get_ident()
                    logger.warning(f"Recreated queue for {self._id} in current loop context")
                    
                    # Try get_nowait on the new queue, but it's likely empty
                    return self._queue.get_nowait()
                except (asyncio.QueueEmpty, Exception):
                    # Simulate empty queue if recreation fails or new queue is empty
                    raise asyncio.QueueEmpty()
            else:
                # For other RuntimeErrors, log and re-raise
                logger.error(f"RuntimeError in get_nowait for {self._id}: {e}")
                raise

    async def wait_for_processing(self, timeout=5.0):
        """Wait for all currently queued events to be processed."""
        if self._queue is None:
            return True  # Queue not initialized, nothing to wait for
            
        start_time = time.time()
        
        # Wait until the queue is empty or timeout
        while time.time() - start_time < timeout:
            try:
                if self._queue.qsize() == 0:
                    # Add a small delay to allow for any in-progress processing
                    await asyncio.sleep(0.1)
                    if self._queue.qsize() == 0:  # Double check after delay
                        return True
            except NotImplementedError:
                # Some queue implementations don't support qsize()
                await asyncio.sleep(0.1)
            
            await asyncio.sleep(0.05)
        
        return False  # Timed out

    async def _process_events(self):
        """Process events with batching support and priority handling"""
        consecutive_errors = 0
        batch = []
        last_event_type = None
        max_batch_size = 5  # Max events to process in a batch (reduced for testing)
        
        while self._running:
            try:
                # Process high priority queue first - these are never batched for immediate processing
                try:
                    # Use shorter timeout for high priority check to avoid blocking
                    high_priority_event = await asyncio.wait_for(
                        self.high_priority_queue.get(), 
                        timeout=0.1
                    )
                    # Process high priority event immediately
                    await self._process_single_event(high_priority_event)
                    self.high_priority_queue.task_done()
                    consecutive_errors = 0
                    continue  # Continue loop to keep checking high priority first
                except asyncio.TimeoutError:
                    # No high priority events, continue to normal priority
                    pass
                except asyncio.QueueEmpty:
                    # Queue is empty, continue to normal priority
                    pass
                except RuntimeError as e:
                    # Handle loop mismatch for high priority queue
                    if "different event loop" in str(e):
                        with self._queue_lock:
                            self._high_priority_queue = asyncio.Queue(maxsize=max(100, self._max_size // 10))
                        consecutive_errors += 1
                        await asyncio.sleep(min(consecutive_errors * 0.1, 5))
                        continue
                    else:
                        raise
                
                # Check if we need to process the current batch
                if batch and (len(batch) >= max_batch_size or 
                             (last_event_type is not None and batch[0].event_type != last_event_type)):
                    await self._process_event_batch(batch)
                    batch = []
                
                # Try to get event from normal priority queue
                try:
                    # Use shorter timeout to balance responsiveness
                    normal_event = await asyncio.wait_for(
                        self.normal_priority_queue.get(), 
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
                        
                    self.normal_priority_queue.task_done()
                    
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
                            self.low_priority_queue.get(), 
                            timeout=0.5
                        )
                        await self._process_single_event(low_event)
                        self.low_priority_queue.task_done()
                        consecutive_errors = 0
                    except (asyncio.TimeoutError, asyncio.QueueEmpty):
                        # No events in any queue, sleep briefly
                        await asyncio.sleep(0.1)
                        
                except RuntimeError as e:
                    # Handle loop mismatch for normal priority queue
                    if "different event loop" in str(e):
                        with self._queue_lock:
                            self._normal_priority_queue = asyncio.Queue(maxsize=self._max_size)
                            # Update legacy queue reference
                            self._queue = self._normal_priority_queue
                        consecutive_errors += 1
                        await asyncio.sleep(min(consecutive_errors * 0.1, 5))
                    else:
                        raise
                
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
        """Process a batch of events with the same event type"""
        if not batch:
            logger.debug("Attempted to process empty batch, skipping")
            return
            
        event_type = batch[0].event_type
        logger.debug(f"Processing batch of {len(batch)} events of type {event_type}")
        
        # Get subscribers for this event type
        subscribers = self._subscribers.get(event_type, set())
        
        if not subscribers:
            logger.debug(f"No subscribers for event type: {event_type}")
            return
            
        logger.debug(f"Found {len(subscribers)} subscribers for event type {event_type}")
            
        # Group events for batch processing
        batched_data = []
        for event in batch:
            batched_data.append(event.data)
            
        # Create a single batched event, preserving correlation ID
        correlation_id = batch[0].correlation_id if batch and hasattr(batch[0], 'correlation_id') and batch[0].correlation_id else None
        
        # Create a direct data dictionary instead of Event object for simpler testing
        event_data = {
            "batch": True,
            "count": len(batch),
            "items": batched_data,
            "correlation_id": correlation_id  # Add correlation ID to batch data too
        }
        
        # Create the event with simpler structure
        batched_event = Event(
            event_type=event_type,
            data=event_data,
            correlation_id=correlation_id  # Set correlation ID on Event object
        )
        
        # Process batch for each subscriber
        for subscriber_entry in subscribers:
            callback, loop_id, thread_id = subscriber_entry
            # Generate a unique event_id for retry tracking
            event_id = f"{event_type}_batch_{id(callback)}_{datetime.now().timestamp()}"
            try:
                # Only pass the required arguments to _deliver_event
                await self._deliver_event(batched_event, callback, event_id)
            except Exception as e:
                logger.error(f"Error in batch event delivery for {event_type}: {e}")
                # Continue to next subscriber

    async def _process_single_event(self, event):
        """Process a single event with better error isolation"""
        # Get subscribers for this event type
        subscribers = self._subscribers.get(event.event_type, set())
        
        if not subscribers:
            logger.debug(f"No subscribers for event type: {event.event_type}")
            return
        
        # Process event for each subscriber
        for subscriber_entry in subscribers:
            callback, loop_id, thread_id = subscriber_entry
            # Generate a unique event_id for retry tracking
            event_id = f"{event.event_type}_{id(callback)}_{datetime.now().timestamp()}"
            try:
                # Only pass the required arguments to _deliver_event
                await self._deliver_event(event, callback, event_id)
            except Exception as e:
                logger.error(f"Error in event delivery for {event.event_type}: {e}")
                # Continue to next subscriber instead of failing completely

    async def start(self):
        """Start event processing safely in the current event loop"""
        # Use EventLoopManager to submit to the creation loop
        await EventLoopManager.submit_to_resource_loop(self._id, self._start_internal())
    
    async def _start_internal(self):
        """Internal implementation for starting the queue in creation loop"""
        logger.info(f"Starting event queue {self._id} in creation loop")
        
        # Force initialization of all priority queues
        # This ensures they're all created before the event processor starts
        self.high_priority_queue  # Initialize high priority queue
        self.normal_priority_queue  # Initialize normal priority queue
        self.low_priority_queue  # Initialize low priority queue
        
        logger.debug(f"All priority queues initialized for {self._id}")
        
        # Check if already running
        if self._running and self._task and not self._task.done():
            logger.info(f"Event processor task for {self._id} already running")
            return
            
        # Create a new task in the current loop
        self._running = True
        self._task = asyncio.create_task(self._process_events())
        logger.info(f"Event processor task created for queue {self._id}")
        
        # Set name on task for better debugging if supported
        if hasattr(self._task, 'set_name'):
            self._task.set_name(f"event_processor_{self._id}")
        
        # Update registration with EventLoopManager to ensure proper resource tracking
        EventLoopManager.register_resource(self._id, self)

    async def stop(self):
        """Stop event processing safely using the creation loop"""
        # Use EventLoopManager to submit to the creation loop
        await EventLoopManager.submit_to_resource_loop(self._id, self._stop_internal())
    
    async def _stop_internal(self):
        """Internal implementation for stopping the queue in creation loop"""
        logger.info(f"Stopping event queue {self._id}")
        
        # Mark as not running to prevent new tasks
        self._running = False
        
        # Try to safely drain the queues with timeout protection
        try:
            total_items = 0
            try:
                total_items += self.high_priority_queue.qsize()
                total_items += self.normal_priority_queue.qsize()
                total_items += self.low_priority_queue.qsize()
            except NotImplementedError:
                # Some queue implementations don't support qsize
                pass
                
            if total_items > 0:
                logger.info(f"Waiting for {total_items} queued events to complete in queue {self._id}")
                
                # Use shorter timeout for faster shutdown
                try:
                    await asyncio.wait_for(self._wait_for_empty_queues(), timeout=3.0)
                    logger.info(f"Successfully drained queue {self._id}")
                except asyncio.TimeoutError:
                    logger.warning(f"Timed out waiting for queue {self._id} to drain")
            else:
                logger.info(f"Queues for {self._id} are already empty")
        except Exception as e:
            logger.warning(f"Error draining queue {self._id}: {e}")
        
        # Cancel the processor task
        if self._task and not self._task.done():
            try:
                logger.info(f"Cancelling event processor task for queue {self._id}")
                self._task.cancel()
                
                # Wait with timeout for the task to be cancelled
                try:
                    await asyncio.wait_for(asyncio.shield(self._task), timeout=2.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass
            except Exception as e:
                logger.error(f"Error cancelling event processor task: {e}")
        
        # Clear resources
        subscribers_count = sum(len(subs) for subs in self._subscribers.values())
        logger.info(f"Clearing {subscribers_count} subscribers from queue {self._id}")
        self._subscribers.clear()
        
        # Clear processing retries to prevent memory leaks
        retry_count = len(self._processing_retries)
        if retry_count > 0:
            logger.info(f"Clearing {retry_count} processing retries from queue {self._id}")
        self._processing_retries.clear()
        
        # Unregister from EventLoopManager
        EventLoopManager.unregister_resource(self._id)
        
        # Remove task reference
        self._task = None
        
        logger.info(f"Event queue {self._id} stopped successfully")
    
    async def _wait_for_empty_queues(self):
        """Wait for all queues to be empty"""
        while self._running:
            try:
                high_empty = self.high_priority_queue.empty()
                normal_empty = self.normal_priority_queue.empty()
                low_empty = self.low_priority_queue.empty()
                
                if high_empty and normal_empty and low_empty:
                    await asyncio.sleep(0.1)  # Brief pause to allow any in-progress processing
                    
                    # Double-check all are still empty
                    if (self.high_priority_queue.empty() and 
                        self.normal_priority_queue.empty() and 
                        self.low_priority_queue.empty()):
                        return True
                        
                await asyncio.sleep(0.1)
            except Exception:
                # If we can't check queue status, assume not empty
                await asyncio.sleep(0.1)

    async def subscribe(self, 
                        event_type: str, 
                        callback: Callable[[str, Dict[str, Any]], Awaitable[None]]) -> None:
        """Add subscriber for an event type with loop context tracking
        
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
            
        # Use EventLoopManager to submit to the queue's creation loop
        await EventLoopManager.submit_to_resource_loop(self._id, self._subscribe_internal(event_type, callback))
    
    async def _subscribe_internal(self, event_type: str, callback: Callable):
        """Internal implementation of subscribe that runs in creation loop"""
        # Get current thread and loop context for tracking
        thread_id = threading.get_ident()
        
        try:
            loop = asyncio.get_running_loop()
            loop_id = id(loop)
        except RuntimeError:
            logger.warning(f"No event loop when subscribing to {event_type}")
            loop_id = None
        
        # Create a set for this event type if it doesn't exist
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        
        # Add subscriber with context
        self._subscribers[event_type].add((callback, loop_id, thread_id))
        
        # Check if callback is a coroutine function for logging
        is_coroutine = asyncio.iscoroutinefunction(callback)
        logger.debug(f"Added subscriber for {event_type} events (coroutine={is_coroutine}, thread={thread_id}, loop={loop_id})")

    async def unsubscribe(self, 
                          event_type: str, 
                          callback: Callable[[str, Dict[str, Any]], Awaitable[None]]) -> None:
        """Remove a subscriber"""
        # Convert enum to string if needed
        if hasattr(event_type, 'value'):
            event_type = event_type.value
            
        # Use EventLoopManager to submit to the queue's creation loop
        await EventLoopManager.submit_to_resource_loop(self._id, self._unsubscribe_internal(event_type, callback))
    
    async def _unsubscribe_internal(self, event_type: str, callback: Callable):
        """Internal implementation of unsubscribe that runs in creation loop"""
        if event_type in self._subscribers:
            # Find the subscriber entry with matching callback
            to_remove = None
            for entry in self._subscribers[event_type]:
                subscriber_callback, _, _ = entry
                if subscriber_callback == callback:
                    to_remove = entry
                    break
            
            if to_remove:
                self._subscribers[event_type].discard(to_remove)
                logger.debug(f"Removed subscriber for {event_type} events")
    
    async def emit_error(self,
                        error,
                        additional_context: Optional[Dict[str, Any]] = None) -> None:
        """Emit error event with full context"""
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
        """Deliver event with proper loop context and retry handling"""
        # Initialize retry counter if needed
        if event_id not in self._processing_retries:
            self._processing_retries[event_id] = 0
        
        retry_count = self._processing_retries[event_id]
        max_retries = self._max_retries
        
        # Find the subscriber's loop and thread context
        subscriber_loop_id = None
        subscriber_thread_id = None
        
        # Extract loop and thread info from subscriber entry
        for event_type, subscribers in self._subscribers.items():
            for subscriber_entry in subscribers:
                sub_callback, sub_loop_id, sub_thread_id = subscriber_entry
                if sub_callback == callback:
                    subscriber_loop_id = sub_loop_id
                    subscriber_thread_id = sub_thread_id
                    break
            if subscriber_loop_id is not None:
                break
        
        # Attempt delivery with proper context
        while retry_count <= max_retries:
            try:
                # If we have subscriber loop context, use it for delivery
                if subscriber_loop_id is not None and subscriber_thread_id is not None:
                    # Check if any matching loop exists in registry
                    target_loop = None
                    for loop_info in EventLoopManager._loop_storage.list_all_loops():
                        loop, thread_id = loop_info
                        if id(loop) == subscriber_loop_id:
                            target_loop = loop
                            break
                    
                    if target_loop is not None:
                        # We found the subscriber's loop, submit to it
                        try:
                            # Use run_coroutine_threadsafe for cross-thread delivery
                            future = asyncio.run_coroutine_threadsafe(
                                self._call_subscriber(callback, event),
                                target_loop
                            )
                            # Wait for the result with timeout protection
                            result = await asyncio.wrap_future(future)
                            
                            # Delivery succeeded
                            self._processing_retries.pop(event_id, None)
                            return
                        except concurrent.futures.TimeoutError:
                            # Timeout, increment retry counter and continue
                            retry_count += 1
                            self._processing_retries[event_id] = retry_count
                            logger.warning(f"Timeout delivering event {event_id} to subscriber loop, retry {retry_count}/{max_retries}")
                        except Exception as e:
                            # For specific error types, don't retry
                            retry_count += 1
                            self._processing_retries[event_id] = retry_count
                            logger.warning(f"Error delivering event {event_id}: {e}, retry {retry_count}/{max_retries}")
                    else:
                        # Subscriber loop no longer exists, fall back to direct delivery
                        logger.warning(f"Subscriber loop for event {event_id} no longer exists, using direct delivery")
                        await self._call_subscriber(callback, event)
                        self._processing_retries.pop(event_id, None)
                        return
                else:
                    # No loop context info, use direct delivery
                    await self._call_subscriber(callback, event)
                    self._processing_retries.pop(event_id, None)
                    return
            except Exception as e:
                # Retry for retriable errors
                retry_count += 1
                self._processing_retries[event_id] = retry_count
                
                if retry_count > max_retries:
                    logger.error(f"Max retries reached for event {event_id}")
                    self._processing_retries.pop(event_id, None)
                    raise
                
                # Exponential backoff with jitter
                base_delay = self._retry_delay * (2 ** (retry_count - 1))
                jitter = random.uniform(0, base_delay * 0.1)  # 10% jitter
                delay = base_delay + jitter
                
                logger.warning(f"Retry {retry_count}/{max_retries} for event {event_id} after error: {e}")
                await asyncio.sleep(delay)
    
    async def _call_subscriber(self, callback, event: Event):
        """Simple wrapper to call subscriber with timing metrics"""
        start_time = time.monotonic()
        
        try:
            # Direct call with explicit tuple unpacking prevention
            # Get event_type and data directly from the event
            event_type = event.event_type
            data = event.data
            
            # Call directly with positional args
            if asyncio.iscoroutinefunction(callback):
                await callback(event_type, data)
            else:
                callback(event_type, data)
            
            delivery_time = time.monotonic() - start_time
            
            # Get a unique ID for logging (event_id may not be accessible here)
            event_id = event.metadata.get("event_id", str(id(event)))
            logger.debug(f"Delivered event {event_id} in {delivery_time:.3f}s")
        except Exception as e:
            logger.error(f"Error delivering event to subscriber: {e}")
            # Don't propagate errors from event handling to prevent event loop disruption

    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.queue.qsize()
    
    def get_subscriber_count(self, event_type: str) -> int:
        """Get number of subscribers for an event type"""
        return len(self._subscribers.get(event_type, set()))
    
    async def get_recent_events(self, 
                              event_type: Optional[str] = None,
                              limit: int = 100) -> List[Event]:
        """Get recent events, optionally filtered by type"""
        events = self._event_history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]