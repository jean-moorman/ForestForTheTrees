import logging
from typing import Optional

from resources import (
    EventQueue, 
    StateManager, 
    CacheManager, 
    AgentContextManager, 
    MetricsManager, 
    ErrorHandler, 
    MemoryMonitor
)
from interface import AgentInterface, ValidationManager

logger = logging.getLogger(__name__)

class FeatureAgentBase(AgentInterface):
    """Base class for all feature-related agents in phase three"""
    
    def __init__(self, 
                agent_name: str,
                event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                memory_monitor: Optional[MemoryMonitor] = None):
        """Initialize the base feature agent
        
        Args:
            agent_name: The name identifier for this agent
            event_queue: Queue for system events
            state_manager: Manager for application state
            context_manager: Manager for agent context
            cache_manager: Manager for caching results
            metrics_manager: Manager for metrics collection
            error_handler: Handler for error processing
            memory_monitor: Optional monitor for memory usage
        """
        super().__init__(
            agent_name, 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        self._validation_manager = ValidationManager(event_queue, state_manager, context_manager)