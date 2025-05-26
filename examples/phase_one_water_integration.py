"""
Example demonstrating Phase One with Water Agent integration.

This script provides a practical example of using the Phase One workflow with Water Agent
coordination between sequential agents, focusing on how the Water Agent detects and
resolves misunderstandings during agent handoffs.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from resources import (
    EventQueue, 
    StateManager, 
    AgentContextManager, 
    CacheManager, 
    MetricsManager,
    ErrorHandler,
    MemoryMonitor
)
from resources.monitoring import HealthTracker
from resources.water_agent import WaterAgentCoordinator

from phase_one.workflow import PhaseOneWorkflow
from phase_one.agents.garden_planner import GardenPlannerAgent
from phase_one.agents.earth_agent import EarthAgent
from phase_one.agents.environmental_analysis import EnvironmentalAnalysisAgent
from phase_one.agents.root_system_architect import RootSystemArchitectAgent
from phase_one.agents.tree_placement_planner import TreePlacementPlannerAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample user request for the demonstration
SAMPLE_USER_REQUEST = """
Create a web application that allows users to track their daily habits and goals.
The application should have user authentication, a dashboard for tracking progress,
and the ability to set recurring habits and goals with reminders.
"""

async def setup_resources():
    """Set up shared resources for the agents."""
    # Create shared resources
    event_queue = EventQueue()
    await event_queue.start()
    
    state_manager = StateManager(event_queue)
    context_manager = AgentContextManager(event_queue)
    cache_manager = CacheManager(event_queue)
    metrics_manager = MetricsManager(event_queue)
    error_handler = ErrorHandler(event_queue)
    memory_monitor = MemoryMonitor(event_queue)
    health_tracker = HealthTracker(event_queue)
    
    return {
        "event_queue": event_queue,
        "state_manager": state_manager,
        "context_manager": context_manager,
        "cache_manager": cache_manager,
        "metrics_manager": metrics_manager,
        "error_handler": error_handler,
        "memory_monitor": memory_monitor,
        "health_tracker": health_tracker
    }

async def initialize_agents(resources):
    """Initialize Phase One agents."""
    # Create Garden Planner agent
    garden_planner = GardenPlannerAgent(
        agent_id="garden_planner",
        event_queue=resources["event_queue"],
        state_manager=resources["state_manager"],
        context_manager=resources["context_manager"],
        cache_manager=resources["cache_manager"],
        metrics_manager=resources["metrics_manager"],
        error_handler=resources["error_handler"],
        memory_monitor=resources["memory_monitor"],
        health_tracker=resources["health_tracker"],
        model="claude-3-7-sonnet-20250219"
    )
    
    # Create Earth agent
    earth_agent = EarthAgent(
        agent_id="earth_agent",
        event_queue=resources["event_queue"],
        state_manager=resources["state_manager"],
        context_manager=resources["context_manager"],
        cache_manager=resources["cache_manager"],
        metrics_manager=resources["metrics_manager"],
        error_handler=resources["error_handler"],
        memory_monitor=resources["memory_monitor"],
        health_tracker=resources["health_tracker"],
        model="claude-3-7-sonnet-20250219"
    )
    
    # Create Environmental Analysis agent
    env_analysis = EnvironmentalAnalysisAgent(
        agent_id="environmental_analysis",
        event_queue=resources["event_queue"],
        state_manager=resources["state_manager"],
        context_manager=resources["context_manager"],
        cache_manager=resources["cache_manager"],
        metrics_manager=resources["metrics_manager"],
        error_handler=resources["error_handler"],
        memory_monitor=resources["memory_monitor"],
        health_tracker=resources["health_tracker"],
        model="claude-3-7-sonnet-20250219"
    )
    
    # Create Root System Architect agent
    root_system = RootSystemArchitectAgent(
        agent_id="root_system_architect",
        event_queue=resources["event_queue"],
        state_manager=resources["state_manager"],
        context_manager=resources["context_manager"],
        cache_manager=resources["cache_manager"],
        metrics_manager=resources["metrics_manager"],
        error_handler=resources["error_handler"],
        memory_monitor=resources["memory_monitor"],
        health_tracker=resources["health_tracker"],
        model="claude-3-7-sonnet-20250219"
    )
    
    # Create Tree Placement Planner agent
    tree_placement = TreePlacementPlannerAgent(
        agent_id="tree_placement_planner",
        event_queue=resources["event_queue"],
        state_manager=resources["state_manager"],
        context_manager=resources["context_manager"],
        cache_manager=resources["cache_manager"],
        metrics_manager=resources["metrics_manager"],
        error_handler=resources["error_handler"],
        memory_monitor=resources["memory_monitor"],
        health_tracker=resources["health_tracker"],
        model="claude-3-7-sonnet-20250219"
    )
    
    return {
        "garden_planner": garden_planner,
        "earth_agent": earth_agent,
        "environmental_analysis": env_analysis,
        "root_system_architect": root_system,
        "tree_placement_planner": tree_placement
    }

async def setup_phase_one_workflow(resources, agents):
    """Set up the Phase One workflow with Water Agent integration."""
    # Create the workflow
    workflow = PhaseOneWorkflow(
        garden_planner_agent=agents["garden_planner"],
        earth_agent=agents["earth_agent"],
        environmental_analysis_agent=agents["environmental_analysis"],
        root_system_architect_agent=agents["root_system_architect"],
        tree_placement_planner_agent=agents["tree_placement_planner"],
        event_queue=resources["event_queue"],
        state_manager=resources["state_manager"],
        max_earth_validation_cycles=3,
        validation_timeout=120.0
    )
    
    # Optional: Configure Water Agent coordinator with specific settings
    # workflow.sequential_coordinator._water_coordinator = WaterAgentCoordinator(
    #     state_manager=resources["state_manager"]
    # )
    
    return workflow

async def run_phase_one_with_water_agent():
    """Run the Phase One workflow with Water Agent integration."""
    try:
        logger.info("Starting Phase One with Water Agent integration demonstration")
        
        # Setup resources
        resources = await setup_resources()
        
        # Initialize agents
        agents = await initialize_agents(resources)
        
        # Setup Phase One workflow
        workflow = await setup_phase_one_workflow(resources, agents)
        
        # Define a unique operation ID for this run
        operation_id = f"phase_one_demo_{datetime.now().isoformat().replace(':', '-')}"
        
        logger.info(f"Starting Phase One workflow with operation ID: {operation_id}")
        logger.info(f"Processing user request: {SAMPLE_USER_REQUEST[:100]}...")
        
        # Run the Phase One workflow
        result = await workflow.execute_phase_one(SAMPLE_USER_REQUEST, operation_id)
        
        # Check if the workflow completed successfully
        if result["status"] == "completed":
            logger.info("Phase One workflow completed successfully!")
            
            # Display the final outputs
            logger.info("\n=== Task Analysis ===")
            logger.info(json.dumps(result["final_output"]["task_analysis"], indent=2)[:500] + "...")
            
            logger.info("\n=== Environmental Analysis ===")
            logger.info(json.dumps(result["final_output"]["environmental_analysis"], indent=2)[:500] + "...")
            
            logger.info("\n=== Data Architecture ===")
            logger.info(json.dumps(result["final_output"]["data_architecture"], indent=2)[:500] + "...")
            
            logger.info("\n=== Component Architecture ===")
            logger.info(json.dumps(result["final_output"]["component_architecture"], indent=2)[:500] + "...")
            
            # Get and display Water Agent coordination results
            for coordination_type in ["garden_to_env", "env_to_root", "root_to_tree"]:
                coordination_id = f"{operation_id}_{coordination_type}"
                coordination_status = await workflow.sequential_coordinator.get_coordination_status(coordination_id)
                
                logger.info(f"\n=== Water Agent Coordination: {coordination_type} ===")
                logger.info(f"Status: {coordination_status['status']}")
                logger.info(f"Result: {coordination_status.get('result', 'N/A')}")
                
                if "misunderstandings_count" in coordination_status:
                    logger.info(f"Misunderstandings detected: {coordination_status['misunderstandings_count']}")
                    
                if "first_output_updated" in coordination_status:
                    logger.info(f"First agent output updated: {coordination_status['first_output_updated']}")
                    
                if "history" in coordination_status and coordination_status["history"]:
                    logger.info(f"Coordination attempts: {len(coordination_status['history'])}")
        else:
            logger.error(f"Phase One workflow failed with status: {result['status']}")
            logger.error(f"Failure stage: {result.get('failure_stage', 'unknown')}")
            logger.error(f"Error: {result.get('error', 'unknown')}")
    
    except Exception as e:
        logger.error(f"Error in Phase One demonstration: {str(e)}", exc_info=True)
    
    finally:
        # Clean up resources
        if "resources" in locals():
            event_queue = resources.get("event_queue")
            if event_queue:
                await event_queue.stop()
        
        logger.info("Phase One demonstration completed")

if __name__ == "__main__":
    asyncio.run(run_phase_one_with_water_agent())