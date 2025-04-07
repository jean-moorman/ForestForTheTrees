import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, AsyncMock, call

from system_error_recovery import (
    SystemErrorRecovery, 
    ErrorHandler, 
    ErrorSeverity, 
    ErrorClassification,
    SystemMonitoringAgent
)


class TestSystemErrorRecovery:
    """Test suite for the SystemErrorRecovery class with monitoring agent integration."""

    @pytest.fixture
    def event_queue(self):
        """Fixture for a mock event queue."""
        queue = AsyncMock()
        queue.emit = AsyncMock()
        queue._running = True
        return queue

    @pytest.fixture
    def health_tracker(self):
        """Fixture for a mock health tracker."""
        tracker = AsyncMock()
        tracker.update_health = AsyncMock()
        return tracker

    @pytest.fixture
    def system_monitor(self):
        """Fixture for a mock system monitor."""
        monitor = MagicMock()
        monitor.health_tracker = self.health_tracker()
        return monitor

    @pytest.fixture
    def error_recovery(self, event_queue, health_tracker, system_monitor):
        """Fixture for the SystemErrorRecovery being tested."""
        recovery = SystemErrorRecovery(event_queue, health_tracker, system_monitor)
        return recovery

    @pytest.mark.asyncio
    async def test_init(self, error_recovery, event_queue, health_tracker, system_monitor):
        """Test the initialization of the error recovery system."""
        # Check that the system is properly initialized
        assert error_recovery._event_queue == event_queue
        assert error_recovery._health_tracker == health_tracker
        assert error_recovery._system_monitor == system_monitor
        assert isinstance(error_recovery._error_handler, ErrorHandler)
        assert isinstance(error_recovery._monitoring_agent, SystemMonitoringAgent)
        assert not error_recovery._running
        assert error_recovery._monitoring_task is None

    @pytest.mark.asyncio
    async def test_start_stop(self, error_recovery):
        """Test starting and stopping the error recovery system."""
        # Patch monitoring agent start/stop methods
        with patch.object(error_recovery._monitoring_agent, 'start', new=AsyncMock()) as mock_start, \
             patch.object(error_recovery._monitoring_agent, 'stop', new=AsyncMock()) as mock_stop:
            
            # Start the system
            await error_recovery.start()
            assert error_recovery._running
            mock_start.assert_called_once()
            
            # Stop the system
            await error_recovery.stop()
            assert not error_recovery._running
            mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_session_context_manager(self, error_recovery):
        """Test the start_session context manager."""
        # Patch start/stop methods
        with patch.object(error_recovery, 'start', new=AsyncMock()) as mock_start, \
             patch.object(error_recovery, 'stop', new=AsyncMock()) as mock_stop:
            
            # Use context manager
            async with error_recovery.start_session():
                mock_start.assert_called_once()
                assert not mock_stop.called
            
            # Verify stop was called after context exit
            mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recovery_recommendation(self, error_recovery):
        """Test getting recovery recommendations from monitoring agent."""
        # Create mock error
        error = Exception("Test error")
        component_id = "test_component"
        operation = "test_operation"
        
        # Create mock recommendation
        mock_recommendation = {
            "recommended_action": "restart_component",
            "required_components": [component_id],
            "fallback_action": "manual_intervention_required",
            "decision_context": {
                "primary_trigger": "Test error",
                "contributing_factors": ["Test factor"],
                "risk_assessment": "Low risk",
                "success_likelihood": 0.8
            }
        }
        
        # Patch monitoring agent get_recovery_recommendation method
        with patch.object(
            error_recovery._monitoring_agent, 
            'get_recovery_recommendation', 
            new=AsyncMock(return_value=mock_recommendation)
        ) as mock_get_recommendation:
            
            # Get recommendation
            recommendation = await error_recovery.get_recovery_recommendation(error, component_id, operation)
            
            # Verify monitoring agent method was called correctly
            mock_get_recommendation.assert_called_once()
            call_args = mock_get_recommendation.call_args[0][0]
            assert call_args["error_type"] == "Exception"
            assert call_args["error_message"] == "Test error"
            assert call_args["component_id"] == component_id
            assert call_args["operation"] == operation
            
            # Verify recommendation was returned correctly
            assert recommendation == mock_recommendation
            assert recommendation["recommended_action"] == "restart_component"
            assert recommendation["required_components"] == [component_id]

    @pytest.mark.asyncio
    async def test_handle_operation_error_with_monitoring_agent(self, error_recovery):
        """Test handling errors with monitoring agent recommendations."""
        # Create test data
        error = Exception("Test error")
        component_id = "test_component"
        operation = "test_operation"
        cleanup_callback = AsyncMock()
        
        # Create mock objects
        mock_classification = ErrorClassification(
            severity=ErrorSeverity.DEGRADED,
            error_type="test_error",
            source=component_id,
            impact_score=0.5,
            requires_intervention=False,
            recovery_strategy=None
        )
        
        mock_recommendation = {
            "recommended_action": "restart_component",
            "required_components": [component_id],
            "fallback_action": "manual_intervention_required",
            "decision_context": {
                "primary_trigger": "Test error",
                "contributing_factors": ["Test factor"],
                "risk_assessment": "Low risk",
                "success_likelihood": 0.8
            }
        }
        
        # Patch methods
        with patch.object(error_recovery._error_handler, 'handle_error', 
                          new=AsyncMock(return_value=mock_classification)) as mock_handle_error, \
             patch.object(error_recovery, 'get_recovery_recommendation',
                          new=AsyncMock(return_value=mock_recommendation)) as mock_get_recommendation, \
             patch.object(error_recovery, 'implement_recovery_strategy',
                          new=AsyncMock(return_value=True)) as mock_implement_strategy:
            
            # Set error recovery system to running state
            error_recovery._running = True
            
            # Handle the error
            result = await error_recovery.handle_operation_error(
                error, operation, component_id, cleanup_callback
            )
            
            # Verify error handler was called
            mock_handle_error.assert_called_once()
            
            # Verify recovery recommendation was requested
            mock_get_recommendation.assert_called_once()
            mock_get_recommendation.assert_called_with(error, component_id, operation)
            
            # Verify recovery strategy was set on the error
            assert hasattr(error, 'recovery_strategy')
            assert error.recovery_strategy == "restart_component"
            
            # Verify recovery strategy was implemented
            mock_implement_strategy.assert_called_once()
            mock_implement_strategy.assert_called_with(error, component_id, cleanup_callback)
            
            # Verify the result is the error classification
            assert result == mock_classification

    @pytest.mark.asyncio
    async def test_handle_operation_error_with_cleanup(self, error_recovery):
        """Test handling errors that require cleanup."""
        # Create test data
        error = Exception("Test error")
        component_id = "test_component"
        operation = "test_operation"
        cleanup_callback = AsyncMock()
        
        # Create mock classification with fatal severity
        mock_classification = ErrorClassification(
            severity=ErrorSeverity.FATAL,
            error_type="test_error",
            source=component_id,
            impact_score=0.9,
            requires_intervention=True,
            recovery_strategy=None
        )
        
        # Patch methods
        with patch.object(error_recovery._error_handler, 'handle_error', 
                          new=AsyncMock(return_value=mock_classification)) as mock_handle_error, \
             patch.object(error_recovery, 'get_recovery_recommendation',
                          new=AsyncMock(return_value=None)) as mock_get_recommendation, \
             patch.object(error_recovery, 'implement_recovery_strategy',
                          new=AsyncMock(return_value=False)) as mock_implement_strategy:
            
            # Set error recovery system to running state
            error_recovery._running = True
            
            # Handle the error
            result = await error_recovery.handle_operation_error(
                error, operation, component_id, cleanup_callback
            )
            
            # Verify cleanup was called due to fatal severity and failed recovery
            cleanup_callback.assert_called_once()
            cleanup_callback.assert_called_with(True)  # True indicates forced cleanup
            
            # Verify the result is the error classification
            assert result == mock_classification

    @pytest.mark.asyncio
    async def test_implement_recovery_strategy_standard_strategies(self, error_recovery, event_queue):
        """Test implementing standard recovery strategies."""
        # Create test data
        component_id = "test_component"
        cleanup_callback = AsyncMock()
        
        # Test each standard strategy
        for strategy in ["force_cleanup", "reduce_load", "retry_with_backoff", 
                         "restart_component", "emergency_cleanup"]:
            # Create error with strategy
            error = Exception("Test error")
            error.recovery_strategy = strategy
            error.operation = "test_operation"
            
            # Implement strategy
            result = await error_recovery.implement_recovery_strategy(error, component_id, cleanup_callback)
            
            # Verify strategy was implemented successfully
            assert result is True
            
            # Verify events were emitted
            assert event_queue.emit.called
            
            # Clear mock for next iteration
            event_queue.emit.reset_mock()
            cleanup_callback.reset_mock()

    @pytest.mark.asyncio
    async def test_implement_recovery_strategy_monitoring_agent_strategies(self, error_recovery, event_queue):
        """Test implementing strategies recommended by monitoring agent."""
        # Create test data
        component_id = "test_component"
        cleanup_callback = AsyncMock()
        
        # Test each monitoring agent strategy
        for strategy in ["scale_up_resources", "redistribute_load", "terminate_resource_heavy_processes",
                         "enable_fallback_systems", "clear_development_blockers", 
                         "reset_stalled_paths", "rollback_failed_changes"]:
            # Create error with strategy
            error = Exception("Test error")
            error.recovery_strategy = strategy
            error.operation = "test_operation"
            
            # Implement strategy
            result = await error_recovery.implement_recovery_strategy(error, component_id, cleanup_callback)
            
            # Verify strategy was implemented successfully
            assert result is True
            
            # For certain strategies, verify cleanup was called
            if strategy in ["redistribute_load", "terminate_resource_heavy_processes", "reset_stalled_paths"]:
                cleanup_callback.assert_called_once()
                
            # For other strategies, verify event was emitted
            if strategy not in ["redistribute_load", "terminate_resource_heavy_processes", "reset_stalled_paths"]:
                assert event_queue.emit.called
            
            # Clear mock for next iteration
            event_queue.emit.reset_mock()
            cleanup_callback.reset_mock()

    @pytest.mark.asyncio
    async def test_implement_recovery_strategy_unknown_strategy(self, error_recovery):
        """Test implementing an unknown recovery strategy."""
        # Create error with unknown strategy
        error = Exception("Test error")
        error.recovery_strategy = "unknown_strategy"
        component_id = "test_component"
        
        # Implement strategy
        result = await error_recovery.implement_recovery_strategy(error, component_id, None)
        
        # Verify strategy implementation failed
        assert result is False

    @pytest.mark.asyncio
    async def test_implement_recovery_strategy_error_handling(self, error_recovery):
        """Test that errors in recovery strategy implementation are handled gracefully."""
        # Create test data
        error = Exception("Test error")
        error.recovery_strategy = "force_cleanup"
        error.operation = "test_operation"
        component_id = "test_component"
        
        # Create mock cleanup callback that raises an exception
        cleanup_callback = AsyncMock(side_effect=Exception("Cleanup error"))
        
        # Patch track_recovery method to avoid errors there
        with patch.object(error_recovery._error_handler, 'track_recovery', new=AsyncMock()):
            # Implement strategy
            result = await error_recovery.implement_recovery_strategy(error, component_id, cleanup_callback)
            
            # Verify strategy implementation failed but didn't crash
            assert result is False