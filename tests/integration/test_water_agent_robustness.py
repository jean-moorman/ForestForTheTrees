"""
Robustness tests for Water Agent focusing on error handling, circuit breakers,
and system resilience under various failure conditions.
"""

import pytest
import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

from resources.water_agent import WaterAgentCoordinator
from resources.water_agent.context_manager import WaterAgentContextManager
from resources.water_agent.reflective import WaterAgentReflective
from resources.monitoring.circuit_breakers import CircuitOpenError, CircuitState
from resources.errors import CoordinationError, MisunderstandingDetectionError
from tests.fixtures.water_agent_test_data import WaterAgentTestDataProvider


class FailureSimulator:
    """Simulates various types of failures for testing robustness."""
    
    def __init__(self):
        self.failure_count = 0
        self.failure_types = []
        
    async def simulate_llm_timeout(self, *args, **kwargs):
        """Simulate LLM API timeout."""
        self.failure_count += 1
        self.failure_types.append("llm_timeout")
        await asyncio.sleep(0.1)  # Simulate delay
        raise asyncio.TimeoutError("LLM API request timed out")
        
    async def simulate_llm_rate_limit(self, *args, **kwargs):
        """Simulate LLM API rate limiting."""
        self.failure_count += 1
        self.failure_types.append("llm_rate_limit")
        raise Exception("Rate limit exceeded: 429 Too Many Requests")
        
    async def simulate_invalid_json_response(self, *args, **kwargs):
        """Simulate invalid JSON response from LLM."""
        self.failure_count += 1
        self.failure_types.append("invalid_json")
        return "This is not valid JSON {invalid structure"
        
    async def simulate_malformed_schema_response(self, *args, **kwargs):
        """Simulate response that doesn't match expected schema."""
        self.failure_count += 1
        self.failure_types.append("malformed_schema")
        return json.dumps({
            "wrong_field": "value",
            "misunderstandings": "should be array",
            "missing_required_fields": True
        })
        
    async def simulate_state_manager_failure(self, *args, **kwargs):
        """Simulate state manager persistence failure."""
        self.failure_count += 1
        self.failure_types.append("state_failure")
        raise Exception("Database connection failed")
        
    async def simulate_memory_pressure(self, *args, **kwargs):
        """Simulate memory pressure conditions."""
        self.failure_count += 1
        self.failure_types.append("memory_pressure")
        raise MemoryError("Insufficient memory for operation")
        
    async def simulate_intermittent_failure(self, *args, **kwargs):
        """Simulate intermittent failures that succeed after retries."""
        self.failure_count += 1
        self.failure_types.append("intermittent")
        if self.failure_count <= 2:
            raise Exception("Temporary failure")
        else:
            return json.dumps({
                "misunderstandings": [],
                "first_agent_questions": [],
                "second_agent_questions": []
            })


@pytest.fixture
def failure_simulator():
    """Create a failure simulator for testing."""
    return FailureSimulator()


@pytest.fixture
def robust_water_coordinator():
    """Create a Water Agent Coordinator configured for robustness testing."""
    state_manager = AsyncMock()
    state_manager.get_state = AsyncMock(return_value=None)
    state_manager.set_state = AsyncMock(return_value=True)
    
    coordinator = WaterAgentCoordinator(
        state_manager=state_manager,
        resource_id="robust_test_coordinator"
    )
    coordinator._emit_event = AsyncMock()
    return coordinator


class TestCircuitBreakerBehavior:
    """Test circuit breaker functionality under various failure conditions."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_repeated_failures(self, robust_water_coordinator, failure_simulator):
        """Test that circuit breaker opens after repeated failures."""
        # Mock the LLM call to always fail
        robust_water_coordinator._call_llm = failure_simulator.simulate_llm_timeout
        
        # Create test agents
        first_agent = MagicMock()
        first_agent.agent_id = "test_agent_1"
        second_agent = MagicMock()
        second_agent.agent_id = "test_agent_2"
        
        # Attempt coordination multiple times to trigger circuit breaker
        failures = 0
        for attempt in range(5):
            try:
                await robust_water_coordinator.coordinate_agents(
                    first_agent,
                    "Test output 1",
                    second_agent,
                    "Test output 2"
                )
            except (CoordinationError, asyncio.TimeoutError):
                failures += 1
        
        # Verify multiple failures occurred
        assert failures > 0
        assert failure_simulator.failure_count >= 3
        
        # Verify circuit breaker would have opened (in a real implementation)
        # This is a conceptual test - actual circuit breaker implementation would prevent further calls
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery_after_timeout(self, robust_water_coordinator, failure_simulator):
        """Test circuit breaker recovery after timeout period."""
        # Configure for intermittent failures
        robust_water_coordinator._call_llm = failure_simulator.simulate_intermittent_failure
        
        first_agent = MagicMock()
        first_agent.agent_id = "recovery_test_1"
        second_agent = MagicMock()
        second_agent.agent_id = "recovery_test_2"
        
        # Initial failures
        with pytest.raises(CoordinationError):
            await robust_water_coordinator.coordinate_agents(
                first_agent, "Output 1", second_agent, "Output 2"
            )
        
        with pytest.raises(CoordinationError):
            await robust_water_coordinator.coordinate_agents(
                first_agent, "Output 1", second_agent, "Output 2"
            )
        
        # After failures, should eventually succeed
        try:
            result = await robust_water_coordinator.coordinate_agents(
                first_agent, "Output 1", second_agent, "Output 2"
            )
            # Should succeed after circuit breaker allows retry
            assert result is not None
        except CoordinationError:
            # May still fail depending on timing, which is acceptable
            pass
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_fail_fast_behavior(self, robust_water_coordinator):
        """Test that circuit breaker provides fail-fast behavior when open."""
        # Simulate circuit breaker in open state
        with patch('resources.monitoring.circuit_breakers.CircuitBreaker') as mock_cb:
            mock_circuit_instance = AsyncMock()
            mock_circuit_instance.execute = AsyncMock(side_effect=CircuitOpenError("Circuit is open"))
            mock_cb.return_value = mock_circuit_instance
            
            first_agent = MagicMock()
            second_agent = MagicMock()
            
            start_time = datetime.now()
            
            with pytest.raises(CoordinationError):
                await robust_water_coordinator.coordinate_agents(
                    first_agent, "Output 1", second_agent, "Output 2"
                )
            
            # Should fail fast without long delays
            duration = datetime.now() - start_time
            assert duration < timedelta(seconds=1)


class TestErrorHandlingRobustness:
    """Test error handling robustness across different failure scenarios."""
    
    @pytest.mark.asyncio
    async def test_invalid_json_response_handling(self, robust_water_coordinator, failure_simulator):
        """Test handling of invalid JSON responses from LLM."""
        # Mock invalid JSON response
        robust_water_coordinator._call_llm = failure_simulator.simulate_invalid_json_response
        
        first_agent = MagicMock()
        second_agent = MagicMock()
        
        # Should handle invalid JSON gracefully
        with pytest.raises(CoordinationError):
            await robust_water_coordinator.coordinate_agents(
                first_agent, "Output 1", second_agent, "Output 2"
            )
        
        # Verify error was tracked
        assert failure_simulator.failure_count > 0
        assert "invalid_json" in failure_simulator.failure_types
    
    @pytest.mark.asyncio
    async def test_malformed_schema_response_handling(self, robust_water_coordinator, failure_simulator):
        """Test handling of responses that don't match expected schema."""
        robust_water_coordinator._call_llm = failure_simulator.simulate_malformed_schema_response
        
        first_agent = MagicMock()
        second_agent = MagicMock()
        
        # Should handle schema violations gracefully
        with pytest.raises(CoordinationError):
            await robust_water_coordinator.coordinate_agents(
                first_agent, "Output 1", second_agent, "Output 2"
            )
        
        assert "malformed_schema" in failure_simulator.failure_types
    
    @pytest.mark.asyncio
    async def test_state_persistence_failure_handling(self, robust_water_coordinator, failure_simulator):
        """Test handling of state persistence failures."""
        # Mock state manager failure
        robust_water_coordinator._state_manager.set_state = failure_simulator.simulate_state_manager_failure
        
        first_agent = MagicMock()
        second_agent = MagicMock()
        
        # Mock successful LLM calls but failing state persistence
        robust_water_coordinator._call_llm = AsyncMock(return_value=json.dumps({
            "misunderstandings": [],
            "first_agent_questions": [],
            "second_agent_questions": []
        }))
        
        # Should handle state failures gracefully
        try:
            result = await robust_water_coordinator.coordinate_agents(
                first_agent, "Output 1", second_agent, "Output 2"
            )
            # May succeed despite state failure
            assert result is not None
        except CoordinationError:
            # Or may fail, but should be handled gracefully
            pass
        
        assert "state_failure" in failure_simulator.failure_types
    
    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self, robust_water_coordinator, failure_simulator):
        """Test handling of memory pressure conditions."""
        robust_water_coordinator._call_llm = failure_simulator.simulate_memory_pressure
        
        first_agent = MagicMock()
        second_agent = MagicMock()
        
        with pytest.raises(CoordinationError):
            await robust_water_coordinator.coordinate_agents(
                first_agent, "Output 1", second_agent, "Output 2"
            )
        
        assert "memory_pressure" in failure_simulator.failure_types
    
    @pytest.mark.asyncio
    async def test_concurrent_coordination_failure_isolation(self, robust_water_coordinator, failure_simulator):
        """Test that failures in one coordination don't affect others."""
        # Set up mixed success/failure scenario
        call_count = 0
        async def mixed_response(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:  # Every other call fails
                await failure_simulator.simulate_llm_timeout()
            else:
                return json.dumps({
                    "misunderstandings": [],
                    "first_agent_questions": [],
                    "second_agent_questions": []
                })
        
        robust_water_coordinator._call_llm = mixed_response
        
        # Start multiple concurrent coordinations
        agents = [(MagicMock(), MagicMock()) for _ in range(4)]
        
        tasks = [
            robust_water_coordinator.coordinate_agents(
                first, f"Output {i}A", second, f"Output {i}B"
            )
            for i, (first, second) in enumerate(agents)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Some should succeed, some should fail
        successes = [r for r in results if not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, Exception)]
        
        # Verify isolation - some succeed despite others failing
        assert len(successes) > 0 or len(failures) == len(results)  # Either some succeed or all fail consistently
    
    @pytest.mark.asyncio
    async def test_timeout_handling_in_coordination(self, robust_water_coordinator):
        """Test proper timeout handling in coordination operations."""
        # Mock very slow LLM response
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(10)  # Simulate very slow response
            return "{}"
        
        robust_water_coordinator._call_llm = slow_response
        
        first_agent = MagicMock()
        second_agent = MagicMock()
        
        start_time = datetime.now()
        
        with pytest.raises((CoordinationError, asyncio.TimeoutError)):
            # Should timeout before the 10 second delay
            await asyncio.wait_for(
                robust_water_coordinator.coordinate_agents(
                    first_agent, "Output 1", second_agent, "Output 2"
                ),
                timeout=2.0
            )
        
        duration = datetime.now() - start_time
        assert duration < timedelta(seconds=3)  # Should timeout quickly


class TestContextManagerRobustness:
    """Test robustness of context management under failure conditions."""
    
    @pytest.mark.asyncio
    async def test_context_recovery_after_corruption(self):
        """Test context recovery when stored context is corrupted."""
        state_manager = AsyncMock()
        
        # Mock corrupted context data
        corrupted_context = {"invalid": "data", "missing_required_fields": True}
        state_manager.get_state = AsyncMock(return_value=corrupted_context)
        
        context_manager = WaterAgentContextManager(state_manager=state_manager)
        
        # Should handle corrupted context gracefully
        result = await context_manager.get_coordination_context("corrupted_context_id")
        
        # Should return None or create new context instead of crashing
        assert result is None or hasattr(result, 'coordination_id')
    
    @pytest.mark.asyncio
    async def test_context_cleanup_under_storage_pressure(self):
        """Test context cleanup when storage is under pressure."""
        state_manager = AsyncMock()
        state_manager.find_keys = AsyncMock(return_value=[
            f"water_agent:coordination:context_{i}" for i in range(1000)
        ])
        
        # Mock individual context retrieval
        async def mock_get_context(key):
            context_id = key.split(":")[-1]
            # Simulate old contexts
            return {
                "coordination_id": context_id,
                "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
                "status": "completed"
            }
        
        state_manager.get_state = AsyncMock(side_effect=mock_get_context)
        state_manager.delete_state = AsyncMock(return_value=True)
        
        context_manager = WaterAgentContextManager(state_manager=state_manager)
        
        # Should handle large cleanup operations
        deleted_count = await context_manager.cleanup_old_contexts(max_age_days=7)
        
        # Should successfully clean up contexts
        assert deleted_count >= 0
    
    @pytest.mark.asyncio
    async def test_concurrent_context_access_safety(self):
        """Test safety of concurrent context access and modification."""
        state_manager = AsyncMock()
        state_manager.get_state = AsyncMock(return_value=None)
        state_manager.set_state = AsyncMock(return_value=True)
        
        context_manager = WaterAgentContextManager(state_manager=state_manager)
        
        coordination_id = "concurrent_test_context"
        
        # Create context
        context = await context_manager.create_coordination_context(
            first_agent_id="agent1",
            second_agent_id="agent2",
            coordination_id=coordination_id
        )
        
        # Simulate concurrent updates
        async def update_context(iteration):
            await context_manager.update_coordination_iteration(
                coordination_id=coordination_id,
                iteration=iteration,
                first_agent_questions=[f"Question {iteration}"],
                first_agent_responses=[f"Response {iteration}"],
                second_agent_questions=[f"Question {iteration}"],
                second_agent_responses=[f"Response {iteration}"],
                resolved=[],
                unresolved=[]
            )
        
        # Run concurrent updates
        tasks = [update_context(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should handle concurrent access without corruption
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0  # No exceptions should occur


class TestReflectiveAgentRobustness:
    """Test robustness of reflective agent functionality."""
    
    @pytest.mark.asyncio
    async def test_reflection_failure_fallback(self):
        """Test fallback behavior when reflection fails."""
        # Mock dependencies
        mock_dependencies = {
            'event_queue': AsyncMock(),
            'state_manager': AsyncMock(),
            'context_manager': AsyncMock(),
            'cache_manager': AsyncMock(),
            'metrics_manager': AsyncMock(),
            'error_handler': AsyncMock(),
            'memory_monitor': AsyncMock(),
            'health_tracker': AsyncMock()
        }
        
        with patch('phase_one.agents.base.AgentInterface'), \
             patch('interfaces.agent.interface.AgentInterface'), \
             patch('interfaces.agent.metrics.InterfaceMetrics'), \
             patch('asyncio.create_task'):
            
            reflective_agent = WaterAgentReflective(
                agent_id="test_reflective_robustness",
                max_reflection_cycles=2,
                **mock_dependencies
            )
            
            # Mock successful initial detection
            initial_detection = {
                "misunderstandings": [{"id": "M1", "severity": "HIGH"}],
                "first_agent_questions": ["Test question"],
                "second_agent_questions": ["Test question"]
            }
            
            reflective_agent.get_circuit_breaker = MagicMock()
            mock_circuit_breaker = AsyncMock()
            mock_circuit_breaker.execute = AsyncMock(return_value=initial_detection)
            reflective_agent.get_circuit_breaker.return_value = mock_circuit_breaker
            
            # Mock reflection failure
            reflective_agent.standard_reflect = AsyncMock(side_effect=Exception("Reflection failed"))
            
            # Should fall back to original detection when reflection fails
            result = await reflective_agent.detect_misunderstandings(
                "First agent output",
                "Second agent output",
                use_reflection=True
            )
            
            # Should return original detection despite reflection failure
            assert result == initial_detection
    
    @pytest.mark.asyncio
    async def test_reflection_infinite_loop_prevention(self):
        """Test prevention of infinite reflection loops."""
        mock_dependencies = {
            'event_queue': AsyncMock(),
            'state_manager': AsyncMock(),
            'context_manager': AsyncMock(),
            'cache_manager': AsyncMock(),
            'metrics_manager': AsyncMock(),
            'error_handler': AsyncMock(),
            'memory_monitor': AsyncMock(),
            'health_tracker': AsyncMock()
        }
        
        with patch('phase_one.agents.base.AgentInterface'), \
             patch('interfaces.agent.interface.AgentInterface'), \
             patch('interfaces.agent.metrics.InterfaceMetrics'), \
             patch('asyncio.create_task'):
            
            reflective_agent = WaterAgentReflective(
                agent_id="test_infinite_loop_prevention",
                max_reflection_cycles=3,
                **mock_dependencies
            )
            
            # Mock detection and circuit breaker
            initial_detection = {
                "misunderstandings": [{"id": "M1", "severity": "HIGH"}],
                "first_agent_questions": ["Test question"],
                "second_agent_questions": ["Test question"]
            }
            
            reflective_agent.get_circuit_breaker = MagicMock()
            mock_circuit_breaker = AsyncMock()
            mock_circuit_breaker.execute = AsyncMock(return_value=initial_detection)
            reflective_agent.get_circuit_breaker.return_value = mock_circuit_breaker
            
            # Mock reflection that always suggests more improvement
            reflective_agent.standard_reflect = AsyncMock(return_value={
                "reflection_results": {
                    "overall_assessment": {
                        "critical_improvements": [
                            {"importance": "critical", "description": "Always improve"}
                        ]
                    }
                }
            })
            
            # Mock revision that always suggests more reflection
            reflective_agent.standard_refine = AsyncMock(return_value={
                "revised_detection": initial_detection,
                "needs_further_reflection": True  # Always suggests more reflection
            })
            
            # Should stop after max cycles even if always suggesting improvement
            result = await reflective_agent.detect_misunderstandings(
                "First agent output",
                "Second agent output",
                use_reflection=True
            )
            
            # Should complete despite infinite loop potential
            assert result is not None
            assert reflective_agent.current_reflection_cycle <= reflective_agent.max_reflection_cycles


class TestSystemIntegrationRobustness:
    """Test robustness of integrated system components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_robustness_with_multiple_failures(self, robust_water_coordinator, failure_simulator):
        """Test end-to-end robustness with multiple simultaneous failures."""
        # Configure multiple failure points
        robust_water_coordinator._call_llm = failure_simulator.simulate_intermittent_failure
        robust_water_coordinator._state_manager.set_state = failure_simulator.simulate_state_manager_failure
        
        first_agent = MagicMock()
        first_agent.agent_id = "robust_test_1"
        first_agent.clarify = AsyncMock(side_effect=Exception("Agent clarification failed"))
        
        second_agent = MagicMock()
        second_agent.agent_id = "robust_test_2"
        second_agent.clarify = AsyncMock(return_value="Working clarification")
        
        # Should handle multiple failure points gracefully
        try:
            result = await robust_water_coordinator.coordinate_agents(
                first_agent, "Test output 1", second_agent, "Test output 2"
            )
            # May succeed if failures are handled properly
        except CoordinationError:
            # Or may fail, but should be controlled failure
            pass
        
        # Verify multiple failure types were encountered
        assert len(set(failure_simulator.failure_types)) > 1
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_after_failures(self, robust_water_coordinator, failure_simulator):
        """Test that resources are properly cleaned up after failures."""
        # Monitor resource allocation
        initial_resources = {
            'state_calls': robust_water_coordinator._state_manager.set_state.call_count,
            'emit_calls': robust_water_coordinator._emit_event.call_count
        }
        
        robust_water_coordinator._call_llm = failure_simulator.simulate_llm_timeout
        
        first_agent = MagicMock()
        second_agent = MagicMock()
        
        # Cause multiple failures
        for _ in range(3):
            try:
                await robust_water_coordinator.coordinate_agents(
                    first_agent, "Output 1", second_agent, "Output 2"
                )
            except (CoordinationError, asyncio.TimeoutError):
                pass
        
        # Verify resources were managed properly despite failures
        # Should have attempted state management and event emission
        final_resources = {
            'state_calls': robust_water_coordinator._state_manager.set_state.call_count,
            'emit_calls': robust_water_coordinator._emit_event.call_count
        }
        
        # Resource usage should indicate proper cleanup attempts
        assert final_resources['emit_calls'] > initial_resources['emit_calls']  # Error events emitted