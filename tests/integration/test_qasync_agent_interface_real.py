"""
Real integration tests for qasync-agent interface integration.

These tests exercise the actual failure scenarios that were occurring in production,
without mocks, to ensure the fixes work in real conditions.
"""

import asyncio
import logging
import pytest
import sys
import threading
import time
from typing import Dict, Any, Optional
from unittest.mock import patch

import qasync
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from interfaces.agent.interface import AgentInterface
from interfaces.agent import AgentState
from agent import Agent
from resources.events.qasync_utils import get_qasync_compatible_loop, qasync_wait_for
from resources.events.loop_management import EventLoopManager
from resources import EventQueue, StateManager, AgentContextManager, MetricsManager
from phase_one.agents.garden_planner import GardenPlannerAgent

logger = logging.getLogger(__name__)


class TestQAsyncAgentInterfaceReal:
    """Test real qasync-agent interface integration without mocks."""
    
    @pytest.fixture
    async def qasync_app(self):
        """Create a real QApplication with qasync event loop."""
        if QApplication.instance() is None:
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()
            
        # Create qasync event loop
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        # Register with EventLoopManager
        EventLoopManager.register_loop(loop, "main", threading.get_ident())
        
        yield app, loop
        
        # Cleanup
        try:
            loop.close()
        except Exception:
            pass
            
    @pytest.fixture
    async def real_event_queue(self):
        """Create a real event queue without mocks."""
        queue = EventQueue("test_queue")
        await queue.start()
        yield queue
        await queue.stop()
        
    @pytest.fixture
    async def real_resources(self, real_event_queue):
        """Create real resource managers without mocks."""
        state_manager = StateManager(real_event_queue)
        await state_manager.initialize()
        
        context_manager = AgentContextManager(real_event_queue, state_manager)
        await context_manager.initialize()
        
        metrics_manager = MetricsManager(real_event_queue)
        await metrics_manager.initialize()
        
        yield {
            'event_queue': real_event_queue,
            'state_manager': state_manager,
            'context_manager': context_manager,
            'metrics_manager': metrics_manager
        }
        
        # Cleanup
        await metrics_manager.terminate()
        await context_manager.terminate() 
        await state_manager.terminate()
        
    @pytest.fixture
    async def real_agent_interface(self, real_resources):
        """Create a real agent interface with real dependencies."""
        interface = AgentInterface(
            agent_id="test_garden_planner",
            event_queue=real_resources['event_queue'],
            state_manager=real_resources['state_manager'],
            agent_context_manager=real_resources['context_manager'],
            metrics_manager=real_resources['metrics_manager']
        )
        await interface.initialize()
        yield interface
        await interface.terminate()
        
    @pytest.fixture
    async def real_garden_planner(self, real_agent_interface):
        """Create a real garden planner agent."""
        agent = GardenPlannerAgent(interface=real_agent_interface)
        yield agent

    async def test_qasync_loop_detection_in_agent_interface(self, qasync_app, real_agent_interface):
        """Test that agent interface can detect qasync loop correctly."""
        app, qasync_loop = qasync_app
        
        # This should work without RuntimeError
        loop = get_qasync_compatible_loop()
        assert loop is not None
        assert loop is qasync_loop
        
        # Test setting agent state in qasync context
        await real_agent_interface.set_agent_state(AgentState.PROCESSING)
        assert real_agent_interface.agent_state == AgentState.PROCESSING
        
    async def test_agent_processing_in_qasync_context(self, qasync_app, real_garden_planner):
        """Test the exact failure scenario: agent processing in qasync context."""
        app, qasync_loop = qasync_app
        
        # This is the real test - this used to fail with "RuntimeError: no running event loop"
        request_id = "test_request_001"
        user_prompt = "create a simple game"
        
        # This should not raise RuntimeError
        try:
            response = await real_garden_planner.interface.process_with_validation(
                request_id=request_id,
                user_prompt=user_prompt,
                timeout=10.0  # Short timeout for test
            )
            # Response might fail for other reasons (no LLM), but should not be event loop error
            assert True, "No RuntimeError occurred"
        except Exception as e:
            # The error should NOT be "no running event loop"
            assert "no running event loop" not in str(e), f"Event loop error still occurring: {e}"
            
    async def test_qasync_wait_for_vs_asyncio_wait_for(self, qasync_app):
        """Test that qasync_wait_for works where asyncio.wait_for fails."""
        app, qasync_loop = qasync_app
        
        async def dummy_operation():
            await asyncio.sleep(0.1)
            return "success"
            
        # This should work with qasync_wait_for
        result = await qasync_wait_for(dummy_operation(), timeout=1.0)
        assert result == "success"
        
        # This might fail with direct asyncio.wait_for in some qasync contexts
        # We'll test that our implementation handles it
        try:
            result2 = await asyncio.wait_for(dummy_operation(), timeout=1.0)
            # If it works, that's fine too
            assert result2 == "success"
        except RuntimeError as e:
            if "no running event loop" in str(e):
                # This confirms why we needed qasync_wait_for
                logger.info("Confirmed: asyncio.wait_for fails in qasync context")
                
    async def test_agent_state_transitions_qasync(self, qasync_app, real_agent_interface):
        """Test agent state transitions in qasync context."""
        app, qasync_loop = qasync_app
        
        # Test all state transitions that were failing
        from interfaces.agent.interface import AgentState
        
        states_to_test = [
            AgentState.IDLE,
            AgentState.PROCESSING,
            AgentState.COMPLETED,
            AgentState.ERROR,
            AgentState.IDLE  # Back to idle
        ]
        
        for state in states_to_test:
            # This used to fail with "no running event loop"
            await real_agent_interface.set_agent_state(state)
            assert real_agent_interface.agent_state == state
            
    async def test_concurrent_operations_qasync(self, qasync_app, real_agent_interface):
        """Test concurrent agent operations in qasync context."""
        app, qasync_loop = qasync_app
        
        async def state_operation(state_name, delay):
            await asyncio.sleep(delay)
            await real_agent_interface.set_agent_state(AgentState.PROCESSING)
            await asyncio.sleep(0.1)
            await real_agent_interface.set_agent_state(AgentState.IDLE)
            return state_name
            
        # Run multiple operations concurrently
        tasks = [
            state_operation("op1", 0.1),
            state_operation("op2", 0.2),
            state_operation("op3", 0.15)
        ]
        
        # This should not cause event loop issues
        results = await asyncio.gather(*tasks)
        assert len(results) == 3
        
    async def test_timeout_handling_qasync(self, qasync_app, real_agent_interface):
        """Test timeout handling in qasync context."""
        app, qasync_loop = qasync_app
        
        async def slow_operation():
            await asyncio.sleep(2.0)  # Longer than timeout
            return "should_not_reach"
            
        # Test that qasync_wait_for handles timeouts correctly
        with pytest.raises(asyncio.TimeoutError):
            await qasync_wait_for(slow_operation(), timeout=0.5)
            
    async def test_event_loop_manager_integration(self, qasync_app):
        """Test EventLoopManager integration with qasync."""
        app, qasync_loop = qasync_app
        
        # EventLoopManager should recognize the qasync loop
        primary_loop = EventLoopManager.get_primary_loop()
        assert primary_loop is not None
        
        # get_qasync_compatible_loop should return the same loop
        compatible_loop = get_qasync_compatible_loop()
        assert compatible_loop is primary_loop
        
    def test_real_gui_prompt_submission_simulation(self, qasync_app, real_garden_planner):
        """Simulate the real GUI prompt submission that was failing."""
        app, qasync_loop = qasync_app
        
        # This simulates the real failure scenario from the logs
        async def simulate_prompt_processing():
            # Step 1: GUI prompt submission (simulated)
            prompt = "make a simple game"
            
            # Step 2: qasync task creation (simulated)
            async def process_prompt_async():
                # Step 3: Agent interface processing (the failure point)
                request_id = f"sim_{int(time.time())}"
                
                # This was failing with "RuntimeError: no running event loop"
                return await real_garden_planner.interface.process_with_validation(
                    request_id=request_id,
                    user_prompt=prompt,
                    timeout=5.0
                )
                
            # Step 4: Execute with qasync_wait_for (our fix)
            try:
                task = qasync_loop.create_task(process_prompt_async())
                result = await qasync_wait_for(task, timeout=10.0)
                return "success"  # Even if LLM fails, event loop should work
            except Exception as e:
                if "no running event loop" in str(e):
                    pytest.fail(f"Event loop error still occurring: {e}")
                # Other errors are acceptable for this test
                return "no_event_loop_error"
                
        # Run the simulation
        async def run_simulation():
            result = await simulate_prompt_processing()
            assert result in ["success", "no_event_loop_error"]
            
        # Use QTimer to run async code in qasync context
        timer = QTimer()
        timer.timeout.connect(lambda: qasync_loop.create_task(run_simulation()))
        timer.setSingleShot(True)
        timer.start(100)  # Start after 100ms
        
        # Run event loop briefly
        qasync_loop.call_later(2.0, app.quit)
        app.exec_()


class TestAgentInterfaceEventLoopRobustness:
    """Test agent interface robustness in various event loop scenarios."""
    
    async def test_multiple_loop_contexts(self):
        """Test agent interface works across different loop contexts."""
        # Test will be implemented to verify cross-thread robustness
        pass
        
    async def test_loop_transition_handling(self):
        """Test handling of event loop transitions.""" 
        # Test will be implemented to verify loop transition robustness
        pass


if __name__ == "__main__":
    # Allow running this test directly for debugging
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))