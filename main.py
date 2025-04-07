import random
import signal
import struct
import sys
import asyncio
import logging
import threading
import time

import concurrent
import qasync
from typing import Dict, Any, Protocol, Optional, Callable, Awaitable
from datetime import datetime
from functools import partial
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer, QObject, pyqtSignal, pyqtSlot

from display import ForestDisplay
from phase_zero import PhaseZeroOrchestrator
from phase_one import PhaseOneOrchestrator
from phase_two import PhaseTwo
from phase_three import PhaseThreeInterface

class DisplayOrchestratorInterface(Protocol):
    """Interface for display to interact with orchestrators via main.py"""
    async def process_task(self, prompt: str) -> Dict[str, Any]:
        """Process a task request from the UI"""
        pass
        
    async def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get metrics for a specific agent"""
        pass

class MainOrchestrator:
    """Mediator that coordinates between display and phase orchestrators"""
    def __init__(self, phase_zero: PhaseZeroOrchestrator, phase_one: PhaseOneOrchestrator, 
                 phase_two: PhaseTwo, phase_three: PhaseThreeInterface):
        self.phase_zero = phase_zero
        self.phase_one = phase_one
        self.phase_two = phase_two
        self.phase_three = phase_three
        self.logger = logging.getLogger(__name__)
        
    async def process_task(self, prompt: str) -> Dict[str, Any]:
        """Process task across phases"""
        self.logger.info(f"MainOrchestrator processing task: {prompt}")
        try:
            # First delegate to phase_one orchestrator to get structural components
            phase_one_result = await self.phase_one.process_task(prompt)
            self.logger.info(f"Phase One completed with status: {phase_one_result.get('status', 'unknown')}")
            
            # Check if phase one was successful
            if phase_one_result.get("status") != "success":
                return phase_one_result
            
            # Extract structural components and system requirements from phase one result
            structural_components = phase_one_result.get("structural_components", [])
            system_requirements = phase_one_result.get("system_requirements", {})
            
            if not structural_components:
                self.logger.warning("No structural components found in Phase One result")
                return phase_one_result
            
            # Now delegate to phase_two for systematic development
            operation_id = f"phase_two_{int(time.time())}"
            phase_two_result = await self.phase_two.process_structural_components(
                structural_components,
                system_requirements,
                operation_id
            )
            
            self.logger.info(f"Phase Two completed with status: {phase_two_result.get('status', 'unknown')}")
            
            # Combine results from both phases
            combined_result = {
                "status": phase_two_result.get("status", "unknown"),
                "phase_one_outputs": phase_one_result,
                "phase_two_outputs": phase_two_result,
                "message": f"Processed task through Phases One and Two: {phase_two_result.get('status', 'unknown')}"
            }
            
            return combined_result
            
        except Exception as e:
            self.logger.error(f"Error processing task: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "phase_one_outputs": {},
                "phase_two_outputs": {}
            }
        
    async def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get metrics for a specific agent"""
        self.logger.info(f"Getting metrics for agent: {agent_id}")
        try:
            # Determine which phase the agent belongs to
            if agent_id in ['monitoring', 'soil', 'microbial', 'root_system', 
                           'mycelial', 'insect', 'bird', 'pollinator', 'evolution']:
                # Phase Zero agent
                return await self._get_phase_zero_agent_metrics(agent_id)
            elif agent_id in ['garden_planner', 'environmental_analysis', 
                             'root_system_architect', 'tree_placement']:
                # Phase One agent
                return await self._get_phase_one_agent_metrics(agent_id)
            elif agent_id in ['component_test_creation_agent', 'component_implementation_agent',
                             'integration_test_agent', 'system_test_agent', 'deployment_test_agent']:
                # Phase Two agent
                return await self._get_phase_two_agent_metrics(agent_id)
            elif agent_id in ['feature_elaboration_agent', 'feature_test_spec_agent',
                             'feature_integration_agent', 'feature_performance_agent',
                             'natural_selection_agent']:
                # Phase Three agent
                return await self._get_phase_three_agent_metrics(agent_id) 
            else:
                return {"status": "error", "message": f"Unknown agent ID: {agent_id}"}
        except Exception as e:
            self.logger.error(f"Error getting agent metrics: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "agent_id": agent_id}
            
    async def _get_phase_zero_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get metrics for a Phase Zero agent"""
        # Implementation depends on what metrics are available from phase_zero
        # This is a placeholder with example metrics
        return {
            "status": "success",
            "agent_id": agent_id,
            "phase": "zero",
            "metrics": {
                "operations": 10,
                "throughput": 5.2,
                "error_rate": 0.01
            }
        }
        
    async def _get_phase_one_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get metrics for a Phase One agent"""
        # Implementation depends on what metrics are available from phase_one
        # This is a placeholder with example metrics
        return {
            "status": "success",
            "agent_id": agent_id,
            "phase": "one",
            "metrics": {
                "iterations": 5,
                "refinements": 2,
                "complexity_score": 0.8
            }
        }
        
    async def _get_phase_two_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get metrics for a Phase Two agent"""
        # Implementation depends on what metrics are available from phase_two
        # This is a placeholder with example metrics
        return {
            "status": "success",
            "agent_id": agent_id,
            "phase": "two",
            "metrics": {
                "components_processed": 3,
                "tests_created": 12,
                "integration_score": 85
            }
        }
        
    async def _get_phase_three_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get metrics for a Phase Three agent"""
        # Implementation depends on what metrics are available from phase_three
        # This is a placeholder with example metrics
        return {
            "status": "success",
            "agent_id": agent_id,
            "phase": "three",
            "metrics": {
                "features_developed": 7,
                "performance_score": 92,
                "evolution_iterations": 2
            }
        }
from resources.monitoring import SystemMonitor, MemoryMonitor, HealthTracker
from resources.state import StateManager
from resources.managers import AgentContextManager, CacheManager, MetricsManager, ResourceCoordinator, CircuitBreakerRegistry
from resources import ResourceEventTypes, EventQueue  
from system_error_recovery import SystemErrorRecovery, ErrorHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('forest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AsyncHelper(QObject):
    runCoroutineSignal = pyqtSignal(object, object, object)  # Signal to run coroutine in main thread
    errorOccurred = pyqtSignal(str)
    taskCompleted = pyqtSignal(dict)
    
    def __init__(self, app):
        super().__init__()
        self.app = app  # Store reference to ForestApplication
        self.shutdown_requested = False
        self.runCoroutineSignal.connect(self._run_coroutine_in_main_thread)
        self._pending_futures = set()  # Track futures created with run_coroutine_threadsafe

    def run_coroutine(self, coro, callback=None, error_callback=None):
        """Safely run a coroutine from the Qt world with improved error handling"""
        # Check if shutdown is in progress
        if self.shutdown_requested:
            logger.warning("Ignoring coroutine request during shutdown")
            if error_callback:
                error_callback("Operation cancelled: application is shutting down")
            return None
            
        # Emit signal to ensure execution in main thread
        self.runCoroutineSignal.emit(coro, callback, error_callback)

    @pyqtSlot(object, object, object)
    def _run_coroutine_in_main_thread(self, coro, callback, error_callback):
        """Qt slot that safely handles coroutines with better error handling"""
        # Create a proper callback chain for task completion
        def _task_done_callback(task):
            try:
                # Check if task was cancelled
                if task.cancelled():
                    logger.debug("Task was cancelled")
                    self.taskCompleted.emit({"status": "cancelled"})
                    if error_callback:
                        error_callback("Operation cancelled")
                    return
                    
                # Get result, which will raise any exceptions that occurred
                result = task.result()
                
                # Call original callback with the result
                if callback:
                    try:
                        callback(result)
                    except Exception as callback_error:
                        logger.error(f"Error in callback: {callback_error}", exc_info=True)
                        self.errorOccurred.emit(str(callback_error))
                        if error_callback:
                            error_callback(str(callback_error))
                
                # Emit completion signal
                self.taskCompleted.emit({"status": "success", "result": result})
            except asyncio.CancelledError:
                # Task was cancelled, not an error
                logger.debug("Task was cancelled (CancelledError caught)")
                self.taskCompleted.emit({"status": "cancelled"})
                if error_callback:
                    error_callback("Operation cancelled")
            except Exception as e:
                # An error occurred in the task
                logger.error(f"Task error: {e}", exc_info=True)
                self.errorOccurred.emit(str(e))
                self.taskCompleted.emit({"status": "error", "error": str(e)})
                if error_callback:
                    error_callback(str(e))
        
        # Register the task with proper error handling
        try:
            # Create a task only if it's not already one
            if isinstance(coro, asyncio.Task):
                task = coro
            else:
                task = self.app.register_task(coro)
                
            # Add our callback
            task.add_done_callback(_task_done_callback)
            return task
        except Exception as e:
            logger.error(f"Failed to create task: {e}", exc_info=True)
            self.errorOccurred.emit(str(e))
            self.taskCompleted.emit({"status": "error", "error": str(e)})
            if error_callback:
                error_callback(str(e))
            return None
                
    def request_shutdown(self):
        """Mark that shutdown is in progress to prevent new tasks and 
        cancel any pending futures."""
        if self.shutdown_requested:
            # Already shutting down
            return
            
        logger.info("AsyncHelper: Shutdown requested")
        self.shutdown_requested = True
        
        # Cancel any pending futures
        if hasattr(self, '_pending_futures'):
            pending_count = len(self._pending_futures)
            if pending_count > 0:
                logger.info(f"Cancelling {pending_count} pending futures")
                for future in list(self._pending_futures):
                    try:
                        if not future.done() and not future.cancelled():
                            future.cancel()
                    except Exception as e:
                        logger.error(f"Error cancelling future: {e}")
                self._pending_futures.clear()
                
        # Disconnect signals
        try:
            self.runCoroutineSignal.disconnect()
        except Exception:
            # Already disconnected
            pass
        

class ForestApplication:
    def __init__(self):
        # Get existing QApplication or create one
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        
        # Initialize the event queue in constructor instead of deferring
        self._event_queue = EventQueue(queue_id="forest_main_queue")
        
        # Store the thread ID and loop information for diagnostics
        self._init_thread_id = threading.get_ident()
        try:
            current_loop = asyncio.get_event_loop()
            self._init_loop_id = id(current_loop)
        except RuntimeError:
            self._init_loop_id = None
            logger.warning("No event loop available during ForestApplication initialization")
        
        self._tasks = set()  # Central registry for all asyncio tasks
        self._threads = set()

        # Defer other initializations that need the event queue
        self._initialized = False
        
    async def setup_async(self):
        """Initialize components that require the event loop"""
        if self._initialized:
            logger.info("ForestApplication already initialized")
            return
            
        # Use the improved EventLoopManager to manage event loop context
        from resources.events import EventLoopManager
        current_loop = EventLoopManager.get_event_loop()
        current_thread = threading.get_ident()
        logger.info(f"setup_async running in loop {id(current_loop)} on thread {current_thread}")
        
        # The event queue is now initialized in __init__, just start it here
        logger.info("Starting the event queue with improved thread safety")
        # EventQueue.start will use EventLoopManager for correct loop context
        await self._event_queue.start()
        
        # Set up the async helper
        asyncio.get_event_loop()
        self.async_helper = AsyncHelper(self)
        
        # Initialize components with proper event system coordination
        from resources.events import EventLoopManager, ResourceEventTypes
        
        # Create a correlation ID for this initialization sequence
        import uuid
        correlation_id = f"init_sequence_{str(uuid.uuid4())}"
        logger.info(f"Starting manager initialization with correlation ID: {correlation_id}")
        
        try:
            # Initialize centralized resource and circuit breaker coordinators
            logger.info("Initializing resource coordinator and circuit breaker registry")
            self.circuit_registry = CircuitBreakerRegistry(self._event_queue)
            self.resource_coordinator = ResourceCoordinator(self._event_queue)
            
            # Initialize state manager first (fundamental component)
            logger.info("Initializing resource managers")
            self.resource_manager = StateManager(self._event_queue)
            
            # Register resource manager with coordinator as a core component with no dependencies
            self.resource_coordinator.register_manager("state_manager", self.resource_manager)
            
            # Initialize remaining managers with proper dependency tracking
            self.context_manager = AgentContextManager(self._event_queue)
            self.resource_coordinator.register_manager("context_manager", self.context_manager, 
                                                      dependencies=["state_manager"])
            
            self.cache_manager = CacheManager(self._event_queue)
            self.resource_coordinator.register_manager("cache_manager", self.cache_manager, 
                                                     dependencies=["state_manager"])
            
            self.metrics_manager = MetricsManager(self._event_queue)
            self.resource_coordinator.register_manager("metrics_manager", self.metrics_manager, 
                                                     dependencies=["state_manager"])
            
            self.error_handler = ErrorHandler(self._event_queue)
            self.resource_coordinator.register_manager("error_handler", self.error_handler, 
                                                     dependencies=["state_manager"])
                                                     
            self.error_recovery = SystemErrorRecovery(self._event_queue, self.health_tracker)
            self.resource_coordinator.register_manager("error_recovery", self.error_recovery, 
                                                     dependencies=["state_manager", "health_tracker"])

            # Initialize monitoring components with proper registration
            logger.info("Initializing monitoring components")
            self.memory_monitor = MemoryMonitor(self._event_queue)
            self.resource_coordinator.register_manager("memory_monitor", self.memory_monitor, 
                                                     dependencies=[], 
                                                     optional_dependencies=["metrics_manager"])
            
            self.health_tracker = HealthTracker(self._event_queue)
            self.resource_coordinator.register_manager("health_tracker", self.health_tracker, 
                                                     dependencies=[], 
                                                     optional_dependencies=["memory_monitor"])
            
            self.system_monitor = SystemMonitor(self._event_queue, self.memory_monitor, self.health_tracker)
            self.resource_coordinator.register_manager("system_monitor", self.system_monitor, 
                                                     dependencies=["memory_monitor", "health_tracker"])
            
            # Initialize all components in dependency order
            logger.info("Starting coordinated initialization of all components")
            await self.resource_coordinator.initialize_all()
            
            # System monitor is started as part of the initialization
            
            # Emit success event for initialization
            await self._event_queue.emit(
                ResourceEventTypes.SYSTEM_HEALTH_CHANGED,
                {
                    "component": "system",
                    "status": "HEALTHY",
                    "description": "All managers initialized successfully",
                    "correlation_id": correlation_id
                },
                correlation_id=correlation_id
            )
        except Exception as e:
            logger.error(f"Error in manager initialization: {e}")
            # Emit error event for initialization failure
            await self._event_queue.emit(
                ResourceEventTypes.ERROR_OCCURRED,
                {
                    "message": f"Manager initialization failed: {str(e)}",
                    "severity": "ERROR", 
                    "component": "system",
                    "correlation_id": correlation_id
                },
                correlation_id=correlation_id,
                priority="high"
            )
            raise
        # Initialize orchestrators and UI
        try:
            logger.info("Initializing orchestrators")
            self.phase_zero = PhaseZeroOrchestrator(self._event_queue, self.resource_manager, 
                                                   self.context_manager, self.cache_manager, 
                                                   self.metrics_manager, self.error_handler,
                                                   error_recovery=self.error_recovery)
            
            # Initialize phase_three before phase_two since phase_two depends on it
            self.phase_three = PhaseThreeInterface(self._event_queue, self.resource_manager, 
                                                 self.context_manager, self.cache_manager, 
                                                 self.metrics_manager, self.error_handler,
                                                 memory_monitor=self._memory_monitor,
                                                 system_monitor=self._system_monitor)
            
            # Initialize phase_two with reference to phase_three
            self.phase_two = PhaseTwo(self._event_queue, self.resource_manager, 
                                    self.context_manager, self.cache_manager, 
                                    self.metrics_manager, self.error_handler,
                                    self.phase_zero, self.phase_three,
                                    memory_monitor=self._memory_monitor,
                                    system_monitor=self._system_monitor)
            
            self.phase_one = PhaseOneOrchestrator(self._event_queue, self.resource_manager, 
                                                 self.context_manager, self.cache_manager, 
                                                 self.metrics_manager, self.error_handler, 
                                                 error_recovery=self.error_recovery,
                                                 phase_zero=self.phase_zero)
                                                 
            # Create orchestrator mediator to coordinate between display and phases
            self.main_orchestrator = MainOrchestrator(self.phase_zero, self.phase_one, 
                                                    self.phase_two, self.phase_three)
                                                 
            logger.info("Initializing UI")
            self.main_window = ForestDisplay(self._event_queue, self.main_orchestrator, self.system_monitor, 
                                            metrics_manager=self.metrics_manager)
            self.main_window.show()
            
            # Set up UI connections
            logger.info("Setting up UI connections")
            task = self.register_task(self._setup_ui_connections())
        except Exception as e:
            self._handle_fatal_error("Initialization failed", e)
            sys.exit(1)
            
        # Set up event processing timer
        self.event_timer = QTimer()
        self.event_timer.timeout.connect(self.check_events_queue)
        self.event_timer.start(100)
        
        self._initialized = True
        logger.info("ForestApplication async setup complete")

    def _create_task_callback(self, callback=None):
        """
        Creates a callback function to be executed when a task completes.
        
        Args:
            callback: Optional callback function to be executed when the task completes
            
        Returns:
            A callback function that removes the task from the task set and 
            calls the provided callback if one was provided
        """
        def _on_task_complete(task):
            self._tasks.discard(task)
            if callback:
                callback(task)
        return _on_task_complete

    # def register_thread(self, thread):
    #     """Register a QThread for tracking and cleanup."""
    #     # Ensure we have a _threads set
    #     if not hasattr(self, '_threads'):
    #         self._threads = set()
            
    #     self._threads.add(thread)
        
    #     # Use a finished signal to automatically remove threads when they end
    #     thread.finished.connect(lambda thread=thread: self._thread_finished(thread))
        
    #     # Track thread state for debugging
    #     thread.started.connect(lambda: logger.debug(f"Thread started: {thread}"))
        
    #     return thread
    def register_thread(self, thread):
        """Register a QThread for tracking and cleanup."""
        # Ensure we have a _threads set
        if not hasattr(self, '_threads'):
            self._threads = set()
            
        self._threads.add(thread)
        
        # Define a direct handler for each thread to ensure proper capturing
        def on_thread_finished():
            logger.debug(f"Signal handler removing thread from tracking: {thread}")
            self._thread_finished(thread)
        
        # Connect the appropriate signal with a direct handler
        if hasattr(thread, 'finished_signal'):
            thread.finished_signal.connect(on_thread_finished)
        else:
            thread.finished.connect(on_thread_finished)
        
        # Track thread state for debugging
        thread.started.connect(lambda: logger.debug(f"Thread started: {thread}"))
        
        return thread

    def _thread_finished(self, thread):
        """Handle thread completion."""
        logger.debug(f"Thread finished: {thread}")
        self._threads.discard(thread)
        
    def _stop_threads(self):
        """Stop all managed threads safely with improved timeout handling."""
        thread_count = len(self._threads)
        if thread_count == 0:
            logger.debug("No threads to stop")
            return
            
        logger.info(f"Stopping {thread_count} threads...")
        
        # Make a copy to avoid modification during iteration
        threads_to_stop = list(self._threads)
        
        # First ask all threads to quit
        for thread in threads_to_stop:
            if thread.isRunning():
                logger.debug(f"Requesting thread to quit: {thread}")
                thread.quit()
        
        # Then wait for them with a timeout, one by one with progress
        deadline = time.time() + 5.0  # 5 second total timeout
        remaining_threads = list(threads_to_stop)
        
        while remaining_threads and time.time() < deadline:
            for thread in list(remaining_threads):  # Use a copy for iteration
                # Check if the thread has finished
                if not thread.isRunning():
                    logger.debug(f"Thread stopped gracefully: {thread}")
                    remaining_threads.remove(thread)
                    continue
                    
                # Wait a bit more with decreasing time
                remaining_time = max(0.1, deadline - time.time())
                if thread.wait(int(remaining_time * 1000)):  # wait takes milliseconds
                    logger.debug(f"Thread stopped after waiting: {thread}")
                    remaining_threads.remove(thread)
            
            # Small sleep to prevent CPU spiking in this loop
            time.sleep(0.05)
        
        # Forcefully terminate any remaining threads, one by one with logging
        for thread in remaining_threads:
            logger.warning(f"Thread did not quit gracefully, terminating: {thread}")
            thread.terminate()
            # Small wait to allow the termination to take effect
            thread.wait(100)  # Wait 100ms
                
        # Clear the set AFTER all threads are confirmed stopped
        self._threads.clear()
        logger.info("All threads stopped")
        
    async def _setup_ui_connections(self):
        """Set up UI event connections and subscriptions."""
        try:
            # Connect UI signals
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'timeline'):
                self.main_window.timeline.agent_selected.connect(self._handle_agent_selection)
            
            # Set up event subscriptions
            if hasattr(self, 'resource_manager') and hasattr(self.resource_manager, '_event_queue'):
                await self.resource_manager._event_queue.subscribe(
                    ResourceEventTypes.ERROR_OCCURRED,
                    self.main_window._handle_error if hasattr(self, 'main_window') else None
                )
        except Exception as e:
            logger.error(f"Error setting up UI connections: {e}")
            # Don't raise the exception, just log it

    def check_events_queue(self):
        """Process events with better error handling and loop mismatch protection"""
        # Early return if queue is not available or we're shutting down
        if not hasattr(self, '_event_queue') or (hasattr(self, 'async_helper') and self.async_helper.shutdown_requested):
            return
        
        # Process limited batch to prevent blocking UI
        max_events = 10
        events_processed = 0
        
        # Valid high priority events
        high_priority_types = {
            ResourceEventTypes.ERROR_OCCURRED.value if hasattr(ResourceEventTypes.ERROR_OCCURRED, 'value') 
            else str(ResourceEventTypes.ERROR_OCCURRED),
            ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value if hasattr(ResourceEventTypes.SYSTEM_HEALTH_CHANGED, 'value')
            else str(ResourceEventTypes.SYSTEM_HEALTH_CHANGED)
        }
        
        try:
            # Collect events to process, respecting max_events limit
            high_priority_events = []
            normal_events = []
            
            while events_processed < max_events:
                try:
                    # Get events with better error handling for loop mismatches
                    try:
                        event = self._event_queue.get_nowait()
                    except RuntimeError as e:
                        if "different event loop" in str(e):
                            logger.error(f"Event loop mismatch in check_events_queue: {e}")
                            # Log details for debugging
                            try:
                                current_loop = asyncio.get_event_loop()
                                logger.error(f"Current loop: {id(current_loop)}, Thread: {threading.get_ident()}")
                                logger.error(f"Queue created in loop: {self._event_queue._creation_loop_id}, Thread: {self._event_queue._loop_thread_id}")
                            except Exception as loop_err:
                                logger.error(f"Error getting loop details: {loop_err}")
                            break
                        else:
                            raise
                    
                    if not event:
                        break
                    
                    events_processed += 1
                    
                    # Sort by priority
                    if event.event_type in high_priority_types:
                        high_priority_events.append(event)
                    else:
                        normal_events.append(event)
                        
                except asyncio.QueueEmpty:
                    break
                except Exception as e:
                    logger.error(f"Error getting event: {e}")
                    time.sleep(0.01)  # Prevent CPU spin
                    break
            
            # Process high priority events first
            for event in high_priority_events:
                self._process_single_event(event)
                
            # Then process normal events
            for event in normal_events:
                self._process_single_event(event)
                
            # Schedule another check if needed
            if events_processed >= max_events and not (hasattr(self, 'async_helper') and self.async_helper.shutdown_requested):
                QTimer.singleShot(0, self.check_events_queue)
                
        except Exception as e:
            logger.error(f"Event processing error: {e}", exc_info=True)

    def _process_single_event(self, event):
        """Process a single event with error handling for NoneType await issues"""
        try:
            event_type = event.event_type
            data = event.data
            
            # Handle each event in its own try-except to isolate failures
            try:
                if event_type == ResourceEventTypes.METRIC_RECORDED:
                    self._handle_metric_update(event_type, data)
                elif event_type == ResourceEventTypes.ERROR_OCCURRED:
                    self._handle_error(event_type, data)
                else:
                    # Check if event_type is an Enum and get its value/name
                    if isinstance(event_type, ResourceEventTypes):
                        # Use the enum value as the string identifier
                        handler_name = f"_handle_{event_type.value.lower()}"
                    else:
                        # Fallback if it's already a string
                        handler_name = f"_handle_{event_type.lower()}"

                    # Look for a dedicated handler method
                    handler = getattr(self, handler_name, None)
                    
                    # Check if handler exists and is callable
                    if handler and callable(handler):
                        # Check if handler is a coroutine function that needs to be awaited
                        if asyncio.iscoroutinefunction(handler):
                            # For coroutine functions, we need to schedule them differently
                            logger.debug(f"Scheduling coroutine handler for event {event_type}")
                            self.async_helper.run_coroutine(
                                handler(event_type, data),
                                lambda result: logger.debug(f"Event handler for {event_type} completed"),
                                lambda error: logger.error(f"Error in event handler for {event_type}: {error}")
                            )
                        else:
                            # For regular functions, just call them directly
                            handler(event_type, data)
                    else:
                        # Fallback for unhandled event types
                        logger.debug(f"Unhandled event type: {event_type} (no handler found)")
            except AttributeError as attr_error:
                if "can't be used in 'await'" in str(attr_error):
                    logger.error(f"NoneType await error in handler for {event_type}: {attr_error}")
                    # This is specifically handling the NoneType await expression error
                    logger.error(f"Event handler for {event_type} may be returning None instead of a coroutine")
                else:
                    # Other attribute errors
                    logger.error(f"Attribute error handling event {event_type}: {attr_error}", 
                            exc_info=True)
            except Exception as handler_error:
                # Log but continue processing other events
                logger.error(f"Error handling event {event_type}: {handler_error}", 
                        exc_info=True)
        except Exception as e:
            logger.error(f"Event processing error: {e}", exc_info=True)

    def _cleanup_components(self):
        """Clean up application components in a safe manner.
        Called during application shutdown."""
        logger.info("Cleaning up application components")
        
        try:
            # Clean up memory monitor
            if hasattr(self, 'memory_monitor'):
                try:
                    logger.debug("Cleaning up memory monitor")
                    # Call any cleanup methods if they exist
                    if hasattr(self.memory_monitor, 'shutdown') and callable(self.memory_monitor.shutdown):
                        self.memory_monitor.shutdown()
                except Exception as e:
                    logger.error(f"Error cleaning up memory monitor: {e}")
            
            # Clean up system monitor
            if hasattr(self, 'system_monitor'):
                try:
                    logger.debug("Cleaning up system monitor")
                    if hasattr(self.system_monitor, 'shutdown') and callable(self.system_monitor.shutdown):
                        self.system_monitor.shutdown()
                except Exception as e:
                    logger.error(f"Error cleaning up system monitor: {e}")
            
            # Clean up health tracker
            if hasattr(self, 'health_tracker'):
                try:
                    logger.debug("Cleaning up health tracker")
                    if hasattr(self.health_tracker, 'shutdown') and callable(self.health_tracker.shutdown):
                        self.health_tracker.shutdown()
                except Exception as e:
                    logger.error(f"Error cleaning up health tracker: {e}")
            
            # Clean up phase_zero
            if hasattr(self, 'phase_zero'):
                try:
                    logger.debug("Cleaning up phase zero")
                    if hasattr(self.phase_zero, 'shutdown') and callable(self.phase_zero.shutdown):
                        self.phase_zero.shutdown()
                except Exception as e:
                    logger.error(f"Error cleaning up phase zero: {e}")
            
            # Clean up phase_one
            if hasattr(self, 'phase_one'):
                try:
                    logger.debug("Cleaning up phase one")
                    if hasattr(self.phase_one, 'shutdown') and callable(self.phase_one.shutdown):
                        self.phase_one.shutdown()
                except Exception as e:
                    logger.error(f"Error cleaning up phase one: {e}")
            
            # Clean up main_window
            if hasattr(self, 'main_window'):
                try:
                    logger.debug("Cleaning up main window")
                    if hasattr(self.main_window, 'close') and callable(self.main_window.close):
                        self.main_window.close()
                except Exception as e:
                    logger.error(f"Error cleaning up main window: {e}")
            
            # Clean up resource_manager last
            if hasattr(self, 'resource_manager'):
                try:
                    logger.debug("Cleaning up resource manager")
                    if hasattr(self.resource_manager, 'shutdown') and callable(self.resource_manager.shutdown):
                        self.resource_manager.shutdown()
                except Exception as e:
                    logger.error(f"Error cleaning up resource manager: {e}")
                    
            logger.info("Component cleanup completed")
        except Exception as e:
            logger.error(f"Error during component cleanup: {e}", exc_info=True)

    def _handle_agent_selection(self, agent_id: str):
        try:
            agent_state = self.resource_manager.get_state(f"agent:{agent_id}:state")
            if agent_state:
                self.main_window.agent_metrics.update_metrics(agent_id)
        except Exception as e:
            logger.error(f"Agent selection error: {e}")
            # self._attempt_recovery(e)

    async def setup_event_processing(self):
        try:
            monitor_timer = QTimer()
            monitor_timer.timeout.connect(self._update_system_monitoring)
            monitor_timer.start(5000)
            
            await self.resource_manager._event_queue.subscribe(
                ResourceEventTypes.METRIC_RECORDED,
                self._handle_metric_update
            )
            
        except Exception as e:
            logger.error(f"Event processing setup failed: {e}")
            # self._attempt_recovery(e)

    async def _update_system_monitoring(self):
        try:
            # Try to collect metrics with error handling
            try:
                metrics = await self.system_monitor.collect_system_metrics()
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                metrics = {"error": str(e), "timestamp": datetime.now().isoformat()}
            
            # Try to analyze metrics with error handling
            try:
                monitoring_result = await self.phase_zero.monitoring_agent.analyze_metrics(metrics)
            except Exception as e:
                logger.error(f"Error analyzing metrics: {e}")
                monitoring_result = {"flag_raised": False}
            
            # Try to update UI with error handling
            try:
                self.main_window.system_metrics.update_metrics()
            except Exception as e:
                logger.error(f"Error updating metrics UI: {e}")
                
            # Handle monitoring flags if raised
            if monitoring_result.get("flag_raised"):
                try:
                    await self._handle_system_flags(monitoring_result)
                except Exception as e:
                    logger.error(f"Error handling system flags: {e}")
                    
        except Exception as e:
            logger.error(f"Monitoring update failed: {e}")
            # Don't propagate the exception to prevent crashing the monitoring loop

    def _handle_metric_update(self, event_type: str, data: Dict[str, Any]):
        try:
            metric_name = data.get("metric")
            if metric_name:
                self.main_window.system_metrics.check_thresholds({
                    metric_name: data.get("value", 0)
                })
        except Exception as e:
            logger.error(f"Metric update error: {e}")
            # self._attempt_recovery(e)

    async def _handle_system_flags(self, monitoring_result: Dict[str, Any]):
        try:
            self.main_window.system_metrics.alert_widget.add_alert(
                monitoring_result.get("severity", "WARNING"),
                monitoring_result.get("message", "System flag raised")
            )
            
            if monitoring_result.get("requires_refinement"):
                self.async_helper.run_coroutine(
                    self.phase_one.process_task(
                        "System refinement required",
                        monitoring_result
                    )
                )
        except Exception as e:
            logger.error(f"System flags handling error: {e}")
            # await self._attempt_recovery(e)

    # async def _attempt_recovery(self, error: Exception):
    #     try:
    #         recovery_result = await self.phase_zero.monitoring_agent.analyze_metrics({
    #             "error": str(error),
    #             "timestamp": datetime.now().isoformat(),
    #             "system_state": self.resource_manager.get_system_state()
    #         })
            
    #         if recovery_result.get("recovery_recommendation"):
    #             await self._execute_recovery_plan(recovery_result["recovery_recommendation"])
    #         else:
    #             self._handle_fatal_error("Unrecoverable system error", error)
                
    #     except Exception as recovery_error:
    #         self._handle_fatal_error("Recovery attempt failed", recovery_error)
    
    # Disable recovery attempts for now
    async def _attempt_recovery(self, error: Exception):
        """Temporarily disabled recovery attempts"""
        logger.error(f"Error occurred (recovery disabled): {error}")
        self._handle_error("System error", error)

    async def _execute_recovery_plan(self, recovery_plan: Dict[str, Any]):
        try:
            for action in recovery_plan.get("recovery_sequence", []):
                if action["type"] == "reinitialize":
                    await self._reinitialize_component(action["target"])
                elif action["type"] == "restart":
                    await self._restart_component(action["target"])
                elif action["type"] == "reset":
                    await self._reset_component(action["target"])
                    
            logger.info("System recovery completed")
            
        except Exception as e:
            logger.error(f"Recovery execution failed: {e}")
            raise

    async def _reinitialize_component(self, component: str):
        if component == "phase_zero":
            self.phase_zero = PhaseZeroOrchestrator(self._event_queue, self.resource_manager, self.context_manager, self.cache_manager, self.metrics_manager, self.error_handler)
        elif component == "phase_one":
            self.phase_one = PhaseOneOrchestrator(self._event_queue, self.resource_manager, self.context_manager, self.cache_manager, self.metrics_manager, self.error_handler, phase_zero=self.phase_zero)
        elif component == "monitor":
            self.system_monitor = SystemMonitor()

    async def _restart_component(self, component: str):
        self.resource_manager.reset_component_state(component)
        await self._reinitialize_component(component)

    async def _reset_component(self, component: str):
        self.resource_manager.reset_component_state(component)

    def run(self):
        """Run the application main loop."""
        try:
            # Show the main window if it's not already visible
            if hasattr(self, 'main_window') and not self.main_window.isVisible():
                self.main_window.show()
            
            # Make sure the event timer is running
            if hasattr(self, 'event_timer') and not self.event_timer.isActive():
                self.event_timer.start(100)
            
            # Register signal handlers for clean shutdown
            self._setup_signal_handlers()
            
            # Set up any necessary exception hooks
            sys.excepthook = self._global_exception_handler
            
            # Check if event loop is already running
            if not hasattr(self.app, '_is_running'):
                self.app._is_running = False
                
            if self.app._is_running:
                logger.warning("Qt event loop is already running, not starting it again")
                return 0
                
            # Let the qasync event loop handle the Qt application execution
            logger.info("Starting application main loop")
            self.app._is_running = True
            try:
                return self.app.exec()
            finally:
                self.app._is_running = False
        except Exception as e:
            logger.error(f"Runtime error: {e}", exc_info=True)
            self._handle_fatal_error("Runtime error", e)
            return 1

    def _setup_signal_handlers(self):
        """Set up signal handlers using Qt mechanisms"""
        # For Unix-like systems, use asyncio's signal handling
        if hasattr(signal, 'SIGINT') and sys.platform != 'win32':
            loop = asyncio.get_event_loop()
            for signame in ('SIGINT', 'SIGTERM'):
                if hasattr(signal, signame):
                    try:
                        loop.add_signal_handler(
                            getattr(signal, signame),
                            lambda signame=signame: self._handle_signal(signame)
                        )
                        logger.debug(f"Added signal handler for {signame}")
                    except NotImplementedError:
                        # Fallback for platforms where add_signal_handler is not implemented
                        signal.signal(
                            getattr(signal, signame),
                            lambda signum, frame, signame=signame: self._handle_signal(signame)
                        )
                        logger.debug(f"Added fallback signal handler for {signame}")
        else:
            # Fallback for Windows - still use a timer, but simplify
            self.exit_check_timer = QTimer()
            self.exit_check_timer.timeout.connect(self._check_exit_request)
            self.exit_check_timer.start(200)

    def _handle_signal(self, signame):
        """Handle a signal in the main thread safely."""
        logger.info(f"Received signal {signame}, initiating shutdown")
        # Schedule the app to quit safely from the main thread
        QTimer.singleShot(0, self.app.quit)

    def _check_exit_request(self):
        """Check for exit requests on Windows."""
        # Simplified version that just checks for Ctrl+C
        try:
            import msvcrt
            if msvcrt.kbhit() and msvcrt.getch() == b'\x03':  # Ctrl+C
                logger.info("Ctrl+C detected, initiating shutdown")
                self.exit_check_timer.stop()
                QTimer.singleShot(0, self.app.quit)
        except (ImportError, IOError, OSError):
            pass  # Ignore if msvcrt is not available

    def _global_exception_handler(self, exc_type, exc_value, exc_traceback):
        """Global exception handler for unhandled exceptions with improved handling."""
        # Skip for KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            logger.info("Keyboard interrupt received")
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Log the exception
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.critical(f"Unhandled exception: {error_msg}")
        
        # Check if we're in the main thread
        if threading.current_thread() is threading.main_thread():
            # Show error dialog directly if in main thread
            self._show_error_dialog("Unhandled Exception", error_msg)
        else:
            # Schedule error dialog from the main thread
            QTimer.singleShot(0, lambda: self._show_error_dialog("Unhandled Exception", error_msg))

    def _show_error_dialog(self, title, message):
        """Show an error dialog safely from the main thread."""
        try:
            # First check that we have a main window
            if hasattr(self, 'main_window') and self.main_window is not None:
                QMessageBox.critical(self.main_window, title, message)
            else:
                # Fallback to a parent-less dialog if no main window
                QMessageBox.critical(None, title, message)
        except Exception as e:
            # Last resort if even showing the dialog fails
            logger.critical(f"Failed to show error dialog: {e}")
            logger.critical(f"Original error: {message}")
        
    def _handle_error(self, context, error_message):
        """Standardized error handling method with improved logging."""
        # Generate a unique error ID for tracking
        error_id = time.strftime('%Y%m%d%H%M%S-') + str(random.randint(1000, 9999))
        
        # Log with the ID for correlation
        logger.error(f"Error {error_id} in {context}: {error_message}")
        
        # Notify the user interface if available
        if hasattr(self, 'main_window'):
            try:
                self.main_window._handle_error(context, f"{error_message} (Error ID: {error_id})")
            except Exception as ui_error:
                logger.error(f"Failed to show error in UI: {ui_error}")
        
        # Return the error ID for potential reference
        return error_id

    def _handle_fatal_error(self, context: str, error: Exception):
        """Handle fatal errors with improved diagnostics and cleanup."""
        # Generate unique error ID
        error_id = time.strftime('%Y%m%d%H%M%S-') + str(random.randint(1000, 9999))
        
        # Format traceback
        tb = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        error_msg = f"{context} (Error ID: {error_id}):\n\n{tb}"
        
        # Log the error
        logger.critical(error_msg)
        
        # Try to stop ongoing processes if possible
        if hasattr(self, 'async_helper'):
            self.async_helper.request_shutdown()
        
        # Show message box
        try:
            QMessageBox.critical(
                None,
                "Fatal Error",
                f"A fatal error has occurred (Error ID: {error_id}):\n\n{error}\n\nThe application will now exit."
            )
        except Exception as dialog_error:
            logger.critical(f"Failed to show error dialog: {dialog_error}")
        
        # Force exit on fatal errors instead of attempting recovery
        sys.exit(1)

    def _show_error_dialog(self, title, message):
        """Show an error dialog safely from the main thread."""
        QMessageBox.critical(self.main_window, title, message)
    
    def register_task(self, coro, callback=None):
        """Register and track an asyncio task with proper error handling"""
        # Check if we're in shutdown mode
        if hasattr(self, 'async_helper') and self.async_helper.shutdown_requested:
            logger.warning("Task creation rejected: application is shutting down")
            if callable(callback):
                try:
                    # Create a fake cancelled task to pass to the callback
                    future = asyncio.Future()
                    future.cancel()
                    callback(future)
                except Exception as e:
                    logger.error(f"Error calling callback with cancelled task: {e}")
            return None
        
        loop = asyncio.get_event_loop()
        
        # Create a task if needed
        if isinstance(coro, asyncio.Task):
            task = coro
        else:
            task = loop.create_task(coro)
        
        # Add task lifecycle management
        def _on_task_complete(task):
            # Always remove the task from registry
            self._tasks.discard(task)
            
            # Call the original callback if provided
            if callback:
                try:
                    callback(task)
                except Exception as e:
                    logger.error(f"Error in task callback: {e}", exc_info=True)
        
        task.add_done_callback(_on_task_complete)
        self._tasks.add(task)
        return task

    def _cancel_tasks_sync(self):
        """Synchronously cancel all asyncio tasks"""
        try:
            # Check if there's a running event loop first
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                logger.warning("No running event loop during task cancellation")
                self._tasks.clear()  # Clear tasks since we can't cancel them properly
                return
                
            if not loop.is_running():
                logger.warning("Event loop is not running during task cancellation")
                self._tasks.clear()  # Clear tasks since we can't cancel them properly
                return
                    
            # Use run_coroutine_threadsafe since we're in the Qt thread
            future = asyncio.run_coroutine_threadsafe(self.cancel_all_tasks(), loop)
            try:
                # Wait with timeout for tasks to cancel
                future.result(timeout=5.0)
            except concurrent.futures.TimeoutError:
                logger.error("Timeout waiting for tasks to cancel")
                # Force clear tasks after timeout
                self._tasks.clear()
            except asyncio.CancelledError:
                logger.warning("Task cancellation was itself cancelled")
                self._tasks.clear()
            except Exception as e:
                logger.error(f"Error cancelling tasks: {e}")
                # Last resort: clear task set
                self._tasks.clear()
        except Exception as e:
            logger.error(f"Failed to cancel tasks: {e}", exc_info=True)
            # Last resort: clear task set
            self._tasks.clear()

    async def cancel_all_tasks(self):
        """Cancel all tasks with proper timeout and exception handling"""
        if not self._tasks:
            return
            
        logger.info(f"Cancelling {len(self._tasks)} tasks...")
        
        # Make a copy to avoid modification during iteration
        tasks_to_cancel = list(self._tasks)
        
        # Flag async_helper to prevent new tasks
        if hasattr(self, 'async_helper'):
            self.async_helper.request_shutdown()
        
        # Cancel all tasks
        for task in tasks_to_cancel:
            if not task.done() and not task.cancelled():
                # Suppress traceback logging for cancelled tasks to reduce noise
                try:
                    task._log_traceback = False
                except AttributeError:
                    pass
                task.cancel()
        
        # Wait for tasks to complete with timeout
        if tasks_to_cancel:
            # Filter out completed tasks
            pending_tasks = [t for t in tasks_to_cancel if not t.done()]
            
            if pending_tasks:
                try:
                    # Use wait with timeout
                    done, pending = await asyncio.wait(
                        pending_tasks, 
                        timeout=5.0,
                        return_when=asyncio.ALL_COMPLETED
                    )
                    
                    if pending:
                        logger.warning(f"{len(pending)} tasks did not cancel properly")
                        # Force remove them from the set
                        for task in pending:
                            self._tasks.discard(task)
                except asyncio.CancelledError:
                    logger.warning("cancel_all_tasks was itself cancelled")
                    # Clear all tasks from the set to ensure clean shutdown
                    self._tasks.clear()
                except Exception as e:
                    logger.error(f"Error waiting for tasks to cancel: {e}")
                    # Last resort: clear task set
                    self._tasks.clear()
            
        logger.info("Task cancellation complete")
    
    def run_async_operation(self, coro, on_success=None, on_error=None):
        """
        Run an async operation from a UI event with proper callbacks
        
        Args:
            coro: Coroutine to run
            on_success: Function to call with the result on success
            on_error: Function to call with error message on failure
        """
        # Create callback to handle result
        def handle_completion(result_dict):
            status = result_dict.get("status")
            if status == "success":
                if on_success:
                    on_success(result_dict.get("result"))
            elif status == "error" and on_error:
                on_error(result_dict.get("error"))
        
        # Connect to task completion signal
        temp_connection = self.async_helper.taskCompleted.connect(handle_completion)
        
        # Run the coroutine
        self.async_helper.run_coroutine(coro)
        
        # Return the connection so it can be disconnected later if needed
        return temp_connection

    def _handle_task_error(self, error):
        """Handle task errors in a standardized way."""
        # Log the error
        logger.error(f"Task error: {error}", exc_info=True)
        
        # Emit to main window or other UI components if needed
        if hasattr(self, 'main_window'):
            self.main_window._handle_error("Task error", str(error))

    def close(self):
        """Clean up resources in the correct sequence with improved event queue handling"""
        logger.info("Application shutdown initiated")
        
        # 1. Flag the AsyncHelper to stop accepting new tasks
        if hasattr(self, 'async_helper'):
            self.async_helper.request_shutdown()
        
        # 2. Stop all timers to prevent new events
        self._stop_all_timers()
        
        # 3. Process pending Qt events to flush any pending signals
        self.app.processEvents()
        
        # 4. Disable signal handlers
        self._stop_signal_handlers()
        
        # 5. Cancel all async tasks
        self._cancel_tasks_sync()
        
        # 6. Process events again to handle any callbacks from task cancellation
        self.app.processEvents()
        
        # 7. Stop all threads
        self._stop_threads()
        
        # 8. Process events again
        self.app.processEvents()
        
        # 9. Clean up component resources with proper dependency order
        logger.info("Shutting down application components")
        
        try:
            # Create a correlation ID for tracking the shutdown sequence
            import uuid
            shutdown_id = str(uuid.uuid4())
            logger.info(f"Starting coordinated shutdown with ID: {shutdown_id}")
            
            # Clean up orchestrators first (they depend on the managers)
            if hasattr(self, 'phase_one'):
                self._shutdown_component('phase_one')
            
            if hasattr(self, 'phase_zero'):
                self._shutdown_component('phase_zero')
            
            # Then UI components
            if hasattr(self, 'main_window'):
                self._shutdown_component('main_window')
                
            # Use ResourceCoordinator for orderly component shutdown
            if hasattr(self, 'resource_coordinator'):
                try:
                    logger.info("Initiating coordinated shutdown via ResourceCoordinator")
                    # Run in the correct loop context
                    if asyncio.get_event_loop().is_running():
                        future = asyncio.run_coroutine_threadsafe(
                            self.resource_coordinator.shutdown(),
                            asyncio.get_event_loop()
                        )
                        # Wait with timeout for orderly shutdown
                        try:
                            future.result(timeout=15.0)
                            logger.info("ResourceCoordinator shutdown completed successfully")
                        except concurrent.futures.TimeoutError:
                            logger.warning("Timeout during ResourceCoordinator shutdown")
                        except Exception as e:
                            logger.error(f"Error during ResourceCoordinator shutdown: {e}")
                except Exception as e:
                    logger.error(f"Error starting ResourceCoordinator shutdown: {e}")
            
            # Use EventLoopManager to clean up any remaining registered resources
            # This is a fallback in case some components weren't properly registered
            from resources.events import EventLoopManager
            if asyncio.get_event_loop().is_running():
                future = asyncio.run_coroutine_threadsafe(
                    EventLoopManager.cleanup_resources(),
                    asyncio.get_event_loop()
                )
                # Wait with timeout
                try:
                    future.result(timeout=10.0)
                    logger.info("EventLoopManager resources cleaned up successfully")
                except concurrent.futures.TimeoutError:
                    logger.warning("Timeout while cleaning up resources")
                except Exception as e:
                    logger.error(f"Error during resource cleanup: {e}")
            
            # For backwards compatibility or fallback, stop any components that weren't handled properly
            # Only used if ResourceCoordinator fails or is not available
            if not hasattr(self, 'resource_coordinator') or not asyncio.get_event_loop().is_running():
                # First monitoring components (they depend on the event queue)
                if hasattr(self, 'system_monitor'):
                    self._shutdown_component('system_monitor', async_method=True)
                
                if hasattr(self, 'memory_monitor'):
                    self._shutdown_component('memory_monitor', async_method=True)
                
                if hasattr(self, 'health_tracker'):
                    self._shutdown_component('health_tracker', async_method=True)
                
                # Then resource managers (they depend on the event queue)
                for component in ['resource_manager', 'context_manager', 'cache_manager', 
                                'metrics_manager', 'error_handler']:
                    if hasattr(self, component):
                        self._shutdown_component(component)
            
            # Finally, stop the event queue safely in its own loop context
            if hasattr(self, '_event_queue'):
                try:
                    logger.info("Stopping event queue")
                    if hasattr(self._event_queue, 'stop'):
                        # This will automatically use EventLoopManager to run in the queue's creation loop
                        if asyncio.get_event_loop().is_running():
                            future = asyncio.run_coroutine_threadsafe(self._event_queue.stop(), asyncio.get_event_loop())
                            future.result(timeout=5.0)
                        logger.info("Event queue stopped")
                except Exception as e:
                    logger.error(f"Error stopping event queue: {e}")
            
            logger.info("Application components shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
            # Continue with shutdown despite errors
        
        logger.info("Application shutdown complete")

    def _shutdown_component(self, component_name, async_method=False):
        """Safely shut down a component by name"""
        try:
            component = getattr(self, component_name)
            logger.info(f"Shutting down {component_name}")
            
            # Check for shutdown method
            if hasattr(component, 'shutdown') and callable(component.shutdown):
                # Determine if method is async regardless of async_method parameter
                is_async = asyncio.iscoroutinefunction(component.shutdown)
                if is_async:
                    loop = asyncio.get_event_loop()
                    future = asyncio.run_coroutine_threadsafe(component.shutdown(), loop)
                    future.result(timeout=5.0)
                else:
                    component.shutdown()
            # Check for stop method
            elif hasattr(component, 'stop') and callable(component.stop):
                if async_method:
                    # Run async method in sync context
                    loop = asyncio.get_event_loop()
                    future = asyncio.run_coroutine_threadsafe(component.stop(), loop)
                    future.result(timeout=5.0)
                else:
                    component.stop()
            # Check for close method (like for UI components)
            elif hasattr(component, 'close') and callable(component.close):
                component.close()
                
            logger.info(f"{component_name} shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down {component_name}: {e}")

    def _stop_all_timers(self):
        """Stop all QTimer instances"""
        logger.debug("Stopping all timers")
        
        # Explicitly stop event timer first
        if hasattr(self, 'event_timer') and self.event_timer.isActive():
            self.event_timer.stop()
        
        # Find and stop all other timers
        for attr_name in dir(self):
            try:
                attr = getattr(self, attr_name)
                if isinstance(attr, QTimer) and attr.isActive():
                    attr.stop()
            except Exception as e:
                logger.warning(f"Error stopping timer {attr_name}: {e}")
    
    def _stop_signal_handlers(self):
        """Disable signal handlers during shutdown."""
        logger.debug("Disabling signal handlers")
        
        # Remove signal handlers if possible
        if hasattr(signal, 'SIGINT') and sys.platform != 'win32':
            loop = asyncio.get_event_loop()
            for signame in ('SIGINT', 'SIGTERM'):
                if hasattr(signal, signame):
                    try:
                        loop.remove_signal_handler(getattr(signal, signame))
                        logger.debug(f"Removed signal handler for {signame}")
                    except (NotImplementedError, ValueError, RuntimeError):
                        # Ignore if handler wasn't set or can't be removed
                        pass
        
        # Stop the exit check timer on Windows
        if hasattr(self, 'exit_check_timer') and self.exit_check_timer.isActive():
            try:
                self.exit_check_timer.stop()
                logger.debug("Stopped exit check timer")
            except Exception as e:
                logger.warning(f"Error stopping exit check timer: {e}")


async def main():
    forest_app = None
    try:
         # The event loop should already be set up by qasync
        loop = asyncio.get_event_loop()
        logger.info(f"Main function running in event loop {id(loop)} on thread {threading.get_ident()}")
        
        # Create the application instance with deferred initialization
        forest_app = ForestApplication()

        # Now perform async initialization in the qasync event loop
        logger.info("Running setup_async")
        await forest_app.setup_async()

        # Now configure the main window's async components
        logger.info("Setting up main window async components")
        if hasattr(forest_app, 'main_window') and hasattr(forest_app.main_window, 'setup_async'):
            await forest_app.main_window.setup_async()
        
        # Set up event processing
        logger.info("Setting up event processing")
        await forest_app.setup_event_processing()
        
        return forest_app
    except Exception as e:
        logger.critical("Application failed to start", exc_info=True)
        QMessageBox.critical(None, "Startup Error", 
            f"The application failed to start:\n\n{str(e)}")
        if forest_app:
            forest_app.close()
        return None
    
async def test_event_system_integration():
    """Test the integration between EventQueue and SystemMonitor"""
    logger.info("Testing event system integration")
    
    # Create event queue
    event_queue = EventQueue()
    await event_queue.start()
    
    # Create monitoring components
    memory_monitor = MemoryMonitor(event_queue)
    health_tracker = HealthTracker(event_queue)
    system_monitor = SystemMonitor(event_queue, memory_monitor, health_tracker)
    
    # Start monitoring
    await system_monitor.start()
    
    # Test event emission
    logger.info("Emitting test events")
    for i in range(5):
        await event_queue.emit(
            ResourceEventTypes.METRIC_RECORDED.value,
            {"metric": f"test_metric_{i}", "value": i, "timestamp": datetime.now().isoformat()}
        )
    
    # Wait for events to process
    logger.info("Waiting for events to process")
    await event_queue.wait_for_processing(timeout=2.0)
    
    # Test shutdown sequence
    logger.info("Testing shutdown sequence")
    await system_monitor.stop()
    await event_queue.stop()
    
    logger.info("Integration test complete")
    
if __name__ == "__main__":
    try:
        # Set up exception hook before anything else
        def early_exception_hook(exc_type, exc_value, exc_traceback):
            """Exception hook for early startup errors."""
            print("Early startup error:")
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            logger.critical("Early startup error", exc_info=(exc_type, exc_value, exc_traceback))
            QMessageBox.critical(None, "Startup Error", 
                f"The application failed during early startup:\n\n{str(exc_value)}")
            sys.exit(1)
        
        # Set the early exception hook
        sys.excepthook = early_exception_hook
        
        # Create the Qt application only if one doesn't already exist
        app = QApplication.instance() or QApplication(sys.argv)
        app._is_running = False  # Add flag to track event loop state
        
        # Record the thread ID for the main thread
        main_thread_id = threading.get_ident()
        logger.info(f"Main thread ID: {main_thread_id}")
        
        # Configure qasync with proper exception handler
        def async_exception_handler(loop, context):
            """Custom exception handler for asyncio."""
            exception = context.get('exception')
            message = context.get('message')
            
            # Check if we're in the main thread
            current_thread_id = threading.get_ident()
            if current_thread_id != main_thread_id:
                logger.warning(f"Exception occurred in thread {current_thread_id}, not main thread {main_thread_id}")
            
            # Don't log cancelled tasks as errors
            if isinstance(exception, asyncio.CancelledError):
                logger.debug(f"Task was cancelled: {message}")
                return
                
            # For event loop binding errors, log with more detail
            if exception and isinstance(exception, RuntimeError) and "different event loop" in str(exception):
                logger.error(f"Event loop binding error: {message}", exc_info=exception)
                # Try to get the current loop information
                try:
                    current_loop = asyncio.get_event_loop()
                    logger.error(f"Current loop ID: {id(current_loop)}, Thread ID: {threading.get_ident()}")
                except RuntimeError:
                    logger.error("No event loop in current thread")
                return
                
            # Log the exception
            logger.error(f"Asyncio error: {message}", exc_info=exception)
            
            if 'forest_app' in globals() and forest_app:
                # If we have a ForestApplication instance, use its error handler
                error_id = forest_app._handle_error("Asyncio error", message)
                logger.error(f"Asyncio error logged with ID: {error_id}")
                
        # Create the event loop with qasync
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        logger.info(f"Created qasync event loop: {id(loop)}")
        
        # Set custom exception handler
        loop.set_exception_handler(async_exception_handler)
        
        # Initialize the forest_app variable
        forest_app = None
        
        # Run the application with proper cleanup using context manager
        with loop:
            try:
                # Initialize the application
                logger.info("Running main() to initialize application")
                forest_app = loop.run_until_complete(main())
                
                if forest_app:
                    # Replace the exception hook with the application's version
                    sys.excepthook = forest_app._global_exception_handler
                    
                    # Start the application only if it was initialized successfully
                    logger.info("Starting application main loop")
                    exit_code = forest_app.run()
                else:
                    logger.error("Application initialization failed")
                    exit_code = 1
            finally:
                # Clean up properly, regardless of how we exit the block
                if forest_app:
                    try:
                        # Ensure app is properly closed
                        logger.info("Closing application")
                        forest_app.close()
                    except Exception as e:
                        logger.error(f"Error during application cleanup: {e}", exc_info=True)
        
        # Final cleanup - explicitly process events before quitting
        logger.info("Processing final events")
        app.processEvents()
        
        # Quit only if the app isn't already being quit
        if not app._is_running:
            logger.info("Quitting application")
            app.quit()
            
        logger.info(f"Exiting with code {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.critical("Failed to initialize application", exc_info=True)
        # Show error dialog for truly catastrophic failures
        try:
            QMessageBox.critical(None, "Fatal Error", 
                f"The application failed catastrophically:\n\n{str(e)}")
        except:
            print(f"FATAL ERROR: {e}")
            traceback.print_exc()
        sys.exit(1)