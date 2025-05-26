"""
Tests for comprehensive AgentInterface state transitions in the FFTT system.
"""

import pytest
import asyncio
import pytest_asyncio
import logging
from unittest.mock import AsyncMock, patch
from typing import List, Dict, Any
import time
from datetime import datetime, timedelta

# Import real implementations
from resources import (
    ResourceType, 
    ResourceState, 
    EventQueue, 
    StateManager, 
    AgentContextManager,
    CacheManager,
    MetricsManager,
    ErrorHandler,
    MemoryMonitor
)

from interfaces.agent.interface import AgentInterface, AgentState
from interfaces.errors import StateTransitionError

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define fixtures for testing
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def event_queue():
    """Create and start an event queue for testing."""
    queue = EventQueue()
    await queue.start()
    yield queue
    await queue.stop()

@pytest.fixture
def state_manager(event_queue):
    """Create a state manager for testing."""
    return StateManager(event_queue)

@pytest.fixture
def cache_manager(event_queue):
    """Create a cache manager for testing."""
    return CacheManager(event_queue)

@pytest.fixture
def metrics_manager(event_queue):
    """Create a metrics manager for testing."""
    return MetricsManager(event_queue)

@pytest.fixture
def error_handler(event_queue):
    """Create an error handler for testing."""
    return ErrorHandler(event_queue)

@pytest.fixture
def agent_context_manager(event_queue):
    """Create an agent context manager for testing."""
    return AgentContextManager(event_queue)

@pytest.fixture
def memory_monitor(event_queue):
    """Create a memory monitor for testing."""
    return MemoryMonitor(event_queue)

@pytest.fixture
def agent_interface(event_queue, state_manager, agent_context_manager, cache_manager, 
                   metrics_manager, error_handler, memory_monitor):
    """Create an agent interface for testing."""
    return AgentInterface(
        "test_agent",
        event_queue,
        state_manager,
        agent_context_manager,
        cache_manager,
        metrics_manager,
        error_handler,
        memory_monitor
    )

# Basic state transition tests
@pytest.mark.asyncio
async def test_initial_agent_state(agent_interface):
    """Test the initial state of the agent interface."""
    assert agent_interface.agent_state == AgentState.READY
    
    # Ensure initialized
    await agent_interface.ensure_initialized()
    
    # Verify resource state mapping
    resource_state = await agent_interface.get_state()
    assert resource_state == ResourceState.INITIALIZING  # Initial resource state

@pytest.mark.asyncio
async def test_all_agent_state_transitions(agent_interface):
    """Test all possible valid agent state transitions."""
    # Ensure the interface is initialized
    await agent_interface.ensure_initialized()
    
    # Initial state should be READY
    assert agent_interface.agent_state == AgentState.READY
    
    # Test transitioning to each state and verify the mapping to resource state
    state_resource_mapping = {
        AgentState.PROCESSING: ResourceState.ACTIVE,
        AgentState.VALIDATING: ResourceState.PAUSED,
        AgentState.FAILED_VALIDATION: ResourceState.FAILED,
        AgentState.COMPLETE: ResourceState.ACTIVE,
        AgentState.ERROR: ResourceState.TERMINATED
    }
    
    for agent_state, expected_resource_state in state_resource_mapping.items():
        # Set the agent state
        await agent_interface.set_agent_state(agent_state, {"test": True})
        
        # Verify the agent state was set
        assert agent_interface.agent_state == agent_state
        
        # Verify the corresponding resource state was set
        resource_state = await agent_interface.get_state()
        assert resource_state == expected_resource_state
        
        # Verify metadata was stored
        state_entry = await state_manager.get_state(f"interface:{agent_interface.interface_id}")
        if hasattr(state_entry, 'metadata'):
            assert state_entry.metadata.get("test") == True

@pytest.mark.asyncio
async def test_state_transition_events(agent_interface):
    """Test that state transitions emit appropriate events."""
    # Ensure the interface is initialized
    await agent_interface.ensure_initialized()
    
    # Clear event history
    agent_interface._event_queue._event_history.clear()
    
    # Set the agent state
    await agent_interface.set_agent_state(AgentState.PROCESSING)
    
    # Verify an event was emitted
    events = agent_interface._event_queue._event_history
    state_change_events = [e for e in events if e.event_type == "INTERFACE_STATE_CHANGED"]
    
    assert len(state_change_events) >= 1
    assert state_change_events[0].data["interface_id"] == agent_interface.interface_id
    assert state_change_events[0].data["new_state"] == ResourceState.ACTIVE.name

# Test state transition workflow
@pytest.mark.asyncio
async def test_full_processing_state_workflow(agent_interface):
    """Test a full state transition workflow during processing."""
    # Ensure the interface is initialized
    await agent_interface.ensure_initialized()
    
    # Mock agent.get_response to avoid real processing
    async def mock_get_response(*args, **kwargs):
        return {"message": "Test response", "status": "success"}
    
    # Save original and patch
    original_get_response = agent_interface.agent.get_response
    agent_interface.agent.get_response = mock_get_response
    
    try:
        # Process a request
        result = await agent_interface.process_with_validation(
            "Test conversation",
            system_prompt_info=("test_dir", "test_prompt"),
            schema={"type": "object"},
            current_phase="test_phase",
            operation_id="test_op"
        )
        
        # Verify the agent went through the proper state transitions
        assert agent_interface.agent_state == AgentState.COMPLETE
        
        # Verify the resource state is correct
        resource_state = await agent_interface.get_state()
        assert resource_state == ResourceState.ACTIVE
        
        # Verify the response
        assert result["status"] == "success"
        assert result["message"] == "Test response"
        assert result["request_id"] == "test_op"
        
    finally:
        # Restore original method
        agent_interface.agent.get_response = original_get_response

@pytest.mark.asyncio
async def test_failure_state_workflow(agent_interface):
    """Test state transitions during processing failure."""
    # Ensure the interface is initialized
    await agent_interface.ensure_initialized()
    
    # Mock agent.get_response to simulate a failure
    async def mock_get_response_error(*args, **kwargs):
        raise ValueError("Simulated error in processing")
    
    # Save original and patch
    original_get_response = agent_interface.agent.get_response
    agent_interface.agent.get_response = mock_get_response_error
    
    try:
        # Process a request
        result = await agent_interface.process_with_validation(
            "Test conversation",
            system_prompt_info=("test_dir", "test_prompt"),
            schema={"type": "object"},
            current_phase="test_phase",
            operation_id="test_error_op"
        )
        
        # Verify the agent went to ERROR state
        assert agent_interface.agent_state == AgentState.ERROR
        
        # Verify the resource state is TERMINATED
        resource_state = await agent_interface.get_state()
        assert resource_state == ResourceState.TERMINATED
        
        # Verify the error response
        assert result["status"] == "error"
        assert "error" in result
        assert "Simulated error in processing" in result["error"]
        
    finally:
        # Restore original method
        agent_interface.agent.get_response = original_get_response

@pytest.mark.asyncio
async def test_timeout_state_workflow(agent_interface):
    """Test state transitions during processing timeout."""
    # Ensure the interface is initialized
    await agent_interface.ensure_initialized()
    
    # Mock agent.get_response to simulate a timeout
    async def mock_get_response_timeout(*args, **kwargs):
        await asyncio.sleep(0.5)  # Sleep longer than our test timeout
        return {"message": "This should never be returned"}
    
    # Save original and patch
    original_get_response = agent_interface.agent.get_response
    agent_interface.agent.get_response = mock_get_response_timeout
    
    try:
        # Process a request with a very short timeout
        result = await agent_interface.process_with_validation(
            "Test conversation",
            system_prompt_info=("test_dir", "test_prompt"),
            schema={"type": "object"},
            current_phase="test_phase",
            operation_id="test_timeout_op",
            timeout=0.1  # Very short timeout
        )
        
        # Verify the agent went to ERROR state
        assert agent_interface.agent_state == AgentState.ERROR
        
        # Verify the resource state is TERMINATED
        resource_state = await agent_interface.get_state()
        assert resource_state == ResourceState.TERMINATED
        
        # Verify the timeout error response
        assert result["status"] == "error"
        assert "error" in result
        assert "timeout" in result["error"].lower()
        
    finally:
        # Restore original method
        agent_interface.agent.get_response = original_get_response

@pytest.mark.asyncio
async def test_validation_state_workflow(agent_interface):
    """Test state transitions during validation workflow."""
    # Ensure the interface is initialized
    await agent_interface.ensure_initialized()
    
    # Mock the validation manager's validate_agent_output to control validation
    original_validate = agent_interface._validation_manager.validate_agent_output
    
    # First scenario: validation succeeds
    async def mock_validate_success(*args, **kwargs):
        # First set the agent to VALIDATING state
        await agent_interface.set_agent_state(AgentState.VALIDATING)
        # Return success
        return True, {"status": "success", "data": {"validated": True}}, None
    
    agent_interface._validation_manager.validate_agent_output = mock_validate_success
    
    # Mock agent.get_response to return a success
    async def mock_get_response(*args, **kwargs):
        return {"message": "Test response", "status": "success"}
    
    agent_interface.agent.get_response = mock_get_response
    
    try:
        # Process with successful validation
        result = await agent_interface.process_with_validation(
            "Test conversation",
            system_prompt_info=("test_dir", "test_prompt"),
            schema={"type": "object"},
            current_phase="test_phase",
            operation_id="test_validation_success_op"
        )
        
        # Verify result
        assert result["status"] == "success"
        assert agent_interface.agent_state == AgentState.COMPLETE
        
        # Now test validation failure
        async def mock_validate_failure(*args, **kwargs):
            # First set the agent to VALIDATING state
            await agent_interface.set_agent_state(AgentState.VALIDATING)
            # Then to FAILED_VALIDATION state
            await agent_interface.set_agent_state(AgentState.FAILED_VALIDATION)
            # Return failure
            return False, None, {"error_type": "validation_error", "details": "Test validation error"}
        
        agent_interface._validation_manager.validate_agent_output = mock_validate_failure
        
        # Process with failed validation
        result = await agent_interface.process_with_validation(
            "Test conversation",
            system_prompt_info=("test_dir", "test_prompt"),
            schema={"type": "object"},
            current_phase="test_phase",
            operation_id="test_validation_failure_op"
        )
        
        # Verify the failed validation scenario
        assert agent_interface.agent_state == AgentState.FAILED_VALIDATION
        resource_state = await agent_interface.get_state()
        assert resource_state == ResourceState.FAILED
        
    finally:
        # Restore original methods
        agent_interface._validation_manager.validate_agent_output = original_validate
        agent_interface.agent.get_response = original_get_response

@pytest.mark.asyncio
async def test_state_transition_concurrency(agent_interface):
    """Test state transitions under concurrent operations."""
    # Ensure the interface is initialized
    await agent_interface.ensure_initialized()
    
    # Create concurrent state transition tasks
    async def transition_task(state, sleep_time):
        await asyncio.sleep(sleep_time)  # Randomize timing
        await agent_interface.set_agent_state(state, {"concurrent": True})
        return state
    
    # Launch multiple state transition tasks
    tasks = [
        asyncio.create_task(transition_task(AgentState.PROCESSING, 0.01)),
        asyncio.create_task(transition_task(AgentState.VALIDATING, 0.02)),
        asyncio.create_task(transition_task(AgentState.COMPLETE, 0.03)),
        asyncio.create_task(transition_task(AgentState.ERROR, 0.04))
    ]
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)
    
    # The final state should be the last one executed (ERROR)
    assert agent_interface.agent_state == AgentState.ERROR
    
    # The resource state should match the expected mapping for ERROR
    resource_state = await agent_interface.get_state()
    assert resource_state == ResourceState.TERMINATED

@pytest.mark.asyncio
async def test_state_transition_with_state_manager_failure(agent_interface):
    """Test state transitions when the state manager fails."""
    # Ensure the interface is initialized
    await agent_interface.ensure_initialized()
    
    # Patch the state manager's set_state to simulate failure
    original_set_state = agent_interface._state_manager.set_state
    
    async def mock_set_state_failure(*args, **kwargs):
        raise Exception("Simulated state manager failure")
    
    agent_interface._state_manager.set_state = mock_set_state_failure
    
    try:
        # Attempt to set state - should update agent_state even if state_manager fails
        await agent_interface.set_agent_state(AgentState.PROCESSING)
        
        # Verify agent_state was updated despite state manager failure
        assert agent_interface.agent_state == AgentState.PROCESSING
        
    finally:
        # Restore original method
        agent_interface._state_manager.set_state = original_set_state

@pytest.mark.asyncio
async def test_state_transition_lock_failure(agent_interface):
    """Test state transitions when the state lock acquisition fails."""
    # Ensure the interface is initialized
    await agent_interface.ensure_initialized()
    
    # Create a dummy lock that always fails to acquire
    class FailingLock:
        async def __aenter__(self):
            raise Exception("Lock acquisition simulated failure")
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    # Replace the state lock with our failing lock
    original_lock = agent_interface._state_lock
    agent_interface._state_lock = FailingLock()
    
    try:
        # Attempt to set state - should use fallback direct state setting
        await agent_interface.set_agent_state(AgentState.PROCESSING)
        
        # Verify agent_state was updated despite lock failure
        assert agent_interface.agent_state == AgentState.PROCESSING
        
    finally:
        # Restore original lock
        agent_interface._state_lock = original_lock

@pytest.mark.asyncio
async def test_rapid_state_transitions(agent_interface):
    """Test rapid transitions between all agent states."""
    # Ensure the interface is initialized
    await agent_interface.ensure_initialized()
    
    # Get all possible states
    all_states = list(AgentState)
    
    # Rapidly transition through all states
    for state in all_states:
        await agent_interface.set_agent_state(state)
        assert agent_interface.agent_state == state
    
    # Verify we can transition directly from any state to any other state
    # (trying a few key combinations)
    direct_transitions = [
        (AgentState.READY, AgentState.ERROR),
        (AgentState.ERROR, AgentState.READY),
        (AgentState.PROCESSING, AgentState.COMPLETE),
        (AgentState.VALIDATING, AgentState.FAILED_VALIDATION),
        (AgentState.FAILED_VALIDATION, AgentState.PROCESSING)
    ]
    
    for from_state, to_state in direct_transitions:
        await agent_interface.set_agent_state(from_state)
        assert agent_interface.agent_state == from_state
        
        await agent_interface.set_agent_state(to_state)
        assert agent_interface.agent_state == to_state

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])