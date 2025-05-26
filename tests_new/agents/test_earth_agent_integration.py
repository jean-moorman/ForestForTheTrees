"""
Integration test for Earth Agent validation in Phase One.

This test script focuses specifically on testing the Earth Agent's validation of
Garden Planner output in Phase One, verifying that it can correctly validate, 
identify issues, and provide feedback for refinement.
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

from phase_one.agents.garden_planner import GardenPlannerAgent
from phase_one.agents.earth_agent import EarthAgent
from phase_one.validation.garden_planner_validator import GardenPlannerValidator
from phase_one.models.enums import DevelopmentState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("earth_agent_test.log")
    ]
)
logger = logging.getLogger(__name__)

# Test user request
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
async def test_garden_planner_output_generation():
    """Test the Garden Planner agent's ability to generate initial task analysis."""
    logger.info("Testing Garden Planner output generation...")
    
    # Setup resources
    resources = TestResources()
    await resources.setup()
    
    try:
        # Create Garden Planner agent
        garden_planner = GardenPlannerAgent(
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
        
        # Set Garden Planner to analyzing state
        garden_planner.development_state = DevelopmentState.ANALYZING
        
        # Generate initial task analysis
        logger.info("Generating initial task analysis...")
        initial_analysis = await garden_planner._process(TEST_REQUEST)
        
        # Verify initial analysis structure
        assert "task_analysis" in initial_analysis, "Missing task analysis in Garden Planner output"
        task_analysis = initial_analysis["task_analysis"]
        
        # Verify task analysis fields
        required_fields = ["original_request", "interpreted_goal", "scope", 
                          "technical_requirements", "constraints", "considerations"]
        
        for field in required_fields:
            assert field in task_analysis, f"Missing {field} in task analysis"
        
        # Log success
        logger.info("Garden Planner successfully generated task analysis.")
        logger.info(f"Task analysis contains fields: {', '.join(task_analysis.keys())}")
        
        return initial_analysis
        
    finally:
        # Clean up resources
        await resources.cleanup()


@pytest.mark.asyncio
async def test_earth_agent_validation():
    """Test Earth Agent's validation of Garden Planner output."""
    logger.info("Testing Earth Agent validation...")
    
    # Setup resources
    resources = TestResources()
    await resources.setup()
    
    try:
        # Create Earth agent
        earth_agent = EarthAgent(
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
        
        # Create Garden Planner agent to generate output
        garden_planner = GardenPlannerAgent(
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
        
        # Set Garden Planner to analyzing state
        garden_planner.development_state = DevelopmentState.ANALYZING
        
        # Generate Garden Planner output
        logger.info("Generating Garden Planner output for validation...")
        garden_planner_output = await garden_planner._process(TEST_REQUEST)
        
        # Validate Garden Planner output with Earth Agent
        validation_id = f"test_validation_{datetime.now().isoformat().replace(':', '-')}"
        logger.info(f"Validating Garden Planner output with Earth Agent, validation ID: {validation_id}")
        
        validation_result = await earth_agent.validate_garden_planner_output(
            TEST_REQUEST,
            garden_planner_output,
            validation_id
        )
        
        # Verify validation result
        assert "validation_result" in validation_result, "Missing validation result from Earth Agent"
        
        validation_category = validation_result["validation_result"]["validation_category"]
        is_valid = validation_result["validation_result"]["is_valid"]
        explanation = validation_result["validation_result"]["explanation"]
        
        logger.info(f"Validation category: {validation_category}")
        logger.info(f"Is valid: {is_valid}")
        logger.info(f"Explanation: {explanation[:100]}...")
        
        # Check for architectural issues
        if "architectural_issues" in validation_result:
            issues = validation_result["architectural_issues"]
            logger.info(f"Found {len(issues)} architectural issues:")
            
            for i, issue in enumerate(issues):
                logger.info(f"Issue {i+1}: {issue.get('description', 'No description')} (Severity: {issue.get('severity', 'Unknown')})")
        
        return validation_result
        
    finally:
        # Clean up resources
        await resources.cleanup()


@pytest.mark.asyncio
async def test_garden_planner_validator():
    """Test the GardenPlannerValidator integration with Earth Agent."""
    logger.info("Testing GardenPlannerValidator with Earth Agent...")
    
    # Setup resources
    resources = TestResources()
    await resources.setup()
    
    try:
        # Create Garden Planner agent
        garden_planner = GardenPlannerAgent(
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
        earth_agent = EarthAgent(
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
        
        # Create Garden Planner validator
        validator = GardenPlannerValidator(
            garden_planner_agent=garden_planner,
            earth_agent=earth_agent,
            event_queue=resources.event_queue,
            state_manager=resources.state_manager,
            max_refinement_cycles=3,
            validation_timeout=180.0
        )
        
        # Set Garden Planner to analyzing state
        garden_planner.development_state = DevelopmentState.ANALYZING
        
        # Generate Garden Planner output
        logger.info("Generating Garden Planner output...")
        garden_planner_output = await garden_planner._process(TEST_REQUEST)
        
        # Validate Garden Planner output with validator
        validation_id = f"validator_test_{datetime.now().isoformat().replace(':', '-')}"
        logger.info(f"Running Garden Planner validator, operation ID: {validation_id}")
        
        # Run the validation process
        is_valid, validated_analysis, validation_history = await validator.validate_initial_task_analysis(
            TEST_REQUEST,
            garden_planner_output,
            validation_id
        )
        
        # Verify validation result
        logger.info(f"Validation result: {'Valid' if is_valid else 'Invalid'}")
        logger.info(f"Validation cycles: {len(validation_history)}")
        
        for i, cycle in enumerate(validation_history):
            logger.info(f"Cycle {i+1}: {cycle.get('validation_category', 'Unknown')}, Issues: {cycle.get('issue_count', 0)}")
        
        # Check validated analysis
        assert "task_analysis" in validated_analysis, "Missing task analysis in validated output"
        
        # Get validation status
        validation_status = await validator.get_validation_status(validation_id)
        logger.info(f"Validation status: {validation_status.get('status', 'Unknown')}")
        
        return {
            "is_valid": is_valid,
            "validated_analysis": validated_analysis,
            "validation_history": validation_history,
            "validation_status": validation_status
        }
        
    finally:
        # Clean up resources
        await resources.cleanup()


async def run_earth_agent_tests():
    """Run all Earth Agent integration tests."""
    try:
        logger.info("Starting Earth Agent integration tests")
        
        # Test Garden Planner output generation
        garden_planner_output = await test_garden_planner_output_generation()
        logger.info("Garden Planner output generation test completed")
        
        # Test Earth Agent validation
        earth_validation = await test_earth_agent_validation()
        logger.info("Earth Agent validation test completed")
        
        # Test Garden Planner validator
        validator_result = await test_garden_planner_validator()
        logger.info("Garden Planner validator test completed")
        
        # Final results
        logger.info("All Earth Agent integration tests completed successfully")
        
        return {
            "garden_planner_output": garden_planner_output,
            "earth_validation": earth_validation,
            "validator_result": validator_result
        }
        
    except Exception as e:
        logger.error(f"Error in Earth Agent integration tests: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(run_earth_agent_tests())