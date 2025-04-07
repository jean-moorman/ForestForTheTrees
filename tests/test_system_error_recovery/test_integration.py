import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

from system_error_recovery import (
    SystemErrorRecovery, 
    SystemMonitoringAgent,
    ErrorSeverity,
    HealthStatus
)
from resources.events import EventQueue
from resources.monitoring import SystemMonitor, MemoryMonitor, HealthTracker


class TestSystemErrorRecoveryIntegration:
    """Integration tests for SystemErrorRecovery with SystemMonitoringAgent."""

    @pytest.fixture
    async def event_queue(self):
        """Fixture for a real event queue."""
        queue = EventQueue()
        await queue.start()
        yield queue
        await queue.stop()

    @pytest.fixture
    async def health_tracker(self, event_queue):
        """Fixture for a real health tracker."""
        tracker = HealthTracker(event_queue)
        yield tracker

    @pytest.fixture
    async def memory_monitor(self, event_queue):
        """Fixture for a memory monitor."""
        # Using real MemoryMonitor but not starting it
        monitor = MemoryMonitor(event_queue)
        yield monitor

    @pytest.fixture
    async def system_monitor(self, event_queue, health_tracker, memory_monitor):
        """Fixture for a real system monitor."""
        # Create a real SystemMonitor but patch _monitoring_loop to avoid actual monitoring
        monitor = SystemMonitor(event_queue, memory_monitor, health_tracker)
        
        # Add some health status data
        await health_tracker.update_health(
            "test_component",
            HealthStatus(
                status="HEALTHY",
                source="test_component",
                description="Component is healthy"
            )
        )
        
        yield monitor

    @pytest.fixture
    async def error_recovery(self, event_queue, health_tracker, system_monitor):
        """Fixture for the SystemErrorRecovery system."""
        recovery = SystemErrorRecovery(event_queue, health_tracker, system_monitor)
        
        # Use context manager to ensure proper start/stop
        async with recovery.start_session():
            yield recovery

    @pytest.mark.asyncio
    async def test_error_recovery_with_monitoring_recommendations(self, error_recovery, event_queue):
        """Test that error recovery uses monitoring agent recommendations."""
        # Create a test error
        class TestError(Exception):
            pass
        
        error = TestError("Test error")
        component_id = "test_component"
        operation = "test_operation"
        
        # Setup event listener to capture emitted events
        events = []
        
        async def event_listener(event_type, data):
            events.append((event_type, data))
        
        subscription = await event_queue.subscribe("resource_error_occurred", event_listener)
        subscription2 = await event_queue.subscribe("monitoring_alert", event_listener)
        
        try:
            # Create a mock cleanup callback
            cleanup_callback = AsyncMock()
            
            # Handle the error
            try:
                # Patch the agent's get_recovery_recommendation to return a specific recommendation
                with patch.object(
                    error_recovery._monitoring_agent,
                    'get_recovery_recommendation',
                    new=AsyncMock(return_value={
                        "recommended_action": "restart_component",
                        "required_components": [component_id],
                        "fallback_action": "emergency_cleanup",
                        "decision_context": {
                            "primary_trigger": "Test error",
                            "contributing_factors": ["Test factor"],
                            "risk_assessment": "Low risk",
                            "success_likelihood": 0.8
                        },
                        "timestamp": datetime.now().isoformat()
                    })
                ):
                    # Handle the error
                    classification = await error_recovery.handle_operation_error(
                        error, operation, component_id, cleanup_callback
                    )
                    
                    # Verify classification was returned
                    assert classification is not None
                    assert classification.error_type == "unknown"  # Default classification for a basic exception
                    
                    # Verify recovery strategy was set on the error
                    assert hasattr(error, 'recovery_strategy')
                    assert error.recovery_strategy == "restart_component"
                    
                    # Verify cleanup callback was called
                    await asyncio.sleep(0.1)  # Allow time for async operations
                    assert cleanup_callback.called
                    
                    # Verify appropriate events were emitted
                    await asyncio.sleep(0.1)  # Allow time for events to be processed
                    error_events = [e for e in events if e[0] == "resource_error_occurred"]
                    assert len(error_events) > 0
                    
                    # The error event should contain the component_id
                    assert error_events[0][1]["component_id"] == component_id
            except Exception as e:
                pytest.fail(f"Error handling raised an exception: {e}")
        finally:
            # Clean up subscriptions
            await event_queue.unsubscribe("resource_error_occurred", event_listener)
            await event_queue.unsubscribe("monitoring_alert", event_listener)

    @pytest.mark.asyncio
    async def test_monitoring_agent_metrics_collection(self, error_recovery, health_tracker):
        """Test that the monitoring agent collects metrics from the real system."""
        # Update health status to trigger metrics collection
        await health_tracker.update_health(
            "test_component2",
            HealthStatus(
                status="DEGRADED",
                source="test_component2",
                description="Component is degraded"
            )
        )
        
        # Allow time for monitoring agent to collect metrics
        await asyncio.sleep(0.1)
        
        # Get metrics directly from agent
        metrics = await error_recovery._monitoring_agent._collect_metrics()
        
        # Verify metrics were collected
        assert "component_health" in metrics
        assert "test_component" in metrics["component_health"]
        assert "test_component2" in metrics["component_health"]
        assert metrics["component_health"]["test_component"]["status"] == "HEALTHY"
        assert metrics["component_health"]["test_component2"]["status"] == "DEGRADED"

    @pytest.mark.asyncio
    async def test_handling_multiple_errors(self, error_recovery):
        """Test handling multiple errors in sequence."""
        # Create test errors with different severities
        class TransientError(Exception):
            pass
        
        class DegradedError(Exception):
            pass
        
        class FatalError(Exception):
            pass
        
        transient_error = TransientError("Transient error")
        degraded_error = DegradedError("Degraded error")
        fatal_error = FatalError("Fatal error")
        
        component_id = "test_component"
        operation = "test_operation"
        cleanup_callback = AsyncMock()
        
        # Patch classify_error to assign different severities based on error type
        original_classify = error_recovery._error_handler._classify_error
        
        def mock_classify_error(err, context):
            if isinstance(err, TransientError):
                classification = original_classify(err, context)
                classification.severity = ErrorSeverity.TRANSIENT
                return classification
            elif isinstance(err, DegradedError):
                classification = original_classify(err, context)
                classification.severity = ErrorSeverity.DEGRADED
                return classification
            elif isinstance(err, FatalError):
                classification = original_classify(err, context)
                classification.severity = ErrorSeverity.FATAL
                return classification
            return original_classify(err, context)
        
        # Apply the patch
        with patch.object(
            error_recovery._error_handler,
            '_classify_error',
            side_effect=mock_classify_error
        ):
            # Handle the transient error
            transient_result = await error_recovery.handle_operation_error(
                transient_error, operation, component_id, cleanup_callback
            )
            assert transient_result.severity == ErrorSeverity.TRANSIENT
            
            # Handle the degraded error
            degraded_result = await error_recovery.handle_operation_error(
                degraded_error, operation, component_id, cleanup_callback
            )
            assert degraded_result.severity == ErrorSeverity.DEGRADED
            
            # Handle the fatal error
            fatal_result = await error_recovery.handle_operation_error(
                fatal_error, operation, component_id, cleanup_callback
            )
            assert fatal_result.severity == ErrorSeverity.FATAL
            
            # Verify cleanup was called with forced=True for the fatal error
            cleanup_callback.assert_called_with(True)

    @pytest.mark.asyncio
    async def test_monitoring_agent_integration_full_cycle(self, error_recovery, event_queue, health_tracker):
        """Test a full cycle of monitoring, error handling, and recovery."""
        # Patch the _monitoring_loop to simulate metrics collection and analysis
        original_analyze = error_recovery._monitoring_agent._analyze_metrics
        
        async def mock_analyze_metrics(metrics):
            # Simulate finding a critical issue
            return {
                "flag_raised": True,
                "flag_type": "COMPONENT_FAILURE",
                "affected_components": ["test_component"],
                "metrics_snapshot": {
                    "error_rate": 0.05,
                    "resource_usage": 85,
                    "development_state": "ACTIVE",
                    "component_health": "CRITICAL"
                },
                "primary_triggers": ["Component in CRITICAL state: test_component"],
                "contributing_factors": ["Multiple components showing degraded performance"],
                "timestamp": datetime.now().isoformat()
            }
        
        # Create an error to handle
        class TestError(Exception):
            pass
        
        error = TestError("Test error")
        component_id = "test_component"
        operation = "test_operation"
        cleanup_callback = AsyncMock()
        
        # Setup event listener to capture emitted events
        events = []
        
        async def event_listener(event_type, data):
            events.append((event_type, data))
        
        subscription = await event_queue.subscribe("monitoring_alert", event_listener)
        
        try:
            # Update component health to trigger monitoring alert
            await health_tracker.update_health(
                "test_component",
                HealthStatus(
                    status="CRITICAL",
                    source="test_component",
                    description="Component is in critical state"
                )
            )
            
            # Apply the patch and trigger a metrics collection cycle
            with patch.object(
                error_recovery._monitoring_agent,
                '_analyze_metrics',
                side_effect=mock_analyze_metrics
            ):
                # Trigger a metrics collection cycle
                metrics = await error_recovery._monitoring_agent._collect_metrics()
                report = await error_recovery._monitoring_agent._analyze_metrics(metrics)
                await error_recovery._monitoring_agent._emit_monitoring_alert(report)
                
                # Allow time for events to be processed
                await asyncio.sleep(0.1)
                
                # Verify monitoring alert was emitted
                monitoring_events = [e for e in events if e[0] == "monitoring_alert"]
                assert len(monitoring_events) > 0
                assert monitoring_events[0][1]["alert_type"] == "COMPONENT_FAILURE"
                assert "test_component" in monitoring_events[0][1]["affected_components"]
                
                # Now handle an error and verify the monitoring recommendation is used
                with patch.object(
                    error_recovery._monitoring_agent,
                    'get_recovery_recommendation',
                    new=AsyncMock(return_value={
                        "recommended_action": "emergency_shutdown",
                        "required_components": [component_id],
                        "fallback_action": "manual_intervention_required",
                        "decision_context": {
                            "primary_trigger": "Critical component failure",
                            "contributing_factors": ["Recent monitoring alert for same component"],
                            "risk_assessment": "High risk",
                            "success_likelihood": 0.6
                        },
                        "timestamp": datetime.now().isoformat()
                    })
                ):
                    # Handle the error
                    classification = await error_recovery.handle_operation_error(
                        error, operation, component_id, cleanup_callback
                    )
                    
                    # Verify recovery strategy was set based on recommendation
                    assert hasattr(error, 'recovery_strategy')
                    assert error.recovery_strategy == "emergency_shutdown"
                    
                    # Verify cleanup callback was called
                    await asyncio.sleep(0.1)
                    assert cleanup_callback.called
        finally:
            # Clean up subscription
            await event_queue.unsubscribe("monitoring_alert", event_listener)