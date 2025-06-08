"""
Integration tests for FFTT system architecture improvements.

Tests verify:
1. Event Queue Standardization
2. Centralized Error Handling
3. Resource Cleanup Coordination
4. Thread Safety in Cross-Component Operations
"""
import asyncio
import pytest
import logging
import time
import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Awaitable
from unittest.mock import MagicMock, patch, AsyncMock
import random
import sys
import os

# Add proper import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import modules to test
from resources.events import EventQueue, ResourceEventTypes, EventLoopManager
from resources.base import BaseManager, CleanupConfig, CleanupPolicy, ManagerConfig
from resources.errors import ResourceError, ResourceOperationError, ErrorSeverity, ResourceTimeoutError
from resources.monitoring import HealthStatus
from resources.managers import AgentContextManager, CacheManager, MetricsManager
from resources.state import StateManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

import pytest_asyncio

class TestIntegration:
    """Integration tests for the improved component integration."""
    
    @pytest_asyncio.fixture
    async def event_queue(self):
        """Fixture for centralized event queue."""
        queue = EventQueue(queue_id="test_integration_queue")
        await queue.start()
        yield queue
        await queue.stop()
        
    @pytest_asyncio.fixture
    async def state_manager(self, event_queue):
        """Fixture for state manager."""
        manager = StateManager(event_queue)
        yield manager
        await manager.cleanup(force=True)
        
    @pytest_asyncio.fixture
    async def context_manager(self, event_queue):
        """Fixture for agent context manager."""
        manager = AgentContextManager(event_queue)
        yield manager
        await manager.cleanup(force=True)
        
    @pytest_asyncio.fixture
    async def cache_manager(self, event_queue):
        """Fixture for cache manager."""
        manager = CacheManager(event_queue)
        yield manager
        await manager.cleanup(force=True)
        
    @pytest_asyncio.fixture
    async def metrics_manager(self, event_queue):
        """Fixture for metrics manager."""
        manager = MetricsManager(event_queue)
        yield manager
        await manager.cleanup(force=True)
        
    @pytest_asyncio.fixture
    async def test_manager(self, event_queue):
        """Create a minimal concrete implementation of BaseManager for testing."""
        class TestManager(BaseManager):
            async def _cleanup_resources(self, force=False):
                self.cleanup_called = True
                self.cleanup_force = force
                logger.info(f"TestManager cleanup called with force={force}")
                
        manager = TestManager(event_queue=event_queue)
        await manager.start()
        yield manager
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_event_queue_standardization(self, event_queue):
        """Test that the event queue is properly initialized and used."""
        # Verify event queue is running
        assert hasattr(event_queue, '_running')
        assert event_queue._running
        
        # Verify queue has proper ID
        assert hasattr(event_queue, '_id')
        assert event_queue._id == "test_integration_queue"
        
        # Verify it's registered with EventLoopManager
        assert event_queue._id in EventLoopManager._resource_registry
        
        # Use a simpler approach with an event to signal completion
        event_processed = asyncio.Event()
        test_value = None
        event_type_received = None
        
        async def test_subscriber(event_type, data):
            nonlocal test_value, event_type_received
            logger.info(f"Subscriber received event: {event_type} with data: {data}")
            
            # Handle batched events - events are wrapped in a batch object
            if data.get("batch"):
                logger.info("Received batched event")
                items = data.get("items", [])
                if items and len(items) > 0:
                    test_value = items[0].get("test_key")
            else:
                # Direct event data
                test_value = data.get("test_key")
                
            event_type_received = event_type
            event_processed.set()
            
        # Subscribe to test event
        logger.info("Subscribing to test_event")
        await event_queue.subscribe("test_event", test_subscriber)
        
        # Emit test event
        test_data = {"test_key": "test_value"}
        logger.info(f"Emitting test_event with data: {test_data}")
        await event_queue.emit("test_event", test_data)
        
        # Wait for event to be processed with timeout
        logger.info("Waiting for event processing signal...")
        try:
            await asyncio.wait_for(event_processed.wait(), timeout=2.0)
            logger.info("Event processed signal received")
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for event to be processed")
            assert False, "Timeout waiting for event to be processed"
        
        # Verify event was received correctly
        assert event_type_received == "test_event", f"Expected event_type 'test_event', got {event_type_received}"
        assert test_value == "test_value", f"Expected test_value 'test_value', got {test_value}"
    
    @pytest.mark.asyncio
    async def test_event_queue_priority(self, event_queue):
        """Test that event priorities are respected."""
        # Use event completion signals
        both_processed = asyncio.Event()
        event_sequence = []
        events_count = 0
        
        async def event_handler(event_type, data):
            nonlocal events_count
            logger.info(f"Handler received: {event_type} with data: {data}")
            
            # For priority test, we want to respond to the raw event type, not the wrapped data
            # but we may need to handle batched events
            if data.get("batch"):
                logger.info(f"Received batched event with {data.get('count', 0)} items")
            
            # Record the event type
            event_sequence.append(event_type)
            events_count += 1
            
            # Set event when both events have been processed
            if events_count >= 2:
                both_processed.set()
            
            # Add slight delay to simulate processing time
            await asyncio.sleep(0.1)
            
        # Subscribe to both events
        logger.info("Subscribing to priority test events")
        await event_queue.subscribe("low_priority", event_handler)
        await event_queue.subscribe("high_priority", event_handler)
        
        # Emit a low priority event followed by a high priority event
        logger.info("Emitting low priority event")
        await event_queue.emit("low_priority", {"priority": "low"}, priority="low")
        logger.info("Emitting high priority event")
        await event_queue.emit("high_priority", {"priority": "high"}, priority="high")
        
        # Wait for both events to be processed with timeout
        logger.info("Waiting for both events to be processed...")
        try:
            await asyncio.wait_for(both_processed.wait(), timeout=3.0)
            logger.info("Both events processed signal received")
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for both events to be processed")
            assert False, "Timeout waiting for both events to be processed"
        
        # Verify high priority event was processed first
        logger.info(f"Event sequence: {event_sequence}")
        assert len(event_sequence) == 2, f"Expected 2 events in sequence, got {len(event_sequence)}"
        assert event_sequence[0] == "high_priority", "High priority event should be processed first"
        assert event_sequence[1] == "low_priority", "Low priority event should be processed second"
        
    @pytest.mark.asyncio
    async def test_centralized_error_handling(self, event_queue, state_manager):
        """Test the standardized error handling pattern."""
        # Track error events
        error_events = []
        
        async def error_subscriber(event_type, data):
            error_events.append((event_type, data))
            
        # Subscribe to both error event types
        await event_queue.subscribe(ResourceEventTypes.ERROR_OCCURRED.value, error_subscriber)
        await event_queue.subscribe(ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value, error_subscriber)
        
        # Trigger an error in state manager
        try:
            # Create a proper ResourceError with required arguments
            test_error = ResourceOperationError(
                message="Test resource error",
                resource_id="test_integration",
                severity=ErrorSeverity.DEGRADED,
                operation="test_operation"
            )
            await state_manager.handle_operation_error(test_error, "test_operation")
        except Exception as e:
            logger.error(f"Unexpected exception: {e}")
            assert False, "Error handling should not propagate errors"
        
        # Wait for events to process
        await event_queue.wait_for_processing()
        
        # Verify both error events were emitted
        assert len(error_events) >= 2
        
        # Verify error events contain required fields
        for event_type, data in error_events:
            logger.info(f"Examining error event: {event_type}, data: {data}")
            
            # Handle batched events
            if data.get("batch"):
                logger.info("Found batched error event")
                items = data.get("items", [])
                for item in items:
                    # Check each item in the batch
                    assert "component_id" in item, f"Missing component_id in {item}"
                    assert "operation" in item, f"Missing operation in {item}"
                    if "timestamp" not in item and "context" in item:
                        # Sometimes timestamp is in context
                        assert "timestamp" in item["context"], f"Missing timestamp in {item}"
                    # Correlation ID might be in context
                    if "correlation_id" not in item and "context" in item:
                        assert "correlation_id" in item["context"], f"Missing correlation_id in {item}"
            else:
                # Non-batched events
                assert "component_id" in data, f"Missing component_id in {data}"
                assert "operation" in data, f"Missing operation in {data}"
                assert "timestamp" in data, f"Missing timestamp in {data}"
                # Correlation ID might be in context
                if "correlation_id" not in data and "context" in data:
                    assert "correlation_id" in data["context"], f"Missing correlation_id in {data}"
    
    @pytest.mark.asyncio
    async def test_error_handling_correlation(self, test_manager):
        """Test error correlation IDs and standardized error emission."""
        # Set up error tracking
        emitted_errors = []
        
        async def error_handler(event_type, data):
            if event_type in [ResourceEventTypes.ERROR_OCCURRED.value, 
                              ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value]:
                emitted_errors.append(data)
                
        # Subscribe to error events
        await test_manager._event_queue.subscribe(ResourceEventTypes.ERROR_OCCURRED.value, error_handler)
        await test_manager._event_queue.subscribe(ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value, error_handler)
        
        # Generate a test error
        test_error = ResourceOperationError(
            message="Test error",
            resource_id="test_resource",
            severity=ErrorSeverity.DEGRADED,
            operation="test_operation"
        )
        
        # Process the error (with timeout)
        try:
            await asyncio.wait_for(
                test_manager.handle_operation_error(test_error, "test_operation"),
                timeout=2.0
            )
        except asyncio.TimeoutError:
            pytest.fail("Error handling timed out after 2 seconds")
        
        # Wait for error processing (with timeout)
        try:
            await asyncio.wait_for(asyncio.sleep(0.5), timeout=1.0)
        except asyncio.TimeoutError:
            pytest.fail("Waiting for error events timed out")
        
        # Verify error was emitted to both event types (for backward compatibility)
        error_occurred_count = sum(1 for e in emitted_errors 
                                  if e.get("error_type") and "test_resource" in str(e))
        
        assert error_occurred_count >= 2, "Error should be emitted to both event types"
        
        # Verify correlation ID was added
        correlation_id_present = any("correlation_id" in e for e in emitted_errors)
        assert correlation_id_present, "Correlation ID should be present in error events"
        
        # Verify error details are present
        error_details = [e for e in emitted_errors if e.get("message") == "Test error" 
                         or (e.get("context") and "Test error" in str(e.get("context")))]
        assert len(error_details) > 0, "Error details should be present in events"
    
    @pytest.mark.asyncio
    async def test_error_recovery_tracking(self, test_manager):
        """Test that error recovery tracking works correctly."""
        # Set up error tracking
        recovery_events = []
        
        async def recovery_handler(event_type, data):
            if event_type in [ResourceEventTypes.RESOURCE_ERROR_RECOVERY_STARTED.value,
                              ResourceEventTypes.RESOURCE_ERROR_RECOVERY_COMPLETED.value]:
                recovery_events.append((event_type, data))
                
        # Subscribe to recovery events
        await test_manager._event_queue.subscribe(
            ResourceEventTypes.RESOURCE_ERROR_RECOVERY_STARTED.value, recovery_handler)
        await test_manager._event_queue.subscribe(
            ResourceEventTypes.RESOURCE_ERROR_RECOVERY_COMPLETED.value, recovery_handler)
        
        # Create a recoverable error
        test_error = ResourceOperationError(
            message="Recoverable test error",
            resource_id="test_resource",
            severity=ErrorSeverity.DEGRADED,
            operation="test_operation",
            recovery_strategy="force_cleanup"  # This is a valid strategy
        )
        
        # Handle the error which should trigger recovery (with timeout)
        try:
            await asyncio.wait_for(
                test_manager.handle_operation_error(test_error, "test_operation"),
                timeout=2.0
            )
        except asyncio.TimeoutError:
            pytest.fail("Error handling timed out after 2 seconds")
        
        # Wait for recovery processing (with timeout)
        timeout_future = asyncio.create_task(asyncio.sleep(1.0))
        
        # Add a timeout for the waiting
        try:
            await asyncio.wait_for(timeout_future, timeout=2.0)
        except asyncio.TimeoutError:
            pytest.fail("Waiting for recovery events timed out")
        
        # Verify recovery events were emitted
        assert len(recovery_events) > 0, "Recovery events should be emitted"
        
        # Verify we have both started and completed events
        event_types = [event[0] for event in recovery_events]
        assert ResourceEventTypes.RESOURCE_ERROR_RECOVERY_STARTED.value in event_types, "Recovery started event missing"
        assert ResourceEventTypes.RESOURCE_ERROR_RECOVERY_COMPLETED.value in event_types, "Recovery completed event missing"
    
    @pytest.mark.asyncio
    async def test_implement_recovery_strategy(self, test_manager):
        """Test that recovery strategies are correctly implemented."""
        # Test each recovery strategy
        strategies = ["force_cleanup", "reduce_load", "retry_with_backoff", 
                      "restart_component", "emergency_cleanup"]
        
        for strategy in strategies:
            # Create error with this strategy
            test_error = ResourceOperationError(
                message=f"Test error with {strategy}",
                resource_id="test_resource",
                severity=ErrorSeverity.DEGRADED,
                operation=f"test_{strategy}",
                recovery_strategy=strategy
            )
            
            try:
                # Implement the recovery strategy with timeout
                result = await asyncio.wait_for(
                    test_manager.implement_recovery_strategy(test_error),
                    timeout=2.0  # 2 second timeout
                )
                
                # All strategies should succeed except manual_intervention_required
                assert result is True, f"Strategy {strategy} should return True"
            except asyncio.TimeoutError:
                pytest.fail(f"Recovery strategy {strategy} timed out after 2 seconds")
            
        # Special case for manual intervention
        manual_error = ResourceOperationError(
            message="Manual intervention required",
            resource_id="test_resource",
            severity=ErrorSeverity.FATAL,
            operation="test_manual",
            recovery_strategy="manual_intervention_required"
        )
        
        try:
            # Manual intervention should return False (with timeout)
            result = await asyncio.wait_for(
                test_manager.implement_recovery_strategy(manual_error),
                timeout=2.0  # 2 second timeout
            )
            assert result is False, "Manual intervention should return False"
        except asyncio.TimeoutError:
            pytest.fail("Manual intervention recovery strategy timed out after 2 seconds")
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_coordination(self, event_queue, cache_manager):
        """Test the coordinated resource cleanup."""
        # Add some data to the cache
        await cache_manager.set_cache("test_key1", "test_value1")
        await cache_manager.set_cache("test_key2", "test_value2")
        await cache_manager.set_cache("test_key3", "test_value3")
        
        # Verify cache has data
        assert await cache_manager.get_cache("test_key1") == "test_value1"
        
        # Track cleanup events
        cleanup_events = []
        
        async def cleanup_subscriber(event_type, data):
            cleanup_events.append((event_type, data))
            
        # Subscribe to cleanup events
        await event_queue.subscribe(ResourceEventTypes.RESOURCE_CLEANUP.value, cleanup_subscriber)
        
        # Perform cleanup
        await cache_manager.cleanup(force=True)
        
        # Wait for events to process
        await event_queue.wait_for_processing()
        
        # Verify cleanup event was emitted
        assert len(cleanup_events) >= 1
        
        # Verify cleanup event contains required fields
        event_type, data = cleanup_events[0]
        assert event_type == ResourceEventTypes.RESOURCE_CLEANUP.value
        assert "resource_id" in data
        assert "component" in data
        assert "timestamp" in data
        assert "force" in data
        assert data["force"] is True
    
    @pytest.mark.asyncio
    async def test_base_manager_cleanup(self, test_manager):
        """Test that BaseManager cleanup works correctly."""
        # Verify cleanup flags are not set initially
        assert not hasattr(test_manager, "cleanup_called")
        
        # Call cleanup
        await test_manager.cleanup()
        
        # Verify cleanup was called
        assert test_manager.cleanup_called
        assert test_manager.cleanup_force is False
        
        # Reset for forced cleanup test
        test_manager.cleanup_called = False
        
        # Call forced cleanup
        await test_manager.cleanup(force=True)
        
        # Verify forced cleanup was called
        assert test_manager.cleanup_called
        assert test_manager.cleanup_force is True
    
    @pytest.mark.asyncio
    async def test_manager_cleanup_chain(self, event_queue):
        """Test cleanup across multiple managers."""
        # Create tracked flags
        cleanup_calls = {}
        
        # Create concrete manager implementation
        class TrackingManager(BaseManager):
            def __init__(self, event_queue, name):
                super().__init__(event_queue=event_queue)
                self.name = name
                cleanup_calls[name] = {"called": False, "force": False}
                
            async def _cleanup_resources(self, force=False):
                cleanup_calls[self.name]["called"] = True
                cleanup_calls[self.name]["force"] = force
                
        # Create multiple managers
        manager1 = TrackingManager(event_queue, "manager1")
        manager2 = TrackingManager(event_queue, "manager2")
        manager3 = TrackingManager(event_queue, "manager3")
        
        # Register with EventLoopManager
        EventLoopManager.register_resource("manager1", manager1)
        EventLoopManager.register_resource("manager2", manager2)
        EventLoopManager.register_resource("manager3", manager3)
        
        # Verify no cleanup called yet
        for name in cleanup_calls:
            assert cleanup_calls[name]["called"] == False
            
        # Clean up all resources through EventLoopManager
        await EventLoopManager.cleanup_resources()
        
        # Wait for cleanup to complete
        await asyncio.sleep(0.5)
        
        # Verify all managers were cleaned up
        for name in cleanup_calls:
            assert cleanup_calls[name]["called"] == True, f"{name} cleanup not called"
    
    @pytest.mark.asyncio
    async def test_concrete_manager_cleanup_resources(self, state_manager, context_manager, 
                                                     cache_manager, metrics_manager):
        """Test that concrete manager implementations have _cleanup_resources method."""
        # Verify each manager type has cleanup implementation
        managers = [state_manager, context_manager, cache_manager, metrics_manager]
        
        for manager in managers:
            # Check method exists and is callable
            assert hasattr(manager, "_cleanup_resources")
            
            # Call cleanup
            await manager.cleanup()
            
            # Call forced cleanup
            await manager.cleanup(force=True)
    
    @pytest.mark.asyncio
    async def test_thread_safety(self, event_queue, metrics_manager):
        """Test thread safety in cross-component operations."""
        # Create a lot of concurrent operations to test thread safety
        async def record_metric(i):
            await metrics_manager.record_metric(
                f"test_metric_{i % 10}",  # Use 10 different metrics
                float(i),
                {"test_index": i}
            )
            
        # Run many concurrent operations
        tasks = [record_metric(i) for i in range(100)]
        await asyncio.gather(*tasks)
        
        # Wait for processing
        await event_queue.wait_for_processing()
        
        # Verify metrics were recorded correctly
        for i in range(10):
            metric_name = f"test_metric_{i}"
            metrics = await metrics_manager.get_metrics(metric_name)
            assert len(metrics) > 0
    
    @pytest.mark.asyncio
    async def test_operation_specific_locks(self, test_manager):
        """Test that operation-specific locks prevent concurrent execution."""
        # Create a delay-based test operation
        async def slow_operation():
            await asyncio.sleep(0.5)
            return "operation_result"
        
        # Create a set to track concurrent executions
        execution_flag = {"running": False, "violations": 0}
        
        # Create a wrapped operation that detects concurrent execution
        async def concurrent_detection_wrapper():
            if execution_flag["running"]:
                execution_flag["violations"] += 1
                raise RuntimeError("Detected concurrent execution!")
                
            execution_flag["running"] = True
            try:
                return await slow_operation()
            finally:
                execution_flag["running"] = False
                
        # Execute operation with thread safety
        op_key = "test_operation"
        
        # Run multiple concurrent attempts to execute the operation
        tasks = []
        for _ in range(5):
            task = asyncio.create_task(
                test_manager._ensure_thread_safety(op_key, concurrent_detection_wrapper)
            )
            tasks.append(task)
            
        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify no concurrent execution occurred
        assert execution_flag["violations"] == 0, "Thread safety violation detected"
    
    @pytest.mark.asyncio
    async def test_lock_acquisition_timeout(self, test_manager):
        """Test that lock acquisition timeouts work correctly."""
        # Create a lock manually
        op_key = "timeout_test"
        test_manager._operation_locks[op_key] = asyncio.Lock()
        
        # Acquire the lock
        async with test_manager._operation_locks[op_key]:
            # Try to acquire it again with timeout
            start_time = time.monotonic()
            
            # Define operation that will be blocked
            async def blocked_operation():
                await asyncio.sleep(5)  # This won't execute due to timeout
                return "never_reached"
            
            # Should timeout quickly
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(
                    test_manager._ensure_thread_safety(op_key, blocked_operation),
                    timeout=0.2
                )
            
            # Verify timeout occurred quickly
            elapsed = time.monotonic() - start_time
            assert elapsed < 1.0, "Timeout took too long"
            
    @pytest.mark.asyncio
    async def test_multi_component_integration(self, event_queue, state_manager, 
                                             context_manager, cache_manager, metrics_manager):
        """Test integration between multiple components using the central event queue."""
        # Create some test data
        test_data = {
            "state_key": "test_state",
            "state_data": {"value": "test_state_value"},
            "cache_key": "test_cache",
            "cache_data": {"value": "test_cache_value"},
            "metric_name": "test_integrated_metric",
            "metric_value": 42.0
        }
        
        # Track relevant events
        received_events = []
        
        async def event_subscriber(event_type, data):
            received_events.append((event_type, data))
            
        # Subscribe to various event types
        event_types = [
            ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
            ResourceEventTypes.CACHE_UPDATED.value,
            ResourceEventTypes.METRIC_RECORDED.value
        ]
        
        for event_type in event_types:
            await event_queue.subscribe(event_type, event_subscriber)
        
        # Perform operations in each component
        state_result = await state_manager.set_state(
            test_data["state_key"], 
            test_data["state_data"]
        )
        
        await cache_manager.set_cache(
            test_data["cache_key"],
            test_data["cache_data"]
        )
        
        await metrics_manager.record_metric(
            test_data["metric_name"],
            test_data["metric_value"],
            {"source": "integration_test"}
        )
        
        # Wait for events to process
        await event_queue.wait_for_processing()
        
        # Verify that operations succeeded
        assert state_result is not None
        assert await cache_manager.get_cache(test_data["cache_key"]) == test_data["cache_data"]
        
        metrics = await metrics_manager.get_metrics(test_data["metric_name"])
        assert len(metrics) > 0
        assert metrics[0]["value"] == test_data["metric_value"]
        
        # Verify events were properly emitted
        assert len(received_events) >= 3
        
        # Check each event type was received
        event_types_received = [event_type for event_type, _ in received_events]
        for event_type in event_types:
            assert event_type in event_types_received
    
    @pytest.mark.asyncio
    async def test_event_propagation_between_components(self, state_manager, context_manager, event_queue):
        """Test that events propagate correctly between components."""
        # Track events received by each component
        state_events = []
        context_events = []
        
        # Set up event handlers
        async def state_event_handler(event_type, data):
            state_events.append((event_type, data))
            
        async def context_event_handler(event_type, data):
            context_events.append((event_type, data))
            
        # Subscribe components to test events
        test_event = "test_integration_event"
        await event_queue.subscribe(test_event, state_event_handler)
        await event_queue.subscribe(test_event, context_event_handler)
        
        # Emit test event
        test_data = {"integration_test": True, "timestamp": datetime.now().isoformat()}
        await event_queue.emit(test_event, test_data)
        
        # Wait for event processing
        await asyncio.sleep(0.5)
        
        # Verify both components received the event
        assert len(state_events) > 0, "State manager didn't receive event"
        assert len(context_events) > 0, "Context manager didn't receive event"
        
        # Verify event data is consistent
        assert state_events[0][1] == test_data, "State manager received incorrect data"
        assert context_events[0][1] == test_data, "Context manager received incorrect data"
    
    @pytest.mark.asyncio
    async def test_cross_component_error_handling(self, state_manager, cache_manager, event_queue):
        """Test error handling across multiple components."""
        # Track error events
        error_events = []
        
        # Set up error handler
        async def error_handler(event_type, data):
            if event_type in [ResourceEventTypes.ERROR_OCCURRED.value, 
                              ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value]:
                error_events.append((event_type, data))
                
        # Subscribe to error events
        await event_queue.subscribe(ResourceEventTypes.ERROR_OCCURRED.value, error_handler)
        await event_queue.subscribe(ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value, error_handler)
        
        # Create errors in different components
        state_error = ResourceOperationError(
            message="State error",
            resource_id="state_manager",
            severity=ErrorSeverity.DEGRADED, 
            operation="state_test"
        )
        
        cache_error = ResourceOperationError(
            message="Cache error",
            resource_id="cache_manager",
            severity=ErrorSeverity.TRANSIENT,
            operation="cache_test"
        )
        
        # Process errors in both components
        await state_manager.handle_operation_error(state_error, "state_test")
        await cache_manager.handle_operation_error(cache_error, "cache_test")
        
        # Wait for error processing
        await asyncio.sleep(0.5)
        
        # Verify errors from both components were emitted
        component_ids = [data.get("component_id") for _, data in error_events]
        
        # Look for both managers in the component IDs
        state_manager_found = any("state" in str(component_id).lower() for component_id in component_ids)
        cache_manager_found = any("cache" in str(component_id).lower() for component_id in component_ids)
        
        assert state_manager_found, "State manager error not found"
        assert cache_manager_found, "Cache manager error not found"
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_cascading(self, event_queue):
        """Test that resource cleanup cascades correctly."""
        # Create tracked resources
        cleanup_sequence = []
        
        # Define a resource dependency structure
        class DependentResource(BaseManager):
            def __init__(self, event_queue, name, dependencies=None):
                super().__init__(event_queue=event_queue)
                self.name = name
                self.dependencies = dependencies or []
                
            async def _cleanup_resources(self, force=False):
                # Record cleanup
                cleanup_sequence.append(self.name)
                
                # Clean up dependencies if force=True
                if force and self.dependencies:
                    for dep in self.dependencies:
                        await dep.cleanup(force=True)
        
        # Create a dependency tree
        leaf1 = DependentResource(event_queue, "leaf1")
        leaf2 = DependentResource(event_queue, "leaf2")
        branch1 = DependentResource(event_queue, "branch1", [leaf1])
        branch2 = DependentResource(event_queue, "branch2", [leaf2])
        root = DependentResource(event_queue, "root", [branch1, branch2])
        
        # Clean up the root with force=True to cascade
        await root.cleanup(force=True)
        
        # Verify cleanup cascaded to all resources
        for name in ["leaf1", "leaf2", "branch1", "branch2", "root"]:
            assert name in cleanup_sequence, f"{name} was not cleaned up"
        
        # Verify root was cleaned up first
        assert cleanup_sequence[0] == "root", "Root should be cleaned up first"