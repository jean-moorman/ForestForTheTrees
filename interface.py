"""
Interface module for the FFTT system.

This file serves as a compatibility layer for the refactored interfaces package.
New code should import directly from the interfaces package.

Example:
  from interfaces import AgentInterface, ComponentInterface

instead of:
  from interface import AgentInterface, ComponentInterface
"""

import logging
import warnings

# Issue deprecation warning
warnings.warn(
    "Importing from interface.py is deprecated. "
    "Please import from the interfaces package instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import and re-export all interfaces from the refactored package
from interfaces import (
    # Errors
    InterfaceError,
    InitializationError,
    StateTransitionError,
    ResourceError,
    ValidationError,
    TimeoutError,
    
    # Base interface
    BaseInterface,
    
    # Agent interfaces
    AgentInterface,
    AgentState,
    
    # Component, feature and functionality interfaces
    ComponentInterface,
    FeatureInterface,
    FunctionalityInterface,
    
    # Coordination interface
    CoordinationInterface,
    
    # Testing tools
    TestAgent
)

# Import submodules for backward compatibility
from interfaces.agent.validation import ValidationManager
from interfaces.agent.cache import InterfaceCache
from interfaces.agent.metrics import InterfaceMetrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for backward compatibility
from resources import CircuitBreakerConfig
CACHE_CIRCUIT_CONFIG = CircuitBreakerConfig(
    failure_threshold=10,
    recovery_timeout=30,
    failure_window=30
)

# For backward compatibility - main testing function
async def main():
    """
    Test the AgentInterface process_with_validation functionality.
    For backward compatibility only.
    """
    from interfaces.testing.runners import test_agent_process
    await test_agent_process()

# Make this file runnable for backward compatibility
if __name__ == "__main__":
    import asyncio
    
    # Set up logging with more detailed format
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the test
    asyncio.run(main())