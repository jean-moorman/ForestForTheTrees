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
    CircuitBreakerConfig, 
    ErrorClassification, 
    ErrorSeverity, 
    ErrorHandler, 
    EventQueue, 
    ResourceEventTypes, 
    StateManager, 
    CacheManager, 
    AgentContextManager, 
    MetricsManager, 
    AgentContext, 
    AgentContextType, 
    MemoryMonitor, 
    MemoryThresholds
)

from agent import Agent
from agent_validation import Validator

# Import the actual interface classes
from interface import (
    BaseInterface,
    InterfaceError,
    InitializationError,
    StateTransitionError,
    ResourceError,
    ValidationError,
    TimeoutError,
    AgentState,
    ValidationManager,
    InterfaceCache,
    InterfaceMetrics,
    AgentInterface,
    FeatureInterface,
    ComponentInterface,
    TestAgent
)

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
def validation_manager(event_queue, state_manager, agent_context_manager):
    """Create a validation manager for testing."""
    return ValidationManager(event_queue, state_manager, agent_context_manager)

# Tests for BaseInterface
@pytest.mark.asyncio
async def test_base_interface_initialization(event_queue, state_manager, agent_context_manager, cache_manager, 
                                           metrics_manager, error_handler, memory_monitor):
    # Test initialization
    interface = BaseInterface(
        "test_interface", 
        event_queue, 
        state_manager,
        agent_context_manager,
        cache_manager,
        metrics_manager,
        error_handler,
        memory_monitor
    )
    
    assert interface.interface_id == "test_interface"
    assert interface._event_queue == event_queue
    assert interface._state_manager == state_manager
    assert interface._initialized == False
    
    # Test ensure_initialized
    await interface.ensure_initialized()
    assert interface._initialized == True
    
    # Test ensure_initialized idempotency
    await interface.ensure_initialized()
    assert interface._initialized == True

@pytest.mark.asyncio
async def test_base_interface_state_management(event_queue, state_manager, agent_context_manager, cache_manager, 
                                             metrics_manager, error_handler, memory_monitor):
    interface = BaseInterface(
        "test_interface", 
        event_queue, 
        state_manager,
        agent_context_manager,
        cache_manager,
        metrics_manager,
        error_handler,
        memory_monitor
    )
    await interface.ensure_initialized()
    
    # Test set_state
    await interface.set_state(ResourceState.ACTIVE)
    state = await interface.get_state()
    assert state == ResourceState.ACTIVE
    
    # Test state change
    await interface.set_state(ResourceState.PAUSED)
    state = await interface.get_state()
    assert state == ResourceState.PAUSED
    
    # Test event emission
    assert len(event_queue._event_history) >= 2
    for event in event_queue._event_history:
        event_type = event.event_type
        payload = event.data
        if event_type == ResourceEventTypes.INTERFACE_STATE_CHANGED.value:
            assert payload["interface_id"] == "test_interface"
            
    # Test cleanup
    result = await interface.cleanup()
    assert result == True
    
    cleanup_events = [e for e in event_queue._event_history if e.event_type == ResourceEventTypes.RESOURCE_CLEANUP.value]
    assert len(cleanup_events) >= 1
    c_data = cleanup_events[0].data
    assert c_data["interface_id"] == "test_interface"
    assert c_data["status"] == "success"

# Tests for InterfaceCache
@pytest.mark.asyncio
async def test_interface_cache(event_queue, cache_manager, memory_monitor):
    cache = InterfaceCache(event_queue, "test_cache", cache_manager, memory_monitor)
    
    # Test setting cache
    await cache.set_cache("key1", "value1")
    
    # Test getting cache
    value = await cache.get_cache("key1")
    assert value == "value1"
    
    # Test cache miss
    value = await cache.get_cache("nonexistent_key")
    assert value is None
    
    # Test invalidating cache
    await cache.invalidate("key1")
    value = await cache.get_cache("key1")
    assert value is None
    
    # Test memory tracking
    assert len(memory_monitor._resource_sizes) > 0
    assert "test_cache" in memory_monitor.components

# Fix for InterfaceMetrics test - pass the metrics_manager explicitly
@pytest.mark.asyncio
async def test_interface_metrics(event_queue, state_manager, metrics_manager):
    interface_metrics = InterfaceMetrics(event_queue, state_manager, "test_interface")
    
    # Test initialization
    metric_name = f"interface:test_interface:initialized"
    assert metric_name in interface_metrics._metrics_manager.metrics
    
    # Test registering core metrics
    await interface_metrics.register_core_metrics(ResourceState.ACTIVE)
    
    health_metric = f"interface:test_interface:health"
    assert health_metric in interface_metrics._metrics_manager.metrics
    assert interface_metrics._metrics_manager.metrics[health_metric][0]["value"] == 1.0
    
    # Test validation metrics
    validation_history = [
        {"success": True, "timestamp": datetime.now().isoformat()},
        {"success": False, "timestamp": datetime.now().isoformat(), "error_analysis": {"error_type": "validation_error"}},
        {"success": True, "timestamp": datetime.now().isoformat()}
    ]
    
    await interface_metrics.register_validation_metrics(validation_history)
    
    success_rate_metric = f"interface:test_interface:validation:success_rate"
    assert success_rate_metric in interface_metrics._metrics_manager.metrics
    assert interface_metrics._metrics_manager.metrics[success_rate_metric][0]["value"] == 2/3
    
    # Test performance metrics
    await interface_metrics.register_performance_metrics(0.5, {"status": "success"})
    
    response_time_metric = f"interface:test_interface:response_time"
    assert response_time_metric in interface_metrics._metrics_manager.metrics
    assert interface_metrics._metrics_manager.metrics[response_time_metric][0]["value"] == 0.5
    
    success_metric = f"interface:test_interface:success"
    assert success_metric in interface_metrics._metrics_manager.metrics
    assert interface_metrics._metrics_manager.metrics[success_metric][0]["value"] == 1.0
    
    # Test with error
    await interface_metrics.register_performance_metrics(0.7, {"error": "test error"})
    
    assert interface_metrics._metrics_manager.metrics[success_metric][1]["value"] == 0.0

# Tests for ValidationManager
@pytest.mark.asyncio
async def test_validation_manager(event_queue, state_manager, agent_context_manager):
    validation_manager = ValidationManager(event_queue, state_manager, agent_context_manager)
    
    # Create a context for testing
    await agent_context_manager.create_context(
        agent_id="test_agent",
        operation_id="test_op",
        schema={"type": "object"},
        context_type=AgentContextType.PERSISTENT
    )
    
    # Test successful validation
    success_output = {"status": "success", "data": {"test": "value"}}
    success, validated_output, error_analysis = await validation_manager.validate_agent_output(
        "test_interface",
        success_output,
        {"type": "object"},
        "test_op"
    )
    
    assert success == True
    assert validated_output == success_output
    
    # Test failed validation
    error_output = {"error": "test error", "status": "error"}
    success, validated_output, error_analysis = await validation_manager.validate_agent_output(
        "test_interface",
        error_output,
        {"type": "object"},
        "test_op"
    )
    
    assert success == False
    assert validated_output is None
    assert "error_type" in error_analysis
    
    # Test context updates
    context = await agent_context_manager.get_context("agent_context:test_op")
    assert context.validation_attempts == 2
    assert len(context.validation_history) == 2

# New test for validation failure recovery
@pytest.mark.asyncio
async def test_validation_manager_failure_recovery(event_queue, state_manager, agent_context_manager):
    validation_manager = ValidationManager(event_queue, state_manager, agent_context_manager)
    
    # Create test context
    await agent_context_manager.create_context(
        agent_id="test_agent",
        operation_id="recovery_test",
        schema={"type": "object"},
        context_type=AgentContextType.PERSISTENT
    )
    
    # Test failed validation followed by success
    error_output = {"error": "test error", "status": "error"}
    success_output = {"status": "success", "data": {"test": "value"}}
    
    # First validation fails
    success, _, _ = await validation_manager.validate_agent_output(
        "test_interface",
        error_output,
        {"type": "object"},
        "recovery_test"
    )
    assert success == False
    
    # Second validation succeeds
    success, validated_output, _ = await validation_manager.validate_agent_output(
        "test_interface",
        success_output,
        {"type": "object"},
        "recovery_test"
    )
    assert success == True
    assert validated_output == success_output
    
    # Check context updates
    context = await agent_context_manager.get_context("agent_context:recovery_test")
    assert context.validation_attempts == 2
    assert len(context.validation_history) == 2
    assert context.validation_history[0]["success"] == False
    assert context.validation_history[1]["success"] == True

# Tests for AgentInterface
@pytest.mark.asyncio
async def test_agent_interface_initialization(event_queue, state_manager, context_manager, 
                                             cache_manager, metrics_manager, error_handler, 
                                             memory_monitor):
    agent_interface = AgentInterface(
        "test_agent",
        event_queue,
        state_manager,
        context_manager,
        cache_manager,
        metrics_manager,
        error_handler,
        memory_monitor
    )
    
    assert agent_interface.interface_id == "agent:test_agent"
    assert agent_interface.agent_state == AgentState.READY
    assert agent_interface.model == "claude-3-7-sonnet-20250219"
    
    # Test initialization
    await agent_interface.ensure_initialized()
    assert agent_interface._initialized == True

@pytest.mark.asyncio
async def test_agent_interface_state_management(event_queue, state_manager, context_manager, 
                                              cache_manager, metrics_manager, error_handler, 
                                              memory_monitor):
    agent_interface = AgentInterface(
        "test_agent",
        event_queue,
        state_manager,
        context_manager,
        cache_manager,
        metrics_manager,
        error_handler,
        memory_monitor
    )
    
    await agent_interface.ensure_initialized()
    
    # Test agent state setting
    await agent_interface.set_agent_state(AgentState.PROCESSING)
    assert agent_interface.agent_state == AgentState.PROCESSING
    
    resource_state = await agent_interface.get_state()
    assert resource_state == ResourceState.ACTIVE
    
    # Test different agent states
    await agent_interface.set_agent_state(AgentState.VALIDATING)
    assert agent_interface.agent_state == AgentState.VALIDATING
    
    resource_state = await agent_interface.get_state()
    assert resource_state == ResourceState.PAUSED
    
    await agent_interface.set_agent_state(AgentState.ERROR)
    assert agent_interface.agent_state == AgentState.ERROR
    
    resource_state = await agent_interface.get_state()
    assert resource_state == ResourceState.TERMINATED

@pytest.mark.asyncio
async def test_agent_interface_process_with_validation(event_queue, state_manager, context_manager, 
                                                     cache_manager, metrics_manager, error_handler, 
                                                     memory_monitor):
    agent_interface = AgentInterface(
        "test_agent",
        event_queue,
        state_manager,
        context_manager,
        cache_manager,
        metrics_manager,
        error_handler,
        memory_monitor
    )
    
    # Test successful processing
    result = await agent_interface.process_with_validation(
        "Test conversation",
        system_prompt_info=("test_dir", "test_prompt"),
        schema={"type": "object"},
        current_phase="test_phase",
        operation_id="test_op"
    )
    
    assert "message" in result
    assert result["status"] == "success"
    assert result["request_id"] == "test_op"
    
    # Test error handling
    result = await agent_interface.process_with_validation(
        "Test with error in it",
        system_prompt_info=("test_dir", "test_prompt"),
        schema={"type": "object"},
        current_phase="test_phase",
        operation_id="test_error_op"
    )
    
    assert "error" in result
    assert result["status"] == "error"
    assert result["request_id"] == "test_error_op"

# Test thorough cleanup
@pytest.mark.asyncio
async def test_thorough_cleanup(event_queue, state_manager, context_manager, cache_manager, 
                               metrics_manager, error_handler, memory_monitor):
    interface = BaseInterface(
        "cleanup_test", 
        event_queue, 
        state_manager,
        context_manager,
        cache_manager,
        metrics_manager,
        error_handler,
        memory_monitor
    )
    await interface.ensure_initialized()
    
    # Register with memory monitor
    assert "cleanup_test" in memory_monitor.components
    
    # Execute cleanup
    result = await interface.cleanup()
    assert result == True
    
    # Verify component was unregistered
    assert "cleanup_test" not in memory_monitor.components
    
    # Verify cleanup state was set
    cleanup_state = await state_manager.get_state(f"cleanup:cleanup_test")
    assert cleanup_state is not None
    assert "status" in cleanup_state and cleanup_state["status"] == "completed"
    
    # Verify event queue is stopped
    assert not event_queue._running

# Test initialization failure
@pytest.mark.asyncio
async def test_base_interface_initialization_failure():
    # Create a mock event queue that fails to start
    failing_queue = EventQueue()
    failing_queue._running = False
    
    # Mock the start method to always fail
    original_start = failing_queue.start
    async def mock_start():
        return False
    failing_queue.start = mock_start
    
    # Create minimal required managers
    state_manager = StateManager(failing_queue)
    context_manager = AgentContextManager(failing_queue)
    cache_manager = CacheManager(failing_queue)
    metrics_manager = MetricsManager(failing_queue)
    error_handler = ErrorHandler(failing_queue)
    memory_monitor = MemoryMonitor(failing_queue)
    
    interface = BaseInterface(
        "failure_test", 
        failing_queue,
        state_manager,
        context_manager,
        cache_manager,
        metrics_manager,
        error_handler,
        memory_monitor
    )
    
    # Test initialization failure
    with pytest.raises(InitializationError):
        await interface.ensure_initialized()

# Tests for FeatureInterface
@pytest.mark.asyncio
async def test_feature_interface(event_queue, state_manager, context_manager, cache_manager, 
                                metrics_manager, error_handler, memory_monitor):
    feature_interface = FeatureInterface(
        "test_feature", 
        event_queue,
        state_manager,
        context_manager,
        cache_manager,
        metrics_manager,
        error_handler,
        memory_monitor
    )
    
    assert feature_interface.interface_id == "feature:test_feature"
    
    # Test state management
    feature_interface.set_feature_state("test_key", "test_value")
    assert feature_interface.get_feature_state("test_key") == "test_value"
    
    # Test missing state
    assert feature_interface.get_feature_state("nonexistent_key") is None

# Tests for ComponentInterface
@pytest.mark.asyncio
async def test_component_interface(event_queue, state_manager, context_manager, cache_manager, 
                                  metrics_manager, error_handler, memory_monitor):
    component_interface = ComponentInterface(
        "test_component", 
        event_queue,
        state_manager,
        context_manager,
        cache_manager,
        metrics_manager,
        error_handler,
        memory_monitor
    )
    
    assert component_interface.interface_id == "component:test_component"
    
    # Test initialization
    await component_interface.ensure_initialized()
    assert component_interface._initialized == True
    
    # Test cleanup
    result = await component_interface.cleanup()
    assert result == True

# Tests for TestAgent
@pytest.mark.asyncio
async def test_test_agent():
    test_agent = TestAgent()
    
    # Test initialization
    init_result = await test_agent.initialize()
    assert init_result == True
    
    # Test response generation
    response = await test_agent.get_response(
        "Test conversation",
        schema={"type": "object"},
        current_phase="test_phase",
        operation_id="test_op"
    )
    
    assert response["message"] == "Test response"
    assert response["status"] == "success"
    assert response["data"]["conversation"] == "Test conversation"
    assert response["data"]["phase"] == "test_phase"
    
    # Test process_with_validation
    result = await test_agent.process_with_validation(
        "Test conversation",
        system_prompt_info=("test_dir", "test_prompt"),
        schema={"type": "object"},
        current_phase="test_phase",
        operation_id="test_op_2"
    )
    
    assert result["message"] == "Test response"
    assert result["status"] == "success"
    assert result["request_id"] == "test_op_2"

# Test error handling scenarios
@pytest.mark.asyncio
async def test_error_handling_in_agent_interface(event_queue, state_manager, context_manager, 
                                               cache_manager, metrics_manager, error_handler, 
                                               memory_monitor):
    agent_interface = AgentInterface(
        "test_agent",
        event_queue,
        state_manager,
        context_manager,
        cache_manager,
        metrics_manager,
        error_handler,
        memory_monitor
    )
    
    # Patch agent.get_response to simulate timeout
    async def mock_timeout(*args, **kwargs):
        await asyncio.sleep(0.5)  # Sleep longer than the timeout
        return {"message": "This should not be returned"}
    
    agent_interface.agent.get_response = mock_timeout
    
    # Test timeout handling
    result = await agent_interface.process_with_validation(
        "Test conversation",
        system_prompt_info=("test_dir", "test_prompt"),
        schema={"type": "object"},
        timeout=0.1  # Very short timeout
    )
    
    assert "error" in result
    assert "timeout" in result["error"].lower()
    assert agent_interface.agent_state == AgentState.ERROR
    
    # Patch agent.get_response to simulate exception
    async def mock_exception(*args, **kwargs):
        raise ValueError("Simulated exception")
    
    agent_interface.agent.get_response = mock_exception
    
    # Test exception handling
    result = await agent_interface.process_with_validation(
        "Test conversation",
        system_prompt_info=("test_dir", "test_prompt"),
        schema={"type": "object"}
    )
    
    assert "error" in result
    assert "exception" in result["error"].lower()
    assert agent_interface.agent_state == AgentState.ERROR

def main():
    """Run the full test suite when this file is executed directly."""
    import sys
    import pytest
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Running interface tests...")
    
    # Run the tests with appropriate pytest flags
    # -v: verbose output
    # -s: show print statements
    # --asyncio-mode=auto: handle async tests properly
    args = ["-v", "-s", "--asyncio-mode=auto", __file__]
    
    # Add any additional command-line arguments
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])
    
    # Run pytest with our arguments and exit with its return code
    sys.exit(pytest.main(args))

# if __name__ == "__main__":
#     # Only run when the file is executed directly, not when imported
#     sys.exit(pytest.main([__file__]))
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])