"""
Tests for the guideline management functionality in the interface module.
"""

import pytest
import asyncio
import pytest_asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import logging
import sys
import time
from datetime import datetime, timedelta
import json
import random

# Import real implementations instead of creating mocks
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

from interfaces.agent.guideline import GuidelineManager
from interfaces.agent.interface import AgentInterface
from agent import Agent

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
def guideline_manager(event_queue, state_manager):
    """Create a guideline manager for testing."""
    return GuidelineManager(event_queue, state_manager, "test_agent")

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

# Tests for GuidelineManager
@pytest.mark.asyncio
async def test_guideline_manager_initialization(guideline_manager):
    """Test guideline manager initialization."""
    assert guideline_manager._agent_id == "test_agent"
    assert isinstance(guideline_manager._event_queue, EventQueue)
    assert isinstance(guideline_manager._state_manager, StateManager)
    assert guideline_manager._guideline_updates == {}

@pytest.mark.asyncio
async def test_apply_guideline_update_success(guideline_manager, state_manager):
    """Test successful guideline update application."""
    # Define test data
    origin_agent_id = "origin_agent"
    propagation_context = {
        "update_id": "test_update_1",
        "required_adaptations": [
            {
                "type": "interface_adaptation",
                "description": "Update interface elements"
            }
        ]
    }
    update_data = {
        "interfaces": {
            "api_version": "2.0",
            "endpoints": ["endpoint1", "endpoint2"]
        }
    }
    
    # Apply the update
    result = await guideline_manager.apply_guideline_update(
        origin_agent_id,
        propagation_context,
        update_data
    )
    
    # Verify the result
    assert result["success"] == True
    assert result["agent_id"] == "test_agent"
    assert result["update_id"] == "test_update_1"
    
    # Check the state manager for stored update
    update_state = await state_manager.get_state(
        "agent:test_agent:guideline_update:test_update_1"
    )
    assert update_state is not None
    assert update_state["status"] == "applied"
    assert update_state["origin_agent_id"] == origin_agent_id
    
    # Check guideline state
    guideline_state = await state_manager.get_state("agent:test_agent:guideline")
    assert guideline_state is not None
    assert guideline_state["interfaces"]["api_version"] == "2.0"
    assert len(guideline_state["interfaces"]["endpoints"]) == 2

@pytest.mark.asyncio
async def test_apply_guideline_update_error(guideline_manager, state_manager):
    """Test guideline update application with error."""
    # Define test data
    origin_agent_id = "origin_agent"
    propagation_context = {
        "update_id": "test_update_error",
        "required_adaptations": [
            {
                "type": "interface_adaptation",
                "description": "Update interface elements"
            }
        ]
    }
    update_data = {
        "interfaces": {
            "api_version": "2.0",
            "endpoints": ["endpoint1", "endpoint2"]
        }
    }
    
    # Patch the _apply_adaptations method to raise an exception
    async def mock_apply_adaptations(*args, **kwargs):
        raise ValueError("Test error")
    
    original_apply_adaptations = guideline_manager._apply_adaptations
    guideline_manager._apply_adaptations = mock_apply_adaptations
    
    try:
        # Apply the update, which should fail
        result = await guideline_manager.apply_guideline_update(
            origin_agent_id,
            propagation_context,
            update_data
        )
        
        # Verify the result
        assert result["success"] == False
        assert "Error applying guideline update" in result["reason"]
        
        # Check the state manager for stored update with error
        update_state = await state_manager.get_state(
            "agent:test_agent:guideline_update:test_update_error"
        )
        assert update_state is not None
        assert update_state["status"] == "error"
        assert "error" in update_state
        
    finally:
        # Restore the original method
        guideline_manager._apply_adaptations = original_apply_adaptations

@pytest.mark.asyncio
async def test_verify_guideline_update_success(guideline_manager, state_manager):
    """Test successful guideline update verification."""
    # First apply an update to verify
    origin_agent_id = "origin_agent"
    update_id = "verify_test_update"
    propagation_context = {
        "update_id": update_id,
        "required_adaptations": [
            {
                "type": "interface_adaptation",
                "description": "Update interface elements"
            }
        ]
    }
    update_data = {
        "interfaces": {
            "api_version": "2.0",
            "endpoints": ["endpoint1", "endpoint2"]
        }
    }
    
    # Apply the update
    await guideline_manager.apply_guideline_update(
        origin_agent_id,
        propagation_context,
        update_data
    )
    
    # Verify the update
    result = await guideline_manager.verify_guideline_update(update_id)
    
    # Check the verification result
    assert result["verified"] == True
    assert result["agent_id"] == "test_agent"
    assert result["update_id"] == update_id

@pytest.mark.asyncio
async def test_verify_guideline_update_failure(guideline_manager):
    """Test guideline update verification failure."""
    # Try to verify an update that doesn't exist
    result = await guideline_manager.verify_guideline_update("nonexistent_update")
    
    # Check the verification result
    assert result["verified"] == False
    assert "not found" in result["errors"][0]

@pytest.mark.asyncio
async def test_check_update_readiness(guideline_manager):
    """Test checking update readiness."""
    # Define test data
    origin_agent_id = "origin_agent"
    propagation_context = {
        "update_id": "readiness_test",
        "required_adaptations": []
    }
    
    # Check readiness
    result = await guideline_manager.check_update_readiness(
        origin_agent_id,
        propagation_context
    )
    
    # Verify result
    assert result["ready"] == True
    assert result["concerns"] == []

@pytest.mark.asyncio
async def test_check_update_readiness_with_concerns(guideline_manager):
    """Test checking update readiness with concerns."""
    # Define test data
    origin_agent_id = "origin_agent"
    propagation_context = {
        "update_id": "readiness_test_concerns"
    }
    
    # Patch the _check_adaptation_concerns method to return concerns
    async def mock_check_concerns(*args, **kwargs):
        return [{
            "type": "test_concern",
            "description": "Test concern for readiness"
        }]
    
    original_check_concerns = guideline_manager._check_adaptation_concerns
    guideline_manager._check_adaptation_concerns = mock_check_concerns
    
    try:
        # Check readiness
        result = await guideline_manager.check_update_readiness(
            origin_agent_id,
            propagation_context
        )
        
        # Verify result
        assert result["ready"] == False
        assert len(result["concerns"]) == 1
        assert result["concerns"][0]["type"] == "test_concern"
        
    finally:
        # Restore the original method
        guideline_manager._check_adaptation_concerns = original_check_concerns

# Tests for AgentInterface guideline methods
@pytest.mark.asyncio
async def test_agent_interface_apply_guideline_update(agent_interface):
    """Test agent interface apply_guideline_update method."""
    # Initialize the agent interface
    await agent_interface.ensure_initialized()
    
    # Define test data
    origin_agent_id = "origin_agent"
    propagation_context = {
        "update_id": "agent_interface_test",
        "required_adaptations": []
    }
    update_data = {
        "interfaces": {
            "api_version": "2.0",
            "endpoints": ["endpoint1", "endpoint2"]
        }
    }
    
    # Apply the update
    result = await agent_interface.apply_guideline_update(
        origin_agent_id,
        propagation_context,
        update_data
    )
    
    # Verify result
    assert result["success"] == True
    assert result["agent_id"] == "agent:test_agent"
    assert result["update_id"] == "agent_interface_test"

@pytest.mark.asyncio
async def test_agent_interface_verify_guideline_update(agent_interface):
    """Test agent interface verify_guideline_update method."""
    # Initialize the agent interface
    await agent_interface.ensure_initialized()
    
    # Define test data
    origin_agent_id = "origin_agent"
    update_id = "agent_verify_test"
    propagation_context = {
        "update_id": update_id,
        "required_adaptations": []
    }
    update_data = {
        "interfaces": {
            "api_version": "2.0",
            "endpoints": ["endpoint1", "endpoint2"]
        }
    }
    
    # First apply an update
    await agent_interface.apply_guideline_update(
        origin_agent_id,
        propagation_context,
        update_data
    )
    
    # Then verify it
    result = await agent_interface.verify_guideline_update(update_id)
    
    # Check verification result
    assert result["verified"] == True
    assert result["agent_id"] == "agent:test_agent"
    assert result["update_id"] == update_id

@pytest.mark.asyncio
async def test_agent_interface_check_update_readiness(agent_interface):
    """Test agent interface check_update_readiness method."""
    # Initialize the agent interface
    await agent_interface.ensure_initialized()
    
    # Define test data
    origin_agent_id = "origin_agent"
    propagation_context = {
        "update_id": "agent_readiness_test",
        "required_adaptations": []
    }
    
    # Check readiness
    result = await agent_interface.check_update_readiness(
        origin_agent_id,
        propagation_context
    )
    
    # Verify result
    assert result["ready"] == True
    assert result["concerns"] == []

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])