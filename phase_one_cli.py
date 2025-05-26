"""
Phase One CLI Runner

This script provides a command-line interface for testing Phase One functionality
without requiring the GUI. It's a simpler alternative to phase_one_test.py for quick
testing and debugging of Phase One components.
"""
import asyncio
import argparse
import logging
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Import Phase One components
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
from resources.managers import AgentContextManager, CacheManager, MetricsManager
from resources.monitoring import HealthTracker, MemoryMonitor, SystemMonitor
from resources.errors import ErrorHandler
from system_error_recovery import SystemErrorRecovery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase_one_cli.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PhaseOneCLI:
    """Command-line interface for testing Phase One functionality."""
    
    def __init__(self):
        """Initialize the CLI with required resources."""
        self.event_queue = None
        self.state_manager = None
        self.context_manager = None
        self.cache_manager = None
        self.metrics_manager = None
        self.error_handler = None
        self.health_tracker = None
        self.memory_monitor = None
        self.system_monitor = None
        self.phase_one = None
        
    async def setup(self):
        """Set up all required resources."""
        logger.info("Setting up Phase One CLI resources")
        
        # Initialize event queue
        self.event_queue = EventQueue()
        await self.event_queue.start()
        
        # Initialize managers
        self.state_manager = StateManager(self.event_queue)
        self.context_manager = AgentContextManager(self.event_queue)
        self.cache_manager = CacheManager(self.event_queue)
        self.metrics_manager = MetricsManager(self.event_queue)
        self.error_handler = ErrorHandler(self.event_queue)
        
        # Initialize monitors
        self.memory_monitor = MemoryMonitor(self.event_queue)
        self.health_tracker = HealthTracker(self.event_queue)
        self.system_monitor = SystemMonitor(
            self.event_queue, 
            self.memory_monitor, 
            self.health_tracker
        )
        
        # Initialize error recovery
        self.error_recovery = SystemErrorRecovery(self.event_queue, self.health_tracker)
        
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
        self.phase_one = FixedPhaseOneOrchestrator(
            self.event_queue,
            self.state_manager,
            self.context_manager,
            self.cache_manager,
            self.metrics_manager,
            self.error_handler,
            error_recovery=self.error_recovery,
            phase_zero=self.phase_zero,  # Use minimal phase zero
            health_tracker=self.health_tracker,
            memory_monitor=self.memory_monitor,
            system_monitor=self.system_monitor
        )
        
        logger.info("Phase One CLI setup complete")
        
    async def process_prompt(self, prompt: str, operation_id: Optional[str] = None):
        """Process a user prompt through Phase One."""
        if not operation_id:
            operation_id = f"cli_{datetime.now().isoformat().replace(':', '-')}"
            
        logger.info(f"Processing prompt with operation ID: {operation_id}")
        logger.info(f"Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"Prompt: {prompt}")
        
        try:
            # Process the prompt with Phase One
            result = await self.phase_one.process_task(prompt, operation_id)
            
            # Return the result
            return result
        except Exception as e:
            logger.error(f"Error processing prompt: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "operation_id": operation_id
            }
            
    async def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up resources")
        
        # Shutdown Phase One orchestrator
        if self.phase_one:
            try:
                await self.phase_one.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down Phase One: {e}")
                
        # Stop event queue
        if self.event_queue:
            try:
                await self.event_queue.stop()
            except Exception as e:
                logger.error(f"Error stopping event queue: {e}")
                
        logger.info("Cleanup complete")
        
    async def run_from_file(self, file_path: str):
        """Run Phase One with a prompt from a file."""
        try:
            # Read prompt from file
            with open(file_path, 'r') as f:
                prompt = f.read()
                
            # Process the prompt
            result = await self.process_prompt(prompt)
            
            # Print result
            self._print_result(result)
            
            return result
        except Exception as e:
            logger.error(f"Error processing file: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error processing file: {str(e)}"
            }
            
    async def run_interactive(self):
        """Run Phase One in interactive mode."""
        print("Phase One CLI Interactive Mode")
        print("Enter your prompt (type 'exit' to quit):")
        
        while True:
            try:
                # Get user input
                prompt = input("> ")
                
                # Check for exit command
                if prompt.lower() in ('exit', 'quit', 'bye'):
                    break
                    
                # Process the prompt
                result = await self.process_prompt(prompt)
                
                # Print result
                self._print_result(result)
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                logger.error(f"Error in interactive mode: {e}", exc_info=True)
                print(f"Error: {str(e)}")
                
        print("Interactive session ended")
        
    def _print_result(self, result: Dict[str, Any]):
        """Print result in a readable format."""
        print("\n===== RESULT =====")
        print(f"Status: {result.get('status', 'unknown')}")
        
        if result.get('status') == 'error':
            print(f"Error: {result.get('message', 'Unknown error')}")
            return
            
        # Print structural components if available
        if 'structural_components' in result:
            print("\nStructural Components:")
            components = result['structural_components']
            for i, component in enumerate(components):
                print(f"  {i+1}. {component.get('name', 'Unknown')}: {component.get('description', 'No description')}")
                print(f"     Dependencies: {', '.join(component.get('dependencies', []))}")
                
        # Print system requirements summary if available
        if 'system_requirements' in result:
            requirements = result['system_requirements']
            print("\nSystem Requirements Summary:")
            
            if 'task_analysis' in requirements:
                task = requirements['task_analysis']
                print(f"  Goal: {task.get('interpreted_goal', 'Unknown')}")
                if 'technical_requirements' in task:
                    tech = task['technical_requirements']
                    print(f"  Tech Stack: {', '.join(tech.get('languages', []))}, {', '.join(tech.get('frameworks', []))}")
            
            if 'environmental_analysis' in requirements:
                env = requirements['environmental_analysis']
                if 'analysis' in env and 'requirements' in env['analysis']:
                    print(f"  Functional Requirements: {', '.join(env['analysis']['requirements'].get('functional', []))}")
        
        # Print execution time if available
        if 'execution_time' in result:
            print(f"\nExecution Time: {result['execution_time']:.2f} seconds")
            
        print("==================\n")
        
async def main():
    """Main function to parse arguments and run the CLI."""
    parser = argparse.ArgumentParser(description='Phase One CLI Runner')
    parser.add_argument('-f', '--file', help='Path to file containing the prompt')
    parser.add_argument('-i', '--interactive', action='store_true', help='Run in interactive mode')
    parser.add_argument('-p', '--prompt', help='Direct prompt to process')
    parser.add_argument('-o', '--output', help='Path to output file for results')
    
    args = parser.parse_args()
    
    cli = PhaseOneCLI()
    result = None
    
    try:
        # Setup resources
        await cli.setup()
        
        # Process based on arguments
        if args.file:
            result = await cli.run_from_file(args.file)
        elif args.prompt:
            result = await cli.process_prompt(args.prompt)
            cli._print_result(result)
        elif args.interactive:
            await cli.run_interactive()
        else:
            # Default to interactive mode if no arguments
            await cli.run_interactive()
            
        # Save result to file if output specified
        if args.output and result:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
                logger.info(f"Result saved to {args.output}")
                
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        print(f"Error: {str(e)}")
    finally:
        # Cleanup resources
        await cli.cleanup()
        
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)