import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from system_error_recovery import SystemErrorRecovery, SystemMonitoringAgent
from resources.events import EventQueue
from resources.monitoring import SystemMonitor, MemoryMonitor, HealthTracker


@pytest.fixture
def async_mock():
    """Create a preconfigured AsyncMock with common methods."""
    mock = AsyncMock()
    mock.emit = AsyncMock()
    mock._running = True
    return mock


@pytest.fixture
def mock_event_queue():
    """Fixture for a mock event queue."""
    queue = AsyncMock()
    queue.emit = AsyncMock()
    queue._running = True
    return queue


@pytest.fixture
def mock_health_tracker():
    """Fixture for a mock health tracker."""
    tracker = MagicMock()
    tracker.update_health = AsyncMock()
    return tracker


@pytest.fixture
def mock_memory_monitor():
    """Fixture for a mock memory monitor."""
    monitor = MagicMock()
    monitor._resource_sizes = {"resource1": 100, "resource2": 200}
    return monitor


@pytest.fixture
def mock_system_monitor(mock_health_tracker, mock_memory_monitor):
    """Fixture for a mock system monitor."""
    monitor = MagicMock()
    monitor.health_tracker = mock_health_tracker
    monitor.memory_monitor = mock_memory_monitor
    return monitor


@pytest.fixture
def mock_monitoring_agent(mock_event_queue, mock_system_monitor):
    """Fixture for a mock monitoring agent."""
    agent = AsyncMock()
    agent.get_recovery_recommendation = AsyncMock(return_value={
        "recommended_action": "restart_component",
        "required_components": ["test_component"],
        "fallback_action": "manual_intervention_required",
        "decision_context": {
            "primary_trigger": "Test error",
            "contributing_factors": ["Test factor"],
            "risk_assessment": "Low risk",
            "success_likelihood": 0.8
        }
    })
    return agent


@pytest.fixture
def patched_error_recovery(mock_event_queue, mock_health_tracker, mock_system_monitor, mock_monitoring_agent):
    """Fixture for an error recovery system with mocked components."""
    # Create the error recovery system
    error_recovery = SystemErrorRecovery(mock_event_queue, mock_health_tracker, mock_system_monitor)
    
    # Replace monitoring agent with mock
    error_recovery._monitoring_agent = mock_monitoring_agent
    
    return error_recovery


@pytest.fixture
async def real_event_queue():
    """Fixture for a real event queue for integration tests."""
    queue = EventQueue()
    await queue.start()
    yield queue
    await queue.stop()


@pytest.fixture
async def real_health_tracker(real_event_queue):
    """Fixture for a real health tracker for integration tests."""
    tracker = HealthTracker(real_event_queue)
    yield tracker


@pytest.fixture
async def real_memory_monitor(real_event_queue):
    """Fixture for a real memory monitor for integration tests."""
    monitor = MemoryMonitor(real_event_queue)
    yield monitor


@pytest.fixture
async def real_system_monitor(real_event_queue, real_health_tracker, real_memory_monitor):
    """Fixture for a real system monitor for integration tests."""
    # Create a real SystemMonitor but patch _monitoring_loop to avoid actual monitoring
    with patch.object(SystemMonitor, '_monitoring_loop', new=AsyncMock()):
        monitor = SystemMonitor(real_event_queue, real_memory_monitor, real_health_tracker)
        yield monitor


@pytest.fixture
async def real_error_recovery(real_event_queue, real_health_tracker, real_system_monitor):
    """Fixture for a real error recovery system for integration tests."""
    recovery = SystemErrorRecovery(real_event_queue, real_health_tracker, real_system_monitor)
    
    # Patch the LLM client to avoid actual LLM calls
    with patch.object(SystemMonitoringAgent, '_llm_client', new=AsyncMock()):
        # Start the system to allow testing
        await recovery.start()
        yield recovery
        # Clean up
        await recovery.stop()