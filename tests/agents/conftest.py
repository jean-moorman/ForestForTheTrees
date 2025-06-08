"""
Pytest fixtures for Water Agent tests.

This module provides shared fixtures for the Water Agent test suite.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json

from resources.state import StateManager
from resources.events import EventQueue
from resources.water_agent import WaterAgentCoordinator
from resources.water_agent.context_manager import WaterAgentContextManager
from interfaces.agent.interface import AgentInterface


@pytest.fixture
def event_queue():
    """Create a real EventQueue for testing."""
    queue = EventQueue()
    queue.emit = AsyncMock()
    return queue


@pytest.fixture
def state_manager():
    """Create a mock StateManager for testing."""
    state_manager = AsyncMock(spec=StateManager)
    state_manager.get_state = AsyncMock(return_value=None)
    state_manager.set_state = AsyncMock(return_value=True)
    state_manager.delete_state = AsyncMock(return_value=True)
    state_manager.find_keys = AsyncMock(return_value=[])
    return state_manager


@pytest.fixture
def llm_client():
    """Create a mock LLM client for testing."""
    llm_client = MagicMock()
    llm_client.generate_text = AsyncMock(return_value=MagicMock(text="{}"))
    return llm_client


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    agent = MagicMock(spec=AgentInterface)
    agent.agent_id = "test_agent"
    agent.__class__.__name__ = "TestAgent"
    agent.clarify = AsyncMock(return_value="Clarification response")
    return agent


@pytest.fixture
def mock_output_pairs():
    """Create sample output pairs for testing coordination."""
    return {
        "simple": (
            "First agent output for testing",
            "Second agent output for testing"
        ),
        "with_misunderstanding": (
            "First agent output with an ambiguous term X",
            "Second agent output interpreting X differently"
        ),
        "json": (
            json.dumps({"content": "First agent JSON output", "metadata": {"key": "value"}}),
            json.dumps({"content": "Second agent JSON output", "metadata": {"key": "value"}})
        ),
        "complex": (
            "First agent output with requirements:\n1. Requirement A\n2. Requirement B\n3. Requirement C",
            "Second agent output implementing:\n1. Implementation of A\n2. Implementation of C\n3. Implementation of D"
        )
    }


@pytest.fixture
def mock_misunderstanding_data():
    """Create sample misunderstanding data for testing."""
    return [
        {
            "id": "issue1",
            "description": "Term X is ambiguous",
            "severity": "HIGH",
            "affected_elements": ["requirement B", "implementation D"]
        },
        {
            "id": "issue2",
            "description": "Requirement B is missing implementation",
            "severity": "MEDIUM",
            "affected_elements": ["requirement B"]
        }
    ]


@pytest.fixture
def coordination_context_factory(state_manager):
    """Factory fixture to create coordination contexts for testing."""
    async def _create_context(coordination_id=None, with_data=False):
        context_manager = WaterAgentContextManager(state_manager=state_manager)
        context_manager._emit_event = AsyncMock()
        
        if not coordination_id:
            coordination_id = f"test_coordination_{id(context_manager)}"
            
        context = await context_manager.create_coordination_context(
            first_agent_id="first_agent",
            second_agent_id="second_agent",
            coordination_id=coordination_id
        )
        
        if with_data:
            # Add test data
            await context_manager.save_coordination_outputs(
                coordination_id,
                "First agent output for testing",
                "Second agent output for testing"
            )
            
            # Add an iteration
            await context_manager.update_coordination_iteration(
                coordination_id,
                iteration=1,
                first_agent_questions=["Question for first agent"],
                first_agent_responses=["Response from first agent"],
                second_agent_questions=["Question for second agent"],
                second_agent_responses=["Response from second agent"],
                resolved=[{"id": "issue1", "resolution_summary": "Issue 1 resolved"}],
                unresolved=[{"id": "issue2", "severity": "MEDIUM", "description": "Issue 2 unresolved"}]
            )
            
        return context, context_manager
        
    return _create_context