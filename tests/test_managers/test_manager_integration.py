import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
import sys
import json

from resources.managers import AgentContextManager, CacheManager, MetricsManager, AgentContextType
from resources.events import EventQueue, ResourceEventTypes
from resources.common import HealthStatus
from resources.base import CleanupConfig, CleanupPolicy, MemoryThresholds

# Integration tests for managers
class TestManagerIntegration:
    
    @pytest_asyncio.fixture
    async def integrated_managers(self, event_queue, default_cleanup_config, default_memory_thresholds):
        """Create all managers sharing the same event queue."""
        context_manager = AgentContextManager(
            event_queue=event_queue,
            cleanup_config=default_cleanup_config,
            memory_thresholds=default_memory_thresholds
        )
        
        cache_manager = CacheManager(
            event_queue=event_queue,
            cleanup_config=default_cleanup_config,
            memory_thresholds=default_memory_thresholds
        )
        
        metrics_manager = MetricsManager(
            event_queue=event_queue,
            cleanup_config=default_cleanup_config,
            memory_thresholds=default_memory_thresholds
        )
        
        yield (context_manager, cache_manager, metrics_manager)
        
        # Cleanup all resources after test
        for context_id in list(context_manager._agent_contexts.keys()):
            await context_manager._cleanup_context(context_id)
            
        for key in list(cache_manager._cache.keys()):
            await cache_manager.invalidate(key)
            
        metrics_manager._metrics.clear()
    
    @pytest.mark.asyncio
    async def test_shared_event_queue(self, integrated_managers, event_queue):
        """Test that all managers share the same event queue and can emit events."""
        context_manager, cache_manager, metrics_manager = integrated_managers
        
        # Set up event tracking
        events_received = []
        
        # Create a listener function
        async def event_listener(event_type, payload):
            events_received.append((event_type, payload))
        
        # Register the listener
        await event_queue.subscribe(ResourceEventTypes.AGENT_CONTEXT_UPDATED.value, event_listener)
        await event_queue.subscribe(ResourceEventTypes.CACHE_UPDATED.value, event_listener)
        await event_queue.subscribe(ResourceEventTypes.METRIC_RECORDED.value, event_listener)
        
        # Perform operations on all managers
        await context_manager.create_context(
            agent_id="integration_test_agent",
            operation_id="integration_op",
            schema={"test": "schema"}
        )
        
        await cache_manager.set_cache(
            key="integration_test_cache",
            value={"test": "value"}
        )
        
        await metrics_manager.record_metric(
            metric_name="integration_test_metric",
            value=100.0,
            metadata={"integration": "test"}
        )
        
        # Verify events were received
        # Allow a short time for events to be processed
        await asyncio.sleep(0.1)
        
        # Verify we got events from all managers
        event_types = [e[0] for e in events_received]
        assert ResourceEventTypes.AGENT_CONTEXT_UPDATED.value in event_types
        assert ResourceEventTypes.CACHE_UPDATED.value in event_types
        assert ResourceEventTypes.METRIC_RECORDED.value in event_types
    
    @pytest.mark.asyncio
    async def test_context_with_cached_data(self, integrated_managers, sample_agent_schema, sample_agent_data):
        """Test using CacheManager to cache AgentContext data."""
        context_manager, cache_manager, metrics_manager = integrated_managers
        
        # Create a context
        context = await context_manager.create_context(
            agent_id="cache_test_agent",
            operation_id="cache_op",
            schema=sample_agent_schema
        )
        
        # Update context with data
        await context_manager.update_context(
            context_id="cache_test_agent",
            data_updates=sample_agent_data
        )
        
        # Cache the context data
        context_dict = context.to_dict()
        await cache_manager.set_cache(
            key="context_cache_cache_test_agent",
            value=context_dict,
            metadata={"type": "agent_context"}
        )
        
        # Verify context was cached
        cached_context = await cache_manager.get_cache("context_cache_cache_test_agent")
        assert cached_context is not None
        assert cached_context["operation_id"] == "cache_op"
        assert cached_context["data"] == [sample_agent_data]
        
        # Clean up the context but keep the cache
        await context_manager._cleanup_context("cache_test_agent")
        
        # Verify context is gone but cache remains
        context = await context_manager.get_context("cache_test_agent")
        assert context is None
        
        cached_context = await cache_manager.get_cache("context_cache_cache_test_agent")
        assert cached_context is not None
    
    @pytest.mark.asyncio
    async def test_metrics_for_cache_operations(self, integrated_managers):
        """Test recording metrics for cache operations."""
        context_manager, cache_manager, metrics_manager = integrated_managers
        
        # Perform cache operations and record metrics
        start_time = datetime.now()
        
        # Operation 1
        await cache_manager.set_cache(
            key="metrics_test_1",
            value={"data": "value1"}
        )
        
        op1_time = (datetime.now() - start_time).total_seconds() * 1000  # in ms
        await metrics_manager.record_metric(
            metric_name="cache_operation_time",
            value=op1_time,
            metadata={"operation": "set", "key": "metrics_test_1"}
        )
        
        # Operation 2
        start_time = datetime.now()
        await cache_manager.get_cache("metrics_test_1")
        
        op2_time = (datetime.now() - start_time).total_seconds() * 1000  # in ms
        await metrics_manager.record_metric(
            metric_name="cache_operation_time",
            value=op2_time,
            metadata={"operation": "get", "key": "metrics_test_1"}
        )
        
        # Get metrics
        metrics = await metrics_manager.get_metrics("cache_operation_time")
        
        # Verify metrics were recorded
        assert len(metrics) == 2
        assert metrics[0]["metadata"]["operation"] == "set"
        assert metrics[1]["metadata"]["operation"] == "get"
        
        # Calculate stats
        stats = await metrics_manager.get_metric_stats("cache_operation_time")
        assert "avg" in stats
        assert "min" in stats
        assert "max" in stats
    
    @pytest.mark.asyncio
    async def test_context_metrics_and_cache(self, integrated_managers, sample_agent_schema, sample_agent_data):
        """Test end-to-end workflow with all three managers."""
        context_manager, cache_manager, metrics_manager = integrated_managers
        
        # Track operations with metrics
        operation_times = []
        
        # 1. Create context and measure time
        start_time = datetime.now()
        context = await context_manager.create_context(
            agent_id="workflow_test_agent",
            operation_id="workflow_op",
            schema=sample_agent_schema
        )
        op_time = (datetime.now() - start_time).total_seconds() * 1000
        operation_times.append(("create_context", op_time))
        
        # 2. Update context and measure time
        start_time = datetime.now()
        await context_manager.update_context(
            context_id="workflow_test_agent",
            data_updates=sample_agent_data
        )
        op_time = (datetime.now() - start_time).total_seconds() * 1000
        operation_times.append(("update_context", op_time))
        
        # 3. Cache context and measure time
        start_time = datetime.now()
        context_dict = context.to_dict()
        await cache_manager.set_cache(
            key="workflow_context_cache",
            value=context_dict
        )
        op_time = (datetime.now() - start_time).total_seconds() * 1000
        operation_times.append(("cache_context", op_time))
        
        # 4. Record metrics for all operations
        for operation, time_ms in operation_times:
            await metrics_manager.record_metric(
                metric_name="workflow_operation_time",
                value=time_ms,
                metadata={"operation": operation}
            )
            
        # 5. Get and analyze metrics
        metrics = await metrics_manager.get_metrics("workflow_operation_time")
        assert len(metrics) == 3
        
        # Calculate average operation time
        avg_time = await metrics_manager.get_metric_average("workflow_operation_time")
        assert avg_time is not None
        
        # Store analysis results in cache
        await cache_manager.set_cache(
            key="workflow_analysis",
            value={
                "operation_count": len(metrics),
                "average_time_ms": avg_time,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Verify cached analysis
        analysis = await cache_manager.get_cache("workflow_analysis")
        assert analysis is not None
        assert analysis["operation_count"] == 3
        assert abs(analysis["average_time_ms"] - avg_time) < 0.001
    
    @pytest.mark.asyncio
    async def test_system_health_aggregation(self, integrated_managers, sample_agent_schema, sample_cache_data, sample_metrics_data):
        """Test aggregating health status from all managers."""
        context_manager, cache_manager, metrics_manager = integrated_managers
        
        # Add some load to each manager
        # 1. Create contexts
        for i in range(3):
            await context_manager.create_context(
                agent_id=f"health_test_agent_{i}",
                operation_id=f"health_op_{i}",
                schema=sample_agent_schema
            )
            
        # 2. Add cache entries
        for i in range(5):
            await cache_manager.set_cache(
                key=f"health_test_cache_{i}",
                value=sample_cache_data
            )
            
        # 3. Record metrics
        for name, value, metadata in sample_metrics_data:
            await metrics_manager.record_metric(
                metric_name=name,
                value=value,
                metadata=metadata
            )
            
        # 4. Get health status from all managers
        context_health = await context_manager.get_health_status()
        cache_health = await cache_manager.get_health_status()
        metrics_health = await metrics_manager.get_health_status()
        
        # 5. Aggregate health status
        system_health = {
            "status": "HEALTHY",  # Start with HEALTHY
            "components": {
                "agent_context_manager": context_health.to_dict() if hasattr(context_health, "to_dict") else context_health,
                "cache_manager": cache_health.to_dict() if hasattr(cache_health, "to_dict") else cache_health,
                "metrics_manager": metrics_health.to_dict() if hasattr(metrics_health, "to_dict") else metrics_health
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # If any component is DEGRADED or worse, system health is degraded
        for component in system_health["components"].values():
            if component.get("status", "") == "DEGRADED":
                system_health["status"] = "DEGRADED"
                break
                
        # Verify system health
        assert system_health["status"] in ["HEALTHY", "DEGRADED"]
        assert len(system_health["components"]) == 3
        assert "timestamp" in system_health
    
    @pytest.mark.asyncio
    async def test_memory_threshold_coordination(self, event_queue):
        """Test coordination of memory thresholds across managers."""
        # Create shared memory thresholds
        memory_thresholds = MemoryThresholds(
            warning_percent=70.0,
            critical_percent=85.0,
            per_resource_max_mb=5.0  # Very low for testing
        )
        
        # Create managers with shared thresholds
        context_manager = AgentContextManager(
            event_queue=event_queue,
            memory_thresholds=memory_thresholds
        )
        
        cache_manager = CacheManager(
            event_queue=event_queue,
            memory_thresholds=memory_thresholds
        )
        
        # Track memory threshold events
        threshold_events = []
        
        async def threshold_listener(event_type, payload):
            if "MEMORY" in event_type:
                threshold_events.append((event_type, payload))
        
        # Register listener for memory events
        await event_queue.subscribe("MEMORY_WARNING", threshold_listener)
        await event_queue.subscribe("MEMORY_CRITICAL", threshold_listener)
        
        # Simulate memory usage in both managers
        # This is a bit tricky since we can't easily control actual memory usage in a test
        # We'll directly manipulate the memory monitor's resource sizes
        
        # 1. Set memory usage in context manager
        context_manager._memory_monitor._resource_sizes["context_test"] = 6.0  # > per_resource_max_mb
        
        # 2. Set memory usage in cache manager
        cache_manager._memory_monitor._resource_sizes["cache_test"] = 6.0  # > per_resource_max_mb
        
        # 3. Manually trigger memory check in both managers
        # This would normally happen during operations
        await context_manager._memory_monitor.check_memory()
        await cache_manager._memory_monitor.check_memory()
        
        # Allow time for events to be processed
        await asyncio.sleep(0.1)
        
        # Verify memory threshold events were emitted
        assert len(threshold_events) > 0
        
        # Clean up
        context_manager._memory_monitor._resource_sizes.clear()
        cache_manager._memory_monitor._resource_sizes.clear()
    
    @pytest.mark.asyncio
    async def test_context_restoration_from_cache(self, integrated_managers, sample_agent_schema, sample_agent_data):
        """Test restoring an agent context from cache."""
        context_manager, cache_manager, metrics_manager = integrated_managers
        
        # 1. Create and populate a context
        original_context = await context_manager.create_context(
            agent_id="restore_test_agent",
            operation_id="restore_op",
            schema=sample_agent_schema,
            context_type=AgentContextType.PERSISTENT
        )
        
        await context_manager.update_context(
            context_id="restore_test_agent",
            data_updates=sample_agent_data
        )
        
        # 2. Cache the context data
        original_dict = original_context.to_dict()
        await cache_manager.set_cache(
            key="restore_test_context",
            value=original_dict
        )
        
        # 3. Remove the original context
        await context_manager._cleanup_context("restore_test_agent")
        
        # 4. Restore context from cache
        cached_dict = await cache_manager.get_cache("restore_test_context")
        
        # Create a new context with the cached data
        restored_context = await context_manager.create_context(
            agent_id="restored_agent",
            operation_id=cached_dict["operation_id"],
            schema=cached_dict["schema"],
            context_type=AgentContextType.valueOf(cached_dict["context_type"]) if hasattr(AgentContextType, "valueOf") else AgentContextType[cached_dict["context_type"]]
        )
        
        # Restore data
        for data_item in cached_dict["data"]:
            await context_manager.update_context(
                context_id="restored_agent",
                data_updates=data_item
            )
            
        # 5. Record metric for restoration time and success
        await metrics_manager.record_metric(
            metric_name="context_restoration",
            value=1.0,  # Success
            metadata={"original_id": "restore_test_agent", "restored_id": "restored_agent"}
        )
        
        # 6. Verify restoration was successful
        restored = await context_manager.get_context("restored_agent")
        assert restored is not None
        assert restored.operation_id == original_context.operation_id
        assert restored.schema == original_context.schema

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])