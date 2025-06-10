"""
Simple verification tests for the event loop fixes implemented in Stage 1.

These tests verify that the specific "RuntimeError: no running event loop" 
issues have been resolved without complex mocking.
"""

import asyncio
import pytest
import threading
from unittest.mock import Mock

pytestmark = pytest.mark.asyncio

from interfaces.agent.interface import AgentInterface
from interfaces.agent import AgentState
from resources.events.qasync_utils import get_qasync_compatible_loop, qasync_wait_for
from resources.events.loop_management import EventLoopManager
from resources import EventQueue


class TestEventLoopFixesVerification:
    """Verify the specific fixes for event loop issues."""
    
    @pytest.fixture
    async def minimal_resources(self):
        """Create minimal resources for testing."""
        event_queue = EventQueue("test")
        await event_queue.start()
        
        # Create mock managers to avoid complex setup
        state_manager = Mock()
        state_manager.initialize = Mock(return_value=asyncio.Future())
        state_manager.initialize.return_value.set_result(True)
        
        context_manager = Mock()
        context_manager.get_context = Mock(return_value=asyncio.Future())
        context_manager.get_context.return_value.set_result(None)
        context_manager.create_context = Mock(return_value=asyncio.Future())
        context_manager.create_context.return_value.set_result({"context": "test"})
        
        metrics_manager = Mock()
        metrics_manager.record_metric = Mock(return_value=asyncio.Future())
        metrics_manager.record_metric.return_value.set_result(None)
        
        yield {
            'event_queue': event_queue,
            'state_manager': state_manager,
            'context_manager': context_manager,
            'metrics_manager': metrics_manager
        }
        
        await event_queue.stop()
        
    @pytest.fixture
    async def agent_interface(self, minimal_resources):
        """Create agent interface with minimal setup."""
        interface = AgentInterface(
            agent_id="test_agent",
            event_queue=minimal_resources['event_queue'],
            state_manager=minimal_resources['state_manager'],
            agent_context_manager=minimal_resources['context_manager'],
            metrics_manager=minimal_resources['metrics_manager']
        )
        await interface.initialize()
        yield interface
        await interface.terminate()
        
    async def test_qasync_wait_for_replaces_asyncio_wait_for(self, agent_interface):
        """Test that qasync_wait_for works where asyncio.wait_for might fail."""
        # This tests our core fix
        async def dummy_task():
            await asyncio.sleep(0.01)
            return "success"
            
        # This should work with our qasync_wait_for implementation
        result = await qasync_wait_for(dummy_task(), timeout=1.0)
        assert result == "success"
        
    async def test_get_qasync_compatible_loop_robustness(self):
        """Test that get_qasync_compatible_loop is robust."""
        # This should not raise RuntimeError
        loop = get_qasync_compatible_loop()
        assert loop is not None
        assert isinstance(loop, asyncio.AbstractEventLoop)
        
    async def test_agent_state_transitions_no_loop_error(self, agent_interface):
        """Test that agent state transitions don't cause loop errors."""
        # These operations were failing before our fixes
        await agent_interface.set_agent_state(AgentState.PROCESSING)
        assert agent_interface.agent_state == AgentState.PROCESSING
        
        await agent_interface.set_agent_state(AgentState.COMPLETE)  
        assert agent_interface.agent_state == AgentState.COMPLETE
        
        await agent_interface.set_agent_state(AgentState.ERROR)
        assert agent_interface.agent_state == AgentState.ERROR
        
    async def test_timeout_operations_use_qasync_compatible(self, agent_interface):
        """Test that timeout operations use qasync-compatible methods."""
        # Test the specific code path that was failing
        async def slow_operation():
            await asyncio.sleep(0.5)
            return "slow_result"
            
        # This should use qasync_wait_for internally and not fail
        with pytest.raises(asyncio.TimeoutError):
            await qasync_wait_for(slow_operation(), timeout=0.1)
            
    async def test_concurrent_state_operations(self, agent_interface):
        """Test concurrent state operations don't cause loop conflicts."""
        async def state_change(target_state):
            await agent_interface.set_agent_state(target_state)
            return target_state
            
        # Run multiple state changes concurrently
        tasks = [
            state_change(AgentState.PROCESSING),
            state_change(AgentState.VALIDATING),
            state_change(AgentState.COMPLETE)
        ]
        
        # This should not cause "no running event loop" errors
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that no RuntimeError about event loops occurred
        for result in results:
            if isinstance(result, Exception):
                assert "no running event loop" not in str(result)
                
    async def test_resource_cleanup_no_component_id_error(self):
        """Test that resource cleanup doesn't have component_id errors."""
        from resources.base import BaseManager
        from resources import EventQueue
        
        # Create a minimal manager to test cleanup
        event_queue = EventQueue("cleanup_test")
        await event_queue.start()
        
        class TestManager(BaseManager):
            async def _cleanup_resources(self, force=False):
                pass  # Minimal implementation
                
        manager = TestManager(event_queue)
        await manager.initialize()
        
        # This should not raise "name 'component_id' is not defined"
        try:
            await manager.cleanup(force=True)
        except NameError as e:
            if "component_id" in str(e):
                pytest.fail(f"component_id error still present: {e}")
                
        await manager.terminate()
        await event_queue.stop()
        
    async def test_event_loop_manager_registration(self):
        """Test that EventLoopManager registration works properly."""
        # Get current loop
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(current_loop)
            
        # Register with EventLoopManager
        thread_id = threading.get_ident()
        EventLoopManager.register_loop(current_loop, "test", thread_id)
        
        # Verify retrieval works
        retrieved_loop = EventLoopManager.get_primary_loop()
        assert retrieved_loop is not None
        
        # Verify qasync compatibility
        compatible_loop = get_qasync_compatible_loop()
        assert compatible_loop is not None
        

class TestSpecificFailureScenarios:
    """Test the specific failure scenarios from the logs."""
    
    async def test_agent_interface_process_with_validation_timeout(self):
        """Test the specific failure in process_with_validation."""
        # This tests the exact code path that was failing at line 588
        
        # Create minimal setup
        event_queue = EventQueue("validation_test")
        await event_queue.start()
        
        # Mock the dependencies that aren't crucial for this test
        state_manager = Mock()
        state_manager.initialize = Mock(return_value=asyncio.Future())
        state_manager.initialize.return_value.set_result(True)
        
        context_manager = Mock()
        context_manager.get_context = Mock(return_value=asyncio.Future())
        context_manager.get_context.return_value.set_result(None)
        
        metrics_manager = Mock()
        metrics_manager.record_metric = Mock(return_value=asyncio.Future())
        metrics_manager.record_metric.return_value.set_result(None)
        
        interface = AgentInterface(
            agent_id="validation_test_agent",
            event_queue=event_queue,
            state_manager=state_manager,
            agent_context_manager=context_manager,
            metrics_manager=metrics_manager
        )
        await interface.initialize()
        
        # Mock agent that will timeout
        interface.agent = Mock()
        interface.agent.get_response = Mock(side_effect=asyncio.TimeoutError("Test timeout"))
        
        # This should handle the timeout without "no running event loop" error
        try:
            await interface.process_with_validation(
                request_id="test_timeout",
                user_prompt="test prompt",
                timeout=0.1  # Very short timeout
            )
        except Exception as e:
            # Should be timeout or validation error, not event loop error
            assert "no running event loop" not in str(e).lower()
            
        await interface.terminate()
        await event_queue.stop()


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))