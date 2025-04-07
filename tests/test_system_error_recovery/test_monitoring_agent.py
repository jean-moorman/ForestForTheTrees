import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, AsyncMock

from system_error_recovery import SystemMonitoringAgent, ErrorSeverity


class TestSystemMonitoringAgent:
    """Test suite for the SystemMonitoringAgent class."""

    @pytest.fixture
    def event_queue(self):
        """Fixture for a mock event queue."""
        queue = AsyncMock()
        queue.emit = AsyncMock()
        queue._running = True
        return queue

    @pytest.fixture
    def system_monitor(self):
        """Fixture for a mock system monitor."""
        monitor = MagicMock()
        
        # Configure health tracker mock
        health_tracker = MagicMock()
        health_tracker._component_health = {
            "component1": MagicMock(
                status="HEALTHY", 
                description="Component 1 is healthy",
                timestamp=datetime.now(),
                metadata={}
            ),
            "component2": MagicMock(
                status="DEGRADED", 
                description="Component 2 is degraded",
                timestamp=datetime.now(),
                metadata={}
            )
        }
        
        health_tracker.get_system_health.return_value = MagicMock(
            status="DEGRADED",
            description="System is degraded",
            metadata={"status_counts": {"HEALTHY": 1, "DEGRADED": 1}}
        )
        
        # Configure memory monitor mock
        memory_monitor = MagicMock()
        memory_monitor._resource_sizes = {
            "resource1": 100,
            "resource2": 200
        }
        
        # Set up monitor properties
        monitor.health_tracker = health_tracker
        monitor.memory_monitor = memory_monitor
        
        return monitor

    @pytest.fixture
    def monitoring_agent(self, event_queue, system_monitor):
        """Fixture for the SystemMonitoringAgent being tested."""
        agent = SystemMonitoringAgent(event_queue, system_monitor)
        return agent

    @pytest.mark.asyncio
    async def test_init(self, monitoring_agent, event_queue, system_monitor):
        """Test the initialization of the monitoring agent."""
        # Check that the agent is properly initialized
        assert monitoring_agent._event_queue == event_queue
        assert monitoring_agent._system_monitor == system_monitor
        assert isinstance(monitoring_agent._metrics_history, dict)
        assert not monitoring_agent._running
        assert monitoring_agent._monitoring_task is None

    @pytest.mark.asyncio
    async def test_start_stop(self, monitoring_agent):
        """Test starting and stopping the monitoring agent."""
        # Start the agent
        await monitoring_agent.start()
        assert monitoring_agent._running
        assert monitoring_agent._monitoring_task is not None
        
        # Stop the agent
        await monitoring_agent.stop()
        assert not monitoring_agent._running

    @pytest.mark.asyncio
    async def test_collect_metrics(self, monitoring_agent, system_monitor):
        """Test collecting system metrics."""
        metrics = await monitoring_agent._collect_metrics()
        
        # Check that metrics were collected correctly
        assert "timestamp" in metrics
        assert "component_health" in metrics
        assert "resource_usage" in metrics
        
        # Check component health metrics
        assert "component1" in metrics["component_health"]
        assert "component2" in metrics["component_health"]
        assert metrics["component_health"]["component1"]["status"] == "HEALTHY"
        assert metrics["component_health"]["component2"]["status"] == "DEGRADED"
        
        # Check resource usage metrics
        assert "tracked_resources" in metrics["resource_usage"]
        assert metrics["resource_usage"]["tracked_resources"]["resource1"] == 100
        assert metrics["resource_usage"]["tracked_resources"]["resource2"] == 200
        assert metrics["resource_usage"]["total_tracked_mb"] == 300

    @pytest.mark.asyncio
    async def test_update_metrics_history(self, monitoring_agent):
        """Test updating metrics history."""
        # Create sample metrics
        metrics = {
            "error_rates": {"component1": 0.01},
            "resource_usage": {"total_tracked_mb": 300},
            "component_health": {"component1": {"status": "HEALTHY"}},
            "development_state": {"state": "ACTIVE"}
        }
        
        # Update history
        monitoring_agent._update_metrics_history(metrics)
        
        # Check that history was updated
        assert len(monitoring_agent._metrics_history["error_rate"]) == 1
        assert len(monitoring_agent._metrics_history["resource_usage"]) == 1
        assert len(monitoring_agent._metrics_history["component_health"]) == 1
        assert len(monitoring_agent._metrics_history["development_state"]) == 1
        
        # Check that history entry has correct structure
        assert "timestamp" in monitoring_agent._metrics_history["error_rate"][0]
        assert "data" in monitoring_agent._metrics_history["error_rate"][0]
        assert monitoring_agent._metrics_history["error_rate"][0]["data"] == {"component1": 0.01}

    @pytest.mark.asyncio
    async def test_analyze_metrics(self, monitoring_agent):
        """Test analyzing system metrics."""
        # Create sample metrics
        metrics = {
            "component_health": {
                "component1": {"status": "CRITICAL", "description": "Critical error"},
                "component2": {"status": "HEALTHY", "description": "Healthy"}
            },
            "resource_usage": {
                "total_tracked_mb": 300,
                "tracked_resources": {"resource1": 100, "resource2": 200}
            }
        }
        
        # Mock the LLM client initialization
        with patch("resources.events.get_llm_client", return_value=AsyncMock()):
            # Get analysis
            analysis = await monitoring_agent._analyze_metrics(metrics)
            
            # Check that analysis has correct structure
            assert "flag_raised" in analysis
            assert analysis["flag_raised"] is True
            assert analysis["flag_type"] == "COMPONENT_FAILURE"
            assert "component1" in analysis["affected_components"]
            assert "metrics_snapshot" in analysis
            assert "primary_triggers" in analysis
            assert "contributing_factors" in analysis
            assert "timestamp" in analysis

    @pytest.mark.asyncio
    async def test_emit_monitoring_alert(self, monitoring_agent, event_queue):
        """Test emitting a monitoring alert."""
        # Create sample report
        report = {
            "flag_raised": True,
            "flag_type": "COMPONENT_FAILURE",
            "affected_components": ["component1"],
            "metrics_snapshot": {
                "error_rate": 0.05,
                "resource_usage": 85,
                "development_state": "ACTIVE",
                "component_health": "CRITICAL"
            },
            "primary_triggers": ["Component in CRITICAL state: component1"],
            "contributing_factors": ["Multiple components showing degraded performance"]
        }
        
        # Emit alert
        await monitoring_agent._emit_monitoring_alert(report)
        
        # Check that event was emitted correctly
        event_queue.emit.assert_called_once()
        args = event_queue.emit.call_args[0]
        
        # Check event type
        assert args[0] == "monitoring_alert"
        
        # Check event data
        assert "alert_type" in args[1]
        assert args[1]["alert_type"] == "COMPONENT_FAILURE"
        assert "affected_components" in args[1]
        assert args[1]["affected_components"] == ["component1"]
        assert "description" in args[1]
        assert "metrics" in args[1]
        assert "primary_triggers" in args[1]
        assert "timestamp" in args[1]

    @pytest.mark.asyncio
    async def test_get_recovery_recommendation(self, monitoring_agent):
        """Test getting recovery recommendations."""
        # Create sample error context
        error_context = {
            "error_type": "ResourceExhaustionError",
            "error_message": "Out of memory",
            "component_id": "component1",
            "operation": "process_data",
            "severity": "FATAL",
            "timestamp": datetime.now().isoformat(),
            "stacktrace": "..."
        }
        
        # Create sample reports in recent_reports
        monitoring_agent._recent_reports.append({
            "flag_raised": True,
            "flag_type": "RESOURCE_CRITICAL",
            "affected_components": ["component1"],
            "metrics_snapshot": {
                "resource_usage": 90
            },
            "timestamp": datetime.now().isoformat()
        })
        
        # Get recommendation
        recommendation = await monitoring_agent.get_recovery_recommendation(error_context)
        
        # Check that recommendation has correct structure
        assert "recommended_action" in recommendation
        assert "required_components" in recommendation
        assert "fallback_action" in recommendation
        assert "decision_context" in recommendation
        assert "primary_trigger" in recommendation["decision_context"]
        assert "contributing_factors" in recommendation["decision_context"]
        assert "risk_assessment" in recommendation["decision_context"]
        assert "success_likelihood" in recommendation["decision_context"]
        assert "timestamp" in recommendation
        
        # Check that recommendation makes sense for the error context
        assert recommendation["recommended_action"] == "emergency_shutdown"
        assert "component1" in recommendation["required_components"]

    @pytest.mark.asyncio
    async def test_simulate_llm_response(self, monitoring_agent):
        """Test simulating LLM responses for testing."""
        # Test with critical component
        metrics_critical = {
            "component_health": {
                "component1": {"status": "CRITICAL"}
            }
        }
        response = monitoring_agent._simulate_llm_response(metrics_critical)
        assert response["flag_raised"] is True
        assert response["flag_type"] == "COMPONENT_FAILURE"
        
        # Test with high resource usage
        metrics_high_usage = {
            "resource_usage": {
                "total_tracked_mb": 1500
            }
        }
        response = monitoring_agent._simulate_llm_response(metrics_high_usage)
        assert response["flag_raised"] is True
        assert response["flag_type"] == "RESOURCE_CRITICAL"
        
        # Test with healthy system
        metrics_healthy = {
            "component_health": {
                "component1": {"status": "HEALTHY"}
            },
            "resource_usage": {
                "total_tracked_mb": 100
            }
        }
        response = monitoring_agent._simulate_llm_response(metrics_healthy)
        assert response["flag_raised"] is False

    @pytest.mark.asyncio
    async def test_validate_response(self, monitoring_agent):
        """Test validating LLM responses against JSON schema."""
        # Create sample response and schema
        response = {
            "flag_raised": True,
            "flag_type": "COMPONENT_FAILURE",
            "affected_components": ["component1"],
            "metrics_snapshot": {
                "error_rate": 0.05,
                "resource_usage": 85,
                "development_state": "ACTIVE",
                "component_health": "CRITICAL"
            },
            "primary_triggers": ["Component in CRITICAL state: component1"],
            "contributing_factors": ["Multiple components showing degraded performance"]
        }
        
        schema = {
            "required": [
                "flag_raised",
                "flag_type",
                "affected_components",
                "metrics_snapshot",
                "primary_triggers"
            ]
        }
        
        # Validate valid response
        assert monitoring_agent._validate_response(response, schema) is True
        
        # Test invalid response
        with pytest.raises(ValueError):
            monitoring_agent._validate_response({"flag_raised": True}, schema)

    def test_get_recent_reports(self, monitoring_agent):
        """Test getting recent monitoring reports."""
        # Add sample reports
        for i in range(10):
            monitoring_agent._recent_reports.append({
                "flag_raised": True,
                "flag_type": f"SAMPLE_FLAG_{i}",
                "timestamp": datetime.now().isoformat()
            })
        
        # Get recent reports with default limit
        reports = monitoring_agent.get_recent_reports()
        assert len(reports) == 5
        
        # Get recent reports with custom limit
        reports = monitoring_agent.get_recent_reports(limit=3)
        assert len(reports) == 3
        
        # Check that reports are in correct order (newest first)
        assert reports[0]["flag_type"] == "SAMPLE_FLAG_9"
        assert reports[1]["flag_type"] == "SAMPLE_FLAG_8"
        assert reports[2]["flag_type"] == "SAMPLE_FLAG_7"


@pytest.mark.asyncio
async def test_monitoring_loop_metrics_collection():
    """Test that the monitoring loop collects and analyzes metrics."""
    # Create mocks
    event_queue = AsyncMock()
    system_monitor = MagicMock()
    
    # Set up health tracker
    health_tracker = MagicMock()
    health_tracker._component_health = {
        "component1": MagicMock(
            status="HEALTHY",
            timestamp=datetime.now(),
            metadata={}
        )
    }
    health_tracker.get_system_health.return_value = MagicMock(
        status="HEALTHY",
        metadata={}
    )
    system_monitor.health_tracker = health_tracker
    
    # Set up memory monitor
    memory_monitor = MagicMock()
    memory_monitor._resource_sizes = {"resource1": 100}
    system_monitor.memory_monitor = memory_monitor
    
    # Create agent and patch sleep
    agent = SystemMonitoringAgent(event_queue, system_monitor)
    agent._check_interval = 0.1
    
    # Use context manager to ensure cleanup
    try:
        # Patch asyncio.sleep to avoid actual waiting
        with patch("asyncio.sleep", new=AsyncMock()):
            # Start the monitoring loop
            await agent.start()
            
            # Wait a moment for the loop to execute
            await asyncio.sleep(0.2)
            
            # Stop the monitoring loop
            await agent.stop()
            
            # Check that metrics were collected
            assert len(agent._metrics_history["component_health"]) > 0
            assert len(agent._metrics_history["resource_usage"]) > 0
    finally:
        # Ensure we stop the agent
        if agent._running:
            await agent.stop()


@pytest.mark.asyncio
async def test_monitoring_loop_error_handling():
    """Test that the monitoring loop handles errors gracefully."""
    # Create mocks
    event_queue = AsyncMock()
    system_monitor = MagicMock()
    
    # Create agent with mocked methods that raise exceptions
    agent = SystemMonitoringAgent(event_queue, system_monitor)
    agent._check_interval = 0.1
    agent._collect_metrics = AsyncMock(side_effect=Exception("Test error"))
    
    # Use context manager to ensure cleanup
    try:
        # Patch asyncio.sleep to avoid actual waiting
        with patch("asyncio.sleep", new=AsyncMock()):
            # Start the monitoring loop
            await agent.start()
            
            # Wait a moment for the loop to execute
            await asyncio.sleep(0.2)
            
            # Stop the monitoring loop
            await agent.stop()
            
            # Check that the loop continued despite errors
            assert agent._collect_metrics.call_count > 0
    finally:
        # Ensure we stop the agent
        if agent._running:
            await agent.stop()