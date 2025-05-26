"""
Tests for FunctionalityInterface and FeatureInterface in the FFTT system.
"""

import pytest
import asyncio
import pytest_asyncio
import logging
from typing import List, Dict, Any

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

from interfaces.feature.functionality import FunctionalityInterface
from interfaces.feature.interface import FeatureInterface

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
def functionality_interface(event_queue, state_manager, agent_context_manager, cache_manager, 
                          metrics_manager, error_handler, memory_monitor):
    """Create a functionality interface for testing."""
    return FunctionalityInterface(
        "test_functionality",
        event_queue,
        state_manager,
        agent_context_manager,
        cache_manager,
        metrics_manager,
        error_handler,
        memory_monitor
    )

@pytest.fixture
def feature_interface(event_queue, state_manager, agent_context_manager, cache_manager, 
                     metrics_manager, error_handler, memory_monitor):
    """Create a feature interface for testing."""
    return FeatureInterface(
        "test_feature",
        event_queue,
        state_manager,
        agent_context_manager,
        cache_manager,
        metrics_manager,
        error_handler,
        memory_monitor
    )

# Tests for FunctionalityInterface
@pytest.mark.asyncio
async def test_functionality_interface_initialization(functionality_interface):
    """Test functionality interface initialization."""
    assert functionality_interface.interface_id == "functionality:test_functionality"
    assert functionality_interface.functionality_id == "test_functionality"
    assert functionality_interface._functionality_state == {}
    assert functionality_interface._dependencies == set()
    
    # Test initialization
    await functionality_interface.ensure_initialized()
    assert functionality_interface._initialized == True

@pytest.mark.asyncio
async def test_set_get_functionality_state(functionality_interface):
    """Test setting and getting functionality state."""
    # Ensure the interface is initialized
    await functionality_interface.ensure_initialized()
    
    # Test setting state
    await functionality_interface.set_functionality_state("test_key", "test_value")
    assert functionality_interface._functionality_state["test_key"] == "test_value"
    
    # Test getting state from local cache
    value = await functionality_interface.get_functionality_state("test_key")
    assert value == "test_value"
    
    # Test getting state that doesn't exist
    value = await functionality_interface.get_functionality_state("nonexistent_key")
    assert value is None
    
    # Test getting state from state manager
    state_key = f"functionality:{functionality_interface.functionality_id}:state:test_key"
    state = await functionality_interface._state_manager.get_state(state_key)
    assert state == "test_value"

@pytest.mark.asyncio
async def test_add_get_dependencies(functionality_interface):
    """Test adding and getting dependencies."""
    # Ensure the interface is initialized
    await functionality_interface.ensure_initialized()
    
    # Test adding a dependency
    await functionality_interface.add_dependency("dependency_functionality")
    assert "dependency_functionality" in functionality_interface._dependencies
    
    # Test getting dependencies
    dependencies = await functionality_interface.get_dependencies()
    assert "dependency_functionality" in dependencies
    assert len(dependencies) == 1
    
    # Add another dependency
    await functionality_interface.add_dependency("another_dependency")
    dependencies = await functionality_interface.get_dependencies()
    assert len(dependencies) == 2
    assert "dependency_functionality" in dependencies
    assert "another_dependency" in dependencies
    
    # Test getting dependencies from state manager
    state_key = f"functionality:{functionality_interface.functionality_id}:dependencies"
    state = await functionality_interface._state_manager.get_state(state_key)
    assert len(state) == 2
    assert "dependency_functionality" in state
    assert "another_dependency" in state

@pytest.mark.asyncio
async def test_validate_functionality(functionality_interface):
    """Test validating a functionality."""
    # Ensure the interface is initialized
    await functionality_interface.ensure_initialized()
    
    # Test validation without dependencies
    validation_result = await functionality_interface.validate()
    assert validation_result["valid"] == True
    assert len(validation_result["errors"]) == 0
    
    # Add self as a dependency (should create a cyclic dependency)
    await functionality_interface.add_dependency(functionality_interface.functionality_id)
    
    # Test validation with cyclic dependency
    validation_result = await functionality_interface.validate()
    assert validation_result["valid"] == False
    assert len(validation_result["errors"]) == 1
    assert "depends on itself" in validation_result["errors"][0]

# Tests for FeatureInterface
@pytest.mark.asyncio
async def test_feature_interface_initialization(feature_interface):
    """Test feature interface initialization."""
    assert feature_interface.interface_id == "feature:test_feature"
    assert feature_interface.feature_id == "test_feature"
    assert feature_interface._feature_state == {}
    assert feature_interface._dependencies == set()
    assert feature_interface._functionalities == set()
    
    # Test initialization
    await feature_interface.ensure_initialized()
    assert feature_interface._initialized == True

@pytest.mark.asyncio
async def test_set_get_feature_state(feature_interface):
    """Test setting and getting feature state."""
    # Ensure the interface is initialized
    await feature_interface.ensure_initialized()
    
    # Test setting state
    await feature_interface.set_feature_state("test_key", "test_value")
    assert feature_interface._feature_state["test_key"] == "test_value"
    
    # Test getting state from local cache
    value = await feature_interface.get_feature_state("test_key")
    assert value == "test_value"
    
    # Test getting state that doesn't exist
    value = await feature_interface.get_feature_state("nonexistent_key")
    assert value is None
    
    # Test getting state from state manager
    state_key = f"feature:{feature_interface.feature_id}:state:test_key"
    state = await feature_interface._state_manager.get_state(state_key)
    assert state == "test_value"

@pytest.mark.asyncio
async def test_add_get_dependencies_feature(feature_interface):
    """Test adding and getting dependencies for a feature."""
    # Ensure the interface is initialized
    await feature_interface.ensure_initialized()
    
    # Test adding a dependency
    await feature_interface.add_dependency("dependency_feature")
    assert "dependency_feature" in feature_interface._dependencies
    
    # Test getting dependencies
    dependencies = await feature_interface.get_dependencies()
    assert "dependency_feature" in dependencies
    assert len(dependencies) == 1
    
    # Add another dependency
    await feature_interface.add_dependency("another_dependency")
    dependencies = await feature_interface.get_dependencies()
    assert len(dependencies) == 2
    assert "dependency_feature" in dependencies
    assert "another_dependency" in dependencies
    
    # Test getting dependencies from state manager
    state_key = f"feature:{feature_interface.feature_id}:dependencies"
    state = await feature_interface._state_manager.get_state(state_key)
    assert len(state) == 2
    assert "dependency_feature" in state
    assert "another_dependency" in state

@pytest.mark.asyncio
async def test_add_get_functionalities(feature_interface):
    """Test adding and getting functionalities."""
    # Ensure the interface is initialized
    await feature_interface.ensure_initialized()
    
    # Test adding a functionality
    await feature_interface.add_functionality("test_functionality")
    assert "test_functionality" in feature_interface._functionalities
    
    # Test getting functionalities
    functionalities = await feature_interface.get_functionalities()
    assert "test_functionality" in functionalities
    assert len(functionalities) == 1
    
    # Add another functionality
    await feature_interface.add_functionality("another_functionality")
    functionalities = await feature_interface.get_functionalities()
    assert len(functionalities) == 2
    assert "test_functionality" in functionalities
    assert "another_functionality" in functionalities
    
    # Test getting functionalities from state manager
    state_key = f"feature:{feature_interface.feature_id}:functionalities"
    state = await feature_interface._state_manager.get_state(state_key)
    assert len(state) == 2
    assert "test_functionality" in state
    assert "another_functionality" in state

@pytest.mark.asyncio
async def test_validate_feature(feature_interface):
    """Test validating a feature."""
    # Ensure the interface is initialized
    await feature_interface.ensure_initialized()
    
    # Test validation without functionalities (should give warning)
    validation_result = await feature_interface.validate()
    assert validation_result["valid"] == True
    assert len(validation_result["errors"]) == 0
    assert len(validation_result["warnings"]) == 1
    assert "no functionalities" in validation_result["warnings"][0]
    
    # Add a functionality
    await feature_interface.add_functionality("test_functionality")
    
    # Test validation with functionality (should have no warnings)
    validation_result = await feature_interface.validate()
    assert validation_result["valid"] == True
    assert len(validation_result["errors"]) == 0
    assert len(validation_result["warnings"]) == 0
    
    # Add self as a dependency (should create a cyclic dependency)
    await feature_interface.add_dependency(feature_interface.feature_id)
    
    # Test validation with cyclic dependency
    validation_result = await feature_interface.validate()
    assert validation_result["valid"] == False
    assert len(validation_result["errors"]) == 1
    assert "depends on itself" in validation_result["errors"][0]

@pytest.mark.asyncio
async def test_feature_functionality_integration(feature_interface, functionality_interface):
    """Test integration between feature and functionality interfaces."""
    # Ensure interfaces are initialized
    await feature_interface.ensure_initialized()
    await functionality_interface.ensure_initialized()
    
    # Add functionality to feature
    await feature_interface.add_functionality(functionality_interface.functionality_id)
    
    # Verify functionality is in the feature
    functionalities = await feature_interface.get_functionalities()
    assert functionality_interface.functionality_id in functionalities
    
    # Add feature as dependency to functionality
    await functionality_interface.add_dependency(feature_interface.feature_id)
    
    # Verify feature is in functionality dependencies
    dependencies = await functionality_interface.get_dependencies()
    assert feature_interface.feature_id in dependencies
    
    # Set functionality state
    test_data = {"key": "value", "nested": {"data": True}}
    await functionality_interface.set_functionality_state("complex_data", test_data)
    
    # Verify state was set
    retrieved_data = await functionality_interface.get_functionality_state("complex_data")
    assert retrieved_data == test_data
    assert retrieved_data["nested"]["data"] == True

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])