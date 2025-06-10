"""
Application Lifecycle Management for Phase One GUI

Handles initialization, setup, and shutdown sequences for the Phase One application,
including resource coordination and dependency management.
"""

import asyncio
import logging
import threading
import time

from resources.events import EventQueue
from resources.state import StateManager
from resources.managers import AgentContextManager, CacheManager, MetricsManager, ResourceCoordinator, CircuitBreakerRegistry
from resources.monitoring import SystemMonitor, MemoryMonitor, HealthTracker
from resources.errors import ErrorHandler
from system_error_recovery import SystemErrorRecovery
from phase_one_minimal_phase_zero import MinimalPhaseZeroOrchestrator

# Import Phase One components
from phase_one.agents.garden_planner import GardenPlannerAgent
from phase_one.agents.earth_agent import EarthAgent
from phase_one.agents.environmental_analysis import EnvironmentalAnalysisAgent
from phase_one.agents.root_system_architect import RootSystemArchitectAgent
from phase_one.agents.tree_placement_planner import TreePlacementPlannerAgent
from phase_one.workflow import PhaseOneWorkflow
from phase_one.orchestrator import PhaseOneOrchestrator

# Import display
from display import ForestDisplay

logger = logging.getLogger(__name__)


class LifecycleManager:
    """Manages the complete lifecycle of the Phase One application."""
    
    def __init__(self, app_instance):
        self.app = app_instance
        self._initialized = False
        
    async def setup_async(self):
        """Initialize components that require the event loop."""
        if self._initialized:
            logger.info("Application already initialized")
            return
        
        # Use existing event loop from event manager
        try:
            from resources.events.loop_management import EventLoopManager
            self.app.loop = EventLoopManager.get_primary_loop() or EventLoopManager.ensure_event_loop()
            
            # If we're in the main thread, ensure this is the primary loop
            if threading.current_thread() is threading.main_thread() and not EventLoopManager.get_primary_loop():
                EventLoopManager.set_primary_loop(self.app.loop)
                
        except (ImportError, AttributeError):
            # Fall back to ensure_event_loop if EventLoopManager is not available
            from resources.events.utils import ensure_event_loop, run_async_in_thread
            self.app.loop = ensure_event_loop()
        
        # Store thread context for diagnostics
        current_thread_id = threading.get_ident()
        is_main_thread = threading.current_thread() is threading.main_thread()
        logger.info(f"Using event loop {id(self.app.loop)} in {'main' if is_main_thread else 'worker'} thread {current_thread_id} for setup_async")
        
        # Make sure this loop is set as the current event loop
        asyncio.set_event_loop(self.app.loop)
        
        # Start the event queue with additional error handling
        logger.info("Starting the event queue")
        try:
            await self.app.event_queue.start()
            logger.info(f"Event queue started successfully")
        except Exception as e:
            logger.error(f"Error starting event queue: {e}", exc_info=True)
            raise
        
        # Initialize centralized resource and circuit breaker coordinators
        self.app.circuit_registry = CircuitBreakerRegistry(self.app.event_queue)
        self.app.resource_coordinator = ResourceCoordinator(self.app.event_queue)
        
        # Define all managers to be registered
        managers_to_register = [
            ("state_manager", StateManager(self.app.event_queue), []),
            ("context_manager", AgentContextManager(self.app.event_queue), ["state_manager"]),
            ("cache_manager", CacheManager(self.app.event_queue), ["state_manager"]),
            ("metrics_manager", MetricsManager(self.app.event_queue), ["state_manager"]),
            ("error_handler", ErrorHandler(self.app.event_queue), ["state_manager"]),
            ("memory_monitor", MemoryMonitor(self.app.event_queue), []),
            ("health_tracker", HealthTracker(self.app.event_queue), []),
            ("system_monitor", SystemMonitor(self.app.event_queue, None, None), ["memory_monitor", "health_tracker"]),
            ("error_recovery", SystemErrorRecovery(self.app.event_queue, None), ["state_manager", "health_tracker"])
        ]
        
        # Register all managers and store references
        logger.info(f"Registering {len(managers_to_register)} resource managers")
        for name, manager, deps in managers_to_register:
            self.app.resource_coordinator.register_manager(name, manager, dependencies=deps)
            setattr(self.app, name, manager)
        
        # Update manager references that need other managers
        self.app.system_monitor.memory_monitor = self.app.memory_monitor
        self.app.system_monitor.health_tracker = self.app.health_tracker
        self.app.error_recovery._health_tracker = self.app.health_tracker
        
        # Initialize all components in dependency order using the centralized coordinator
        logger.info("Starting coordinated initialization of all resource managers")
        try:
            await self.app.resource_coordinator.initialize_all()
            logger.info("✅ All resource managers initialized successfully")
        except Exception as e:
            logger.error(f"Error during resource initialization: {e}", exc_info=True)
            raise
        
        # Set up background processing thread for monitoring systems
        logger.info("Setting up background processing thread")
        self.app.event_manager.setup_background_thread()
        
        # Initialize Minimal Phase Zero orchestrator 
        logger.info("Initializing Minimal Phase Zero orchestrator")
        self.app.phase_zero = MinimalPhaseZeroOrchestrator(
            self.app.event_queue,
            self.app.state_manager,
            self.app.context_manager,
            self.app.cache_manager,
            self.app.metrics_manager,
            self.app.error_handler,
            health_tracker=self.app.health_tracker,
            memory_monitor=self.app.memory_monitor,
            system_monitor=self.app.system_monitor
        )
        
        # Initialize Phase One agents and workflow manually
        logger.info("Initializing Phase One agents and workflow")
        try:
            await self._initialize_phase_one_components()
        except Exception as e:
            logger.error(f"Error initializing Phase One orchestrator: {e}", exc_info=True)
            raise
        
        # Create the interface for display
        from .interface import PhaseOneInterface
        self.app.phase_one_interface = PhaseOneInterface(self.app.phase_one)
        
        # Initialize UI
        logger.info("Initializing UI")
        self.app.main_window = ForestDisplay(
            self.app.event_queue,
            self.app.phase_one_interface,
            self.app.system_monitor
        )
        self.app.main_window.show()
        
        self._initialized = True
        logger.info("Phase One App setup complete")
        
    async def _initialize_phase_one_components(self):
        """Initialize Phase One agents, workflow, and orchestrator."""
        # Initialize agents with necessary parameters
        garden_planner = GardenPlannerAgent(
            "garden_planner",
            self.app.event_queue,
            self.app.state_manager,
            self.app.context_manager,
            self.app.cache_manager,
            self.app.metrics_manager,
            self.app.error_handler,
            self.app.memory_monitor,
            self.app.health_tracker
        )
        
        earth_agent = EarthAgent(
            "earth_agent",
            self.app.event_queue,
            self.app.state_manager,
            self.app.context_manager,
            self.app.cache_manager,
            self.app.metrics_manager,
            self.app.error_handler,
            self.app.memory_monitor,
            self.app.health_tracker
        )
        
        env_analysis = EnvironmentalAnalysisAgent(
            "environmental_analysis",
            self.app.event_queue,
            self.app.state_manager,
            self.app.context_manager,
            self.app.cache_manager,
            self.app.metrics_manager,
            self.app.error_handler,
            self.app.memory_monitor,
            self.app.health_tracker
        )
        
        root_system = RootSystemArchitectAgent(
            "root_system_architect",
            self.app.event_queue,
            self.app.state_manager,
            self.app.context_manager,
            self.app.cache_manager,
            self.app.metrics_manager,
            self.app.error_handler,
            self.app.memory_monitor,
            self.app.health_tracker
        )
        
        tree_placement = TreePlacementPlannerAgent(
            "tree_placement_planner",
            self.app.event_queue,
            self.app.state_manager,
            self.app.context_manager,
            self.app.cache_manager,
            self.app.metrics_manager,
            self.app.error_handler,
            self.app.memory_monitor,
            self.app.health_tracker
        )
        
        # Create workflow
        workflow = PhaseOneWorkflow(
            garden_planner,
            earth_agent,
            env_analysis,
            root_system,
            tree_placement,
            self.app.event_queue,
            self.app.state_manager
        )
        
        # Initialize Phase One orchestrator
        logger.info("Initializing Phase One orchestrator with pre-initialized agents")
        self.app.phase_one = PhaseOneOrchestrator(
            self.app.event_queue,
            self.app.state_manager,
            self.app.context_manager,
            self.app.cache_manager,
            self.app.metrics_manager,
            self.app.error_handler,
            error_recovery=self.app.error_recovery,
            phase_zero=self.app.phase_zero,
            health_tracker=self.app.health_tracker,
            memory_monitor=self.app.memory_monitor,
            system_monitor=self.app.system_monitor,
            # Pass pre-initialized agents and workflow
            garden_planner_agent=garden_planner,
            earth_agent=earth_agent,
            environmental_analysis_agent=env_analysis,
            root_system_architect_agent=root_system,
            tree_placement_planner_agent=tree_placement,
            workflow=workflow
        )
    
    def shutdown(self):
        """Clean up resources in the correct sequence."""
        logger.info("Application shutdown initiated")
        
        # Process pending Qt events
        self.app.app.processEvents()
        
        # Log circuit breaker creation summary
        if hasattr(self.app, 'circuit_registry') and hasattr(self.app.circuit_registry, 'log_creation_summary'):
            try:
                self.app.circuit_registry.log_creation_summary()
            except Exception as e:
                logger.error(f"Error logging circuit breaker summary: {e}")
        elif hasattr(self.app, 'circuit_registry'):
            logger.debug("Circuit registry doesn't have log_creation_summary method")
                
        # Cleanup Phase One orchestrator
        if hasattr(self.app, 'phase_one'):
            try:
                self._cleanup_phase_one()
            except Exception as e:
                logger.error(f"Error shutting down Phase One: {e}", exc_info=True)
                
        # Cleanup UI components
        if hasattr(self.app, 'main_window'):
            try:
                self.app.main_window.close()
            except Exception as e:
                logger.error(f"Error closing main window: {e}")
                
        # Shutdown event queue last
        if hasattr(self.app, 'event_queue'):
            try:
                self._cleanup_event_queue()
            except Exception as e:
                logger.error(f"Error stopping event queue: {e}", exc_info=True)
                
        logger.info("Application shutdown complete")
    
    def _cleanup_phase_one(self):
        """Clean up Phase One orchestrator with simplified sync approach."""
        if not hasattr(self.app, 'phase_one') or not self.app.phase_one:
            return
            
        try:
            # For shutdown, use a simplified approach to avoid thread/loop conflicts
            # Call any synchronous cleanup methods first
            if hasattr(self.app.phase_one, '_sync_cleanup'):
                self.app.phase_one._sync_cleanup()
            
            # Set shutdown flag to stop any background processing
            if hasattr(self.app.phase_one, '_shutdown_requested'):
                self.app.phase_one._shutdown_requested = True
                
            # Log successful cleanup
            logger.info("Phase One orchestrator cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during Phase One cleanup: {e}")
            # Continue with shutdown even if cleanup fails
    
    def _cleanup_event_queue(self):
        """Clean up event queue with simplified sync approach."""
        if not hasattr(self.app, 'event_queue') or not self.app.event_queue:
            return
            
        try:
            # For shutdown, use simplified synchronous cleanup
            # Set shutdown flag to stop processing
            if hasattr(self.app.event_queue, '_shutdown_requested'):
                self.app.event_queue._shutdown_requested = True
                
            # Call any synchronous cleanup methods
            if hasattr(self.app.event_queue, '_sync_cleanup'):
                self.app.event_queue._sync_cleanup()
            
            # Log successful cleanup
            logger.info("Event queue cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during event queue cleanup: {e}")
            # Continue with shutdown even if cleanup fails