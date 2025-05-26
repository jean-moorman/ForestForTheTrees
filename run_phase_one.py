#!/usr/bin/env python3
"""
Run Phase One Standalone Script

This script runs just the Phase One of the FFTT system, similar to main.py but without
the Phase Two dependencies. It includes the Earth agent for validation and the Water agent
for coordination between sequential agents.

It provides a complete GUI using display.py for testing Phase One functionality.
"""
import asyncio
import logging
import signal
import sys
import time
import threading
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

import qasync
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

# Import display for GUI
from display import ForestDisplay

# Import only Phase One components
from phase_one.orchestrator import PhaseOneOrchestrator
from phase_one_minimal_phase_zero import MinimalPhaseZeroOrchestrator
from resources.events import EventQueue
from resources.state import StateManager
from resources.managers import AgentContextManager, CacheManager, MetricsManager, ResourceCoordinator, CircuitBreakerRegistry
from resources.monitoring import SystemMonitor, MemoryMonitor, HealthTracker
from resources.errors import ErrorHandler
from system_error_recovery import SystemErrorRecovery

# Import agents directly to customize their initialization
from phase_one.agents.garden_planner import GardenPlannerAgent
from phase_one.agents.earth_agent import EarthAgent
from phase_one.agents.environmental_analysis import EnvironmentalAnalysisAgent
from phase_one.agents.root_system_architect import RootSystemArchitectAgent
from phase_one.agents.tree_placement_planner import TreePlacementPlannerAgent
from phase_one.workflow import PhaseOneWorkflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('run_phase_one.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PhaseOneInterface:
    """Interface for display to interact with Phase One Orchestrator."""
    
    def __init__(self, phase_one: PhaseOneOrchestrator):
        self.phase_one = phase_one
        self.logger = logging.getLogger(__name__)
        
    async def process_task(self, prompt: str) -> Dict[str, Any]:
        """Process task using Phase One orchestrator."""
        self.logger.info(f"Processing task: {prompt}")
        
        # Import our utility function
        from resources.events.utils import ensure_event_loop, ensure_async_execution
        
        try:
            # Ensure we have an event loop using our utility function
            ensure_event_loop()
            
            # Delegate to phase_one orchestrator with proper error handling
            try:
                # Use direct async execution for the process_task call
                result = await self.phase_one.process_task(prompt)
                
                # Return the result
                return {
                    "status": result.get("status", "unknown"),
                    "phase_one_outputs": result,
                    "message": f"Processed task through Phase One: {result.get('status', 'unknown')}"
                }
            except RuntimeError as e:
                if "no running event loop" in str(e):
                    self.logger.warning(f"No running event loop detected, using ensure_async_execution: {e}")
                    # Use our special executor for async operations in case of event loop issues
                    # This creates a new event loop if needed in a thread-safe way
                    result = ensure_async_execution(self.phase_one.process_task, prompt)
                    return {
                        "status": result.get("status", "unknown"),
                        "phase_one_outputs": result,
                        "message": f"Processed task through Phase One with fallback: {result.get('status', 'unknown')}"
                    }
                else:
                    # Re-raise other RuntimeErrors
                    raise
            except Exception as e:
                self.logger.error(f"Error in phase_one.process_task: {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": str(e),
                    "phase_one_outputs": {}
                }
                
        except Exception as e:
            self.logger.error(f"Error processing task: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "phase_one_outputs": {}
            }
            
    async def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get metrics for a specific agent."""
        self.logger.info(f"Getting metrics for agent: {agent_id}")
        
        # Import our utility function
        from resources.events.utils import ensure_event_loop, ensure_async_execution
        
        try:
            # Ensure we have an event loop using our utility function
            ensure_event_loop()
            
            try:
                # Delegate to phase_one for agent metrics directly
                return await self.phase_one.get_agent_metrics(agent_id)
            except RuntimeError as e:
                if "no running event loop" in str(e):
                    self.logger.warning(f"No running event loop detected for metrics, using ensure_async_execution: {e}")
                    # Use our special executor for async operations in case of event loop issues
                    return ensure_async_execution(self.phase_one.get_agent_metrics, agent_id)
                else:
                    # Re-raise other RuntimeErrors
                    raise
            except Exception as e:
                self.logger.error(f"Error getting agent metrics: {e}", exc_info=True)
                return {"status": "error", "message": str(e), "agent_id": agent_id}
        except Exception as e:
            self.logger.error(f"Error in get_agent_metrics: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "agent_id": agent_id}

class PhaseOneApp:
    """Application for running Phase One functionality."""
    
    def __init__(self):
        # Get existing QApplication or create one
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
            
        # Make sure we have a properly set up event loop first 
        from resources.events.utils import ensure_event_loop
        from resources.events.loop_management import EventLoopManager
        
        # Ensure we have a valid event loop in the main thread
        self.loop = ensure_event_loop()
        # Keep track of thread context for diagnostic purposes
        current_thread_id = threading.get_ident()
        is_main_thread = threading.current_thread() is threading.main_thread()
        logger.info(f"Initialized event loop {id(self.loop)} on {'main' if is_main_thread else 'worker'} thread {current_thread_id}")
        
        # Register this loop as primary if we're in the main thread
        if is_main_thread:
            primary_loop = EventLoopManager.get_primary_loop()
            if not primary_loop or id(primary_loop) != id(self.loop):
                result = EventLoopManager.set_primary_loop(self.loop)
                if result:
                    self._loop_registered_as_primary = True
                    logger.info(f"Registered application loop {id(self.loop)} as primary in main thread")
        
        # Initialize the event queue with proper event loop
        self.event_queue = EventQueue(queue_id="phase_one_queue")
        
        # Store the event loop ID that created the queue for diagnostics
        logger.info(f"EventQueue created with loop ID {self.event_queue._creation_loop_id} on thread {self.event_queue._loop_thread_id}")
        
        # Track tasks and resources
        self._tasks = set()
        self._initialized = False
        
    async def setup_async(self):
        """Initialize components that require the event loop."""
        if self._initialized:
            logger.info("Application already initialized")
            return
        
        # First try to use EventLoopManager if available
        try:
            from resources.events.loop_management import EventLoopManager
            self.loop = EventLoopManager.get_primary_loop() or EventLoopManager.ensure_event_loop()
            
            # If we're in the main thread, ensure this is the primary loop
            if threading.current_thread() is threading.main_thread() and not EventLoopManager.get_primary_loop():
                EventLoopManager.set_primary_loop(self.loop)
                
        except (ImportError, AttributeError):
            # Fall back to ensure_event_loop if EventLoopManager is not available
            from resources.events.utils import ensure_event_loop
            self.loop = ensure_event_loop()
        
        # Store thread context for diagnostics
        current_thread_id = threading.get_ident()
        is_main_thread = threading.current_thread() is threading.main_thread()
        logger.info(f"Using event loop {id(self.loop)} in {'main' if is_main_thread else 'worker'} thread {current_thread_id} for setup_async")
        
        # Make sure this loop is set as the current event loop
        asyncio.set_event_loop(self.loop)
        
        # Initialize health check tracking
        self._last_loop_health_check = time.time()
        self._healthcheck_timer = QTimer()
        self._healthcheck_timer.timeout.connect(self._check_event_loop_health)
        # Run health check every 30 seconds
        self._healthcheck_timer.start(30000)
        
        # Start the event queue with additional error handling
        logger.info("Starting the event queue")
        try:
            # We should NOT manually override the event queue's loop references
            # Let EventLoopManager handle the proper loop registration and tracking
            # This ensures the event queue uses the correct loop context throughout its lifecycle
            
            # Simply start the event queue and let it manage its own loop context
            # The EventQueue.start() method will use EventLoopManager.submit_to_resource_loop
            # to ensure it runs in the correct loop context
            await self.event_queue.start()
            logger.info(f"Event queue started successfully")
        except Exception as e:
            logger.error(f"Error starting event queue: {e}", exc_info=True)
            raise
        
        # Initialize centralized resource and circuit breaker coordinators
        logger.info("Initializing resource coordinator and circuit breaker registry")
        self.circuit_registry = CircuitBreakerRegistry(self.event_queue)
        self.resource_coordinator = ResourceCoordinator(self.event_queue)
        
        # Register all managers without explicitly initializing them individually
        logger.info("Registering resource managers with coordinator")
        
        # Core managers
        self.state_manager = StateManager(self.event_queue)
        self.resource_coordinator.register_manager("state_manager", self.state_manager)
        
        self.context_manager = AgentContextManager(self.event_queue)
        self.resource_coordinator.register_manager("context_manager", self.context_manager, 
                                                  dependencies=["state_manager"])
        
        self.cache_manager = CacheManager(self.event_queue)
        self.resource_coordinator.register_manager("cache_manager", self.cache_manager, 
                                                 dependencies=["state_manager"])
        
        self.metrics_manager = MetricsManager(self.event_queue)
        self.resource_coordinator.register_manager("metrics_manager", self.metrics_manager, 
                                                 dependencies=["state_manager"])
        
        self.error_handler = ErrorHandler(self.event_queue)
        self.resource_coordinator.register_manager("error_handler", self.error_handler, 
                                                 dependencies=["state_manager"])
        
        # Monitoring managers
        self.memory_monitor = MemoryMonitor(self.event_queue)
        self.resource_coordinator.register_manager("memory_monitor", self.memory_monitor)
        
        self.health_tracker = HealthTracker(self.event_queue)
        self.resource_coordinator.register_manager("health_tracker", self.health_tracker)
        
        self.system_monitor = SystemMonitor(self.event_queue, self.memory_monitor, self.health_tracker)
        self.resource_coordinator.register_manager("system_monitor", self.system_monitor, 
                                                 dependencies=["memory_monitor", "health_tracker"])
        
        # Error recovery manager
        self.error_recovery = SystemErrorRecovery(self.event_queue, self.health_tracker)
        self.resource_coordinator.register_manager("error_recovery", self.error_recovery, 
                                                 dependencies=["state_manager", "health_tracker"])
        
        # Initialize all components in dependency order using the centralized coordinator
        logger.info("Starting coordinated initialization of all components")
        try:
            # Call initialize_all() directly and await it
            # Don't create a separate variable for the coroutine to avoid trying to await it twice
            await self.resource_coordinator.initialize_all()
        except Exception as e:
            logger.error(f"Error during resource initialization: {e}", exc_info=True)
            raise
        
        # Initialize Minimal Phase Zero orchestrator 
        logger.info("Initializing Minimal Phase Zero orchestrator")
        self.phase_zero = MinimalPhaseZeroOrchestrator(
            self.event_queue,
            self.state_manager,
            self.context_manager,
            self.cache_manager,
            self.metrics_manager,
            self.error_handler,
            health_tracker=self.health_tracker,
            memory_monitor=self.memory_monitor,
            system_monitor=self.system_monitor
        )
        
        # Initialize Phase One agents and workflow manually instead of using the PhaseOneOrchestrator directly
        logger.info("Initializing Phase One agents and workflow")
        try:
            # Initialize agents with necessary parameters
            garden_planner = GardenPlannerAgent(
                "garden_planner",
                self.event_queue,
                self.state_manager,
                self.context_manager,
                self.cache_manager,
                self.metrics_manager,
                self.error_handler,
                self.memory_monitor,
                self.health_tracker
            )
            
            earth_agent = EarthAgent(
                "earth_agent",
                self.event_queue,
                self.state_manager,
                self.context_manager,
                self.cache_manager,
                self.metrics_manager,
                self.error_handler,
                self.memory_monitor,
                self.health_tracker
            )
            
            env_analysis = EnvironmentalAnalysisAgent(
                "environmental_analysis",
                self.event_queue,
                self.state_manager,
                self.context_manager,
                self.cache_manager,
                self.metrics_manager,
                self.error_handler,
                self.memory_monitor,
                self.health_tracker
            )
            
            root_system = RootSystemArchitectAgent(
                "root_system_architect",
                self.event_queue,
                self.state_manager,
                self.context_manager,
                self.cache_manager,
                self.metrics_manager,
                self.error_handler,
                self.memory_monitor,
                self.health_tracker
            )
            
            tree_placement = TreePlacementPlannerAgent(
                "tree_placement_planner",
                self.event_queue,
                self.state_manager,
                self.context_manager,
                self.cache_manager,
                self.metrics_manager,
                self.error_handler,
                self.memory_monitor,
                self.health_tracker
            )
            
            # Create workflow
            workflow = PhaseOneWorkflow(
                garden_planner,
                earth_agent,
                env_analysis,
                root_system,
                tree_placement,
                self.event_queue,
                self.state_manager
            )
            
            # Initialize Phase One orchestrator
            logger.info("Initializing Phase One orchestrator with pre-initialized agents")
            self.phase_one = PhaseOneOrchestrator(
                self.event_queue,
                self.state_manager,
                self.context_manager,
                self.cache_manager,
                self.metrics_manager,
                self.error_handler,
                error_recovery=self.error_recovery,
                phase_zero=self.phase_zero,
                health_tracker=self.health_tracker,
                memory_monitor=self.memory_monitor,
                system_monitor=self.system_monitor,
                # Pass pre-initialized agents and workflow
                garden_planner_agent=garden_planner,
                earth_agent=earth_agent,
                environmental_analysis_agent=env_analysis,
                root_system_architect_agent=root_system,
                tree_placement_planner_agent=tree_placement,
                workflow=workflow
            )
        except Exception as e:
            logger.error(f"Error initializing Phase One orchestrator: {e}", exc_info=True)
            raise
        
        # Create the interface for display
        self.phase_one_interface = PhaseOneInterface(self.phase_one)
        
        # Initialize UI
        logger.info("Initializing UI")
        self.main_window = ForestDisplay(
            self.event_queue,
            self.phase_one_interface,
            self.system_monitor
        )
        self.main_window.show()
        
        # Setup event processing timer
        self.event_timer = QTimer()
        self.event_timer.timeout.connect(self.check_events_queue)
        self.event_timer.start(100)
        
        self._initialized = True
        logger.info("Phase One App setup complete")
        
    def check_events_queue(self):
        """Process events from the queue with improved error handling."""
        global APPLICATION_MAIN_LOOP
        
        # Early return if queue is not available
        if not hasattr(self, 'event_queue'):
            return
            
        # Process limited batch to prevent blocking UI
        max_events = 10
        events_processed = 0
        
        try:
            # Import event loop utilities
            from resources.events.utils import ensure_event_loop
            from resources.events.loop_management import EventLoopManager
            
            # Use our updated ensure_event_loop utility, which will maintain
            # consistent event loop usage across threads and processes
            loop = ensure_event_loop()
            self._persistent_loop = loop
            
            # Log with clear thread context
            current_thread_id = threading.get_ident()
            is_main_thread = threading.current_thread() is threading.main_thread()
            logger.debug(f"Using event loop {id(loop)} in {'main' if is_main_thread else 'worker'} thread {current_thread_id}")
            
            # Register the loop with EventLoopManager if we're in the main thread
            if is_main_thread and not hasattr(self, '_loop_registered_as_primary'):
                primary_loop = EventLoopManager.get_primary_loop()
                
                # If no primary loop exists or it's different than our current loop, set this as primary
                if not primary_loop or id(primary_loop) != id(loop):
                    result = EventLoopManager.set_primary_loop(loop)
                    if result:
                        self._loop_registered_as_primary = True
                        logger.info(f"Registered loop {id(loop)} as primary in main thread {current_thread_id}")
                else:
                    # Already registered
                    self._loop_registered_as_primary = True
            
            # Get a reference to the current loop
            loop = self._persistent_loop
            
            # With our new implementation, the event queue has its own dedicated thread and loop
            # We should NOT manually update its loop reference, as that will break the queue's processing
            # The code below is commented out to prevent breaking the queue's dedicated thread/loop model
            
            # REMOVED: This was causing issues by forcing the event queue to use the main thread's loop
            # when it should be using its own dedicated thread's loop
            #if hasattr(self.event_queue, '_creation_loop_id'):
            #    if self.event_queue._creation_loop_id != id(loop):
            #        logger.warning(f"Fixing event queue loop reference from {self.event_queue._creation_loop_id} to {id(loop)}")
            #        self.event_queue._creation_loop_id = id(loop)
            #        self.event_queue._loop_thread_id = threading.get_ident()
            
            # Process events with enhanced error handling
            while events_processed < max_events:
                # Use get_nowait to avoid blocking the UI thread
                try:
                    # Ensure we're using the persistent loop
                    asyncio.set_event_loop(self._persistent_loop)
                    
                    # Get event from queue with proper error handling
                    try:
                        event = self.event_queue.get_nowait()
                    except (RuntimeError, AttributeError) as e:
                        error_msg = str(e).lower()
                        if "no running event loop" in error_msg or "has no attribute" in error_msg or "different event loop" in error_msg:
                            # Handle issues with event loop
                            logger.warning(f"Event loop issue detected: {error_msg}")
                            # Ensure we have a valid loop and update the event queue
                            loop = ensure_event_loop()
                            self._persistent_loop = loop
                            asyncio.set_event_loop(loop)
                            
                            # REMOVED: This was causing issues by forcing the event queue to use the main thread's loop
                            # With our new implementation, the event queue has its own dedicated thread and loop
                            # We should NOT manually update its loop reference
                            # self.event_queue._creation_loop_id = id(loop)
                            # self.event_queue._loop_thread_id = threading.get_ident()
                            
                            # Try one more time
                            try:
                                event = self.event_queue.get_nowait()
                            except asyncio.QueueEmpty:
                                # No events to process
                                break
                        else:
                            raise
                            
                    if not event:
                        break
                        
                    events_processed += 1
                    # Process the event (simplified for testing)
                    logger.debug(f"Processing event: {event.event_type}")
                except asyncio.QueueEmpty:
                    # No more events to process
                    break
                except Exception as e:
                    logger.error(f"Error getting event: {e}")
                    # Don't break immediately on error - continue to process events if possible
                    if events_processed == 0:  # Only break if we haven't processed any events
                        break
                        
            # Schedule another check if we processed the maximum number of events
            # This ensures we continue processing if there are more events
            if events_processed >= max_events:
                QTimer.singleShot(0, self.check_events_queue)
                
        except Exception as e:
            logger.error(f"Event processing error: {e}", exc_info=True)
            # Re-schedule event check after a short delay to recover from errors
            QTimer.singleShot(100, self.check_events_queue)
            
    def register_task(self, coro):
        """Register and track an asyncio task with improved event loop handling."""
        try:
            # Try to get the running loop
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, get or create one
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop in this thread, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                logger.info(f"Created new event loop in thread {threading.get_ident()}")
        
        if isinstance(coro, asyncio.Task):
            task = coro
        else:
            task = loop.create_task(coro)
            
        # Add task lifecycle management
        def _on_task_complete(task):
            self._tasks.discard(task)
            # Check health after task completion
            if hasattr(self, "_last_loop_health_check") and time.time() - self._last_loop_health_check > 10:
                self._check_event_loop_health()
        
        task.add_done_callback(_on_task_complete)
        self._tasks.add(task)
        return task
        
    def _check_event_loop_health(self):
        """Perform health check on the event loop."""
        try:
            self._last_loop_health_check = time.time()
            current_thread = threading.get_ident()
            
            # Try to get the current event loop
            try:
                loop = asyncio.get_running_loop()
                loop_status = "running"
            except RuntimeError:
                try:
                    loop = asyncio.get_event_loop()
                    loop_status = "available"
                except RuntimeError:
                    logger.warning(f"No event loop available in thread {current_thread}")
                    # Create a new event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop_status = "created"
                    logger.info(f"Created new event loop in thread {current_thread} during health check")
            
            # Check if loop is closed
            if loop.is_closed():
                logger.warning(f"Event loop is closed in thread {current_thread}, creating new one")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop_status = "recreated"
            
            # Check number of pending tasks
            try:
                pending_tasks = len(asyncio.all_tasks(loop))
            except RuntimeError:
                pending_tasks = len(self._tasks)
                
            logger.debug(f"Event loop health: status={loop_status}, thread={current_thread}, "
                        f"pending_tasks={pending_tasks}, app_tasks={len(self._tasks)}")
            
            # Ensure event queue has a valid loop
            if hasattr(self, 'event_queue'):
                if not hasattr(self.event_queue, '_creation_loop_id') or not hasattr(self.event_queue, '_loop_thread_id'):
                    logger.warning("Event queue missing loop context attributes")
                elif self.event_queue._creation_loop_id != id(loop) or self.event_queue._loop_thread_id != current_thread:
                    logger.debug(f"Event queue loop mismatch: queue={self.event_queue._creation_loop_id}/{self.event_queue._loop_thread_id}, "
                                f"current={id(loop)}/{current_thread}")
            
            return {
                "status": loop_status,
                "thread_id": current_thread,
                "loop_id": id(loop),
                "pending_tasks": pending_tasks,
                "app_tasks": len(self._tasks),
                "timestamp": time.time()
            }
                
        except Exception as e:
            logger.error(f"Error checking event loop health: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
        
    def run(self):
        """Run the application main loop."""
        try:
            # Show the main window
            if hasattr(self, 'main_window') and not self.main_window.isVisible():
                self.main_window.show()
                
            # Make sure the event timer is running
            if hasattr(self, 'event_timer') and not self.event_timer.isActive():
                self.event_timer.start(100)
                
            # Setup signal handlers
            self._setup_signal_handlers()
            
            # Set up exception hook
            sys.excepthook = self._global_exception_handler
            
            # Run the Qt event loop
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
        """Set up signal handlers for clean shutdown."""
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
                        signal.signal(
                            getattr(signal, signame),
                            lambda signum, frame, signame=signame: self._handle_signal(signame)
                        )
                        logger.debug(f"Added fallback signal handler for {signame}")
                        
    def _handle_signal(self, signame):
        """Handle a signal in the main thread safely."""
        logger.info(f"Received signal {signame}, initiating shutdown")
        # Schedule the app to quit safely from the main thread
        QTimer.singleShot(0, self.app.quit)
        
    def _global_exception_handler(self, exc_type, exc_value, exc_traceback):
        """Global exception handler for unhandled exceptions."""
        # Skip for KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            logger.info("Keyboard interrupt received")
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        # Log the exception
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.critical(f"Unhandled exception: {error_msg}")
        
        # Show error dialog
        self._show_error_dialog("Unhandled Exception", error_msg)
        
    def _show_error_dialog(self, title, message):
        """Show an error dialog safely from the main thread."""
        if hasattr(self, 'main_window') and self.main_window is not None:
            QMessageBox.critical(self.main_window, title, message)
        else:
            QMessageBox.critical(None, title, message)
            
    def _handle_fatal_error(self, context: str, error: Exception):
        """Handle fatal errors with improved diagnostics and cleanup."""
        # Format traceback
        tb = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        error_msg = f"{context}:\n\n{tb}"
        
        # Log the error
        logger.critical(error_msg)
        
        # Show message box
        QMessageBox.critical(
            None,
            "Fatal Error",
            f"A fatal error has occurred:\n\n{error}\n\nThe application will now exit."
        )
        
        # Force exit on fatal errors
        sys.exit(1)
        
    def close(self):
        """Clean up resources in the correct sequence."""
        logger.info("Application shutdown initiated")
        
        # Stop all timers
        if hasattr(self, 'event_timer') and self.event_timer.isActive():
            self.event_timer.stop()
            
        # Stop health check timer
        if hasattr(self, '_healthcheck_timer') and self._healthcheck_timer.isActive():
            self._healthcheck_timer.stop()
            
        # Process pending Qt events
        self.app.processEvents()
        
        # Cancel all async tasks
        for task in list(self._tasks):
            if not task.done() and not task.cancelled():
                task.cancel()
                
        # Cleanup Phase One orchestrator
        if hasattr(self, 'phase_one'):
            try:
                # Try to get a valid event loop
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        # Create a new event loop if needed
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                # Check if loop is running, if not, run it in new thread to process coroutines
                if not loop.is_running():
                    # Create a new thread to run the shutdown coroutine
                    def run_shutdown():
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.phase_one.shutdown())
                        
                    shutdown_thread = threading.Thread(target=run_shutdown)
                    shutdown_thread.daemon = True
                    shutdown_thread.start()
                    shutdown_thread.join(timeout=5.0)
                else:
                    # Use run_coroutine_threadsafe for running loop
                    future = asyncio.run_coroutine_threadsafe(
                        self.phase_one.shutdown(),
                        loop
                    )
                    future.result(timeout=5.0)
            except Exception as e:
                logger.error(f"Error shutting down Phase One: {e}", exc_info=True)
                
        # Cleanup UI components
        if hasattr(self, 'main_window'):
            try:
                self.main_window.close()
            except Exception as e:
                logger.error(f"Error closing main window: {e}")
                
        # Shutdown event queue last
        if hasattr(self, 'event_queue'):
            try:
                # Try to get a valid event loop
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        # Create a new event loop if needed
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                # Check if loop is running, if not, run it in new thread to process coroutines
                if not loop.is_running():
                    # Create a new thread to run the stop coroutine
                    def run_stop():
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.event_queue.stop())
                        
                    stop_thread = threading.Thread(target=run_stop)
                    stop_thread.daemon = True
                    stop_thread.start()
                    stop_thread.join(timeout=5.0)
                else:
                    # Use run_coroutine_threadsafe for running loop
                    future = asyncio.run_coroutine_threadsafe(
                        self.event_queue.stop(),
                        loop
                    )
                    future.result(timeout=5.0)
            except Exception as e:
                logger.error(f"Error stopping event queue: {e}", exc_info=True)
                
        logger.info("Application shutdown complete")

async def main():
    """Main function to initialize and run the application."""
    # Use the global variable without declaring it again
    phase_one_app = None
    try:
        # The event loop should already be set up by qasync
        loop = asyncio.get_event_loop()
        logger.info(f"Main function running in event loop {id(loop)}")
        
        # Ensure loop is available globally and through EventLoopManager
        global APPLICATION_MAIN_LOOP
        if APPLICATION_MAIN_LOOP is None:
            APPLICATION_MAIN_LOOP = loop
            
        # Register with EventLoopManager for consistent access
        from resources.events.loop_management import EventLoopManager
        result = EventLoopManager.set_primary_loop(loop)
        logger.info(f"Registered event loop with EventLoopManager in main(): {result}")
        
        # Create the application instance with deferred initialization
        phase_one_app = PhaseOneApp()
        
        # Store loop reference in the app
        phase_one_app.loop = loop
        phase_one_app.main_loop = loop
        
        # Now perform async initialization
        logger.info("Running setup_async")
        await phase_one_app.setup_async()
        
        # Configure the main window's async components
        logger.info("Setting up main window async components")
        if hasattr(phase_one_app, 'main_window') and hasattr(phase_one_app.main_window, 'setup_async'):
            await phase_one_app.main_window.setup_async()
            
        return phase_one_app
    except Exception as e:
        logger.critical("Application failed to start", exc_info=True)
        QMessageBox.critical(None, "Startup Error", 
            f"The application failed to start:\n\n{str(e)}")
        if phase_one_app:
            phase_one_app.close()
        return None

# Global reference to main application event loop
APPLICATION_MAIN_LOOP = None

if __name__ == "__main__":
    try:
        # Create the Qt application
        app = QApplication.instance() or QApplication(sys.argv)
        app._is_running = False  # Add flag to track event loop state
        
        # Configure qasync
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        logger.info(f"Created qasync event loop: {id(loop)}")
        
        # Store the loop in the global variable for consistent access
        APPLICATION_MAIN_LOOP = loop
        
        # Register with EventLoopManager for consistent access
        from resources.events.loop_management import EventLoopManager
        result = EventLoopManager.set_primary_loop(loop)
        logger.info(f"Registered main event loop with EventLoopManager: {result}")
        
        # Initialize the phase_one_app variable
        phase_one_app = None
        
        # Run the application with proper cleanup
        with loop:
            try:
                # Initialize the application
                logger.info("Running main() to initialize application")
                phase_one_app = loop.run_until_complete(main())
                
                if phase_one_app:
                    # Replace the exception hook with the application's version
                    sys.excepthook = phase_one_app._global_exception_handler
                    
                    # Start the application
                    logger.info("Starting application main loop")
                    exit_code = phase_one_app.run()
                else:
                    logger.error("Application initialization failed")
                    exit_code = 1
            finally:
                # Clean up properly
                if phase_one_app:
                    try:
                        logger.info("Closing application")
                        phase_one_app.close()
                    except Exception as e:
                        logger.error(f"Error during application cleanup: {e}", exc_info=True)
                        
        # Final cleanup
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