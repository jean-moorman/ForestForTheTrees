"""
Tests for the Water Agent Coordinator functionality.

This module tests the Water Agent's core functionality for coordinating between agents,
detecting misunderstandings, generating questions, and resolving ambiguities.
"""

import pytest
import asyncio
import uuid
import json
from unittest.mock import AsyncMock, MagicMock, patch

from resources.water_agent import WaterAgentCoordinator, MisunderstandingDetector
from resources.water_agent import QuestionResponseHandler, AmbiguityResolutionTracker
from resources.water_agent.context_manager import CoordinationContext, WaterAgentContextManager
from resources.state import StateManager
from resources.common import ResourceType
from resources.errors import CoordinationError, MisunderstandingDetectionError


@pytest.fixture
def state_manager_mock():
    """Create a mock StateManager for testing."""
    state_manager = AsyncMock(spec=StateManager)
    state_manager.get_state = AsyncMock(return_value=None)
    state_manager.set_state = AsyncMock(return_value=True)
    state_manager.find_keys = AsyncMock(return_value=[])
    return state_manager


@pytest.fixture
def llm_client_mock():
    """Create a mock LLM client for testing."""
    llm_client = MagicMock()
    llm_client.generate_text = AsyncMock(return_value=MagicMock(text="{}"))
    return llm_client


@pytest.fixture
def water_agent_coordinator(state_manager_mock, llm_client_mock):
    """Create a WaterAgentCoordinator for testing."""
    with patch('resources.water_agent.WaterAgentContextManager'):
        coordinator = WaterAgentCoordinator(
            state_manager=state_manager_mock,
            llm_client=llm_client_mock
        )
        coordinator._emit_event = AsyncMock()
        coordinator._call_llm = AsyncMock(return_value=json.dumps({
            "misunderstandings": [],
            "first_agent_questions": [],
            "second_agent_questions": []
        }))
        return coordinator


@pytest.fixture
def misunderstanding_detector(llm_client_mock):
    """Create a MisunderstandingDetector for testing."""
    detector = MisunderstandingDetector(llm_client=llm_client_mock)
    detector._call_llm = AsyncMock(return_value=json.dumps({
        "misunderstandings": [],
        "first_agent_questions": [],
        "second_agent_questions": []
    }))
    return detector


@pytest.fixture
def resolution_tracker(llm_client_mock):
    """Create an AmbiguityResolutionTracker for testing."""
    tracker = AmbiguityResolutionTracker(llm_client=llm_client_mock)
    tracker._call_llm = AsyncMock(return_value=json.dumps({
        "resolved_misunderstandings": [],
        "unresolved_misunderstandings": [],
        "new_first_agent_questions": [],
        "new_second_agent_questions": [],
        "require_further_iteration": False
    }))
    return tracker


@pytest.fixture
def context_manager(state_manager_mock):
    """Create a WaterAgentContextManager for testing."""
    context_manager = WaterAgentContextManager(state_manager=state_manager_mock)
    context_manager._emit_event = AsyncMock()
    return context_manager


@pytest.fixture
def mock_agents():
    """Create mock agents for testing coordination."""
    first_agent = MagicMock()
    first_agent.agent_id = "test_agent_1"
    first_agent.__class__.__name__ = "TestAgent1"
    first_agent.clarify = AsyncMock(return_value="Clarification response from agent 1")
    
    second_agent = MagicMock()
    second_agent.agent_id = "test_agent_2"
    second_agent.__class__.__name__ = "TestAgent2"
    second_agent.clarify = AsyncMock(return_value="Clarification response from agent 2")
    
    return first_agent, second_agent


@pytest.mark.asyncio
async def test_coordination_context_creation():
    """Test creation and serialization of CoordinationContext."""
    # Create a context
    context_id = str(uuid.uuid4())
    context = CoordinationContext(
        coordination_id=context_id,
        first_agent_id="agent1",
        second_agent_id="agent2",
        mode="standard",
        max_iterations=3,
        severity_threshold="LOW"
    )
    
    # Test basic attributes
    assert context.coordination_id == context_id
    assert context.first_agent_id == "agent1"
    assert context.second_agent_id == "agent2"
    assert context.mode == "standard"
    assert context.max_iterations == 3
    assert context.severity_threshold == "LOW"
    assert context.status == "created"
    
    # Test to_dict serialization
    context_dict = context.to_dict()
    assert context_dict["coordination_id"] == context_id
    assert context_dict["first_agent_id"] == "agent1"
    assert context_dict["second_agent_id"] == "agent2"
    
    # Test from_dict deserialization
    new_context = CoordinationContext.from_dict(context_dict)
    assert new_context.coordination_id == context_id
    assert new_context.first_agent_id == "agent1"
    assert new_context.second_agent_id == "agent2"


@pytest.mark.asyncio
async def test_coordination_context_update():
    """Test updating a CoordinationContext with iteration data."""
    # Create a context
    context = CoordinationContext(
        coordination_id="test_coordination",
        first_agent_id="agent1",
        second_agent_id="agent2"
    )
    
    # Test updating iteration
    context.update_iteration(
        iteration=1,
        first_agent_questions=["Q1", "Q2"],
        first_agent_responses=["A1", "A2"],
        second_agent_questions=["Q3", "Q4"],
        second_agent_responses=["A3", "A4"],
        resolved=[{"id": "issue1", "resolution_summary": "Issue 1 resolved"}],
        unresolved=[{"id": "issue2", "severity": "HIGH", "description": "Issue 2 description"}]
    )
    
    # Check state after update
    assert context.status == "in_progress"
    assert len(context.iterations) == 1
    assert context.resolved_issues == {"issue1"}
    assert "issue2" in context.unresolved_issues
    
    # Test completing the context
    context.complete(
        first_agent_final_output="Final output from agent 1",
        second_agent_final_output="Final output from agent 2",
        final_status="all_issues_resolved"
    )
    
    # Check state after completion
    assert context.status == "completed"
    assert context.first_agent_final_output == "Final output from agent 1"
    assert context.second_agent_final_output == "Final output from agent 2"
    assert context.final_status == "all_issues_resolved"
    assert context.completed_at is not None


@pytest.mark.asyncio
async def test_context_manager(context_manager):
    """Test WaterAgentContextManager operations."""
    # Test creating a context
    context = await context_manager.create_coordination_context(
        first_agent_id="agent1",
        second_agent_id="agent2",
        coordination_id="test_coordination"
    )
    
    # Verify context was created
    assert context.coordination_id == "test_coordination"
    assert context.first_agent_id == "agent1"
    assert context.second_agent_id == "agent2"
    
    # Test getting a context
    with patch.object(context_manager._state_manager, 'get_state') as mock_get_state:
        # Mock returning a serialized context
        mock_get_state.return_value = context.to_dict()
        
        # Get the context
        retrieved_context = await context_manager.get_coordination_context("test_coordination")
        
        # Verify context was retrieved
        assert retrieved_context is not None
        assert retrieved_context.coordination_id == "test_coordination"
        assert retrieved_context.first_agent_id == "agent1"
        
    # Test saving outputs
    result = await context_manager.save_coordination_outputs(
        coordination_id="test_coordination",
        first_agent_output="Output from agent 1",
        second_agent_output="Output from agent 2"
    )
    
    # Verify saving was successful
    assert result == True
    
    # Test completing coordination
    result = await context_manager.complete_coordination(
        coordination_id="test_coordination",
        first_agent_final_output="Final output from agent 1",
        second_agent_final_output="Final output from agent 2",
        final_status="all_issues_resolved"
    )
    
    # Verify completion was successful
    assert result == True


@pytest.mark.asyncio
async def test_misunderstanding_detection(misunderstanding_detector):
    """Test detecting misunderstandings between agent outputs."""
    # Test with no misunderstandings
    first_output = "First agent output"
    second_output = "Second agent output"
    
    misunderstandings, first_questions, second_questions = await misunderstanding_detector.detect_misunderstandings(
        first_output, second_output
    )
    
    # Verify no misunderstandings were found
    assert len(misunderstandings) == 0
    assert len(first_questions) == 0
    assert len(second_questions) == 0
    
    # Test with misunderstandings by mocking the LLM response
    misunderstanding_detector._call_llm = AsyncMock(return_value=json.dumps({
        "misunderstandings": [
            {
                "id": "misunderstanding1",
                "description": "Misunderstanding description",
                "severity": "HIGH",
                "affected_elements": ["element1", "element2"]
            }
        ],
        "first_agent_questions": [
            {"misunderstanding_id": "misunderstanding1", "question": "Question for first agent"}
        ],
        "second_agent_questions": [
            {"misunderstanding_id": "misunderstanding1", "question": "Question for second agent"}
        ]
    }))
    
    misunderstandings, first_questions, second_questions = await misunderstanding_detector.detect_misunderstandings(
        first_output, second_output
    )
    
    # Verify misunderstandings were found
    assert len(misunderstandings) == 1
    assert misunderstandings[0]["id"] == "misunderstanding1"
    assert misunderstandings[0]["severity"] == "HIGH"
    assert len(first_questions) == 1
    assert first_questions[0] == "Question for first agent"
    assert len(second_questions) == 1
    assert second_questions[0] == "Question for second agent"


@pytest.mark.asyncio
async def test_question_response_handler():
    """Test collecting responses from agents."""
    # Create a question response handler
    handler = QuestionResponseHandler()
    
    # Create a mock agent
    agent = MagicMock()
    agent.__class__.__name__ = "TestAgent"
    agent.clarify = AsyncMock(return_value="Response to question")
    
    # Test getting responses with no questions
    responses = await handler.get_agent_responses(agent, [])
    assert len(responses) == 0
    
    # Test getting responses with questions
    responses = await handler.get_agent_responses(agent, ["Question 1", "Question 2"])
    assert len(responses) == 2
    assert responses[0] == "Response to question"
    assert responses[1] == "Response to question"
    assert agent.clarify.call_count == 2
    
    # Test response caching
    agent.clarify.reset_mock()
    responses = await handler.get_agent_responses(agent, ["Question 1", "Question 2"])
    assert len(responses) == 2
    assert responses[0] == "Response to question"
    assert responses[1] == "Response to question"
    # Should use cached responses and not call clarify again
    assert agent.clarify.call_count == 0


@pytest.mark.asyncio
async def test_resolution_assessment(resolution_tracker):
    """Test assessment of resolution progress."""
    # Initialize tracking with misunderstandings
    misunderstandings = [
        {
            "id": "issue1",
            "description": "Issue 1 description",
            "severity": "HIGH"
        },
        {
            "id": "issue2",
            "description": "Issue 2 description",
            "severity": "MEDIUM"
        }
    ]
    
    resolution_tracker.initialize_tracking(misunderstandings)
    
    # Verify tracking state
    assert len(resolution_tracker.unresolved_issues) == 2
    assert "issue1" in resolution_tracker.unresolved_issues
    assert "issue2" in resolution_tracker.unresolved_issues
    assert len(resolution_tracker.resolved_issues) == 0
    
    # Test with no resolution yet
    resolution_tracker._call_llm = AsyncMock(return_value=json.dumps({
        "resolved_misunderstandings": [],
        "unresolved_misunderstandings": misunderstandings,
        "new_first_agent_questions": [{"question": "Follow-up question for first agent"}],
        "new_second_agent_questions": [{"question": "Follow-up question for second agent"}],
        "require_further_iteration": True
    }))
    
    resolved, unresolved, new_first_questions, new_second_questions = await resolution_tracker.assess_resolution(
        misunderstandings,
        ["Question for first agent"],
        ["Response from first agent"],
        ["Question for second agent"],
        ["Response from second agent"]
    )
    
    # Verify assessment results
    assert len(resolved) == 0
    assert len(unresolved) == 2
    assert len(new_first_questions) == 1
    assert len(new_second_questions) == 1
    
    # Test with resolution of one issue
    resolution_tracker._call_llm = AsyncMock(return_value=json.dumps({
        "resolved_misunderstandings": [
            {"id": "issue1", "resolution_summary": "Issue 1 resolved through clarification"}
        ],
        "unresolved_misunderstandings": [
            {"id": "issue2", "severity": "MEDIUM", "description": "Issue 2 description"}
        ],
        "new_first_agent_questions": [],
        "new_second_agent_questions": [{"question": "Follow-up question for second agent about issue 2"}],
        "require_further_iteration": True
    }))
    
    resolved, unresolved, new_first_questions, new_second_questions = await resolution_tracker.assess_resolution(
        misunderstandings,
        ["Question for first agent"],
        ["Response from first agent"],
        ["Question for second agent"],
        ["Response from second agent"]
    )
    
    # Verify assessment results
    assert len(resolved) == 1
    assert resolved[0]["id"] == "issue1"
    assert len(unresolved) == 1
    assert unresolved[0]["id"] == "issue2"
    assert len(new_first_questions) == 0
    assert len(new_second_questions) == 1
    
    # Verify tracker state was updated
    assert "issue1" in resolution_tracker.resolved_issues
    assert "issue2" in resolution_tracker.unresolved_issues
    assert "issue1" not in resolution_tracker.unresolved_issues


@pytest.mark.asyncio
async def test_water_agent_coordination_no_misunderstandings(water_agent_coordinator, mock_agents):
    """Test coordination process with no misunderstandings detected."""
    first_agent, second_agent = mock_agents
    
    # Mock detecting no misunderstandings
    water_agent_coordinator.misunderstanding_detector.detect_misunderstandings = AsyncMock(
        return_value=([], [], [])
    )
    
    # Run coordination
    updated_first_output, updated_second_output, context = await water_agent_coordinator.coordinate_agents(
        first_agent,
        "First agent output",
        second_agent,
        "Second agent output"
    )
    
    # Verify no changes were made
    assert updated_first_output == "First agent output"
    assert updated_second_output == "Second agent output"
    assert context.get("status") != "failed"
    assert water_agent_coordinator._emit_event.call_count > 0


@pytest.mark.asyncio
async def test_water_agent_coordination_with_misunderstandings(water_agent_coordinator, mock_agents):
    """Test coordination process with misunderstandings detected and resolved."""
    first_agent, second_agent = mock_agents
    
    # Mock detecting misunderstandings
    water_agent_coordinator.misunderstanding_detector.detect_misunderstandings = AsyncMock(
        return_value=(
            [{"id": "misunderstanding1", "description": "Test misunderstanding", "severity": "HIGH"}],
            ["Question for first agent"],
            ["Question for second agent"]
        )
    )
    
    # Mock response handling
    water_agent_coordinator.response_handler.get_agent_responses = AsyncMock(
        side_effect=lambda agent, questions: asyncio.Future().set_result(
            ["Response from agent"] * len(questions)
        )
    )
    
    # Mock resolution assessment
    water_agent_coordinator.resolution_tracker.assess_resolution = AsyncMock(
        return_value=(
            [{"id": "misunderstanding1", "resolution_summary": "Resolved through clarification"}],
            [],
            [],
            []
        )
    )
    
    # Mock final output generation
    water_agent_coordinator._generate_final_outputs = AsyncMock(
        return_value=(
            "Updated first agent output",
            "Updated second agent output",
            {"first_agent_changes": ["Change 1"], "second_agent_changes": ["Change 1"]}
        )
    )
    
    # Run coordination
    updated_first_output, updated_second_output, context = await water_agent_coordinator.coordinate_agents(
        first_agent,
        "First agent output",
        second_agent,
        "Second agent output"
    )
    
    # Verify outputs were updated
    assert updated_first_output == "Updated first agent output"
    assert updated_second_output == "Updated second agent output"
    assert context.get("status") != "failed"
    assert water_agent_coordinator._emit_event.call_count > 0


@pytest.mark.asyncio
async def test_water_agent_coordination_error_handling(water_agent_coordinator, mock_agents):
    """Test error handling during the coordination process."""
    first_agent, second_agent = mock_agents
    
    # Mock an error in misunderstanding detection
    water_agent_coordinator.misunderstanding_detector.detect_misunderstandings = AsyncMock(
        side_effect=MisunderstandingDetectionError("Test error")
    )
    
    # Run coordination and expect an error
    with pytest.raises(CoordinationError):
        await water_agent_coordinator.coordinate_agents(
            first_agent,
            "First agent output",
            second_agent,
            "Second agent output"
        )
    
    # Verify error event was emitted
    assert water_agent_coordinator._emit_event.call_count > 0
    for call in water_agent_coordinator._emit_event.call_args_list:
        if call[0][0] == "coordination_error":
            break
    else:
        assert False, "coordination_error event was not emitted"


@pytest.mark.asyncio
async def test_context_pruning(context_manager):
    """Test pruning temporary data from a coordination context."""
    # Create a test context
    context = await context_manager.create_coordination_context(
        first_agent_id="agent1",
        second_agent_id="agent2",
        coordination_id="test_pruning"
    )
    
    # Add test data to the context
    context.status = "completed"
    context.misunderstandings = [{"id": "issue1", "description": "Test issue"}]
    context.iterations = [
        {
            "iteration": 1,
            "timestamp": "2023-01-01T00:00:00",
            "first_agent_questions": ["Question 1", "Question 2"],
            "first_agent_responses": ["Response 1", "Response 2"],
            "second_agent_questions": ["Question 3", "Question 4"],
            "second_agent_responses": ["Response 3", "Response 4"],
            "resolved": [{"id": "issue1", "resolution_summary": "Resolved"}],
            "unresolved": []
        }
    ]
    context.resolved_issues = {"issue1"}
    context.first_agent_final_output = "Final output from agent 1"
    context.second_agent_final_output = "Final output from agent 2"
    context.final_status = "all_issues_resolved"
    context.completed_at = "2023-01-01T01:00:00"
    
    # Update context in the manager
    await context_manager.update_coordination_context(context)
    
    # Mock getting the context for pruning
    with patch.object(context_manager, 'get_coordination_context') as mock_get_context:
        mock_get_context.return_value = context
        
        # Test pruning
        result = await context_manager.prune_temporary_data(
            coordination_id="test_pruning",
            keep_final_outputs=True
        )
        
        # Verify pruning was successful
        assert result == True
        
        # Verify context was modified
        pruned_context = await context_manager.get_coordination_context("test_pruning")
        assert pruned_context is not None
        assert pruned_context.status == "completed"
        assert pruned_context.first_agent_final_output == "Final output from agent 1"
        assert pruned_context.second_agent_final_output == "Final output from agent 2"
        
        # Verify temporary data was pruned
        assert len(pruned_context.iterations) == 1
        assert "first_agent_questions" not in pruned_context.iterations[0]
        assert "first_agent_responses" not in pruned_context.iterations[0]
        assert "second_agent_questions" not in pruned_context.iterations[0]
        assert "second_agent_responses" not in pruned_context.iterations[0]
        assert "first_agent_questions_count" in pruned_context.iterations[0]
        assert "second_agent_questions_count" in pruned_context.iterations[0]