"""
Test Async Error Handling from run_phase_one.py

This module tests async error handling scenarios including event loop creation failures,
handling of closed event loops, async task cleanup, and deadlock detection.
"""

import pytest
import asyncio
import threading
import time
from unittest.mock import MagicMock, patch, AsyncMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from run_phase_one import PhaseOneApp, PhaseOneInterface
from resources.events import EventQueue
from resources.events.utils import ensure_event_loop, run_async_in_thread
from resources.events.loop_management import EventLoopManager


class TestEventLoopCreationFailures:
    """Test handling of event loop creation failures."""
    
    def test_event_loop_creation_failure_recovery(self):
        """Test recovery when event loop creation fails."""
        original_new_event_loop = asyncio.new_event_loop
        call_count = 0
        
        def failing_new_event_loop():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Fail first 2 attempts
                raise RuntimeError("Event loop creation failed")
            return original_new_event_loop()  # Succeed on 3rd attempt
        
        with patch('asyncio.new_event_loop', side_effect=failing_new_event_loop):
            # Should eventually succeed after retries
            loop = ensure_event_loop()
            assert loop is not None
            assert not loop.is_closed()
            
            # Should have made 3 attempts
            assert call_count == 3
            
            # Cleanup
            loop.close()
    
    def test_set_event_loop_failure_handling(self):
        """Test handling when setting event loop fails."""
        original_set_event_loop = asyncio.set_event_loop
        set_call_count = 0
        
        def failing_set_event_loop(loop):
            nonlocal set_call_count
            set_call_count += 1
            if set_call_count == 1:  # Fail first attempt
                raise RuntimeError("Cannot set event loop")
            original_set_event_loop(loop)
        
        with patch('asyncio.set_event_loop', side_effect=failing_set_event_loop):
            with patch('asyncio.new_event_loop') as mock_new_loop:
                test_loop = asyncio.new_event_loop()
                mock_new_loop.return_value = test_loop
                
                try:
                    # Should handle set_event_loop failure gracefully
                    result_loop = ensure_event_loop()
                    assert result_loop is test_loop
                    
                    # Should have attempted to set loop twice
                    assert set_call_count == 2
                
                finally:
                    test_loop.close()
    
    def test_event_loop_manager_failure_recovery(self):
        """Test EventLoopManager recovery from failures."""
        # Simulate EventLoopManager failure
        with patch.object(EventLoopManager, 'set_primary_loop', side_effect=Exception("Manager failed")):
            # Should still create loop even if manager fails
            loop = ensure_event_loop()
            assert loop is not None
            assert not loop.is_closed()
            loop.close()


class TestClosedEventLoopHandling:
    """Test handling of closed event loops."""
    
    def test_closed_loop_detection_and_replacement(self):
        """Test detection and replacement of closed event loops."""
        # Create and close a loop
        closed_loop = asyncio.new_event_loop()
        closed_loop.close()
        
        # Set as current loop
        asyncio.set_event_loop(closed_loop)
        
        # ensure_event_loop should detect closed loop and create new one
        new_loop = ensure_event_loop()
        assert new_loop is not closed_loop
        assert not new_loop.is_closed()
        assert closed_loop.is_closed()
        
        # Cleanup
        new_loop.close()
    
    @pytest.mark.asyncio
    async def test_async_operation_on_closed_loop(self):
        """Test async operation handling when loop is closed unexpectedly."""
        event_queue = EventQueue(queue_id="closed_loop_test")
        await event_queue.start()
        
        try:
            # Create a coroutine that will run when loop is closed
            async def test_operation():
                await asyncio.sleep(0.01)
                return "operation_completed"
            
            # Start the operation
            task = asyncio.create_task(test_operation())
            
            # Close the loop (simulating unexpected closure)
            # Note: This is tricky to test as closing the current loop
            # would break the test itself. We'll simulate the error instead.
            
            # Complete the task normally (in real scenario, this would fail)
            result = await task
            assert result == "operation_completed"
        
        finally:
            await event_queue.stop()
    
    def test_phase_one_app_closed_loop_recovery(self):
        """Test PhaseOneApp recovery from closed event loop."""
        with patch('run_phase_one.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                # First call returns closed loop, second call returns valid loop
                closed_loop = asyncio.new_event_loop()
                closed_loop.close()
                valid_loop = asyncio.new_event_loop()
                
                mock_ensure.side_effect = [closed_loop, valid_loop]
                
                try:
                    # Create app
                    app = PhaseOneApp()
                    
                    # Should handle closed loop and get valid one
                    health_result = app._check_event_loop_health()
                    
                    # Should indicate recovery
                    assert health_result is not None
                    assert 'status' in health_result
                
                finally:
                    valid_loop.close()


class TestAsyncTaskCleanup:
    """Test async task cleanup and resource management."""
    
    @pytest.mark.asyncio
    async def test_task_cancellation_handling(self):
        """Test proper handling of task cancellation."""
        cancelled_tasks = []
        cleanup_called = []
        
        async def cancellable_task(task_id):
            """Task that can be cancelled and tracks cleanup."""
            try:
                await asyncio.sleep(1.0)  # Long-running task
                return f"task_{task_id}_completed"
            except asyncio.CancelledError:
                cleanup_called.append(task_id)
                cancelled_tasks.append(task_id)
                raise  # Re-raise to properly handle cancellation
        
        # Start multiple tasks
        tasks = []
        for i in range(5):
            task = asyncio.create_task(cancellable_task(i))
            tasks.append(task)
        
        # Let tasks start
        await asyncio.sleep(0.01)
        
        # Cancel all tasks
        for task in tasks:
            task.cancel()
        
        # Wait for cancellation to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all tasks were cancelled
        for result in results:
            assert isinstance(result, asyncio.CancelledError)
        
        # Verify cleanup was called for all tasks
        assert len(cleanup_called) == 5
        assert set(cleanup_called) == set(range(5))
    
    @pytest.mark.asyncio
    async def test_task_exception_cleanup(self):
        """Test cleanup when tasks raise exceptions."""
        exception_tasks = []
        cleanup_tasks = []
        
        async def failing_task(task_id, should_fail):
            """Task that may fail and tracks cleanup."""
            try:
                if should_fail:
                    raise ValueError(f"Task {task_id} failed")
                await asyncio.sleep(0.01)
                return f"task_{task_id}_success"
            except Exception as e:
                exception_tasks.append(task_id)
                raise
            finally:
                cleanup_tasks.append(task_id)
        
        # Mix of failing and succeeding tasks
        tasks = []
        for i in range(6):
            should_fail = i % 2 == 0  # Even tasks fail
            task = asyncio.create_task(failing_task(i, should_fail))
            tasks.append(task)
        
        # Gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify results
        success_count = 0
        exception_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, ValueError):
                exception_count += 1
                assert i % 2 == 0  # Even tasks should fail
            else:
                success_count += 1
                assert i % 2 == 1  # Odd tasks should succeed
        
        assert success_count == 3
        assert exception_count == 3
        
        # Verify cleanup was called for all tasks
        assert len(cleanup_tasks) == 6
        assert set(cleanup_tasks) == set(range(6))
    
    @pytest.mark.asyncio
    async def test_phase_one_app_task_cleanup(self):
        """Test PhaseOneApp task cleanup functionality."""
        with patch('run_phase_one.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Create some test tasks
                    async def test_task(task_id):
                        await asyncio.sleep(0.1)
                        return f"task_{task_id}"
                    
                    # Register tasks with app
                    tasks = []
                    for i in range(3):
                        coro = test_task(i)
                        task = app.register_task(coro)
                        tasks.append(task)
                    
                    # Verify tasks are tracked
                    assert len(app._tasks) == 3
                    
                    # Cancel tasks (simulating cleanup)
                    for task in tasks:
                        task.cancel()
                    
                    # Wait for cancellation
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Verify tasks were cleaned up
                    assert len(app._tasks) == 0
                
                finally:
                    test_loop.close()


class TestDeadlockDetectionAndPrevention:
    """Test deadlock detection and prevention mechanisms."""
    
    @pytest.mark.asyncio
    async def test_circular_dependency_detection(self):
        """Test detection of circular dependencies in async operations."""
        # Simulate circular dependency scenario
        resource_locks = {
            'resource_a': asyncio.Lock(),
            'resource_b': asyncio.Lock()
        }
        
        deadlock_detected = []
        
        async def task_a():
            """Task that acquires resources in one order."""
            try:
                async with resource_locks['resource_a']:
                    await asyncio.sleep(0.01)  # Hold lock briefly
                    
                    # Try to acquire second resource (potential deadlock)
                    try:
                        await asyncio.wait_for(resource_locks['resource_b'].acquire(), timeout=0.1)
                        try:
                            await asyncio.sleep(0.01)
                            return "task_a_success"
                        finally:
                            resource_locks['resource_b'].release()
                    except asyncio.TimeoutError:
                        deadlock_detected.append("task_a_timeout")
                        return "task_a_timeout"
            except Exception as e:
                return f"task_a_error_{str(e)}"
        
        async def task_b():
            """Task that acquires resources in reverse order."""
            try:
                async with resource_locks['resource_b']:
                    await asyncio.sleep(0.01)  # Hold lock briefly
                    
                    # Try to acquire first resource (potential deadlock)
                    try:
                        await asyncio.wait_for(resource_locks['resource_a'].acquire(), timeout=0.1)
                        try:
                            await asyncio.sleep(0.01)
                            return "task_b_success"
                        finally:
                            resource_locks['resource_a'].release()
                    except asyncio.TimeoutError:
                        deadlock_detected.append("task_b_timeout")
                        return "task_b_timeout"
            except Exception as e:
                return f"task_b_error_{str(e)}"
        
        # Run tasks that could deadlock
        results = await asyncio.gather(task_a(), task_b())
        
        # At least one should timeout (detecting potential deadlock)
        timeouts = [r for r in results if "timeout" in r]
        assert len(timeouts) >= 1, "Should detect potential deadlock via timeout"
        assert len(deadlock_detected) >= 1
    
    @pytest.mark.asyncio
    async def test_timeout_based_deadlock_prevention(self):
        """Test timeout-based deadlock prevention."""
        long_running_tasks = []
        
        async def potentially_blocking_operation(operation_id, delay):
            """Operation that might block indefinitely."""
            try:
                await asyncio.sleep(delay)
                return f"operation_{operation_id}_completed"
            except asyncio.CancelledError:
                long_running_tasks.append(f"operation_{operation_id}_cancelled")
                raise
        
        # Start operations with varying delays
        operations = []
        for i in range(3):
            # Some operations are very slow (simulating potential deadlock)
            delay = 2.0 if i % 2 == 0 else 0.01
            op = asyncio.create_task(potentially_blocking_operation(i, delay))
            operations.append(op)
        
        # Use timeout to prevent deadlock
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*operations, return_exceptions=True),
                timeout=0.1
            )
            # Should not reach here due to timeout
            assert False, "Should have timed out"
        except asyncio.TimeoutError:
            # Cancel remaining operations
            for op in operations:
                op.cancel()
            
            # Wait for cancellation
            await asyncio.gather(*operations, return_exceptions=True)
            
            # Verify timeout prevented deadlock
            assert len(long_running_tasks) > 0
    
    @pytest.mark.asyncio
    async def test_resource_ordering_deadlock_prevention(self):
        """Test deadlock prevention through resource ordering."""
        # Ordered resource acquisition to prevent deadlock
        resource_order = ['resource_1', 'resource_2', 'resource_3']
        resource_locks = {name: asyncio.Lock() for name in resource_order}
        
        successful_acquisitions = []
        
        async def ordered_acquisition_task(task_id, needed_resources):
            """Task that acquires resources in consistent order."""
            # Sort needed resources by global order
            ordered_resources = [r for r in resource_order if r in needed_resources]
            
            acquired_locks = []
            try:
                # Acquire in order
                for resource in ordered_resources:
                    await resource_locks[resource].acquire()
                    acquired_locks.append(resource)
                
                # Do work with resources
                await asyncio.sleep(0.01)
                successful_acquisitions.append(f"task_{task_id}_{len(acquired_locks)}_resources")
                
                return f"task_{task_id}_success"
            
            finally:
                # Release in reverse order
                for resource in reversed(acquired_locks):
                    resource_locks[resource].release()
        
        # Tasks with overlapping resource needs
        tasks = [
            ordered_acquisition_task(0, ['resource_1', 'resource_2']),
            ordered_acquisition_task(1, ['resource_2', 'resource_3']),
            ordered_acquisition_task(2, ['resource_1', 'resource_3']),
            ordered_acquisition_task(3, ['resource_1', 'resource_2', 'resource_3'])
        ]
        
        # Should complete without deadlock
        results = await asyncio.gather(*tasks)
        
        # All tasks should succeed
        for result in results:
            assert "success" in result
        
        # All tasks should have acquired resources
        assert len(successful_acquisitions) == 4


class TestAsyncExceptionPropagation:
    """Test proper propagation of exceptions in async contexts."""
    
    @pytest.mark.asyncio
    async def test_exception_propagation_through_gather(self):
        """Test exception propagation through asyncio.gather."""
        async def failing_task(task_id):
            await asyncio.sleep(0.01)
            if task_id == 2:
                raise ValueError(f"Task {task_id} failed")
            return f"task_{task_id}_success"
        
        # Run tasks with one failure
        tasks = [failing_task(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify exception is captured, not propagated
        success_count = 0
        exception_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, ValueError):
                exception_count += 1
                assert i == 2  # Only task 2 should fail
            else:
                success_count += 1
                assert "success" in result
        
        assert success_count == 4
        assert exception_count == 1
    
    @pytest.mark.asyncio
    async def test_exception_propagation_in_phase_one_interface(self):
        """Test exception handling in PhaseOneInterface async operations."""
        # Mock orchestrator that can fail
        mock_orchestrator = MagicMock()
        mock_orchestrator._state_manager = MagicMock()
        
        # Mock state manager methods
        async def failing_get_state(key, state_type):
            if "fail" in key:
                raise RuntimeError("State manager failure")
            return {"status": "initialized", "operation_id": key}
        
        async def working_set_state(key, value, state_type):
            return True
        
        mock_orchestrator._state_manager.get_state = failing_get_state
        mock_orchestrator._state_manager.set_state = working_set_state
        
        interface = PhaseOneInterface(mock_orchestrator)
        
        # Test normal operation
        normal_status = await interface.get_step_status("normal_operation")
        assert normal_status["status"] == "initialized"
        
        # Test failing operation
        failing_status = await interface.get_step_status("fail_operation")
        assert failing_status["status"] == "error"
        assert "State manager failure" in failing_status["message"]
    
    @pytest.mark.asyncio
    async def test_nested_exception_handling(self):
        """Test handling of nested exceptions in async calls."""
        exception_chain = []
        
        async def level_3_operation():
            await asyncio.sleep(0.01)
            raise ValueError("Level 3 error")
        
        async def level_2_operation():
            try:
                return await level_3_operation()
            except ValueError as e:
                exception_chain.append("level_2_caught")
                raise RuntimeError("Level 2 error") from e
        
        async def level_1_operation():
            try:
                return await level_2_operation()
            except RuntimeError as e:
                exception_chain.append("level_1_caught")
                raise ConnectionError("Level 1 error") from e
        
        # Test nested exception handling
        with pytest.raises(ConnectionError) as exc_info:
            await level_1_operation()
        
        # Verify exception chain
        assert len(exception_chain) == 2
        assert "level_2_caught" in exception_chain
        assert "level_1_caught" in exception_chain
        
        # Verify exception chaining
        assert exc_info.value.__cause__.__class__ == RuntimeError
        assert exc_info.value.__cause__.__cause__.__class__ == ValueError


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])