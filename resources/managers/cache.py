from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Set
import asyncio
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
    CleanupPolicy,
    DEFAULT_CACHE_CIRCUIT_CONFIG
)

logger = logging.getLogger(__name__)

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