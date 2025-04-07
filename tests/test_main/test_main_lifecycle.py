import pytest
import asyncio
import sys
import time
from datetime import datetime, timedelta
import logging

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

import qasync

# Import the modules we want to test
from main import ForestApplication
from resources.monitoring import SystemMonitor, MemoryMonitor, HealthTracker, CircuitBreaker, CircuitState
from resources import ResourceEventTypes, EventQueue

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Test timeout constants
SHORT_TIMEOUT = 0.5
NORMAL_TIMEOUT = 2.0

class TestSignals(QObject):
    """Test signals for async operations"""
    event_received = pyqtSignal(str, object)

@pytest.fixture
def qapp():
    """Fixture to create a Qt application instance"""
    app = QApplication.instance() or QApplication(sys.argv)
    yield app
    app.processEvents()

@pytest.fixture
def event_loop(qapp):
    """Fixture to create an event loop that works with Qt"""
    loop = qasync.QEventLoop(qapp)
    asyncio.set_event_loop(loop)
    yield loop
    
    # Clean up pending tasks
    pending_tasks = asyncio.all_tasks(loop)
    for task in pending_tasks:
        if not task.done():
            task.cancel()
    
    # Run loop until tasks are cancelled
    loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
    loop.close()

@pytest.fixture
async def event_queue(event_loop):
    """Create and initialize an event queue"""
    queue = EventQueue()
    await queue.start()
    yield queue
    # Stop queue after test
    await queue.stop()

@pytest.fixture
async def memory_monitor(event_queue):
    """Create a memory monitor"""
    monitor = MemoryMonitor(event_queue)
    await monitor.start()
    yield monitor
    # Cleanup
    if hasattr(monitor, 'stop'):
        await monitor.stop()

@pytest.fixture
async def health_tracker(event_queue):
    """Create a health tracker"""
    tracker = HealthTracker(event_queue)
    yield tracker
    # Cleanup
    if hasattr(tracker, 'stop'):
        await tracker.stop()

@pytest.fixture
async def system_monitor(event_queue, memory_monitor, health_tracker):
    """Create a system monitor"""
    monitor = SystemMonitor(event_queue, memory_monitor, health_tracker)
    await monitor.start()
    yield monitor
    # Cleanup
    await monitor.stop()

@pytest.mark.asyncio
class TestMonitoringSystem:
    """Tests for the monitoring system components"""

    async def test_memory_monitor_resource_tracking(self, memory_monitor):
        """Test tracking memory resources"""
        # Register a test resource
        test_resource_id = "test:resource:1"
        resource_size = 10.5  # MB
        
        await memory_monitor.register_resource(test_resource_id, resource_size)
        
        # Check that resource was registered
        assert test_resource_id in memory_monitor._resource_sizes
        assert memory_monitor._resource_sizes[test_resource_id] == resource_size
        
        # Update resource size
        new_size = 15.2  # MB
        await memory_monitor.update_resource(test_resource_id, new_size)
        
        # Check that resource size was updated
        assert memory_monitor._resource_sizes[test_resource_id] == new_size
        
        # Remove resource
        await memory_monitor.remove_resource(test_resource_id)
        
        # Check that resource was removed
        assert test_resource_id not in memory_monitor._resource_sizes

    async def test_memory_monitor_threshold_alert(self, memory_monitor, event_queue):
        """Test memory threshold alerts"""
        # Setup event receiver
        alerts_received = []
        
        async def alert_handler(event_type, data):
            if event_type == ResourceEventTypes.RESOURCE_ALERT_CREATED.value:
                alerts_received.append(data)
        
        # Subscribe to alerts
        await event_queue.subscribe(ResourceEventTypes.RESOURCE_ALERT_CREATED.value, alert_handler)
        
        # Set low thresholds to trigger alert
        memory_monitor._thresholds.total_memory_mb = 100  # Small total memory
        memory_monitor._thresholds.warning_percent = 10   # Low warning threshold
        
        # Add resources to exceed threshold
        await memory_monitor.register_resource("test:resource:1", 5)
        await memory_monitor.register_resource("test:resource:2", 7)
        
        # Trigger check
        await memory_monitor.check_thresholds()
        
        # Wait for alert processing
        await asyncio.sleep(SHORT_TIMEOUT)
        
        # Check alert
        assert len(alerts_received) >= 1
        assert alerts_received[0]["alert_type"] == "memory"
        assert alerts_received[0]["percent"] >= 10  # Should exceed our threshold

    async def test_health_tracker_status(self, health_tracker):
        """Test health status tracking"""
        # Check initial health status
        health_status = health_tracker.get_system_health()
        assert health_status.status == "HEALTHY"
        
        # Add some health metrics
        health_tracker.record_health_metric("component1", {"status": "OK", "latency": 10})
        health_tracker.record_health_metric("component2", {"status": "OK", "latency": 20})
        
        # Check health status is still good
        health_status = health_tracker.get_system_health()
        assert health_status.status == "HEALTHY"
        
        # Add a degraded component
        health_tracker.record_health_metric("component3", {"status": "DEGRADED", "latency": 500})
        
        # Check overall health is now degraded
        health_status = health_tracker.get_system_health()
        assert health_status.status == "DEGRADED"
        
        # Add a critical component
        health_tracker.record_health_metric("component4", {"status": "CRITICAL", "error": "Test error"})
        
        # Check overall health is now critical
        health_status = health_tracker.get_system_health()
        assert health_status.status == "CRITICAL"

    async def test_circuit_breaker(self, system_monitor, event_queue):
        """Test circuit breaker functionality"""
        # Create a circuit breaker
        circuit_id = "test_circuit"
        circuit = CircuitBreaker(circuit_id, event_queue)
        
        # Register with system monitor
        await system_monitor.register_circuit_breaker(circuit_id, circuit)
        
        # Check initial state
        assert circuit.state == CircuitState.CLOSED
        
        # Setup event receiver
        state_changes = []
        
        async def state_change_handler(event_type, data):
            if event_type == ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value:
                if data.get("component", "").startswith("circuit_breaker_"):
                    state_changes.append(data)
        
        # Subscribe to state changes
        await event_queue.subscribe(ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value, state_change_handler)
        
        # Record multiple failures to trip the circuit
        for i in range(circuit._failure_threshold + 1):
            await circuit.record_failure(Exception(f"Test failure {i}"))
        
        # Wait for event processing
        await asyncio.sleep(SHORT_TIMEOUT)
        
        # Check circuit is open
        assert circuit.state == CircuitState.OPEN
        
        # Check state change was emitted
        assert len(state_changes) >= 1
        assert state_changes[-1]["status"] == "OPEN"
        
        # Fast-forward time to allow recovery attempt
        # This is hacky but necessary for testing time-based transitions
        original_last_state_change = circuit.last_state_change
        circuit.last_state_change = datetime.now() - timedelta(seconds=circuit._reset_timeout + 1)
        
        # Attempt recovery (should transition to HALF_OPEN)
        await circuit.attempt_recovery()
        
        # Check circuit is half-open
        assert circuit.state == CircuitState.HALF_OPEN
        
        # Record successful operation to close circuit
        await circuit.record_success()
        
        # Check circuit is closed
        assert circuit.state == CircuitState.CLOSED

    async def test_system_monitor_integration(self, system_monitor, event_queue):
        """Test integration of system monitor components"""
        # Setup event receiver
        metrics_received = []
        
        async def metrics_handler(event_type, data):
            if event_type == ResourceEventTypes.METRIC_RECORDED.value:
                metrics_received.append(data)
        
        # Subscribe to metrics
        await event_queue.subscribe(ResourceEventTypes.METRIC_RECORDED.value, metrics_handler)
        
        # Collect system metrics
        metrics = await system_monitor.collect_system_metrics()
        
        # Check metrics structure
        assert isinstance(metrics, dict)
        assert "timestamp" in metrics
        assert "memory" in metrics
        assert "health" in metrics
        assert "circuits" in metrics
        
        # Wait for metric events
        await asyncio.sleep(NORMAL_TIMEOUT)
        
        # Check metrics were emitted
        assert len(metrics_received) > 0

@pytest.mark.asyncio
class TestLifecycleManagement:
    """Tests for application lifecycle management"""

    async def test_initialization_sequence(self, qapp, event_loop):
        """Test the application initialization sequence"""
        # Create application without initializing
        app = ForestApplication()
        
        # Check pre-initialization state
        assert not hasattr(app, 'resource_manager') or app.resource_manager is None
        assert not app._initialized
        
        # Run initialization
        await app.setup_async()
        
        # Check post-initialization state
        assert app._initialized
        assert app.resource_manager is not None
        assert app.context_manager is not None
        assert app.cache_manager is not None
        assert app.metrics_manager is not None
        assert app.error_handler is not None
        assert app.memory_monitor is not None
        assert app.health_tracker is not None
        assert app.system_monitor is not None
        assert app.phase_zero is not None
        assert app.phase_one is not None
        assert app.main_window is not None
        assert app.event_timer.isActive()
        
        # Clean up
        app.close()

    async def test_shutdown_sequence(self, qapp, event_loop):
        """Test the application shutdown sequence"""
        # Create and initialize application
        app = ForestApplication()
        await app.setup_async()
        
        # Create some test tasks and threads
        async def long_task():
            try:
                await asyncio.sleep(10)  # Long enough to be cancelled
                return "Task completed"
            except asyncio.CancelledError:
                return "Task cancelled"
                
        class TestThread(QThread):
            def run(self):
                time.sleep(10)  # Long enough to be cancelled
                
        # Register tasks and threads
        tasks = [app.register_task(long_task()) for _ in range(3)]
        threads = [app.register_thread(TestThread()) for _ in range(2)]
        
        # Start threads
        for thread in threads:
            thread.start()
        
        # Check that tasks and threads are registered
        assert len(app._tasks) == 3
        assert len(app._threads) == 2
        
        # Initiate shutdown
        app.close()
        
        # Check post-shutdown state
        assert len(app._tasks) == 0  # All tasks should be cancelled
        assert len(app._threads) == 0  # All threads should be stopped
        
        # Check that timers are stopped
        assert not app.event_timer.isActive()
        
        # Check that async helper is in shutdown state
        assert app.async_helper.shutdown_requested

    async def test_main_function(self, qapp, event_loop, monkeypatch):
        """Test the main function"""
        from main import main
        
        # Setup test state tracking
        app_created = None
        
        # Patch QMessageBox to avoid UI dialogs
        def mock_critical(*args, **kwargs):
            pass
        
        from PyQt6.QtWidgets import QMessageBox
        monkeypatch.setattr(QMessageBox, 'critical', mock_critical)
        
        # Run main function
        app_instance = await main()
        
        # Check that application was created and initialized
        assert app_instance is not None
        assert isinstance(app_instance, ForestApplication)
        assert app_instance._initialized
        
        # Clean up
        app_instance.close()

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])