import pytest
import asyncio
import pytest_asyncio
import time
from datetime import datetime
import logging
from enum import Enum

# Import the modules being tested
from resources.events import Event, EventQueue, EventMonitor, ResourceEventTypes
from resources.common import ResourceType, HealthStatus, ErrorSeverity, ResourceState
from resources.errors import ResourceOperationError, ResourceError

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_event_integration")

# Fixtures for async testing
@pytest_asyncio.fixture
async def event_queue():
    """Create a new event queue for each test."""
    queue = EventQueue(max_size=100)
    await queue.start()
    yield queue
    await queue.stop()

# Simple resource manager for integration testing
class ResourceManager:
    """Sample resource manager that uses the event system."""
    
    def __init__(self, event_queue):
        self.event_queue = event_queue
        self.resources = {}
        self.resource_states = {}
        self.metrics = {}
    
    @pytest.mark.asyncio
    async def initialize(self):
        """Initialize the resource manager."""
        # Subscribe to relevant events
        await self.event_queue.subscribe(
            ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
            self._handle_resource_state_change
        )
        await self.event_queue.subscribe(
            ResourceEventTypes.RESOURCE_METRIC_RECORDED.value,
            self._handle_resource_metric
        )
        await self.event_queue.subscribe(
            ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
            self._handle_resource_error
        )
    
    @pytest.mark.asyncio
    async def create_resource(self, resource_id, resource_type, metadata=None):
        """Create a new managed resource."""
        if resource_id in self.resources:
            raise ValueError(f"Resource {resource_id} already exists")
        
        # Store resource
        self.resources[resource_id] = {
            "type": resource_type,
            "created_at": datetime.now(),
            "metadata": metadata or {}
        }
        
        # Set initial state
        self.resource_states[resource_id] = ResourceState.ACTIVE
        
        # Emit state change event
        await self.event_queue.emit(
            ResourceEventTypes.RESOURCE_STATE_CHANGED,
            {
                "resource_id": resource_id,
                "previous_state": None,
                "new_state": ResourceState.ACTIVE.name,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return resource_id
    
    @pytest.mark.asyncio
    async def update_resource_state(self, resource_id, new_state):
        """Update a resource's state."""
        if resource_id not in self.resources:
            raise ValueError(f"Resource {resource_id} does not exist")
        
        previous_state = self.resource_states[resource_id]
        self.resource_states[resource_id] = new_state
        
        # Emit state change event
        await self.event_queue.emit(
            ResourceEventTypes.RESOURCE_STATE_CHANGED,
            {
                "resource_id": resource_id,
                "previous_state": previous_state.name,
                "new_state": new_state.name,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @pytest.mark.asyncio
    async def record_metric(self, resource_id, metric_name, value):
        """Record a metric for a resource."""
        if resource_id not in self.resources:
            raise ValueError(f"Resource {resource_id} does not exist")
        
        # Store metric
        if resource_id not in self.metrics:
            self.metrics[resource_id] = {}
        
        self.metrics[resource_id][metric_name] = {
            "value": value,
            "timestamp": datetime.now()
        }
        
        # Emit metric event
        await self.event_queue.emit(
            ResourceEventTypes.RESOURCE_METRIC_RECORDED,
            {
                "resource_id": resource_id,
                "metric_name": metric_name,
                "value": value,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @pytest.mark.asyncio
    async def simulate_error(self, resource_id, error_message, severity):
        """Simulate an error for a resource."""
        if resource_id not in self.resources:
            raise ValueError(f"Resource {resource_id} does not exist")
        
        # Create error
        error = ResourceOperationError(
            message=error_message,
            resource_id=resource_id,
            severity=severity,
            operation="test_operation"
        )
        
        # Add context
        error.context = type('OperationContext', (), {
            'resource_id': resource_id,
            'operation': "test_operation",
            'attempt': 1,
            'recovery_attempts': 0,
            'details': {}
        })
        
        # Emit error event
        await self.event_queue.emit_error(error)
        
        # Update resource state if error is fatal
        if severity == ErrorSeverity.FATAL:
            await self.update_resource_state(resource_id, ResourceState.FAILED)
    
    @pytest.mark.asyncio
    async def _handle_resource_state_change(self, event_type, data):
        """Handle resource state change events."""
        logger.debug(f"Received state change: {data}")
        # In a real implementation, this would trigger additional logic
    
    @pytest.mark.asyncio
    async def _handle_resource_metric(self, event_type, data):
        """Handle resource metric events."""
        logger.debug(f"Received metric: {data}")
        # In a real implementation, this might trigger alerts or scaling
    
    @pytest.mark.asyncio
    async def _handle_resource_error(self, event_type, data):
        """Handle resource error events."""
        logger.debug(f"Received error: {data}")
        # In a real implementation, this would trigger recovery or escalation

# Test class for integration scenarios
class TestEventIntegration:
    """Integration tests with a sample resource manager."""
    
    @pytest.mark.asyncio
    async def test_resource_lifecycle_events(self, event_queue):
        """Test a complete resource lifecycle with events."""
        # Create resource manager
        manager = ResourceManager(event_queue)
        await manager.initialize()
        
        # Track state change events
        state_changes = []
        async def state_change_listener(event_type, data):
            state_changes.append(data)
        
        # Subscribe to state changes
        await event_queue.subscribe(
            ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
            state_change_listener
        )
        
        # Create a resource
        resource_id = await manager.create_resource(
            "test-resource-1",
            ResourceType.CACHE,
            {"description": "Test cache resource"}
        )
        
        # Update state through various lifecycle stages
        await manager.update_resource_state(resource_id, ResourceState.PAUSED)
        await manager.update_resource_state(resource_id, ResourceState.ACTIVE)
        await manager.update_resource_state(resource_id, ResourceState.FAILED)
        await manager.update_resource_state(resource_id, ResourceState.RECOVERED)
        await manager.update_resource_state(resource_id, ResourceState.TERMINATED)
        
        # Wait for event processing
        await asyncio.sleep(0.2)
        
        # Verify state changes were tracked
        assert len(state_changes) == 6  # Initial + 5 updates
        
        # Verify state transition sequence
        states = [change["new_state"] for change in state_changes]
        expected_states = [
            ResourceState.ACTIVE.name,
            ResourceState.PAUSED.name,
            ResourceState.ACTIVE.name,
            ResourceState.FAILED.name,
            ResourceState.RECOVERED.name,
            ResourceState.TERMINATED.name
        ]
        assert states == expected_states
    
    @pytest.mark.asyncio
    async def test_resource_metrics_and_health(self, event_queue):
        """Test resource metrics and health monitoring."""
        # Create resource manager
        manager = ResourceManager(event_queue)
        await manager.initialize()
        
        # Track metric events
        metrics = []
        async def metric_listener(event_type, data):
            metrics.append(data)
        
        # Subscribe to metric events
        await event_queue.subscribe(
            ResourceEventTypes.RESOURCE_METRIC_RECORDED.value,
            metric_listener
        )
        
        # Create a resource
        resource_id = await manager.create_resource(
            "test-resource-2",
            ResourceType.COMPUTE,
            {"description": "Test compute resource"}
        )
        
        # Record various metrics
        await manager.record_metric(resource_id, "cpu_usage", 0.25)
        await manager.record_metric(resource_id, "memory_usage", 512)
        await manager.record_metric(resource_id, "request_count", 1000)
        await manager.record_metric(resource_id, "error_rate", 0.01)
        
        # Record changing metrics
        for i in range(1, 6):
            # Simulate increasing load
            await manager.record_metric(resource_id, "cpu_usage", 0.25 + (i * 0.1))
            await manager.record_metric(resource_id, "request_count", 1000 + (i * 100))
            await asyncio.sleep(0.01)
        
        # Wait for event processing
        await asyncio.sleep(0.2)
        
        # Verify metrics were tracked
        assert len(metrics) == 4 + (5 * 2)  # Initial 4 + 5 updates of 2 metrics
        
        # Verify CPU metrics show an increase
        cpu_metrics = [m for m in metrics if m["metric_name"] == "cpu_usage"]
        cpu_values = [m["value"] for m in cpu_metrics]
        assert len(cpu_values) == 6  # Initial + 5 updates
        assert cpu_values == [0.25, 0.35, 0.45, 0.55, 0.65, 0.75]
        
        # Verify metrics were stored in the manager
        assert len(manager.metrics[resource_id]) == 4  # 4 unique metric names
        assert "cpu_usage" in manager.metrics[resource_id]
        assert "memory_usage" in manager.metrics[resource_id]
        assert "request_count" in manager.metrics[resource_id]
        assert "error_rate" in manager.metrics[resource_id]
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, event_queue):
        """Test error handling and recovery workflow."""
        # Create resource manager
        manager = ResourceManager(event_queue)
        await manager.initialize()
        
        # Track error events
        errors = []
        async def error_listener(event_type, data):
            errors.append(data)
        
        # Subscribe to error events
        await event_queue.subscribe(
            ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
            error_listener
        )
        
        # Create a resource
        resource_id = await manager.create_resource(
            "test-resource-3",
            ResourceType.AGENT,
            {"description": "Test agent resource"}
        )
        
        # Simulate different types of errors
        await manager.simulate_error(
            resource_id, 
            "Transient connection error", 
            ErrorSeverity.TRANSIENT
        )
        
        await manager.simulate_error(
            resource_id,
            "Service degraded due to high load",
            ErrorSeverity.DEGRADED
        )
        
        await manager.simulate_error(
            resource_id,
            "Fatal process crash",
            ErrorSeverity.FATAL
        )
        
        # Wait for event processing
        await asyncio.sleep(0.2)
        
        # Verify errors were tracked
        assert len(errors) == 3
        
        # Verify error severity progression
        severities = [error["severity"] for error in errors]
        assert severities == ["TRANSIENT", "DEGRADED", "FATAL"]
        
        # Verify resource state after fatal error
        assert manager.resource_states[resource_id] == ResourceState.FAILED
        
        # Simulate recovery
        await manager.update_resource_state(resource_id, ResourceState.RECOVERED)
        
        # Wait for event processing
        await asyncio.sleep(0.1)
        
        # Verify resource is now recovered
        assert manager.resource_states[resource_id] == ResourceState.RECOVERED
    
    @pytest.mark.asyncio
    async def test_event_correlation(self, event_queue):
        """Test event correlation across a resource lifecycle."""
        # Create resource manager
        manager = ResourceManager(event_queue)
        await manager.initialize()
        
        # Create a correlation ID
        correlation_id = "correlation-123"
        
        # Create a resource with the correlation ID
        resource_id = await manager.create_resource(
            "test-resource-4",
            ResourceType.STATE,
            {"correlation_id": correlation_id}
        )
        
        # Track all events with this correlation ID
        correlated_events = []
        async def correlation_listener(event_type, data):
            correlated_events.append((event_type, data))
        
        # Subscribe to all event types we'll use
        for event_type in [
            ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
            ResourceEventTypes.RESOURCE_METRIC_RECORDED.value,
            ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value
        ]:
            await event_queue.subscribe(event_type, correlation_listener)
        
        # Create a sequence of events with the correlation ID
        # State change
        await event_queue.emit(
            ResourceEventTypes.RESOURCE_STATE_CHANGED,
            {
                "resource_id": resource_id,
                "previous_state": ResourceState.ACTIVE.name,
                "new_state": ResourceState.PAUSED.name,
            },
            correlation_id
        )
        
        # Metric
        await event_queue.emit(
            ResourceEventTypes.RESOURCE_METRIC_RECORDED,
            {
                "resource_id": resource_id,
                "metric_name": "throttled",
                "value": True,
            },
            correlation_id
        )
        
        # Error
        error = ResourceOperationError(
            message="Resource throttled",
            resource_id=resource_id,
            severity=ErrorSeverity.DEGRADED,
            operation="process_requests"
        )
        error.context = type('OperationContext', (), {
            'resource_id': resource_id,
            'operation': "process_requests",
            'attempt': 1,
            'recovery_attempts': 0,
            'details': {}
        })
        
        # Emit error with correlation ID
        await event_queue.emit_error(
            error=error,
            additional_context={"correlation_id": correlation_id}
        )
        
        # Wait for event processing
        await asyncio.sleep(0.2)
        
        # Verify all correlated events were tracked
        assert len(correlated_events) == 4
        
        # Verify event types
        event_types = [event[0] for event in correlated_events]
        assert ResourceEventTypes.RESOURCE_STATE_CHANGED.value in event_types
        assert ResourceEventTypes.RESOURCE_METRIC_RECORDED.value in event_types
        assert ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value in event_types

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])