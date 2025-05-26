"""
Cache management for agent interfaces in the FFTT system.
"""

import asyncio
from datetime import datetime
import logging
import sys
import time
from typing import Dict, Any, Optional

from resources import (
    EventQueue,
    CacheManager,
    MetricsManager,
    MemoryMonitor
)
from ..errors import ResourceError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InterfaceCache:
    """
    Interface cache using dedicated CacheManager with improved error handling and metrics.
    """
    def __init__(self, event_queue: EventQueue, interface_id: str, cache_manager: CacheManager, memory_monitor: MemoryMonitor):
        """
        Initialize the interface cache.
        
        Args:
            event_queue: Queue for event handling
            interface_id: ID of the interface
            cache_manager: Manager for caching
            memory_monitor: Monitor for memory usage
        """
        self._cache_manager = cache_manager
        self._interface_id = interface_id
        self._cache_prefix = f"interface_cache:{interface_id}:"
        self._metrics_manager = MetricsManager(event_queue)
        self._memory_monitor = memory_monitor
        self._event_queue = event_queue
        
        # Ensure component is registered with memory monitor
        asyncio.create_task(self._ensure_registered())
        
    async def _ensure_registered(self) -> None:
        """Ensure the component is registered with memory monitor."""
        if not self._memory_monitor:
            logger.warning("Memory monitor is None, cannot register cache")
            return
            
        try:
            # Check if memory_monitor has register_component and call it appropriately
            if hasattr(self._memory_monitor, 'register_component'):
                if asyncio.iscoroutinefunction(self._memory_monitor.register_component):
                    await self._memory_monitor.register_component(self._interface_id)
                else:
                    self._memory_monitor.register_component(self._interface_id)
            else:
                logger.warning("Memory monitor does not have register_component method")
        except Exception as e:
            logger.warning(f"Failed to register cache with memory monitor: {str(e)}")
            
    async def set_cache(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Enhanced cache setting with better error handling, retries and memory monitoring.
        
        Args:
            key: Cache key
            value: Value to cache
            metadata: Additional metadata
            
        Raises:
            ResourceError: If cache setting fails
        """
        start_time = time.monotonic()
        cache_key = f"{self._interface_id}:{key}"
        
        # Enhanced metadata
        if metadata is None:
            metadata = {}
            
        metadata.update({
            "key": key,
            "interface_id": self._interface_id,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # Enhanced memory monitoring with prevention
            size_bytes = sys.getsizeof(value)
            size_mb = size_bytes / (1024 * 1024)
            
            # Define memory thresholds
            warning_threshold_mb = 10  # 10MB
            critical_threshold_mb = 50  # 50MB
            max_allowed_mb = 100       # 100MB
            
            # Check against maximum allowed size to prevent memory issues
            if size_mb > max_allowed_mb:
                logger.error(f"Cache value for {cache_key} exceeds maximum allowed size: {size_mb:.2f}MB > {max_allowed_mb}MB")
                try:
                    from resources.events import ResourceEventTypes
                    await self._event_queue.emit(
                        ResourceEventTypes.ERROR_OCCURRED.value,
                        {
                            "interface_id": self._interface_id,
                            "error": f"Cache value exceeds maximum allowed size: {size_mb:.2f}MB > {max_allowed_mb}MB",
                            "error_type": "MemoryLimitExceeded",
                            "key": key,
                            "size_mb": size_mb,
                            "max_allowed_mb": max_allowed_mb,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to emit error event: {str(e)}")
                    
                # Return early without setting cache to prevent memory issues
                raise ResourceError(f"Cache value exceeds maximum allowed size: {size_mb:.2f}MB > {max_allowed_mb}MB")
            
            # Warning for large values
            if size_mb > warning_threshold_mb:
                alert_type = "warning" if size_mb <= critical_threshold_mb else "critical"
                logger.warning(f"Cache value for {cache_key} is large: {size_mb:.2f}MB ({alert_type})")
                
                try:
                    from resources.events import ResourceEventTypes
                    await self._event_queue.emit(
                        ResourceEventTypes.RESOURCE_ALERT_CREATED.value,
                        {
                            "interface_id": self._interface_id,
                            "alert_type": f"large_cache_value_{alert_type}",
                            "severity": alert_type.upper(),
                            "message": f"Large cache value detected: {size_mb:.2f}MB",
                            "size_mb": size_mb,
                            "key": key,
                            "warning_threshold_mb": warning_threshold_mb,
                            "critical_threshold_mb": critical_threshold_mb,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to emit alert event: {str(e)}")
            
            # Track memory with enhanced error recovery
            try:
                # Get current memory usage before adding new resource
                total_memory_mb = 0
                try:
                    import psutil
                    process = psutil.Process()
                    total_memory_mb = process.memory_info().rss / (1024 * 1024)
                except ImportError:
                    # Fallback if psutil not available
                    pass
                
                # Track the resource
                await self._memory_monitor.track_resource(
                    f"cache:{key}", 
                    size_mb,
                    self._interface_id
                )
                
                # If total memory is high, trigger cleanup proactively
                if total_memory_mb > 0 and total_memory_mb > 500:  # 500MB threshold
                    logger.warning(f"High memory usage detected: {total_memory_mb:.2f}MB. Triggering proactive cleanup.")
                    
                    # Emit memory pressure event
                    try:
                        from resources.events import ResourceEventTypes
                        await self._event_queue.emit(
                            ResourceEventTypes.RESOURCE_ALERT_CREATED.value,
                            {
                                "interface_id": self._interface_id,
                                "alert_type": "memory_pressure",
                                "severity": "WARNING",
                                "message": f"High memory usage: {total_memory_mb:.2f}MB",
                                "total_memory_mb": total_memory_mb,
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                    except Exception:
                        pass  # Ignore event emission failures
                    
                    # Trigger cache cleanup (asynchronously so it doesn't block)
                    asyncio.create_task(self._trigger_memory_cleanup())
                
            except Exception as e:
                logger.warning(f"Failed to track memory for cache {key}: {str(e)}")
                
            # Call set_cache_with_retries to handle actual cache setting with retries
            await self.set_cache_with_retries(cache_key, value, metadata, size_mb, start_time)
                
        except Exception as e:
            # Record failure metrics
            if metadata is None:
                metadata = {}
            await self._metrics_manager.record_metric(
                f"cache:{self._interface_id}:set_failures",
                1.0,
                metadata={**metadata, "error": str(e)}
            )
            raise
    
    async def _trigger_memory_cleanup(self) -> None:
        """Trigger memory cleanup when memory pressure is detected."""
        try:
            # Use cache manager's cleanup if available
            if hasattr(self._cache_manager, 'cleanup') and callable(self._cache_manager.cleanup):
                if asyncio.iscoroutinefunction(self._cache_manager.cleanup):
                    await self._cache_manager.cleanup(force=True)
                else:
                    self._cache_manager.cleanup(force=True)
                    
            # Log cleanup success
            logger.info(f"Completed proactive memory cleanup for {self._interface_id}")
            
        except Exception as e:
            logger.error(f"Failed to perform memory cleanup: {str(e)}")
            
    async def set_cache_with_retries(self, cache_key, value, metadata, size_mb, start_time):
        """
        Set cache with retries.
        
        Args:
            cache_key: Full cache key
            value: Value to cache
            metadata: Additional metadata
            size_mb: Size in MB
            start_time: Start time for metrics
            
        Raises:
            ResourceError: If all retries fail
        """
        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                # Set cache with circuit breaker protection
                await self._cache_manager.set_cache(cache_key, value, metadata)
                
                # Record success metrics
                duration = time.monotonic() - start_time
                await self._metrics_manager.record_metric(
                    f"cache:{self._interface_id}:set_duration",
                    duration,
                    metadata={**metadata, "size_mb": size_mb, "duration_seconds": duration}
                )
                
                await self._metrics_manager.record_metric(
                    f"cache:{self._interface_id}:set_success",
                    1.0,
                    metadata={**metadata, "size_mb": size_mb}
                )
                
                return  # Success
            except Exception as e:
                retry_count += 1
                last_error = e
                logger.warning(f"Cache set retry {retry_count}/{max_retries} for {cache_key}: {str(e)}")
                
                if retry_count >= max_retries:
                    break
                
                # Exponential backoff
                await asyncio.sleep(0.1 * (2 ** retry_count))
        
        # If we get here, all retries failed
        logger.error(f"Cache set failed after {max_retries} retries for {cache_key}: {str(last_error)}")
        await self._metrics_manager.record_metric(
            f"cache:{self._interface_id}:set_failures",
            1.0,
            metadata={**metadata, "error": str(last_error), "retries": max_retries}
        )
        
        raise ResourceError(f"Failed to set cache after {max_retries} retries: {str(last_error)}")

    async def get_cache(self, key: str) -> Optional[Any]:
        """
        Get cache with enhanced error handling, retries and metrics.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
            
        Raises:
            ResourceError: If all retries fail
        """
        start_time = time.monotonic()
        hit = False
        cache_key = f"{self._interface_id}:{key}"
        
        try:
            # Get with retries
            max_retries = 3
            retry_count = 0
            last_error = None
            
            while retry_count < max_retries:
                try:
                    # Get with circuit breaker protection
                    value = await self._cache_manager.get_cache(cache_key)
                    
                    hit = value is not None
                    
                    # Record metrics
                    duration = time.monotonic() - start_time
                    await self._metrics_manager.record_metric(
                        f"cache:{self._interface_id}:get_duration",
                        duration,
                        metadata={"key": key, "hit": hit, "duration_seconds": duration}
                    )
                    
                    # Record cache hit/miss
                    await self._metrics_manager.record_metric(
                        f"cache:{self._interface_id}:hits",
                        1.0 if hit else 0.0,
                        metadata={"key": key}
                    )
                    
                    return value
                    
                except Exception as e:
                    retry_count += 1
                    last_error = e
                    logger.warning(f"Cache get retry {retry_count}/{max_retries} for {cache_key}: {str(e)}")
                    
                    if retry_count >= max_retries:
                        break
                        
                    # Exponential backoff
                    await asyncio.sleep(0.1 * (2 ** retry_count))
            
            # If we get here, all retries failed
            logger.error(f"Cache get failed after {max_retries} retries for {cache_key}: {str(last_error)}")
            await self._metrics_manager.record_metric(
                f"cache:{self._interface_id}:get_failures",
                1.0,
                metadata={"key": key, "error": str(last_error), "retries": max_retries}
            )
            
            raise ResourceError(f"Failed to get cache after {max_retries} retries: {str(last_error)}")
            
        except Exception as e:
            await self._metrics_manager.record_metric(
                f"cache:{self._interface_id}:get_failures",
                1.0,
                metadata={"key": key, "error": str(e)}
            )
            raise
        
    async def invalidate(self, key: str) -> None:
        """
        Invalidate cache entry with enhanced error handling.
        
        Args:
            key: Cache key
            
        Raises:
            ResourceError: If invalidation fails
        """
        cache_key = f"{self._interface_id}:{key}"
        
        try:
            await self._cache_manager.invalidate(cache_key)
            
            # Record successful invalidation
            await self._metrics_manager.record_metric(
                f"cache:{self._interface_id}:invalidations",
                1.0,
                metadata={"key": key}
            )
            
            # Clean up memory tracking
            try:
                await self._memory_monitor.untrack_resource(f"cache:{key}", self._interface_id)
            except Exception as e:
                logger.warning(f"Failed to untrack memory for invalidated cache {key}: {str(e)}")
                
        except Exception as e:
            logger.error(f"Failed to invalidate cache for {key}: {str(e)}")
            
            # Record failed invalidation
            await self._metrics_manager.record_metric(
                f"cache:{self._interface_id}:invalidation_failures",
                1.0,
                metadata={"key": key, "error": str(e)}
            )
            
            raise ResourceError(f"Failed to invalidate cache: {str(e)}")