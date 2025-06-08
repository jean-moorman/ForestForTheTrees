"""
Test Forest Display Integration from run_phase_one.py

This module tests the integration between Phase One workflow and the forest display GUI
components. Tests PhaseOneApp communication with display components and real-time updates.
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from run_phase_one import PhaseOneApp, PhaseOneInterface
from display.core.main_window import ForestDisplay
from display.content.agent_output import AgentOutputWidget
from display.visualization.timeline import TimelineWidget
from display.monitoring.phase_metrics import PhaseMetricsWidget
from resources.events import EventQueue
from resources.state import StateManager


class MockForestDisplayComponents:
    """Mock forest display components for testing."""
    
    def __init__(self):
        self.main_window = MagicMock()
        self.agent_output_widget = MagicMock()
        self.timeline_widget = MagicMock()
        self.phase_metrics_widget = MagicMock()
        
        # Setup mock methods
        self.setup_mock_methods()
    
    def setup_mock_methods(self):
        """Setup mock methods for display components."""
        self.agent_output_widget.update_agent_output = AsyncMock()
        self.agent_output_widget.clear_output = AsyncMock()
        self.agent_output_widget.set_agent_status = AsyncMock()
        
        self.timeline_widget.add_step_event = AsyncMock()
        self.timeline_widget.update_step_status = AsyncMock()
        self.timeline_widget.mark_step_completed = AsyncMock()
        
        self.phase_metrics_widget.update_progress = AsyncMock()
        self.phase_metrics_widget.add_metric = AsyncMock()
        self.phase_metrics_widget.update_timing = AsyncMock()


@pytest.fixture
async def event_queue():
    """Create an event queue for testing."""
    queue = EventQueue()
    await queue.start()
    yield queue
    await queue.stop()


@pytest.fixture
async def state_manager(event_queue):
    """Create a state manager for testing."""
    manager = StateManager(event_queue)
    await manager.initialize()
    return manager


@pytest.fixture
def mock_orchestrator(state_manager):
    """Create a mock orchestrator for testing."""
    orchestrator = MagicMock()
    orchestrator._state_manager = state_manager
    
    # Setup agent mocks
    orchestrator.garden_planner_agent = MagicMock()
    orchestrator.earth_agent = MagicMock()
    orchestrator.environmental_analysis_agent = MagicMock()
    orchestrator.root_system_architect_agent = MagicMock()
    orchestrator.tree_placement_planner_agent = MagicMock()
    orchestrator.foundation_refinement_agent = MagicMock()
    
    # Setup async process methods
    async def mock_agent_process(*args):
        await asyncio.sleep(0.01)
        return {
            "status": "success",
            "result": "Mock agent processing completed",
            "timestamp": datetime.now().isoformat()
        }
    
    for agent in [orchestrator.garden_planner_agent, orchestrator.earth_agent,
                  orchestrator.environmental_analysis_agent, orchestrator.root_system_architect_agent,
                  orchestrator.tree_placement_planner_agent, orchestrator.foundation_refinement_agent]:
        agent.process = mock_agent_process
    
    return orchestrator


@pytest.fixture
def mock_display_components():
    """Create mock display components."""
    return MockForestDisplayComponents()


@pytest.fixture
def phase_one_interface(mock_orchestrator):
    """Create a PhaseOneInterface for testing."""
    return PhaseOneInterface(mock_orchestrator)


class TestAgentOutputIntegration:
    """Test integration with AgentOutputWidget."""
    
    @pytest.mark.asyncio
    async def test_agent_output_update_on_step_execution(self, phase_one_interface, mock_display_components):
        """Test agent output widget updates during step execution."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    app.agent_output_widget = mock_display_components.agent_output_widget
                    
                    # Start operation
                    operation_id = await phase_one_interface.start_phase_one("Test forest display integration")
                    
                    # Execute first step
                    step_result = await phase_one_interface.execute_next_step(operation_id)
                    
                    # Simulate app updating display based on step result
                    await app.agent_output_widget.update_agent_output(
                        agent_name="garden_planner",
                        output=step_result["step_result"]["result"],
                        status=step_result["step_result"]["status"]
                    )
                    
                    # Verify agent output widget was updated
                    mock_display_components.agent_output_widget.update_agent_output.assert_called_once()
                    call_args = mock_display_components.agent_output_widget.update_agent_output.call_args
                    assert call_args[1]["agent_name"] == "garden_planner"
                    assert call_args[1]["status"] == "success"
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_agent_status_indicator_updates(self, phase_one_interface, mock_display_components):
        """Test agent status indicator updates during workflow."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    app.agent_output_widget = mock_display_components.agent_output_widget
                    
                    operation_id = await phase_one_interface.start_phase_one("Test status updates")
                    
                    # Simulate setting agent status to "running"
                    await app.agent_output_widget.set_agent_status("garden_planner", "running")
                    
                    # Execute step
                    step_result = await phase_one_interface.execute_next_step(operation_id)
                    
                    # Simulate setting agent status to "completed"
                    await app.agent_output_widget.set_agent_status("garden_planner", "completed")
                    
                    # Verify status updates
                    assert mock_display_components.agent_output_widget.set_agent_status.call_count == 2
                    
                    calls = mock_display_components.agent_output_widget.set_agent_status.call_args_list
                    assert calls[0][0] == ("garden_planner", "running")
                    assert calls[1][0] == ("garden_planner", "completed")
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_agent_output_clearing_between_operations(self, phase_one_interface, mock_display_components):
        """Test agent output clearing between different operations."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    app.agent_output_widget = mock_display_components.agent_output_widget
                    
                    # First operation
                    operation_id_1 = await phase_one_interface.start_phase_one("First operation")
                    await phase_one_interface.execute_next_step(operation_id_1)
                    
                    # Clear output before second operation
                    await app.agent_output_widget.clear_output()
                    
                    # Second operation
                    operation_id_2 = await phase_one_interface.start_phase_one("Second operation")
                    await phase_one_interface.execute_next_step(operation_id_2)
                    
                    # Verify clear was called
                    mock_display_components.agent_output_widget.clear_output.assert_called_once()
                
                finally:
                    test_loop.close()


class TestTimelineIntegration:
    """Test integration with TimelineWidget."""
    
    @pytest.mark.asyncio
    async def test_timeline_step_event_tracking(self, phase_one_interface, mock_display_components):
        """Test timeline widget tracking step events."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    app.timeline_widget = mock_display_components.timeline_widget
                    
                    operation_id = await phase_one_interface.start_phase_one("Test timeline tracking")
                    
                    # Execute multiple steps and track in timeline
                    steps = ["garden_planner", "earth_agent_validation", "environmental_analysis"]
                    
                    for step_name in steps:
                        # Add step event to timeline
                        await app.timeline_widget.add_step_event(
                            operation_id=operation_id,
                            step_name=step_name,
                            event_type="step_started",
                            timestamp=datetime.now().isoformat()
                        )
                        
                        # Execute step
                        step_result = await phase_one_interface.execute_next_step(operation_id)
                        
                        # Mark step completed in timeline
                        await app.timeline_widget.mark_step_completed(
                            operation_id=operation_id,
                            step_name=step_name,
                            status=step_result["step_result"]["status"],
                            timestamp=datetime.now().isoformat()
                        )
                    
                    # Verify timeline events were tracked
                    assert mock_display_components.timeline_widget.add_step_event.call_count == 3
                    assert mock_display_components.timeline_widget.mark_step_completed.call_count == 3
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_timeline_step_status_updates(self, phase_one_interface, mock_display_components):
        """Test timeline widget step status updates."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    app.timeline_widget = mock_display_components.timeline_widget
                    
                    operation_id = await phase_one_interface.start_phase_one("Test status updates")
                    
                    # Update step status through various states
                    step_statuses = ["queued", "running", "completed"]
                    
                    for status in step_statuses:
                        await app.timeline_widget.update_step_status(
                            operation_id=operation_id,
                            step_name="garden_planner",
                            status=status,
                            timestamp=datetime.now().isoformat()
                        )
                    
                    # Verify status updates
                    assert mock_display_components.timeline_widget.update_step_status.call_count == 3
                    
                    calls = mock_display_components.timeline_widget.update_step_status.call_args_list
                    for i, expected_status in enumerate(step_statuses):
                        assert calls[i][1]["status"] == expected_status
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_timeline_parallel_operation_tracking(self, phase_one_interface, mock_display_components):
        """Test timeline tracking multiple parallel operations."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    app.timeline_widget = mock_display_components.timeline_widget
                    
                    # Start multiple operations
                    operation_ids = []
                    for i in range(3):
                        op_id = await phase_one_interface.start_phase_one(f"Parallel operation {i}")
                        operation_ids.append(op_id)
                    
                    # Track each operation in timeline
                    for i, op_id in enumerate(operation_ids):
                        await app.timeline_widget.add_step_event(
                            operation_id=op_id,
                            step_name="garden_planner",
                            event_type="step_started",
                            timestamp=datetime.now().isoformat()
                        )
                    
                    # Verify all operations tracked
                    assert mock_display_components.timeline_widget.add_step_event.call_count == 3
                    
                    # Verify unique operation IDs
                    calls = mock_display_components.timeline_widget.add_step_event.call_args_list
                    tracked_op_ids = [call[1]["operation_id"] for call in calls]
                    assert len(set(tracked_op_ids)) == 3  # All unique
                
                finally:
                    test_loop.close()


class TestPhaseMetricsIntegration:
    """Test integration with PhaseMetricsWidget."""
    
    @pytest.mark.asyncio
    async def test_progress_tracking_integration(self, phase_one_interface, mock_display_components):
        """Test progress tracking integration with metrics widget."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    app.phase_metrics_widget = mock_display_components.phase_metrics_widget
                    
                    operation_id = await phase_one_interface.start_phase_one("Test progress tracking")
                    
                    # Execute steps and update progress
                    total_steps = 6
                    for step_num in range(1, 4):  # Execute first 3 steps
                        step_result = await phase_one_interface.execute_next_step(operation_id)
                        
                        # Update progress
                        progress_percentage = (step_num / total_steps) * 100
                        await app.phase_metrics_widget.update_progress(
                            operation_id=operation_id,
                            progress_percentage=progress_percentage,
                            completed_steps=step_num,
                            total_steps=total_steps
                        )
                    
                    # Verify progress updates
                    assert mock_display_components.phase_metrics_widget.update_progress.call_count == 3
                    
                    # Check progress values
                    calls = mock_display_components.phase_metrics_widget.update_progress.call_args_list
                    expected_progress = [16.67, 33.33, 50.0]  # Approximately
                    for i, call in enumerate(calls):
                        assert abs(call[1]["progress_percentage"] - expected_progress[i]) < 1.0
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_timing_metrics_integration(self, phase_one_interface, mock_display_components):
        """Test timing metrics integration."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    app.phase_metrics_widget = mock_display_components.phase_metrics_widget
                    
                    operation_id = await phase_one_interface.start_phase_one("Test timing metrics")
                    
                    # Record step timing
                    start_time = datetime.now()
                    step_result = await phase_one_interface.execute_next_step(operation_id)
                    end_time = datetime.now()
                    
                    execution_time_ms = (end_time - start_time).total_seconds() * 1000
                    
                    # Update timing metrics
                    await app.phase_metrics_widget.update_timing(
                        operation_id=operation_id,
                        step_name="garden_planner",
                        execution_time_ms=execution_time_ms,
                        start_time=start_time.isoformat(),
                        end_time=end_time.isoformat()
                    )
                    
                    # Verify timing update
                    mock_display_components.phase_metrics_widget.update_timing.assert_called_once()
                    call_args = mock_display_components.phase_metrics_widget.update_timing.call_args
                    assert call_args[1]["step_name"] == "garden_planner"
                    assert call_args[1]["execution_time_ms"] > 0
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_custom_metrics_integration(self, phase_one_interface, mock_display_components):
        """Test custom metrics integration."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    app.phase_metrics_widget = mock_display_components.phase_metrics_widget
                    
                    operation_id = await phase_one_interface.start_phase_one("Test custom metrics")
                    
                    # Add custom metrics
                    custom_metrics = [
                        {"name": "memory_usage_mb", "value": 256.5, "unit": "MB"},
                        {"name": "cpu_utilization", "value": 45.3, "unit": "%"},
                        {"name": "network_requests", "value": 12, "unit": "count"}
                    ]
                    
                    for metric in custom_metrics:
                        await app.phase_metrics_widget.add_metric(
                            operation_id=operation_id,
                            metric_name=metric["name"],
                            metric_value=metric["value"],
                            metric_unit=metric["unit"],
                            timestamp=datetime.now().isoformat()
                        )
                    
                    # Verify custom metrics
                    assert mock_display_components.phase_metrics_widget.add_metric.call_count == 3
                    
                    calls = mock_display_components.phase_metrics_widget.add_metric.call_args_list
                    for i, call in enumerate(calls):
                        assert call[1]["metric_name"] == custom_metrics[i]["name"]
                        assert call[1]["metric_value"] == custom_metrics[i]["value"]
                
                finally:
                    test_loop.close()


class TestRealTimeDisplayUpdates:
    """Test real-time display updates during workflow execution."""
    
    @pytest.mark.asyncio
    async def test_real_time_step_progression_display(self, phase_one_interface, mock_display_components):
        """Test real-time display updates as steps progress."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    app.agent_output_widget = mock_display_components.agent_output_widget
                    app.timeline_widget = mock_display_components.timeline_widget
                    app.phase_metrics_widget = mock_display_components.phase_metrics_widget
                    
                    operation_id = await phase_one_interface.start_phase_one("Test real-time updates")
                    
                    # Simulate real-time updates for each step
                    steps = ["garden_planner", "earth_agent_validation", "environmental_analysis"]
                    
                    for i, step_name in enumerate(steps):
                        # Pre-step: Show running status
                        await app.agent_output_widget.set_agent_status(step_name, "running")
                        await app.timeline_widget.update_step_status(
                            operation_id=operation_id, step_name=step_name, 
                            status="running", timestamp=datetime.now().isoformat()
                        )
                        
                        # Execute step
                        step_result = await phase_one_interface.execute_next_step(operation_id)
                        
                        # Post-step: Update with results
                        await app.agent_output_widget.update_agent_output(
                            agent_name=step_name,
                            output=step_result["step_result"]["result"],
                            status=step_result["step_result"]["status"]
                        )
                        
                        await app.timeline_widget.mark_step_completed(
                            operation_id=operation_id, step_name=step_name,
                            status=step_result["step_result"]["status"],
                            timestamp=datetime.now().isoformat()
                        )
                        
                        await app.phase_metrics_widget.update_progress(
                            operation_id=operation_id,
                            progress_percentage=((i + 1) / len(steps)) * 100,
                            completed_steps=i + 1,
                            total_steps=len(steps)
                        )
                    
                    # Verify all components received real-time updates
                    assert mock_display_components.agent_output_widget.set_agent_status.call_count == 3
                    assert mock_display_components.agent_output_widget.update_agent_output.call_count == 3
                    assert mock_display_components.timeline_widget.update_step_status.call_count == 3
                    assert mock_display_components.timeline_widget.mark_step_completed.call_count == 3
                    assert mock_display_components.phase_metrics_widget.update_progress.call_count == 3
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_error_state_display_updates(self, phase_one_interface, mock_display_components):
        """Test display updates when steps encounter errors."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    app.agent_output_widget = mock_display_components.agent_output_widget
                    app.timeline_widget = mock_display_components.timeline_widget
                    
                    # Mock an agent to fail
                    async def failing_agent_process(*args):
                        raise Exception("Simulated agent failure")
                    
                    phase_one_interface.orchestrator.earth_agent.process = failing_agent_process
                    
                    operation_id = await phase_one_interface.start_phase_one("Test error display")
                    
                    # Execute garden planner (should succeed)
                    step1_result = await phase_one_interface.execute_next_step(operation_id)
                    await app.agent_output_widget.update_agent_output(
                        agent_name="garden_planner",
                        output=step1_result["step_result"]["result"],
                        status=step1_result["step_result"]["status"]
                    )
                    
                    # Execute earth agent (should fail)
                    step2_result = await phase_one_interface.execute_next_step(operation_id)
                    
                    # Update display with error status
                    await app.agent_output_widget.set_agent_status("earth_agent", "error")
                    await app.timeline_widget.update_step_status(
                        operation_id=operation_id,
                        step_name="earth_agent",
                        status="error",
                        timestamp=datetime.now().isoformat()
                    )
                    
                    # Verify error state updates
                    assert mock_display_components.agent_output_widget.set_agent_status.call_count >= 1
                    assert mock_display_components.timeline_widget.update_step_status.call_count >= 1
                    
                    # Check for error status in calls
                    status_calls = mock_display_components.agent_output_widget.set_agent_status.call_args_list
                    error_calls = [call for call in status_calls if call[0][1] == "error"]
                    assert len(error_calls) >= 1
                
                finally:
                    test_loop.close()


class TestDisplayComponentCommunication:
    """Test communication between different display components."""
    
    @pytest.mark.asyncio
    async def test_coordinated_display_updates(self, phase_one_interface, mock_display_components):
        """Test coordinated updates across all display components."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    app.agent_output_widget = mock_display_components.agent_output_widget
                    app.timeline_widget = mock_display_components.timeline_widget
                    app.phase_metrics_widget = mock_display_components.phase_metrics_widget
                    
                    operation_id = await phase_one_interface.start_phase_one("Test coordinated updates")
                    
                    # Single step execution should update all components
                    step_result = await phase_one_interface.execute_next_step(operation_id)
                    
                    # Simulate coordinated update
                    update_data = {
                        "operation_id": operation_id,
                        "step_name": "garden_planner",
                        "status": step_result["step_result"]["status"],
                        "result": step_result["step_result"]["result"],
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Update all components with consistent data
                    await asyncio.gather(
                        app.agent_output_widget.update_agent_output(
                            agent_name=update_data["step_name"],
                            output=update_data["result"],
                            status=update_data["status"]
                        ),
                        app.timeline_widget.add_step_event(
                            operation_id=update_data["operation_id"],
                            step_name=update_data["step_name"],
                            event_type="step_completed",
                            timestamp=update_data["timestamp"]
                        ),
                        app.phase_metrics_widget.add_metric(
                            operation_id=update_data["operation_id"],
                            metric_name="step_completion",
                            metric_value=1,
                            metric_unit="count",
                            timestamp=update_data["timestamp"]
                        )
                    )
                    
                    # Verify all components were updated
                    mock_display_components.agent_output_widget.update_agent_output.assert_called_once()
                    mock_display_components.timeline_widget.add_step_event.assert_called_once()
                    mock_display_components.phase_metrics_widget.add_metric.assert_called_once()
                    
                    # Verify consistent data across components
                    agent_call = mock_display_components.agent_output_widget.update_agent_output.call_args
                    timeline_call = mock_display_components.timeline_widget.add_step_event.call_args
                    metrics_call = mock_display_components.phase_metrics_widget.add_metric.call_args
                    
                    assert agent_call[1]["agent_name"] == timeline_call[1]["step_name"]
                    assert timeline_call[1]["operation_id"] == metrics_call[1]["operation_id"]
                
                finally:
                    test_loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])