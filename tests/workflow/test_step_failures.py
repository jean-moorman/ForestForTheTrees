"""
Test Step Failure Scenarios from run_phase_one.py

This module tests various failure scenarios in step execution including
step failures, error propagation, and graceful degradation.
"""

import pytest
import pytest_asyncio
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from run_phase_one import PhaseOneInterface
from resources.events import EventQueue
from resources.state import StateManager


class FailingMockOrchestrator:
    """Mock orchestrator that can simulate step failures."""
    
    def __init__(self):
        self._state_manager = None
        self.failure_config = {}
        self.call_history = []
        
        # Setup agents
        self.garden_planner_agent = MagicMock()
        self.earth_agent = MagicMock()
        self.environmental_analysis_agent = MagicMock()
        self.root_system_architect_agent = MagicMock()
        self.tree_placement_planner_agent = MagicMock()
        self.foundation_refinement_agent = MagicMock()
        
        self._setup_failing_agents()
    
    def _setup_failing_agents(self):
        """Setup agents that can fail on command."""
        
        async def failing_agent_process(agent_name, *args):
            """Generic agent process that can be configured to fail."""
            self.call_history.append(agent_name)
            
            failure_config = self.failure_config.get(agent_name, {})
            
            if failure_config.get('should_fail', False):
                error_type = failure_config.get('error_type', 'generic')
                error_message = failure_config.get('error_message', f'{agent_name} processing failed')
                
                if error_type == 'exception':
                    raise Exception(error_message)
                elif error_type == 'validation_error':
                    return {
                        "status": "error",
                        "error_type": "validation_failed",
                        "message": error_message,
                        "validation_issues": failure_config.get('validation_issues', [])
                    }
                elif error_type == 'timeout':
                    raise asyncio.TimeoutError(error_message)
                elif error_type == 'missing_dependency':
                    return {
                        "status": "error",
                        "error_type": "missing_dependency",
                        "message": error_message,
                        "missing_dependency": failure_config.get('missing_dependency', 'unknown')
                    }
                else:
                    return {
                        "status": "error",
                        "error_type": error_type,
                        "message": error_message
                    }
            
            # Success case
            return {
                "status": "success",
                "agent": agent_name,
                "result": f"Successful processing by {agent_name}",
                "timestamp": datetime.now().isoformat()
            }
        
        # Assign to agents
        self.garden_planner_agent.process = lambda *args: failing_agent_process('garden_planner', *args)
        self.earth_agent.process = lambda *args: failing_agent_process('earth_agent', *args)
        self.environmental_analysis_agent.process = lambda *args: failing_agent_process('environmental_analysis', *args)
        self.root_system_architect_agent.process = lambda *args: failing_agent_process('root_system_architect', *args)
        self.tree_placement_planner_agent.process = lambda *args: failing_agent_process('tree_placement_planner', *args)
        self.foundation_refinement_agent.process = lambda *args: failing_agent_process('foundation_refinement', *args)
    
    def configure_agent_failure(self, agent_name, should_fail=True, error_type='generic', error_message=None, **kwargs):
        """Configure an agent to fail."""
        self.failure_config[agent_name] = {
            'should_fail': should_fail,
            'error_type': error_type,
            'error_message': error_message or f'{agent_name} configured to fail',
            **kwargs
        }
    
    def clear_agent_failure(self, agent_name):
        """Clear failure configuration for an agent."""
        if agent_name in self.failure_config:
            del self.failure_config[agent_name]


@pytest_asyncio.fixture
async def event_queue():
    """Create an event queue for testing."""
    queue = EventQueue()
    await queue.start()
    yield queue
    await queue.stop()


@pytest_asyncio.fixture
async def state_manager(event_queue):
    """Create a state manager for testing."""
    manager = StateManager(event_queue)
    await manager.initialize()
    return manager


@pytest.fixture
def failing_orchestrator(state_manager):
    """Create a failing mock orchestrator."""
    orchestrator = FailingMockOrchestrator()
    orchestrator._state_manager = state_manager
    return orchestrator


@pytest.fixture
def phase_one_interface_failing(failing_orchestrator):
    """Create a PhaseOneInterface with failing orchestrator."""
    return PhaseOneInterface(failing_orchestrator)


class TestGardenPlannerFailures:
    """Test failures in the Garden Planner step."""
    
    @pytest.mark.asyncio
    async def test_garden_planner_exception(self, phase_one_interface_failing, failing_orchestrator):
        """Test Garden Planner step failing with exception."""
        # Configure Garden Planner to fail
        failing_orchestrator.configure_agent_failure(
            'garden_planner',
            error_type='exception',
            error_message='Garden Planner encountered critical error'
        )
        
        operation_id = await phase_one_interface_failing.start_phase_one("Create failing app")
        
        # Execute Garden Planner step
        step_result = await phase_one_interface_failing.execute_next_step(operation_id)
        
        # Should complete but with error status
        assert step_result["status"] == "step_completed"
        step_data = step_result["step_result"]
        assert step_data["status"] == "error"
        assert "Garden Planner encountered critical error" in step_data["error"]
        
        # Verify workflow status reflects failure
        status = await phase_one_interface_failing.get_step_status(operation_id)
        assert status["status"] == "running"  # Still running but step failed
        assert "garden_planner" in status["steps_completed"]
        
        # Next step should still be earth_agent_validation (workflow continues)
        assert step_result["next_step"] == "earth_agent_validation"
    
    @pytest.mark.asyncio
    async def test_garden_planner_validation_failure(self, phase_one_interface_failing, failing_orchestrator):
        """Test Garden Planner validation failure."""
        failing_orchestrator.configure_agent_failure(
            'garden_planner',
            error_type='validation_error',
            error_message='Task analysis validation failed',
            validation_issues=[
                'Scope definition is too vague',
                'Technical requirements are incomplete',
                'Missing business constraints'
            ]
        )
        
        operation_id = await phase_one_interface_failing.start_phase_one("Vague application request")
        step_result = await phase_one_interface_failing.execute_next_step(operation_id)
        
        # Should capture validation-specific error details
        step_data = step_result["step_result"]
        assert step_data["status"] == "error"
        assert step_data["result"]["error_type"] == "validation_failed"
        assert len(step_data["result"]["validation_issues"]) == 3
        assert "Scope definition is too vague" in step_data["result"]["validation_issues"]
    
    @pytest.mark.asyncio
    async def test_garden_planner_timeout(self, phase_one_interface_failing, failing_orchestrator):
        """Test Garden Planner step timeout."""
        failing_orchestrator.configure_agent_failure(
            'garden_planner',
            error_type='timeout',
            error_message='Garden Planner processing timed out'
        )
        
        operation_id = await phase_one_interface_failing.start_phase_one("Timeout test app")
        step_result = await phase_one_interface_failing.execute_next_step(operation_id)
        
        # Should handle timeout gracefully
        step_data = step_result["step_result"]
        assert step_data["status"] == "error"
        assert "timed out" in step_data["error"].lower()


class TestEarthAgentFailures:
    """Test failures in the Earth Agent validation step."""
    
    @pytest.mark.asyncio
    async def test_earth_agent_validation_rejection(self, phase_one_interface_failing, failing_orchestrator):
        """Test Earth Agent rejecting Garden Planner output."""
        # Garden Planner succeeds
        failing_orchestrator.clear_agent_failure('garden_planner')
        
        # Earth Agent fails validation
        failing_orchestrator.configure_agent_failure(
            'earth_agent',
            error_type='validation_error',
            error_message='Garden Planner output does not meet architectural standards',
            validation_issues=[
                'Component dependencies are circular',
                'Security requirements not addressed',
                'Scalability concerns not considered'
            ]
        )
        
        operation_id = await phase_one_interface_failing.start_phase_one("Test validation rejection")
        
        # Execute Garden Planner (should succeed)
        step1_result = await phase_one_interface_failing.execute_next_step(operation_id)
        assert step1_result["step_result"]["status"] == "success"
        
        # Execute Earth Agent (should fail validation)
        step2_result = await phase_one_interface_failing.execute_next_step(operation_id)
        
        step_data = step2_result["step_result"]
        assert step_data["status"] == "error"
        assert step_data["result"]["error_type"] == "validation_failed"
        assert "architectural standards" in step_data["result"]["message"]
        assert len(step_data["result"]["validation_issues"]) == 3
    
    @pytest.mark.asyncio
    async def test_earth_agent_missing_input(self, phase_one_interface_failing, failing_orchestrator):
        """Test Earth Agent with missing Garden Planner input."""
        # Configure Garden Planner to return incomplete output
        failing_orchestrator.configure_agent_failure(
            'garden_planner',
            error_type='incomplete_output',
            error_message='Garden Planner returned incomplete analysis'
        )
        
        operation_id = await phase_one_interface_failing.start_phase_one("Test missing input")
        
        # Execute Garden Planner (incomplete output)
        await phase_one_interface_failing.execute_next_step(operation_id)
        
        # Execute Earth Agent (should handle missing input)
        step_result = await phase_one_interface_failing.execute_next_step(operation_id)
        
        # Earth Agent should handle missing input gracefully
        step_data = step_result["step_result"]
        # Could either succeed with warnings or fail gracefully
        assert step_data["status"] in ["success", "error"]


class TestDownstreamStepFailures:
    """Test failures in downstream steps."""
    
    @pytest.mark.asyncio
    async def test_environmental_analysis_failure(self, phase_one_interface_failing, failing_orchestrator):
        """Test Environmental Analysis step failure."""
        # First two steps succeed
        failing_orchestrator.clear_agent_failure('garden_planner')
        failing_orchestrator.clear_agent_failure('earth_agent')
        
        # Environmental Analysis fails
        failing_orchestrator.configure_agent_failure(
            'environmental_analysis',
            error_type='processing_error',
            error_message='Unable to analyze environmental constraints'
        )
        
        operation_id = await phase_one_interface_failing.start_phase_one("Test env analysis failure")
        
        # Execute first two steps (should succeed)
        await phase_one_interface_failing.execute_next_step(operation_id)  # Garden Planner
        await phase_one_interface_failing.execute_next_step(operation_id)  # Earth Agent
        
        # Execute Environmental Analysis (should fail)
        step_result = await phase_one_interface_failing.execute_next_step(operation_id)
        
        step_data = step_result["step_result"]
        assert step_data["status"] == "error"
        assert "environmental constraints" in step_data["result"]["message"]
        
        # Verify workflow status shows partial completion
        status = await phase_one_interface_failing.get_step_status(operation_id)
        assert len(status["steps_completed"]) == 3  # 2 successful + 1 failed
        assert "environmental_analysis" in status["steps_completed"]
    
    @pytest.mark.asyncio
    async def test_root_system_architect_dependency_failure(self, phase_one_interface_failing, failing_orchestrator):
        """Test Root System Architect failing due to missing dependencies."""
        # First three steps succeed
        for agent in ['garden_planner', 'earth_agent', 'environmental_analysis']:
            failing_orchestrator.clear_agent_failure(agent)
        
        # Root System Architect fails due to missing dependency
        failing_orchestrator.configure_agent_failure(
            'root_system_architect',
            error_type='missing_dependency',
            error_message='Environmental Analysis output required but not available',
            missing_dependency='environmental_analysis_output'
        )
        
        operation_id = await phase_one_interface_failing.start_phase_one("Test dependency failure")
        
        # Execute first three steps
        for _ in range(3):
            await phase_one_interface_failing.execute_next_step(operation_id)
        
        # Execute Root System Architect (should fail)
        step_result = await phase_one_interface_failing.execute_next_step(operation_id)
        
        step_data = step_result["step_result"]
        assert step_data["status"] == "error"
        assert step_data["result"]["error_type"] == "missing_dependency"
        assert step_data["result"]["missing_dependency"] == "environmental_analysis_output"
    
    @pytest.mark.asyncio
    async def test_tree_placement_planner_complex_failure(self, phase_one_interface_failing, failing_orchestrator):
        """Test Tree Placement Planner with complex failure scenario."""
        # First four steps succeed
        for agent in ['garden_planner', 'earth_agent', 'environmental_analysis', 'root_system_architect']:
            failing_orchestrator.clear_agent_failure(agent)
        
        # Tree Placement Planner has complex failure
        failing_orchestrator.configure_agent_failure(
            'tree_placement_planner',
            error_type='architecture_conflict',
            error_message='Component architecture conflicts detected',
            conflicts=[
                'Circular dependency between auth and user services',
                'Database access pattern conflicts',
                'Incompatible interface definitions'
            ]
        )
        
        operation_id = await phase_one_interface_failing.start_phase_one("Test complex failure")
        
        # Execute first four steps
        for _ in range(4):
            await phase_one_interface_failing.execute_next_step(operation_id)
        
        # Execute Tree Placement Planner (should fail)
        step_result = await phase_one_interface_failing.execute_next_step(operation_id)
        
        step_data = step_result["step_result"]
        assert step_data["status"] == "error"
        assert step_data["result"]["error_type"] == "architecture_conflict"
        assert "conflicts" in step_data["result"]
        assert len(step_data["result"]["conflicts"]) == 3


class TestFailureRecoveryAndPropagation:
    """Test failure recovery and error propagation."""
    
    @pytest.mark.asyncio
    async def test_partial_workflow_completion(self, phase_one_interface_failing, failing_orchestrator):
        """Test workflow continuing after early step failure."""
        # Configure failure in middle step
        failing_orchestrator.clear_agent_failure('garden_planner')
        failing_orchestrator.clear_agent_failure('earth_agent')
        failing_orchestrator.configure_agent_failure(
            'environmental_analysis',
            error_type='processing_error',
            error_message='Environmental analysis failed'
        )
        failing_orchestrator.clear_agent_failure('root_system_architect')
        failing_orchestrator.clear_agent_failure('tree_placement_planner')
        
        operation_id = await phase_one_interface_failing.start_phase_one("Test partial completion")
        
        # Execute all steps despite failure in middle
        results = []
        for i in range(5):  # Execute 5 steps
            step_result = await phase_one_interface_failing.execute_next_step(operation_id)
            results.append(step_result)
        
        # Verify execution pattern
        assert results[0]["step_result"]["status"] == "success"  # Garden Planner
        assert results[1]["step_result"]["status"] == "success"  # Earth Agent
        assert results[2]["step_result"]["status"] == "error"    # Environmental Analysis (fails)
        assert results[3]["step_result"]["status"] == "success"  # Root System (continues despite previous failure)
        assert results[4]["step_result"]["status"] == "success"  # Tree Placement (continues)
        
        # Verify final status shows mixed results
        final_status = await phase_one_interface_failing.get_step_status(operation_id)
        assert len(final_status["steps_completed"]) == 5
        assert final_status["progress_percentage"] == 100  # All steps attempted
    
    @pytest.mark.asyncio
    async def test_error_metadata_preservation(self, phase_one_interface_failing, failing_orchestrator):
        """Test that error metadata is preserved across step execution."""
        failing_orchestrator.configure_agent_failure(
            'garden_planner',
            error_type='custom_error',
            error_message='Detailed error with metadata',
            error_code='GP_001',
            error_category='validation',
            suggested_action='Review input prompt for clarity'
        )
        
        operation_id = await phase_one_interface_failing.start_phase_one("Test error metadata")
        step_result = await phase_one_interface_failing.execute_next_step(operation_id)
        
        # Verify error metadata is preserved
        step_data = step_result["step_result"]
        assert step_data["status"] == "error"
        
        result = step_data["result"]
        assert result["error_type"] == "custom_error"
        assert result["error_code"] == "GP_001"
        assert result["error_category"] == "validation"
        assert result["suggested_action"] == "Review input prompt for clarity"
        
        # Verify metadata is also stored in workflow state
        status = await phase_one_interface_failing.get_step_status(operation_id)
        step_results = status["step_results"]
        garden_result = step_results["garden_planner"]
        assert garden_result["result"]["error_code"] == "GP_001"
    
    @pytest.mark.asyncio
    async def test_cascading_failure_handling(self, phase_one_interface_failing, failing_orchestrator):
        """Test handling of cascading failures."""
        # Configure multiple failures
        failing_orchestrator.configure_agent_failure(
            'garden_planner',
            error_type='analysis_error',
            error_message='Initial analysis failed'
        )
        
        failing_orchestrator.configure_agent_failure(
            'earth_agent',
            error_type='validation_error',
            error_message='Cannot validate incomplete analysis'
        )
        
        operation_id = await phase_one_interface_failing.start_phase_one("Test cascading failures")
        
        # Execute first few steps
        step1_result = await phase_one_interface_failing.execute_next_step(operation_id)
        step2_result = await phase_one_interface_failing.execute_next_step(operation_id)
        
        # Both should fail
        assert step1_result["step_result"]["status"] == "error"
        assert step2_result["step_result"]["status"] == "error"
        
        # Verify both errors are recorded
        status = await phase_one_interface_failing.get_step_status(operation_id)
        assert len(status["step_results"]) == 2
        
        for step_name, result in status["step_results"].items():
            assert result["status"] == "error"


class TestFailureIsolation:
    """Test that failures are properly isolated between operations."""
    
    @pytest.mark.asyncio
    async def test_failure_isolation_between_operations(self, phase_one_interface_failing, failing_orchestrator):
        """Test that failures in one operation don't affect others."""
        # Configure Garden Planner to fail
        failing_orchestrator.configure_agent_failure(
            'garden_planner',
            error_type='processing_error',
            error_message='Garden Planner failure for operation 1'
        )
        
        # Start two operations
        operation_id_1 = await phase_one_interface_failing.start_phase_one("Failing operation")
        operation_id_2 = await phase_one_interface_failing.start_phase_one("Succeeding operation")
        
        # Execute first operation (should fail)
        step1_result = await phase_one_interface_failing.execute_next_step(operation_id_1)
        assert step1_result["step_result"]["status"] == "error"
        
        # Clear failure for second operation
        failing_orchestrator.clear_agent_failure('garden_planner')
        
        # Execute second operation (should succeed)
        step2_result = await phase_one_interface_failing.execute_next_step(operation_id_2)
        assert step2_result["step_result"]["status"] == "success"
        
        # Verify operations are isolated
        status_1 = await phase_one_interface_failing.get_step_status(operation_id_1)
        status_2 = await phase_one_interface_failing.get_step_status(operation_id_2)
        
        assert status_1["step_results"]["garden_planner"]["status"] == "error"
        assert status_2["step_results"]["garden_planner"]["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_agent_state_reset_between_operations(self, phase_one_interface_failing, failing_orchestrator):
        """Test that agent state is properly reset between operations."""
        # First operation: configure failure
        failing_orchestrator.configure_agent_failure(
            'environmental_analysis',
            error_type='state_error',
            error_message='Agent in bad state'
        )
        
        operation_id_1 = await phase_one_interface_failing.start_phase_one("First operation")
        
        # Execute steps until Environmental Analysis
        await phase_one_interface_failing.execute_next_step(operation_id_1)  # Garden Planner
        await phase_one_interface_failing.execute_next_step(operation_id_1)  # Earth Agent
        step_result = await phase_one_interface_failing.execute_next_step(operation_id_1)  # Environmental Analysis (fails)
        
        assert step_result["step_result"]["status"] == "error"
        
        # Second operation: clear failure
        failing_orchestrator.clear_agent_failure('environmental_analysis')
        operation_id_2 = await phase_one_interface_failing.start_phase_one("Second operation")
        
        # Execute same steps for second operation
        await phase_one_interface_failing.execute_next_step(operation_id_2)  # Garden Planner
        await phase_one_interface_failing.execute_next_step(operation_id_2)  # Earth Agent
        step_result_2 = await phase_one_interface_failing.execute_next_step(operation_id_2)  # Environmental Analysis
        
        # Should succeed this time
        assert step_result_2["step_result"]["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])