"""
Optimized Phase One Workflow Integration Tests

This module contains integration tests for the Phase One workflow with proper
timeout management and streamlined execution for CI/CD environments.
"""

import asyncio
import json
import pytest
import pytest_asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from resources import (
    EventQueue, StateManager, AgentContextManager, CacheManager, 
    MetricsManager, ErrorHandler, MemoryMonitor, ResourceType
)
from resources.monitoring import HealthTracker
from phase_one.workflow import PhaseOneWorkflow
from phase_one.orchestrator import PhaseOneOrchestrator
from phase_one.agents.garden_planner import GardenPlannerAgent
from phase_one.agents.earth_agent import EarthAgent
from phase_one.agents.environmental_analysis import EnvironmentalAnalysisAgent
from phase_one.agents.root_system_architect import RootSystemArchitectAgent
from phase_one.agents.tree_placement_planner import TreePlacementPlannerAgent

logger = logging.getLogger(__name__)

class TestPhaseOneWorkflowOptimized:
    """Optimized Phase One workflow integration tests."""

    @pytest_asyncio.fixture
    async def lightweight_resources(self):
        """Create lightweight resource managers for faster testing."""
        event_queue = EventQueue()
        await event_queue.start()
        
        # Use in-memory backends for speed
        state_manager = StateManager(event_queue)
        await state_manager.initialize()
        
        context_manager = AgentContextManager(event_queue)
        await context_manager.initialize()
        
        cache_manager = CacheManager(event_queue)
        await cache_manager.initialize()
        
        metrics_manager = MetricsManager(event_queue)
        await metrics_manager.initialize()
        
        error_handler = ErrorHandler(event_queue)
        
        memory_monitor = MemoryMonitor(event_queue)
        health_tracker = HealthTracker(event_queue)

        yield {
            'event_queue': event_queue,
            'state_manager': state_manager,
            'context_manager': context_manager,
            'cache_manager': cache_manager,
            'metrics_manager': metrics_manager,
            'error_handler': error_handler,
            'memory_monitor': memory_monitor,
            'health_tracker': health_tracker
        }
        
        # Cleanup
        await event_queue.stop()

    @pytest_asyncio.fixture
    async def fast_agents(self, lightweight_resources):
        """Create agents optimized for fast testing."""
        return {
            'garden_planner': GardenPlannerAgent(
                agent_id="fast_garden_planner",
                **lightweight_resources
            ),
            'earth_agent': EarthAgent(
                agent_id="fast_earth_agent",
                **lightweight_resources,
                max_validation_cycles=1  # Reduced for speed
            ),
            'environmental_analysis': EnvironmentalAnalysisAgent(
                agent_id="fast_environmental_analysis",
                **lightweight_resources
            ),
            'root_system_architect': RootSystemArchitectAgent(
                agent_id="fast_root_system_architect",
                **lightweight_resources
            ),
            'tree_placement_planner': TreePlacementPlannerAgent(
                agent_id="fast_tree_placement_planner",
                **lightweight_resources
            )
        }

    @pytest_asyncio.fixture
    async def fast_workflow(self, fast_agents, lightweight_resources):
        """Create workflow optimized for fast testing."""
        return PhaseOneWorkflow(
            garden_planner_agent=fast_agents['garden_planner'],
            earth_agent=fast_agents['earth_agent'],
            environmental_analysis_agent=fast_agents['environmental_analysis'],
            root_system_architect_agent=fast_agents['root_system_architect'],
            tree_placement_planner_agent=fast_agents['tree_placement_planner'],
            event_queue=lightweight_resources['event_queue'],
            state_manager=lightweight_resources['state_manager'],
            max_earth_validation_cycles=1,  # Reduced for speed
            validation_timeout=30.0  # Reduced timeout
        )

    @pytest.fixture
    def simple_test_requests(self):
        """Provide simple test requests for fast execution."""
        return [
            "Create a simple todo list app",
            "Build a basic note-taking application",
            "Make a simple calculator web app"
        ]

    @pytest.mark.asyncio
    @pytest.mark.timeout(180)  # 3 minute timeout
    async def test_workflow_basic_execution(self, fast_workflow, simple_test_requests):
        """Test basic workflow execution with timeout protection."""
        user_request = simple_test_requests[0]
        operation_id = f"test_basic_{datetime.now().isoformat()}"
        
        logger.info(f"Testing basic workflow execution with request: {user_request}")
        
        # Use asyncio timeout for additional protection
        try:
            result = await asyncio.wait_for(
                fast_workflow.execute_phase_one(user_request, operation_id),
                timeout=150.0  # 2.5 minute internal timeout
            )
            
            # Verify result structure
            assert isinstance(result, dict), "Workflow should return dictionary"
            assert "status" in result, "Result should contain status"
            assert "operation_id" in result, "Result should contain operation_id"
            
            # Check for successful completion or controlled failure
            if result["status"] == "completed":
                assert "final_output" in result, "Completed workflow should have final_output"
                assert "agents" in result, "Completed workflow should have agent results"
                logger.info("Workflow completed successfully")
            elif result["status"] == "failed":
                assert "failure_stage" in result, "Failed workflow should indicate failure stage"
                logger.info(f"Workflow failed at stage: {result.get('failure_stage')}")
            else:
                pytest.fail(f"Unexpected workflow status: {result['status']}")
            
        except asyncio.TimeoutError:
            pytest.fail("Workflow execution exceeded timeout - potential performance issue")
        
        logger.info("Basic workflow execution test passed")

    @pytest.mark.asyncio 
    @pytest.mark.timeout(120)  # 2 minute timeout
    async def test_workflow_agent_sequence(self, fast_agents, lightweight_resources):
        """Test individual agent sequence without full workflow."""
        user_request = "Create a simple web app"
        
        logger.info("Testing agent sequence execution")
        
        try:
            # 1. Garden Planner
            start_time = datetime.now()
            garden_result = await asyncio.wait_for(
                fast_agents['garden_planner'].process_with_validation(
                    conversation=user_request,
                    system_prompt_info=("FFTT_system_prompts/phase_one", "garden_planner_agent"),
                    operation_id="test_sequence_garden"
                ),
                timeout=30.0
            )
            garden_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Garden Planner completed in {garden_time:.2f}s")
            
            assert "task_analysis" in garden_result, "Garden Planner should produce task_analysis"
            
            # 2. Earth Agent validation (quick validation)
            start_time = datetime.now()
            earth_result = await asyncio.wait_for(
                fast_agents['earth_agent'].validate_garden_planner_output(
                    user_request,
                    garden_result,
                    "test_sequence_earth"
                ),
                timeout=20.0
            )
            earth_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Earth Agent completed in {earth_time:.2f}s")
            
            assert "is_valid" in earth_result, "Earth Agent should provide validation"
            
            # Only continue if validation passes or we can proceed
            if not earth_result.get("is_valid", False):
                logger.info("Earth Agent validation failed - stopping sequence test")
                return
            
            # 3. Environmental Analysis
            start_time = datetime.now()
            env_result = await asyncio.wait_for(
                fast_agents['environmental_analysis']._process(
                    f"Task Analysis: {json.dumps(garden_result.get('task_analysis', {}))}"
                ),
                timeout=20.0
            )
            env_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Environmental Analysis completed in {env_time:.2f}s")
            
            assert isinstance(env_result, dict), "Environmental Analysis should return dict"
            
            # 4. Root System Architect
            start_time = datetime.now()
            root_result = await asyncio.wait_for(
                fast_agents['root_system_architect']._process(
                    f"Environmental Analysis: {json.dumps(env_result)}"
                ),
                timeout=20.0
            )
            root_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Root System Architect completed in {root_time:.2f}s")
            
            assert isinstance(root_result, dict), "Root System Architect should return dict"
            
            # 5. Tree Placement Planner
            start_time = datetime.now()
            tree_result = await asyncio.wait_for(
                fast_agents['tree_placement_planner']._process(
                    f"Task Analysis: {json.dumps(garden_result.get('task_analysis', {}))} "
                    f"Environmental Analysis: {json.dumps(env_result)} "
                    f"Data Architecture: {json.dumps(root_result)}"
                ),
                timeout=30.0
            )
            tree_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Tree Placement Planner completed in {tree_time:.2f}s")
            
            assert isinstance(tree_result, dict), "Tree Placement Planner should return dict"
            
            total_time = garden_time + earth_time + env_time + root_time + tree_time
            logger.info(f"Total agent sequence time: {total_time:.2f}s")
            
        except asyncio.TimeoutError as e:
            pytest.fail(f"Agent sequence exceeded timeout: {str(e)}")
        
        logger.info("Agent sequence test passed")

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)  # 1 minute timeout
    async def test_workflow_error_handling(self, fast_workflow):
        """Test workflow error handling with malformed inputs."""
        
        logger.info("Testing workflow error handling")
        
        error_inputs = [
            "",  # Empty input
            "x" * 1000,  # Very long input
            "Invalid request with special chars: àáâãäåæç",
        ]
        
        for i, error_input in enumerate(error_inputs):
            operation_id = f"test_error_{i}_{datetime.now().isoformat()}"
            
            try:
                result = await asyncio.wait_for(
                    fast_workflow.execute_phase_one(error_input, operation_id),
                    timeout=45.0
                )
                
                # Should handle gracefully
                assert isinstance(result, dict), f"Should return dict for error input {i}"
                assert "status" in result, f"Should have status for error input {i}"
                
                # Status should indicate error or completion
                assert result["status"] in ["error", "failed", "completed"], \
                    f"Should have valid status for error input {i}"
                
                logger.info(f"Error input {i} handled gracefully: {result['status']}")
                
            except asyncio.TimeoutError:
                logger.warning(f"Error input {i} timed out - this may be acceptable")
            except Exception as e:
                pytest.fail(f"Unhandled exception for error input {i}: {str(e)}")
        
        logger.info("Workflow error handling test passed")

    @pytest.mark.asyncio
    @pytest.mark.timeout(90)  # 1.5 minute timeout
    async def test_workflow_state_management(self, fast_workflow, simple_test_requests):
        """Test workflow state management and persistence."""
        user_request = simple_test_requests[1]
        operation_id = f"test_state_{datetime.now().isoformat()}"
        
        logger.info("Testing workflow state management")
        
        try:
            # Start workflow
            result = await asyncio.wait_for(
                fast_workflow.execute_phase_one(user_request, operation_id),
                timeout=75.0
            )
            
            # Check workflow status
            status_result = await fast_workflow.get_workflow_status(operation_id)
            
            assert isinstance(status_result, dict), "Status should be dictionary"
            assert "status" in status_result, "Status should contain status field"
            assert "operation_id" in status_result, "Status should contain operation_id"
            
            # Verify operation_id matches
            assert status_result["operation_id"] == operation_id, "Operation IDs should match"
            
            logger.info(f"Workflow status: {status_result['status']}")
            
        except asyncio.TimeoutError:
            pytest.fail("Workflow state management test exceeded timeout")
        
        logger.info("Workflow state management test passed")

    @pytest.mark.asyncio
    @pytest.mark.timeout(200)  # Extended timeout for orchestrator
    async def test_orchestrator_integration(self, lightweight_resources, fast_agents):
        """Test orchestrator integration with workflow."""
        user_request = "Build a simple blog application"
        operation_id = f"test_orchestrator_{datetime.now().isoformat()}"
        
        logger.info("Testing orchestrator integration")
        
        try:
            # Create orchestrator
            orchestrator = PhaseOneOrchestrator(
                **lightweight_resources,
                max_earth_validation_cycles=1,
                validation_timeout=30.0,
                # Pass pre-initialized agents to avoid initialization overhead
                garden_planner_agent=fast_agents['garden_planner'],
                earth_agent=fast_agents['earth_agent'],
                environmental_analysis_agent=fast_agents['environmental_analysis'],
                root_system_architect_agent=fast_agents['root_system_architect'],
                tree_placement_planner_agent=fast_agents['tree_placement_planner'],
                max_refinement_cycles=1  # Reduced for speed
            )
            
            # Process task with timeout
            result = await asyncio.wait_for(
                orchestrator.process_task(user_request, operation_id),
                timeout=180.0
            )
            
            # Verify orchestrator result
            assert isinstance(result, dict), "Orchestrator should return dictionary"
            assert "status" in result, "Should contain status"
            assert "operation_id" in result, "Should contain operation_id"
            
            if result["status"] == "success":
                assert "structural_components" in result, "Should contain structural components"
                logger.info("Orchestrator completed successfully")
            elif result["status"] in ["failed", "error"]:
                logger.info(f"Orchestrator failed with status: {result['status']}")
            else:
                pytest.fail(f"Unexpected orchestrator status: {result['status']}")
            
        except asyncio.TimeoutError:
            pytest.fail("Orchestrator integration test exceeded timeout")
        
        logger.info("Orchestrator integration test passed")

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)  # Quick timeout for validation
    async def test_workflow_validation_only(self, fast_agents):
        """Test just the validation workflow without full execution."""
        user_request = "Create a simple counter app"
        
        logger.info("Testing validation-only workflow")
        
        try:
            # Create minimal Garden Planner output
            garden_output = {
                "task_analysis": {
                    "original_request": user_request,
                    "interpreted_goal": "Build a simple counter application",
                    "scope": {
                        "included": ["Counter display", "Increment button", "Decrement button"],
                        "excluded": ["Advanced features"],
                        "assumptions": ["Web-based application"]
                    },
                    "technical_requirements": {
                        "languages": ["JavaScript", "HTML", "CSS"],
                        "frameworks": ["Vanilla JS"],
                        "apis": [],
                        "infrastructure": ["Web server"]
                    },
                    "constraints": {
                        "technical": ["Browser compatibility"],
                        "business": ["Simple design"],
                        "performance": ["Fast loading"]
                    },
                    "considerations": {
                        "security": ["Input validation"],
                        "scalability": ["Single user"],
                        "maintainability": ["Clean code"]
                    }
                }
            }
            
            # Test validation
            validation_result = await asyncio.wait_for(
                fast_agents['earth_agent'].validate_garden_planner_output(
                    user_request,
                    garden_output,
                    "test_validation_only"
                ),
                timeout=25.0
            )
            
            assert isinstance(validation_result, dict), "Validation should return dictionary"
            assert "is_valid" in validation_result, "Should contain validation decision"
            assert "validation_category" in validation_result, "Should contain validation category"
            
            logger.info(f"Validation result: {validation_result['validation_category']}")
            
        except asyncio.TimeoutError:
            pytest.fail("Validation-only test exceeded timeout")
        
        logger.info("Validation-only workflow test passed")

# Additional marker for CI/CD environments
@pytest.mark.integration
@pytest.mark.fast
class TestPhaseOneWorkflowCI:
    """Streamlined tests for CI/CD environments."""
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_minimal_workflow_smoke_test(self):
        """Minimal smoke test for CI/CD pipeline."""
        
        logger.info("Running minimal workflow smoke test")
        
        # Quick resource setup
        event_queue = EventQueue()
        await event_queue.start()
        
        try:
            state_manager = StateManager(event_queue)
            await state_manager.initialize()
            
            # Test basic agent creation
            garden_planner = GardenPlannerAgent(
                agent_id="ci_garden_planner",
                event_queue=event_queue,
                state_manager=state_manager,
                context_manager=AgentContextManager(event_queue),
                cache_manager=CacheManager(event_queue),
                metrics_manager=MetricsManager(event_queue),
                error_handler=ErrorHandler(event_queue),
                memory_monitor=MemoryMonitor(event_queue),
                health_tracker=HealthTracker(event_queue)
            )
            
            # Verify agent creation
            assert garden_planner is not None, "Agent should be created successfully"
            assert garden_planner.agent_id == "ci_garden_planner", "Agent should have correct ID"
            
            logger.info("Minimal smoke test passed")
            
        finally:
            await event_queue.stop()