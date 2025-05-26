"""
Test agent implementation for the FFTT system.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple

from resources import (
    EventQueue,
    StateManager,
    CacheManager,
    AgentContextManager,
    MetricsManager,
    ErrorHandler,
    MemoryMonitor
)
from agent import Agent
from ..agent import AgentInterface, AgentState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAgent(AgentInterface):
    """
    Agent implementation for testing purposes.
    Provides a controlled environment for testing agent functionality.
    """
    
    def __init__(self):
        """Initialize the test agent with all required resource managers."""
        # Create a proper event queue with start() already called
        event_queue = EventQueue()
        
        # Create all required resource managers using the same event queue
        state_manager = StateManager(event_queue)
        context_manager = AgentContextManager(event_queue)
        cache_manager = CacheManager(event_queue)
        metrics_manager = MetricsManager(event_queue)
        error_handler = ErrorHandler(event_queue)
        memory_monitor = MemoryMonitor(event_queue)
        
        super().__init__(
            "test_agent", 
            event_queue=event_queue,
            state_manager=state_manager,
            context_manager=context_manager,
            cache_manager=cache_manager,
            metrics_manager=metrics_manager,
            error_handler=error_handler,
            memory_monitor=memory_monitor
        )
        self._initialized = False
        
        # Create a proper test agent that can process requests
        self.agent = Agent(
            event_queue=event_queue,
            state_manager=state_manager,
            context_manager=context_manager,
            cache_manager=cache_manager,
            metrics_manager=metrics_manager,
            error_handler=error_handler,
            model="test-model"  # Use a test model identifier
        )
        
    async def initialize(self) -> bool:
        """
        Properly initialize the event queue with retry and verification.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        if hasattr(self._event_queue, '_running') and not self._event_queue._running:
            try:
                # Start with retry
                max_retries = 3
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        await self._event_queue.start()
                        
                        # Verify it started
                        if not self._event_queue._running:
                            from ..errors import InitializationError
                            raise InitializationError("Failed to start event queue")
                        
                        # Success
                        break
                    except Exception as e:
                        retry_count += 1
                        logger.warning(f"Event queue start retry {retry_count}/{max_retries}: {str(e)}")
                        if retry_count >= max_retries:
                            logger.error("Failed to start event queue after max retries")
                            return False
                        await asyncio.sleep(0.1 * (2 ** retry_count))
            except Exception as e:
                logger.error(f"Error starting event queue: {str(e)}")
                return False
        
        # Allow a short time for event queue to start processing
        await asyncio.sleep(0.1)
        
        # Ensure base interface is initialized
        try:
            await self.ensure_initialized()
        except Exception as e:
            logger.error(f"Error initializing base interface: {str(e)}")
            return False
        
        logger.info("TestAgent initialized successfully")
        return True
        
    async def get_response(self, 
                    conversation: str,
                    schema: Dict[str, Any],
                    current_phase: Optional[str] = None,
                    operation_id: Optional[str] = None,
                    system_prompt_info: Optional[Tuple[str]] = None) -> Dict[str, Any]:
        """
        Implement a test response method with proper logging.
        
        Args:
            conversation: Conversation to process
            schema: Schema for validation
            current_phase: Current phase of processing
            operation_id: ID of the operation
            system_prompt_info: System prompt information
            
        Returns:
            Test response
        """
        logger.info(f"Processing request - Phase: {current_phase}, Operation: {operation_id}")
        try:
            if not self._initialized:
                await self.initialize()
                # Ensure base interface is initialized too
                await self.ensure_initialized()
                self._initialized = True
                
            return {
                "message": "Test response",
                "status": "success",
                "data": {
                    "conversation": conversation,
                    "phase": current_phase or "default"
                }
            }
        except Exception as e:
            logger.error(f"Error in get_response: {str(e)}", exc_info=True)
            raise