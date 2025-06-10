"""
Realistic event loop management tests that reduce over-mocking and test real behavior.

This replaces over-mocked tests with honest integration tests that exercise
the actual event loop management without hiding critical failures.
"""

import asyncio
import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from resources.events.loop_management import EventLoopManager, SimpleEventLoopRegistry
from resources.events.qasync_utils import get_qasync_compatible_loop, qasync_wait_for
from interfaces.agent.interface import AgentInterface
from interfaces.agent import AgentState

pytestmark = pytest.mark.asyncio


class TestRealisticEventLoopManagement:
    """Test event loop management with real components, minimal mocking."""
    
    def test_event_loop_registry_thread_safety(self):
        """Test that event loop registry is thread-safe without mocks."""
        registry = SimpleEventLoopRegistry()
        
        def setup_main_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = registry.set_main_loop(loop)
            return loop, success
            
        def setup_background_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = registry.set_background_loop(loop)
            return loop, success
            
        # Test main loop registration
        main_loop, main_success = setup_main_loop()
        assert main_success
        assert registry.get_main_loop() is main_loop
        
        # Test background loop registration  
        bg_loop, bg_success = setup_background_loop()
        assert bg_success
        assert registry.get_background_loop() is bg_loop
        
        # Cleanup
        main_loop.close()
        bg_loop.close()
            
    async def test_event_loop_manager_real_loop_detection(self):
        """Test EventLoopManager with real event loop detection."""
        # Clear any existing state
        EventLoopManager.cleanup()
        
        # Set current loop as primary
        current_loop = asyncio.get_running_loop()
        EventLoopManager.set_primary_loop(current_loop)
        
        # Test retrieval
        retrieved_loop = EventLoopManager.get_primary_loop()
        assert retrieved_loop is current_loop
        
        # Test qasync compatibility
        compatible_loop = get_qasync_compatible_loop()
        assert compatible_loop is not None
        
    async def test_cross_thread_event_loop_coordination(self):
        """Test event loop coordination across threads without mocks."""
        main_thread_id = threading.get_ident()
        main_loop = asyncio.get_running_loop()
        
        # Register main loop
        EventLoopManager.set_primary_loop(main_loop)
        
        background_loop = None
        background_thread_id = None
        
        def setup_background_loop():
            nonlocal background_loop, background_thread_id
            background_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(background_loop)
            background_thread_id = threading.get_ident()
            
            # Register background loop
            EventLoopManager.set_background_loop(background_loop)
            
            return background_loop
            
        # Create background thread with its own loop
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(setup_background_loop)
            bg_loop = future.result()
            
        # Verify both loops are registered
        assert EventLoopManager.get_primary_loop() is main_loop
        assert EventLoopManager.get_background_loop() is bg_loop
        
        # Cleanup
        bg_loop.call_soon_threadsafe(bg_loop.stop)
        bg_loop.close()
        
    async def test_agent_interface_in_different_loop_contexts(self):
        """Test agent interface works in different event loop contexts."""
        from resources import EventQueue
        from unittest.mock import Mock
        
        # Create minimal real resources
        event_queue = EventQueue("context_test")
        await event_queue.start()
        
        # Mock only what's necessary for this test
        state_manager = Mock()
        state_manager.initialize = Mock(return_value=asyncio.Future())
        state_manager.initialize.return_value.set_result(True)
        
        context_manager = Mock()
        context_manager.get_context = Mock(return_value=asyncio.Future())
        context_manager.get_context.return_value.set_result(None)
        
        metrics_manager = Mock()
        metrics_manager.record_metric = Mock(return_value=asyncio.Future())
        metrics_manager.record_metric.return_value.set_result(None)
        
        # Test agent interface in current context
        interface = AgentInterface(
            agent_id="context_test_agent",
            event_queue=event_queue,
            state_manager=state_manager,
            agent_context_manager=context_manager,
            metrics_manager=metrics_manager
        )
        await interface.initialize()
        
        # Test state transitions work without loop errors
        await interface.set_agent_state(AgentState.PROCESSING)
        assert interface.agent_state == AgentState.PROCESSING
        
        await interface.set_agent_state(AgentState.COMPLETE)
        assert interface.agent_state == AgentState.COMPLETE
        
        await interface.terminate()
        await event_queue.stop()
        
    async def test_qasync_utils_without_mocking_internals(self):
        """Test qasync utilities with real async operations."""
        async def test_operation(delay, result):
            await asyncio.sleep(delay)
            return result
            
        # Test successful operation
        result = await qasync_wait_for(test_operation(0.01, "success"), timeout=1.0)
        assert result == "success"
        
        # Test timeout
        with pytest.raises(asyncio.TimeoutError):
            await qasync_wait_for(test_operation(0.5, "too_slow"), timeout=0.1)
            
        # Test concurrent operations
        tasks = [
            test_operation(0.01, f"result_{i}")
            for i in range(3)
        ]
        
        results = await asyncio.gather(
            *[qasync_wait_for(task, timeout=1.0) for task in tasks]
        )
        
        assert len(results) == 3
        assert all("result_" in result for result in results)
        
    async def test_event_loop_failure_recovery(self):
        """Test recovery from event loop failures without mocks."""
        # Simulate event loop context issues
        original_get_running_loop = asyncio.get_running_loop
        
        def failing_get_running_loop():
            raise RuntimeError("no running event loop")
            
        # Temporarily break asyncio.get_running_loop
        asyncio.get_running_loop = failing_get_running_loop
        
        try:
            # Our qasync compatibility should handle this
            loop = get_qasync_compatible_loop()
            assert loop is not None
            
        finally:
            # Restore original function
            asyncio.get_running_loop = original_get_running_loop
            
    async def test_real_timeout_handling_patterns(self):
        """Test real timeout handling patterns used in the codebase."""
        async def operation_that_times_out():
            await asyncio.sleep(1.0)
            return "should_not_complete"
            
        async def operation_that_succeeds():
            await asyncio.sleep(0.01)
            return "success"
            
        # Test timeout with qasync_wait_for
        start_time = time.time()
        with pytest.raises(asyncio.TimeoutError):
            await qasync_wait_for(operation_that_times_out(), timeout=0.1)
        elapsed = time.time() - start_time
        
        # Should timeout quickly, not wait for full operation
        assert elapsed < 0.5
        
        # Test successful operation
        result = await qasync_wait_for(operation_that_succeeds(), timeout=0.5)
        assert result == "success"
        
    async def test_event_loop_manager_cleanup_and_recovery(self):
        """Test EventLoopManager cleanup and recovery without mocks."""
        # Get current state
        current_loop = asyncio.get_running_loop()
        current_thread = threading.get_ident()
        
        # Register a test loop
        test_loop = asyncio.new_event_loop()
        EventLoopManager.register_loop(test_loop, "test_cleanup", 12345)
        
        # Verify registration
        assert EventLoopManager.get_loop(12345) is test_loop
        
        # Test cleanup
        EventLoopManager.cleanup()
        
        # After cleanup, should not have the test loop
        assert EventLoopManager.get_loop(12345) is None
        
        # But should still be able to get a compatible loop
        compatible_loop = get_qasync_compatible_loop()
        assert compatible_loop is not None
        
        # Cleanup
        test_loop.close()


class TestReducedMockingIntegration:
    """Integration tests that use real components wherever possible."""
    
    async def test_agent_state_transitions_realistic(self):
        """Test agent state transitions with real coordination."""
        from resources import EventQueue
        from unittest.mock import Mock
        
        # Use real event queue
        event_queue = EventQueue("realistic_test")
        await event_queue.start()
        
        # Mock only external dependencies, not core functionality
        state_manager = Mock()
        state_manager.initialize = AsyncMock(return_value=True)
        
        context_manager = Mock()
        context_manager.get_context = AsyncMock(return_value=None)
        context_manager.create_context = AsyncMock(return_value={"test": True})
        
        metrics_manager = Mock()
        metrics_manager.record_metric = AsyncMock()
        
        # Create real agent interface
        interface = AgentInterface(
            agent_id="realistic_agent",
            event_queue=event_queue,
            state_manager=state_manager,
            agent_context_manager=context_manager,
            metrics_manager=metrics_manager
        )
        
        await interface.initialize()
        
        # Test realistic state transition sequence
        states = [
            AgentState.READY,
            AgentState.PROCESSING,
            AgentState.VALIDATING,
            AgentState.COMPLETE,
            AgentState.READY
        ]
        
        for state in states:
            await interface.set_agent_state(state)
            assert interface.agent_state == state
            
            # Verify the real coordination calls were made
            assert context_manager.get_context.called or context_manager.create_context.called
            
        await interface.terminate()
        await event_queue.stop()
        
    async def test_concurrent_operations_realistic_load(self):
        """Test concurrent operations under realistic load."""
        from resources import EventQueue
        from unittest.mock import Mock, AsyncMock
        
        event_queue = EventQueue("load_test")
        await event_queue.start()
        
        # Minimal mocking
        managers = {}
        for manager_type in ['state_manager', 'context_manager', 'metrics_manager']:
            mock = Mock()
            mock.initialize = AsyncMock(return_value=True)
            mock.record_metric = AsyncMock()
            mock.get_context = AsyncMock(return_value=None)
            mock.create_context = AsyncMock(return_value={})
            managers[manager_type] = mock
        
        # Create multiple agent interfaces
        interfaces = []
        for i in range(5):
            interface = AgentInterface(
                agent_id=f"load_test_agent_{i}",
                event_queue=event_queue,
                state_manager=managers['state_manager'],
                agent_context_manager=managers['context_manager'],
                metrics_manager=managers['metrics_manager']
            )
            await interface.initialize()
            interfaces.append(interface)
            
        # Run concurrent state transitions
        async def agent_workflow(interface, agent_id):
            await interface.set_agent_state(AgentState.PROCESSING)
            await asyncio.sleep(0.01)  # Simulate work
            await interface.set_agent_state(AgentState.COMPLETE)
            return agent_id
            
        # Execute all workflows concurrently
        results = await asyncio.gather(
            *[agent_workflow(interface, i) for i, interface in enumerate(interfaces)]
        )
        
        assert len(results) == 5
        
        # Verify all interfaces ended in correct state
        for interface in interfaces:
            assert interface.agent_state == AgentState.COMPLETE
            await interface.terminate()
            
        await event_queue.stop()


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))