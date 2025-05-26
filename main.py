"""
Main application entry point for Forest For The Trees (FFTT).

This module provides the main application class and execution flow for the FFTT system,
with clear thread boundaries and proper event loop management following the actor model.
"""
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
from resources.managers import AgentContextManager, CacheManager, MetricsManager, ResourceCoordinator
from resources.monitoring.circuit_breakers import CircuitBreakerRegistry
from resources import ResourceEventTypes 
from resources.events import EventQueue, EventLoopManager
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
    """
    Helper class for running async tasks from the Qt main thread.
    
    This class provides a safe way to run coroutines from Qt callbacks while
    ensuring proper error handling and completion notifications. It follows the
    actor model, maintaining clear thread boundaries with the main Qt thread.
    """
    runCoroutineSignal = pyqtSignal(object, object, object)  # Signal to run coroutine in main thread
    errorOccurred = pyqtSignal(str)
    taskCompleted = pyqtSignal(dict)
    
    def __init__(self, app):
        super().__init__()
        self.app = app  # Store reference to ForestApplication
        self.shutdown_requested = False
        self.runCoroutineSignal.connect(self._run_coroutine_in_main_thread)
        self._pending_futures = set()  # Track futures created with run_coroutine_threadsafe
        self._main_thread_id = threading.get_ident()
        logger.debug(f"AsyncHelper initialized in thread {self._main_thread_id}")

    def run_coroutine(self, coro, callback=None, error_callback=None):
        """Safely run a coroutine from the Qt world with improved error handling"""
        # Check if shutdown is in progress
        if self.shutdown_requested:
            logger.warning("Ignoring coroutine request during shutdown")
            if error_callback:
                error_callback("Operation cancelled: application is shutting down")
            return None
        
        # Check if we're in the main thread
        current_thread = threading.get_ident()
        if current_thread != self._main_thread_id:
            logger.warning(f"run_coroutine called from non-main thread {current_thread}, using signal to dispatch")
            # If not in main thread, emit signal to ensure execution in main thread
            self.runCoroutineSignal.emit(coro, callback, error_callback)
        else:
            # Already in main thread, execute directly
            self._run_coroutine_in_main_thread(coro, callback, error_callback)
            
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
        

class EventProcessor(threading.Thread):
    """
    Dedicated thread for processing events from the event queue.
    
    This class implements the actor pattern for event processing, running in its own
    thread with its own event loop. Communication with this actor is done through
    thread-safe message passing via the event queue.
    """
    def __init__(self, event_queue, queue_id="main_event_processor"):
        super().__init__()
        self.daemon = True
        self.name = f"EventProcessor-{queue_id}"
        self._event_queue = event_queue
        self._queue_id = queue_id
        self._stop_event = threading.Event()
        self._loop = None
        self._tasks = set()
        self._thread_id = None
        
        # Signal for notifying when the processor is ready
        self.finished_signal = pyqtSignal()
        
        logger.info(f"EventProcessor created for queue {queue_id}")
        
    def run(self):
        """Thread entry point to run the event processor."""
        try:
            self._thread_id = threading.get_ident()
            logger.info(f"EventProcessor thread {self._thread_id} starting for queue {self._queue_id}")
            
            # Create an event loop for this thread and establish clear ownership
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            # Register with EventLoopManager using thread-local storage to ensure proper thread ownership
            from resources.events.loop_management import ThreadLocalEventLoopStorage
            ThreadLocalEventLoopStorage.get_instance().set_loop(self._loop)
            
            # Log the thread ownership for debugging
            logger.debug(f"Event processor thread {threading.get_ident()} owns event loop {id(self._loop)}")
            
            # Run the event processing coroutine
            self._loop.run_until_complete(self._process_events())
            
            logger.info(f"EventProcessor thread exiting for queue {self._queue_id}")
        except Exception as e:
            logger.error(f"Error in event processor thread: {e}", exc_info=True)
        finally:
            # Clean up event loop
            if self._loop and not self._loop.is_closed():
                self._loop.close()
                
    async def _process_events(self):
        """Main event processing coroutine."""
        try:
            logger.info(f"Event processing started for queue {self._queue_id}")
            
            while not self._stop_event.is_set():
                try:
                    # Get events from queue with a timeout
                    await self._process_event_batch()
                    
                    # Add a small delay to prevent CPU spinning
                    await asyncio.sleep(0.01)
                    
                except Exception as e:
                    logger.error(f"Error processing events: {e}", exc_info=True)
                    await asyncio.sleep(0.1)  # Add delay after error
                    
            logger.info(f"Event processing stopped for queue {self._queue_id}")
        except asyncio.CancelledError:
            logger.info(f"Event processing cancelled for queue {self._queue_id}")
        except Exception as e:
            logger.error(f"Unexpected error in event processor: {e}", exc_info=True)
            
    async def _process_event_batch(self):
        """Process a batch of events from the queue."""
        # Maximum number of events to process in one batch
        max_batch_size = 10
        events_processed = 0
        
        # Process high priority events first
        while events_processed < max_batch_size:
            try:
                # Try to get a high priority event first
                event = self._event_queue.get_nowait()
                
                # Process the event
                await self._process_single_event(event)
                events_processed += 1
                
            except asyncio.QueueEmpty:
                # No more events in the queue
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)
                
        return events_processed
                
    async def _process_single_event(self, event):
        """Process a single event."""
        logger.debug(f"Processing event: {event.event_type}")
        # Event processing logic goes here
        # This would delegate to subscribers registered with the event queue
            
    def stop(self):
        """Signal the processor to stop."""
        logger.info(f"Stopping event processor for queue {self._queue_id}")
        self._stop_event.set()
        
        # Cancel all running tasks
        if self._loop and not self._loop.is_closed():
            for task in asyncio.all_tasks(self._loop):
                task.cancel()
                
        logger.info(f"Event processor stop signal sent for queue {self._queue_id}")


class ResourceManager:
    """
    Centralized management of all application resources with proper lifecycle tracking.
    
    This class manages the lifecycle of all resources in the application, ensuring proper
    initialization, monitoring, and cleanup. It follows the actor model, with each resource
    potentially running in its own thread with its own event loop.
    """
    def __init__(self, main_event_queue):
        self._event_queue = main_event_queue
        self._resources = {}  # resource_id -> resource instance
        self._dependencies = {}  # resource_id -> list of dependency resource_ids
        self._reverse_dependencies = {}  # resource_id -> list of dependent resource_ids
        self._resource_states = {}  # resource_id -> state
        self._resource_threads = {}  # resource_id -> thread
        self._lock = threading.RLock()
        
        logger.info("ResourceManager initialized")
        
    async def register_resource(self, resource_id, resource, dependencies=None):
        """Register a resource with dependency tracking."""
        with self._lock:
            if resource_id in self._resources:
                logger.warning(f"Resource {resource_id} already registered, updating")
                
            self._resources[resource_id] = resource
            
            # Store dependencies
            if dependencies:
                self._dependencies[resource_id] = list(dependencies)
                
                # Update reverse dependencies
                for dep_id in dependencies:
                    if dep_id not in self._reverse_dependencies:
                        self._reverse_dependencies[dep_id] = []
                    if resource_id not in self._reverse_dependencies[dep_id]:
                        self._reverse_dependencies[dep_id].append(resource_id)
            
            # Initialize state
            self._resource_states[resource_id] = "registered"
            
        logger.info(f"Registered resource: {resource_id}")
        
    async def initialize_all(self):
        """Initialize all resources in dependency order with thread boundary awareness."""
        # Find initialization order based on dependencies
        initialization_order = self._calculate_initialization_order()
        logger.info(f"Initializing resources in order: {initialization_order}")
        
        # Group resources by their thread affinity
        from resources.events.loop_management import EventLoopManager
        thread_local = threading.local()
        thread_local.current_thread_id = threading.get_ident()
        
        # Track which resources are initialized in which thread
        thread_resources = {}
        
        # Initialize resources in order
        for resource_id in initialization_order:
            # Determine if resource specifies thread affinity
            resource = self._resources[resource_id]
            thread_affinity = getattr(resource, '_thread_affinity', None)
            
            if thread_affinity and thread_affinity != thread_local.current_thread_id:
                # Resource should be initialized in a specific thread
                if thread_affinity not in thread_resources:
                    thread_resources[thread_affinity] = []
                thread_resources[thread_affinity].append(resource_id)
                logger.debug(f"Resource {resource_id} queued for initialization in thread {thread_affinity}")
            else:
                # Initialize in current thread
                await self.initialize_resource(resource_id)
                logger.debug(f"Resource {resource_id} initialized in thread {thread_local.current_thread_id}")
        
        # For resources that need to be initialized in other threads, use EventLoopManager
        for thread_id, resources in thread_resources.items():
            for resource_id in resources:
                # Use EventLoopManager to run in the correct thread
                try:
                    logger.debug(f"Submitting {resource_id} initialization to thread {thread_id}")
                    future = EventLoopManager.run_coroutine_threadsafe(
                        self.initialize_resource(resource_id),
                        target_loop=EventLoopManager.get_loop_for_thread(thread_id)
                    )
                    # Wait for initialization to complete
                    await asyncio.wrap_future(future)
                except Exception as e:
                    logger.error(f"Failed to initialize {resource_id} in thread {thread_id}: {e}")
                    self._resource_states[resource_id] = "failed"
            
        logger.info("All resources initialized")
        
    def _calculate_initialization_order(self):
        """Calculate initialization order based on dependencies."""
        # Implementation of topological sort
        # This ensures resources are initialized after their dependencies
        with self._lock:
            # Create a copy of the dependency graph
            graph = dict(self._dependencies)
            
            # Add resources without dependencies
            for resource_id in self._resources:
                if resource_id not in graph:
                    graph[resource_id] = []
            
            # Calculate in-degree for each resource
            in_degree = {resource_id: 0 for resource_id in graph}
            for resource_id, deps in graph.items():
                for dep in deps:
                    in_degree[dep] = in_degree.get(dep, 0) + 1
            
            # Find resources with no dependencies
            queue = [resource_id for resource_id in graph if in_degree[resource_id] == 0]
            
            # Process resources in order
            initialization_order = []
            while queue:
                resource_id = queue.pop(0)
                initialization_order.append(resource_id)
                
                # Reduce in-degree of dependent resources
                for dep_resource_id in self._reverse_dependencies.get(resource_id, []):
                    in_degree[dep_resource_id] -= 1
                    if in_degree[dep_resource_id] == 0:
                        queue.append(dep_resource_id)
            
            # Check for circular dependencies
            if len(initialization_order) != len(self._resources):
                logger.error("Circular dependencies detected in resource initialization")
                
            return initialization_order
            
    async def initialize_resource(self, resource_id):
        """Initialize a single resource."""
        with self._lock:
            if resource_id not in self._resources:
                logger.warning(f"Cannot initialize unknown resource: {resource_id}")
                return False
                
            resource = self._resources[resource_id]
            current_state = self._resource_states.get(resource_id)
            
            if current_state == "initialized":
                logger.debug(f"Resource {resource_id} already initialized")
                return True
                
            # Update state
            self._resource_states[resource_id] = "initializing"
            
        # Check dependencies
        dependencies = self._dependencies.get(resource_id, [])
        for dep_id in dependencies:
            dep_state = self._resource_states.get(dep_id)
            if dep_state != "initialized":
                logger.warning(f"Dependency {dep_id} not initialized for {resource_id}")
                # Try to initialize it
                await self.initialize_resource(dep_id)
                
        # Initialize the resource
        try:
            if hasattr(resource, 'initialize') and callable(resource.initialize):
                # Check if it's an async method
                if asyncio.iscoroutinefunction(resource.initialize):
                    await resource.initialize()
                else:
                    resource.initialize()
                    
            # Update state
            with self._lock:
                self._resource_states[resource_id] = "initialized"
                
            logger.info(f"Resource {resource_id} initialized")
            return True
        except Exception as e:
            logger.error(f"Error initializing resource {resource_id}: {e}", exc_info=True)
            with self._lock:
                self._resource_states[resource_id] = "error"
            return False
            
    async def shutdown(self):
        """Shutdown all resources in reverse initialization order."""
        # Get reverse of initialization order
        shutdown_order = self._calculate_initialization_order()
        shutdown_order.reverse()
        
        logger.info(f"Shutting down resources in order: {shutdown_order}")
        
        # Shutdown resources in order
        for resource_id in shutdown_order:
            await self.shutdown_resource(resource_id)
            
        logger.info("All resources shut down")
        
    async def shutdown_resource(self, resource_id):
        """Shutdown a single resource."""
        with self._lock:
            if resource_id not in self._resources:
                logger.warning(f"Cannot shutdown unknown resource: {resource_id}")
                return False
                
            resource = self._resources[resource_id]
            current_state = self._resource_states.get(resource_id)
            
            if current_state == "shutdown":
                logger.debug(f"Resource {resource_id} already shut down")
                return True
                
            # Update state
            self._resource_states[resource_id] = "shutting_down"
            
        # Shutdown any dependent resources first
        dependents = self._reverse_dependencies.get(resource_id, [])
        for dep_id in dependents:
            dep_state = self._resource_states.get(dep_id)
            if dep_state not in ["shutting_down", "shutdown"]:
                logger.debug(f"Shutting down dependent resource {dep_id} before {resource_id}")
                await self.shutdown_resource(dep_id)
                
        # Shutdown the resource
        try:
            # Try various shutdown method names
            if hasattr(resource, 'shutdown') and callable(resource.shutdown):
                if asyncio.iscoroutinefunction(resource.shutdown):
                    await resource.shutdown()
                else:
                    resource.shutdown()
            elif hasattr(resource, 'stop') and callable(resource.stop):
                if asyncio.iscoroutinefunction(resource.stop):
                    await resource.stop()
                else:
                    resource.stop()
            elif hasattr(resource, 'close') and callable(resource.close):
                if asyncio.iscoroutinefunction(resource.close):
                    await resource.close()
                else:
                    resource.close()
                    
            # Update state
            with self._lock:
                self._resource_states[resource_id] = "shutdown"
                
            logger.info(f"Resource {resource_id} shut down")
            return True
        except Exception as e:
            logger.error(f"Error shutting down resource {resource_id}: {e}", exc_info=True)
            with self._lock:
                self._resource_states[resource_id] = "error_shutdown"
            return False


class ForestApplication:
    """
    Main application class for Forest For The Trees (FFTT).
    
    This class manages the lifecycle of the application components following
    the actor model, with clear thread boundaries and resource ownership.
    """
    def __init__(self):
        # Get existing QApplication or create one
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        
        # Initialize the event queue in constructor
        self._event_queue = EventQueue(queue_id="forest_main_queue")
        
        # Store the thread ID and loop information for diagnostics
        self._init_thread_id = threading.get_ident()
        try:
            current_loop = asyncio.get_event_loop()
            self._init_loop_id = id(current_loop)
        except RuntimeError:
            self._init_loop_id = None
            logger.warning("No event loop available during ForestApplication initialization")
        
        # Set up thread-safe task tracking
        self._tasks = set()
        self._tasks_lock = threading.RLock()
        self._threads = set()
        self._thread_lock = threading.RLock()
        
        # Flag for initialization status
        self._initialized = False
        
        # Create resource manager
        self._resource_manager = ResourceManager(self._event_queue)
        
        # Create dedicated event processor thread
        self._event_processor = None
        
        logger.info("ForestApplication instance created")
        
    async def setup_async(self):
        """Initialize components that require the event loop"""
        if self._initialized:
            logger.info("ForestApplication already initialized")
            return
            
        # Start a dedicated event processor thread
        self._event_processor = EventProcessor(self._event_queue)
        self.register_thread(self._event_processor)
        self._event_processor.start()
        
        # Set up the async helper for Qt integration
        self.async_helper = AsyncHelper(self)
        
        # Initialize components with proper resource manager coordination
        try:
            # Generate correlation ID for tracking
            correlation_id = f"init_sequence_{threading.get_ident()}_{int(time.time())}"
            logger.info(f"Starting initialization with correlation ID: {correlation_id}")
            
            # Initialize centralized circuit breaker registry with thread-safety
            logger.info("Initializing circuit breaker registry")
            self.circuit_registry = CircuitBreakerRegistry(self._event_queue)
            await self._resource_manager.register_resource("circuit_breaker_registry", self.circuit_registry)
            
            # Initialize state manager first (fundamental component)
            logger.info("Initializing state manager")
            self.state_manager = StateManager(self._event_queue)
            await self._resource_manager.register_resource("state_manager", self.state_manager)
            
            # Initialize resource managers with proper dependency tracking
            logger.info("Initializing resource managers")
            
            # Context manager depends on state manager
            self.context_manager = AgentContextManager(self._event_queue)
            await self._resource_manager.register_resource(
                "context_manager", 
                self.context_manager, 
                dependencies=["state_manager"]
            )
            
            # Cache manager depends on state manager
            self.cache_manager = CacheManager(self._event_queue)
            await self._resource_manager.register_resource(
                "cache_manager", 
                self.cache_manager, 
                dependencies=["state_manager"]
            )
            
            # Metrics manager depends on state manager
            self.metrics_manager = MetricsManager(self._event_queue)
            await self._resource_manager.register_resource(
                "metrics_manager", 
                self.metrics_manager, 
                dependencies=["state_manager"]
            )
            
            # Initialize monitoring components
            logger.info("Initializing monitoring components")
            
            # Memory monitor has no dependencies
            self.memory_monitor = MemoryMonitor(self._event_queue)
            await self._resource_manager.register_resource("memory_monitor", self.memory_monitor)
            
            # Health tracker depends on memory monitor for diagnostics
            self.health_tracker = HealthTracker(self._event_queue)
            await self._resource_manager.register_resource(
                "health_tracker", 
                self.health_tracker, 
                dependencies=["memory_monitor"]
            )
            
            # System monitor depends on both memory monitor and health tracker
            self.system_monitor = SystemMonitor(self._event_queue, self.memory_monitor, self.health_tracker)
            await self._resource_manager.register_resource(
                "system_monitor", 
                self.system_monitor, 
                dependencies=["memory_monitor", "health_tracker"]
            )
            
            # Error handling components
            logger.info("Initializing error handling components")
            
            # Error handler depends on state manager
            self.error_handler = ErrorHandler(self._event_queue)
            await self._resource_manager.register_resource(
                "error_handler", 
                self.error_handler, 
                dependencies=["state_manager"]
            )
            
            # Error recovery depends on error handler and health tracker
            self.error_recovery = SystemErrorRecovery(self._event_queue, self.health_tracker)
            await self._resource_manager.register_resource(
                "error_recovery", 
                self.error_recovery, 
                dependencies=["error_handler", "health_tracker"]
            )
            
            # Initialize all components in dependency order
            logger.info("Starting coordinated initialization of all resources")
            await self._resource_manager.initialize_all()
            
            # Initialize orchestrators after resource managers
            logger.info("Initializing orchestrators")
            
            # Phase zero depends on resource managers
            self.phase_zero = PhaseZeroOrchestrator(
                self._event_queue, 
                self.state_manager, 
                self.context_manager, 
                self.cache_manager, 
                self.metrics_manager, 
                self.error_handler,
                error_recovery=self.error_recovery
            )
            await self._resource_manager.register_resource(
                "phase_zero", 
                self.phase_zero, 
                dependencies=["state_manager", "context_manager", "cache_manager", "metrics_manager", "error_handler"]
            )
            
            # Initialize phase_three first since phase_two depends on it
            self.phase_three = PhaseThreeInterface(
                self._event_queue, 
                self.state_manager, 
                self.context_manager, 
                self.cache_manager, 
                self.metrics_manager, 
                self.error_handler,
                memory_monitor=self.memory_monitor,
                system_monitor=self.system_monitor
            )
            await self._resource_manager.register_resource(
                "phase_three", 
                self.phase_three, 
                dependencies=["state_manager", "context_manager", "cache_manager", "metrics_manager", "error_handler"]
            )
            
            # Phase two depends on phase three and phase zero
            self.phase_two = PhaseTwo(
                self._event_queue, 
                self.state_manager, 
                self.context_manager, 
                self.cache_manager, 
                self.metrics_manager, 
                self.error_handler,
                self.phase_zero, 
                self.phase_three,
                memory_monitor=self.memory_monitor,
                system_monitor=self.system_monitor
            )
            await self._resource_manager.register_resource(
                "phase_two", 
                self.phase_two, 
                dependencies=["phase_zero", "phase_three"]
            )
            
            # Phase one depends on phase zero
            self.phase_one = PhaseOneOrchestrator(
                self._event_queue, 
                self.state_manager, 
                self.context_manager, 
                self.cache_manager, 
                self.metrics_manager, 
                self.error_handler, 
                error_recovery=self.error_recovery,
                phase_zero=self.phase_zero,
                health_tracker=self.health_tracker,
                memory_monitor=self.memory_monitor,
                system_monitor=self.system_monitor
            )
            await self._resource_manager.register_resource(
                "phase_one", 
                self.phase_one, 
                dependencies=["phase_zero"]
            )
            
            # Create orchestrator mediator to coordinate between display and phases
            self.main_orchestrator = MainOrchestrator(
                self.phase_zero, 
                self.phase_one, 
                self.phase_two, 
                self.phase_three
            )
            await self._resource_manager.register_resource(
                "main_orchestrator", 
                self.main_orchestrator, 
                dependencies=["phase_zero", "phase_one", "phase_two", "phase_three"]
            )
            
            # Initialize UI
            logger.info("Initializing UI")
            self.main_window = ForestDisplay(
                self._event_queue, 
                self.main_orchestrator, 
                self.system_monitor, 
                metrics_manager=self.metrics_manager
            )
            self.main_window.show()
            
            # Set up UI connections
            logger.info("Setting up UI connections")
            task = self.register_task(self._setup_ui_connections())
            
            # Set up event processing timer for UI thread
            self._setup_event_checks()
            
            # Emit success event for initialization
            await self._event_queue.emit(
                ResourceEventTypes.SYSTEM_HEALTH_CHANGED,
                {
                    "component": "system",
                    "status": "HEALTHY",
                    "description": "All components initialized successfully",
                    "correlation_id": correlation_id
                },
                correlation_id=correlation_id
            )
            
            self._initialized = True
            logger.info("ForestApplication async setup complete")
            
        except Exception as e:
            logger.error(f"Error in initialization: {e}", exc_info=True)
            self._handle_fatal_error("Initialization failed", e)
            raise
        
    def _setup_event_checks(self):
        """Set up periodic event checking from the UI thread with thread boundary enforcement."""
        # Store UI thread ID for boundary enforcement
        self._ui_thread_id = threading.get_ident()
        logger.info(f"UI thread initialized with ID: {self._ui_thread_id}")
        
        # Register UI thread with EventLoopManager for proper thread ownership
        from resources.events.loop_management import ThreadLocalEventLoopStorage
        try:
            loop = asyncio.get_event_loop()
            ThreadLocalEventLoopStorage.get_instance().set_loop(loop)
        except Exception as e:
            logger.warning(f"Could not register UI thread event loop: {e}")
        
        # Set up event processing timer
        self.event_timer = QTimer()
        self.event_timer.timeout.connect(self.check_events_queue)
        self.event_timer.start(100)
        
        # Set up monitoring timer for system health
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._update_system_monitoring)
        self.monitor_timer.start(5000)
        
        # Register UI-specific event types that should only be processed on the UI thread
        self._ui_event_types = set([
            "UI_UPDATE", "DISPLAY_REFRESH", "STATUS_UPDATE", "PROGRESS_UPDATE",
            "DIALOG_SHOW", "DIALOG_HIDE", "WINDOW_UPDATE"
        ])
        
    def check_events_queue(self):
        """Process events with thread boundary enforcement and better error handling"""
        # Verify we're running in the UI thread
        current_thread_id = threading.get_ident()
        if hasattr(self, '_ui_thread_id') and current_thread_id != self._ui_thread_id:
            logger.error(f"Event check called from wrong thread: {current_thread_id}, should be UI thread {self._ui_thread_id}")
            return
        
        # Early return if queue is not available or we're shutting down
        if not hasattr(self, '_event_queue') or (hasattr(self, 'async_helper') and self.async_helper.shutdown_requested):
            return
        
        # Process limited batch to prevent blocking UI
        max_events = 10
        events_processed = 0
        
        # Define high priority event types
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
                    # Get events with better error handling
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
        """Process a single event with thread boundary enforcement and error handling"""
        # Verify we're in the UI thread for events that must be processed there
        if hasattr(self, '_ui_thread_id') and hasattr(self, '_ui_event_types'):
            current_thread_id = threading.get_ident()
            
            # Check if this is a UI-specific event
            if event.event_type in self._ui_event_types and current_thread_id != self._ui_thread_id:
                logger.warning(f"UI event {event.event_type} being processed on non-UI thread {current_thread_id}")
                # Reschedule to UI thread via EventLoopManager if needed
                from resources.events.loop_management import EventLoopManager
                if hasattr(self, '_ui_thread_id'):
                    try:
                        loop = EventLoopManager.get_loop_for_thread(self._ui_thread_id)
                        if loop:
                            logger.debug(f"Rescheduling UI event {event.event_type} to UI thread")
                            EventLoopManager.run_coroutine_threadsafe(
                                self._process_ui_event(event),
                                target_loop=loop
                            )
                            return
                    except Exception as e:
                        logger.error(f"Failed to reschedule UI event: {e}")
        
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
    
    async def _process_ui_event(self, event):
        """Process a UI-specific event in the UI thread."""
        logger.debug(f"Processing UI event {event.event_type} in UI thread {threading.get_ident()}")
        try:
            # This method should only be called from the UI thread
            if not hasattr(self, '_ui_thread_id') or threading.get_ident() != self._ui_thread_id:
                logger.error(f"_process_ui_event called from wrong thread: {threading.get_ident()}")
                return
                
            # Process the event normally, but skip the thread check to avoid recursion
            event_type = event.event_type
            data = event.data
            
            # Handle UI event with appropriate handler
            handler_name = f"_handle_{event_type.lower()}"
            if hasattr(self, handler_name) and callable(getattr(self, handler_name)):
                handler = getattr(self, handler_name)
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, data)
                else:
                    handler(event_type, data)
            else:
                logger.warning(f"No handler found for UI event {event_type}")
        except Exception as e:
            logger.error(f"Error processing UI event {event.event_type}: {e}", exc_info=True)
    
    def _update_system_monitoring(self):
        """Update system monitoring from the UI thread."""
        # Skip if shutting down
        if hasattr(self, 'async_helper') and self.async_helper.shutdown_requested:
            return
            
        # Use the async helper to run monitoring in the background
        self.async_helper.run_coroutine(
            self._run_system_monitoring(),
            lambda result: logger.debug("System monitoring update completed"),
            lambda error: logger.error(f"Error in system monitoring update: {error}")
        )
    
    async def _run_system_monitoring(self):
        """Background task for system monitoring."""
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
        """Handle metric update events."""
        try:
            metric_name = data.get("metric")
            if metric_name and hasattr(self, 'main_window') and hasattr(self.main_window, 'system_metrics'):
                self.main_window.system_metrics.check_thresholds({
                    metric_name: data.get("value", 0)
                })
        except Exception as e:
            logger.error(f"Metric update error: {e}")
    
    async def _handle_system_flags(self, monitoring_result: Dict[str, Any]):
        """Handle system monitoring flags."""
        try:
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'system_metrics'):
                self.main_window.system_metrics.alert_widget.add_alert(
                    monitoring_result.get("severity", "WARNING"),
                    monitoring_result.get("message", "System flag raised")
                )
                
            if monitoring_result.get("requires_refinement") and hasattr(self, 'phase_one'):
                self.async_helper.run_coroutine(
                    self.phase_one.process_task(
                        "System refinement required",
                        monitoring_result
                    )
                )
        except Exception as e:
            logger.error(f"System flags handling error: {e}")
    
    async def _setup_ui_connections(self):
        """Set up UI event connections and subscriptions."""
        try:
            # Connect UI signals
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'timeline'):
                self.main_window.timeline.agent_selected.connect(self._handle_agent_selection)
            
            # Set up event subscriptions
            if hasattr(self, 'state_manager') and hasattr(self.state_manager, '_event_queue'):
                await self.state_manager._event_queue.subscribe(
                    ResourceEventTypes.ERROR_OCCURRED,
                    self.main_window._handle_error if hasattr(self, 'main_window') else None
                )
        except Exception as e:
            logger.error(f"Error setting up UI connections: {e}")
            # Don't raise the exception, just log it
    
    def _handle_agent_selection(self, agent_id: str):
        """Handle agent selection events from the UI."""
        try:
            agent_state = self.state_manager.get_state(f"agent:{agent_id}:state")
            if agent_state and hasattr(self, 'main_window') and hasattr(self.main_window, 'agent_metrics'):
                self.main_window.agent_metrics.update_metrics(agent_id)
        except Exception as e:
            logger.error(f"Agent selection error: {e}")
    
    def register_thread(self, thread):
        """Register a thread for tracking and cleanup with thread safety."""
        with self._thread_lock:
            self._threads.add(thread)
            
            # Set up callback for thread completion
            if hasattr(thread, 'finished_signal'):
                thread.finished_signal.connect(lambda: self._thread_finished(thread))
            elif hasattr(thread, 'finished'):
                thread.finished.connect(lambda: self._thread_finished(thread))
                
            # Track thread state for debugging
            if hasattr(thread, 'started'):
                thread.started.connect(lambda: logger.debug(f"Thread started: {thread}"))
                
            logger.debug(f"Registered thread: {thread}")
            return thread
    
    def _thread_finished(self, thread):
        """Handle thread completion with thread safety."""
        logger.debug(f"Thread finished: {thread}")
        with self._thread_lock:
            self._threads.discard(thread)
    
    def _stop_threads(self):
        """Stop all registered threads safely with improved timeout handling."""
        with self._thread_lock:
            thread_count = len(self._threads)
            if thread_count == 0:
                logger.debug("No threads to stop")
                return
                
            logger.info(f"Stopping {thread_count} threads...")
            
            # Make a copy to avoid modification during iteration
            threads_to_stop = list(self._threads)
            
        # First ask all threads to quit
        for thread in threads_to_stop:
            if hasattr(thread, 'isRunning') and thread.isRunning():
                logger.debug(f"Requesting thread to quit: {thread}")
                if hasattr(thread, 'quit'):
                    thread.quit()
                elif hasattr(thread, 'stop'):
                    thread.stop()
        
        # Then wait for them with a timeout, one by one with progress
        deadline = time.time() + 5.0  # 5 second total timeout
        remaining_threads = list(threads_to_stop)
        
        while remaining_threads and time.time() < deadline:
            for thread in list(remaining_threads):  # Use a copy for iteration
                # Check if the thread has finished
                if hasattr(thread, 'isRunning') and not thread.isRunning():
                    logger.debug(f"Thread stopped gracefully: {thread}")
                    remaining_threads.remove(thread)
                    continue
                    
                # Wait a bit more with decreasing time
                remaining_time = max(0.1, deadline - time.time())
                if hasattr(thread, 'wait') and thread.wait(int(remaining_time * 1000)):  # wait takes milliseconds
                    logger.debug(f"Thread stopped after waiting: {thread}")
                    remaining_threads.remove(thread)
            
            # Small sleep to prevent CPU spiking in this loop
            time.sleep(0.05)
        
        # Forcefully terminate any remaining threads, one by one with logging
        for thread in remaining_threads:
            logger.warning(f"Thread did not quit gracefully, terminating: {thread}")
            if hasattr(thread, 'terminate'):
                thread.terminate()
                
                # Small wait to allow the termination to take effect
                if hasattr(thread, 'wait'):
                    thread.wait(100)  # Wait 100ms
                    
        # Clear the thread set
        with self._thread_lock:
            self._threads.clear()
            
        logger.info("All threads stopped")
    
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
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            logger.warning("No running event loop during task creation, creating new one")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Create a task if needed
        if isinstance(coro, asyncio.Task):
            task = coro
        else:
            task = loop.create_task(coro)
        
        # Add task lifecycle management with thread safety
        def _on_task_complete(task):
            # Always remove the task from registry
            with self._tasks_lock:
                self._tasks.discard(task)
            
            # Call the original callback if provided
            if callback:
                try:
                    callback(task)
                except Exception as e:
                    logger.error(f"Error in task callback: {e}", exc_info=True)
        
        task.add_done_callback(_on_task_complete)
        
        # Add task to registry with thread safety
        with self._tasks_lock:
            self._tasks.add(task)
            
        return task
    
    def _cancel_tasks_sync(self):
        """Synchronously cancel all asyncio tasks with thread safety."""
        try:
            # Check if there's a running event loop first
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                logger.warning("No running event loop during task cancellation")
                with self._tasks_lock:
                    self._tasks.clear()  # Clear tasks since we can't cancel them properly
                return
                
            if not loop.is_running():
                logger.warning("Event loop is not running during task cancellation")
                with self._tasks_lock:
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
                with self._tasks_lock:
                    self._tasks.clear()
            except asyncio.CancelledError:
                logger.warning("Task cancellation was itself cancelled")
                with self._tasks_lock:
                    self._tasks.clear()
            except Exception as e:
                logger.error(f"Error cancelling tasks: {e}")
                # Last resort: clear task set
                with self._tasks_lock:
                    self._tasks.clear()
        except Exception as e:
            logger.error(f"Failed to cancel tasks: {e}", exc_info=True)
            # Last resort: clear task set
            with self._tasks_lock:
                self._tasks.clear()
    
    async def cancel_all_tasks(self):
        """Cancel all tasks with proper timeout and exception handling"""
        # Copy the tasks set to avoid modification during iteration
        with self._tasks_lock:
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
                        with self._tasks_lock:
                            for task in pending:
                                self._tasks.discard(task)
                except asyncio.CancelledError:
                    logger.warning("cancel_all_tasks was itself cancelled")
                    # Clear all tasks from the set to ensure clean shutdown
                    with self._tasks_lock:
                        self._tasks.clear()
                except Exception as e:
                    logger.error(f"Error waiting for tasks to cancel: {e}")
                    # Last resort: clear task set
                    with self._tasks_lock:
                        self._tasks.clear()
            
        logger.info("Task cancellation complete")
    
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
    
    def run(self):
        """Run the application main loop with proper setup and error handling."""
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
        """Set up signal handlers for graceful shutdown."""
        # For Unix-like systems, use asyncio's signal handling
        if hasattr(signal, 'SIGINT') and sys.platform != 'win32':
            try:
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
            except Exception as e:
                logger.warning(f"Error setting up signal handlers: {e}")
        else:
            # Fallback for Windows - use a timer for checking exit requests
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
        
        # 8. Shut down all resources in proper order
        try:
            # Use resource manager for orderly component shutdown
            if hasattr(self, '_resource_manager'):
                try:
                    logger.info("Initiating coordinated shutdown via ResourceManager")
                    if asyncio.get_event_loop().is_running():
                        future = asyncio.run_coroutine_threadsafe(
                            self._resource_manager.shutdown(),
                            asyncio.get_event_loop()
                        )
                        try:
                            future.result(timeout=15.0)
                            logger.info("ResourceManager shutdown completed successfully")
                        except concurrent.futures.TimeoutError:
                            logger.warning("Timeout during ResourceManager shutdown")
                        except Exception as e:
                            logger.error(f"Error during ResourceManager shutdown: {e}")
                except Exception as e:
                    logger.error(f"Error starting ResourceManager shutdown: {e}")
            
            # Use EventLoopManager to clean up any remaining registered resources
            try:
                from resources.events import EventLoopManager
                if asyncio.get_event_loop().is_running():
                    future = asyncio.run_coroutine_threadsafe(
                        EventLoopManager.cleanup_resources(),
                        asyncio.get_event_loop()
                    )
                    try:
                        future.result(timeout=10.0)
                        logger.info("EventLoopManager resources cleaned up successfully")
                    except concurrent.futures.TimeoutError:
                        logger.warning("Timeout while cleaning up resources")
                    except Exception as e:
                        logger.error(f"Error during resource cleanup: {e}")
            except Exception as e:
                logger.error(f"Error during EventLoopManager cleanup: {e}")
            
            # Close the event queue if it wasn't properly closed by resource manager
            if hasattr(self, '_event_queue'):
                try:
                    logger.info("Stopping event queue")
                    if hasattr(self._event_queue, 'stop'):
                        try:
                            if asyncio.get_event_loop().is_running():
                                future = asyncio.run_coroutine_threadsafe(
                                    self._event_queue.stop(), 
                                    asyncio.get_event_loop()
                                )
                                future.result(timeout=5.0)
                        except Exception as e:
                            logger.error(f"Error stopping event queue via event loop: {e}")
                    logger.info("Event queue stopped")
                except Exception as e:
                    logger.error(f"Error stopping event queue: {e}")
            
            # Stop the event processor thread if it wasn't stopped by resource manager
            if hasattr(self, '_event_processor') and self._event_processor:
                try:
                    logger.info("Stopping event processor thread")
                    self._event_processor.stop()
                    self._event_processor.join(timeout=5.0)
                    logger.info("Event processor thread stopped")
                except Exception as e:
                    logger.error(f"Error stopping event processor thread: {e}")
            
            logger.info("Application components shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
            # Continue with shutdown despite errors
        
        logger.info("Application shutdown complete")
    
    def _stop_all_timers(self):
        """Stop all QTimer instances safely."""
        logger.debug("Stopping all timers")
        
        # Explicitly stop event timer first
        if hasattr(self, 'event_timer') and self.event_timer.isActive():
            self.event_timer.stop()
        
        # Stop monitoring timer if exists
        if hasattr(self, 'monitor_timer') and self.monitor_timer.isActive():
            self.monitor_timer.stop()
        
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
            try:
                loop = asyncio.get_event_loop()
                for signame in ('SIGINT', 'SIGTERM'):
                    if hasattr(signal, signame):
                        try:
                            loop.remove_signal_handler(getattr(signal, signame))
                            logger.debug(f"Removed signal handler for {signame}")
                        except (NotImplementedError, ValueError, RuntimeError):
                            # Ignore if handler wasn't set or can't be removed
                            pass
            except Exception as e:
                logger.warning(f"Error removing signal handlers: {e}")
        
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
        
        return forest_app
    except Exception as e:
        logger.critical("Application failed to start", exc_info=True)
        QMessageBox.critical(None, "Startup Error", 
            f"The application failed to start:\n\n{str(e)}")
        if forest_app:
            forest_app.close()
        return None
    
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