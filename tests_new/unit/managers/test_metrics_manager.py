import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
import time
import sys

from resources.managers import MetricsManager
from resources.common import HealthStatus
from resources.base import CleanupPolicy, CleanupConfig, MemoryThresholds

# Tests for MetricsManager
class TestMetricsManager:
    
    @pytest.mark.asyncio
    async def test_record_metric(self, metrics_manager):
        """Test recording a simple metric."""
        # Record a metric
        await metrics_manager.record_metric(
            metric_name="test_metric",
            value=42.5,
            metadata={"source": "test"}
        )
        
        # Verify metric was recorded
        assert "test_metric" in metrics_manager._metrics
        assert len(metrics_manager._metrics["test_metric"]) == 1
        assert metrics_manager._metrics["test_metric"][0]["value"] == 42.5
        assert metrics_manager._metrics["test_metric"][0]["metadata"]["source"] == "test"
        assert "timestamp" in metrics_manager._metrics["test_metric"][0]
        
    @pytest.mark.asyncio
    async def test_record_multiple_metrics(self, metrics_manager):
        """Test recording multiple metrics for the same name."""
        # Record multiple metrics
        for i in range(5):
            await metrics_manager.record_metric(
                metric_name="multi_metric",
                value=float(i),
                metadata={"iteration": i}
            )
            
        # Verify all metrics were recorded
        assert "multi_metric" in metrics_manager._metrics
        assert len(metrics_manager._metrics["multi_metric"]) == 5
        
        # Verify values
        values = [m["value"] for m in metrics_manager._metrics["multi_metric"]]
        assert values == [0.0, 1.0, 2.0, 3.0, 4.0]
        
        # Verify metadata
        iterations = [m["metadata"]["iteration"] for m in metrics_manager._metrics["multi_metric"]]
        assert iterations == [0, 1, 2, 3, 4]
        
    @pytest.mark.asyncio
    async def test_get_metrics_all(self, metrics_manager, sample_metrics_data):
        """Test getting all metrics for a name."""
        # Record sample metrics
        for name, value, metadata in sample_metrics_data:
            await metrics_manager.record_metric(
                metric_name=name,
                value=value,
                metadata=metadata
            )
            
        # Get all metrics for a specific name
        metrics = await metrics_manager.get_metrics("response_time")
        
        # Verify metrics
        assert len(metrics) == 1
        assert metrics[0]["value"] == 150.5
        assert metrics[0]["metadata"]["endpoint"] == "/api/query"
        
    @pytest.mark.asyncio
    async def test_get_metrics_with_window(self, metrics_manager):
        """Test getting metrics within a time window."""
        # Record metrics with different timestamps
        now = datetime.now()
        
        # First, manually create metrics with specific timestamps
        metrics_manager._metrics["window_metric"] = [
            {
                "value": 1.0,
                "timestamp": (now - timedelta(minutes=30)).isoformat(),
                "metadata": {}
            },
            {
                "value": 2.0,
                "timestamp": (now - timedelta(minutes=20)).isoformat(),
                "metadata": {}
            },
            {
                "value": 3.0,
                "timestamp": (now - timedelta(minutes=10)).isoformat(),
                "metadata": {}
            },
            {
                "value": 4.0,
                "timestamp": now.isoformat(),
                "metadata": {}
            }
        ]
        
        # Get metrics with a 15-minute window
        metrics = await metrics_manager.get_metrics(
            metric_name="window_metric",
            window=timedelta(minutes=15)
        )
        
        # Verify only the most recent 2 metrics are returned
        assert len(metrics) == 2
        assert metrics[0]["value"] == 3.0
        assert metrics[1]["value"] == 4.0
        
    @pytest.mark.asyncio
    async def test_get_metrics_with_limit(self, metrics_manager):
        """Test getting metrics with a limit."""
        # Record 10 metrics
        for i in range(10):
            await metrics_manager.record_metric(
                metric_name="limit_metric",
                value=float(i),
                metadata={}
            )
            
        # Get metrics with a limit of 3
        metrics = await metrics_manager.get_metrics(
            metric_name="limit_metric",
            limit=3
        )
        
        # Verify only the most recent 3 metrics are returned
        assert len(metrics) == 3
        assert metrics[0]["value"] == 7.0
        assert metrics[1]["value"] == 8.0
        assert metrics[2]["value"] == 9.0
        
    @pytest.mark.asyncio
    async def test_get_metrics_with_window_and_limit(self, metrics_manager):
        """Test getting metrics with both window and limit."""
        # Record metrics with different timestamps
        now = datetime.now()
        
        # Create metrics with specific timestamps
        metrics_manager._metrics["window_limit_metric"] = [
            {
                "value": 1.0,
                "timestamp": (now - timedelta(minutes=40)).isoformat(),
                "metadata": {}
            },
            {
                "value": 2.0,
                "timestamp": (now - timedelta(minutes=30)).isoformat(),
                "metadata": {}
            },
            {
                "value": 3.0,
                "timestamp": (now - timedelta(minutes=20)).isoformat(),
                "metadata": {}
            },
            {
                "value": 4.0,
                "timestamp": (now - timedelta(minutes=10)).isoformat(),
                "metadata": {}
            },
            {
                "value": 5.0,
                "timestamp": now.isoformat(),
                "metadata": {}
            }
        ]
        
        # Get metrics with a 30-minute window and limit of 2
        metrics = await metrics_manager.get_metrics(
            metric_name="window_limit_metric",
            window=timedelta(minutes=30),
            limit=2
        )
        
        # Verify results - should be filtered by window first (last 3 entries), then limited to 2
        assert len(metrics) == 2
        assert metrics[0]["value"] == 4.0
        assert metrics[1]["value"] == 5.0
        
    @pytest.mark.asyncio
    async def test_get_metrics_nonexistent(self, metrics_manager):
        """Test getting metrics for a non-existent name."""
        metrics = await metrics_manager.get_metrics("nonexistent_metric")
        assert metrics == []
        
    @pytest.mark.asyncio
    async def test_get_metric_average(self, metrics_manager):
        """Test calculating metric average."""
        # Record metrics with different values
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        for value in values:
            await metrics_manager.record_metric(
                metric_name="avg_metric",
                value=value,
                metadata={}
            )
            
        # Calculate average
        avg = await metrics_manager.get_metric_average("avg_metric")
        
        # Verify average
        assert avg == 30.0  # (10+20+30+40+50)/5 = 30
        
    @pytest.mark.asyncio
    async def test_get_metric_average_with_window(self, metrics_manager):
        """Test calculating metric average within a time window."""
        # Record metrics with different timestamps
        now = datetime.now()
        
        # Create metrics with specific timestamps
        metrics_manager._metrics["avg_window_metric"] = [
            {
                "value": 10.0,
                "timestamp": (now - timedelta(minutes=30)).isoformat(),
                "metadata": {}
            },
            {
                "value": 20.0,
                "timestamp": (now - timedelta(minutes=20)).isoformat(),
                "metadata": {}
            },
            {
                "value": 30.0,
                "timestamp": (now - timedelta(minutes=10)).isoformat(),
                "metadata": {}
            },
            {
                "value": 40.0,
                "timestamp": now.isoformat(),
                "metadata": {}
            }
        ]
        
        # Calculate average with a 15-minute window
        avg = await metrics_manager.get_metric_average(
            metric_name="avg_window_metric",
            window=timedelta(minutes=15)
        )
        
        # Verify average of the last 2 metrics
        assert avg == 35.0  # (30+40)/2 = 35
        
    @pytest.mark.asyncio
    async def test_get_metric_average_nonexistent(self, metrics_manager):
        """Test calculating average for a non-existent metric."""
        avg = await metrics_manager.get_metric_average("nonexistent_metric")
        assert avg is None
        
    @pytest.mark.asyncio
    async def test_get_metric_stats(self, metrics_manager):
        """Test calculating comprehensive metric statistics."""
        # Record metrics with different values
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        for value in values:
            await metrics_manager.record_metric(
                metric_name="stats_metric",
                value=value,
                metadata={}
            )
            
        # Calculate stats
        stats = await metrics_manager.get_metric_stats("stats_metric")
        
        # Verify stats
        assert stats["min"] == 10.0
        assert stats["max"] == 50.0
        assert stats["avg"] == 30.0
        assert stats["count"] == 5
        
    @pytest.mark.asyncio
    async def test_get_metric_stats_with_window(self, metrics_manager):
        """Test calculating statistics within a time window."""
        # Record metrics with different timestamps
        now = datetime.now()
        
        # Create metrics with specific timestamps
        metrics_manager._metrics["stats_window_metric"] = [
            {
                "value": 10.0,
                "timestamp": (now - timedelta(minutes=30)).isoformat(),
                "metadata": {}
            },
            {
                "value": 20.0,
                "timestamp": (now - timedelta(minutes=20)).isoformat(),
                "metadata": {}
            },
            {
                "value": 30.0,
                "timestamp": (now - timedelta(minutes=10)).isoformat(),
                "metadata": {}
            },
            {
                "value": 40.0,
                "timestamp": now.isoformat(),
                "metadata": {}
            }
        ]
        
        # Calculate stats with a 15-minute window
        stats = await metrics_manager.get_metric_stats(
            metric_name="stats_window_metric",
            window=timedelta(minutes=15)
        )
        
        # Verify stats of the last 2 metrics
        assert stats["min"] == 30.0
        assert stats["max"] == 40.0
        assert stats["avg"] == 35.0
        assert stats["count"] == 2
        
    @pytest.mark.asyncio
    async def test_get_metric_stats_nonexistent(self, metrics_manager):
        """Test calculating stats for a non-existent metric."""
        stats = await metrics_manager.get_metric_stats("nonexistent_metric")
        assert stats == {}
        
    @pytest.mark.asyncio
    async def test_cleanup_inactive_metrics(self, event_queue):
        """Test cleanup of inactive metrics."""
        # Create manager with short TTL for testing
        cleanup_config = CleanupConfig(
            policy=CleanupPolicy.TTL,
            ttl_seconds=10,  # Short TTL for testing
            check_interval=1  # Check every second
        )
        
        manager = MetricsManager(
            event_queue=event_queue,
            cleanup_config=cleanup_config
        )
        
        # Add metrics with old timestamps
        now = datetime.now()
        old_time = now - timedelta(seconds=cleanup_config.ttl_seconds * 2)
        
        from collections import deque
        manager._metrics["inactive_metric"] = deque([
            {
                "value": 42.0,
                "timestamp": old_time.isoformat(),
                "metadata": {}
            }
        ], maxlen=1000)
        
        # Record another current metric
        await manager.record_metric(
            metric_name="active_metric",
            value=99.0,
            metadata={}
        )
        
        # Force cleanup to bypass check interval
        await manager.cleanup(force=True)
        
        # Verify inactive metric was cleaned up
        assert "inactive_metric" not in manager._metrics
        
        # Active metric should still be there
        assert "active_metric" in manager._metrics
        
    @pytest.mark.asyncio
    async def test_cleanup_empty_metrics(self, metrics_manager):
        """Test cleanup of empty metric series."""
        # Create an empty metric series
        from collections import deque
        metrics_manager._metrics["empty_metric"] = deque(maxlen=1000)
        
        # Force cleanup to bypass check interval
        await metrics_manager.cleanup(force=True)
        
        # Verify empty metric was cleaned up
        assert "empty_metric" not in metrics_manager._metrics
        
    @pytest.mark.asyncio
    async def test_memory_monitoring(self, metrics_manager):
        """Test that memory usage is monitored correctly."""
        # Record some metrics
        for i in range(100):  # Add enough to have measurable memory impact
            await metrics_manager.record_metric(
                metric_name="memory_test_metric",
                value=float(i),
                metadata={"iteration": i}
            )
            
        # Verify memory usage is tracked
        assert f"metrics_memory_test_metric" in metrics_manager._memory_monitor._resource_sizes
        
        # The size should be non-zero
        assert metrics_manager._memory_monitor._resource_sizes[f"metrics_memory_test_metric"] > 0
        
    @pytest.mark.asyncio
    async def test_get_health_status(self, metrics_manager, sample_metrics_data):
        """Test getting health status."""
        # Record sample metrics
        for name, value, metadata in sample_metrics_data:
            await metrics_manager.record_metric(
                metric_name=name,
                value=value,
                metadata=metadata
            )
            
        # Get health status
        health = await metrics_manager.get_health_status()
        
        # Verify health status
        assert health is not None
        assert health.status in ["HEALTHY", "DEGRADED"]
        assert health.source == "metrics_manager"
        assert "total_series" in health.metadata
        assert health.metadata["total_series"] >= 3
        assert "total_points" in health.metadata
        assert health.metadata["total_points"] >= 3
        
    @pytest.mark.asyncio
    async def test_max_length_deque(self, metrics_manager):
        """Test that metrics deque respects maxlen."""
        # Record more metrics than the default maxlen (1000)
        for i in range(1050):
            await metrics_manager.record_metric(
                metric_name="maxlen_metric",
                value=float(i),
                metadata={}
            )
            
        # Verify length is limited to maxlen
        assert len(metrics_manager._metrics["maxlen_metric"]) == 1000
        
        # Verify oldest metrics were dropped (first 50 should be gone)
        first_value = metrics_manager._metrics["maxlen_metric"][0]["value"]
        assert first_value == 50.0

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])