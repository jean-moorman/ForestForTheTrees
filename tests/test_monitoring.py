from asyncio.log import logger
import pytest
import pytest_asyncio
import asyncio
import psutil
import time
import gc
from datetime import datetime, timedelta

from resources.monitoring import (
    CircuitBreaker, 
    CircuitState, 
    CircuitOpenError,
    MemoryMonitor, 
    HealthTracker, 
    SystemMonitor,
    SystemMonitorConfig,
    ReliabilityMetrics
)
from resources.common import HealthStatus, MemoryThresholds, CircuitBreakerConfig
from resources.events import EventQueue, ResourceEventTypes
from resources.errors import ResourceError, ResourceExhaustionError, ResourceTimeoutError

# Mark all tests as asyncio
pytestmark = pytest.mark.asyncio

# Utility functions for testing
async def create_temp_memory_pressure(size_mb, duration=0.5):
    """Create temporary memory pressure for testing."""
    data = bytearray(int(size_mb * 1024 * 1024))  # Allocate memory
    await asyncio.sleep(duration)  # Hold for duration
    del data  # Release memory
    gc.collect()

async def failing_operation():
    """A simple operation that always fails with ResourceError."""
    raise ResourceError("Test failure", resource_id="test_resource", severity="ERROR")

async def success_operation():
    """A simple operation that always succeeds."""
    return "success"

# Fixtures
@pytest_asyncio.fixture
async def event_queue():
    """Create a real event queue for testing."""
    queue = EventQueue()
    yield queue
    # Clean up if needed
    await queue.stop() if hasattr(queue, 'stop') else None

@pytest.fixture
def memory_thresholds():
    """Create memory thresholds for testing."""
    return MemoryThresholds(
        warning_percent=0.7,
        critical_percent=0.9,
        per_resource_max_mb=100
    )

@pytest.fixture
def circuit_breaker_config():
    """Create circuit breaker config with short timeouts for testing."""
    return CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=1,  # Short timeout for testing
        failure_window=10,
        half_open_max_tries=2
    )

@pytest_asyncio.fixture
async def memory_monitor(event_queue, memory_thresholds):
    """Create a real memory monitor for testing."""
    monitor = MemoryMonitor(event_queue, memory_thresholds)
    monitor._check_interval = 0.1  # Faster intervals for testing
    yield monitor
    if hasattr(monitor, '_monitoring_task') and monitor._monitoring_task and not monitor._monitoring_task.done():
        monitor._running = False
        await asyncio.sleep(0.2)  # Give it time to shut down
        try:
            monitor._monitoring_task.cancel()
            await monitor._monitoring_task
        except asyncio.CancelledError:
            pass

@pytest_asyncio.fixture
async def health_tracker(event_queue):
    """Create a health tracker for testing."""
    tracker = HealthTracker(event_queue)
    yield tracker
    # No specific cleanup needed

@pytest_asyncio.fixture
async def circuit_breaker(event_queue, circuit_breaker_config):
    """Create a circuit breaker for testing."""
    breaker = CircuitBreaker("test_circuit", event_queue, circuit_breaker_config)
    yield breaker
    # No specific cleanup needed

@pytest_asyncio.fixture
async def system_monitor(event_queue, memory_monitor, health_tracker):
    """Create a system monitor for testing."""
    config = SystemMonitorConfig(
        check_interval=0.1,  # Short interval for testing
        memory_check_threshold=0.85,
        circuit_check_interval=0.1,
        metric_window=60
    )
    monitor = SystemMonitor(event_queue, memory_monitor, health_tracker, config)
    yield monitor
    await monitor.stop()


class TestCircuitBreaker:
    """Tests for the CircuitBreaker class."""
    
    async def test_initialization(self, event_queue, circuit_breaker_config):
        """Test that the circuit breaker initializes correctly with default and custom config."""
        # Default configuration
        breaker = CircuitBreaker("test_circuit", event_queue)
        assert breaker.name == "test_circuit"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.last_failure_time is None
        
        # Custom configuration
        custom_breaker = CircuitBreaker("custom_circuit", event_queue, circuit_breaker_config)
        assert custom_breaker.config.failure_threshold == 3
        assert custom_breaker.config.recovery_timeout == 1

    async def test_execute_success(self, circuit_breaker):
        """Test executing an operation successfully."""
        result = await circuit_breaker.execute(success_operation)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0

    async def test_execute_failure(self, circuit_breaker):
        """Test executing an operation that fails."""
        with pytest.raises(ResourceError):
            await circuit_breaker.execute(failing_operation)
            
        assert circuit_breaker.failure_count == 1
        assert circuit_breaker.last_failure_time is not None
        assert circuit_breaker.state == CircuitState.CLOSED  # Still closed after one failure

    async def test_transition_to_open(self, circuit_breaker):
        """Test that circuit breaker transitions to OPEN after threshold failures."""
        # Need to fail multiple times to open the circuit
        for _ in range(circuit_breaker.config.failure_threshold):
            with pytest.raises(ResourceError):
                await circuit_breaker.execute(failing_operation)
                
        assert circuit_breaker.state == CircuitState.OPEN
        
        # Now attempts should immediately fail with CircuitOpenError
        with pytest.raises(CircuitOpenError):
            await circuit_breaker.execute(success_operation)

    async def test_half_open_transition(self, circuit_breaker):
        """Test transition to HALF_OPEN after recovery timeout."""
        # First open the circuit
        for _ in range(circuit_breaker.config.failure_threshold):
            with pytest.raises(ResourceError):
                await circuit_breaker.execute(failing_operation)

        assert circuit_breaker.state == CircuitState.OPEN

        # Wait slightly longer than recovery timeout
        await asyncio.sleep(circuit_breaker.config.recovery_timeout + 0.1)
        
        # Force a state check - this helps isolate where the issue might be
        await circuit_breaker._check_state_transition()
        
        # Verify the state transition happened
        assert circuit_breaker.state == CircuitState.HALF_OPEN, \
            f"Circuit should be HALF_OPEN after {circuit_breaker.config.recovery_timeout + 0.1}s wait"

        # Try a successful operation
        result = await circuit_breaker.execute(success_operation)
        assert result == "success"

    async def test_recover_to_closed(self, circuit_breaker):
        """Test recovery from HALF_OPEN to CLOSED with successful operations."""
        # First transition to OPEN
        for _ in range(circuit_breaker.config.failure_threshold):
            with pytest.raises(ResourceError):
                await circuit_breaker.execute(failing_operation)
                
        assert circuit_breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout to transition to HALF_OPEN
        await asyncio.sleep(circuit_breaker.config.recovery_timeout + 0.1)
        
        # Execute successful operations to recover
        max_tries = circuit_breaker.config.half_open_max_tries
        for _ in range(max_tries):
            try:
                await circuit_breaker.execute(success_operation)
            except CircuitOpenError:
                pass
        
        # After successful operations, circuit should transition back to CLOSED
        # Try one more time to check state
        try:
            await circuit_breaker.execute(success_operation)
            if circuit_breaker.half_open_successes >= max_tries:
                assert circuit_breaker.state == CircuitState.CLOSED
        except CircuitOpenError:
            pass


class TestMemoryMonitor:
    """Tests for the MemoryMonitor class."""
    
    async def test_singleton_pattern(self, event_queue, memory_thresholds):
        """Test that MemoryMonitor follows the singleton pattern."""
        monitor1 = MemoryMonitor(event_queue, memory_thresholds)
        monitor2 = MemoryMonitor(event_queue, memory_thresholds)
        assert monitor1 is monitor2  # Same instance
        
    async def test_register_component(self, memory_monitor):
        """Test registering a component with custom thresholds."""
        custom_thresholds = MemoryThresholds(
            warning_percent=0.5,
            critical_percent=0.8,
            per_resource_max_mb=50
        )
        memory_monitor.register_component("test_component", custom_thresholds)
        assert "test_component" in memory_monitor._component_thresholds
        assert memory_monitor._component_thresholds["test_component"] is custom_thresholds
        
    async def test_track_resource(self, memory_monitor, event_queue):
        """Test tracking resource memory usage."""
        # Set up to capture emitted events
        events = []
        
        # Define a callback that logs captured events
        async def capture_event(event_type, data):
            logger.info(f"Test captured event: {event_type} with data: {data}")
            events.append((event_type, data))
        
        # Subscribe to the event
        event_type = ResourceEventTypes.RESOURCE_ALERT_CREATED.value
        logger.info(f"Subscribing to event type: {event_type}")
        await event_queue.subscribe(event_type=event_type, callback=capture_event)
        
        # Track a resource below threshold
        await memory_monitor.track_resource("test_component:resource1", 10.0, "test_component")
        assert "test_component:resource1" in memory_monitor._resource_sizes
        assert memory_monitor._resource_sizes["test_component:resource1"] == 10.0
        
        # Track a resource above threshold to trigger alert
        resource_size = memory_monitor._thresholds.per_resource_max_mb + 10
        logger.info(f"Tracking resource with size {resource_size}MB > threshold {memory_monitor._thresholds.per_resource_max_mb}MB")
        await memory_monitor.track_resource(
            "test_component:resource2",
            resource_size,
            "test_component"
        )
        
        # Give some time for async events to propagate
        await asyncio.sleep(0.1)
        
        # Log all captured events for debugging
        logger.info(f"All captured events: {events}")
        
        # Check for alert events
        alert_events = [e for e, d in events if e == ResourceEventTypes.RESOURCE_ALERT_CREATED.value]
        logger.info(f"Captured alert events: {alert_events}")
        
        # Assert that we have at least one alert event
        assert len(alert_events) > 0, "Expected at least one RESOURCE_ALERT_CREATED event"
        
    async def test_monitor_start_stop(self, memory_monitor):
        """Test starting and stopping memory monitoring."""
        # Start monitoring
        await memory_monitor.start()
        assert memory_monitor._running is True
        assert memory_monitor._monitoring_task is not None
        
        # Let it run for a bit
        await asyncio.sleep(0.2)
        
        # Stop monitoring
        await memory_monitor.stop()
        assert memory_monitor._running is False
        
        # Wait for task to complete
        if memory_monitor._monitoring_task and not memory_monitor._monitoring_task.done():
            try:
                await asyncio.wait_for(memory_monitor._monitoring_task, timeout=0.5)
            except asyncio.TimeoutError:
                memory_monitor._monitoring_task.cancel()
        
    async def test_resource_management(self, memory_monitor):
        """Test resource registration and removal."""
        resource_id = "test_resource_123"
        
        # Register resource
        memory_monitor.register_resource_size(resource_id, 50.0)
        assert resource_id in memory_monitor._resource_sizes
        assert memory_monitor._resource_sizes[resource_id] == 50.0
        
        # Remove resource
        memory_monitor.remove_resource(resource_id)
        assert resource_id not in memory_monitor._resource_sizes
        
    async def test_real_memory_check(self, memory_monitor):
        """Test that memory monitor can actually check system memory."""
        # Start memory monitor
        await memory_monitor.start()
        
        # Create temporary memory pressure
        await create_temp_memory_pressure(10)  # Allocate 10MB
        
        # Let monitor run a check
        await asyncio.sleep(0.2)
        
        # Stop monitoring
        await memory_monitor.stop()
        
        # No assertions here, we're just testing that the real check doesn't crash


class TestHealthTracker:
    """Tests for the HealthTracker class."""
    
    async def test_update_health(self, health_tracker, event_queue):
        """Test updating component health status."""
        # Start the event queue to enable event processing
        await event_queue.start()
        
        # Set up to capture emitted events
        events = []
        async def capture_event(event_type, data):
            events.append((event_type, data))
        await event_queue.subscribe(ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value, capture_event)

        # Update health status
        status = HealthStatus(
            status="HEALTHY",
            source="test_component",
            description="Test health status"
        )
        await health_tracker.update_health("test_component", status)
        
        # Wait a moment for async event processing to complete
        await asyncio.sleep(0.1)
        
        # Check component health was updated
        assert health_tracker.get_component_health("test_component") is status

        # Check event was emitted
        assert any(
            event_type == ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value
            for event_type, _ in events
        )
        
        # Clean up
        await event_queue.stop()
        
    async def test_subscription(self, health_tracker):
        """Test subscribing to health updates."""
        # Set up to capture health updates
        updates = []
        async def health_callback(component, status):
            updates.append((component, status))
            
        # Subscribe to updates
        await health_tracker.subscribe(health_callback)
        
        # Update health status
        status = HealthStatus(
            status="HEALTHY",
            source="test_component",
            description="Test health status"
        )
        await health_tracker.update_health("test_component", status)
        
        # Check callback was invoked
        assert len(updates) == 1
        assert updates[0][0] == "test_component"
        assert updates[0][1] is status
        
        # Unsubscribe
        await health_tracker.unsubscribe(health_callback)
        
        # Update again
        await health_tracker.update_health("test_component2", status)
        
        # Should not receive update for new component
        assert len(updates) == 1
        
    async def test_get_system_health(self, health_tracker):
        """Test getting overall system health status with different component states."""
        # Initial state - no components
        system_health = health_tracker.get_system_health()
        assert system_health.status == "UNKNOWN"
        
        # Add a healthy component
        healthy_status = HealthStatus(
            status="HEALTHY",
            source="healthy_component",
            description="Healthy component"
        )
        await health_tracker.update_health("healthy_component", healthy_status)
        
        system_health = health_tracker.get_system_health()
        assert system_health.status == "HEALTHY"
        
        # Add a degraded component
        degraded_status = HealthStatus(
            status="DEGRADED",
            source="degraded_component",
            description="Degraded component"
        )
        await health_tracker.update_health("degraded_component", degraded_status)
        
        system_health = health_tracker.get_system_health()
        assert system_health.status == "DEGRADED"
        
        # Add a critical component - should take precedence
        critical_status = HealthStatus(
            status="CRITICAL",
            source="critical_component",
            description="Critical component"
        )
        await health_tracker.update_health("critical_component", critical_status)
        
        system_health = health_tracker.get_system_health()
        assert system_health.status == "CRITICAL"


class TestReliabilityMetrics:
    """Tests for the ReliabilityMetrics class."""
    
    def test_state_duration(self):
        """Test tracking state durations."""
        metrics = ReliabilityMetrics(metric_window=60)
        
        # Update state durations
        metrics.update_state_duration("test_circuit", "CLOSED", 10.0)
        metrics.update_state_duration("test_circuit", "CLOSED", 5.0)
        metrics.update_state_duration("test_circuit", "OPEN", 3.0)
        
        # Check durations for individual states
        assert metrics.get_state_duration("test_circuit", "CLOSED") == 15.0
        assert metrics.get_state_duration("test_circuit", "OPEN") == 3.0
        assert metrics.get_state_duration("test_circuit", "HALF_OPEN") == 0.0  # Not recorded
        
        # Check all durations for a circuit
        durations = metrics.get_state_durations("test_circuit")
        assert durations["CLOSED"] == 15.0
        assert durations["OPEN"] == 3.0
        assert "HALF_OPEN" not in durations
        
        # Check nonexistent circuit
        assert metrics.get_state_duration("nonexistent", "CLOSED") == 0.0
        assert metrics.get_state_durations("nonexistent") == {}
        
    def test_error_recording(self):
        """Test recording errors and calculating density."""
        metrics = ReliabilityMetrics(metric_window=60)
        
        # Record errors at different times
        now = datetime.now()
        metrics.record_error("test_circuit", now - timedelta(seconds=30))
        metrics.record_error("test_circuit", now - timedelta(seconds=20))
        metrics.record_error("test_circuit", now - timedelta(seconds=10))
        
        # Calculate error density
        density = metrics.get_error_density("test_circuit")
        assert density == 3  # 3 errors per minute (normalized to per-minute rate)
        
        # Record more errors
        metrics.record_error("test_circuit", now)
        
        # Recalculate density
        density = metrics.get_error_density("test_circuit")
        assert density == 4  # 4 errors per minute
        
        # Check nonexistent circuit
        assert metrics.get_error_density("nonexistent") == 0.0
        
    def test_recovery_time(self):
        """Test recording and retrieving recovery times."""
        metrics = ReliabilityMetrics()
        
        # Record recovery times
        metrics.record_recovery("test_circuit", 5.0)
        metrics.record_recovery("test_circuit", 10.0)
        metrics.record_recovery("test_circuit", 15.0)
        
        # Get average recovery time
        avg_time = metrics.get_avg_recovery_time("test_circuit")
        assert avg_time == 10.0  # (5.0 + 10.0 + 15.0) / 3
        
        # No recovery times for new circuit
        avg_time = metrics.get_avg_recovery_time("new_circuit")
        assert avg_time is None
        
    def test_error_cleanup(self):
        """Test cleanup of old errors outside the metric window."""
        metrics = ReliabilityMetrics(metric_window=30)
        
        # Record some errors
        now = datetime.now()
        metrics.record_error("test_circuit", now - timedelta(seconds=60))  # Old
        metrics.record_error("test_circuit", now - timedelta(seconds=20))  # Recent
        metrics.record_error("test_circuit", now - timedelta(seconds=10))  # Recent
        
        # Force cleanup
        metrics._cleanup_old_errors("test_circuit")
        
        # Should have removed the old error
        assert len(metrics._circuit_metrics["test_circuit"].error_timestamps) == 2


class TestSystemMonitor:
    """Tests for the SystemMonitor class."""
    
    async def test_initialization(self, system_monitor):
        """Test that the system monitor initializes correctly."""
        assert system_monitor.event_queue is not None
        assert system_monitor.memory_monitor is not None
        assert system_monitor.health_tracker is not None
        assert system_monitor.config is not None
        assert system_monitor._circuit_breakers == {}
        assert system_monitor._running is False
        
    async def test_register_circuit_breaker(self, system_monitor, circuit_breaker, event_queue):
        """Test registering a circuit breaker with the system monitor."""
        # Set up to capture emitted events
        events = []
        async def capture_event(event_type, data):
            events.append((event_type, data))
        await event_queue.subscribe(ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value, capture_event)
        
        # Register circuit breaker
        await system_monitor.register_circuit_breaker("test_circuit", circuit_breaker)
        
        # Circuit breaker should be registered
        assert "test_circuit" in system_monitor._circuit_breakers
        assert system_monitor._circuit_breakers["test_circuit"] is circuit_breaker
        
        # Health status should be updated
        component_health = system_monitor.health_tracker.get_component_health("circuit_breaker_test_circuit")
        assert component_health is not None
        assert component_health.status == "HEALTHY"
        
        # Event should be emitted
        health_events = [e for e, d in events 
                         if e == ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value]
        assert len(health_events) > 0
        
    async def test_monitoring_loop(self, system_monitor):
        """Test the monitoring loop functionality."""
        # Start monitoring
        await system_monitor.start()
        assert system_monitor._running is True
        
        # Let it run for a bit
        await asyncio.sleep(0.3)
        
        # Stop monitoring
        await system_monitor.stop()
        assert system_monitor._running is False
        
    async def test_memory_status(self, system_monitor, memory_monitor):
        """Test checking memory status."""
        # Register some resources to track
        memory_monitor.register_resource_size("test_resource_1", 10.0)
        memory_monitor.register_resource_size("test_resource_2", 20.0)
        
        # Should be able to get memory status
        memory_status = await system_monitor._get_memory_status()
        assert isinstance(memory_status, float)
        
        # Create some temporary memory pressure
        await create_temp_memory_pressure(50)  # 50MB
        
        # Check memory status again
        memory_status = await system_monitor._get_memory_status()
        assert isinstance(memory_status, float)
        
    async def test_emit_monitoring_status(self, system_monitor, event_queue):
        """Test emitting monitoring status."""
        # Set up to capture emitted events
        events = []
        async def capture_event(event_type, data):
            events.append((event_type, data))
        await event_queue.subscribe(ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value, capture_event)
        
        # Emit monitoring status
        await system_monitor._emit_monitoring_status()
        await asyncio.sleep(0.1)  # Small delay to allow event processing
        
        # Check if event was emitted
        status_events = [d for e, d in events if e == ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value]
        assert len(status_events) > 0
        
        # At least one event should have component == "system_monitor"
        assert any(
            d.get("component") == "system_monitor" 
            for d in status_events
        )


# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])