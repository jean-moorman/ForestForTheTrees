"""
Tests for the Agent Coordination Interface.

This module tests the coordination interface that allows agents to participate
in the Water Agent coordination process to resolve misunderstandings.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json
from datetime import datetime

from interfaces.agent.coordination import CoordinationInterface
from resources.water_agent import WaterAgentCoordinator
from resources.errors import CoordinationError


@pytest.fixture
def agent_interface_mock():
    """Create a mock agent interface for testing coordination."""
    agent_interface = MagicMock()
    agent_interface.agent_id = "test_agent"
    agent_interface.interface_id = "test_interface"
    agent_interface._state_manager = AsyncMock()
    agent_interface._context_manager = AsyncMock()
    agent_interface._metrics_manager = AsyncMock()
    agent_interface._metrics_manager.record_metric = AsyncMock()
    agent_interface.agent = MagicMock()
    agent_interface.agent.get_response = AsyncMock(return_value="Response from agent")
    return agent_interface


@pytest.fixture
def next_agent_mock():
    """Create a mock next agent for testing coordination."""
    next_agent = MagicMock()
    next_agent.agent_id = "next_agent"
    next_agent.clarify = AsyncMock(return_value="Clarification from next agent")
    next_agent.coordination_interface = MagicMock()
    next_agent.coordination_interface.update_output = AsyncMock(return_value=True)
    return next_agent


@pytest.fixture
def coordination_interface(agent_interface_mock):
    """Create a CoordinationInterface for testing."""
    # Mock the WaterAgentCoordinator
    with patch('interfaces.agent.coordination.WaterAgentCoordinator') as mock_coordinator_class:
        mock_coordinator = AsyncMock(spec=WaterAgentCoordinator)
        mock_coordinator.coordinate_agents = AsyncMock(
            return_value=("Updated first output", "Updated second output", {"status": "completed"})
        )
        mock_coordinator_class.return_value = mock_coordinator
        
        # Create the coordination interface
        interface = CoordinationInterface(agent_interface_mock)
        return interface


@pytest.mark.asyncio
async def test_clarify(coordination_interface, agent_interface_mock):
    """Test the clarify method of the coordination interface."""
    # Test clarifying a question
    response = await coordination_interface.clarify("What do you mean by X?")
    
    # Verify the agent was called
    assert agent_interface_mock.agent.get_response.called
    
    # Verify metrics were recorded
    assert agent_interface_mock._metrics_manager.record_metric.called
    
    # Verify response was returned
    assert response == "Response from agent"
    
    # Test caching of responses
    agent_interface_mock.agent.get_response.reset_mock()
    agent_interface_mock._metrics_manager.record_metric.reset_mock()
    
    response = await coordination_interface.clarify("What do you mean by X?")
    
    # Verify the agent was not called again (cached response)
    assert not agent_interface_mock.agent.get_response.called
    
    # Verify metrics were still recorded
    assert agent_interface_mock._metrics_manager.record_metric.called
    
    # Verify same response was returned
    assert response == "Response from agent"


@pytest.mark.asyncio
async def test_update_output(coordination_interface, agent_interface_mock):
    """Test updating agent output based on coordination results."""
    # Mock getting the agent context
    agent_context = {
        "output": "Original output",
        "output_history": []
    }
    agent_interface_mock._context_manager.get_context = AsyncMock(return_value=agent_context)
    
    # Test updating output
    result = await coordination_interface.update_output(
        "Original output",
        "Updated output after coordination"
    )
    
    # Verify context was retrieved
    assert agent_interface_mock._context_manager.get_context.called
    
    # Verify context was updated
    assert agent_interface_mock._context_manager.update_context.called
    
    # Verify original output was saved in history
    context_arg = agent_interface_mock._context_manager.update_context.call_args[0][1]
    assert len(context_arg["output_history"]) == 1
    assert context_arg["output_history"][0]["output"] == "Original output"
    assert context_arg["output_history"][0]["reason"] == "coordination_update"
    assert context_arg["output"] == "Updated output after coordination"
    assert context_arg["coordination_applied"] == True
    
    # Verify result was successful
    assert result == True


@pytest.mark.asyncio
async def test_update_output_no_existing_context(coordination_interface, agent_interface_mock):
    """Test updating output when no context exists yet."""
    # Mock no existing context
    agent_interface_mock._context_manager.get_context = AsyncMock(return_value=None)
    agent_interface_mock._context_manager.create_context = AsyncMock(return_value={})
    
    # Test updating output
    result = await coordination_interface.update_output(
        "Original output",
        "Updated output after coordination"
    )
    
    # Verify context was created
    assert agent_interface_mock._context_manager.create_context.called
    
    # Verify result was successful
    assert result == True


@pytest.mark.asyncio
async def test_coordinate_with_next_agent(coordination_interface, agent_interface_mock, next_agent_mock):
    """Test coordination with the next agent in a sequence."""
    # Test successful coordination
    my_output = "Output from test agent"
    next_output = "Output from next agent"
    
    updated_my_output, updated_next_output, metadata = await coordination_interface.coordinate_with_next_agent(
        next_agent_mock,
        my_output,
        next_output
    )
    
    # Verify coordination was performed
    assert coordination_interface.coordination_manager.coordinate_agents.called
    
    # Verify metrics were recorded
    assert agent_interface_mock._metrics_manager.record_metric.called
    
    # Verify outputs were updated
    assert updated_my_output == "Updated first output"
    assert updated_next_output == "Updated second output"
    assert metadata["status"] == "completed"
    
    # Verify update_output was called for both agents
    assert next_agent_mock.coordination_interface.update_output.called


@pytest.mark.asyncio
async def test_coordinate_with_next_agent_no_changes(coordination_interface, agent_interface_mock, next_agent_mock):
    """Test coordination with no changes needed."""
    # Mock coordination with no changes
    coordination_interface.coordination_manager.coordinate_agents = AsyncMock(
        return_value=("Output from test agent", "Output from next agent", {"status": "completed"})
    )
    
    my_output = "Output from test agent"
    next_output = "Output from next agent"
    
    updated_my_output, updated_next_output, metadata = await coordination_interface.coordinate_with_next_agent(
        next_agent_mock,
        my_output,
        next_output
    )
    
    # Verify coordination was performed
    assert coordination_interface.coordination_manager.coordinate_agents.called
    
    # Verify metrics were recorded
    assert agent_interface_mock._metrics_manager.record_metric.called
    
    # Verify outputs were not updated (same as input)
    assert updated_my_output == my_output
    assert updated_next_output == next_output
    assert metadata["status"] == "completed"
    
    # Verify update_output was not called for either agent
    assert not next_agent_mock.coordination_interface.update_output.called


@pytest.mark.asyncio
async def test_coordinate_with_next_agent_error(coordination_interface, agent_interface_mock, next_agent_mock):
    """Test coordination with an error."""
    # Mock coordination error
    coordination_interface.coordination_manager.coordinate_agents = AsyncMock(
        side_effect=CoordinationError("Test coordination error")
    )
    
    my_output = "Output from test agent"
    next_output = "Output from next agent"
    
    updated_my_output, updated_next_output, metadata = await coordination_interface.coordinate_with_next_agent(
        next_agent_mock,
        my_output,
        next_output
    )
    
    # Verify coordination was attempted
    assert coordination_interface.coordination_manager.coordinate_agents.called
    
    # Verify metrics were recorded for the error
    assert agent_interface_mock._metrics_manager.record_metric.called
    
    # Verify outputs were not changed
    assert updated_my_output == my_output
    assert updated_next_output == next_output
    assert metadata["status"] == "failed"
    assert "error" in metadata
    
    # Verify update_output was not called
    assert not next_agent_mock.coordination_interface.update_output.called


@pytest.mark.asyncio
async def test_coordinate_with_next_agent_exception(coordination_interface, agent_interface_mock, next_agent_mock):
    """Test coordination with an unexpected exception."""
    # Mock unexpected exception
    coordination_interface.coordination_manager.coordinate_agents = AsyncMock(
        side_effect=Exception("Unexpected test exception")
    )
    
    my_output = "Output from test agent"
    next_output = "Output from next agent"
    
    updated_my_output, updated_next_output, metadata = await coordination_interface.coordinate_with_next_agent(
        next_agent_mock,
        my_output,
        next_output
    )
    
    # Verify coordination was attempted
    assert coordination_interface.coordination_manager.coordinate_agents.called
    
    # Verify metrics were recorded for the exception
    assert agent_interface_mock._metrics_manager.record_metric.called
    
    # Verify outputs were not changed
    assert updated_my_output == my_output
    assert updated_next_output == next_output
    assert metadata["status"] == "exception"
    assert "error" in metadata
    
    # Verify update_output was not called
    assert not next_agent_mock.coordination_interface.update_output.called