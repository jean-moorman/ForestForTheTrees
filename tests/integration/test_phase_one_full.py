"""
Integration test script for Phase One with Earth & Water agent integration.

This script performs a full integration test of the Phase One workflow,
using actual agents to process a user request from start to finish, including:
- Garden Planner agent with Earth Agent validation
- Water Agent coordination between sequential agents
- Environmental Analysis Agent
- Root System Architect Agent
- Tree Placement Planner Agent
"""

import asyncio
import logging
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from resources import (
    EventQueue, 
    StateManager, 
    AgentContextManager, 
    CacheManager, 
    MetricsManager,
    ErrorHandler,
    MemoryMonitor,
    ResourceType
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("phase_one_integration_test.log")
    ]
)
logger = logging.getLogger(__name__)

# Simple test request for faster testing cycle
TEST_REQUEST = """
Create a web application that allows users to track their daily habits and goals.
The application should have user authentication, a dashboard for tracking progress,
and the ability to set recurring habits and goals with reminders.
"""

class TestResources:
    """Container class for shared resources used in tests."""
    
    def __init__(self):
        self.event_queue = None
        self.state_manager = None
        self.context_manager = None
        self.cache_manager = None
        self.metrics_manager = None
        self.error_handler = None
        self.memory_monitor = None
        self.health_tracker = None
        
    async def setup(self):
        """Initialize and start all shared resources."""
        self.event_queue = EventQueue()
        await self.event_queue.start()
        
        self.state_manager = StateManager(self.event_queue)
        self.context_manager = AgentContextManager(self.event_queue)
        self.cache_manager = CacheManager(self.event_queue)
        self.metrics_manager = MetricsManager(self.event_queue)
        self.error_handler = ErrorHandler(self.event_queue)
        self.memory_monitor = MemoryMonitor(self.event_queue)
        self.health_tracker = HealthTracker(self.event_queue)
        
        logger.info("Resources initialized successfully")
        
    async def cleanup(self):
        """Stop and clean up all resources."""
        logger.info("Cleaning up resources")
        if self.event_queue:
            await self.event_queue.stop()


@pytest.mark.asyncio
async def test_full_phase_one_integration():
    """Full integration test for Phase One workflow."""
    resources = TestResources()
    try:
        # Setup resources
        await resources.setup()
        
        # Initialize agents
        logger.info("Initializing agents...")
        agents = {}
        
        # Create Garden Planner agent
        agents["garden_planner"] = GardenPlannerAgent(
            agent_id="garden_planner",
            event_queue=resources.event_queue,
            state_manager=resources.state_manager,
            context_manager=resources.context_manager,
            cache_manager=resources.cache_manager,
            metrics_manager=resources.metrics_manager,
            error_handler=resources.error_handler,
            memory_monitor=resources.memory_monitor,
            health_tracker=resources.health_tracker
        )
        
        # Create Earth agent
        agents["earth_agent"] = EarthAgent(
            agent_id="earth_agent",
            event_queue=resources.event_queue,
            state_manager=resources.state_manager,
            context_manager=resources.context_manager,
            cache_manager=resources.cache_manager,
            metrics_manager=resources.metrics_manager,
            error_handler=resources.error_handler,
            memory_monitor=resources.memory_monitor,
            health_tracker=resources.health_tracker,
            max_validation_cycles=3
        )
        
        # Create Environmental Analysis agent
        agents["environmental_analysis"] = EnvironmentalAnalysisAgent(
            agent_id="environmental_analysis",
            event_queue=resources.event_queue,
            state_manager=resources.state_manager,
            context_manager=resources.context_manager,
            cache_manager=resources.cache_manager,
            metrics_manager=resources.metrics_manager,
            error_handler=resources.error_handler,
            memory_monitor=resources.memory_monitor,
            health_tracker=resources.health_tracker
        )
        
        # Create Root System Architect agent
        agents["root_system_architect"] = RootSystemArchitectAgent(
            agent_id="root_system_architect",
            event_queue=resources.event_queue,
            state_manager=resources.state_manager,
            context_manager=resources.context_manager,
            cache_manager=resources.cache_manager,
            metrics_manager=resources.metrics_manager,
            error_handler=resources.error_handler,
            memory_monitor=resources.memory_monitor,
            health_tracker=resources.health_tracker
        )
        
        # Create Tree Placement Planner agent
        agents["tree_placement_planner"] = TreePlacementPlannerAgent(
            agent_id="tree_placement_planner",
            event_queue=resources.event_queue,
            state_manager=resources.state_manager,
            context_manager=resources.context_manager,
            cache_manager=resources.cache_manager,
            metrics_manager=resources.metrics_manager,
            error_handler=resources.error_handler,
            memory_monitor=resources.memory_monitor,
            health_tracker=resources.health_tracker
        )
        
        logger.info("All agents initialized successfully")
        
        # Create Phase One workflow
        logger.info("Creating Phase One workflow...")
        workflow = PhaseOneWorkflow(
            garden_planner_agent=agents["garden_planner"],
            earth_agent=agents["earth_agent"],
            environmental_analysis_agent=agents["environmental_analysis"],
            root_system_architect_agent=agents["root_system_architect"],
            tree_placement_planner_agent=agents["tree_placement_planner"],
            event_queue=resources.event_queue,
            state_manager=resources.state_manager,
            max_earth_validation_cycles=3,
            validation_timeout=180.0  # 3 minutes timeout for validation
        )
        
        # Define a unique operation ID
        operation_id = f"integration_test_{datetime.now().isoformat().replace(':', '-')}"
        logger.info(f"Starting workflow with operation ID: {operation_id}")
        
        # Execute Phase One workflow
        logger.info(f"Processing user request: {TEST_REQUEST.strip()[:100]}...")
        result = await workflow.execute_phase_one(TEST_REQUEST, operation_id)
        
        # Verify the workflow completed successfully
        assert result["status"] == "completed", f"Workflow failed with status: {result.get('status')}, stage: {result.get('failure_stage')}"
        
        # Log workflow result summary
        logger.info(f"Workflow completed with status: {result['status']}")
        
        # Check all expected outputs are present
        assert "task_analysis" in result["final_output"], "Missing task analysis in output"
        assert "environmental_analysis" in result["final_output"], "Missing environmental analysis in output"
        assert "data_architecture" in result["final_output"], "Missing data architecture in output"
        assert "component_architecture" in result["final_output"], "Missing component architecture in output"
        
        # Check validation history
        if "garden_planner" in result["agents"]:
            garden_planner_result = result["agents"]["garden_planner"]
            assert garden_planner_result["success"], "Garden Planner failed"
            
            if "validation" in garden_planner_result:
                validation = garden_planner_result["validation"]
                logger.info(f"Earth Agent validation successful: {validation['is_valid']}")
                logger.info(f"Validation history: {len(validation['validation_history'])} cycles")
        
        # Log component architecture summary
        component_arch = result["final_output"]["component_architecture"]
        if "components" in component_arch:
            components = component_arch["components"]
            logger.info(f"Component architecture generated with {len(components)} components:")
            for component in components:
                logger.info(f"- {component.get('name', 'Unnamed')} ({component.get('id', 'no-id')}): {component.get('description', 'No description')}")
        
        # Check Water Agent coordination
        for coordination_type in ["garden_to_env", "env_to_root", "root_to_tree"]:
            coordination_id = f"{operation_id}_{coordination_type}_coordination"
            coordination_status = await workflow.sequential_coordinator.get_coordination_status(coordination_id)
            
            logger.info(f"Water Agent coordination for {coordination_type}:")
            logger.info(f"- Status: {coordination_status['status']}")
            logger.info(f"- Result: {coordination_status.get('result', 'N/A')}")
            
            if "misunderstandings_count" in coordination_status:
                logger.info(f"- Misunderstandings detected: {coordination_status['misunderstandings_count']}")
                
            if "first_output_updated" in coordination_status:
                logger.info(f"- Output updated: {coordination_status['first_output_updated']}")
        
        logger.info("Integration test completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error in Phase One integration test: {str(e)}", exc_info=True)
        raise
        
    finally:
        # Clean up resources
        await resources.cleanup()


if __name__ == "__main__":
    asyncio.run(test_full_phase_one_integration())