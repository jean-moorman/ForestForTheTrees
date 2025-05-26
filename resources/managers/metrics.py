from collections import deque, defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Set
import sys
import logging

from resources.common import ResourceState, ResourceType, InterfaceState, HealthStatus
from resources.errors import (
    ErrorSeverity,
    ResourceOperationError,
    ResourceError,
    ResourceExhaustionError,
    ResourceTimeoutError
)
from resources.events import ResourceEventTypes, EventQueue
from resources.base import (
    BaseManager, 
    MemoryThresholds,
    CleanupConfig,
    CleanupPolicy
)

logger = logging.getLogger(__name__)

class MetricsManager(BaseManager):
    """Manages metrics collection and aggregation"""
    def __init__(self, 
                 event_queue: EventQueue,
                 cleanup_config: Optional[CleanupConfig] = None,
                 memory_thresholds: Optional[MemoryThresholds] = None):
        super().__init__(
            event_queue=event_queue,
            cleanup_config=cleanup_config or CleanupConfig(
                policy=CleanupPolicy.MAX_SIZE,
                max_size=10000,
                check_interval=300
            ),
            memory_thresholds=memory_thresholds
        )
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._last_cleanup = datetime.now()
    
    async def record_metric(self, 
                          metric_name: str,
                          value: float,
                          metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record a metric value"""
        async def _record():
            metric_data = {
                "value": value,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            self._metrics[metric_name].append(metric_data)
            
            # Monitor memory usage
            metrics_size = sys.getsizeof(self._metrics[metric_name]) / (1024 * 1024)
            self._memory_monitor._resource_sizes[f"metrics_{metric_name}"] = metrics_size
            
            # Memory threshold check
            if self._memory_thresholds and metrics_size > self._memory_thresholds.per_resource_max_mb:
                # Try to reduce by removing oldest metrics
                if len(self._metrics[metric_name]) > 10:
                    # Keep only the most recent 75% of metrics
                    keep_count = int(len(self._metrics[metric_name]) * 0.75)
                    self._metrics[metric_name] = deque(list(self._metrics[metric_name])[-keep_count:], maxlen=self._metrics[metric_name].maxlen)
                    
                    # Recalculate size after reduction
                    metrics_size = sys.getsizeof(self._metrics[metric_name]) / (1024 * 1024)
                    self._memory_monitor._resource_sizes[f"metrics_{metric_name}"] = metrics_size
                    
                # Check if still over threshold after reduction
                if metrics_size > self._memory_thresholds.per_resource_max_mb:
                    raise ResourceExhaustionError(
                        resource_id=metric_name,
                        operation="record_metric",
                        current_usage=metrics_size,
                        limit=self._memory_thresholds.per_resource_max_mb,
                        resource_type=ResourceType.METRICS.name,
                        details={"metric_count": len(self._metrics[metric_name])}
                    )
    
            await self.event_bus.emit(
                ResourceEventTypes.METRIC_RECORDED.value,
                {
                    "metric": metric_name,
                    "value": value,
                    "metadata": metadata or {}
                }
            )
            
        await self.protected_operation("write_metrics", _record)

    async def get_metrics(self, 
                         metric_name: str,
                         window: Optional[timedelta] = None,
                         limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get metrics with optional time window and limit"""
        async def _get():
            if metric_name not in self._metrics:
                return []
                
            metrics = list(self._metrics[metric_name])
            
            if window:
                cutoff = datetime.now() - window
                metrics = [
                    m for m in metrics 
                    if datetime.fromisoformat(m["timestamp"]) > cutoff
                ]
                
            if limit:
                metrics = metrics[-limit:]
                
            return metrics
            
        return await self.protected_operation("read_metrics", _get)
        
    async def get_metric_average(self, 
                            metric_name: str,
                            window: Optional[timedelta] = None) -> Optional[float]:
        """Calculate average for a metric over time window"""
        async def _get_average_operation():
            metrics = await self.get_metrics(metric_name, window)
            if not metrics:
                return None
                    
            values = [m["value"] for m in metrics]
            return sum(values) / len(values)
        
        return await self.protected_operation("get_metric_average", _get_average_operation)

    async def get_metric_stats(self,
                            metric_name: str,
                            window: Optional[timedelta] = None) -> Dict[str, float]:
        """Get comprehensive statistics for a metric"""
        async def _get_stats_operation():
            metrics = await self.get_metrics(metric_name, window)
            if not metrics:
                return {}
                    
            values = [m["value"] for m in metrics]
            return {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "count": len(values)
            }
        
        return await self.protected_operation("get_metric_stats", _get_stats_operation)

    async def _cleanup_resources(self, force: bool = False) -> None:
        """Clean up old metrics with enhanced tracking
        
        Args:
            force: If True, perform aggressive cleanup regardless of interval
        """
        now = datetime.now()
        if not force and (now - self._last_cleanup).total_seconds() < self._cleanup_config.check_interval:
            return
                
        self._last_cleanup = now
        
        # Determine TTL to use - default to 24 hours if not specified
        ttl_seconds = getattr(self._cleanup_config, 'ttl_seconds', 86400)
        # Use more aggressive TTL if force=True
        if force and ttl_seconds is not None:
            ttl_seconds = ttl_seconds // 2
        elif force:
            # Default to 12 hours if ttl_seconds is None and force is True
            ttl_seconds = 43200
        
        # Remove metrics for inactive series
        inactive_metrics = []
        for metric_name in self._metrics:
            # Check if there are any metrics in this series
            if not self._metrics[metric_name]:
                inactive_metrics.append(metric_name)
                continue
                    
            latest_metric = self._metrics[metric_name][-1]
            latest_time = datetime.fromisoformat(latest_metric["timestamp"])
            if (now - latest_time).total_seconds() > ttl_seconds:
                inactive_metrics.append(metric_name)
                    
        # Track cleanup statistics
        metrics_cleaned = len(inactive_metrics)
        original_count = len(self._metrics)
        memory_reclaimed = 0
                    
        for metric_name in inactive_metrics:
            # Track memory being reclaimed
            memory_used = self._memory_monitor._resource_sizes.get(f"metrics_{metric_name}", 0)
            memory_reclaimed += memory_used
            
            # Remove the metric
            del self._metrics[metric_name]
            self._memory_monitor._resource_sizes.pop(f"metrics_{metric_name}", None)
                
            # Emit event for cleanup
            await self.event_bus.emit(
                ResourceEventTypes.METRIC_RECORDED.value,
                {
                    "metric": metric_name,
                    "operation": "cleaned_up"
                }
            )
            
        # Report cleanup statistics
        if metrics_cleaned > 0:
            logger.info(f"Cleaned up {metrics_cleaned} metric series, reclaimed {memory_reclaimed:.2f}MB")
            
        await self.event_bus.emit(
            ResourceEventTypes.METRIC_RECORDED.value,
            {
                "metric": "metrics_cleanup",
                "value": metrics_cleaned,
                "memory_reclaimed_mb": memory_reclaimed,
                "remaining_series": len(self._metrics),
                "force": force,
                "timestamp": datetime.now().isoformat()
            }
        )

    async def get_health_status(self) -> HealthStatus:
        """Get metrics system health status"""
        async def _get_health_operation():
            total_series = len(self._metrics)
            total_points = sum(len(series) for series in self._metrics.values())
            total_memory = sum(
                self._memory_monitor._resource_sizes.get(f"metrics_{name}", 0)
                for name in self._metrics
            )
            
            status = "HEALTHY"
            description = "Metrics system operating normally"
            
            if total_series > self._cleanup_config.max_size * 0.8:
                status = "DEGRADED"
                description = "High number of metric series"
                
            return HealthStatus(
                status=status,
                source="metrics_manager",
                description=description,
                metadata={
                    "total_series": total_series,
                    "total_points": total_points,
                    "total_memory_mb": total_memory
                }
            )
        
        return await self.protected_operation("get_health_status", _get_health_operation)