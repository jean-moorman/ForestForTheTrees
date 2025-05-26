"""
Simple test for interface imports and basic functionality.
"""

import pytest
import asyncio
import logging
from unittest.mock import MagicMock, patch

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test basic imports from interfaces package."""
    # Test importing from interfaces package
    from interfaces import (
        InterfaceError,
        BaseInterface,
        AgentInterface,
        ComponentInterface,
        FeatureInterface
    )
    
    # Verify the imports worked
    assert hasattr(BaseInterface, '__init__')
    assert hasattr(AgentInterface, '__init__')
    assert hasattr(ComponentInterface, '__init__')
    assert hasattr(FeatureInterface, '__init__')
    
    # Test interface.py compatibility layer
    # Note: We don't test warnings here since they're already triggered
    from interface import (
        InterfaceError,
        BaseInterface as CompatBaseInterface,
        AgentInterface as CompatAgentInterface,
        ComponentInterface as CompatComponentInterface,
        FeatureInterface as CompatFeatureInterface
    )
    
    # Verify compatibility imports point to the real classes
    assert CompatBaseInterface is BaseInterface
    assert CompatAgentInterface is AgentInterface
    assert CompatComponentInterface is ComponentInterface
    assert CompatFeatureInterface is FeatureInterface

def test_interface_mocking():
    """Test that we can create interface mocks for testing."""
    # Mock the BaseInterface
    from interfaces import BaseInterface
    
    # Create a mock BaseInterface
    mock_base = MagicMock(spec=BaseInterface)
    mock_base.interface_id = "mock_interface"
    mock_base.ensure_initialized.return_value = None
    mock_base.get_state.return_value = "ACTIVE"
    
    # Verify we can use the mock
    assert mock_base.interface_id == "mock_interface"
    
    # Test async mocking
    async def test_async_mock():
        # Call the mocked async method
        await mock_base.ensure_initialized()
        # The mock should track the call
        mock_base.ensure_initialized.assert_called_once()
        
        # Test return value from async mocked method
        state = await mock_base.get_state()
        assert state == "ACTIVE"
    
    # Run the async test
    asyncio.run(test_async_mock())

def test_simple_class_creation():
    """Test that we can instantiate simplified interface classes with mocks."""
    from interfaces import BaseInterface, AgentInterface
    
    # Create mock dependencies
    mock_event_queue = MagicMock()
    mock_state_manager = MagicMock()
    
    # Test that we can create a dummy BaseInterface with minimal dependencies
    with patch.object(BaseInterface, 'ensure_initialized', return_value=None):
        base = BaseInterface(
            "test_interface",
            mock_event_queue,
            mock_state_manager,
            None, # context_manager
            None, # cache_manager
            None, # metrics_manager
            None, # error_handler
            None  # memory_monitor
        )
        # Verify it has the expected ID
        assert base.interface_id == "test_interface"
    
    # Test AgentInterface with minimal dependencies
    with patch.object(AgentInterface, '__init__', return_value=None) as mock_init:
        agent = AgentInterface(
            "test_agent",
            mock_event_queue,
            mock_state_manager
        )
        # Verify the constructor was called
        mock_init.assert_called_once()

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])