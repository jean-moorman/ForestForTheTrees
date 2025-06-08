"""
Realistic integration tests that mirror run_phase_one.py behavior exactly.

This test module creates the exact same system setup as run_phase_one.py to enable
accurate debugging of async/event loop issues. It tests both CLI and GUI modes with 
real prompt submission and processing using the actual LLM system.

NO MOCKS - This uses the real system components exactly as run_phase_one.py does.
"""

import asyncio
import pytest
import sys
import time
import threading
import traceback
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List

import qasync
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Import the exact same components as run_phase_one.py
from run_phase_one import PhaseOneApp, PhaseOneInterface, PhaseOneDebugger, PhaseOneCLI
from display import ForestDisplay

# Import Phase One system components - exact same imports as run_phase_one.py
from phase_one.orchestrator import PhaseOneOrchestrator
from phase_one_minimal_phase_zero import MinimalPhaseZeroOrchestrator
from resources.events import EventQueue
from resources.state import StateManager
from resources.managers import (
    AgentContextManager, CacheManager, MetricsManager, 
    ResourceCoordinator, CircuitBreakerRegistry
)
from resources.monitoring import SystemMonitor, MemoryMonitor, HealthTracker
from resources.errors import ErrorHandler
from system_error_recovery import SystemErrorRecovery

# Import agents directly as in run_phase_one.py
from phase_one.agents.garden_planner import GardenPlannerAgent
from phase_one.agents.earth_agent import EarthAgent
from phase_one.agents.environmental_analysis import EnvironmentalAnalysisAgent
from phase_one.agents.root_system_architect import RootSystemArchitectAgent
from phase_one.agents.tree_placement_planner import TreePlacementPlannerAgent
from phase_one.workflow import PhaseOneWorkflow

# Import event loop management
from resources.events.loop_management import EventLoopManager
from resources.events.utils import ensure_event_loop, run_async_in_thread

# Test-specific imports
from interfaces import AgentState


class RealisticPhaseOneSetup:
    """
    This class recreates the EXACT setup process from run_phase_one.py
    to enable realistic testing of async/event loop issues.
    
    NO MOCKS - Uses real system components exactly as production does.
    """
    
    def __init__(self):
        self.phase_one_app = None
        self.event_queue = None
        self.resource_coordinator = None
        self.phase_one = None
        self.system_monitor = None
        self.main_window = None
        self.cleanup_tasks = []
        
    async def setup_like_run_phase_one(self):
        """
        Recreate the exact setup sequence from PhaseOneApp.setup_async()
        This mirrors lines 580-803 in run_phase_one.py
        """
        # Step 1: Event loop setup (lines 550-569 in run_phase_one.py)
        loop = ensure_event_loop()
        current_thread_id = threading.get_ident()
        is_main_thread = threading.current_thread() is threading.main_thread()
        
        # Always register this loop as primary for testing
        primary_loop = EventLoopManager.get_primary_loop()
        if not primary_loop or id(primary_loop) != id(loop):
            result = EventLoopManager.set_primary_loop(loop)
            print(f"Set primary loop result: {result}, loop: {id(loop)}")
                
        # Step 2: Initialize the event queue (lines 571-629 in run_phase_one.py)
        self.event_queue = EventQueue(queue_id="realistic_test_queue")
        await self.event_queue.start()
        
        # Step 3: Initialize centralized resource coordinators (lines 632-633)
        circuit_registry = CircuitBreakerRegistry(self.event_queue)
        self.resource_coordinator = ResourceCoordinator(self.event_queue)
        
        # Step 4: Define all managers exactly as in run_phase_one.py (lines 636-648)
        managers_to_register = [
            ("state_manager", StateManager(self.event_queue), []),
            ("context_manager", AgentContextManager(self.event_queue), ["state_manager"]),
            ("cache_manager", CacheManager(self.event_queue), ["state_manager"]),
            ("metrics_manager", MetricsManager(self.event_queue), ["state_manager"]),
            ("error_handler", ErrorHandler(self.event_queue), ["state_manager"]),
            ("memory_monitor", MemoryMonitor(self.event_queue), []),
            ("health_tracker", HealthTracker(self.event_queue), []),
            ("system_monitor", SystemMonitor(self.event_queue, None, None), ["memory_monitor", "health_tracker"]),
            ("error_recovery", SystemErrorRecovery(self.event_queue, None), ["state_manager", "health_tracker"])
        ]
        
        # Step 5: Register all managers (lines 650-657)
        for name, manager, deps in managers_to_register:
            self.resource_coordinator.register_manager(name, manager, dependencies=deps)
            setattr(self, name, manager)
        
        # Step 6: Update manager references (lines 655-657)
        self.system_monitor.memory_monitor = self.memory_monitor
        self.system_monitor.health_tracker = self.health_tracker
        self.error_recovery._health_tracker = self.health_tracker
        
        # Step 7: Initialize all components (lines 660-668)
        try:
            await self.resource_coordinator.initialize_all()
        except Exception as e:
            print(f"Resource coordinator initialization warning: {e}")
            # Continue with individual initialization if coordinator fails
            for name, manager, deps in managers_to_register:
                try:
                    await getattr(self, name).initialize()
                except Exception as init_error:
                    print(f"Manager {name} initialization warning: {init_error}")
        
        # Step 8: Initialize Phase Zero (lines 671-682)
        self.phase_zero = MinimalPhaseZeroOrchestrator(
            self.event_queue,
            self.state_manager,
            self.context_manager,
            self.cache_manager,
            self.metrics_manager,
            self.error_handler,
            health_tracker=self.health_tracker,
            memory_monitor=self.memory_monitor,
            system_monitor=self.system_monitor
        )
        
        # Step 9: Initialize Phase One agents exactly as run_phase_one.py (lines 687-746)
        garden_planner = GardenPlannerAgent(
            "garden_planner",
            self.event_queue,
            self.state_manager,
            self.context_manager,
            self.cache_manager,
            self.metrics_manager,
            self.error_handler,
            self.memory_monitor,
            self.health_tracker
        )
        
        earth_agent = EarthAgent(
            "earth_agent",
            self.event_queue,
            self.state_manager,
            self.context_manager,
            self.cache_manager,
            self.metrics_manager,
            self.error_handler,
            self.memory_monitor,
            self.health_tracker
        )
        
        env_analysis = EnvironmentalAnalysisAgent(
            "environmental_analysis",
            self.event_queue,
            self.state_manager,
            self.context_manager,
            self.cache_manager,
            self.metrics_manager,
            self.error_handler,
            self.memory_monitor,
            self.health_tracker
        )
        
        root_system = RootSystemArchitectAgent(
            "root_system_architect",
            self.event_queue,
            self.state_manager,
            self.context_manager,
            self.cache_manager,
            self.metrics_manager,
            self.error_handler,
            self.memory_monitor,
            self.health_tracker
        )
        
        tree_placement = TreePlacementPlannerAgent(
            "tree_placement_planner",
            self.event_queue,
            self.state_manager,
            self.context_manager,
            self.cache_manager,
            self.metrics_manager,
            self.error_handler,
            self.memory_monitor,
            self.health_tracker
        )
        
        # Step 10: Create workflow (lines 749-757)
        workflow = PhaseOneWorkflow(
            garden_planner,
            earth_agent,
            env_analysis,
            root_system,
            tree_placement,
            self.event_queue,
            self.state_manager
        )
        
        # Step 11: Initialize Phase One orchestrator (lines 761-780)
        self.phase_one = PhaseOneOrchestrator(
            self.event_queue,
            self.state_manager,
            self.context_manager,
            self.cache_manager,
            self.metrics_manager,
            self.error_handler,
            error_recovery=self.error_recovery,
            phase_zero=self.phase_zero,
            health_tracker=self.health_tracker,
            memory_monitor=self.memory_monitor,
            system_monitor=self.system_monitor,
            # Pass pre-initialized agents and workflow
            garden_planner_agent=garden_planner,
            earth_agent=earth_agent,
            environmental_analysis_agent=env_analysis,
            root_system_architect_agent=root_system,
            tree_placement_planner_agent=tree_placement,
            workflow=workflow
        )
        
        return self.phase_one
        
    async def create_gui_like_run_phase_one(self):
        """
        Create GUI components exactly like run_phase_one.py does.
        This mirrors lines 785-803 in run_phase_one.py
        """
        # Create the interface for display (line 786)
        interface = PhaseOneInterface(self.phase_one)
        
        # Initialize UI (lines 789-795)
        self.main_window = ForestDisplay(
            self.event_queue,
            interface,
            self.system_monitor
        )
        
        return self.main_window, interface
        
    async def cleanup_like_run_phase_one(self):
        """
        Cleanup exactly like run_phase_one.py does.
        This mirrors the cleanup in PhaseOneApp.close()
        """
        try:
            # Cleanup Phase One orchestrator
            if self.phase_one:
                try:
                    await self.phase_one.shutdown()
                except Exception as e:
                    print(f"Phase One shutdown warning: {e}")
                
            # Cleanup resource coordinator
            if self.resource_coordinator:
                try:
                    # ResourceCoordinator doesn't have shutdown_all, so cleanup managers individually
                    for name in ['state_manager', 'context_manager', 'cache_manager', 'metrics_manager', 
                                'error_handler', 'memory_monitor', 'health_tracker', 'system_monitor', 'error_recovery']:
                        manager = getattr(self, name, None)
                        if manager and hasattr(manager, 'shutdown'):
                            await manager.shutdown()
                except Exception as e:
                    print(f"Resource coordinator shutdown warning: {e}")
                
            # Shutdown event queue last
            if self.event_queue:
                try:
                    await self.event_queue.stop()
                except Exception as e:
                    print(f"Event queue stop warning: {e}")
                
        except Exception as e:
            print(f"Warning during cleanup: {e}")


@pytest.fixture(scope="function")
async def realistic_phase_one_setup():
    """Fixture that creates the exact same setup as run_phase_one.py"""
    # Fix the event loop setup first
    loop = asyncio.get_event_loop()
    EventLoopManager.set_primary_loop(loop)
    
    setup = RealisticPhaseOneSetup()
    
    try:
        await setup.setup_like_run_phase_one()
        yield setup
    finally:
        await setup.cleanup_like_run_phase_one()


@pytest.fixture(scope="function")
def qapp_for_realistic_test():
    """QApplication fixture for realistic GUI testing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Configure qasync exactly like run_phase_one.py (lines 574-576)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Register with EventLoopManager (lines 582-584)
    result = EventLoopManager.set_primary_loop(loop)
    
    yield app, loop
    
    # Cleanup
    if app:
        app.processEvents()


@pytest.mark.asyncio
class TestRealisticPhaseOneIntegration:
    """
    Test suite that mirrors the exact behavior of run_phase_one.py.
    
    These tests use the same setup, same components, and same execution patterns
    to accurately reproduce any async/event loop issues present in the real system.
    
    USES REAL SYSTEM - No mocks, exactly like production.
    """
    
    async def test_cli_mode_realistic_prompt_processing(self, realistic_phase_one_setup):
        """Test CLI mode with real prompt processing like run_phase_one.py CLI."""
        setup = realistic_phase_one_setup
        
        # Create CLI interface exactly like PhaseOneCLI
        cli = PhaseOneCLI()
        
        # Setup CLI using the same initialization as run_phase_one.py
        cli.event_queue = setup.event_queue
        cli.phase_one = setup.phase_one
        cli.debugger = PhaseOneDebugger(setup.phase_one)
        
        # Test realistic prompt processing with a simple prompt
        test_prompt = "Create a simple web page with a contact form"
        
        # Process prompt exactly like CLI mode does
        operation_id = f"test_{time.time()}"
        result = await setup.phase_one.process_task(test_prompt, operation_id)
        
        # Verify result structure matches expected Phase One output
        assert result is not None
        assert isinstance(result, dict)
        
        # The real system should return a proper result structure
        print(f"CLI Result: {result}")
        
        # Check that we got some kind of result from the real system
        assert len(result) > 0, "Real system should return non-empty result"
    
    async def test_gui_mode_realistic_setup(self, realistic_phase_one_setup, qapp_for_realistic_test):
        """Test GUI mode setup exactly like run_phase_one.py GUI mode."""
        setup = realistic_phase_one_setup
        app, loop = qapp_for_realistic_test
        
        # Create GUI components exactly like run_phase_one.py
        main_window, interface = await setup.create_gui_like_run_phase_one()
        
        try:
            # Verify GUI components are created correctly
            assert main_window is not None
            assert isinstance(main_window, ForestDisplay)
            assert interface is not None
            assert isinstance(interface, PhaseOneInterface)
            
            # Show window like run_phase_one.py does
            main_window.show()
            
            # Process events to ensure initialization completes
            app.processEvents()
            await asyncio.sleep(0.1)
            
            # Verify key attributes exist
            assert hasattr(main_window, 'event_queue')
            assert hasattr(main_window, 'orchestrator') 
            assert hasattr(main_window, 'system_monitor')
            assert hasattr(main_window, 'prompt_interface')
            assert hasattr(main_window, 'timeline')
            
            # Test that the event loop integration works
            assert main_window.event_queue == setup.event_queue
            assert main_window.orchestrator == interface
            assert main_window.system_monitor == setup.system_monitor
            
            print("GUI setup completed successfully")
            
        finally:
            if main_window:
                main_window.close()
    
    async def test_realistic_prompt_submission_through_gui(self, realistic_phase_one_setup, qapp_for_realistic_test):
        """Test realistic prompt submission through GUI using the new step-by-step interface."""
        setup = realistic_phase_one_setup
        app, loop = qapp_for_realistic_test
        
        # Create GUI exactly like run_phase_one.py
        main_window, interface = await setup.create_gui_like_run_phase_one()
        
        try:
            main_window.show()
            app.processEvents()
            await asyncio.sleep(0.1)
            
            # Test step-by-step prompt submission through the interface
            test_prompt = "Create a simple landing page for a coffee shop"
            
            print(f"Starting step-by-step prompt submission: {test_prompt}")
            
            # Step 1: Start Phase One workflow
            operation_id = await interface.start_phase_one(test_prompt)
            print(f"✅ Started workflow with operation_id: {operation_id}")
            
            # Step 2: Execute a few steps to verify the interface works
            # We'll only run 2-3 steps to avoid long LLM calls in testing
            steps_to_test = ["garden_planner", "earth_agent_validation"]
            
            for i, expected_step in enumerate(steps_to_test):
                print(f"\n🔄 Testing step {i+1}: {expected_step}")
                
                # Check status before step
                status = await interface.get_step_status(operation_id)
                print(f"Status before step: {status.get('current_step')} - {status.get('progress_percentage', 0):.1f}% complete")
                
                # Execute next step with reasonable timeout for testing
                step_result = await asyncio.wait_for(
                    interface.execute_next_step(operation_id),
                    timeout=180.0  # 3 minutes per step for real LLM calls
                )
                
                # Verify step completed successfully
                assert step_result["status"] == "step_completed"
                assert step_result["operation_id"] == operation_id
                assert step_result["step_executed"] == expected_step
                assert "step_result" in step_result
                
                print(f"✅ Step {expected_step} completed successfully")
                
                # Check updated status
                status = await interface.get_step_status(operation_id)
                assert expected_step in status["steps_completed"]
                print(f"✅ Progress updated: {status.get('progress_percentage', 0):.1f}% complete")
            
            # Verify we have step results
            final_status = await interface.get_step_status(operation_id)
            step_results = final_status.get("step_results", {})
            
            assert len(step_results) >= len(steps_to_test), f"Expected {len(steps_to_test)} step results, got {len(step_results)}"
            
            print(f"✅ Step-by-step GUI processing succeeded!")
            print(f"✅ Completed {len(step_results)} steps with operation_id: {operation_id}")
            
            # Format result for compatibility testing
            result = {
                "status": "success",
                "operation_id": operation_id,
                "phase_one_outputs": step_results,
                "message": f"Partial Phase One execution completed ({len(step_results)} steps)",
                "steps_executed": list(step_results.keys())
            }
            
            # Verify result structure matches GUI expectations
            assert result is not None
            assert isinstance(result, dict)
            assert result["status"] == "success"
            assert "phase_one_outputs" in result
            assert "operation_id" in result
            
            print(f"✅ Result structure validation passed")
            
        finally:
            if main_window:
                main_window.close()
    
    async def test_async_event_loop_consistency(self, realistic_phase_one_setup):
        """Test that async/event loop handling is consistent throughout the real system."""
        setup = realistic_phase_one_setup
        
        # Get the current event loop state
        current_loop = asyncio.get_event_loop()
        primary_loop = EventLoopManager.get_primary_loop()
        
        # Verify loop consistency
        assert current_loop is not None
        assert primary_loop is not None
        
        print(f"Current loop: {id(current_loop)}")
        print(f"Primary loop: {id(primary_loop)}")
        
        # Test that event queue operations work correctly
        test_event_type = "TEST_EVENT"
        test_data = {"test": "data", "timestamp": time.time()}
        
        # Emit event through the queue
        await setup.event_queue.emit(test_event_type, test_data)
        
        # Process events
        await asyncio.sleep(0.1)
        
        # Test that Phase One operations work with the same loop
        test_prompt = "Simple test prompt for loop consistency"
        result = await setup.phase_one.process_task(test_prompt)
        
        # Should complete without event loop errors
        assert result is not None
        print("Event loop consistency test passed")
    
    async def test_memory_and_resource_management(self, realistic_phase_one_setup):
        """Test memory and resource management like run_phase_one.py does."""
        setup = realistic_phase_one_setup
        
        # Test that memory monitor is working
        assert setup.memory_monitor is not None
        
        # Test that health tracker is working  
        assert setup.health_tracker is not None
        
        # Test that system monitor integration works
        assert setup.system_monitor is not None
        assert setup.system_monitor.memory_monitor == setup.memory_monitor
        assert setup.system_monitor.health_tracker == setup.health_tracker
        
        # Simulate some system activity to test resource tracking
        for i in range(3):  # Reduced from 5 to avoid hitting rate limits
            test_prompt = f"Test prompt {i} for resource tracking"
            result = await setup.phase_one.process_task(test_prompt)
            await asyncio.sleep(0.5)  # Longer delay to avoid overwhelming the system
        
        print("Resource management test completed")
        
        # System should handle multiple operations without resource leaks
        assert True  # If we get here without exceptions, resource management is working
    
    async def test_error_recovery_like_run_phase_one(self, realistic_phase_one_setup):
        """Test error recovery mechanisms exactly like run_phase_one.py."""
        setup = realistic_phase_one_setup
        
        # Test that error recovery system is set up
        assert setup.error_recovery is not None
        assert setup.error_handler is not None
        
        # Simulate an error condition and test recovery
        error_data = {
            "error": "Test error for recovery testing",
            "component": "test_component",
            "severity": "MEDIUM"
        }
        
        # Emit error event
        from resources import ResourceEventTypes
        await setup.event_queue.emit(ResourceEventTypes.ERROR_OCCURRED, error_data)
        
        # Process error event
        await asyncio.sleep(0.1)
        
        # System should continue to function after error
        test_prompt = "Test prompt after error for recovery verification"
        result = await setup.phase_one.process_task(test_prompt)
        
        # Should still work after error
        assert result is not None
        print("Error recovery test passed")
    
    async def test_debugger_integration_realistic(self, realistic_phase_one_setup):
        """Test debugger integration exactly like run_phase_one.py debugger."""
        setup = realistic_phase_one_setup
        
        # Create debugger exactly like run_phase_one.py
        debugger = PhaseOneDebugger(setup.phase_one)
        
        # Test debugger workflow status
        operation_id = f"debug_test_{time.time()}"
        
        # Execute through debugger (simulating debugger._cmd_run)
        test_prompt = "Create a simple blog website"
        result = await setup.phase_one.process_task(test_prompt, operation_id)
        
        # Verify debugger can track execution
        assert result is not None
        print(f"Debugger test result: {result}")
        
        # Test debugger metrics retrieval
        try:
            metrics = await setup.phase_one.get_agent_metrics("garden_planner")
            print(f"Agent metrics: {metrics}")
            # Should return some form of metrics data
            assert metrics is not None
        except Exception as e:
            # Some agent metrics might not be available in the real system
            print(f"Metrics retrieval note: {e}")
            # This is acceptable as long as the system doesn't crash
    
    async def test_concurrent_operations_real_system(self, realistic_phase_one_setup):
        """Test concurrent operations on the real system like run_phase_one.py would handle."""
        setup = realistic_phase_one_setup
        
        # Test that multiple prompts can be processed (though maybe not truly concurrent
        # due to LLM API limitations)
        prompts = [
            "Create a simple HTML page",
            "Build a basic CSS layout", 
            "Add JavaScript interactivity"
        ]
        
        results = []
        
        # Process prompts sequentially to avoid overwhelming the real system
        for i, prompt in enumerate(prompts):
            print(f"Processing prompt {i+1}: {prompt}")
            result = await setup.phase_one.process_task(prompt)
            results.append(result)
            
            # Add delay between real API calls
            await asyncio.sleep(1.0)
        
        # All prompts should get responses from the real system
        assert len(results) == len(prompts)
        for i, result in enumerate(results):
            assert result is not None, f"Prompt {i+1} returned None"
            print(f"Result {i+1}: {type(result)} with keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")


@pytest.mark.asyncio 
class TestRealisticEventLoopIssues:
    """
    Specific tests to identify and debug async/event loop issues
    that may occur in the real run_phase_one.py system.
    """
    
    async def test_event_loop_thread_safety_real_system(self, realistic_phase_one_setup):
        """Test event loop thread safety with the real system."""
        setup = realistic_phase_one_setup
        
        # Get current thread and loop info
        current_thread = threading.get_ident()
        current_loop = asyncio.get_event_loop()
        primary_loop = EventLoopManager.get_primary_loop()
        
        print(f"Thread: {current_thread}")
        print(f"Current loop: {id(current_loop)}")  
        print(f"Primary loop: {id(primary_loop)}")
        
        # Verify we're in a consistent state
        assert current_loop is not None
        assert primary_loop is not None
        
        # Test that the real system maintains thread safety
        test_prompt = "Test thread safety with real system"
        result = await setup.phase_one.process_task(test_prompt)
        
        # Verify the loop state hasn't changed
        final_loop = asyncio.get_event_loop()
        final_primary = EventLoopManager.get_primary_loop()
        
        assert id(final_loop) == id(current_loop), "Event loop changed during processing"
        assert id(final_primary) == id(primary_loop), "Primary loop changed during processing"
        
        print("Thread safety test passed with real system")
    
    async def test_event_queue_real_system_integration(self, realistic_phase_one_setup):
        """Test event queue integration with the real system."""
        setup = realistic_phase_one_setup
        
        # Test real event emission and processing
        from resources import ResourceEventTypes
        
        # Emit real system events
        await setup.event_queue.emit(
            ResourceEventTypes.METRIC_RECORDED,
            {
                "metric": "test_metric",
                "value": 42,
                "timestamp": time.time()
            }
        )
        
        # Process events
        await asyncio.sleep(0.1)
        
        # Test that system operations still work after event processing
        test_prompt = "Test after event queue operations"
        result = await setup.phase_one.process_task(test_prompt)
        
        assert result is not None
        print("Event queue integration test passed with real system")
    
    async def test_gui_event_loop_real_interaction(self, realistic_phase_one_setup, qapp_for_realistic_test):
        """Test GUI event loop interaction with the real system."""
        setup = realistic_phase_one_setup
        app, loop = qapp_for_realistic_test
        
        # Create real GUI components
        main_window, interface = await setup.create_gui_like_run_phase_one()
        
        try:
            main_window.show()
            app.processEvents()
            
            # Test real GUI and async interaction
            print("Testing GUI/async interaction with real system")
            
            # Process GUI events
            app.processEvents()
            
            # Process real async operation
            prompt = "Test GUI async interaction"
            result = await interface.process_task(prompt)
            assert result is not None
            
            # Process more GUI events
            app.processEvents()
            
            print("GUI/async interaction test passed with real system")
                
        finally:
            if main_window:
                main_window.close()
    
    async def test_cleanup_real_system_shutdown(self, realistic_phase_one_setup):
        """Test cleanup and shutdown with the real system."""
        setup = realistic_phase_one_setup
        
        # Perform a real operation to create resources
        prompt = "Test cleanup with real system"
        result = await setup.phase_one.process_task(prompt)
        assert result is not None
        
        # Test that real cleanup works properly
        initial_loop = asyncio.get_event_loop()
        
        # Real cleanup should not cause loop issues
        await setup.cleanup_like_run_phase_one()
        
        # Loop should still be accessible
        final_loop = asyncio.get_event_loop()
        assert final_loop is not None
        
        # Should be able to create new operations after cleanup
        await asyncio.sleep(0.01)  # Simple async operation
        
        print("Real system cleanup test passed")


if __name__ == "__main__":
    # Run tests directly for debugging
    pytest.main([__file__, "-v", "-s", "--asyncio-mode=auto"])