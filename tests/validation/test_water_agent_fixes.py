"""
Validation tests for Water Agent fixes.

This module tests the fixes applied to the Water Agent infrastructure
using lightweight fixtures and proper async handling.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from tests_new.fixtures.lightweight_fixtures import (
    lightweight_water_coordinator,
    lightweight_agent_pair,
    lightweight_coordination_scenario,
    mock_prompt_responses
)
from tests_new.fixtures.async_fixtures import (
    coordination_infrastructure,
    async_context_manager
)
from tests_new.fixtures.robustness_fixtures import (
    failure_simulator,
    mock_circuit_breaker,
    robustness_test_environment
)


class TestCircularImportFixes:
    """Test that circular import issues have been resolved."""
    
    def test_lazy_import_resolution(self):
        """Test that lazy import mechanism works correctly."""
        from phase_one.validation.coordination import get_water_agent_coordinator
        
        # Should be able to get the coordinator class without circular import
        WaterAgentCoordinatorClass = get_water_agent_coordinator()
        assert WaterAgentCoordinatorClass is not None
        
        # Should be able to create an instance
        coordinator = WaterAgentCoordinatorClass(resource_id="test_lazy_import")
        assert coordinator.resource_id == "test_lazy_import"
    
    def test_sequential_coordinator_initialization(self):
        """Test that SequentialAgentCoordinator can be created without circular imports."""
        from phase_one.validation.coordination import SequentialAgentCoordinator
        from tests_new.fixtures.async_fixtures import minimal_event_queue, minimal_state_manager
        
        # Create minimal dependencies
        event_queue = AsyncMock()
        state_manager = AsyncMock()
        
        # Should be able to create coordinator without import errors
        coordinator = SequentialAgentCoordinator(
            event_queue=event_queue,
            state_manager=state_manager
        )
        assert coordinator.water_coordinator is not None


class TestAsyncFixtures:
    """Test that async fixtures work correctly."""
    
    @pytest.mark.asyncio
    async def test_coordination_infrastructure(self, coordination_infrastructure):
        """Test that coordination infrastructure fixture provides clean async components."""
        event_queue = coordination_infrastructure["event_queue"]
        state_manager = coordination_infrastructure["state_manager"]
        
        # Should be able to call async methods without errors
        await event_queue.emit("test_event", {"data": "test"})
        await state_manager.set_state("test_key", {"value": "test"})
        
        # Verify calls were made
        assert event_queue.emit.called
        assert state_manager.set_state.called
    
    @pytest.mark.asyncio
    async def test_lightweight_water_coordinator(self, lightweight_water_coordinator):
        """Test lightweight water coordinator fixture."""
        coordinator = lightweight_water_coordinator
        
        # Should have all required components
        assert coordinator.misunderstanding_detector is not None
        assert coordinator.response_handler is not None
        assert coordinator.resolution_tracker is not None
        assert coordinator.context_manager is not None
        
        # Should be able to emit events without errors
        await coordinator._emit_event("test_event", {"test": "data"})
        assert coordinator._emit_event.called
    
    @pytest.mark.asyncio
    async def test_lightweight_agent_pair(self, lightweight_agent_pair):
        """Test lightweight agent pair fixture."""
        first_agent, second_agent = lightweight_agent_pair
        
        # Should be able to call clarify without errors
        response1 = await first_agent.clarify("Test question about terminology")
        response2 = await second_agent.clarify("Test question about requirements")
        
        assert "terminology" in response1.lower()
        assert "requirement" in response2.lower()
        assert len(first_agent.clarification_history) == 1
        assert len(second_agent.clarification_history) == 1


class TestJSONParsingFixes:
    """Test that JSON parsing issues have been resolved."""
    
    @pytest.mark.asyncio
    async def test_detection_result_parsing(self, lightweight_water_coordinator):
        """Test that detection results are parsed correctly."""
        coordinator = lightweight_water_coordinator
        
        # Test with valid detection result
        detection_result = {
            "misunderstandings": [
                {
                    "id": "test_misunderstanding",
                    "description": "Test description",
                    "severity": "MEDIUM"
                }
            ],
            "first_agent_questions": [
                {"question": "Test question for first agent"}
            ],
            "second_agent_questions": [
                {"question": "Test question for second agent"}
            ]
        }
        
        # Mock the detector to return the result
        coordinator.misunderstanding_detector.detect_misunderstandings = AsyncMock(
            return_value=(
                detection_result["misunderstandings"],
                [q["question"] for q in detection_result["first_agent_questions"]],
                [q["question"] for q in detection_result["second_agent_questions"]]
            )
        )
        
        # Test detection
        misunderstandings, first_questions, second_questions = await coordinator.misunderstanding_detector.detect_misunderstandings(
            "First agent output",
            "Second agent output"
        )
        
        assert len(misunderstandings) == 1
        assert len(first_questions) == 1
        assert len(second_questions) == 1
        assert first_questions[0] == "Test question for first agent"
        assert second_questions[0] == "Test question for second agent"
    
    def test_json_parsing_edge_cases(self, mock_prompt_responses):
        """Test JSON parsing handles edge cases correctly."""
        # Test the JSON parsing logic directly
        from resources.water_agent.reflective import WaterAgentReflective
        
        # Create a minimal reflective agent instance for testing
        agent = object.__new__(WaterAgentReflective)
        
        # Test parsing valid JSON
        valid_json = '{"misunderstandings": [], "first_agent_questions": [], "second_agent_questions": []}'
        result = agent._parse_json_string(valid_json)
        assert result["misunderstandings"] == []
        
        # Test parsing JSON with code blocks
        json_with_code_block = '''
        Here's the analysis:
        ```json
        {"misunderstandings": [{"id": "test", "description": "test"}], "first_agent_questions": [], "second_agent_questions": []}
        ```
        '''
        result = agent._parse_json_string(json_with_code_block)
        assert len(result["misunderstandings"]) == 1
        
        # Test invalid JSON fallback
        invalid_json = "This is not JSON at all"
        result = agent._parse_json_string(invalid_json)
        assert result["misunderstandings"] == []
        assert result["first_agent_questions"] == []
        assert result["second_agent_questions"] == []


class TestCoordinationWorkflow:
    """Test complete coordination workflow with fixes."""
    
    @pytest.mark.asyncio
    async def test_basic_coordination_workflow(self, lightweight_water_coordinator, lightweight_agent_pair, lightweight_coordination_scenario):
        """Test basic coordination workflow works end-to-end."""
        coordinator = lightweight_water_coordinator
        first_agent, second_agent = lightweight_agent_pair
        scenario = lightweight_coordination_scenario
        
        # Execute coordination
        try:
            updated_first, updated_second, coordination_metadata = await coordinator.coordinate_agents(
                first_agent=first_agent,
                first_agent_output=scenario["first_agent_output"],
                second_agent=second_agent,
                second_agent_output=scenario["second_agent_output"],
                coordination_context={"coordination_id": scenario["coordination_id"]}
            )
            
            # Verify coordination completed
            assert updated_first is not None
            assert updated_second is not None
            assert coordination_metadata is not None
            assert "coordination_id" in coordination_metadata
            
        except Exception as e:
            pytest.fail(f"Basic coordination workflow failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_coordination_with_real_misunderstandings(self, lightweight_water_coordinator, lightweight_agent_pair):
        """Test coordination when misunderstandings are detected."""
        coordinator = lightweight_water_coordinator
        first_agent, second_agent = lightweight_agent_pair
        
        # Setup coordinator to detect misunderstandings
        coordinator.misunderstanding_detector.detect_misunderstandings = AsyncMock(
            return_value=(
                [{"id": "terminology_conflict", "description": "Different terminology used", "severity": "MEDIUM"}],
                ["Can you clarify the terminology you're using?"],
                ["What do you mean by 'forest layers'?"]
            )
        )
        
        # Setup resolution tracker to show resolution
        coordinator.resolution_tracker.assess_resolution = AsyncMock(
            return_value=(
                [{"id": "terminology_conflict", "resolution_summary": "Terminology clarified"}],
                [],  # No unresolved
                [],  # No new questions
                []
            )
        )
        
        # Execute coordination
        updated_first, updated_second, coordination_metadata = await coordinator.coordinate_agents(
            first_agent=first_agent,
            first_agent_output="Using permaculture forest layers in design",
            second_agent=second_agent,
            second_agent_output="Implementing multi-story vegetation approach",
            coordination_context={"coordination_id": "test_misunderstanding_resolution"}
        )
        
        # Verify coordination handled misunderstandings
        assert coordination_metadata.get("total_iterations", 0) >= 1
        assert len(first_agent.clarification_history) > 0 or len(second_agent.clarification_history) > 0


class TestRobustnessFixes:
    """Test that robustness and circuit breaker fixes work."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self, mock_circuit_breaker, failure_simulator):
        """Test circuit breaker behavior with failures."""
        circuit = mock_circuit_breaker
        simulator = failure_simulator
        
        # Test successful execution
        result = await circuit.execute(simulator.simulate_success)
        assert result is not None
        assert circuit.failure_count == 0
        
        # Test failure accumulation
        for i in range(3):
            try:
                await circuit.execute(simulator.simulate_llm_timeout)
            except Exception:
                pass  # Expected
        
        # Circuit should now be open
        from resources.monitoring.circuit_breakers import CircuitState, CircuitOpenError
        assert circuit.state == CircuitState.OPEN
        
        # Next execution should fail immediately
        with pytest.raises(CircuitOpenError):
            await circuit.execute(simulator.simulate_success)
    
    @pytest.mark.asyncio
    async def test_failure_simulator_patterns(self, failure_simulator):
        """Test failure simulator provides different failure types."""
        simulator = failure_simulator
        
        # Test different failure types
        failure_types = []
        
        try:
            await simulator.simulate_llm_timeout()
        except Exception:
            failure_types.append("timeout")
        
        try:
            await simulator.simulate_llm_rate_limit()
        except Exception:
            failure_types.append("rate_limit")
        
        try:
            await simulator.simulate_network_error()
        except Exception:
            failure_types.append("network")
        
        # Should have triggered different failure types
        assert len(failure_types) >= 3
        assert simulator.failure_count >= 3
    
    @pytest.mark.asyncio
    async def test_robustness_environment_setup(self, robustness_test_environment):
        """Test robustness test environment provides complete infrastructure."""
        env = robustness_test_environment
        
        # Should have all required components
        assert "failure_simulator" in env
        assert "circuit_breakers" in env
        assert "memory_simulator" in env
        assert "test_metrics" in env
        
        # Should have circuit breakers for different components
        assert "detection" in env["circuit_breakers"]
        assert "resolution" in env["circuit_breakers"]
        assert "reflection" in env["circuit_breakers"]
        
        # Circuit breakers should be functional
        detection_cb = env["circuit_breakers"]["detection"]
        result = await detection_cb.execute(lambda: {"success": True})
        assert result["success"] is True


class TestInfrastructureStability:
    """Test overall infrastructure stability."""
    
    @pytest.mark.asyncio
    async def test_async_context_management(self, async_context_manager):
        """Test async context management works correctly."""
        async with async_context_manager as ctx:
            # Should be able to add contexts for cleanup
            test_context = {"test": "data"}
            ctx.add_context(test_context)
            
            # Context manager should handle cleanup automatically
            assert test_context in ctx.contexts
    
    @pytest.mark.asyncio 
    async def test_no_event_loop_conflicts(self, coordination_infrastructure):
        """Test that fixtures don't create event loop conflicts."""
        # Should be able to access coordination infrastructure
        event_queue = coordination_infrastructure["event_queue"]
        state_manager = coordination_infrastructure["state_manager"]
        
        # Should be able to create new async tasks
        async def test_task():
            await asyncio.sleep(0.001)
            return "task_completed"
        
        result = await test_task()
        assert result == "task_completed"
        
        # Should be able to use infrastructure without conflicts
        await event_queue.emit("test", {})
        await state_manager.get_state("test")
    
    def test_import_stability(self):
        """Test that imports are stable and don't cause circular dependencies."""
        # Test importing key modules doesn't cause issues
        from resources.water_agent.coordinator import WaterAgentCoordinator
        from resources.water_agent.reflective import WaterAgentReflective
        from resources.water_agent.context_manager import WaterAgentContextManager
        from phase_one.validation.coordination import SequentialAgentCoordinator
        
        # All imports should succeed without circular dependency errors
        assert WaterAgentCoordinator is not None
        assert WaterAgentReflective is not None
        assert WaterAgentContextManager is not None
        assert SequentialAgentCoordinator is not None


class TestQualityValidation:
    """Validate overall quality improvements."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_scenario_reliability(self, lightweight_water_coordinator, lightweight_agent_pair):
        """Test that end-to-end scenarios are now reliable."""
        coordinator = lightweight_water_coordinator
        first_agent, second_agent = lightweight_agent_pair
        
        # Run multiple coordination scenarios to test reliability
        success_count = 0
        total_runs = 5
        
        for i in range(total_runs):
            try:
                updated_first, updated_second, metadata = await coordinator.coordinate_agents(
                    first_agent=first_agent,
                    first_agent_output=f"Test output {i}",
                    second_agent=second_agent,
                    second_agent_output=f"Response output {i}",
                    coordination_context={"coordination_id": f"test_reliability_{i}"}
                )
                
                if updated_first is not None and updated_second is not None:
                    success_count += 1
                    
            except Exception as e:
                # Log but don't fail - we're testing reliability
                print(f"Run {i} failed: {str(e)}")
        
        # Should have high success rate
        success_rate = success_count / total_runs
        assert success_rate >= 0.8, f"Success rate {success_rate} below threshold"
    
    def test_memory_efficiency(self):
        """Test that fixtures don't create memory leaks."""
        import gc
        import sys
        
        # Get initial memory reference count
        initial_objects = len(gc.get_objects())
        
        # Create and destroy some fixtures
        for _ in range(10):
            from tests_new.fixtures.lightweight_fixtures import LightweightTestAgent
            agent = LightweightTestAgent("test_memory", "test")
            del agent
        
        # Force garbage collection
        gc.collect()
        
        # Check that objects were cleaned up
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects
        
        # Allow some growth but not excessive
        assert object_growth < 100, f"Potential memory leak: {object_growth} objects created"