import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock

from system_error_recovery import (
    SystemErrorRecovery, 
    SystemMonitoringAgent,
    ErrorSeverity,
    HealthStatus
)
from resources.errors import ResourceExhaustionError, ResourceTimeoutError


class MockResourceExhaustionError(Exception):
    """Mock resource exhaustion error for testing."""
    
    def __init__(self, resource_id, current_usage, limit, impact_score=0.8):
        super().__init__(f"Resource {resource_id} exhausted: {current_usage}/{limit}")
        self.resource_id = resource_id
        self.current_usage = current_usage
        self.limit = limit
        self.impact_score = impact_score
        self.recovery_strategy = None
        self.operation = "resource_allocation"
        self.requires_intervention = False


class MockResourceTimeoutError(Exception):
    """Mock resource timeout error for testing."""
    
    def __init__(self, resource_id, operation, timeout_seconds=30):
        super().__init__(f"Resource {resource_id} operation {operation} timed out after {timeout_seconds}s")
        self.resource_id = resource_id
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        self.recovery_strategy = None


class TestMonitoringRecommendations:
    """Test how different error types get recommendations from the monitoring agent."""

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
        tracker = MagicMock()
        tracker.update_health = AsyncMock()
        return tracker

    @pytest.fixture
    def system_monitor(self):
        """Fixture for a mock system monitor."""
        monitor = MagicMock()
        return monitor

    @pytest.fixture
    def error_recovery(self, event_queue, health_tracker, system_monitor):
        """Fixture for the SystemErrorRecovery system."""
        recovery = SystemErrorRecovery(event_queue, health_tracker, system_monitor)
        # Avoid direct LLM calls in tests
        recovery._monitoring_agent._llm_client = AsyncMock()
        return recovery

    @pytest.mark.asyncio
    async def test_resource_exhaustion_error_gets_resource_recommendations(self, error_recovery):
        """Test that resource exhaustion errors get resource-focused recommendations."""
        # Create a resource exhaustion error
        error = MockResourceExhaustionError(
            resource_id="memory",
            current_usage=900,
            limit=800,
            impact_score=0.9
        )
        component_id = "memory_manager"
        operation = "allocate_memory"
        
        # Set up monitoring agent to provide resource-focused recommendations
        with patch.object(
            error_recovery._monitoring_agent,
            '_simulate_recovery_response',
            return_value={
                "recommended_action": "terminate_resource_heavy_processes",
                "required_components": [component_id],
                "fallback_action": "scale_up_resources",
                "decision_context": {
                    "primary_trigger": "Resource exhaustion",
                    "contributing_factors": ["High memory usage"],
                    "risk_assessment": "Critical",
                    "success_likelihood": 0.7
                }
            }
        ):
            # Set error recovery to running state
            error_recovery._running = True
            
            # Get recommendation
            recommendation = await error_recovery.get_recovery_recommendation(error, component_id, operation)
            
            # Verify recommendation is appropriate for resource exhaustion
            assert recommendation["recommended_action"] == "terminate_resource_heavy_processes"
            assert component_id in recommendation["required_components"]
            assert recommendation["fallback_action"] == "scale_up_resources"
            assert "Resource exhaustion" in recommendation["decision_context"]["primary_trigger"]

    @pytest.mark.asyncio
    async def test_timeout_error_gets_retry_recommendations(self, error_recovery):
        """Test that timeout errors get retry-focused recommendations."""
        # Create a timeout error
        error = MockResourceTimeoutError(
            resource_id="database",
            operation="query",
            timeout_seconds=60
        )
        component_id = "database_manager"
        operation = "execute_query"
        
        # Set up monitoring agent to provide retry-focused recommendations
        with patch.object(
            error_recovery._monitoring_agent,
            '_simulate_recovery_response',
            return_value={
                "recommended_action": "retry_with_backoff",
                "required_components": [component_id],
                "fallback_action": "reset_error_components",
                "decision_context": {
                    "primary_trigger": "Operation timeout",
                    "contributing_factors": ["Database overload"],
                    "risk_assessment": "Medium",
                    "success_likelihood": 0.8
                }
            }
        ):
            # Set error recovery to running state
            error_recovery._running = True
            
            # Get recommendation
            recommendation = await error_recovery.get_recovery_recommendation(error, component_id, operation)
            
            # Verify recommendation is appropriate for timeout
            assert recommendation["recommended_action"] == "retry_with_backoff"
            assert component_id in recommendation["required_components"]
            assert recommendation["fallback_action"] == "reset_error_components"
            assert "Operation timeout" in recommendation["decision_context"]["primary_trigger"]

    @pytest.mark.asyncio
    async def test_recurring_errors_get_escalated_recommendations(self, error_recovery):
        """Test that recurring errors get escalated recommendations."""
        # Create a simple error
        error = Exception("Recurring error")
        component_id = "recurring_component"
        operation = "recurring_operation"
        
        # Simulate recurring errors by setting error counts
        error_recovery._error_handler._error_counts[f"{component_id}:{operation}"] = 5
        
        # Add a recent report indicating the component is problematic
        error_recovery._monitoring_agent._recent_reports.append({
            "flag_raised": True,
            "flag_type": "COMPONENT_FAILURE",
            "affected_components": [component_id],
            "timestamp": datetime.now().isoformat()
        })
        
        # Set up monitoring agent to provide escalated recommendations
        with patch.object(
            error_recovery._monitoring_agent,
            '_simulate_recovery_response',
            return_value={
                "recommended_action": "restart_component",
                "required_components": [component_id],
                "fallback_action": "emergency_shutdown",
                "decision_context": {
                    "primary_trigger": "Recurring errors",
                    "contributing_factors": ["Component repeatedly failing"],
                    "risk_assessment": "High",
                    "success_likelihood": 0.6
                }
            }
        ):
            # Set error recovery to running state
            error_recovery._running = True
            
            # Get recommendation
            recommendation = await error_recovery.get_recovery_recommendation(error, component_id, operation)
            
            # Verify recommendation is escalated
            assert recommendation["recommended_action"] == "restart_component"
            assert component_id in recommendation["required_components"]
            assert recommendation["fallback_action"] == "emergency_shutdown"
            assert "Recurring errors" in recommendation["decision_context"]["primary_trigger"]

    @pytest.mark.asyncio
    async def test_full_error_handling_with_recommendations(self, error_recovery):
        """Test the full error handling flow with monitoring agent recommendations."""
        # Create a resource error
        error = MockResourceExhaustionError(
            resource_id="memory",
            current_usage=900,
            limit=800,
            impact_score=0.9
        )
        component_id = "memory_manager"
        operation = "allocate_memory"
        cleanup_callback = AsyncMock()
        
        # Set up monitoring agent to provide recommendations
        with patch.object(
            error_recovery._monitoring_agent,
            'get_recovery_recommendation',
            new=AsyncMock(return_value={
                "recommended_action": "terminate_resource_heavy_processes",
                "required_components": [component_id],
                "fallback_action": "scale_up_resources",
                "decision_context": {
                    "primary_trigger": "Resource exhaustion",
                    "contributing_factors": ["High memory usage"],
                    "risk_assessment": "Critical",
                    "success_likelihood": 0.7
                },
                "timestamp": datetime.now().isoformat()
            })
        ), patch.object(
            error_recovery,
            'implement_recovery_strategy',
            new=AsyncMock(return_value=True)
        ) as mock_implement:
            # Set error recovery to running state
            error_recovery._running = True
            
            # Handle the error
            classification = await error_recovery.handle_operation_error(
                error, operation, component_id, cleanup_callback
            )
            
            # Verify classification was returned
            assert classification is not None
            
            # Verify recovery strategy was set based on recommendation
            assert hasattr(error, 'recovery_strategy')
            assert error.recovery_strategy == "terminate_resource_heavy_processes"
            
            # Verify implementation was called with the recommended strategy
            mock_implement.assert_called_once()
            mock_implement.assert_called_with(error, component_id, cleanup_callback)

    @pytest.mark.asyncio
    async def test_monitoring_agent_recommends_based_on_system_state(self, error_recovery):
        """Test that recommendations change based on system state."""
        # Create a basic error
        error = Exception("Test error")
        component_id = "test_component"
        operation = "test_operation"
        
        # Simulate different system states and verify different recommendations
        
        # Case 1: Healthy system state
        error_recovery._monitoring_agent._recent_reports = []  # Clear previous reports
        error_recovery._monitoring_agent._recent_reports.append({
            "flag_raised": False,
            "flag_type": None,
            "affected_components": [],
            "metrics_snapshot": {
                "error_rate": 0.01,
                "resource_usage": 30,
                "component_health": "HEALTHY"
            },
            "timestamp": datetime.now().isoformat()
        })
        
        # Set up monitoring agent to provide a mild recommendation
        with patch.object(
            error_recovery._monitoring_agent,
            '_simulate_recovery_response',
            return_value={
                "recommended_action": "retry_with_backoff",
                "required_components": [component_id],
                "fallback_action": "reset_error_components",
                "decision_context": {
                    "primary_trigger": "Isolated error",
                    "risk_assessment": "Low",
                    "success_likelihood": 0.9,
                    "contributing_factors": ["System otherwise healthy"]
                }
            }
        ):
            # Get recommendation for healthy system
            healthy_rec = await error_recovery._monitoring_agent.get_recovery_recommendation({
                "error_type": "Exception",
                "component_id": component_id,
                "operation": operation
            })
            assert healthy_rec["recommended_action"] == "retry_with_backoff"
        
        # Case 2: System under resource pressure
        error_recovery._monitoring_agent._recent_reports = []  # Clear previous reports
        error_recovery._monitoring_agent._recent_reports.append({
            "flag_raised": True,
            "flag_type": "RESOURCE_CRITICAL",
            "affected_components": ["memory_manager"],
            "metrics_snapshot": {
                "error_rate": 0.02,
                "resource_usage": 85,
                "component_health": "DEGRADED"
            },
            "timestamp": datetime.now().isoformat()
        })
        
        # Set up monitoring agent to provide a resource-focused recommendation
        with patch.object(
            error_recovery._monitoring_agent,
            '_simulate_recovery_response',
            return_value={
                "recommended_action": "reduce_load",
                "required_components": [component_id],
                "fallback_action": "terminate_resource_heavy_processes",
                "decision_context": {
                    "primary_trigger": "Error during resource pressure",
                    "risk_assessment": "Medium",
                    "success_likelihood": 0.7,
                    "contributing_factors": ["High resource usage detected"]
                }
            }
        ):
            # Get recommendation for system under resource pressure
            resource_rec = await error_recovery._monitoring_agent.get_recovery_recommendation({
                "error_type": "Exception",
                "component_id": component_id,
                "operation": operation
            })
            assert resource_rec["recommended_action"] == "reduce_load"
        
        # Case 3: System with component failures
        error_recovery._monitoring_agent._recent_reports = []  # Clear previous reports
        error_recovery._monitoring_agent._recent_reports.append({
            "flag_raised": True,
            "flag_type": "COMPONENT_FAILURE",
            "affected_components": ["critical_component"],
            "metrics_snapshot": {
                "error_rate": 0.08,
                "resource_usage": 60,
                "component_health": "CRITICAL"
            },
            "timestamp": datetime.now().isoformat()
        })
        
        # Set up monitoring agent to provide a more aggressive recommendation
        with patch.object(
            error_recovery._monitoring_agent,
            '_simulate_recovery_response',
            return_value={
                "recommended_action": "emergency_shutdown",
                "required_components": [component_id, "critical_component"],
                "fallback_action": "manual_intervention_required",
                "decision_context": {
                    "primary_trigger": "Error during critical component failure",
                    "risk_assessment": "High",
                    "success_likelihood": 0.5,
                    "contributing_factors": ["Multiple component failures"]
                }
            }
        ):
            # Get recommendation for system with component failures
            critical_rec = await error_recovery._monitoring_agent.get_recovery_recommendation({
                "error_type": "Exception",
                "component_id": component_id,
                "operation": operation
            })
            assert critical_rec["recommended_action"] == "emergency_shutdown"
            
        # Verify each recommendation was different based on system state
        assert healthy_rec["recommended_action"] != resource_rec["recommended_action"]
        assert resource_rec["recommended_action"] != critical_rec["recommended_action"]
        assert healthy_rec["recommended_action"] != critical_rec["recommended_action"]