"""
Tests for the Sequential Agent Coordinator.

This module tests the Sequential Agent Coordinator functionality for managing
handoffs between sequential agents in the Phase One workflow using the Water Agent.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from phase_one.validation.coordination import SequentialAgentCoordinator
from resources.water_agent import WaterAgentCoordinator
from resources import EventQueue, StateManager, ResourceType
from interfaces.agent.interface import AgentInterface


@pytest.fixture
def event_queue_mock():
    """Create a mock event queue for testing."""
    queue = AsyncMock(spec=EventQueue)
    queue.emit = AsyncMock()
    return queue


@pytest.fixture
def state_manager_mock():
    """Create a mock state manager for testing."""
    state_manager = AsyncMock(spec=StateManager)
    state_manager.get_state = AsyncMock(return_value=None)
    state_manager.set_state = AsyncMock(return_value=True)
    return state_manager


@pytest.fixture
def water_coordinator_mock():
    """Create a mock WaterAgentCoordinator for testing."""
    coordinator = AsyncMock(spec=WaterAgentCoordinator)
    coordinator.coordinate_agents = AsyncMock(
        return_value=("Updated first output", "Updated second output", {})
    )
    return coordinator


@pytest.fixture
def agent_mock():
    """Create a mock agent for testing."""
    agent = MagicMock(spec=AgentInterface)
    agent.agent_id = "test_agent"
    return agent


@pytest.fixture
def sequential_coordinator(event_queue_mock, state_manager_mock, water_coordinator_mock):
    """Create a SequentialAgentCoordinator for testing."""
    with patch('phase_one.validation.coordination.WaterAgentCoordinator', return_value=water_coordinator_mock):
        coordinator = SequentialAgentCoordinator(
            event_queue=event_queue_mock,
            state_manager=state_manager_mock,
            max_coordination_attempts=2,
            coordination_timeout=5.0
        )
        return coordinator


@pytest.mark.asyncio
async def test_coordinate_agent_handoff_no_misunderstandings(sequential_coordinator, agent_mock, water_coordinator_mock):
    """Test coordinating handoff with no misunderstandings detected."""
    # Mock no misunderstandings detected
    water_coordinator_mock.coordinate_agents = AsyncMock(
        return_value=("First agent output", "Second agent mock output", {"misunderstandings": []})
    )
    
    # Create a second agent mock
    second_agent = MagicMock(spec=AgentInterface)
    second_agent.agent_id = "second_agent"
    
    # Test the handoff
    first_agent_output = "First agent output"
    result, metadata = await sequential_coordinator.coordinate_agent_handoff(
        agent_mock,
        first_agent_output,
        second_agent,
        "test_operation"
    )
    
    # Verify the expected results
    assert result == first_agent_output
    assert metadata["status"] == "completed"
    assert metadata["result"] == "no_misunderstandings"
    
    # Verify events were emitted
    assert sequential_coordinator.event_queue.emit.call_count >= 2  # start and complete events
    
    # Verify state was updated
    assert sequential_coordinator.state_manager.set_state.call_count >= 2


@pytest.mark.asyncio
async def test_coordinate_agent_handoff_with_misunderstandings(sequential_coordinator, agent_mock, water_coordinator_mock):
    """Test coordinating handoff with misunderstandings detected and resolved."""
    # Mock misunderstandings detected and resolved
    water_coordinator_mock.coordinate_agents = AsyncMock(
        return_value=(
            "Updated first agent output",
            "Updated second agent output",
            {"misunderstandings": [{"id": "issue1", "description": "Test issue"}]}
        )
    )
    
    # Create a second agent mock
    second_agent = MagicMock(spec=AgentInterface)
    second_agent.agent_id = "second_agent"
    
    # Test the handoff
    first_agent_output = "First agent output"
    result, metadata = await sequential_coordinator.coordinate_agent_handoff(
        agent_mock,
        first_agent_output,
        second_agent,
        "test_operation"
    )
    
    # Verify the expected results
    assert result != first_agent_output  # Output should be updated
    assert metadata["status"] == "completed"
    assert metadata["result"] == "coordination_applied"
    assert metadata["misunderstandings_count"] == 1
    
    # Verify events were emitted
    assert sequential_coordinator.event_queue.emit.call_count >= 2  # start and complete events
    
    # Verify state was updated
    assert sequential_coordinator.state_manager.set_state.call_count >= 3  # initial, attempt, and final states


@pytest.mark.asyncio
async def test_coordinate_agent_handoff_with_dict_output(sequential_coordinator, agent_mock, water_coordinator_mock):
    """Test coordinating handoff with dictionary outputs."""
    # Mock misunderstandings detected and resolved
    water_coordinator_mock.coordinate_agents = AsyncMock(
        return_value=(
            '{"content": "Updated content", "metadata": {"updated": true}}',
            "Updated second agent output",
            {"misunderstandings": [{"id": "issue1", "description": "Test issue"}]}
        )
    )
    
    # Create a second agent mock
    second_agent = MagicMock(spec=AgentInterface)
    second_agent.agent_id = "second_agent"
    
    # Test the handoff with dict output
    first_agent_output = {"content": "Original content", "metadata": {"updated": False}}
    result, metadata = await sequential_coordinator.coordinate_agent_handoff(
        agent_mock,
        first_agent_output,
        second_agent,
        "test_operation"
    )
    
    # Verify the expected results
    assert result != first_agent_output  # Output should be updated
    assert isinstance(result, dict)  # Result should still be a dict
    assert "content" in result
    assert result["content"] != first_agent_output["content"]
    
    assert metadata["status"] == "completed"
    assert metadata["result"] == "coordination_applied"
    assert metadata["misunderstandings_count"] == 1


@pytest.mark.asyncio
async def test_coordinate_agent_handoff_timeout(sequential_coordinator, agent_mock):
    """Test coordinating handoff with timeout."""
    # Set a very short timeout for the test
    sequential_coordinator.coordination_timeout = 0.1
    
    # Make coordinate_agents sleep longer than the timeout
    async def slow_coordinate(*args, **kwargs):
        await asyncio.sleep(0.2)
        return "Updated output", "Mock output", {}
    
    sequential_coordinator.water_coordinator.coordinate_agents = slow_coordinate
    
    # Create a second agent mock
    second_agent = MagicMock(spec=AgentInterface)
    second_agent.agent_id = "second_agent"
    
    # Test the handoff with timeout
    first_agent_output = "First agent output"
    result, metadata = await sequential_coordinator.coordinate_agent_handoff(
        agent_mock,
        first_agent_output,
        second_agent,
        "test_operation"
    )
    
    # Verify the expected results
    assert result == first_agent_output  # Output should not be changed
    assert metadata["status"] == "timeout"
    assert "error" in metadata
    
    # Verify events were emitted
    assert sequential_coordinator.event_queue.emit.call_count >= 2  # start and timeout events
    
    # Verify state was updated
    assert sequential_coordinator.state_manager.set_state.call_count >= 2


@pytest.mark.asyncio
async def test_coordinate_agent_handoff_error(sequential_coordinator, agent_mock, water_coordinator_mock):
    """Test coordinating handoff with an error."""
    # Mock an error during coordination
    water_coordinator_mock.coordinate_agents = AsyncMock(
        side_effect=Exception("Test coordination error")
    )
    
    # Create a second agent mock
    second_agent = MagicMock(spec=AgentInterface)
    second_agent.agent_id = "second_agent"
    
    # Test the handoff with error
    first_agent_output = "First agent output"
    result, metadata = await sequential_coordinator.coordinate_agent_handoff(
        agent_mock,
        first_agent_output,
        second_agent,
        "test_operation"
    )
    
    # Verify the expected results
    assert result == first_agent_output  # Output should not be changed
    assert metadata["status"] == "error"
    assert "error" in metadata
    assert "Test coordination error" in metadata["error"]
    
    # Verify events were emitted
    assert sequential_coordinator.event_queue.emit.call_count >= 2  # start and error events
    
    # Verify state was updated
    assert sequential_coordinator.state_manager.set_state.call_count >= 2


@pytest.mark.asyncio
async def test_coordinate_interactive_handoff(sequential_coordinator, agent_mock, water_coordinator_mock):
    """Test coordinating interactive handoff after second agent has processed."""
    # Mock coordination with updates to both outputs
    water_coordinator_mock.coordinate_agents = AsyncMock(
        return_value=(
            "Updated first agent output",
            "Updated second agent output",
            {"misunderstandings": [{"id": "issue1", "description": "Test issue"}]}
        )
    )
    
    # Create a second agent mock
    second_agent = MagicMock(spec=AgentInterface)
    second_agent.agent_id = "second_agent"
    
    # Test the interactive handoff
    first_agent_output = "First agent output"
    second_agent_output = "Second agent output"
    
    first_result, second_result, metadata = await sequential_coordinator.coordinate_interactive_handoff(
        agent_mock,
        first_agent_output,
        second_agent,
        second_agent_output,
        "test_operation"
    )
    
    # Verify the expected results
    assert first_result != first_agent_output  # First output should be updated
    assert second_result != second_agent_output  # Second output should be updated
    assert metadata["status"] == "completed"
    assert metadata["result"] == "coordination_applied"
    assert metadata["misunderstandings_count"] == 1
    
    # Verify events were emitted
    assert sequential_coordinator.event_queue.emit.call_count >= 2  # start and complete events
    
    # Verify state was updated
    assert sequential_coordinator.state_manager.set_state.call_count >= 3


@pytest.mark.asyncio
async def test_get_coordination_status(sequential_coordinator, state_manager_mock):
    """Test getting coordination status."""
    # Mock state for a coordination operation
    operation_id = "test_operation"
    state_manager_mock.get_state = AsyncMock(return_value={
        "status": "completed",
        "result": "coordination_applied",
        "misunderstandings_count": 1,
        "first_output_updated": True,
        "start_time": "2023-01-01T00:00:00",
        "end_time": "2023-01-01T00:01:00",
        "current_attempt": 1
    })
    
    # Test getting sequential coordination status
    status = await sequential_coordinator.get_coordination_status(operation_id, interactive=False)
    
    # Verify the expected results
    assert status["status"] == "completed"
    assert status["result"] == "coordination_applied"
    assert status["misunderstandings_count"] == 1
    assert status["first_output_updated"] == True
    assert status["operation_id"] == operation_id
    
    # Mock no state found
    state_manager_mock.get_state = AsyncMock(return_value=None)
    
    # Test getting status for unknown operation
    status = await sequential_coordinator.get_coordination_status("unknown_operation", interactive=False)
    
    # Verify the expected results
    assert status["status"] == "unknown"
    assert status["operation_id"] == "unknown_operation"