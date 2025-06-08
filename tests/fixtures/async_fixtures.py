"""
Async-friendly test fixtures for Water Agent testing.

This module provides fixtures that properly handle asyncio event loops
and initialization patterns to avoid common async testing issues.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import logging
from typing import Dict, Any, Optional
import uuid

from resources.state import StateManager
from resources.events import EventQueue
from resources.water_agent.context_manager import WaterAgentContextManager


# Configure logging to reduce noise in tests
logging.getLogger("resources.monitoring.memory").setLevel(logging.WARNING)
logging.getLogger("resources.monitoring.circuit_breakers").setLevel(logging.WARNING)
logging.getLogger("interfaces.agent.metrics").setLevel(logging.WARNING)


@pytest.fixture(scope="function")
def event_loop():
    """Create a new event loop for each test function."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def minimal_event_queue():
    """Create a minimal async-friendly event queue."""
    event_queue = AsyncMock()
    event_queue.emit = AsyncMock()
    event_queue.subscribe = AsyncMock()
    event_queue.start = AsyncMock()
    event_queue.stop = AsyncMock()
    return event_queue


@pytest.fixture
async def minimal_state_manager():
    """Create a minimal async-friendly state manager."""
    state_manager = AsyncMock(spec=StateManager)
    state_manager.get_state = AsyncMock(return_value=None)
    state_manager.set_state = AsyncMock(return_value=True)
    state_manager.delete_state = AsyncMock(return_value=True)
    state_manager.find_keys = AsyncMock(return_value=[])
    return state_manager


@pytest.fixture
async def coordination_infrastructure(minimal_event_queue, minimal_state_manager):
    """Create basic coordination infrastructure for tests."""
    return {
        "event_queue": minimal_event_queue,
        "state_manager": minimal_state_manager
    }


@pytest.fixture
async def lightweight_agent_interface():
    """Create a lightweight agent interface for testing."""
    interface = MagicMock()
    interface.agent_id = "test_agent_interface"
    interface.process_with_validation = AsyncMock()
    interface._event_queue = AsyncMock()
    interface._state_manager = AsyncMock()
    interface._context_manager = AsyncMock()
    interface._cache_manager = AsyncMock()
    interface._metrics_manager = AsyncMock()
    interface._error_handler = AsyncMock()
    interface._memory_monitor = AsyncMock()
    return interface


@pytest.fixture
async def minimal_water_context_manager(minimal_state_manager):
    """Create a minimal water agent context manager."""
    context_manager = WaterAgentContextManager(state_manager=minimal_state_manager)
    context_manager._emit_event = AsyncMock()
    return context_manager


class MockLightweightAgent:
    """Lightweight mock agent for testing."""
    
    def __init__(self, agent_id: str, agent_type: str = "generic"):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.__class__.__name__ = f"Mock{agent_type.title()}Agent"
        self.clarification_count = 0
        
    async def clarify(self, question: str) -> str:
        """Provide a simple clarification response."""
        self.clarification_count += 1
        return f"Agent {self.agent_id} clarification for: {question[:50]}..."
        
    def get_performance_summary(self) -> Dict[str, int]:
        """Get performance metrics."""
        return {
            "clarification_count": self.clarification_count,
            "agent_id": self.agent_id
        }


@pytest.fixture
def lightweight_agent_factory():
    """Factory for creating lightweight test agents."""
    def _create_agent(agent_id: str, agent_type: str = "generic") -> MockLightweightAgent:
        return MockLightweightAgent(agent_id, agent_type)
    return _create_agent


@pytest.fixture
async def mock_coordination_scenario():
    """Create a mock coordination scenario for testing."""
    return {
        "coordination_id": f"test_{uuid.uuid4().hex[:8]}",
        "first_agent_output": "First agent output for coordination testing",
        "second_agent_output": "Second agent output that may have misunderstandings",
        "expected_misunderstandings": [
            {
                "id": "test_misunderstanding_1",
                "description": "Test terminology conflict",
                "severity": "MEDIUM"
            }
        ],
        "expected_questions": {
            "first_agent": ["Clarify terminology usage"],
            "second_agent": ["Confirm understanding of requirements"]
        }
    }


class AsyncContextManager:
    """Helper for managing async contexts in tests."""
    
    def __init__(self):
        self.contexts = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup any contexts
        for context in self.contexts:
            if hasattr(context, 'cleanup'):
                await context.cleanup()
        self.contexts.clear()
        
    def add_context(self, context):
        """Add a context to be cleaned up."""
        self.contexts.append(context)
        return context


@pytest.fixture
async def async_context_manager():
    """Provide an async context manager for test cleanup."""
    async with AsyncContextManager() as manager:
        yield manager


@pytest.fixture
def suppress_asyncio_warnings():
    """Suppress common asyncio warnings in tests."""
    import warnings
    warnings.filterwarnings("ignore", message=".*was never awaited.*")
    warnings.filterwarnings("ignore", message=".*Task was destroyed but it is pending.*")
    warnings.filterwarnings("ignore", message=".*coroutine.*was never awaited.*")
    yield
    warnings.resetwarnings()