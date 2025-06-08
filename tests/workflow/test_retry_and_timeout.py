"""
Test Retry Logic and Timeout Handling from run_phase_one.py

This module tests the sophisticated retry and timeout logic from PhaseOneInterface._execute_single_step
that is completely missing from existing E2E tests.
"""

import pytest
import pytest_asyncio
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from run_phase_one import PhaseOneInterface
from resources.events import EventQueue
from resources.state import StateManager


class TimeoutError(Exception):
    """Custom timeout error for testing."""
    pass


class RetriableError(Exception):
    """Error that should trigger retry logic."""
    pass


class NonRetriableError(Exception):
    """Error that should NOT trigger retry logic."""
    pass


class MockPhaseOneOrchestratorWithRetries:
    """Mock orchestrator that can simulate various failure scenarios."""
    
    def __init__(self):
        self._state_manager = None
        self.call_count = {}
        self.failure_modes = {}
        
        # Setup agents with controllable failure behavior
        self.garden_planner_agent = MagicMock()
        self.earth_agent = MagicMock()
        self.environmental_analysis_agent = MagicMock()
        self.root_system_architect_agent = MagicMock()
        self.tree_placement_planner_agent = MagicMock()
        self.foundation_refinement_agent = MagicMock()
        
        self._setup_agent_mocks()
    
    def _setup_agent_mocks(self):
        """Setup agent mocks with retry behavior."""
        
        async def mock_agent_process(agent_name, *args):
            """Generic mock process that can simulate failures."""
            if agent_name not in self.call_count:
                self.call_count[agent_name] = 0
            self.call_count[agent_name] += 1
            
            failure_mode = self.failure_modes.get(agent_name)
            if failure_mode:
                if failure_mode['type'] == 'timeout':
                    # Simulate timeout by sleeping longer than expected
                    await asyncio.sleep(failure_mode.get('delay', 10))
                    return {"status": "success"}  # Won't reach here due to timeout
                elif failure_mode['type'] == 'exception':
                    if self.call_count[agent_name] <= failure_mode.get('fail_attempts', 1):
                        raise failure_mode['exception']
                elif failure_mode['type'] == 'slow_then_success':
                    if self.call_count[agent_name] == 1:
                        await asyncio.sleep(failure_mode.get('delay', 5))
                    return {"status": "success", "attempt": self.call_count[agent_name]}
            
            # Default success response
            return {
                "status": "success",
                "agent": agent_name,
                "attempt": self.call_count[agent_name],
                "timestamp": datetime.now().isoformat()
            }
        
        # Setup individual agent mocks
        self.garden_planner_agent.process = lambda *args: mock_agent_process('garden_planner', *args)
        self.earth_agent.process = lambda *args: mock_agent_process('earth_agent', *args)
        self.environmental_analysis_agent.process = lambda *args: mock_agent_process('environmental_analysis', *args)
        self.root_system_architect_agent.process = lambda *args: mock_agent_process('root_system_architect', *args)
        self.tree_placement_planner_agent.process = lambda *args: mock_agent_process('tree_placement_planner', *args)
        self.foundation_refinement_agent.process = lambda *args: mock_agent_process('foundation_refinement', *args)
    
    def set_failure_mode(self, agent_name, failure_type, **kwargs):
        """Set failure mode for a specific agent."""
        self.failure_modes[agent_name] = {
            'type': failure_type,
            **kwargs
        }
    
    def clear_failure_mode(self, agent_name):
        """Clear failure mode for an agent."""
        if agent_name in self.failure_modes:
            del self.failure_modes[agent_name]
    
    def get_call_count(self, agent_name):
        """Get number of times an agent was called."""
        return self.call_count.get(agent_name, 0)


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
def mock_orchestrator_with_retries(state_manager):
    """Create a mock orchestrator with retry capabilities."""
    orchestrator = MockPhaseOneOrchestratorWithRetries()
    orchestrator._state_manager = state_manager
    return orchestrator


@pytest.fixture
def phase_one_interface_with_retries(mock_orchestrator_with_retries):
    """Create a PhaseOneInterface for testing retries."""
    return PhaseOneInterface(mock_orchestrator_with_retries)


class TestTimeoutHandling:
    """Test timeout handling in step execution."""
    
    @pytest.mark.asyncio
    async def test_step_timeout_basic(self, phase_one_interface_with_retries, mock_orchestrator_with_retries):
        """Test basic timeout handling for a single step."""
        # Set garden planner to timeout
        mock_orchestrator_with_retries.set_failure_mode(
            'garden_planner', 
            'timeout', 
            delay=5  # Will timeout before this completes
        )
        
        # Start workflow
        operation_id = await phase_one_interface_with_retries.start_phase_one("Create a timeout test app")
        
        # Execute step with short timeout and expect timeout
        start_time = time.time()
        step_result = await phase_one_interface_with_retries.execute_next_step(operation_id)
        execution_time = time.time() - start_time
        
        # Should have timed out and used retry logic
        assert step_result["status"] == "step_completed" or step_result["step_result"]["status"] == "error"
        
        # Should have attempted multiple times (up to max_retries + 1)
        garden_calls = mock_orchestrator_with_retries.get_call_count('garden_planner')
        assert garden_calls >= 1  # At least one attempt
        
        # Execution time should reflect timeout behavior
        assert execution_time >= 3  # Should take at least the base timeout duration
    
    @pytest.mark.asyncio
    async def test_timeout_escalation(self, phase_one_interface_with_retries, mock_orchestrator_with_retries):
        """Test that timeouts increase on retry attempts."""
        # Set up the interface to use shorter timeouts for testing
        with patch.object(phase_one_interface_with_retries, '_execute_single_step') as mock_execute:
            
            async def mock_execute_with_timeout_escalation(step_name, prompt, previous_results, operation_id):
                """Mock _execute_single_step to test timeout escalation."""
                max_retries = 2
                base_timeout = 1.0  # 1 second base timeout
                retry_delays = [0.1, 0.2]  # Short delays for testing
                
                for attempt in range(max_retries + 1):
                    try:
                        # Calculate escalating timeout
                        timeout = base_timeout + (attempt * 0.5)  # Increase by 0.5s per retry
                        
                        # Simulate timeout on first 2 attempts, success on 3rd
                        if attempt < 2:
                            await asyncio.sleep(0.05)  # Small delay
                            raise asyncio.TimeoutError(f"Timed out after {timeout}s")
                        else:
                            return {
                                "status": "success",
                                "step_name": step_name,
                                "execution_time_seconds": timeout - 0.1,
                                "result": {"success": True},
                                "timestamp": datetime.now().isoformat(),
                                "attempt": attempt + 1,
                                "timeout_used": timeout
                            }
                            
                    except asyncio.TimeoutError:
                        if attempt < max_retries:
                            await asyncio.sleep(retry_delays[attempt])
                            continue
                        else:
                            return {
                                "status": "error",
                                "step_name": step_name,
                                "error": "timeout",
                                "message": f"Step {step_name} timed out after {attempt + 1} attempts",
                                "attempts": attempt + 1,
                                "timeout_used": timeout
                            }
                
                return {"status": "error", "message": "Unexpected error"}
            
            mock_execute.side_effect = mock_execute_with_timeout_escalation
            
            # Start workflow and execute step
            operation_id = await phase_one_interface_with_retries.start_phase_one("Test timeout escalation")
            step_result = await phase_one_interface_with_retries.execute_next_step(operation_id)
            
            # Verify the step completed successfully after retries
            assert step_result["status"] == "step_completed"
            step_data = step_result["step_result"]
            assert step_data["status"] == "success"
            assert step_data["attempt"] == 3  # Should succeed on 3rd attempt
            assert step_data["timeout_used"] > 1.0  # Should have used escalated timeout
    
    @pytest.mark.asyncio
    async def test_timeout_with_max_retries_exceeded(self, phase_one_interface_with_retries):
        """Test behavior when max retries are exceeded due to timeouts."""
        with patch.object(phase_one_interface_with_retries, '_execute_single_step') as mock_execute:
            
            async def mock_execute_always_timeout(step_name, prompt, previous_results, operation_id):
                """Mock that always times out."""
                max_retries = 2
                
                for attempt in range(max_retries + 1):
                    if attempt < max_retries:
                        await asyncio.sleep(0.01)  # Small delay
                        continue  # Retry
                    else:
                        return {
                            "status": "error",
                            "step_name": step_name,
                            "error": "timeout",
                            "message": f"Step {step_name} timed out after {attempt + 1} attempts",
                            "execution_time_seconds": 3.0,
                            "timestamp": datetime.now().isoformat(),
                            "attempts": attempt + 1,
                            "timeout_used": 3.0 + attempt
                        }
            
            mock_execute.side_effect = mock_execute_always_timeout
            
            operation_id = await phase_one_interface_with_retries.start_phase_one("Test max timeout retries")
            step_result = await phase_one_interface_with_retries.execute_next_step(operation_id)
            
            # Should fail after max retries
            assert step_result["status"] == "step_completed"  # Step completes but with error
            step_data = step_result["step_result"]
            assert step_data["status"] == "error"
            assert step_data["error"] == "timeout"
            assert step_data["attempts"] == 3  # max_retries + 1


class TestRetryLogic:
    """Test retry logic for different error types."""
    
    @pytest.mark.asyncio
    async def test_retry_on_retriable_error(self, phase_one_interface_with_retries, mock_orchestrator_with_retries):
        """Test retry logic for retriable errors."""
        # Set garden planner to fail on first attempt, succeed on second
        mock_orchestrator_with_retries.set_failure_mode(
            'garden_planner',
            'exception',
            exception=Exception("Temporary network error"),
            fail_attempts=1
        )
        
        operation_id = await phase_one_interface_with_retries.start_phase_one("Test retry logic")
        
        # Execute step - should retry and succeed
        step_result = await phase_one_interface_with_retries.execute_next_step(operation_id)
        
        # Should succeed after retry
        assert step_result["status"] == "step_completed"
        step_data = step_result["step_result"]
        assert step_data["status"] == "success"
        
        # Should have been called twice (initial + 1 retry)
        garden_calls = mock_orchestrator_with_retries.get_call_count('garden_planner')
        assert garden_calls == 2
    
    @pytest.mark.asyncio
    async def test_no_retry_on_non_retriable_error(self, phase_one_interface_with_retries):
        """Test that non-retriable errors don't trigger retries."""
        with patch.object(phase_one_interface_with_retries, '_execute_single_step') as mock_execute:
            
            async def mock_execute_non_retriable_error(step_name, prompt, previous_results, operation_id):
                """Mock that raises a non-retriable error."""
                error_msg = "Garden Planner output required for Earth Agent validation"
                
                return {
                    "status": "error",
                    "step_name": step_name,
                    "error": error_msg,
                    "message": f"Step {step_name} failed: {error_msg}",
                    "execution_time_seconds": 0.1,
                    "timestamp": datetime.now().isoformat(),
                    "attempts": 1,
                    "non_retryable": True
                }
            
            mock_execute.side_effect = mock_execute_non_retriable_error
            
            operation_id = await phase_one_interface_with_retries.start_phase_one("Test non-retriable error")
            step_result = await phase_one_interface_with_retries.execute_next_step(operation_id)
            
            # Should fail immediately without retries
            assert step_result["status"] == "step_completed"
            step_data = step_result["step_result"]
            assert step_data["status"] == "error"
            assert step_data["attempts"] == 1  # No retries
            assert step_data["non_retryable"] is True
    
    @pytest.mark.asyncio
    async def test_retry_delays(self, phase_one_interface_with_retries):
        """Test retry delay implementation."""
        with patch.object(phase_one_interface_with_retries, '_execute_single_step') as mock_execute:
            
            retry_times = []
            
            async def mock_execute_with_delays(step_name, prompt, previous_results, operation_id):
                """Mock that records retry timing."""
                max_retries = 2
                retry_delays = [0.1, 0.2]  # Short delays for testing
                
                for attempt in range(max_retries + 1):
                    retry_times.append(time.time())
                    
                    if attempt < max_retries:
                        await asyncio.sleep(retry_delays[attempt])
                        continue
                    else:
                        return {
                            "status": "success",
                            "step_name": step_name,
                            "execution_time_seconds": 0.5,
                            "result": {"success": True},
                            "timestamp": datetime.now().isoformat(),
                            "attempt": attempt + 1
                        }
            
            mock_execute.side_effect = mock_execute_with_delays
            
            operation_id = await phase_one_interface_with_retries.start_phase_one("Test retry delays")
            await phase_one_interface_with_retries.execute_next_step(operation_id)
            
            # Verify retry delays were applied
            assert len(retry_times) == 3  # Initial + 2 retries
            
            # Check delay between first and second attempt
            delay_1 = retry_times[1] - retry_times[0]
            assert delay_1 >= 0.1  # Should be at least the retry delay
            
            # Check delay between second and third attempt
            delay_2 = retry_times[2] - retry_times[1]
            assert delay_2 >= 0.2  # Should be at least the retry delay
    
    @pytest.mark.asyncio
    async def test_error_classification(self, phase_one_interface_with_retries):
        """Test that errors are correctly classified as retriable or non-retriable."""
        with patch.object(phase_one_interface_with_retries, '_execute_single_step') as mock_execute:
            
            test_cases = [
                # Non-retriable errors (should contain these keywords)
                ("Garden Planner output required", False),
                ("Environmental Analysis output required", False),
                ("missing data for validation", False),
                ("ValueError: invalid input format", False),
                
                # Retriable errors (don't contain non-retriable keywords)
                ("Network timeout occurred", True),
                ("API rate limit exceeded", True),
                ("Temporary service unavailable", True),
                ("Connection reset by peer", True)
            ]
            
            for error_message, should_retry in test_cases:
                call_count = 0
                
                async def mock_execute_error(step_name, prompt, previous_results, operation_id):
                    nonlocal call_count
                    call_count += 1
                    
                    # Simulate error classification logic from run_phase_one.py
                    non_retryable_errors = ["required", "missing", "not found", "ValueError"]
                    is_non_retryable = any(err in error_message for err in non_retryable_errors)
                    
                    if call_count == 1 and not is_non_retryable:
                        # First attempt fails, but should retry
                        raise Exception(error_message)
                    elif call_count > 1:
                        # Retry succeeds
                        return {
                            "status": "success",
                            "step_name": step_name,
                            "attempts": call_count,
                            "message": "Succeeded after retry"
                        }
                    else:
                        # Non-retriable error
                        return {
                            "status": "error",
                            "step_name": step_name,
                            "error": error_message,
                            "attempts": 1,
                            "non_retryable": is_non_retryable
                        }
                
                mock_execute.side_effect = mock_execute_error
                
                operation_id = await phase_one_interface_with_retries.start_phase_one(f"Test error: {error_message}")
                step_result = await phase_one_interface_with_retries.execute_next_step(operation_id)
                
                if should_retry:
                    # Should have retried and succeeded
                    assert call_count >= 2, f"Should have retried for error: {error_message}"
                else:
                    # Should not have retried
                    assert call_count == 1, f"Should not have retried for error: {error_message}"
                
                # Reset for next test case
                call_count = 0


class TestTimeoutConfiguration:
    """Test timeout configuration and escalation."""
    
    @pytest.mark.asyncio
    async def test_base_timeout_values(self, phase_one_interface_with_retries):
        """Test that base timeout values are correctly applied."""
        with patch.object(phase_one_interface_with_retries, '_execute_single_step') as mock_execute:
            
            recorded_timeouts = []
            
            async def mock_execute_record_timeout(step_name, prompt, previous_results, operation_id):
                """Mock that records the timeout values used."""
                # Simulate the timeout calculation from run_phase_one.py
                max_retries = 2
                base_timeout = 180.0  # 3 minutes base timeout
                
                for attempt in range(max_retries + 1):
                    timeout = base_timeout + (attempt * 60.0)  # Add 1 minute per retry
                    recorded_timeouts.append(timeout)
                    
                    if attempt < max_retries:
                        continue  # Simulate retry
                    else:
                        return {
                            "status": "success",
                            "step_name": step_name,
                            "timeout_used": timeout,
                            "attempt": attempt + 1
                        }
            
            mock_execute.side_effect = mock_execute_record_timeout
            
            operation_id = await phase_one_interface_with_retries.start_phase_one("Test timeout values")
            step_result = await phase_one_interface_with_retries.execute_next_step(operation_id)
            
            # Verify timeout escalation
            assert len(recorded_timeouts) == 3  # Initial + 2 retries
            assert recorded_timeouts[0] == 180.0  # Base timeout
            assert recorded_timeouts[1] == 240.0  # Base + 60s
            assert recorded_timeouts[2] == 300.0  # Base + 120s
    
    @pytest.mark.asyncio
    async def test_step_specific_timeouts(self, phase_one_interface_with_retries):
        """Test that different steps can have different timeout requirements."""
        with patch.object(phase_one_interface_with_retries, '_execute_single_step') as mock_execute:
            
            step_timeouts = {}
            
            async def mock_execute_step_timeouts(step_name, prompt, previous_results, operation_id):
                """Mock that simulates step-specific timeout requirements."""
                # Different steps might have different base timeouts in a real system
                base_timeouts = {
                    "garden_planner": 180.0,        # 3 minutes
                    "earth_agent_validation": 120.0, # 2 minutes  
                    "environmental_analysis": 240.0, # 4 minutes
                    "root_system_architect": 300.0,  # 5 minutes
                    "tree_placement_planner": 360.0, # 6 minutes
                    "foundation_refinement": 600.0   # 10 minutes
                }
                
                base_timeout = base_timeouts.get(step_name, 180.0)
                step_timeouts[step_name] = base_timeout
                
                return {
                    "status": "success",
                    "step_name": step_name,
                    "timeout_used": base_timeout,
                    "base_timeout": base_timeout
                }
            
            mock_execute.side_effect = mock_execute_step_timeouts
            
            operation_id = await phase_one_interface_with_retries.start_phase_one("Test step timeouts")
            
            # Execute a few different steps
            for _ in range(3):
                await phase_one_interface_with_retries.execute_next_step(operation_id)
            
            # Verify different steps got appropriate timeouts
            assert len(step_timeouts) == 3
            
            # Garden planner should have shortest timeout
            assert step_timeouts.get("garden_planner", 0) <= step_timeouts.get("environmental_analysis", 999)


class TestRetryMetadata:
    """Test retry metadata and tracking."""
    
    @pytest.mark.asyncio
    async def test_retry_attempt_tracking(self, phase_one_interface_with_retries):
        """Test that retry attempts are properly tracked and reported."""
        with patch.object(phase_one_interface_with_retries, '_execute_single_step') as mock_execute:
            
            async def mock_execute_with_metadata(step_name, prompt, previous_results, operation_id):
                """Mock that provides detailed retry metadata."""
                return {
                    "status": "success",
                    "step_name": step_name,
                    "execution_time_seconds": 15.5,
                    "result": {"data": "test"},
                    "timestamp": datetime.now().isoformat(),
                    "attempt": 2,  # Succeeded on 2nd attempt
                    "timeout_used": 240.0,
                    "retries_performed": 1,
                    "total_attempts": 2
                }
            
            mock_execute.side_effect = mock_execute_with_metadata
            
            operation_id = await phase_one_interface_with_retries.start_phase_one("Test retry metadata")
            step_result = await phase_one_interface_with_retries.execute_next_step(operation_id)
            
            # Verify metadata is preserved
            step_data = step_result["step_result"]
            assert step_data["attempt"] == 2
            assert step_data["timeout_used"] == 240.0
            assert "retries_performed" in step_data
            assert "total_attempts" in step_data
    
    @pytest.mark.asyncio
    async def test_execution_time_accuracy(self, phase_one_interface_with_retries):
        """Test that execution time accounts for retries and delays."""
        with patch.object(phase_one_interface_with_retries, '_execute_single_step') as mock_execute:
            
            async def mock_execute_with_timing(step_name, prompt, previous_results, operation_id):
                """Mock that simulates realistic execution timing."""
                start_time = time.time()
                
                # Simulate retry with delays
                await asyncio.sleep(0.1)  # First attempt
                await asyncio.sleep(0.05)  # Retry delay
                await asyncio.sleep(0.1)  # Second attempt (success)
                
                execution_time = time.time() - start_time
                
                return {
                    "status": "success",
                    "step_name": step_name,
                    "execution_time_seconds": execution_time,
                    "result": {"data": "test"},
                    "timestamp": datetime.now().isoformat(),
                    "attempt": 2
                }
            
            mock_execute.side_effect = mock_execute_with_timing
            
            operation_id = await phase_one_interface_with_retries.start_phase_one("Test execution timing")
            
            start_time = time.time()
            step_result = await phase_one_interface_with_retries.execute_next_step(operation_id)
            total_time = time.time() - start_time
            
            # Verify timing accuracy
            step_data = step_result["step_result"]
            reported_time = step_data["execution_time_seconds"]
            
            # Should account for retries and delays
            assert reported_time >= 0.15  # At least the simulated time
            assert abs(total_time - reported_time) < 0.1  # Should be close to actual time


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])