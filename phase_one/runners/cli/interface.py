"""
Phase One Command-Line Interface

Provides command-line interface for Phase One functionality without GUI components.
Supports both interactive debugging mode and single prompt execution.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from .debugger import PhaseOneDebugger
from resources.events import EventQueue
from resources.state import StateManager
from resources.managers import AgentContextManager, CacheManager, MetricsManager
from resources.monitoring import SystemMonitor, MemoryMonitor, HealthTracker
from resources.errors import ErrorHandler
from system_error_recovery import SystemErrorRecovery
from phase_one_minimal_phase_zero import MinimalPhaseZeroOrchestrator

# Import Phase One agents
from phase_one.agents.garden_planner import GardenPlannerAgent
from phase_one.agents.earth_agent import EarthAgent
from phase_one.agents.environmental_analysis import EnvironmentalAnalysisAgent
from phase_one.agents.root_system_architect import RootSystemArchitectAgent
from phase_one.agents.tree_placement_planner import TreePlacementPlannerAgent
from phase_one.workflow import PhaseOneWorkflow
from phase_one.orchestrator import PhaseOneOrchestrator

logger = logging.getLogger(__name__)


class PhaseOneCLI:
    """Command-line interface for Phase One with debugging capabilities."""
    
    def __init__(self):
        self.phase_one_app = None
        self.debugger = None
        
    async def setup_cli(self):
        """Set up CLI resources without GUI components."""
        from resources.events.utils import ensure_event_loop, run_async_in_thread
        from resources.events.loop_management import EventLoopManager
        
        # Ensure we have a valid event loop
        loop = ensure_event_loop()
        EventLoopManager.set_primary_loop(loop)
        
        # Initialize event queue and managers
        event_queue = EventQueue(queue_id="phase_one_cli_queue")
        await event_queue.start()
        
        # Initialize resource managers
        state_manager = StateManager(event_queue)
        context_manager = AgentContextManager(event_queue)
        cache_manager = CacheManager(event_queue)
        metrics_manager = MetricsManager(event_queue)
        error_handler = ErrorHandler(event_queue)
        memory_monitor = MemoryMonitor(event_queue)
        health_tracker = HealthTracker(event_queue)
        system_monitor = SystemMonitor(event_queue, memory_monitor, health_tracker)
        error_recovery = SystemErrorRecovery(event_queue, health_tracker)
        
        # Initialize Minimal Phase Zero orchestrator 
        phase_zero = MinimalPhaseZeroOrchestrator(
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            health_tracker=health_tracker,
            memory_monitor=memory_monitor,
            system_monitor=system_monitor
        )
        
        # Initialize Phase One agents
        garden_planner = GardenPlannerAgent(
            "garden_planner",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor,
            health_tracker
        )
        
        earth_agent = EarthAgent(
            "earth_agent",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor,
            health_tracker
        )
        
        env_analysis = EnvironmentalAnalysisAgent(
            "environmental_analysis",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor,
            health_tracker
        )
        
        root_system = RootSystemArchitectAgent(
            "root_system_architect",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor,
            health_tracker
        )
        
        tree_placement = TreePlacementPlannerAgent(
            "tree_placement_planner",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor,
            health_tracker
        )
        
        # Create workflow
        workflow = PhaseOneWorkflow(
            garden_planner,
            earth_agent,
            env_analysis,
            root_system,
            tree_placement,
            event_queue,
            state_manager
        )
        
        # Initialize Phase One orchestrator
        phase_one = PhaseOneOrchestrator(
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            error_recovery=error_recovery,
            phase_zero=phase_zero,
            health_tracker=health_tracker,
            memory_monitor=memory_monitor,
            system_monitor=system_monitor,
            garden_planner_agent=garden_planner,
            earth_agent=earth_agent,
            environmental_analysis_agent=env_analysis,
            root_system_architect_agent=root_system,
            tree_placement_planner_agent=tree_placement,
            workflow=workflow
        )
        
        # Create debugger
        self.debugger = PhaseOneDebugger(phase_one)
        
        # Store references for cleanup
        self.event_queue = event_queue
        self.phase_one = phase_one
        
    async def run_interactive_mode(self):
        """Run interactive debugging mode."""
        print("🌲 Phase One CLI - Interactive Debug Mode")
        print("Setting up system...")
        
        try:
            await self.setup_cli()
            print("✅ System initialized successfully!")
            await self.debugger.start_interactive_session()
        except Exception as e:
            logger.error(f"CLI setup failed: {e}", exc_info=True)
            print(f"❌ Setup failed: {str(e)}")
            
    async def run_single_prompt(self, prompt: str, output_file: Optional[str] = None):
        """Run a single prompt and exit."""
        print("🌲 Phase One CLI - Single Prompt Mode")
        print("Setting up system...")
        
        try:
            await self.setup_cli()
            print("✅ System initialized successfully!")
            
            operation_id = f"cli_{datetime.now().isoformat().replace(':', '-')}"
            result = await self.phase_one.process_task(prompt, operation_id)
            
            # Use debugger's pretty printing
            self.debugger._print_execution_result(result)
            
            # Save to file if requested
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"📁 Result saved to: {output_file}")
                
        except Exception as e:
            logger.error(f"CLI execution failed: {e}", exc_info=True)
            print(f"❌ Execution failed: {str(e)}")
            
    async def cleanup(self):
        """Clean up CLI resources."""
        if hasattr(self, 'phase_one') and self.phase_one:
            try:
                await self.phase_one.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down Phase One: {e}")
        
        if hasattr(self, 'event_queue') and self.event_queue:
            try:
                await self.event_queue.stop()
            except Exception as e:
                logger.error(f"Error stopping event queue: {e}")


async def run_cli_mode(args):
    """Run in CLI mode based on arguments."""
    cli = PhaseOneCLI()
    
    try:
        if args.interactive or args.debug:
            await cli.run_interactive_mode()
        elif args.prompt:
            await cli.run_single_prompt(args.prompt, args.output)
        elif args.file:
            with open(args.file, 'r') as f:
                prompt = f.read()
            await cli.run_single_prompt(prompt, args.output)
        else:
            # Default to interactive mode
            await cli.run_interactive_mode()
    finally:
        await cli.cleanup()