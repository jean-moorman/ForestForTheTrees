import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
import sys
from typing import Dict, Any, Optional
import tracemalloc

# Import the necessary modules from the code
from resources.events import EventQueue, ResourceEventTypes
from resources.base import MemoryThresholds, CleanupConfig, CleanupPolicy
from resources.managers import AgentContext, AgentContextManager, AgentContextType
from resources.errors import ResourceOperationError

tracemalloc.start()

@pytest_asyncio.fixture
async def event_queue():
    """Create a real EventQueue for testing."""
    queue = EventQueue()
    return queue

@pytest_asyncio.fixture
async def memory_thresholds():
    """Create memory thresholds for testing."""
    return MemoryThresholds(
        warning_percent=70,
        critical_percent=90
    )

@pytest_asyncio.fixture
async def cleanup_config():
    """Create cleanup config for testing."""
    return CleanupConfig(
        policy=CleanupPolicy.HYBRID,
        ttl_seconds=300,  # 5 minutes for testing
        max_size=10,      # Small size for testing
        check_interval=60  # 1 minute check interval
    )

@pytest_asyncio.fixture
async def agent_context_manager(event_queue, cleanup_config, memory_thresholds):
    """Create an AgentContextManager for testing."""
    manager = AgentContextManager(
        event_queue=event_queue,
        cleanup_config=cleanup_config,
        memory_thresholds=memory_thresholds
    )
    # Initialize the memory monitor's resource sizes dict
    manager._memory_monitor._resource_sizes = {}
    return manager

# Tests for AgentContext
class TestAgentContext:
    @pytest.mark.asyncio
    async def test_agent_context_init(self):
        """Test AgentContext initialization."""
        context = AgentContext(
            operation_id="test_op_1",
            schema={"type": "test"},
            context_type=AgentContextType.FRESH
        )
        assert context.operation_id == "test_op_1"
        assert context.schema == {"type": "test"}
        assert context.context_type == AgentContextType.FRESH
        assert context.window_size is None
        assert context.conversation == []
        assert context.metadata == {}
        assert context.operation_metadata == {}

    @pytest.mark.asyncio
    async def test_agent_context_update_fresh(self):
        """Test updating a FRESH context."""
        context = AgentContext(
            operation_id="test_op_2",
            schema={"type": "test"},
            context_type=AgentContextType.FRESH
        )
        
        await context.update_data({
            "conversation": [{"role": "user", "content": "Hello"}],
            "extra_field": "value"
        })
        
        assert context.conversation == [{"role": "user", "content": "Hello"}]
        assert context.metadata == {"extra_field": "value"}
        
        # Update again should replace data for FRESH
        await context.update_data({
            "conversation": [{"role": "user", "content": "How are you?"}],
            "new_field": "new_value"
        })
        
        assert context.conversation == [{"role": "user", "content": "How are you?"}]
        assert context.metadata == {"new_field": "new_value"}
        assert "extra_field" not in context.metadata
        
    @pytest.mark.asyncio
    async def test_agent_context_update_persistent(self):
        """Test updating a PERSISTENT context."""
        context = AgentContext(
            operation_id="test_op_3",
            schema={"type": "test"},
            context_type=AgentContextType.PERSISTENT
        )
        
        await context.update_data({
            "conversation": [{"role": "user", "content": "Hello"}],
            "extra_field": "value"
        })
        
        assert context.conversation == [{"role": "user", "content": "Hello"}]
        assert context.metadata == {"extra_field": "value"}
        
        # Update again should append data for PERSISTENT
        await context.update_data({
            "conversation": [{"role": "assistant", "content": "I'm fine"}],
            "new_field": "new_value"
        })
        
        assert context.conversation == [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "I'm fine"}
        ]
        assert context.metadata == {"extra_field": "value", "new_field": "new_value"}
        
    @pytest.mark.asyncio
    async def test_agent_context_update_sliding_window(self):
        """Test updating a SLIDING_WINDOW context."""
        context = AgentContext(
            operation_id="test_op_4",
            schema={"type": "test"},
            context_type=AgentContextType.SLIDING_WINDOW,
            window_size=2
        )
        
        await context.update_data({
            "conversation": [{"role": "user", "content": "Hello"}],
            "extra_field": "value"
        })
        
        assert context.conversation == [{"role": "user", "content": "Hello"}]
        assert context.metadata == {"extra_field": "value"}
        
        # Add more messages to exceed window size
        await context.update_data({
            "conversation": [
                {"role": "assistant", "content": "I'm fine"},
                {"role": "user", "content": "What's your name?"}
            ],
            "new_field": "new_value"
        })
        
        # Should keep only the most recent 2 messages
        assert len(context.conversation) == 2
        assert context.conversation == [
            {"role": "assistant", "content": "I'm fine"},
            {"role": "user", "content": "What's your name?"}
        ]
        assert context.metadata == {"extra_field": "value", "new_field": "new_value"}
        
    @pytest.mark.asyncio
    async def test_agent_context_get_current_data(self):
        """Test getting current data."""
        context = AgentContext(
            operation_id="test_op_5",
            schema={"type": "test"},
            context_type=AgentContextType.FRESH
        )
        
        await context.update_data({
            "conversation": [{"role": "user", "content": "Hello"}],
            "extra_field": "value"
        })
        
        data = context.get_current_data()
        assert len(data) == 1
        assert "conversation" in data[0]
        assert data[0]["conversation"] == [{"role": "user", "content": "Hello"}]
        assert data[0]["extra_field"] == "value"
        
    @pytest.mark.asyncio
    async def test_agent_context_to_dict(self):
        """Test converting context to dictionary."""
        context = AgentContext(
            operation_id="test_op_6",
            schema={"type": "test"},
            context_type=AgentContextType.FRESH
        )
        
        await context.update_data({
            "conversation": [{"role": "user", "content": "Hello"}],
            "extra_field": "value"
        })
        
        context_dict = context.to_dict()
        assert context_dict["operation_id"] == "test_op_6"
        assert context_dict["schema"] == {"type": "test"}
        assert context_dict["context_type"] == "FRESH"
        assert context_dict["window_size"] is None
        assert context_dict["conversation"] == [{"role": "user", "content": "Hello"}]
        assert context_dict["metadata"] == {"extra_field": "value"}
        
    @pytest.mark.asyncio
    async def test_agent_context_from_dict(self):
        """Test creating context from dictionary."""
        data_dict = {
            "operation_id": "test_op_7",
            "schema": {"type": "test"},
            "context_type": "FRESH",
            "window_size": None,
            "conversation": [{"role": "user", "content": "Hello"}],
            "metadata": {"extra_field": "value"},
            "operation_metadata": {"session_id": "123"}
        }
        
        context = AgentContext.from_dict(data_dict)
        assert context.operation_id == "test_op_7"
        assert context.schema == {"type": "test"}
        assert context.context_type == AgentContextType.FRESH
        assert context.window_size is None
        assert context.conversation == [{"role": "user", "content": "Hello"}]
        assert context.metadata == {"extra_field": "value"}
        assert context.operation_metadata == {"session_id": "123"}

    @pytest.mark.asyncio
    async def test_agent_context_debug_state(self):
        """Test getting debug state."""
        context = AgentContext(
            operation_id="test_op_8",
            schema={"type": "test"},
            context_type=AgentContextType.FRESH
        )
        
        await context.update_data({
            "conversation": [{"role": "user", "content": "Hello"}],
            "extra_field": "value"
        })
        
        debug_state = context.debug_state()
        assert debug_state["operation_id"] == "test_op_8"
        assert debug_state["context_type"] == "FRESH"
        assert debug_state["window_size"] is None
        assert debug_state["conversation_length"] == 1
        assert debug_state["metadata_keys"] == ["extra_field"]

# Tests for AgentContextManager
class TestAgentContextManager:
    @pytest.mark.asyncio
    async def test_create_context(self, agent_context_manager):
        """Test creating a context."""
        context = await agent_context_manager.create_context(
            agent_id="agent1",
            operation_id="test_op_9",
            schema={"type": "test"},
            context_type=AgentContextType.FRESH
        )
        
        assert context.operation_id == "test_op_9"
        assert context.schema == {"type": "test"}
        assert context.context_type == AgentContextType.FRESH
        
        # Verify it's in the manager
        stored_context = await agent_context_manager.get_context("agent1")
        assert stored_context is not None
        assert stored_context.operation_id == "test_op_9"
        
    @pytest.mark.asyncio
    async def test_create_duplicate_context(self, agent_context_manager):
        """Test creating a duplicate context."""
        await agent_context_manager.create_context(
            agent_id="agent2",
            operation_id="test_op_10",
            schema={"type": "test"},
            context_type=AgentContextType.PERSISTENT
        )
        
        # Creating another PERSISTENT context with same ID should fail
        with pytest.raises(ResourceOperationError):
            await agent_context_manager.create_context(
                agent_id="agent2",
                operation_id="test_op_11",
                schema={"type": "test"},
                context_type=AgentContextType.PERSISTENT
            )
            
        # But creating a FRESH context with same ID should work
        context = await agent_context_manager.create_context(
            agent_id="agent2",
            operation_id="test_op_12",
            schema={"type": "test"},
            context_type=AgentContextType.FRESH
        )
        assert context.operation_id == "test_op_12"
        
    @pytest.mark.asyncio
    async def test_create_sliding_window_context_reuse(self, agent_context_manager):
        """Test that sliding window contexts can be reused."""
        # Create first sliding window context
        context1 = await agent_context_manager.create_context(
            agent_id="sliding_agent",
            operation_id="sliding_op_1",
            schema={"type": "test"},
            context_type=AgentContextType.SLIDING_WINDOW,
            window_size=5
        )
        
        # Creating another sliding window with same ID should return existing one
        context2 = await agent_context_manager.create_context(
            agent_id="sliding_agent",
            operation_id="sliding_op_2",  # Different operation_id
            schema={"type": "test"},
            context_type=AgentContextType.SLIDING_WINDOW,
            window_size=5
        )
        
        # Should be the same context object
        assert context1 is context2
        assert context2.operation_id == "sliding_op_1"  # Original ID maintained
        
    @pytest.mark.asyncio
    async def test_update_context(self, agent_context_manager):
        """Test updating a context."""
        await agent_context_manager.create_context(
            agent_id="agent3",
            operation_id="test_op_13",
            schema={"type": "test"},
            context_type=AgentContextType.PERSISTENT
        )
        
        await agent_context_manager.update_context(
            context_id="agent3",
            data_updates={
                "conversation": [{"role": "user", "content": "Hello"}],
                "extra_field": "value"
            },
            metadata_updates={"session_id": "456"}
        )
        
        context = await agent_context_manager.get_context("agent3")
        assert context.conversation == [{"role": "user", "content": "Hello"}]
        assert context.metadata == {"extra_field": "value"}
        assert context.operation_metadata == {"session_id": "456"}
        
    @pytest.mark.asyncio
    async def test_update_nonexistent_context(self, agent_context_manager):
        """Test updating a nonexistent context."""
        with pytest.raises(ResourceOperationError):
            await agent_context_manager.update_context(
                context_id="nonexistent",
                data_updates={"field": "value"}
            )
            
    @pytest.mark.asyncio
    async def test_cleanup(self, agent_context_manager):
        """Test cleaning up expired contexts."""
        # Create a context
        await agent_context_manager.create_context(
            agent_id="agent4",
            operation_id="test_op_14",
            schema={"type": "test"},
            context_type=AgentContextType.FRESH
        )
        
        # Modify the start_time to make it expired
        context = await agent_context_manager.get_context("agent4")
        context.start_time = datetime.now() - timedelta(seconds=600)  # 10 minutes ago
        
        # Run cleanup
        await agent_context_manager.cleanup()
        
        # Context should be gone
        context = await agent_context_manager.get_context("agent4")
        assert context is None
        
    @pytest.mark.asyncio
    async def test_cleanup(self, agent_context_manager):
        """Test cleaning up expired contexts."""
        # Create a context
        await agent_context_manager.create_context(
            agent_id="agent4",
            operation_id="test_op_14",
            schema={"type": "test"},
            context_type=AgentContextType.FRESH
        )
         
        # Force cleanup to run bypassing the check interval
        await agent_context_manager.cleanup(force=True)
        
        # Context should be gone
        context = await agent_context_manager.get_context("agent4")
        assert context is None
        
    @pytest.mark.asyncio
    async def test_get_health_status(self, agent_context_manager):
        """Test getting health status."""
        # Create some contexts
        for i in range(3):
            await agent_context_manager.create_context(
                agent_id=f"health_agent_{i}",
                operation_id=f"test_op_health_{i}",
                schema={"type": "test"},
                context_type=AgentContextType.FRESH
            )
        
        # Get health status
        health_status = await agent_context_manager.get_health_status()
        
        assert health_status.status == "HEALTHY"
        assert health_status.source == "agent_context_manager"
        assert "Agent context manager operating normally" in health_status.description
        assert health_status.metadata["total_contexts"] == 3
        
        # Create more contexts to reach close to the limit
        for i in range(3, 9):
            await agent_context_manager.create_context(
                agent_id=f"health_agent_{i}",
                operation_id=f"test_op_health_{i}",
                schema={"type": "test"},
                context_type=AgentContextType.FRESH
            )
        
        # Get health status again
        health_status = await agent_context_manager.get_health_status()
        
        assert health_status.status == "DEGRADED"
        assert "High context count" in health_status.description
        assert health_status.metadata["total_contexts"] == 9
        
    @pytest.mark.asyncio
    async def test_memory_monitoring(self, agent_context_manager):
        """Test that memory is being monitored."""
        await agent_context_manager.create_context(
            agent_id="memory_agent",
            operation_id="test_op_memory",
            schema={"type": "test"},
            context_type=AgentContextType.FRESH
        )
        
        # Update with some data to increase memory usage
        await agent_context_manager.update_context(
            context_id="memory_agent",
            data_updates={
                "conversation": [{"role": "user", "content": "Hello" * 1000}],  # Large content
                "extra_field": "value" * 1000  # Large value
            }
        )
        
        # Check that memory size is tracked
        assert "context_memory_agent" in agent_context_manager._memory_monitor._resource_sizes
        assert agent_context_manager._memory_monitor._resource_sizes["context_memory_agent"] > 0

    @pytest.mark.asyncio
    async def test_concurrent_context_updates(self, agent_context_manager):
        """Test concurrent updates to the same context."""
        # Create a context
        await agent_context_manager.create_context(
            agent_id="concurrent_agent",
            operation_id="concurrent_op",
            schema={"type": "test"},
            context_type=AgentContextType.PERSISTENT
        )
        
        # Define update tasks
        async def update_task(index):
            await agent_context_manager.update_context(
                context_id="concurrent_agent",
                data_updates={
                    "conversation": [{"role": "user", "content": f"Message {index}"}],
                    f"field_{index}": f"value_{index}"
                }
            )
        
        # Run multiple updates concurrently
        tasks = [update_task(i) for i in range(5)]
        await asyncio.gather(*tasks)
        
        # Check context after updates
        context = await agent_context_manager.get_context("concurrent_agent")
        assert len(context.conversation) == 5  # All messages should be there
        for i in range(5):
            assert f"field_{i}" in context.metadata
            assert context.metadata[f"field_{i}"] == f"value_{i}"

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])