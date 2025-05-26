import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from resources.events import EventQueue, ResourceEventTypes
from resources.base import CleanupConfig, CleanupPolicy, MemoryThresholds
from resources.managers import AgentContextManager, CacheManager, MetricsManager

# Event queue fixture
@pytest_asyncio.fixture
async def event_queue():
    """Create a real event queue for testing."""
    queue = EventQueue()
    await queue.start()
    yield queue
    # Cleanup
    await queue.stop()

# Memory thresholds fixtures
@pytest.fixture
def default_memory_thresholds():
    """Default memory thresholds."""
    return MemoryThresholds(
        warning_percent=70.0,
        critical_percent=85.0,
        per_resource_max_mb=50.0
    )

@pytest.fixture
def custom_memory_thresholds():
    """Custom memory thresholds for testing."""
    return MemoryThresholds(
        warning_percent=50.0,
        critical_percent=75.0,
        per_resource_max_mb=25.0
    )

# Cleanup config fixtures
@pytest.fixture
def default_cleanup_config():
    """Default cleanup config."""
    return CleanupConfig(
        policy=CleanupPolicy.HYBRID,
        ttl_seconds=3600,  # 1 hour
        max_size=100,      # Small max size for testing
        check_interval=1   # Check every second for testing
    )

@pytest.fixture
def ttl_cleanup_config():
    """TTL-based cleanup config."""
    return CleanupConfig(
        policy=CleanupPolicy.TTL,
        ttl_seconds=10,    # Very short TTL for testing
        check_interval=1   # Check every second for testing
    )

@pytest.fixture
def size_cleanup_config():
    """Size-based cleanup config."""
    return CleanupConfig(
        policy=CleanupPolicy.MAX_SIZE,
        max_size=5,        # Very small max size for testing
        check_interval=1   # Check every second for testing
    )

# Manager fixtures
@pytest_asyncio.fixture
async def agent_context_manager(event_queue, default_cleanup_config, default_memory_thresholds):
    """Create an AgentContextManager for testing."""
    manager = AgentContextManager(
        event_queue=event_queue,
        cleanup_config=default_cleanup_config,
        memory_thresholds=default_memory_thresholds
    )
    yield manager
    # Clean up all contexts after test
    for context_id in list(manager._agent_contexts.keys()):
        await manager._cleanup_context(context_id)

@pytest_asyncio.fixture
async def cache_manager(event_queue, default_cleanup_config, default_memory_thresholds):
    """Create a CacheManager for testing."""
    manager = CacheManager(
        event_queue=event_queue,
        cleanup_config=default_cleanup_config,
        memory_thresholds=default_memory_thresholds
    )
    yield manager
    # Clean up all cache entries after test
    for key in list(manager._cache.keys()):
        await manager.invalidate(key)

@pytest_asyncio.fixture
async def metrics_manager(event_queue, default_cleanup_config, default_memory_thresholds):
    """Create a MetricsManager for testing."""
    manager = MetricsManager(
        event_queue=event_queue,
        cleanup_config=default_cleanup_config,
        memory_thresholds=default_memory_thresholds
    )
    yield manager
    # Clean up all metrics after test
    manager._metrics.clear()

# Sample test data fixtures
@pytest.fixture
def sample_agent_schema():
    """Sample schema for agent context testing."""
    return {
        "user_id": "string",
        "conversation": ["string"],
        "preferences": {
            "language": "string",
            "notifications": "boolean"
        }
    }

@pytest.fixture
def sample_agent_data():
    """Sample data for agent context testing."""
    return {
        "user_id": "user123",
        "conversation": ["Hello, how can I help you?"],
        "preferences": {
            "language": "en",
            "notifications": True
        }
    }

@pytest.fixture
def sample_agent_update():
    """Sample data update for agent context testing."""
    return {
        "conversation": ["What can you do for me?"]
    }

@pytest.fixture
def sample_cache_data():
    """Sample data for cache testing."""
    return {"value": "test_value", "nested": {"key": "value"}}

@pytest.fixture
def sample_metrics_data():
    """Sample metrics for testing."""
    return [
        ("response_time", 150.5, {"endpoint": "/api/query"}),
        ("memory_usage", 45.2, {"component": "cache"}),
        ("cpu_usage", 22.8, {"component": "processor"})
    ]