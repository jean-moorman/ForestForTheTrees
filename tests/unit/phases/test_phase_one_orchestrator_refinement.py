"""
Unit tests for Phase One Orchestrator Refinement Workflow

Tests the orchestrator methods that handle Foundation Refinement Agent integration
and the complete Phase Zero → Foundation Refinement → Recursion workflow.
"""
import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from phase_one.orchestrator import PhaseOneOrchestrator
from phase_one.agents.foundation_refinement import FoundationRefinementAgent
from phase_zero import PhaseZeroOrchestrator
from resources import (
    EventQueue, StateManager, AgentContextManager, CacheManager,
    MetricsManager, ErrorHandler, MemoryMonitor, HealthTracker,
    SystemMonitor
)


@pytest.fixture
def mock_resources():
    """Create mock resource managers for testing."""
    return {
        'event_queue': AsyncMock(spec=EventQueue),
        'state_manager': AsyncMock(spec=StateManager),
        'context_manager': AsyncMock(spec=AgentContextManager),
        'cache_manager': AsyncMock(spec=CacheManager),
        'metrics_manager': AsyncMock(spec=MetricsManager),
        'error_handler': AsyncMock(spec=ErrorHandler),
        'memory_monitor': AsyncMock(spec=MemoryMonitor),
        'health_tracker': AsyncMock(spec=HealthTracker),
        'system_monitor': AsyncMock(spec=SystemMonitor)
    }


@pytest.fixture
def mock_phase_zero():
    """Create mock Phase Zero orchestrator."""
    phase_zero = AsyncMock(spec=PhaseZeroOrchestrator)
    phase_zero.process_system_metrics = AsyncMock(return_value={
        "status": "completed",
        "monitoring_analysis": {"system_health": "good"},
        "deep_analysis": {
            "structural_agent": {"status": "success", "flag_raised": False},
            "requirement_agent": {"status": "success", "flag_raised": False}
        },
        "evolution_synthesis": {"recommendations": ["proceed"]}
    })
    return phase_zero


@pytest.fixture
def mock_foundation_refinement_agent():
    """Create mock Foundation Refinement Agent."""
    agent = AsyncMock(spec=FoundationRefinementAgent)
    agent.analyze_phase_one_outputs = AsyncMock(return_value={
        "refinement_analysis": {
            "critical_failure": {"category": "none_detected"},
            "root_cause": {"responsible_agent": "none"},
            "refinement_action": {"action": "proceed_to_phase_two"}
        },
        "confidence_assessment": "high"
    })
    agent.should_proceed_to_phase_two = MagicMock(return_value=True)
    agent.get_refinement_target_agent = MagicMock(return_value=None)
    agent.get_refinement_guidance = MagicMock(return_value={})
    agent.increment_cycle = MagicMock()
    agent._current_cycle = 0
    return agent


@pytest.fixture
def sample_phase_one_result():
    """Sample Phase One workflow result for testing."""
    return {
        "status": "success",
        "message": "Phase One completed successfully",
        "operation_id": "test_operation_123",
        "structural_components": [
            {"name": "component1", "type": "core"},
            {"name": "component2", "type": "utility"}
        ],
        "system_requirements": {
            "task_analysis": {"requirements": ["req1", "req2"]},
            "environmental_analysis": {"constraints": ["constraint1"]},
            "data_architecture": {"flows": ["flow1"]}
        },
        "workflow_result": {
            "status": "completed",
            "final_output": {
                "task_analysis": {"requirements": ["req1", "req2"]},
                "environmental_analysis": {"constraints": ["constraint1"]},
                "data_architecture": {"flows": ["flow1"]},
                "component_architecture": {"components": [
                    {"name": "component1", "type": "core"},
                    {"name": "component2", "type": "utility"}
                ]}
            },
            "metrics": {"execution_time": 30.5}
        }
    }


@pytest.fixture
def sample_workflow_result():
    """Sample workflow result for testing."""
    return {
        "status": "completed",
        "final_output": {
            "task_analysis": {"requirements": ["req1", "req2"]},
            "environmental_analysis": {"constraints": ["constraint1"]},
            "data_architecture": {"flows": ["flow1"]},
            "component_architecture": {"components": [
                {"name": "component1", "type": "core"},
                {"name": "component2", "type": "utility"}
            ]}
        },
        "metrics": {"execution_time": 30.5}
    }


@pytest_asyncio.fixture
async def orchestrator_with_mocks(mock_resources, mock_phase_zero, mock_foundation_refinement_agent):
    """Create orchestrator with mocked dependencies."""
    # Mock system_monitor to return None to avoid async task creation
    mock_resources['system_monitor'] = None
    
    orchestrator = PhaseOneOrchestrator(
        event_queue=mock_resources['event_queue'],
        state_manager=mock_resources['state_manager'],
        context_manager=mock_resources['context_manager'],
        cache_manager=mock_resources['cache_manager'],
        metrics_manager=mock_resources['metrics_manager'],
        error_handler=mock_resources['error_handler'],
        health_tracker=mock_resources['health_tracker'],
        memory_monitor=mock_resources['memory_monitor'],
        system_monitor=mock_resources['system_monitor'],  # This will be None
        phase_zero=mock_phase_zero,
        foundation_refinement_agent=mock_foundation_refinement_agent,
        max_refinement_cycles=3
    )
    
    # Mock the workflow
    orchestrator.phase_one_workflow = AsyncMock()
    orchestrator.phase_one_workflow.execute_phase_one = AsyncMock()
    
    return orchestrator


class TestFoundationRefinementWorkflow:
    """Test the Foundation Refinement workflow execution."""
    
    async def test_execute_foundation_refinement_workflow_success(
        self, 
        orchestrator_with_mocks, 
        sample_phase_one_result,
        sample_workflow_result,
        mock_phase_zero,
        mock_foundation_refinement_agent
    ):
        """Test successful foundation refinement workflow execution."""
        
        # Execute workflow
        result = await orchestrator_with_mocks._execute_foundation_refinement_workflow(
            sample_phase_one_result,
            sample_workflow_result,
            "test_operation_123"
        )
        
        # Verify Phase Zero was called
        mock_phase_zero.process_system_metrics.assert_called_once()
        
        # Verify Phase Zero metrics were properly formatted
        call_args = mock_phase_zero.process_system_metrics.call_args[0][0]
        assert call_args["operation_id"] == "test_operation_123"
        assert call_args["phase_one_result"] == sample_phase_one_result
        assert "workflow_metrics" in call_args
        assert "timestamp" in call_args
        
        # Verify Foundation Refinement Agent was called
        mock_foundation_refinement_agent.analyze_phase_one_outputs.assert_called_once()
        
        # Verify state storage
        orchestrator_with_mocks._state_manager.set_state.assert_called()
        
        # Verify result structure
        assert result is not None
        assert "refinement_analysis" in result
    
    async def test_execute_foundation_refinement_workflow_phase_zero_failure(
        self,
        orchestrator_with_mocks,
        sample_phase_one_result,
        sample_workflow_result,
        mock_phase_zero,
        mock_foundation_refinement_agent
    ):
        """Test workflow when Phase Zero fails."""
        
        # Make Phase Zero fail
        mock_phase_zero.process_system_metrics.side_effect = Exception("Phase Zero error")
        
        # Execute workflow
        result = await orchestrator_with_mocks._execute_foundation_refinement_workflow(
            sample_phase_one_result,
            sample_workflow_result,
            "test_operation_123"
        )
        
        # Verify Phase Zero was attempted
        mock_phase_zero.process_system_metrics.assert_called_once()
        
        # Verify Foundation Refinement Agent was still called with error feedback
        mock_foundation_refinement_agent.analyze_phase_one_outputs.assert_called_once()
        call_args = mock_foundation_refinement_agent.analyze_phase_one_outputs.call_args
        phase_zero_feedback = call_args[0][1]  # Second argument
        
        assert phase_zero_feedback["status"] == "error"
        assert "Phase Zero error" in phase_zero_feedback["error"]
        
        # Verify result is still returned
        assert result is not None
    
    async def test_execute_foundation_refinement_workflow_no_phase_zero(
        self,
        mock_resources,
        sample_phase_one_result,
        sample_workflow_result,
        mock_foundation_refinement_agent
    ):
        """Test workflow when Phase Zero is not available."""
        
        # Create orchestrator without Phase Zero
        orchestrator = PhaseOneOrchestrator(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler'],
            foundation_refinement_agent=mock_foundation_refinement_agent,
            phase_zero=None  # No Phase Zero
        )
        
        # Execute workflow
        result = await orchestrator._execute_foundation_refinement_workflow(
            sample_phase_one_result,
            sample_workflow_result,
            "test_operation_123"
        )
        
        # Verify Foundation Refinement Agent was called with "not_available" feedback
        mock_foundation_refinement_agent.analyze_phase_one_outputs.assert_called_once()
        call_args = mock_foundation_refinement_agent.analyze_phase_one_outputs.call_args
        phase_zero_feedback = call_args[0][1]  # Second argument
        
        assert phase_zero_feedback["status"] == "not_available"
        assert "not configured" in phase_zero_feedback["message"]
        
        # Verify result is returned
        assert result is not None
    
    async def test_execute_foundation_refinement_workflow_agent_failure(
        self,
        orchestrator_with_mocks,
        sample_phase_one_result,
        sample_workflow_result,
        mock_phase_zero,
        mock_foundation_refinement_agent
    ):
        """Test workflow when Foundation Refinement Agent fails."""
        
        # Make Foundation Refinement Agent fail
        mock_foundation_refinement_agent.analyze_phase_one_outputs.side_effect = Exception("Agent error")
        
        # Execute workflow
        result = await orchestrator_with_mocks._execute_foundation_refinement_workflow(
            sample_phase_one_result,
            sample_workflow_result,
            "test_operation_123"
        )
        
        # Verify safe default is returned
        assert result is not None
        assert "refinement_analysis" in result
        assert result["refinement_analysis"]["refinement_action"]["action"] == "proceed_to_phase_two"
        assert result["workflow_error"] is True
        assert "Agent error" in result["error"]


class TestRefinementCycle:
    """Test refinement cycle execution."""
    
    @patch('resources.air_agent.track_decision_event')
    async def test_execute_refinement_cycle_success(
        self,
        mock_track_decision,
        orchestrator_with_mocks,
        sample_phase_one_result,
        mock_foundation_refinement_agent
    ):
        """Test successful refinement cycle execution."""
        
        # Setup refinement result requiring refinement
        refinement_result = {
            "refinement_analysis": {
                "critical_failure": {"category": "dependency_validation_gap"},
                "root_cause": {"responsible_agent": "root_system_architect"},
                "refinement_action": {"action": "restructure_data_flow"}
            }
        }
        
        # Configure mocks
        mock_foundation_refinement_agent.get_refinement_target_agent.return_value = "root_system_architect"
        mock_foundation_refinement_agent.get_refinement_guidance.return_value = {
            "action": "restructure_data_flow",
            "justification": "Need better validation",
            "current_state": "Missing validation",
            "required_state": "Complete validation",
            "adaptation_path": ["Add checks", "Validate dependencies"]
        }
        
        # Execute refinement cycle
        result = await orchestrator_with_mocks._execute_refinement_cycle(
            sample_phase_one_result,
            refinement_result,
            "test_operation_123"
        )
        
        # Verify target agent was identified
        mock_foundation_refinement_agent.get_refinement_target_agent.assert_called_once_with(refinement_result)
        
        # Verify refinement guidance was extracted
        mock_foundation_refinement_agent.get_refinement_guidance.assert_called_once_with(refinement_result)
        
        # Verify cycle was incremented
        mock_foundation_refinement_agent.increment_cycle.assert_called_once()
        
        # Verify Air Agent tracking was attempted
        mock_track_decision.assert_called_once()
        
        # Verify result contains refinement information
        assert result["refinement_analysis"]["status"] == "refinement_attempted"
        assert result["refinement_analysis"]["target_agent"] == "root_system_architect"
        assert "guidance" in result["refinement_analysis"]
    
    async def test_execute_refinement_cycle_no_target_agent(
        self,
        orchestrator_with_mocks,
        sample_phase_one_result,
        mock_foundation_refinement_agent
    ):
        """Test refinement cycle when no target agent is identified."""
        
        refinement_result = {
            "refinement_analysis": {
                "root_cause": {"responsible_agent": "none"}
            }
        }
        
        # Configure mock to return None
        mock_foundation_refinement_agent.get_refinement_target_agent.return_value = None
        
        # Execute refinement cycle
        result = await orchestrator_with_mocks._execute_refinement_cycle(
            sample_phase_one_result,
            refinement_result,
            "test_operation_123"
        )
        
        # Verify original result is returned with refinement analysis added
        assert result["refinement_analysis"] == refinement_result
        
        # Verify cycle was NOT incremented
        mock_foundation_refinement_agent.increment_cycle.assert_not_called()
    
    @patch('resources.air_agent.track_decision_event')
    async def test_execute_refinement_cycle_air_agent_tracking_failure(
        self,
        mock_track_decision,
        orchestrator_with_mocks,
        sample_phase_one_result,
        mock_foundation_refinement_agent
    ):
        """Test refinement cycle when Air Agent tracking fails."""
        
        refinement_result = {
            "refinement_analysis": {
                "root_cause": {"responsible_agent": "garden_planner"},
                "refinement_action": {"action": "reanalyze_task"}
            }
        }
        
        # Configure mocks
        mock_foundation_refinement_agent.get_refinement_target_agent.return_value = "garden_planner"
        mock_foundation_refinement_agent.get_refinement_guidance.return_value = {"action": "reanalyze_task"}
        
        # Make Air Agent tracking fail
        mock_track_decision.side_effect = Exception("Air Agent error")
        
        # Execute refinement cycle (should not fail)
        result = await orchestrator_with_mocks._execute_refinement_cycle(
            sample_phase_one_result,
            refinement_result,
            "test_operation_123"
        )
        
        # Verify cycle continues despite Air Agent error
        assert result["refinement_analysis"]["status"] == "refinement_attempted"
        assert result["refinement_analysis"]["target_agent"] == "garden_planner"
        
        # Verify cycle was still incremented
        mock_foundation_refinement_agent.increment_cycle.assert_called_once()
    
    async def test_execute_refinement_cycle_exception_handling(
        self,
        orchestrator_with_mocks,
        sample_phase_one_result,
        mock_foundation_refinement_agent
    ):
        """Test refinement cycle exception handling."""
        
        refinement_result = {
            "refinement_analysis": {
                "root_cause": {"responsible_agent": "garden_planner"}
            }
        }
        
        # Make get_refinement_target_agent raise exception
        mock_foundation_refinement_agent.get_refinement_target_agent.side_effect = Exception("Target error")
        
        # Execute refinement cycle
        result = await orchestrator_with_mocks._execute_refinement_cycle(
            sample_phase_one_result,
            refinement_result,
            "test_operation_123"
        )
        
        # Verify error is handled gracefully
        assert result["refinement_analysis"] == refinement_result
        assert "refinement_error" in result
        assert "Target error" in result["refinement_error"]["error"]


class TestOrchestrationProcessTaskRefinementIntegration:
    """Test the integration of refinement workflow in process_task."""
    
    async def test_process_task_with_refinement_needed(
        self,
        orchestrator_with_mocks,
        mock_foundation_refinement_agent
    ):
        """Test process_task when refinement is needed."""
        
        # Setup workflow to return successful result
        workflow_result = {
            "status": "completed",
            "final_output": {
                "task_analysis": {"requirements": ["req1"]},
                "component_architecture": {"components": ["comp1"]}
            }
        }
        orchestrator_with_mocks.phase_one_workflow.execute_phase_one.return_value = workflow_result
        
        # Setup Foundation Refinement Agent to require refinement
        refinement_result = {
            "refinement_analysis": {
                "critical_failure": {"category": "validation_gap"},
                "root_cause": {"responsible_agent": "garden_planner"},
                "refinement_action": {"action": "reanalyze_task"}
            }
        }
        mock_foundation_refinement_agent.analyze_phase_one_outputs.return_value = refinement_result
        mock_foundation_refinement_agent.should_proceed_to_phase_two.return_value = False  # Refinement needed
        mock_foundation_refinement_agent.get_refinement_target_agent.return_value = "garden_planner"
        mock_foundation_refinement_agent.get_refinement_guidance.return_value = {"action": "reanalyze_task"}
        
        # Execute process_task
        result = await orchestrator_with_mocks._process_task_internal(
            "Test user request",
            "test_operation_123"
        )
        
        # Verify workflow was executed
        orchestrator_with_mocks.phase_one_workflow.execute_phase_one.assert_called_once()
        
        # Verify Foundation Refinement Agent was called
        mock_foundation_refinement_agent.analyze_phase_one_outputs.assert_called_once()
        mock_foundation_refinement_agent.should_proceed_to_phase_two.assert_called_once()
        
        # Verify refinement cycle was executed
        assert result["refinement_analysis"]["status"] == "refinement_attempted"
        assert result["refinement_analysis"]["target_agent"] == "garden_planner"
    
    async def test_process_task_no_refinement_needed(
        self,
        orchestrator_with_mocks,
        mock_foundation_refinement_agent
    ):
        """Test process_task when no refinement is needed."""
        
        # Setup workflow to return successful result
        workflow_result = {
            "status": "completed",
            "final_output": {
                "task_analysis": {"requirements": ["req1"]},
                "component_architecture": {"components": ["comp1"]}
            }
        }
        orchestrator_with_mocks.phase_one_workflow.execute_phase_one.return_value = workflow_result
        
        # Setup Foundation Refinement Agent to proceed
        refinement_result = {
            "refinement_analysis": {
                "critical_failure": {"category": "none_detected"},
                "root_cause": {"responsible_agent": "none"},
                "refinement_action": {"action": "proceed_to_phase_two"}
            },
            "confidence_assessment": "high"
        }
        mock_foundation_refinement_agent.analyze_phase_one_outputs.return_value = refinement_result
        mock_foundation_refinement_agent.should_proceed_to_phase_two.return_value = True  # No refinement needed
        
        # Execute process_task
        result = await orchestrator_with_mocks._process_task_internal(
            "Test user request",
            "test_operation_123"
        )
        
        # Verify workflow was executed
        orchestrator_with_mocks.phase_one_workflow.execute_phase_one.assert_called_once()
        
        # Verify Foundation Refinement Agent was called
        mock_foundation_refinement_agent.analyze_phase_one_outputs.assert_called_once()
        mock_foundation_refinement_agent.should_proceed_to_phase_two.assert_called_once()
        
        # Verify no refinement cycle was executed
        mock_foundation_refinement_agent.increment_cycle.assert_not_called()
        
        # Verify result contains refinement analysis
        assert result["refinement_analysis"] == refinement_result
        assert result["status"] == "success"
    
    async def test_process_task_workflow_failure(
        self,
        orchestrator_with_mocks,
        mock_foundation_refinement_agent
    ):
        """Test process_task when workflow fails."""
        
        # Setup workflow to fail
        workflow_result = {
            "status": "failed",
            "failure_stage": "garden_planner",
            "error": "Garden planner validation failed"
        }
        orchestrator_with_mocks.phase_one_workflow.execute_phase_one.return_value = workflow_result
        
        # Execute process_task
        result = await orchestrator_with_mocks._process_task_internal(
            "Test user request",
            "test_operation_123"
        )
        
        # Verify workflow was executed
        orchestrator_with_mocks.phase_one_workflow.execute_phase_one.assert_called_once()
        
        # Verify Foundation Refinement Agent was NOT called for failed workflow
        mock_foundation_refinement_agent.analyze_phase_one_outputs.assert_not_called()
        
        # Verify failure result
        assert result["status"] == "failed"
        assert result["failure_stage"] == "garden_planner"
        assert "Garden planner validation failed" in result["error"]


class TestRefinementWorkflowStateManagement:
    """Test state management during refinement workflows."""
    
    async def test_state_storage_during_refinement_workflow(
        self,
        orchestrator_with_mocks,
        sample_phase_one_result,
        sample_workflow_result,
        mock_phase_zero,
        mock_foundation_refinement_agent
    ):
        """Test that state is properly stored during refinement workflow."""
        
        # Execute workflow
        await orchestrator_with_mocks._execute_foundation_refinement_workflow(
            sample_phase_one_result,
            sample_workflow_result,
            "test_operation_123"
        )
        
        # Verify multiple state storage calls
        state_calls = orchestrator_with_mocks._state_manager.set_state.call_args_list
        
        # Should have stored Phase Zero feedback and complete refinement workflow
        stored_keys = [call[0][0] for call in state_calls]
        
        assert any("phase_zero_feedback" in key for key in stored_keys)
        assert any("refinement_workflow" in key for key in stored_keys)
    
    async def test_event_emission_during_refinement(
        self,
        orchestrator_with_mocks,
        sample_phase_one_result,
        mock_foundation_refinement_agent
    ):
        """Test that events are properly emitted during refinement cycle."""
        
        refinement_result = {
            "refinement_analysis": {
                "root_cause": {"responsible_agent": "garden_planner"},
                "refinement_action": {"action": "reanalyze_task"}
            }
        }
        
        mock_foundation_refinement_agent.get_refinement_target_agent.return_value = "garden_planner"
        
        # Execute refinement cycle
        with patch('phase_one.orchestrator.track_decision_event') as mock_track:
            await orchestrator_with_mocks._execute_refinement_cycle(
                sample_phase_one_result,
                refinement_result,
                "test_operation_123"
            )
            
            # Verify Air Agent decision tracking was attempted
            mock_track.assert_called_once()
            call_args = mock_track.call_args[1]  # kwargs
            assert call_args["agent_id"] == "foundation_refinement_agent"
            assert call_args["decision_type"] == "refinement_cycle"
            assert "operation_id" in call_args["decision_data"]
            assert "target_agent" in call_args["decision_data"]


class TestRefinementWorkflowErrorRecovery:
    """Test error recovery scenarios in refinement workflows."""
    
    async def test_refinement_workflow_graceful_degradation(
        self,
        orchestrator_with_mocks,
        sample_phase_one_result,
        sample_workflow_result,
        mock_phase_zero,
        mock_foundation_refinement_agent
    ):
        """Test graceful degradation when refinement workflow components fail."""
        
        # Make both Phase Zero and Foundation Refinement Agent fail
        mock_phase_zero.process_system_metrics.side_effect = Exception("Phase Zero error")
        mock_foundation_refinement_agent.analyze_phase_one_outputs.side_effect = Exception("Agent error")
        
        # Execute workflow
        result = await orchestrator_with_mocks._execute_foundation_refinement_workflow(
            sample_phase_one_result,
            sample_workflow_result,
            "test_operation_123"
        )
        
        # Verify safe default is returned
        assert result is not None
        assert result["refinement_analysis"]["refinement_action"]["action"] == "proceed_to_phase_two"
        assert result["workflow_error"] is True
        assert "Agent error" in result["error"]
    
    async def test_circuit_breaker_protection_in_workflow(
        self,
        orchestrator_with_mocks,
        sample_phase_one_result,
        sample_workflow_result,
        mock_foundation_refinement_agent
    ):
        """Test circuit breaker protection during workflow execution."""
        
        # Mock Foundation Refinement Agent to return circuit breaker result
        circuit_breaker_result = {
            "refinement_analysis": {
                "critical_failure": {"category": "circuit_breaker_open"},
                "refinement_action": {"action": "proceed_to_phase_two"}
            },
            "circuit_breaker_protection": True,
            "confidence_assessment": "low"
        }
        mock_foundation_refinement_agent.analyze_phase_one_outputs.return_value = circuit_breaker_result
        
        # Execute workflow
        result = await orchestrator_with_mocks._execute_foundation_refinement_workflow(
            sample_phase_one_result,
            sample_workflow_result,
            "test_operation_123"
        )
        
        # Verify circuit breaker protection is preserved
        assert result["circuit_breaker_protection"] is True
        assert result["confidence_assessment"] == "low"
        assert result["refinement_analysis"]["refinement_action"]["action"] == "proceed_to_phase_two"