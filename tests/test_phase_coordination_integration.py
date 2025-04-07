"""
Forest For The Trees (FFTT) Phase Coordination Integration Tests
---------------------------------------------------------------
Tests the integration of the enhanced phase coordination system with the existing phases.
"""
import asyncio
import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from resources import (
    EventQueue,
    StateManager,
    CacheManager,
    MetricsManager,
    AgentContextManager,
    ResourceEventTypes
)
from resources.phase_coordinator import PhaseState, PhaseType, PhaseContext
from resources.phase_coordination_integration import (
    PhaseCoordinationIntegration,
    PhaseOneToTwoTransitionHandler,
    PhaseTwoToThreeTransitionHandler,
    PhaseThreeToFourTransitionHandler
)
from resources.errors import ErrorHandler
from resources.monitoring import SystemMonitor, MemoryMonitor

# Setup basic test fixtures
@pytest.fixture
async def event_queue():
    queue = EventQueue()
    await queue.start()
    yield queue
    await queue.stop()

@pytest.fixture
def state_manager(event_queue):
    return StateManager(event_queue)

@pytest.fixture
def cache_manager(event_queue):
    return CacheManager(event_queue)

@pytest.fixture
def context_manager(event_queue):
    return AgentContextManager(event_queue)

@pytest.fixture
def metrics_manager(event_queue):
    return MetricsManager(event_queue)

@pytest.fixture
def error_handler(event_queue):
    return ErrorHandler(event_queue)

@pytest.fixture
def memory_monitor(event_queue):
    return MemoryMonitor(event_queue)

@pytest.fixture
def system_monitor(event_queue):
    return SystemMonitor(event_queue)

@pytest.fixture
async def integration(
    event_queue,
    state_manager,
    context_manager,
    cache_manager,
    metrics_manager,
    error_handler,
    memory_monitor,
    system_monitor
):
    integration = PhaseCoordinationIntegration(
        event_queue,
        state_manager,
        context_manager,
        cache_manager,
        metrics_manager,
        error_handler,
        memory_monitor,
        system_monitor
    )
    await integration.initialize()
    yield integration

# Test basic initialization
@pytest.mark.asyncio
async def test_integration_initialization(integration):
    """Test that integration initializes properly"""
    assert integration._initialized == True
    
    # Check transition handlers were registered
    assert len(integration._transition_handlers) == 3
    assert (PhaseType.ONE, PhaseType.TWO) in integration._transition_handlers
    assert (PhaseType.TWO, PhaseType.THREE) in integration._transition_handlers
    assert (PhaseType.THREE, PhaseType.FOUR) in integration._transition_handlers

# Test phase initialization
@pytest.mark.asyncio
async def test_phase_initialization(integration):
    """Test phase initialization"""
    # Initialize Phase One
    phase_one_id = await integration.initialize_phase_one({"test_config": "phase_one"})
    assert phase_one_id.startswith("phase_one_")
    
    # Get status
    status = await integration.get_phase_status(phase_one_id)
    assert status["phase_id"] == phase_one_id
    assert status["phase_type"] == PhaseType.ONE.value
    assert status["state"] == PhaseState.READY.name

# Test nested phase execution
@pytest.mark.asyncio
async def test_nested_phase_execution(integration):
    """Test nested phase execution from Phase One to Phase Two"""
    # Initialize Phase One
    phase_one_id = await integration.initialize_phase_one({"test_config": "phase_one"})
    
    # Mock the phase coordinator's coordinate_nested_execution to return a successful result
    with patch.object(
        integration._phase_coordinator, 
        'coordinate_nested_execution', 
        new_callable=AsyncMock
    ) as mock_coordinate:
        mock_result = {
            "status": "success",
            "result": {"execution_complete": True}
        }
        mock_coordinate.return_value = mock_result
        
        # Test coordinating nested execution
        result = await integration.coordinate_nested_execution(
            phase_one_id,
            PhaseType.TWO,
            {"input": "test_data"},
            {"test_config": "phase_two"}
        )
        
        # Verify the result
        assert result == mock_result
        
        # Verify the coordinate_nested_execution was called
        mock_coordinate.assert_called_once()
        
        # Extract the call arguments
        call_args = mock_coordinate.call_args[0]
        
        # Verify parent phase ID was passed correctly
        assert call_args[0] == phase_one_id
        
        # Verify the input was enhanced with execution context
        assert "parent_phase_id" in call_args[2]
        assert "execution_id" in call_args[2]

# Test phase transition handlers
@pytest.mark.asyncio
async def test_phase_one_to_two_handler():
    """Test Phase One to Two transition handler"""
    handler = PhaseOneToTwoTransitionHandler()
    
    # Test before_start
    input_data = {
        "structural_components": [
            {"id": "comp1", "dependencies": []},
            {"id": "comp2", "dependencies": ["comp1"]},
            {"id": "comp3", "dependencies": ["comp1"]}
        ]
    }
    
    result = await handler.before_start("test_phase", input_data)
    
    # Verify dependency analysis was added
    assert "dependency_analysis" in result
    assert "execution_strategy" in result
    
    # Check execution order is correct
    assert result["dependency_analysis"]["execution_order"] == ["comp1", "comp2", "comp3"]
    
    # Test parallel groups were identified correctly
    assert len(result["dependency_analysis"]["parallel_groups"]) == 2
    assert "comp1" in result["dependency_analysis"]["parallel_groups"][0]
    assert all(comp in ["comp2", "comp3"] for comp in result["dependency_analysis"]["parallel_groups"][1])

@pytest.mark.asyncio
async def test_phase_two_to_three_handler():
    """Test Phase Two to Three transition handler"""
    handler = PhaseTwoToThreeTransitionHandler()
    
    # Test before_start
    input_data = {
        "features": [
            {"id": "feat1", "dependencies": []},
            {"id": "feat2", "dependencies": ["feat1"]},
            {"id": "feat3", "dependencies": []}
        ]
    }
    
    result = await handler.before_start("test_phase", input_data)
    
    # Verify execution context was added
    assert "execution_context" in result
    assert "feature_groups" in result
    
    # Check feature groups were identified correctly
    assert len(result["feature_groups"]) == 2
    assert any("feat1" in group and "feat3" in group for group in result["feature_groups"])
    assert any("feat2" in group for group in result["feature_groups"])

@pytest.mark.asyncio
async def test_phase_three_to_four_handler():
    """Test Phase Three to Four transition handler"""
    handler = PhaseThreeToFourTransitionHandler()
    
    # Test before_start
    input_data = {
        "feature_id": "feat1",
        "requirements": {"name": "Test Feature"}
    }
    
    result = await handler.before_start("test_phase", input_data)
    
    # Verify compiler config was added
    assert "compiler_config" in result
    assert "execution_context" in result
    assert result["compiler_config"]["max_iterations"] == 5

# Test phase health
@pytest.mark.asyncio
async def test_get_phase_health(integration):
    """Test getting phase health information"""
    # Mock the phase coordinator's get_phase_health to return health info
    with patch.object(
        integration._phase_coordinator, 
        'get_phase_health', 
        new_callable=AsyncMock
    ) as mock_health:
        mock_health.return_value = {
            "status": "HEALTHY",
            "description": "All phases healthy",
            "state_counts": {
                "INITIALIZING": 0,
                "READY": 2,
                "RUNNING": 1,
                "COMPLETED": 3,
                "FAILED": 0
            }
        }
        
        # Get health status
        health = await integration.get_phase_health()
        
        # Verify the result
        assert health["status"] == "HEALTHY"
        assert health["state_counts"]["RUNNING"] == 1
        assert health["state_counts"]["COMPLETED"] == 3

# Test checkpoint and rollback
@pytest.mark.asyncio
async def test_checkpoint_and_rollback(integration):
    """Test creating checkpoints and rolling back"""
    # Initialize Phase One
    phase_one_id = await integration.initialize_phase_one({"test_config": "phase_one"})
    
    # Mock the phase coordinator's create_checkpoint to return a checkpoint ID
    with patch.object(
        integration._phase_coordinator, 
        'create_checkpoint', 
        new_callable=AsyncMock
    ) as mock_checkpoint:
        checkpoint_id = f"checkpoint_{phase_one_id}_123456"
        mock_checkpoint.return_value = checkpoint_id
        
        # Create checkpoint
        result = await integration.create_checkpoint(phase_one_id)
        
        # Verify the result
        assert result == checkpoint_id
        
    # Mock the phase coordinator's rollback_to_checkpoint to return success
    with patch.object(
        integration._phase_coordinator, 
        'rollback_to_checkpoint', 
        new_callable=AsyncMock
    ) as mock_rollback:
        mock_rollback.return_value = True
        
        # Rollback to checkpoint
        result = await integration.rollback_to_checkpoint(checkpoint_id)
        
        # Verify the result
        assert result == True

# Integration test for the complete nested execution flow
@pytest.mark.asyncio
async def test_complete_phase_flow(integration):
    """Test the complete phase flow with nested execution"""
    # Initialize Phase One
    phase_one_id = await integration.initialize_phase_one({"test_config": "phase_one"})
    
    # Start Phase One
    with patch.object(
        integration._phase_coordinator, 
        'start_phase', 
        new_callable=AsyncMock
    ) as mock_start:
        # Phase One completion result
        mock_start.return_value = {
            "status": "completed",
            "structural_components": [
                {"id": "comp1", "dependencies": []},
                {"id": "comp2", "dependencies": ["comp1"]}
            ]
        }
        
        # Start Phase One
        phase_one_result = await integration.start_phase(
            phase_one_id, 
            {"input_data": "phase_one_input"}
        )
        
        # Verify Phase One result
        assert phase_one_result["status"] == "completed"
        assert len(phase_one_result["structural_components"]) == 2
    
    # Now coordinate nested execution from Phase One to Phase Two
    with patch.object(
        integration._phase_coordinator, 
        'coordinate_nested_execution', 
        new_callable=AsyncMock
    ) as mock_coordinate:
        # Phase Two completion result
        mock_coordinate.return_value = {
            "status": "completed",
            "components_processed": 2,
            "components_completed": 2
        }
        
        # Coordinate nested execution
        phase_two_result = await integration.coordinate_nested_execution(
            phase_one_id,
            PhaseType.TWO,
            {"structural_components": phase_one_result["structural_components"]},
            {"test_config": "phase_two"}
        )
        
        # Verify Phase Two result
        assert phase_two_result["status"] == "completed"
        assert phase_two_result["components_processed"] == 2
        assert phase_two_result["components_completed"] == 2