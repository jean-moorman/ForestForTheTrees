import pytest
import pytest_asyncio
import asyncio
from unittest.mock import MagicMock, patch
from resources import EventQueue
from resources.state import StateManager
from phase_one import PhaseOneOrchestrator
from phase_zero import PhaseZeroOrchestrator

@pytest_asyncio.fixture
async def integrated_system():
    """Set up an integrated system with Phase One and Phase Zero."""
    # Create event queue
    event_queue = EventQueue()
    state_manager = StateManager(event_queue)
    # Create Phase Zero with minimal mocks
    phase_zero = PhaseZeroOrchestrator(
        event_queue=event_queue,
        state_manager=state_manager,
        health_tracker=None,
        memory_monitor=None,
        system_monitor=None
    )
    
    # Mock process_system_metrics to return valid data
    phase_zero.process_system_metrics = MagicMock(return_value={
        "monitoring_analysis": {"flag_raised": False},
        "deep_analysis": {},
        "evolution_synthesis": {}
    })
    
    # Create Phase One with Phase Zero
    phase_one = PhaseOneOrchestrator(
        event_queue=event_queue,
        phase_zero=phase_zero,
        health_tracker=None,
        memory_monitor=None,
        system_monitor=None
    )
    
    # Mock _execute_phase_one to return valid data
    phase_one._execute_phase_one = MagicMock(return_value={
        "status": "success",
        "phase_one_outputs": {
            "garden_planner": {},
            "environmental_analysis": {},
            "root_system": {},
            "tree_placement": {}
        }
    })
    
    return phase_one, phase_zero

@pytest.mark.asyncio
async def test_data_exchange_between_phases(integrated_system):
    """Test data exchange between Phase One and Phase Zero."""
    phase_one, phase_zero = integrated_system
    
    # Process a task
    result = await phase_one.process_task("Test task")
    
    # Verify Phase Zero was called
    phase_zero.process_system_metrics.assert_called_once()
    
    # Verify data was stored in state manager
    latest_version = await phase_one._state_manager.get_state("phase_data:one:latest_version")
    assert latest_version is not None
    
    # Verify we can retrieve the data using the interface
    outputs = await phase_one._data_interface.retrieve_phase_one_outputs()
    assert outputs is not None
    assert "garden_planner" in outputs
    assert "environmental_analysis" in outputs
    assert "root_system" in outputs
    assert "tree_placement" in outputs
    
    # Verify we can retrieve the feedback using the interface
    feedback = await phase_one._data_interface.retrieve_latest_phase_zero_feedback()
    assert feedback is not None
    assert "monitoring_analysis" in feedback
    assert "deep_analysis" in feedback
    assert "evolution_synthesis" in feedback


@pytest.mark.asyncio
async def test_error_handling_in_phase_one(integrated_system):
    """Test error handling in Phase One when Phase Zero fails."""
    phase_one, phase_zero = integrated_system
    
    # Make Phase Zero raise an exception
    phase_zero.process_system_metrics = MagicMock(side_effect=Exception("Test exception"))
    
    # Process a task, should handle the exception gracefully
    result = await phase_one.process_task("Test task")
    
    # Should still return success because we have valid phase one outputs
    assert result["status"] == "success"
    
    # Should include an error in feedback_analysis
    assert "feedback_analysis" in result
    assert "error" in result["feedback_analysis"]

@pytest.mark.asyncio
async def test_data_validation(integrated_system):
    """Test validation of data between phases."""
    phase_one, phase_zero = integrated_system
    
    # Make Phase Zero return invalid data
    phase_zero.process_system_metrics = MagicMock(return_value={
        "monitoring_analysis": {"flag_raised": False},
        # Missing required keys
    })
    
    # Create a patch to prevent error logs during test
    with patch('logging.Logger.error'):
        # Process a task
        result = await phase_one.process_task("Test task")
    
    # Should still succeed because validation error is caught
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_phase_zero_can_access_phase_one_data(integrated_system):
    """Test that Phase Zero can access Phase One data through the interface."""
    phase_one, phase_zero = integrated_system
    
    # Override the mock to actually call _process_metrics_internal
    original_process = phase_zero._process_metrics_internal
    
    # Replace with our test function that checks data access
    async def test_process(metrics, process_id):
        try:
            # Try to retrieve Phase One outputs
            outputs = await phase_zero._data_interface.retrieve_phase_one_outputs()
            assert outputs is not None
            assert "garden_planner" in outputs
            return {
                "monitoring_analysis": {"flag_raised": False, "data_access": "success"},
                "deep_analysis": {},
                "evolution_synthesis": {}
            }
        except Exception as e:
            return {
                "monitoring_analysis": {"flag_raised": True, "error": str(e)},
                "deep_analysis": {},
                "evolution_synthesis": {}
            }
    
    # Replace the mock
    phase_zero._process_metrics_internal = test_process
    phase_zero.process_system_metrics = lambda metrics: phase_zero._process_metrics_internal(metrics, "test")
    
    # First store some Phase One outputs
    await phase_one._data_interface.store_phase_one_outputs({
        "garden_planner": {"test": "data"},
        "environmental_analysis": {"test": "data"},
        "root_system": {"test": "data"},
        "tree_placement": {"test": "data"}
    })
    
    # Process a task
    result = await phase_one.process_task("Test task")
    
    # Verify that Phase Zero was able to access the data
    assert "feedback_analysis" in result
    assert result["feedback_analysis"]["monitoring_analysis"]["data_access"] == "success"
    
    # Restore original method
    phase_zero._process_metrics_internal = original_process

def run_test_case(test_function):
    """Run a single test case with proper async handling."""
    import sys
    
    # Set up asyncio policy for Windows if needed
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Create and run event loop
    loop = asyncio.get_event_loop()
    
    try:
        # Run the test function
        loop.run_until_complete(test_function())
        print(f"✅ Test passed: {test_function.__name__}")
        return True
    except Exception as e:
        print(f"❌ Test failed: {test_function.__name__}")
        print(f"  Error: {str(e)}")
        return False
    finally:
        # Clean up
        loop.close()

def main():
    """Run all integration tests."""
    import sys
    
    # Set up asyncio policy for Windows if needed
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Add configuration for pytest-asyncio
    pytest.main(["-xvs", "--asyncio-mode=strict", __file__])
    # # Run the tests with pytest
    # pytest.main(["-xvs", __file__])

if __name__ == "__main__":
    main()