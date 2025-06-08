"""
Phase One Standalone Runner

This script mimics the functionality of main.py but focuses exclusively on Phase One,
allowing for testing and development of Phase One features without dependencies on
Phase Two or other incomplete components.

This includes:
- Garden Planner agent with Earth agent validation
- Environmental Analysis agent
- Root System Architect agent 
- Tree Placement Planner agent
- Water Agent coordination between sequential agents
"""
import asyncio
import logging
import signal
import sys
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

import qasync
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer, pyqtSignal, pyqtSlot

# Import display for GUI
from display import ForestDisplay

# Import only Phase One components
from phase_one import PhaseOneOrchestrator
from phase_one.agents.garden_planner import GardenPlannerAgent
from phase_one.agents.earth_agent import EarthAgent
from phase_one.agents.environmental_analysis import EnvironmentalAnalysisAgent
from phase_one.agents.root_system_architect import RootSystemArchitectAgent
from phase_one.agents.tree_placement_planner import TreePlacementPlannerAgent
from phase_one.workflow import PhaseOneWorkflow
from phase_one_minimal_phase_zero import MinimalPhaseZeroOrchestrator
from resources.events import EventQueue
from resources.state import StateManager
from resources.managers import AgentContextManager, CacheManager, MetricsManager, ResourceCoordinator, CircuitBreakerRegistry
from resources.monitoring import SystemMonitor, MemoryMonitor, HealthTracker
from resources.errors import ErrorHandler
from system_error_recovery import SystemErrorRecovery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase_one_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PhaseOneTestInterface:
    """Interface for display to interact with Phase One Orchestrator."""
    
    def __init__(self, phase_one: PhaseOneOrchestrator):
        self.phase_one = phase_one
        self.logger = logging.getLogger(__name__)
        
    async def process_task(self, prompt: str) -> Dict[str, Any]:
        """Process task using Phase One orchestrator."""
        self.logger.info(f"Processing task: {prompt}")
        try:
            # Delegate to phase_one orchestrator
            result = await self.phase_one.process_task(prompt)
            
            # Return the result
            return {
                "status": result.get("status", "unknown"),
                "phase_one_outputs": result,
                "message": f"Processed task through Phase One: {result.get('status', 'unknown')}"
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
        try:
            # Delegate to phase_one for agent metrics
            return await self.phase_one.get_agent_metrics(agent_id)
        except Exception as e:
            self.logger.error(f"Error getting agent metrics: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "agent_id": agent_id}

class PhaseOneTestApp:
    """Application for testing Phase One functionality."""
    
    def __init__(self):
        # Get existing QApplication or create one
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
            
        # Initialize the event queue
        self.event_queue = EventQueue(queue_id="phase_one_test_queue")
        
        # Track tasks and resources
        self._tasks = set()
        self._initialized = False
        
    async def setup_async(self):
        """Initialize components that require the event loop."""
        if self._initialized:
            logger.info("Application already initialized")
            return
            
        # Start the event queue
        logger.info("Starting the event queue")
        await self.event_queue.start()
        
        # Initialize centralized resource and circuit breaker coordinators
        logger.info("Initializing resource coordinator and circuit breaker registry")
        self.circuit_registry = CircuitBreakerRegistry(self.event_queue)
        self.resource_coordinator = ResourceCoordinator(self.event_queue)
        
        # Initialize state manager first (fundamental component)
        logger.info("Initializing resource managers")
        self.state_manager = StateManager(self.event_queue)
        
        # Register resource manager with coordinator as a core component with no dependencies
        self.resource_coordinator.register_manager("state_manager", self.state_manager)
        
        # Initialize remaining managers
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
        
        # Initialize monitoring components
        logger.info("Initializing monitoring components")
        self.memory_monitor = MemoryMonitor(self.event_queue)
        self.resource_coordinator.register_manager("memory_monitor", self.memory_monitor)
        
        self.health_tracker = HealthTracker(self.event_queue)
        self.resource_coordinator.register_manager("health_tracker", self.health_tracker)
        
        self.system_monitor = SystemMonitor(self.event_queue, self.memory_monitor, self.health_tracker)
        self.resource_coordinator.register_manager("system_monitor", self.system_monitor, 
                                                 dependencies=["memory_monitor", "health_tracker"])
        
        # Initialize error recovery
        self.error_recovery = SystemErrorRecovery(self.event_queue, self.health_tracker)
        self.resource_coordinator.register_manager("error_recovery", self.error_recovery, 
                                                 dependencies=["state_manager", "health_tracker"])
        
        # Initialize all components in dependency order
        logger.info("Starting coordinated initialization of all components")
        # Don't await here to avoid task nesting issue
        initialize_task = self.resource_coordinator.initialize_all()
        self.register_task(initialize_task)
        
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
        
        # Create a subclass of PhaseOneOrchestrator to fix the agent initialization
        class FixedPhaseOneOrchestrator(PhaseOneOrchestrator):
            def _initialize_agents_and_workflow(self) -> None:
                """Initialize all Phase One agents and workflow with proper agent_id."""
                # Garden Planner Agent
                self.garden_planner_agent = GardenPlannerAgent(
                    "garden_planner",  # Add agent_id
                    self._event_queue,
                    self._state_manager,
                    self._context_manager,
                    self._cache_manager,
                    self._metrics_manager,
                    self._error_handler,
                    self._memory_monitor,
                    health_tracker=self._health_tracker
                )
                
                # Earth Agent for validation
                self.earth_agent = EarthAgent(
                    "earth_agent",  # Add agent_id
                    self._event_queue,
                    self._state_manager,
                    self._context_manager,
                    self._cache_manager,
                    self._metrics_manager,
                    self._error_handler,
                    self._memory_monitor,
                    health_tracker=self._health_tracker
                )
                
                # Environmental Analysis Agent
                self.environmental_analysis_agent = EnvironmentalAnalysisAgent(
                    "environmental_analysis",  # Add agent_id
                    self._event_queue,
                    self._state_manager,
                    self._context_manager,
                    self._cache_manager,
                    self._metrics_manager,
                    self._error_handler,
                    self._memory_monitor,
                    health_tracker=self._health_tracker
                )
                
                # Root System Architect Agent
                self.root_system_architect_agent = RootSystemArchitectAgent(
                    "root_system_architect",  # Add agent_id
                    self._event_queue,
                    self._state_manager,
                    self._context_manager,
                    self._cache_manager,
                    self._metrics_manager,
                    self._error_handler,
                    self._memory_monitor,
                    health_tracker=self._health_tracker
                )
                
                # Tree Placement Planner Agent
                self.tree_placement_planner_agent = TreePlacementPlannerAgent(
                    "tree_placement_planner",  # Add agent_id
                    self._event_queue,
                    self._state_manager,
                    self._context_manager,
                    self._cache_manager,
                    self._metrics_manager,
                    self._error_handler,
                    self._memory_monitor,
                    health_tracker=self._health_tracker
                )
                
                # Initialize Phase One Workflow
                self.phase_one_workflow = PhaseOneWorkflow(
                    self.garden_planner_agent,
                    self.earth_agent,
                    self.environmental_analysis_agent,
                    self.root_system_architect_agent,
                    self.tree_placement_planner_agent,
                    self._event_queue,
                    self._state_manager,
                    max_earth_validation_cycles=self._max_validation_cycles,
                    validation_timeout=self._validation_timeout
                )
        
        # Initialize Phase One orchestrator 
        logger.info("Initializing Phase One orchestrator")
        try:
            # Use our fixed orchestrator class
            self.phase_one = FixedPhaseOneOrchestrator(
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
                system_monitor=self.system_monitor
            )
        except Exception as e:
            logger.error(f"Error initializing Phase One orchestrator: {e}", exc_info=True)
            raise
        
        # Create the interface for display
        self.phase_one_interface = PhaseOneTestInterface(self.phase_one)
        
        # Initialize UI
        logger.info("Initializing UI")
        self.main_window = ForestDisplay(
            self.event_queue,
            self.phase_one_interface,
            self.system_monitor,
            metrics_manager=self.metrics_manager
        )
        self.main_window.show()
        
        # Setup event processing timer
        self.event_timer = QTimer()
        self.event_timer.timeout.connect(self.check_events_queue)
        self.event_timer.start(100)
        
        self._initialized = True
        logger.info("Phase One Test App setup complete")
        
    def check_events_queue(self):
        """Process events from the queue."""
        # Early return if queue is not available
        if not hasattr(self, 'event_queue'):
            return
            
        # Process limited batch to prevent blocking UI
        max_events = 10
        events_processed = 0
        
        try:
            while events_processed < max_events:
                try:
                    event = self.event_queue.get_nowait()
                    if not event:
                        break
                        
                    events_processed += 1
                    # Process the event (simplified for testing)
                    logger.debug(f"Processing event: {event.event_type}")
                except asyncio.QueueEmpty:
                    break
                except Exception as e:
                    logger.error(f"Error getting event: {e}")
                    break
                    
            # Schedule another check if needed
            if events_processed >= max_events:
                QTimer.singleShot(0, self.check_events_queue)
                
        except Exception as e:
            logger.error(f"Event processing error: {e}", exc_info=True)
            
    def register_task(self, coro):
        """Register and track an asyncio task."""
        loop = asyncio.get_event_loop()
        
        if isinstance(coro, asyncio.Task):
            task = coro
        else:
            task = loop.create_task(coro)
            
        # Add task lifecycle management
        def _on_task_complete(task):
            self._tasks.discard(task)
        
        task.add_done_callback(_on_task_complete)
        self._tasks.add(task)
        return task
        
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
            
        # Process pending Qt events
        self.app.processEvents()
        
        # Cancel all async tasks
        for task in list(self._tasks):
            if not task.done() and not task.cancelled():
                task.cancel()
                
        # Cleanup Phase One orchestrator
        if hasattr(self, 'phase_one'):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(
                        self.phase_one.shutdown(),
                        loop
                    )
                    future.result(timeout=5.0)
            except Exception as e:
                logger.error(f"Error shutting down Phase One: {e}")
                
        # Cleanup UI components
        if hasattr(self, 'main_window'):
            try:
                self.main_window.close()
            except Exception as e:
                logger.error(f"Error closing main window: {e}")
                
        # Shutdown event queue last
        if hasattr(self, 'event_queue'):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(
                        self.event_queue.stop(),
                        loop
                    )
                    future.result(timeout=5.0)
            except Exception as e:
                logger.error(f"Error stopping event queue: {e}")
                
        logger.info("Application shutdown complete")

async def main():
    """Main function to initialize and run the application."""
    phase_one_app = None
    try:
        # The event loop should already be set up by qasync
        loop = asyncio.get_event_loop()
        logger.info(f"Main function running in event loop {id(loop)}")
        
        # Create the application instance with deferred initialization
        phase_one_app = PhaseOneTestApp()
        
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

if __name__ == "__main__":
    try:
        # Create the Qt application
        app = QApplication.instance() or QApplication(sys.argv)
        app._is_running = False  # Add flag to track event loop state
        
        # Configure qasync
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        logger.info(f"Created qasync event loop: {id(loop)}")
        
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