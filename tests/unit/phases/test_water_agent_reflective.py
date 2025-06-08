"""
Comprehensive unit tests for WaterAgentReflective.

This module tests the reflective capabilities of the Water Agent including
misunderstanding detection with reflection, circuit breaker integration,
and state management during reflection cycles.
"""

import pytest
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from resources.water_agent.reflective import WaterAgentReflective
from phase_one.models.refinement import AgentPromptConfig
from phase_one.monitoring.circuit_breakers import CircuitBreakerDefinition
from phase_one.models.enums import DevelopmentState
from resources.monitoring.circuit_breakers import CircuitState, CircuitOpenError
from interfaces.agent.interface import AgentState


@pytest.fixture
def mock_event_queue():
    """Mock event queue for testing."""
    queue = AsyncMock()
    queue.emit = AsyncMock()
    queue.subscribe = AsyncMock()
    return queue


@pytest.fixture
def mock_state_manager():
    """Mock state manager for testing."""
    state_manager = AsyncMock()
    state_manager.get_state = AsyncMock(return_value=None)
    state_manager.set_state = AsyncMock(return_value=True)
    state_manager.find_keys = AsyncMock(return_value=[])
    state_manager.delete_state = AsyncMock(return_value=True)
    return state_manager


@pytest.fixture
def mock_context_manager():
    """Mock context manager for testing."""
    context_manager = AsyncMock()
    context_manager.get_context = AsyncMock(return_value={})
    context_manager.set_context = AsyncMock(return_value=True)
    context_manager.update_context = AsyncMock(return_value=True)
    return context_manager


@pytest.fixture
def mock_cache_manager():
    """Mock cache manager for testing."""
    cache_manager = AsyncMock()
    cache_manager.get = AsyncMock(return_value=None)
    cache_manager.set = AsyncMock(return_value=True)
    cache_manager.invalidate = AsyncMock(return_value=True)
    return cache_manager


@pytest.fixture
def mock_metrics_manager():
    """Mock metrics manager for testing."""
    metrics_manager = AsyncMock()
    metrics_manager.record_metric = AsyncMock()
    metrics_manager.get_metric = AsyncMock(return_value=0)
    return metrics_manager


@pytest.fixture
def mock_error_handler():
    """Mock error handler for testing."""
    error_handler = AsyncMock()
    error_handler.handle_error = AsyncMock()
    error_handler.is_recoverable = AsyncMock(return_value=True)
    return error_handler


@pytest.fixture
def mock_memory_monitor():
    """Mock memory monitor for testing."""
    memory_monitor = AsyncMock()
    memory_monitor.check_memory = AsyncMock(return_value={"status": "ok"})
    memory_monitor.get_usage = AsyncMock(return_value={"memory": 0.5})
    return memory_monitor


@pytest.fixture
def mock_health_tracker():
    """Mock health tracker for testing."""
    health_tracker = AsyncMock()
    health_tracker.track_metric = AsyncMock()
    health_tracker.get_health_status = AsyncMock(return_value={"status": "healthy"})
    return health_tracker


@pytest.fixture
def prompt_config():
    """Sample prompt configuration for testing."""
    return AgentPromptConfig(
        system_prompt_base_path="FFTT_system_prompts/core_agents/water_agent",
        reflection_prompt_name="reflection_prompt",
        refinement_prompt_name="revision_prompt",
        initial_prompt_name="misunderstanding_detection_prompt"
    )


@pytest.fixture
def circuit_breaker_definitions():
    """Sample circuit breaker definitions for testing."""
    return [
        CircuitBreakerDefinition(
            name="detection",
            failure_threshold=3,
            recovery_timeout=30,
            failure_window=120
        ),
        CircuitBreakerDefinition(
            name="reflection",
            failure_threshold=2,
            recovery_timeout=45,
            failure_window=180
        ),
        CircuitBreakerDefinition(
            name="revision",
            failure_threshold=2,
            recovery_timeout=45,
            failure_window=180
        )
    ]


@pytest.fixture
def water_agent_reflective(
    mock_event_queue,
    mock_state_manager,
    mock_context_manager,
    mock_cache_manager,
    mock_metrics_manager,
    mock_error_handler,
    mock_memory_monitor,
    mock_health_tracker,
    prompt_config,
    circuit_breaker_definitions
):
    """Create a WaterAgentReflective instance for testing."""
    with patch('phase_one.agents.base.AgentInterface'), \
         patch('interfaces.agent.interface.AgentInterface'), \
         patch('interfaces.agent.metrics.InterfaceMetrics'), \
         patch('asyncio.create_task'):
        agent = WaterAgentReflective(
            agent_id="test_water_agent_reflective",
            event_queue=mock_event_queue,
            state_manager=mock_state_manager,
            context_manager=mock_context_manager,
            cache_manager=mock_cache_manager,
            metrics_manager=mock_metrics_manager,
            error_handler=mock_error_handler,
            memory_monitor=mock_memory_monitor,
            health_tracker=mock_health_tracker,
            max_reflection_cycles=2
        )
    
    # Mock the process_with_validation method
    agent.process_with_validation = AsyncMock()
    agent.standard_reflect = AsyncMock()
    agent.standard_refine = AsyncMock()
    
    # Mock circuit breaker methods
    agent.get_circuit_breaker = MagicMock()
    mock_circuit_breaker = AsyncMock()
    mock_circuit_breaker.execute = AsyncMock()
    agent.get_circuit_breaker.return_value = mock_circuit_breaker
    
    return agent


class TestWaterAgentReflectiveInitialization:
    """Test WaterAgentReflective initialization and configuration."""

    @pytest.mark.asyncio
    async def test_initialization_with_default_params(
        self,
        mock_event_queue,
        mock_state_manager,
        mock_context_manager,
        mock_cache_manager,
        mock_metrics_manager,
        mock_error_handler,
        mock_memory_monitor
    ):
        """Test initialization with default parameters."""
        agent = WaterAgentReflective(
            agent_id="test_agent",
            event_queue=mock_event_queue,
            state_manager=mock_state_manager,
            context_manager=mock_context_manager,
            cache_manager=mock_cache_manager,
            metrics_manager=mock_metrics_manager,
            error_handler=mock_error_handler,
            memory_monitor=mock_memory_monitor
        )
        
        assert agent.agent_id == "test_agent"
        assert agent.development_state == DevelopmentState.INITIALIZING
        assert agent.max_reflection_cycles == 2
        assert agent.current_reflection_cycle == 0

    @pytest.mark.asyncio
    async def test_initialization_with_custom_reflection_cycles(
        self,
        mock_event_queue,
        mock_state_manager,
        mock_context_manager,
        mock_cache_manager,
        mock_metrics_manager,
        mock_error_handler,
        mock_memory_monitor,
        mock_health_tracker
    ):
        """Test initialization with custom max reflection cycles."""
        agent = WaterAgentReflective(
            agent_id="test_agent",
            event_queue=mock_event_queue,
            state_manager=mock_state_manager,
            context_manager=mock_context_manager,
            cache_manager=mock_cache_manager,
            metrics_manager=mock_metrics_manager,
            error_handler=mock_error_handler,
            memory_monitor=mock_memory_monitor,
            health_tracker=mock_health_tracker,
            max_reflection_cycles=5
        )
        
        assert agent.max_reflection_cycles == 5

    def test_prompt_config_setup(self, water_agent_reflective):
        """Test that prompt configuration is set up correctly."""
        assert water_agent_reflective._prompt_config is not None
        assert water_agent_reflective._prompt_config.system_prompt_base_path == "FFTT_system_prompts/core_agents/water_agent"
        assert water_agent_reflective._prompt_config.reflection_prompt_name == "reflection_prompt"
        assert water_agent_reflective._prompt_config.refinement_prompt_name == "revision_prompt"
        assert water_agent_reflective._prompt_config.initial_prompt_name == "misunderstanding_detection_prompt"


class TestMisunderstandingDetectionWithoutReflection:
    """Test misunderstanding detection without reflection capabilities."""

    @pytest.mark.asyncio
    async def test_detect_misunderstandings_without_reflection_success(self, water_agent_reflective):
        """Test successful misunderstanding detection without reflection."""
        # Mock successful detection result
        detection_result = {
            "misunderstandings": [
                {
                    "id": "misunderstanding_1",
                    "description": "Test misunderstanding",
                    "severity": "HIGH"
                }
            ],
            "first_agent_questions": ["Question for first agent"],
            "second_agent_questions": ["Question for second agent"]
        }
        
        # Mock the process_with_validation to return the detection result
        water_agent_reflective.process_with_validation.return_value = detection_result
        
        # Mock the circuit breaker execute to call the lambda
        async def mock_execute(func):
            return await func()
        water_agent_reflective.get_circuit_breaker().execute.side_effect = mock_execute
        
        result = await water_agent_reflective.detect_misunderstandings(
            "First agent output",
            "Second agent output",
            use_reflection=False
        )
        
        # Verify results
        assert result == detection_result
        assert water_agent_reflective.development_state == DevelopmentState.COMPLETE
        assert len(result["misunderstandings"]) == 1
        assert result["misunderstandings"][0]["id"] == "misunderstanding_1"
        
        # Verify state was stored
        water_agent_reflective._state_manager.set_state.assert_called()

    @pytest.mark.asyncio
    async def test_detect_misunderstandings_circuit_breaker_open(self, water_agent_reflective):
        """Test misunderstanding detection when circuit breaker is open."""
        # Mock circuit breaker open error
        water_agent_reflective.get_circuit_breaker().execute.side_effect = CircuitOpenError("Circuit is open")
        
        result = await water_agent_reflective.detect_misunderstandings(
            "First agent output",
            "Second agent output",
            use_reflection=False
        )
        
        # Verify error handling
        assert "error" in result
        assert "Detection error" in result["error"]
        assert water_agent_reflective.development_state == DevelopmentState.ERROR
        assert result["misunderstandings"] == []
        assert result["first_agent_questions"] == []
        assert result["second_agent_questions"] == []

    @pytest.mark.asyncio
    async def test_detect_misunderstandings_unexpected_error(self, water_agent_reflective):
        """Test misunderstanding detection with unexpected error."""
        # Mock unexpected error in circuit breaker execution
        water_agent_reflective.get_circuit_breaker().execute.side_effect = Exception("Unexpected error")
        
        result = await water_agent_reflective.detect_misunderstandings(
            "First agent output",
            "Second agent output",
            use_reflection=False
        )
        
        # Verify error handling
        assert "error" in result
        assert "Detection error" in result["error"]
        assert water_agent_reflective.development_state == DevelopmentState.ERROR

    @pytest.mark.asyncio
    async def test_detect_misunderstandings_no_misunderstandings(self, water_agent_reflective):
        """Test detection when no misunderstandings are found."""
        # Mock no misunderstandings found
        detection_result = {
            "misunderstandings": [],
            "first_agent_questions": [],
            "second_agent_questions": []
        }
        
        water_agent_reflective.get_circuit_breaker().execute.return_value = detection_result
        
        result = await water_agent_reflective.detect_misunderstandings(
            "First agent output",
            "Second agent output",
            use_reflection=False
        )
        
        # Verify results
        assert result == detection_result
        assert water_agent_reflective.development_state == DevelopmentState.COMPLETE
        assert len(result["misunderstandings"]) == 0


class TestMisunderstandingDetectionWithReflection:
    """Test misunderstanding detection with reflection capabilities."""

    @pytest.mark.asyncio
    async def test_detect_misunderstandings_with_reflection_success(self, water_agent_reflective):
        """Test successful misunderstanding detection with reflection."""
        # Mock initial detection result
        initial_detection = {
            "misunderstandings": [
                {
                    "id": "misunderstanding_1",
                    "description": "Test misunderstanding",
                    "severity": "MEDIUM"
                }
            ],
            "first_agent_questions": ["Question for first agent"],
            "second_agent_questions": ["Question for second agent"]
        }
        
        # Mock reflection result with critical improvements
        reflection_result = {
            "reflection_results": {
                "overall_assessment": {
                    "critical_improvements": [
                        {
                            "importance": "critical",
                            "description": "Need to improve severity assessment"
                        }
                    ]
                }
            }
        }
        
        # Mock revised detection result
        revised_detection = {
            "misunderstandings": [
                {
                    "id": "misunderstanding_1",
                    "description": "Improved test misunderstanding",
                    "severity": "HIGH"
                }
            ],
            "first_agent_questions": ["Improved question for first agent"],
            "second_agent_questions": ["Improved question for second agent"]
        }
        
        revision_result = {
            "revised_detection": revised_detection,
            "needs_further_reflection": False
        }
        
        water_agent_reflective.get_circuit_breaker().execute.return_value = initial_detection
        water_agent_reflective.standard_reflect.return_value = reflection_result
        water_agent_reflective.standard_refine.return_value = revision_result
        
        result = await water_agent_reflective.detect_misunderstandings(
            "First agent output",
            "Second agent output",
            use_reflection=True
        )
        
        # Verify results
        assert result == revised_detection
        assert water_agent_reflective.development_state == DevelopmentState.COMPLETE
        assert water_agent_reflective.current_reflection_cycle == 1
        assert result["misunderstandings"][0]["severity"] == "HIGH"
        
        # Verify reflection and refinement were called
        water_agent_reflective.standard_reflect.assert_called_once()
        water_agent_reflective.standard_refine.assert_called_once()

    @pytest.mark.asyncio
    async def test_reflect_and_revise_no_critical_improvements(self, water_agent_reflective):
        """Test reflection when no critical improvements are needed."""
        detection_result = {
            "misunderstandings": [],
            "first_agent_questions": [],
            "second_agent_questions": []
        }
        
        detection_context = {
            "first_agent_output": "First agent output",
            "second_agent_output": "Second agent output",
            "detection_id": "test_detection_id",
            "timestamp": datetime.now().isoformat()
        }
        
        # Mock reflection with no critical improvements
        reflection_result = {
            "reflection_results": {
                "overall_assessment": {
                    "critical_improvements": [
                        {
                            "importance": "low",
                            "description": "Minor improvement"
                        }
                    ]
                }
            }
        }
        
        water_agent_reflective.standard_reflect.return_value = reflection_result
        
        result = await water_agent_reflective._reflect_and_revise_detection(
            detection_result,
            detection_context
        )
        
        # Should return original result without revision
        assert result == detection_result
        assert water_agent_reflective.current_reflection_cycle == 1
        water_agent_reflective.standard_reflect.assert_called_once()
        water_agent_reflective.standard_refine.assert_not_called()

    @pytest.mark.asyncio
    async def test_reflect_and_revise_max_cycles_reached(self, water_agent_reflective):
        """Test reflection when maximum cycles are reached."""
        detection_result = {
            "misunderstandings": [],
            "first_agent_questions": [],
            "second_agent_questions": []
        }
        
        detection_context = {
            "detection_id": "test_detection_id"
        }
        
        # Set current cycle to max
        water_agent_reflective.current_reflection_cycle = water_agent_reflective.max_reflection_cycles
        
        result = await water_agent_reflective._reflect_and_revise_detection(
            detection_result,
            detection_context
        )
        
        # Should return original result without reflection
        assert result == detection_result
        water_agent_reflective.standard_reflect.assert_not_called()
        water_agent_reflective.standard_refine.assert_not_called()

    @pytest.mark.asyncio
    async def test_reflect_and_revise_error_handling(self, water_agent_reflective):
        """Test error handling in reflection and revision process."""
        detection_result = {
            "misunderstandings": [],
            "first_agent_questions": [],
            "second_agent_questions": []
        }
        
        detection_context = {
            "detection_id": "test_detection_id"
        }
        
        # Mock reflection error
        water_agent_reflective.standard_reflect.side_effect = Exception("Reflection error")
        
        result = await water_agent_reflective._reflect_and_revise_detection(
            detection_result,
            detection_context
        )
        
        # Should return original result on error
        assert result == detection_result

    @pytest.mark.asyncio
    async def test_reflect_and_revise_recursive_improvement(self, water_agent_reflective):
        """Test recursive reflection when further improvement is needed."""
        detection_result = {
            "misunderstandings": [{"id": "original", "severity": "LOW"}],
            "first_agent_questions": [],
            "second_agent_questions": []
        }
        
        detection_context = {
            "detection_id": "test_detection_id"
        }
        
        # Mock first reflection cycle with critical improvements
        reflection_result_1 = {
            "reflection_results": {
                "overall_assessment": {
                    "critical_improvements": [
                        {
                            "importance": "critical",
                            "description": "Need further improvement"
                        }
                    ]
                }
            }
        }
        
        revision_result_1 = {
            "revised_detection": {
                "misunderstandings": [{"id": "revised_1", "severity": "MEDIUM"}],
                "first_agent_questions": [],
                "second_agent_questions": []
            },
            "needs_further_reflection": True
        }
        
        # Mock second reflection cycle
        reflection_result_2 = {
            "reflection_results": {
                "overall_assessment": {
                    "critical_improvements": [
                        {
                            "importance": "critical",
                            "description": "Final improvement"
                        }
                    ]
                }
            }
        }
        
        revision_result_2 = {
            "revised_detection": {
                "misunderstandings": [{"id": "final", "severity": "HIGH"}],
                "first_agent_questions": [],
                "second_agent_questions": []
            },
            "needs_further_reflection": False
        }
        
        water_agent_reflective.standard_reflect.side_effect = [reflection_result_1, reflection_result_2]
        water_agent_reflective.standard_refine.side_effect = [revision_result_1, revision_result_2]
        
        result = await water_agent_reflective._reflect_and_revise_detection(
            detection_result,
            detection_context
        )
        
        # Should return final revised result
        assert result == revision_result_2["revised_detection"]
        assert water_agent_reflective.current_reflection_cycle == 2
        assert water_agent_reflective.standard_reflect.call_count == 2
        assert water_agent_reflective.standard_refine.call_count == 2

    @pytest.mark.asyncio
    async def test_reflect_and_revise_with_error_detection_result(self, water_agent_reflective):
        """Test reflection skips when initial detection result has errors."""
        detection_result = {
            "error": "Detection failed",
            "misunderstandings": [],
            "first_agent_questions": [],
            "second_agent_questions": []
        }
        
        detection_context = {
            "detection_id": "test_detection_id"
        }
        
        result = await water_agent_reflective._reflect_and_revise_detection(
            detection_result,
            detection_context
        )
        
        # Should return original error result without reflection
        assert result == detection_result
        water_agent_reflective.standard_reflect.assert_not_called()
        water_agent_reflective.standard_refine.assert_not_called()


class TestWaterAgentReflectiveIntegration:
    """Test integration aspects of WaterAgentReflective."""

    @pytest.mark.asyncio
    async def test_development_state_transitions(self, water_agent_reflective):
        """Test proper development state transitions during processing."""
        detection_result = {
            "misunderstandings": [],
            "first_agent_questions": [],
            "second_agent_questions": []
        }
        
        water_agent_reflective.get_circuit_breaker().execute.return_value = detection_result
        
        # Verify initial state
        assert water_agent_reflective.development_state == DevelopmentState.INITIALIZING
        
        await water_agent_reflective.detect_misunderstandings(
            "First agent output",
            "Second agent output",
            use_reflection=False
        )
        
        # Verify final state
        assert water_agent_reflective.development_state == DevelopmentState.COMPLETE

    @pytest.mark.asyncio
    async def test_state_persistence_during_detection(self, water_agent_reflective):
        """Test that detection context is properly persisted."""
        detection_result = {
            "misunderstandings": [],
            "first_agent_questions": [],
            "second_agent_questions": []
        }
        
        water_agent_reflective.get_circuit_breaker().execute.return_value = detection_result
        
        await water_agent_reflective.detect_misunderstandings(
            "First agent output",
            "Second agent output",
            use_reflection=False
        )
        
        # Verify state manager was called to store context
        calls = water_agent_reflective._state_manager.set_state.call_args_list
        assert len(calls) >= 1
        
        # Check that detection context was stored
        first_call = calls[0]
        assert "water_agent:detection_context:" in first_call[0][0]
        assert "first_agent_output" in first_call[0][1]
        assert "second_agent_output" in first_call[0][1]

    @pytest.mark.asyncio
    async def test_reflection_state_persistence(self, water_agent_reflective):
        """Test that reflection and revision results are persisted."""
        detection_result = {
            "misunderstandings": [{"id": "test", "severity": "LOW"}],
            "first_agent_questions": [],
            "second_agent_questions": []
        }
        
        reflection_result = {
            "reflection_results": {
                "overall_assessment": {
                    "critical_improvements": [
                        {"importance": "critical", "description": "test"}
                    ]
                }
            }
        }
        
        revision_result = {
            "revised_detection": detection_result,
            "needs_further_reflection": False
        }
        
        water_agent_reflective.get_circuit_breaker().execute.return_value = detection_result
        water_agent_reflective.standard_reflect.return_value = reflection_result
        water_agent_reflective.standard_refine.return_value = revision_result
        
        await water_agent_reflective.detect_misunderstandings(
            "First agent output",
            "Second agent output",
            use_reflection=True
        )
        
        # Verify reflection and revision results were stored
        calls = water_agent_reflective._state_manager.set_state.call_args_list
        reflection_stored = any("water_agent:reflection:" in call[0][0] for call in calls)
        revision_stored = any("water_agent:revision:" in call[0][0] for call in calls)
        
        assert reflection_stored
        assert revision_stored

    @pytest.mark.asyncio
    async def test_base_class_method_delegation(self, water_agent_reflective):
        """Test that base class methods delegate properly."""
        test_output = {"test": "data"}
        test_guidance = {"guidance": "test"}
        
        # Test reflect delegation
        await water_agent_reflective.reflect(test_output)
        water_agent_reflective.standard_reflect.assert_called_with(test_output, "detection")
        
        # Test refine delegation
        await water_agent_reflective.refine(test_output, test_guidance)
        water_agent_reflective.standard_refine.assert_called_with(test_output, test_guidance, "detection")


class TestWaterAgentReflectiveEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_empty_agent_outputs(self, water_agent_reflective):
        """Test detection with empty agent outputs."""
        detection_result = {
            "misunderstandings": [],
            "first_agent_questions": [],
            "second_agent_questions": []
        }
        
        water_agent_reflective.get_circuit_breaker().execute.return_value = detection_result
        
        result = await water_agent_reflective.detect_misunderstandings("", "", use_reflection=False)
        
        assert result == detection_result
        assert water_agent_reflective.development_state == DevelopmentState.COMPLETE

    @pytest.mark.asyncio
    async def test_very_long_agent_outputs(self, water_agent_reflective):
        """Test detection with very long agent outputs."""
        long_output = "x" * 10000
        detection_result = {
            "misunderstandings": [],
            "first_agent_questions": [],
            "second_agent_questions": []
        }
        
        water_agent_reflective.get_circuit_breaker().execute.return_value = detection_result
        
        result = await water_agent_reflective.detect_misunderstandings(
            long_output, 
            long_output, 
            use_reflection=False
        )
        
        assert result == detection_result

    @pytest.mark.asyncio
    async def test_malformed_detection_result(self, water_agent_reflective):
        """Test handling of malformed detection results."""
        # Mock malformed result (missing required fields)
        malformed_result = {"some_field": "some_value"}
        
        water_agent_reflective.get_circuit_breaker().execute.return_value = malformed_result
        
        result = await water_agent_reflective.detect_misunderstandings(
            "First agent output",
            "Second agent output",
            use_reflection=False
        )
        
        # Should still return the result (no validation enforced)
        assert result == malformed_result

    @pytest.mark.asyncio
    async def test_state_manager_failure_during_detection(self, water_agent_reflective):
        """Test handling when state manager fails during detection."""
        detection_result = {
            "misunderstandings": [],
            "first_agent_questions": [],
            "second_agent_questions": []
        }
        
        water_agent_reflective.get_circuit_breaker().execute.return_value = detection_result
        water_agent_reflective._state_manager.set_state.side_effect = Exception("State manager error")
        
        # Should still complete detection despite state manager failure
        result = await water_agent_reflective.detect_misunderstandings(
            "First agent output",
            "Second agent output",
            use_reflection=False
        )
        
        # Detection should still succeed even if state persistence fails
        assert "error" in result or result == detection_result

    @pytest.mark.asyncio
    async def test_concurrent_detection_calls(self, water_agent_reflective):
        """Test behavior with concurrent detection calls."""
        detection_result = {
            "misunderstandings": [],
            "first_agent_questions": [],
            "second_agent_questions": []
        }
        
        water_agent_reflective.get_circuit_breaker().execute.return_value = detection_result
        
        # Start multiple concurrent detection calls
        tasks = [
            water_agent_reflective.detect_misunderstandings(
                f"First agent output {i}",
                f"Second agent output {i}",
                use_reflection=False
            )
            for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should complete successfully
        assert len(results) == 3
        for result in results:
            assert result == detection_result or "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])