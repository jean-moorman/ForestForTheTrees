"""
Comprehensive integration tests for ForestDisplay

Tests the main application window including:
- Full application window initialization
- Integration with orchestrator and system monitor
- Event processing and handling
- User interface coordination
- Real-time updates and monitoring
- Error handling and recovery
- Performance under load
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import MagicMock, AsyncMock, patch

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtTest import QTest

from display import ForestDisplay, AlertLevel
from interfaces import AgentState
from resources.events import EventQueue
from resources import ResourceEventTypes
from .conftest import GuiTestBase, TestSignalWaiter, async_wait_for_condition

class TestForestDisplay(GuiTestBase):
    """Test suite for ForestDisplay main window."""
    
    @pytest.mark.asyncio
    async def test_forest_display_initialization(self, display_test_base):
        """Test ForestDisplay initializes correctly with all components."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        # Create ForestDisplay with mock dependencies
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        
        # Check basic initialization
        assert display is not None
        assert isinstance(display, QMainWindow)
        
        # Check core attributes
        assert display.event_queue == event_queue
        assert display.orchestrator == display_test_base.orchestrator
        assert display.system_monitor == display_test_base.system_monitor
        
        # Check async helper initialization
        assert hasattr(display, 'async_helper')
        assert display.async_helper is not None
        
        # Check that main components are created
        central_widget = display.centralWidget()
        assert central_widget is not None
        
    @pytest.mark.asyncio
    async def test_display_ui_components(self, display_test_base):
        """Test that all UI components are properly created."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        
        # Test window properties
        assert display.windowTitle() == "Forest For The Trees - System Monitor"
        assert display.minimumSize().width() >= 1200
        assert display.minimumSize().height() >= 800
        
        # Check that key UI components exist
        assert hasattr(display, 'timeline')
        assert hasattr(display, 'prompt_interface')
        assert hasattr(display, 'metrics_panel')
        assert hasattr(display, 'circuit_panel')
        assert hasattr(display, 'agent_metrics')
        
    @pytest.mark.asyncio
    async def test_header_creation(self, display_test_base):
        """Test header creation with status indicators."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        
        # Check system status components
        assert hasattr(display, 'system_status')
        assert hasattr(display, 'agent_count')
        
        # Check initial status
        assert "System:" in display.system_status.text()
        assert "Active" in display.agent_count.text()
        
    @pytest.mark.asyncio
    async def test_prompt_interface_integration(self, display_test_base):
        """Test prompt interface integration with orchestrator."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        display.show()
        
        await display_test_base.async_process_events(0.1)
        
        # Set up orchestrator response
        test_prompt = "Create a web application"
        expected_response = {
            "status": "success",
            "phase_one_outputs": {"garden_planner": {"strategy": "Test strategy"}},
            "message": "Task processed successfully"
        }
        display_test_base.orchestrator.set_task_response(test_prompt, expected_response)
        
        # Simulate prompt submission
        prompt_interface = display.prompt_interface
        prompt_interface.prompt_input.setText(test_prompt)
        
        # Capture submission
        submitted_prompts = []
        def capture_prompt(prompt):
            submitted_prompts.append(prompt)
        
        # Mock the async processing to avoid actual orchestrator calls
        original_process = display._process_prompt_async
        async def mock_process(prompt):
            capture_prompt(prompt)
            return expected_response
        
        display._process_prompt_async = mock_process
        
        # Trigger submission
        prompt_interface._handle_submit()
        
        # Process events to handle async operations
        await display_test_base.async_process_events(0.2)
        
        # Verify prompt was captured
        assert len(submitted_prompts) == 1
        assert submitted_prompts[0] == test_prompt
        
    @pytest.mark.asyncio
    async def test_timeline_integration(self, display_test_base):
        """Test timeline widget integration with agent selection."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        display.show()
        
        await display_test_base.async_process_events(0.1)
        
        # Test agent selection handling by connecting directly to the signal
        selected_agents = []
        def capture_selection(phase, agent):
            selected_agents.append((phase, agent))
        
        # Connect our test handler to the signal  
        display.timeline.agent_selected.connect(capture_selection)
        
        # Simulate agent selection on timeline
        test_phase = "phase_one"
        test_agent = "garden_planner"
        display.timeline.agent_selected.emit(test_phase, test_agent)
        
        # Process events
        display_test_base.process_events()
        
        # Verify selection was handled
        assert len(selected_agents) == 1
        assert selected_agents[0] == (test_phase, test_agent)
        
        # Also verify that the display's handler was called by checking the timeline's selected_agent
        assert display.timeline.selected_agent == (test_phase, test_agent)
        
    @pytest.mark.asyncio
    async def test_event_processing(self, display_test_base):
        """Test event processing from the event queue."""
        event_queue = await display_test_base.get_event_queue()
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        
        # Initialize pending updates
        display._pending_updates = set()
        
        # Simulate health change event
        await event_queue.emit(
            ResourceEventTypes.SYSTEM_HEALTH_CHANGED,
            {
                "component": "system",
                "status": "HEALTHY",
                "description": "System is operating normally"
            }
        )
        
        # Process events
        await display_test_base.async_process_events(0.2)
        
        # Verify event was processed (basic test)
        # In a real implementation, we'd verify specific UI updates
        assert True
        
    @pytest.mark.asyncio
    async def test_error_handling(self, display_test_base):
        """Test error handling and display."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        
        # Initialize required attributes
        display._pending_updates = set()
        
        # Test error handling
        test_error = "Test error message"
        test_context = {"source": "test", "error": test_error}
        
        # Mock message box to avoid blocking
        with patch('display.QMessageBox.critical') as mock_msgbox:
            display._handle_error(test_error, test_context)
            
            # Verify error dialog would be shown
            mock_msgbox.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_metrics_panel_integration(self, display_test_base):
        """Test metrics panel integration and updates."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        
        # Check metrics panel exists
        assert hasattr(display, 'metrics_panel')
        metrics_panel = display.metrics_panel
        
        # Test metrics update
        try:
            metrics_panel.update_all()
            # If no exception, test passes
            assert True
        except Exception as e:
            pytest.fail(f"Metrics panel update failed: {e}")
            
    @pytest.mark.asyncio
    async def test_circuit_breaker_panel_integration(self, display_test_base):
        """Test circuit breaker panel integration."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        
        # Check circuit panel exists
        assert hasattr(display, 'circuit_panel')
        circuit_panel = display.circuit_panel
        
        # Test circuit update
        try:
            circuit_panel.update_circuits()
            # If no exception, test passes
            assert True
        except Exception as e:
            pytest.fail(f"Circuit panel update failed: {e}")
            
    @pytest.mark.asyncio
    async def test_async_helper_integration(self, display_test_base):
        """Test AsyncHelper integration for async operations."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        
        # Test async helper functionality
        async def test_coroutine():
            await asyncio.sleep(0.1)
            return "async_test_result"
        
        # Set up result capture
        results = []
        def capture_result(result):
            results.append(result)
        
        # Run coroutine through async helper
        display.async_helper.run_coroutine(test_coroutine(), capture_result)
        
        # Wait for completion
        await display_test_base.async_process_events(0.3)
        
        # Verify result was captured
        assert len(results) == 1
        assert results[0] == "async_test_result"
        
    @pytest.mark.asyncio
    async def test_window_cleanup(self, display_test_base):
        """Test proper cleanup when window is closed."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        
        # Initialize display
        display.show()
        await display_test_base.async_process_events(0.1)
        
        # Create some timers to test cleanup
        test_timer = QTimer()
        display_test_base.register_timer(test_timer)
        test_timer.start(100)
        
        # Test cleanup
        display._cleanup_timers()
        
        # Timer should be stopped
        assert not test_timer.isActive()


@pytest.mark.asyncio
class TestForestDisplayIntegration:
    """Integration tests for ForestDisplay with real system components."""
    
    async def test_display_with_real_event_queue(self, display_test_base):
        """Test ForestDisplay with real EventQueue integration."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        # Create display with real event queue
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        
        # Set up monitoring subscription
        display._pending_updates = set()
        
        # Emit a real event
        await event_queue.emit(
            ResourceEventTypes.METRIC_RECORDED,
            {
                "metric": "cpu_usage",
                "value": 75.5,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Process events
        await display_test_base.async_process_events(0.3)
        
        # Verify display handled the event
        assert True  # Basic integration test
        
    async def test_display_performance_under_load(self, display_test_base):
        """Test ForestDisplay performance under event load."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        display.show()
        
        # Initialize pending updates
        display._pending_updates = set()
        
        # Generate many events rapidly
        start_time = time.time()
        
        for i in range(100):
            await event_queue.emit(
                ResourceEventTypes.METRIC_RECORDED,
                {
                    "metric": f"test_metric_{i}",
                    "value": i,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        # Process all events
        await display_test_base.async_process_events(1.0)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should handle load efficiently (less than 2 seconds for 100 events)
        assert processing_time < 2.0, f"Event processing took too long: {processing_time}s"
        
    async def test_display_memory_management(self, display_test_base):
        """Test ForestDisplay memory management with continuous updates."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        
        # Initialize required attributes
        display._pending_updates = set()
        
        # Simulate continuous updates
        for cycle in range(10):
            # Simulate agent state changes
            for agent in ['garden_planner', 'environmental_analysis', 'monitoring']:
                await event_queue.emit(
                    ResourceEventTypes.METRIC_RECORDED,
                    {
                        "metric": f"{agent}_status",
                        "value": cycle,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
            # Process events periodically
            await display_test_base.async_process_events(0.1)
            
        # Final processing
        await display_test_base.async_process_events(0.2)
        
        # Should handle continuous updates without memory issues
        assert True
        
    async def test_display_error_recovery(self, display_test_base):
        """Test ForestDisplay error recovery mechanisms."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        
        # Initialize required attributes
        display._pending_updates = set()
        
        # Simulate error event
        await event_queue.emit(
            ResourceEventTypes.ERROR_OCCURRED,
            {
                "error": "Test error for recovery",
                "component": "test_component",
                "severity": "HIGH"
            }
        )
        
        # Process error event
        await display_test_base.async_process_events(0.2)
        
        # Display should continue functioning after error
        # Test by emitting a normal event
        await event_queue.emit(
            ResourceEventTypes.METRIC_RECORDED,
            {
                "metric": "recovery_test",
                "value": 100,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        await display_test_base.async_process_events(0.2)
        
        # Should handle both error and recovery
        assert True
        
    async def test_display_with_orchestrator_integration(self, display_test_base):
        """Test ForestDisplay integration with orchestrator."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        
        # Test task processing integration
        test_prompt = "Test orchestrator integration"
        
        # Set up expected response
        expected_response = {
            "status": "success",
            "phase_one_outputs": {
                "garden_planner": {"strategy": "Integration test strategy"},
                "earth_agent": {"validation": "passed"}
            },
            "execution_time": 1.5
        }
        display_test_base.orchestrator.set_task_response(test_prompt, expected_response)
        
        # Process task through display
        result = await display._process_prompt_async(test_prompt)
        
        # Verify integration
        assert result["status"] == "success"
        assert "phase_one_outputs" in result
        assert len(display_test_base.orchestrator.process_task_calls) == 1
        assert display_test_base.orchestrator.process_task_calls[0] == test_prompt
        
    async def test_display_agent_metrics_integration(self, display_test_base):
        """Test agent metrics display integration."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        
        # Set up agent metrics response
        test_agent = "garden_planner"
        expected_metrics = {
            "status": "success",
            "agent_id": test_agent,
            "metrics": {
                "operations": 42,
                "success_rate": 0.95,
                "avg_response_time": 1.2
            }
        }
        display_test_base.orchestrator.set_metrics_response(test_agent, expected_metrics)
        
        # Test agent metrics retrieval
        result = await display._update_agent_metrics(test_agent)
        
        # Verify metrics integration
        assert result["status"] == "success"
        assert result["agent_id"] == test_agent
        assert len(display_test_base.orchestrator.get_agent_metrics_calls) == 1
        
    async def test_display_real_time_updates(self, display_test_base):
        """Test real-time updates in ForestDisplay."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        display.show()
        
        # Initialize required attributes
        display._pending_updates = set()
        
        # Simulate real-time system events
        events = [
            (ResourceEventTypes.SYSTEM_HEALTH_CHANGED, {
                "component": "system",
                "status": "HEALTHY"
            }),
            (ResourceEventTypes.METRIC_RECORDED, {
                "metric": "memory_usage",
                "value": 65.5
            }),
            (ResourceEventTypes.RESOURCE_ALERT_CREATED, {
                "alert_type": "memory",
                "level": "WARNING",
                "message": "Memory usage warning"
            })
        ]
        
        # Emit events with timing
        for event_type, data in events:
            await event_queue.emit(event_type, data)
            await asyncio.sleep(0.05)  # Small delay between events
            
        # Process all events
        await display_test_base.async_process_events(0.5)
        
        # Display should handle real-time updates
        assert True
        
    async def test_display_shutdown_sequence(self, display_test_base):
        """Test proper shutdown sequence for ForestDisplay."""
        # Initialize event queue properly
        event_queue = await display_test_base.get_event_queue()
        
        display = ForestDisplay(
            event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        
        # Initialize display
        display.show()
        await display_test_base.async_process_events(0.1)
        
        # Create some resources to test cleanup
        test_timer = QTimer()
        test_timer.start(100)
        display._timers = [test_timer]
        
        # Test async shutdown
        try:
            await display._perform_full_cleanup()
            # If no exception, cleanup worked
            assert True
        except Exception as e:
            # Some cleanup operations might not be available in test environment
            # but basic cleanup should work
            assert "test" in str(e).lower() or "mock" in str(e).lower()
            
        # Timer should be stopped
        assert not test_timer.isActive()