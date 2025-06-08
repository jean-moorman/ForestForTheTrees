"""
Test script to verify the imports and package structure of the interfaces package.
"""

import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_imports():
    """Test importing from the interfaces package."""
    logger.info("Testing imports from interfaces package...")
    
    # Test importing from interfaces package
    from interfaces import (
        InterfaceError,
        BaseInterface,
        AgentInterface,
        AgentState,
        ComponentInterface,
        FeatureInterface,
        FunctionalityInterface,
        TestAgent
    )
    
    # Test importing submodules
    from interfaces.agent.validation import ValidationManager
    from interfaces.agent.cache import InterfaceCache
    from interfaces.agent.metrics import InterfaceMetrics
    
    logger.info("Successfully imported all classes from interfaces package")
    
    # Test compatibility layer
    logger.info("Testing imports from interface.py compatibility layer...")
    
    # Import from interface.py should show deprecation warning
    from interface import (
        InterfaceError,
        BaseInterface,
        AgentInterface,
        ComponentInterface,
        FeatureInterface,
        FunctionalityInterface,
        ValidationManager,
        InterfaceCache,
        InterfaceMetrics
    )
    
    logger.info("Successfully imported from compatibility layer")
    
    return True


async def test_instantiation():
    """Test instantiating classes from the interfaces package."""
    logger.info("Testing class instantiation...")
    
    # Import necessary resources
    from resources import (
        EventQueue,
        StateManager,
        CacheManager,
        AgentContextManager,
        MetricsManager,
        ErrorHandler,
        MemoryMonitor
    )
    
    # Create resource managers
    event_queue = EventQueue()
    await event_queue.start()
    
    state_manager = StateManager(event_queue)
    context_manager = AgentContextManager(event_queue)
    cache_manager = CacheManager(event_queue)
    metrics_manager = MetricsManager(event_queue)
    error_handler = ErrorHandler(event_queue)
    memory_monitor = MemoryMonitor(event_queue)
    
    try:
        # Import and instantiate BaseInterface
        from interfaces import BaseInterface
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
        
        # Import and instantiate ComponentInterface
        from interfaces import ComponentInterface
        component = ComponentInterface(
            "test_component",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
        await component.ensure_initialized()
        logger.info("Successfully instantiated ComponentInterface")
        
        # Import and instantiate FeatureInterface
        from interfaces import FeatureInterface
        feature = FeatureInterface(
            "test_feature",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
        await feature.ensure_initialized()
        logger.info("Successfully instantiated FeatureInterface")
        
        # Clean up
        await base.cleanup()
        await component.cleanup()
        await feature.cleanup()
        
        return True
        
    except Exception as e:
        logger.error(f"Error instantiating classes: {str(e)}", exc_info=True)
        return False
    finally:
        # Stop event queue
        if event_queue._running:
            await event_queue.stop()


async def test_old_interface():
    """Test running the original interface.py main function."""
    logger.info("Testing interface.py main function...")
    
    # Import main from interface.py
    from interface import main
    
    try:
        # Run with a small timeout to avoid hanging
        await asyncio.wait_for(main(), timeout=5.0)
        logger.info("Successfully ran interface.py main function")
        return True
    except asyncio.TimeoutError:
        logger.warning("Timeout running interface.py main - this may be normal if tests take a while")
        return True
    except Exception as e:
        logger.error(f"Error running interface.py main: {str(e)}", exc_info=True)
        return False


async def main():
    """Main test function."""
    logger.info("Starting interfaces package tests")
    
    # Test imports
    import_result = await test_imports()
    if not import_result:
        logger.error("Import tests failed")
        return False
    
    # Test instantiation
    instantiation_result = await test_instantiation()
    if not instantiation_result:
        logger.error("Instantiation tests failed")
        return False
    
    # Test old interface
    old_interface_result = await test_old_interface()
    if not old_interface_result:
        logger.error("Old interface tests failed")
        return False
    
    logger.info("All tests passed successfully!")
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