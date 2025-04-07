from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Set
from collections import deque, defaultdict
from enum import Enum, auto
import asyncio
import sys
import logging
import threading

from resources.common import (
    ResourceState, 
    ResourceType,
    InterfaceState,
    HealthStatus
)
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
    CleanupPolicy,
    DEFAULT_CACHE_CIRCUIT_CONFIG,
    DEFAULT_AGENT_CIRCUIT_CONFIG
)

logger = logging.getLogger(__name__)

class AgentContextType(Enum):
    FRESH = auto()
    PERSISTENT = auto()
    SLIDING_WINDOW = auto()

class AgentContext:
    def __init__(
        self,
        operation_id: str,
        schema: Dict[str, Any],
        context_type: AgentContextType = AgentContextType.FRESH,
        window_size: Optional[int] = None
    ):
        self.operation_id = operation_id
        self.start_time = datetime.now()
        self.schema = schema
        self.context_type = context_type
        self.window_size = window_size if context_type == AgentContextType.SLIDING_WINDOW else None
        # Store conversations as a simple list of messages
        self.conversation: List[Dict[str, Any]] = []
        # Store other context data separately
        self.metadata: Dict[str, Any] = {}
        self.operation_metadata: Dict[str, Any] = {}

    async def update_data(self, new_data: Dict[str, Any]) -> None:
        """Update context data with simplified conversation handling"""
        logger.debug(f"Updating context {self.operation_id} of type {self.context_type.name}")
        
        # Extract conversation messages if present
        new_messages = new_data.pop("conversation", [])
        
        # Handle different context types
        if self.context_type == AgentContextType.FRESH:
            # For FRESH, just replace both conversation and metadata
            self.conversation = new_messages
            self.metadata = new_data
            return
            
        # For PERSISTENT and SLIDING_WINDOW, append messages and update metadata
        self.conversation.extend(new_messages)
        self.metadata.update(new_data)
        
        # Apply window size limit if needed
        if self.context_type == AgentContextType.SLIDING_WINDOW and self.window_size:
            if len(self.conversation) > self.window_size:
                # Keep only most recent messages within window size
                self.conversation = self.conversation[-self.window_size:]
        
        logger.debug(f"Context updated. Conversation size: {len(self.conversation)}")

    def get_current_data(self) -> Dict[str, Any]:
        """Get the current context data in a format compatible with existing code"""
        result = dict(self.metadata)
        if self.conversation:
            result["conversation"] = self.conversation
        return [result]

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for storage"""
        return {
            "operation_id": self.operation_id,
            "start_time": self.start_time.isoformat(),
            "schema": self.schema,
            "conversation": self.conversation,
            "metadata": self.metadata,
            "window_size": self.window_size,
            "context_type": self.context_type.name,
            "operation_metadata": self.operation_metadata
        }
    
    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'AgentContext':
        """Reconstruct context from dictionary storage"""
        context = cls(
            operation_id=data_dict["operation_id"],
            schema=data_dict["schema"],
            context_type=AgentContextType[data_dict["context_type"]],
            window_size=data_dict.get("window_size")
        )
        
        context.conversation = data_dict.get("conversation", [])
        context.metadata = data_dict.get("metadata", {})
        
        # Restore metadata
        context.operation_metadata = data_dict.get("operation_metadata", {})
        
        return context

    def debug_state(self) -> Dict[str, Any]:
        """Return a debug-friendly representation of current state"""
        return {
            "operation_id": self.operation_id,
            "context_type": self.context_type.name,
            "window_size": self.window_size,
            "conversation_length": len(self.conversation),
            "metadata_keys": list(self.metadata.keys()),
            "start_time": self.start_time.isoformat()
        }

class AgentContextManager(BaseManager):
    """Manages agent contexts with versioning and memory monitoring"""
    def __init__(self, 
                 event_queue: EventQueue,
                 cleanup_config: Optional[CleanupConfig] = None,
                 memory_thresholds: Optional[MemoryThresholds] = None):
        super().__init__(
            event_queue=event_queue,
            circuit_breaker_config=DEFAULT_AGENT_CIRCUIT_CONFIG,
            cleanup_config=cleanup_config or CleanupConfig(
                policy=CleanupPolicy.HYBRID,
                ttl_seconds=7200,  # 2 hour default TTL
                max_size=500       # Default max contexts
            ),
            memory_thresholds=memory_thresholds
        )
        self._agent_contexts: Dict[str, AgentContext] = {}
        self._context_locks: Dict[str, asyncio.Lock] = {}
        self._last_cleanup = datetime.now()
    
    async def create_context(self, 
                        agent_id: str,
                        operation_id: str, 
                        schema: Dict[str, Any],
                        context_type: AgentContextType = AgentContextType.FRESH,
                        window_size: Optional[int] = None) -> AgentContext:
        """Create new agent context"""
        async def _create():
            # For FRESH type, we don't check for existing context
            if context_type != AgentContextType.FRESH:
                if agent_id in self._agent_contexts:
                    if context_type == AgentContextType.SLIDING_WINDOW:
                        # Return existing sliding window context if it exists
                        existing_context = self._agent_contexts.get(agent_id)
                        if existing_context:
                            return existing_context
                    raise ResourceOperationError(
                        message=f"Agent context already exists: {agent_id}",
                        resource_id=agent_id,
                        severity=ErrorSeverity.TRANSIENT,
                        operation="create_context",
                        recovery_strategy="use_existing"
                    )
            
            context = AgentContext(
                operation_id=operation_id,
                schema=schema,
                context_type=context_type,
                window_size=window_size
            )
            
            self._agent_contexts[agent_id] = context
            self._context_locks[agent_id] = asyncio.Lock()
            
            # Monitor memory usage with correct key format
            context_size = (sys.getsizeof(context.conversation) + sys.getsizeof(context.metadata)) / (1024 * 1024)
            await self._memory_monitor.track_resource(
                f"context_{agent_id}", 
                context_size,
                agent_id
            )
            
            if self._memory_thresholds and context_size > self._memory_thresholds.per_resource_max_mb:
                raise ResourceExhaustionError(
                    resource_id=agent_id,
                    operation="create_context",
                    current_usage=context_size,
                    limit=self._memory_thresholds.per_resource_max_mb,
                    resource_type=ResourceType.AGENT_CONTEXT.name,
                    details={"context_type": context_type.name}
                )

            await self._event_queue.emit(
                ResourceEventTypes.AGENT_CONTEXT_UPDATED.value,
                {
                    "agent_id": agent_id,
                    "operation": "created",
                    "context_id": operation_id
                }
            )
            
            return context
            
        return await self.protected_operation("create_context", _create)

    async def get_context(self, context_id: str) -> Optional[AgentContext]:
        """Get agent context by ID"""
        async def _get():
            context = self._agent_contexts.get(context_id)
            if context:
                size = (sys.getsizeof(context.conversation) + sys.getsizeof(context.metadata)) / (1024 * 1024)
                self._memory_monitor._resource_sizes[f"context_{context_id}"] = size
            return context
            
        return await self.protected_operation("get_context", _get)

    async def update_context(self, 
                        context_id: str,
                        data_updates: Dict[str, Any],
                        metadata_updates: Optional[Dict[str, Any]] = None) -> None:
        """Update context data and metadata"""
        async def _update():
            context = self._agent_contexts.get(context_id)
            if not context:
                raise ResourceOperationError(
                    message=f"Context not found: {context_id}",
                    resource_id=context_id,
                    severity=ErrorSeverity.DEGRADED, 
                    operation="update_context"
                )
                
            async with self._context_locks[context_id]:
                # Use the context's update_data method instead of directly updating
                await context.update_data(data_updates)
                if metadata_updates:
                    context.operation_metadata.update(metadata_updates)
                    
                size = (sys.getsizeof(context.conversation) + sys.getsizeof(context.metadata)) / (1024 * 1024)
                self._memory_monitor._resource_sizes[f"context_{context_id}"] = size
                
                # memory threshold check
                if self._memory_thresholds and size > self._memory_thresholds.per_resource_max_mb:
                    raise ResourceExhaustionError(
                        resource_id=context_id,
                        operation="update_context",
                        current_usage=size,
                        limit=self._memory_thresholds.per_resource_max_mb,
                        resource_type=ResourceType.AGENT_CONTEXT.name,
                        details={"operation": "update", "conversation_size": len(context.conversation)}
                    )

        await self.protected_operation("update_context", _update)

    async def _cleanup_resources(self, force: bool = False) -> None:
        """Implement specific resource cleanup for agent contexts
        
        Args:
            force: If True, ignore the check interval and force cleanup of all contexts
        """
        if not self._cleanup_config:
            return
                
        now = datetime.now()
        if not force and (now - self._last_cleanup).seconds < self._cleanup_config.check_interval:
            return
                
        self._last_cleanup = now
        
        expired_contexts = set()
        for agent_id, context in self._agent_contexts.items():
            if force or (now - context.start_time).seconds > self._cleanup_config.ttl_seconds:
                expired_contexts.add(agent_id)
                    
        for agent_id in expired_contexts:
            try:
                await self._cleanup_context(agent_id)
                logger.info(f"Cleaned up agent context: {agent_id}")
            except Exception as e:
                logger.error(f"Error cleaning up context {agent_id}: {e}")
        
        # Report cleanup statistics
        await self._event_queue.emit(
            ResourceEventTypes.METRIC_RECORDED.value,
            {
                "metric": "agent_context_cleanup",
                "value": len(expired_contexts),
                "total_contexts": len(self._agent_contexts),
                "timestamp": datetime.now().isoformat()
            }
        )

    async def _cleanup_context(self, context_id: str) -> None:
        """Clean up a specific context"""
        try:
            if context_id in self._agent_contexts:
                del self._agent_contexts[context_id]
            if context_id in self._context_locks:
                del self._context_locks[context_id]
            self._memory_monitor._resource_sizes.pop(f"context_{context_id}", None)
            
            await self._event_queue.emit(
                ResourceEventTypes.AGENT_CONTEXT_UPDATED.value,
                {
                    "context_id": context_id,
                    "operation": "cleaned_up"
                }
            )
        except Exception as e:
            raise ResourceOperationError(
                message=f"Failed to clean up context {context_id}: {str(e)}",
                resource_id=context_id,
                severity=ErrorSeverity.DEGRADED,
                operation="cleanup_context"
            )

    async def get_health_status(self) -> HealthStatus:
        """Get health status of agent context management"""
        async def _get_health_operation():
            total_contexts = len(self._agent_contexts)
            total_memory = sum(
                self._memory_monitor._resource_sizes.get(f"context_{cid}", 0)
                for cid in self._agent_contexts
            )
            
            status = "HEALTHY"
            description = "Agent context manager operating normally"
            
            if total_contexts > self._cleanup_config.max_size * 0.8:
                status = "DEGRADED"
                description = "High context count, cleanup recommended"
                
            return HealthStatus(
                status=status,
                source="agent_context_manager",
                description=description,
                metadata={
                    "total_contexts": total_contexts,
                    "total_memory_mb": total_memory
                }
            )
        
        return await self.protected_operation("get_health_status", _get_health_operation)
    
class CacheManager(BaseManager):
    """Manages cache operations with memory monitoring and cleanup"""
    def __init__(self, 
                 event_queue: EventQueue,
                 cleanup_config: Optional[CleanupConfig] = None,
                 memory_thresholds: Optional[MemoryThresholds] = None):
        super().__init__(
            event_queue=event_queue,
            circuit_breaker_config=DEFAULT_CACHE_CIRCUIT_CONFIG,
            cleanup_config=cleanup_config or CleanupConfig(
                policy=CleanupPolicy.MAX_SIZE,
                max_size=10000,  # Default max cache entries
                check_interval=60  # Check every minute
            ),
            memory_thresholds=memory_thresholds or MemoryThresholds(
                warning_percent=70.0,
                critical_percent=85.0,
                per_resource_max_mb=50.0
            )
        )
        self._cache: Dict[str, Any] = {}
        self._cache_metadata: Dict[str, Dict[str, Any]] = {}
        self._last_cleanup = datetime.now()
    
    async def set_cache(self, 
                       key: str,
                       value: Any,
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """Set cache value with metadata"""
        async def _set():
            # Check size limit
            if len(self._cache) >= self._cleanup_config.max_size:
                await self._cleanup_oldest()

            self._cache[key] = value
            self._cache_metadata[key] = {
                "timestamp": datetime.now().isoformat(),
                "type": ResourceType.CACHE.name,
                **(metadata or {})
            }
            
            # Monitor memory usage
            value_size = sys.getsizeof(value) / (1024 * 1024)
            self._memory_monitor._resource_sizes[f"cache_{key}"] = value_size
            
            # Memory threshold check
            if self._memory_thresholds and value_size > self._memory_thresholds.per_resource_max_mb:
                # Try to clean up first before failing
                await self._cleanup_oldest()
                
                # Recheck size after cleanup
                if value_size > self._memory_thresholds.per_resource_max_mb:
                    raise ResourceExhaustionError(
                        resource_id=key,
                        operation="set_cache",
                        current_usage=value_size,
                        limit=self._memory_thresholds.per_resource_max_mb,
                        resource_type=ResourceType.CACHE.name,
                        details={"value_type": type(value).__name__}
                    )
    
            await self._event_queue.emit(
                ResourceEventTypes.CACHE_UPDATED.value,
                {
                    "key": key,
                    "operation": "set",
                    "metadata": self._cache_metadata[key]
                }
            )
                
        await self.protected_operation("set_cache", _set)
   
    async def get_cache(self, key: str) -> Optional[Any]:
        """Get cached value"""
        async def _get():
            value = self._cache.get(key)
            if value is not None:
                # Update access timestamp
                self._cache_metadata[key]["last_accessed"] = datetime.now().isoformat()
            return value
            
        return await self.protected_operation("get_cache", _get)
        
    async def invalidate(self, key: str) -> None:
        """Invalidate cache entry"""
        async def _invalidate():
            self._cache.pop(key, None)
            self._cache_metadata.pop(key, None)
            self._memory_monitor._resource_sizes.pop(f"cache_{key}", None)
            
            await self._event_queue.emit(
                ResourceEventTypes.CACHE_UPDATED.value,
                {
                    "key": key,
                    "operation": "invalidated"
                }
            )
            
        await self.protected_operation("invalidate_cache", _invalidate)

    async def _cleanup_oldest(self) -> None:
        """Remove oldest cache entries"""
        try:
            if not self._cache:
                return
                    
            # Sort by timestamp and remove oldest
            sorted_entries = sorted(
                self._cache_metadata.items(),
                key=lambda x: x[1]["timestamp"]
            )
            
            # Remove oldest 10% of entries
            num_to_remove = max(1, len(sorted_entries) // 10)
            for key, _ in sorted_entries[:num_to_remove]:
                await self.invalidate(key)
        except Exception as e:
            # Convert generic exception to ResourceOperationError
            raise ResourceOperationError(
                message=f"Failed to clean up oldest cache entries: {str(e)}",
                resource_id="cache_manager",
                severity=ErrorSeverity.DEGRADED,
                operation="cleanup_oldest"
            )

    async def _cleanup_expired(self) -> None:
        """Remove expired cache entries based on TTL"""
        try:
            now = datetime.now()
            expired_keys = []
            
            # Only proceed if TTL is set
            if not hasattr(self._cleanup_config, 'ttl_seconds') or self._cleanup_config.ttl_seconds <= 0:
                return
                    
            for key, metadata in self._cache_metadata.items():
                timestamp = datetime.fromisoformat(metadata.get("timestamp", now.isoformat()))
                if (now - timestamp).total_seconds() > self._cleanup_config.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                await self.invalidate(key)
        except Exception as e:
            # Convert generic exception to ResourceOperationError
            raise ResourceOperationError(
                message=f"Failed to clean up expired cache entries: {str(e)}",
                resource_id="cache_manager",
                severity=ErrorSeverity.DEGRADED,
                operation="cleanup_expired"
            )
    
    async def _cleanup_resources(self, force: bool = False) -> None:
        """Implement cache-specific resource cleanup
        
        Args:
            force: If True, perform aggressive cleanup regardless of policy/interval
        """
        now = datetime.now()
        if not force and (now - self._last_cleanup).seconds < self._cleanup_config.check_interval:
            return
                
        self._last_cleanup = now
        
        cleaned_items = 0
        
        # Size-based cleanup
        if force or self._cleanup_config.policy in [CleanupPolicy.MAX_SIZE, CleanupPolicy.HYBRID]:
            if len(self._cache) > self._cleanup_config.max_size * 0.8: # Start cleaning at 80% fill
                old_count = len(self._cache)
                await self._cleanup_oldest()
                cleaned_items += old_count - len(self._cache)
        
        # TTL-based cleanup
        if force or self._cleanup_config.policy in [CleanupPolicy.TTL, CleanupPolicy.HYBRID]:
            old_count = len(self._cache)
            await self._cleanup_expired()
            cleaned_items += old_count - len(self._cache)
            
        # Report cleanup statistics
        await self._event_queue.emit(
            ResourceEventTypes.METRIC_RECORDED.value,
            {
                "metric": "cache_cleanup",
                "value": cleaned_items,
                "remaining_items": len(self._cache),
                "force": force,
                "timestamp": datetime.now().isoformat()
            }
        )

    async def get_health_status(self) -> HealthStatus:
        """Get cache health status"""
        async def _get_health_operation():
            total_entries = len(self._cache)
            total_memory = sum(
                self._memory_monitor._resource_sizes.get(f"cache_{key}", 0)
                for key in self._cache
            )
            
            status = "HEALTHY"
            description = "Cache operating normally"
            
            if total_entries > self._cleanup_config.max_size * 0.8:
                status = "DEGRADED"
                description = "Cache near capacity"
                
            return HealthStatus(
                status=status,
                source="cache_manager",
                description=description,
                metadata={
                    "total_entries": total_entries,
                    "total_memory_mb": total_memory
                }
            )
        
        return await self.protected_operation("get_health_status", _get_health_operation)

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
    
            await self._event_queue.emit(
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
        if not force and (now - self._last_cleanup).seconds < self._cleanup_config.check_interval:
            return
                
        self._last_cleanup = now
        
        # Determine TTL to use - default to 24 hours if not specified
        ttl_seconds = getattr(self._cleanup_config, 'ttl_seconds', 86400)
        # Use more aggressive TTL if force=True
        if force:
            ttl_seconds = ttl_seconds // 2
        
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
            await self._event_queue.emit(
                ResourceEventTypes.METRIC_RECORDED.value,
                {
                    "metric": metric_name,
                    "operation": "cleaned_up"
                }
            )
            
        # Report cleanup statistics
        if metrics_cleaned > 0:
            logger.info(f"Cleaned up {metrics_cleaned} metric series, reclaimed {memory_reclaimed:.2f}MB")
            
        await self._event_queue.emit(
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


class CircuitBreakerRegistry:
    """Centralized registry for circuit breakers with relationship tracking and cascading failures."""
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls, event_queue=None):
        """Singleton implementation with thread safety."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CircuitBreakerRegistry, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
            
    def __init__(self, event_queue=None):
        """Initialize circuit breaker registry."""
        # Only initialize once
        if self._initialized:
            return
            
        with self._lock:
            if not self._initialized:
                # Store event queue
                self._event_queue = event_queue
                
                # Circuit breaker storage
                self._circuit_breakers = {}
                self._relationships = {}  # parent -> [children]
                self._reverse_dependencies = {}  # child -> [parents]
                
                # Circuit breaker metadata
                self._circuit_metadata = {}
                
                # Circuit state changes
                self._state_history = {}
                
                # Task tracking for cleanup
                self._tasks = set()
                
                # Track registry in EventLoopManager for proper cleanup
                from resources.events import EventLoopManager
                EventLoopManager.register_resource("circuit_breaker_registry", self)
                
                self._initialized = True
                logger.debug("CircuitBreakerRegistry initialized")
    
    async def register_circuit_breaker(self, name: str, circuit, parent=None):
        """Register a circuit breaker with optional dependency on parent.
        
        Args:
            name: Unique identifier for the circuit breaker
            circuit: The CircuitBreaker instance
            parent: Optional parent circuit breaker name that this one depends on
        """
        # Import here to avoid circular imports
        from resources.monitoring import CircuitBreaker
        with self._lock:
            # Register circuit breaker
            self._circuit_breakers[name] = circuit
            
            # Store metadata
            self._circuit_metadata[name] = {
                "registered_time": datetime.now().isoformat(),
                "trip_count": 0,
                "last_trip": None,
                "last_reset": None,
                "component_type": circuit.__class__.__name__ if hasattr(circuit, "__class__") else "unknown"
            }
            
            # Set up parent relationship if specified
            if parent:
                # Add to parent's children
                if parent not in self._relationships:
                    self._relationships[parent] = []
                if name not in self._relationships[parent]:
                    self._relationships[parent].append(name)
                
                # Add to reverse dependency mapping
                if name not in self._reverse_dependencies:
                    self._reverse_dependencies[name] = []
                if parent not in self._reverse_dependencies[name]:
                    self._reverse_dependencies[name].append(parent)
            
            # Subscribe to state changes from the circuit breaker
            if hasattr(circuit, 'add_state_change_listener') and callable(circuit.add_state_change_listener):
                circuit.add_state_change_listener(self._handle_circuit_state_change)
            
            logger.info(f"Registered circuit breaker {name}" + (f" with parent {parent}" if parent else ""))
            
            # If event queue is available, emit registration event
            if self._event_queue:
                try:
                    await self._event_queue.emit(
                        ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
                        {
                            "component": "circuit_breaker_registry",
                            "status": "circuit_registered",
                            "circuit": name,
                            "parent": parent,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                except Exception as e:
                    logger.error(f"Error emitting circuit registration event: {e}")
    
    async def _handle_circuit_state_change(self, circuit_name, old_state, new_state):
        """Handle circuit breaker state changes with cascading trip support."""
        # Store state change in history
        if circuit_name not in self._state_history:
            self._state_history[circuit_name] = []
            
        self._state_history[circuit_name].append({
            "timestamp": datetime.now().isoformat(),
            "old_state": old_state,
            "new_state": new_state
        })
        
        # Limit history size
        if len(self._state_history[circuit_name]) > 100:
            self._state_history[circuit_name] = self._state_history[circuit_name][-100:]
        
        # Update metadata for trip events
        if new_state == "OPEN":
            if circuit_name in self._circuit_metadata:
                self._circuit_metadata[circuit_name]["trip_count"] += 1
                self._circuit_metadata[circuit_name]["last_trip"] = datetime.now().isoformat()
        
        # For reset events
        if old_state == "OPEN" and new_state == "CLOSED":
            if circuit_name in self._circuit_metadata:
                self._circuit_metadata[circuit_name]["last_reset"] = datetime.now().isoformat()
        
        # Emit event for state change
        if self._event_queue:
            try:
                await self._event_queue.emit(
                    ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
                    {
                        "component": "circuit_breaker",
                        "circuit": circuit_name,
                        "old_state": old_state,
                        "new_state": new_state,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Error emitting circuit state change event: {e}")
        
        # Handle cascading trips: when a parent circuit trips, trip all children
        if new_state == "OPEN" and circuit_name in self._relationships:
            children = self._relationships[circuit_name]
            if children:
                logger.warning(f"Cascading trip from {circuit_name} to children: {children}")
                
                # Trip all child circuits
                for child_name in children:
                    child_circuit = self._circuit_breakers.get(child_name)
                    if child_circuit and hasattr(child_circuit, 'trip') and callable(child_circuit.trip):
                        try:
                            # Create task to trip the child circuit
                            task = asyncio.create_task(
                                child_circuit.trip(f"Cascading trip from parent {circuit_name}")
                            )
                            
                            # Track the task for cleanup
                            self._tasks.add(task)
                            task.add_done_callback(lambda t: self._tasks.discard(t))
                            
                        except Exception as e:
                            logger.error(f"Error cascading trip to {child_name}: {e}")
        
        # For recovery, we don't cascade automatically - each circuit follows its own recovery timeout
    
    async def get_circuit_status(self, name=None):
        """Get status of one or all circuit breakers.
        
        Args:
            name: Optional circuit breaker name, or None for all circuits
            
        Returns:
            Dictionary with circuit status information
        """
        if name:
            # Return status for specific circuit
            circuit = self._circuit_breakers.get(name)
            if not circuit:
                return {"error": f"Circuit {name} not found"}
                
            return {
                "name": name,
                "state": circuit.state.name if hasattr(circuit, 'state') else "UNKNOWN",
                "failure_count": circuit.failure_count if hasattr(circuit, 'failure_count') else 0,
                "metadata": self._circuit_metadata.get(name, {}),
                "parents": self._reverse_dependencies.get(name, []),
                "children": self._relationships.get(name, [])
            }
        else:
            # Return status for all circuits
            result = {}
            for circuit_name, circuit in self._circuit_breakers.items():
                result[circuit_name] = {
                    "state": circuit.state.name if hasattr(circuit, 'state') else "UNKNOWN",
                    "failure_count": circuit.failure_count if hasattr(circuit, 'failure_count') else 0,
                    "metadata": self._circuit_metadata.get(circuit_name, {}),
                    "parents": self._reverse_dependencies.get(circuit_name, []),
                    "children": self._relationships.get(circuit_name, [])
                }
            return result
    
    async def reset_all_circuits(self):
        """Reset all circuit breakers to CLOSED state."""
        reset_count = 0
        
        for name, circuit in self._circuit_breakers.items():
            if hasattr(circuit, 'reset') and callable(circuit.reset):
                try:
                    await circuit.reset()
                    reset_count += 1
                    
                    # Update metadata
                    if name in self._circuit_metadata:
                        self._circuit_metadata[name]["last_reset"] = datetime.now().isoformat()
                        
                except Exception as e:
                    logger.error(f"Error resetting circuit {name}: {e}")
        
        # Emit event for reset operation
        if self._event_queue:
            try:
                await self._event_queue.emit(
                    ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
                    {
                        "component": "circuit_breaker_registry",
                        "operation": "reset_all",
                        "reset_count": reset_count,
                        "total_circuits": len(self._circuit_breakers),
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Error emitting circuit reset event: {e}")
                
        return {"reset_count": reset_count, "total_circuits": len(self._circuit_breakers)}
    
    async def stop(self):
        """Clean up resources."""
        # Cancel any pending tasks
        for task in list(self._tasks):
            if not task.done():
                task.cancel()
                
        # Wait for tasks to complete with timeout
        if self._tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._tasks, return_exceptions=True),
                    timeout=2.0
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for circuit breaker tasks to cancel")
        
        # Unregister from EventLoopManager
        from resources.events import EventLoopManager
        EventLoopManager.unregister_resource("circuit_breaker_registry")
        
        logger.info("CircuitBreakerRegistry stopped")

class ResourceCoordinator:
    """Centralized coordinator for all resource managers with dependency-aware initialization and shutdown."""
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls, event_queue=None):
        """Singleton implementation with thread safety."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ResourceCoordinator, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, event_queue):
        """Initialize the resource coordinator."""
        # Only initialize once
        if self._initialized:
            return
            
        with self._lock:
            if not self._initialized:
                self.event_queue = event_queue
                self._managers = {}
                self._dependencies = {}
                self._initialization_order = []
                self._shutdown_order = []
                self._initialized = False
                self._shutting_down = False
                
                # Enhanced dependency tracking
                self._dependency_graph = {}  # For visualization and cycle detection
                self._optional_dependencies = {}  # Dependencies that can be missing
                self._required_dependencies = {}  # Dependencies that must be present
                
                # Component metadata for debugging
                self._component_metadata = {}
                
                # Circuit breaker registry integration
                self._circuit_registry = CircuitBreakerRegistry(event_queue)
                
                # Initialization state tracking
                self._initialization_state = {}  # manager_id -> state (not_started, in_progress, complete, failed)
                
                # Register with EventLoopManager for proper lifecycle management
                from resources.events import EventLoopManager
                EventLoopManager.register_resource("resource_coordinator", self)
                
                self._initialized = True
                logger.debug("ResourceCoordinator initialized")
        
    def register_manager(self, manager_id, manager, dependencies=None, optional_dependencies=None):
        """Register a resource manager with the coordinator with enhanced dependency tracking.
        
        Args:
            manager_id: Unique identifier for the manager
            manager: The manager instance
            dependencies: List of required manager IDs this manager depends on
            optional_dependencies: List of optional manager IDs this manager can use if available
        """
        self._managers[manager_id] = manager
        
        # Store specific dependency types
        self._required_dependencies[manager_id] = dependencies or []
        self._optional_dependencies[manager_id] = optional_dependencies or []
        
        # Combine all dependencies for backward compatibility
        all_dependencies = list(set((dependencies or []) + (optional_dependencies or [])))
        self._dependencies[manager_id] = all_dependencies
        
        # Update dependency graph for visualization
        self._dependency_graph[manager_id] = {
            "required": self._required_dependencies[manager_id],
            "optional": self._optional_dependencies[manager_id]
        }
        
        # Store component metadata
        self._component_metadata[manager_id] = {
            "class": manager.__class__.__name__,
            "register_time": datetime.now().isoformat(),
            "initialized": False,
            "init_time": None,
            "shutdown_time": None
        }
        
        # Default initialization state
        self._initialization_state[manager_id] = "not_started"
        
        # If we've already initialized, initialize this manager now
        if self._initialized:
            async def _delayed_init():
                # Small delay to allow event loop to process other events
                await asyncio.sleep(0.1)
                await self._initialize_manager(manager_id)
                
            asyncio.create_task(_delayed_init())
            
        logger.debug(f"Registered manager {manager_id} with ResourceCoordinator")
        
    async def initialize_all(self):
        """Initialize all registered managers in dependency order with enhanced error handling."""
        if self._initialized:
            logger.warning("ResourceCoordinator already initialized")
            return
            
        logger.info("Starting initialization of all resource managers")
        
        # Calculate initialization order based on dependencies
        try:
            self._initialization_order = self._calculate_initialization_order()
            # Shutdown order is reverse of initialization
            self._shutdown_order = list(reversed(self._initialization_order))
        except Exception as e:
            logger.error(f"Error calculating initialization order: {e}")
            await self.event_queue.emit(
                ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                {
                    "resource_id": "resource_coordinator",
                    "operation": "calculate_initialization_order",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                priority="high"
            )
            raise
        
        # Emit initialization started event
        await self.event_queue.emit(
            ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
            {
                "resource_id": "resource_coordinator",
                "state": "initialization_started",
                "manager_count": len(self._managers),
                "initialization_order": self._initialization_order
            }
        )
        
        # Initialize managers in order with proper error handling
        initialization_results = []
        for manager_id in self._initialization_order:
            # Skip if any required dependency failed
            skip_manager = False
            for dep_id in self._required_dependencies.get(manager_id, []):
                if dep_id in initialization_results and not initialization_results[dep_id]:
                    logger.warning(f"Skipping {manager_id} due to failed dependency {dep_id}")
                    self._initialization_state[manager_id] = "skipped_dep_failure"
                    initialization_results.append((manager_id, False))
                    skip_manager = True
                    break
                    
            if skip_manager:
                continue
                
            # Initialize this manager
            self._initialization_state[manager_id] = "in_progress"
            result = await self._initialize_manager(manager_id)
            self._initialization_state[manager_id] = "complete" if result else "failed"
            initialization_results.append((manager_id, result))
            
            # Update metadata
            self._component_metadata[manager_id]["initialized"] = result
            self._component_metadata[manager_id]["init_time"] = datetime.now().isoformat()
            
            # On failure of critical component, consider stopping initialization
            if not result and manager_id in self._get_critical_managers():
                logger.error(f"Critical manager {manager_id} failed to initialize - stopping initialization")
                
                # Emit critical failure event
                await self.event_queue.emit(
                    ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                    {
                        "resource_id": "resource_coordinator",
                        "operation": "initialize_all",
                        "error": f"Critical manager {manager_id} failed to initialize",
                        "severity": "FATAL",
                        "timestamp": datetime.now().isoformat()
                    },
                    priority="high"
                )
                
                # Stop initializing further managers
                break
        
        # Calculate success rate
        success_count = sum(1 for _, result in initialization_results if result)
        total_count = len(initialization_results)
        
        # Update initialization state
        self._initialized = success_count > 0  # Consider initialized if at least one manager succeeded
        
        # Emit final initialization event
        await self.event_queue.emit(
            ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
            {
                "resource_id": "resource_coordinator",
                "state": "initialized" if self._initialized else "initialization_failed",
                "success_count": success_count,
                "total_count": total_count,
                "success_rate": success_count / total_count if total_count > 0 else 0
            }
        )
        
        logger.info(f"Resource initialization completed: {success_count}/{total_count} managers initialized successfully")
        
    def _get_critical_managers(self):
        """Get the list of critical managers that must initialize successfully."""
        # This could be enhanced with configuration, but for now consider these core components critical
        return ["state_manager", "event_queue", "context_manager"]
        
    async def _initialize_manager(self, manager_id):
        """Initialize a specific manager with proper error handling and dependency verification."""
        manager = self._managers.get(manager_id)
        if not manager:
            logger.error(f"Cannot initialize unknown manager: {manager_id}")
            return False
            
        # Check if required dependencies are initialized
        for dep_id in self._required_dependencies.get(manager_id, []):
            if dep_id not in self._managers:
                logger.error(f"Required dependency {dep_id} for {manager_id} is not registered")
                return False
                
            # Check if dependency was successfully initialized
            if self._initialization_state.get(dep_id) != "complete":
                logger.error(f"Required dependency {dep_id} for {manager_id} is not initialized")
                return False
                
        # Emit initialization event
        try:
            await self.event_queue.emit(
                ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                {
                    "resource_id": manager_id,
                    "state": "initializing"
                }
            )
        except Exception as e:
            logger.error(f"Error emitting initialization event for {manager_id}: {e}")
            
        try:
            # Create initialization correlation ID for tracking
            import uuid
            correlation_id = f"init_{manager_id}_{str(uuid.uuid4())[:8]}"
            
            # Check if manager has start/initialize method
            if hasattr(manager, 'start') and callable(manager.start):
                logger.debug(f"Starting manager {manager_id} (correlation_id: {correlation_id})")
                await manager.start()
            elif hasattr(manager, 'initialize') and callable(manager.initialize):
                logger.debug(f"Initializing manager {manager_id} (correlation_id: {correlation_id})")
                await manager.initialize()
            else:
                logger.debug(f"Manager {manager_id} has no start/initialize method (correlation_id: {correlation_id})")
                
            # Register manager's circuit breaker with registry if it exists
            if hasattr(manager, '_circuit_breaker') and manager._circuit_breaker:
                try:
                    # Import here to avoid circular imports
                    from resources.monitoring import CircuitBreaker
                    
                    # Determine parent circuit if any
                    parent_circuit = None
                    for dep_id in self._required_dependencies.get(manager_id, []):
                        # Consider first dependency as parent for circuit cascading
                        parent_circuit = dep_id
                        break
                        
                    # Register with circuit breaker registry
                    await self._circuit_registry.register_circuit_breaker(
                        manager_id, 
                        manager._circuit_breaker,
                        parent=parent_circuit
                    )
                except Exception as e:
                    logger.error(f"Error registering circuit breaker for {manager_id}: {e}")
                
            # Emit successful initialization event
            await self.event_queue.emit(
                ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                {
                    "resource_id": manager_id,
                    "state": "initialized",
                    "correlation_id": correlation_id
                }
            )
            
            # Update component metadata
            self._component_metadata[manager_id]["initialized"] = True
            self._component_metadata[manager_id]["init_time"] = datetime.now().isoformat()
            self._component_metadata[manager_id]["correlation_id"] = correlation_id
            
            return True
        except Exception as e:
            logger.error(f"Error initializing manager {manager_id}: {e}")
            
            # Update component metadata
            self._component_metadata[manager_id]["initialized"] = False
            self._component_metadata[manager_id]["init_error"] = str(e)
            self._component_metadata[manager_id]["init_time"] = datetime.now().isoformat()
            
            # Emit error event
            await self.event_queue.emit(
                ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                {
                    "resource_id": manager_id,
                    "operation": "initialize",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Also emit state change for consistency
            await self.event_queue.emit(
                ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                {
                    "resource_id": manager_id,
                    "state": "initialization_failed",
                    "error": str(e)
                }
            )
            
            return False
            
    def _calculate_initialization_order(self):
        """Calculate initialization order based on dependencies using topological sort with cycle detection."""
        # Implementation of Kahn's algorithm with cycle detection
        
        # Build an adjacency list and in-degree count
        adjacency = {node: [] for node in self._managers}
        in_degree = {node: 0 for node in self._managers}
        
        # Fill adjacency list and in-degree count
        for node, deps in self._required_dependencies.items():
            for dep in deps:
                if dep in self._managers:  # Only consider registered dependencies
                    adjacency[dep].append(node)
                    in_degree[node] += 1
        
        # Start with nodes that have no dependencies
        queue = [node for node, count in in_degree.items() if count == 0]
        result = []
        
        # Process nodes with in-degree of 0
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # Reduce in-degree of neighbors
            for neighbor in adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles - if we haven't included all nodes, there must be a cycle
        if len(result) != len(self._managers):
            # Find the cycle to provide better error information
            cycle = self._find_dependency_cycle()
            if cycle:
                cycle_str = " -> ".join(cycle)
                logger.error(f"Circular dependency detected: {cycle_str}")
                raise ValueError(f"Circular dependency detected: {cycle_str}")
            else:
                unprocessed = set(self._managers.keys()) - set(result)
                logger.error(f"Unable to determine initialization order, unprocessed nodes: {unprocessed}")
                # Add remaining nodes to maintain backward compatibility
                result.extend(unprocessed)
        
        return result
    
    def _find_dependency_cycle(self):
        """Find and return a dependency cycle if one exists."""
        visited = set()
        path = []
        path_set = set()
        
        def dfs(node):
            # Already completely processed this node, no cycles here
            if node in visited:
                return None
                
            # Check if we're revisiting a node in the current path (cycle found)
            if node in path_set:
                # Return the cycle
                cycle_start = path.index(node)
                return path[cycle_start:] + [node]
                
            # Add node to current path
            path.append(node)
            path_set.add(node)
            
            # Process dependencies
            for dep in self._required_dependencies.get(node, []):
                if dep in self._managers:  # Only consider registered deps
                    cycle = dfs(dep)
                    if cycle:
                        return cycle
            
            # Remove from current path as we're done with this branch
            path.pop()
            path_set.remove(node)
            
            # Mark as fully visited (all paths explored)
            visited.add(node)
            
            # No cycle found
            return None
            
        # Check from each unvisited node
        for node in self._managers:
            if node not in visited:
                cycle = dfs(node)
                if cycle:
                    return cycle
                    
        return None
        
    async def shutdown(self):
        """Shut down all resource managers in reverse initialization order with enhanced reliability."""
        if self._shutting_down:
            logger.warning("ResourceCoordinator already shutting down")
            return
            
        self._shutting_down = True
        logger.info("Starting orderly shutdown of all resource managers")
        
        # Create shutdown correlation ID for tracking
        import uuid
        shutdown_id = f"shutdown_{str(uuid.uuid4())[:8]}"
        
        # Emit shutdown started event
        try:
            await self.event_queue.emit(
                ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                {
                    "resource_id": "resource_coordinator",
                    "state": "shutting_down",
                    "manager_count": len(self._managers),
                    "correlation_id": shutdown_id
                },
                priority="high"
            )
        except Exception as e:
            logger.error(f"Error emitting shutdown event: {e}")
        
        # If no explicit shutdown order is defined, use reverse initialization order
        if not self._shutdown_order:
            # If initialization order isn't defined either, use dependency-based calculation
            if not self._initialization_order:
                try:
                    self._initialization_order = self._calculate_initialization_order()
                except Exception as e:
                    logger.error(f"Error calculating initialization order for shutdown: {e}")
                    # Fall back to arbitrary order (all managers)
                    self._initialization_order = list(self._managers.keys())
                    
            # Reverse for shutdown
            self._shutdown_order = list(reversed(self._initialization_order))
        
        # Shutdown in reverse order
        shutdown_results = []
        for manager_id in self._shutdown_order:
            # Skip managers that were never initialized
            if self._initialization_state.get(manager_id) not in ["complete", "in_progress"]:
                logger.debug(f"Skipping shutdown of uninitialized manager {manager_id}")
                continue
                
            result = await self._shutdown_manager(manager_id)
            shutdown_results.append((manager_id, result))
            
            # Update metadata
            self._component_metadata[manager_id]["shutdown_time"] = datetime.now().isoformat()
            self._component_metadata[manager_id]["shutdown_success"] = result
        
        # Report results
        success_count = sum(1 for _, result in shutdown_results if result)
        total_count = len(shutdown_results)
        logger.info(f"Resource shutdown completed: {success_count}/{total_count} successful")
        
        # Emit final event even if event queue is shutting down
        try:
            await self.event_queue.emit(
                ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                {
                    "resource_id": "resource_coordinator",
                    "state": "shutdown_complete",
                    "success_count": success_count,
                    "total_count": total_count,
                    "correlation_id": shutdown_id
                },
                priority="high"
            )
        except Exception as e:
            logger.error(f"Error emitting final shutdown event: {e}")
        
        # Clean up registry
        try:
            # Reset all flags
            self._shutting_down = False
            self._initialized = False
            
            # Unregister from EventLoopManager
            from resources.events import EventLoopManager
            EventLoopManager.unregister_resource("resource_coordinator")
            
            # Explicitly stop circuit breaker registry
            if hasattr(self, '_circuit_registry'):
                await self._circuit_registry.stop()
                
        except Exception as e:
            logger.error(f"Error during final coordinator cleanup: {e}")
        
    async def _shutdown_manager(self, manager_id):
        """Shutdown a specific manager with timeout and error handling."""
        manager = self._managers.get(manager_id)
        if not manager:
            logger.warning(f"Cannot shutdown unknown manager: {manager_id}")
            return False
            
        try:
            logger.debug(f"Shutting down manager {manager_id}")
            
            # Emit shutdown event
            try:
                await self.event_queue.emit(
                    ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                    {
                        "resource_id": manager_id,
                        "state": "shutting_down"
                    }
                )
            except Exception as e:
                logger.error(f"Error emitting shutdown event for {manager_id}: {e}")
            
            # Check for stop/shutdown method with timeout
            if hasattr(manager, 'stop') and callable(manager.stop):
                try:
                    await asyncio.wait_for(manager.stop(), timeout=10.0)
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout shutting down manager {manager_id}")
                except Exception as e:
                    logger.error(f"Error shutting down manager {manager_id}: {e}")
                    return False
            elif hasattr(manager, 'shutdown') and callable(manager.shutdown):
                try:
                    await asyncio.wait_for(manager.shutdown(), timeout=10.0)
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout shutting down manager {manager_id}")
                except Exception as e:
                    logger.error(f"Error shutting down manager {manager_id}: {e}")
                    return False
            else:
                # No shutdown method available
                logger.debug(f"Manager {manager_id} has no stop/shutdown method")
                
            # Try to emit completion event, but may fail if event queue is already down
            try:
                await self.event_queue.emit(
                    ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                    {
                        "resource_id": manager_id,
                        "state": "shutdown_complete"
                    }
                )
            except Exception as e:
                logger.debug(f"Could not emit shutdown complete event for {manager_id}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error shutting down manager {manager_id}: {e}")
            return False
            
    def get_manager(self, manager_id):
        """Get a specific manager by ID."""
        return self._managers.get(manager_id)
        
    def get_all_managers(self):
        """Get all registered managers."""
        return dict(self._managers)
        
    def get_status(self):
        """Get detailed status of all managers with enhanced information."""
        # Basic status
        status = {
            "initialized": self._initialized,
            "shutting_down": self._shutting_down,
            "managers": list(self._managers.keys()),
            "initialization_order": self._initialization_order,
            "shutdown_order": self._shutdown_order,
            "manager_count": len(self._managers)
        }
        
        # Add dependency information
        status["dependencies"] = self._dependency_graph
        
        # Add component states
        status["component_states"] = {
            manager_id: {
                "initialization_state": self._initialization_state.get(manager_id, "unknown"),
                "metadata": self._component_metadata.get(manager_id, {})
            }
            for manager_id in self._managers
        }
        
        # Add circuit breaker information if available
        if hasattr(self, '_circuit_registry'):
            try:
                # Get synchronous status info for now
                circuit_status = {
                    name: {
                        "state": circuit.state.name if hasattr(circuit, 'state') else "UNKNOWN",
                        "parents": self._circuit_registry._reverse_dependencies.get(name, []),
                        "children": self._circuit_registry._relationships.get(name, [])
                    }
                    for name, circuit in self._circuit_registry._circuit_breakers.items()
                }
                status["circuit_breakers"] = circuit_status
            except Exception as e:
                logger.error(f"Error getting circuit breaker status: {e}")
                status["circuit_breakers"] = {"error": str(e)}
        
        return status

# Export the managers
__all__ = [
    'AgentContextManager',
    'CacheManager',
    'MetricsManager',
    'ResourceCoordinator',
    'CircuitBreakerRegistry'
]