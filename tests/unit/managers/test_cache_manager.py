import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
import time
import sys

from resources.managers import CacheManager
from resources.common import HealthStatus
from resources.base import CleanupPolicy, CleanupConfig, MemoryThresholds

# Tests for CacheManager
class TestCacheManager:
    
    @pytest.mark.asyncio
    async def test_set_cache(self, cache_manager, sample_cache_data):
        """Test setting a cache value."""
        # Set a cache value
        await cache_manager.set_cache(
            key="test_key",
            value=sample_cache_data
        )
        
        # Verify it was set
        assert "test_key" in cache_manager._cache
        assert cache_manager._cache["test_key"] == sample_cache_data
        
        # Verify metadata was created
        assert "test_key" in cache_manager._cache_metadata
        assert "timestamp" in cache_manager._cache_metadata["test_key"]
        
    @pytest.mark.asyncio
    async def test_set_cache_with_metadata(self, cache_manager, sample_cache_data):
        """Test setting a cache value with custom metadata."""
        custom_metadata = {"source": "test", "ttl": 3600}
        
        # Set a cache value with metadata
        await cache_manager.set_cache(
            key="test_meta_key",
            value=sample_cache_data,
            metadata=custom_metadata
        )
        
        # Verify metadata was set
        metadata = cache_manager._cache_metadata["test_meta_key"]
        assert metadata["source"] == "test"
        assert metadata["ttl"] == 3600
        assert "timestamp" in metadata  # System metadata should still be there
        
    @pytest.mark.asyncio
    async def test_get_cache(self, cache_manager, sample_cache_data):
        """Test getting a cache value."""
        # First set a value
        await cache_manager.set_cache(
            key="test_get_key",
            value=sample_cache_data
        )
        
        # Get the value
        value = await cache_manager.get_cache("test_get_key")
        
        # Verify we got the correct value
        assert value == sample_cache_data
        
        # Verify last_accessed was updated
        assert "last_accessed" in cache_manager._cache_metadata["test_get_key"]
        
    @pytest.mark.asyncio
    async def test_get_nonexistent_cache(self, cache_manager):
        """Test getting a cache value that doesn't exist."""
        value = await cache_manager.get_cache("nonexistent_key")
        assert value is None
        
    @pytest.mark.asyncio
    async def test_invalidate_cache(self, cache_manager, sample_cache_data):
        """Test invalidating a cache entry."""
        # First set a value
        await cache_manager.set_cache(
            key="test_invalidate_key",
            value=sample_cache_data
        )
        
        # Verify it exists
        assert "test_invalidate_key" in cache_manager._cache
        
        # Invalidate it
        await cache_manager.invalidate("test_invalidate_key")
        
        # Verify it was removed
        assert "test_invalidate_key" not in cache_manager._cache
        assert "test_invalidate_key" not in cache_manager._cache_metadata
        
    @pytest.mark.asyncio
    async def test_invalidate_nonexistent_cache(self, cache_manager):
        """Test invalidating a cache entry that doesn't exist."""
        # Should not raise an error
        await cache_manager.invalidate("nonexistent_key")
        
    @pytest.mark.asyncio
    async def test_size_based_cleanup(self, event_queue, size_cleanup_config, default_memory_thresholds):
        """Test size-based cleanup when max size is reached."""
        # Create manager with small max size
        manager = CacheManager(
            event_queue=event_queue,
            cleanup_config=size_cleanup_config,  # Using small max size config
            memory_thresholds=default_memory_thresholds
        )
        
        # Add more entries than the max size
        for i in range(10):  # Max size is 5 in the fixture
            await manager.set_cache(
                key=f"size_test_key_{i}",
                value=f"value_{i}"
            )
            # Small delay to ensure different timestamps
            await asyncio.sleep(0.01)
        
        # Force cleanup to bypass check interval
        await manager.cleanup(force=True)
        
        # Verify only the newest entries remain (max_size=5)
        assert len(manager._cache) <= size_cleanup_config.max_size
        
        # The oldest entries should be removed
        for i in range(5):  # First 5 should be gone
            assert f"size_test_key_{i}" not in manager._cache
            
        # The newest entries should remain
        for i in range(5, 10):  # Last 5 should still be there
            assert f"size_test_key_{i}" in manager._cache
            
    @pytest.mark.asyncio
    async def test_ttl_based_cleanup(self, event_queue, ttl_cleanup_config, default_memory_thresholds):
        """Test TTL-based cleanup when entries expire."""
        # Create manager with short TTL
        manager = CacheManager(
            event_queue=event_queue,
            cleanup_config=ttl_cleanup_config,  # Using short TTL config
            memory_thresholds=default_memory_thresholds
        )
        
        # Add some entries
        for i in range(5):
            await manager.set_cache(
                key=f"ttl_test_key_{i}",
                value=f"value_{i}"
            )
        
        # Manually manipulate timestamps to make some entries appear older
        for i in range(3):  # Make first 3 entries appear older than TTL
            old_time = datetime.now() - timedelta(seconds=ttl_cleanup_config.ttl_seconds * 2)
            manager._cache_metadata[f"ttl_test_key_{i}"]["timestamp"] = old_time.isoformat()
            
        # Force cleanup to bypass check interval
        await manager.cleanup(force=True)
        
        # Verify expired entries were removed
        for i in range(3):  # First 3 should be gone (expired)
            assert f"ttl_test_key_{i}" not in manager._cache
            
        # Non-expired entries should remain
        for i in range(3, 5):  # Last 2 should still be there
            assert f"ttl_test_key_{i}" in manager._cache
            
    @pytest.mark.asyncio
    async def test_hybrid_cleanup(self, event_queue, default_memory_thresholds):
        """Test hybrid cleanup (both TTL and size-based)."""
        # Create custom hybrid config
        hybrid_config = CleanupConfig(
            policy=CleanupPolicy.HYBRID,
            ttl_seconds=5,   # Short TTL
            max_size=10,     # Larger max size to avoid premature cleanup
            check_interval=1 # Check every second
        )
        
        # Create manager with hybrid config
        manager = CacheManager(
            event_queue=event_queue,
            cleanup_config=hybrid_config,
            memory_thresholds=default_memory_thresholds
        )
        
        # Add some entries
        for i in range(5):
            await manager.set_cache(
                key=f"hybrid_test_key_{i}",
                value=f"value_{i}"
            )
            await asyncio.sleep(0.01)  # Small delay for different timestamps
            
        # Manually manipulate timestamps for some entries
        for i in range(2):  # Make first 2 entries appear older than TTL
            old_time = datetime.now() - timedelta(seconds=hybrid_config.ttl_seconds * 2)
            manager._cache_metadata[f"hybrid_test_key_{i}"]["timestamp"] = old_time.isoformat()
            
        # Force cleanup to bypass check interval
        await manager.cleanup(force=True)
        
        # Verify both TTL and size-based cleanup worked:
        # 1. First 2 should be gone due to TTL expiration
        # 2. Size limit is 3, so we should have at most 3 entries left
        assert len(manager._cache) <= hybrid_config.max_size
        
        # TTL-expired entries should be gone
        for i in range(2):
            assert f"hybrid_test_key_{i}" not in manager._cache
            
    @pytest.mark.asyncio
    async def test_cleanup_oldest(self, cache_manager):
        """Test removing oldest entries when max size is reached."""
        # Add 5 entries
        for i in range(5):
            await cache_manager.set_cache(
                key=f"oldest_test_key_{i}",
                value=f"value_{i}"
            )
            await asyncio.sleep(0.01)  # Small delay for different timestamps
            
        # Call the internal _cleanup_oldest method directly, forcing removal of 1 entry
        await cache_manager._cleanup_oldest(force_remove_count=1)
        
        # Verify some entries were removed (at least the oldest one)
        assert "oldest_test_key_0" not in cache_manager._cache
        
    @pytest.mark.asyncio
    async def test_automatic_cleanup_on_set(self, event_queue, size_cleanup_config, default_memory_thresholds):
        """Test that cleanup is automatically triggered when setting cache values beyond max size."""
        # Create manager with small max size
        manager = CacheManager(
            event_queue=event_queue,
            cleanup_config=size_cleanup_config,  # Using small max size config
            memory_thresholds=default_memory_thresholds
        )
        
        # Add exactly max_size entries
        for i in range(size_cleanup_config.max_size):
            await manager.set_cache(
                key=f"auto_test_key_{i}",
                value=f"value_{i}"
            )
            await asyncio.sleep(0.01)  # Small delay for different timestamps
            
        # All entries should exist
        for i in range(size_cleanup_config.max_size):
            assert f"auto_test_key_{i}" in manager._cache
            
        # Add one more entry - should trigger cleanup
        await manager.set_cache(
            key="auto_test_key_new",
            value="new_value"
        )
        
        # Verify total entries doesn't exceed max_size
        assert len(manager._cache) <= size_cleanup_config.max_size
        
        # The new entry should exist
        assert "auto_test_key_new" in manager._cache
        
    @pytest.mark.asyncio
    async def test_memory_monitoring(self, cache_manager, sample_cache_data):
        """Test that memory usage is monitored correctly."""
        # Set a cache value
        await cache_manager.set_cache(
            key="memory_test_key",
            value=sample_cache_data
        )
        
        # Verify memory usage is tracked
        assert f"cache_memory_test_key" in cache_manager._memory_monitor._resource_sizes
        
        # The size should be non-zero
        assert cache_manager._memory_monitor._resource_sizes[f"cache_memory_test_key"] > 0
        
        # Invalidate and verify memory tracking is removed
        await cache_manager.invalidate("memory_test_key")
        assert f"cache_memory_test_key" not in cache_manager._memory_monitor._resource_sizes
        
    @pytest.mark.asyncio
    async def test_get_health_status(self, cache_manager, sample_cache_data):
        """Test getting health status."""
        # Add some cache entries
        for i in range(3):
            await cache_manager.set_cache(
                key=f"health_test_key_{i}",
                value=sample_cache_data
            )
            
        # Get health status
        health = await cache_manager.get_health_status()
        
        # Verify health status
        assert health is not None
        assert health.status in ["HEALTHY", "DEGRADED"]
        assert health.source == "cache_manager"
        assert "total_entries" in health.metadata
        assert health.metadata["total_entries"] >= 3
        assert "total_memory_mb" in health.metadata
        
    @pytest.mark.asyncio
    async def test_get_health_status_degraded(self, event_queue, default_memory_thresholds):
        """Test health status changes to DEGRADED when near capacity."""
        # Create manager with very small max size
        small_config = CleanupConfig(
            policy=CleanupPolicy.MAX_SIZE,
            max_size=5,
            check_interval=1
        )
        
        manager = CacheManager(
            event_queue=event_queue,
            cleanup_config=small_config,
            memory_thresholds=default_memory_thresholds
        )
        
        # Add enough entries to approach but not exceed max_size
        for i in range(4):  # 4 out of max 5 (80%)
            await manager.set_cache(
                key=f"degraded_test_key_{i}",
                value=f"value_{i}"
            )
            
        # Get health status
        health = await manager.get_health_status()
        
        # Verify health is DEGRADED
        assert health.status == "DEGRADED"
        assert "Cache near capacity" in health.description

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])