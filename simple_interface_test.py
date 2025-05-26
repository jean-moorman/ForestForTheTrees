"""
Simplified test for interfaces package functionality.
This test focuses on basic imports and mock instantiation of interface classes.
"""

import asyncio
import logging
import sys
from unittest.mock import MagicMock, AsyncMock, patch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test importing from the interfaces package."""
    logger.info("Testing imports from interfaces package...")
    
    # Test importing from interfaces package
    from interfaces import (
        InterfaceError,
        BaseInterface,
        AgentInterface,
        ComponentInterface,
        FeatureInterface
    )
    
    logger.info("Successfully imported all classes from interfaces package")
    
    # Test compatibility layer imports
    logger.info("Testing imports from interface.py compatibility layer...")
    
    with patch('warnings.warn') as mock_warn:
        from interface import (
            InterfaceError,
            BaseInterface,
            AgentInterface,
            ComponentInterface,
            FeatureInterface
        )
        
        # Verify deprecation warning was issued
        assert mock_warn.called, "Deprecation warning should be issued"
    
    logger.info("Successfully imported from compatibility layer")
    
    return True


async def test_mock_instantiation():
    """Test mocked instantiation of interface classes."""
    logger.info("Testing class instantiation with mocks...")
    
    # Import interface classes
    from interfaces import BaseInterface, AgentInterface
    
    # Create mock managers
    event_queue = AsyncMock()
    event_queue.start = AsyncMock()
    event_queue.stop = AsyncMock()
    event_queue._running = True
    
    state_manager = MagicMock()
    context_manager = MagicMock()
    cache_manager = MagicMock()
    metrics_manager = MagicMock()
    error_handler = MagicMock()
    memory_monitor = MagicMock()
    
    # Patch ensure_initialized to avoid real initialization
    with patch.object(BaseInterface, 'ensure_initialized', new_callable=AsyncMock):
        
        # Instantiate BaseInterface
        base = BaseInterface(
            "test_base",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
        
        await base.ensure_initialized()
        logger.info("Successfully instantiated BaseInterface")
        
        # Instantiate AgentInterface
        with patch.object(AgentInterface, 'ensure_initialized', new_callable=AsyncMock):
            agent = AgentInterface(
                "test_agent",
                event_queue,
                state_manager,
                context_manager,
                cache_manager,
                metrics_manager,
                error_handler,
                memory_monitor
            )
            
            await agent.ensure_initialized()
            logger.info("Successfully instantiated AgentInterface")
    
    logger.info("Mock instantiation tests passed")
    return True


async def test_simplified_interface():
    """Test the compatibility layer's main function with a mock."""
    logger.info("Testing interface.py with mock test runner...")
    
    # Mock the test_agent_process function that's called by interface.main()
    with patch('interfaces.testing.runners.test_agent_process', new_callable=AsyncMock) as mock_test:
        from interface import main
        
        # Run main with our mocked test function
        await main()
        
        # Verify the test function was called
        mock_test.assert_called_once()
    
    logger.info("Successfully ran interface compatibility test")
    return True


async def main():
    """Main test function."""
    logger.info("Starting simplified interfaces tests")
    
    # Test imports
    import_result = test_imports()
    if not import_result:
        logger.error("Import tests failed")
        return False
    
    # Test mocked instantiation
    try:
        instantiation_result = await test_mock_instantiation()
        if not instantiation_result:
            logger.error("Mock instantiation tests failed")
            return False
    except Exception as e:
        logger.error(f"Error in mock instantiation tests: {str(e)}", exc_info=True)
        return False
    
    # Test simplified interface
    try:
        interface_result = await test_simplified_interface()
        if not interface_result:
            logger.error("Simplified interface tests failed")
            return False
    except Exception as e:
        logger.error(f"Error in simplified interface test: {str(e)}", exc_info=True)
        return False
    
    logger.info("All simplified tests passed successfully!")
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error in tests: {str(e)}", exc_info=True)
        sys.exit(1)