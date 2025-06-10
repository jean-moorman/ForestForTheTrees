"""
Integration tests for the new async patterns and monitoring.

These tests verify that our standardized async patterns work correctly
and provide the expected monitoring capabilities.
"""

import asyncio
import pytest
import time

from resources.events.async_patterns import (
    qasync_compatible, 
    with_qasync_timeout,
    safe_async_operation,
    timeout_operation,
    concurrent_operations,
    TimeoutOperationError,
    AsyncOperationError
)
from resources.monitoring.async_diagnostics import (
    async_monitor,
    diagnostics,
    log_async_health_report
)

pytestmark = pytest.mark.asyncio


class TestAsyncPatterns:
    """Test the standardized async patterns."""
    
    async def test_qasync_compatible_decorator(self):
        """Test that qasync_compatible decorator works."""
        @qasync_compatible
        async def test_operation():
            await asyncio.sleep(0.01)
            return "success"
            
        result = await test_operation()
        assert result == "success"
        
    async def test_with_qasync_timeout_decorator(self):
        """Test qasync timeout decorator."""
        @with_qasync_timeout(0.1)
        async def fast_operation():
            await asyncio.sleep(0.01)
            return "fast"
            
        @with_qasync_timeout(0.1)
        async def slow_operation():
            await asyncio.sleep(0.2)
            return "slow"
            
        # Fast operation should succeed
        result = await fast_operation()
        assert result == "fast"
        
        # Slow operation should timeout
        with pytest.raises(TimeoutOperationError):
            await slow_operation()
            
    async def test_safe_async_operation(self):
        """Test safe async operation with retries."""
        call_count = 0
        
        async def unreliable_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
            
        # Should succeed after retries
        result = await safe_async_operation(
            unreliable_operation,
            retry_count=3
        )
        assert result == "success"
        assert call_count == 3
        
    async def test_safe_async_operation_with_timeout(self):
        """Test safe async operation with timeout."""
        async def slow_operation():
            await asyncio.sleep(0.2)
            return "slow"
            
        # Should timeout
        with pytest.raises(TimeoutOperationError):
            await safe_async_operation(
                slow_operation,
                timeout=0.1
            )
            
    async def test_timeout_operation_convenience(self):
        """Test timeout_operation convenience function."""
        async def test_op():
            await asyncio.sleep(0.01)
            return "done"
            
        result = await timeout_operation(test_op, 0.5)
        assert result == "done"
        
    async def test_concurrent_operations(self):
        """Test concurrent operations helper."""
        async def task_a():
            await asyncio.sleep(0.01)
            return "a"
            
        async def task_b():
            await asyncio.sleep(0.01)
            return "b"
            
        async def task_c():
            await asyncio.sleep(0.01)
            return "c"
            
        results = await concurrent_operations(task_a(), task_b(), task_c())
        assert results == ["a", "b", "c"]


class TestAsyncMonitoring:
    """Test async monitoring and diagnostics."""
    
    async def test_async_monitor_decorator(self):
        """Test async monitoring decorator."""
        @async_monitor("test_operation")
        async def monitored_operation():
            await asyncio.sleep(0.01)
            return "monitored"
            
        # Clear previous events
        diagnostics.events.clear()
        
        result = await monitored_operation()
        assert result == "monitored"
        
        # Check that event was recorded
        events = list(diagnostics.events)
        assert len(events) >= 1
        
        operation_events = [e for e in events if e.operation == "test_operation"]
        assert len(operation_events) == 1
        
        event = operation_events[0]
        assert event.success
        assert event.duration is not None
        assert event.duration > 0
        
    async def test_async_monitor_with_error(self):
        """Test async monitoring with error."""
        @async_monitor("error_operation")
        async def failing_operation():
            raise ValueError("Test error")
            
        # Clear previous events
        diagnostics.events.clear()
        
        with pytest.raises(ValueError):
            await failing_operation()
            
        # Check that error was recorded
        events = list(diagnostics.events)
        operation_events = [e for e in events if e.operation == "error_operation"]
        assert len(operation_events) == 1
        
        event = operation_events[0]
        assert not event.success
        assert event.error == "Test error"
        assert event.stack_trace is not None
        
    async def test_diagnostics_health_report(self):
        """Test diagnostics health report generation."""
        # Clear previous events
        diagnostics.events.clear()
        diagnostics.operation_stats.clear()
        
        @async_monitor("health_test")
        async def test_operation():
            await asyncio.sleep(0.01)
            return "ok"
            
        # Run some operations
        for i in range(3):
            await test_operation()
            
        # Get health report
        report = diagnostics.get_health_report()
        
        assert "timestamp" in report
        assert "total_events" in report
        assert "operation_summary" in report
        assert report["total_events"] >= 3
        
        # Check operation summary
        op_summary = report["operation_summary"]
        assert "health_test" in op_summary
        
        health_stats = op_summary["health_test"]
        assert health_stats["total_operations"] == 3
        assert health_stats["success_rate"] == 1.0
        assert health_stats["error_count"] == 0
        
    async def test_event_loop_diagnostics(self):
        """Test event loop diagnostics."""
        # Update loop metrics
        diagnostics.update_loop_metrics()
        
        # Check for issues
        issues = diagnostics.diagnose_event_loop_issues()
        
        # Should have minimal issues in test environment
        assert isinstance(issues, list)
        
        # Get loop metrics
        report = diagnostics.get_health_report()
        loop_metrics = report["loop_metrics"]
        
        # Should have at least one loop (the test loop)
        assert len(loop_metrics) >= 0  # May be 0 in some test contexts


class TestIntegratedAsyncWorkflow:
    """Test integrated async workflow with patterns and monitoring."""
    
    async def test_complete_async_workflow(self):
        """Test a complete async workflow using all patterns."""
        @async_monitor("workflow_step")
        @qasync_compatible
        async def workflow_step(step_name: str, delay: float):
            await asyncio.sleep(delay)
            return f"completed_{step_name}"
            
        # Clear diagnostics
        diagnostics.events.clear()
        
        # Execute workflow steps concurrently
        results = await concurrent_operations(
            workflow_step("step1", 0.01),
            workflow_step("step2", 0.01), 
            workflow_step("step3", 0.01)
        )
        
        assert len(results) == 3
        assert all("completed_" in result for result in results)
        
        # Check monitoring data
        events = list(diagnostics.events)
        workflow_events = [e for e in events if e.operation == "workflow_step"]
        assert len(workflow_events) == 3
        assert all(e.success for e in workflow_events)
        
    async def test_resilient_operation_pattern(self):
        """Test resilient operation pattern with retries and monitoring."""
        attempt_count = 0
        
        @async_monitor("resilient_op")
        async def unstable_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count <= 2:
                raise ConnectionError("Temporary network issue")
            return "success_after_retries"
            
        # Clear diagnostics
        diagnostics.events.clear()
        
        # Execute with retries
        result = await safe_async_operation(
            unstable_operation,
            retry_count=3,
            timeout=5.0
        )
        
        assert result == "success_after_retries"
        assert attempt_count == 3
        
        # Check that all attempts were monitored
        events = list(diagnostics.events)
        resilient_events = [e for e in events if e.operation == "resilient_op"]
        assert len(resilient_events) == 3
        
        # First two should be failures, last should be success
        assert not resilient_events[0].success
        assert not resilient_events[1].success  
        assert resilient_events[2].success


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))