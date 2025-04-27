import logging
from typing import Optional

# Direct import for ErrorHandler to avoid import issues
from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, MemoryMonitor
from interface import AgentInterface, ValidationManager, AgentState

# Import ErrorHandler from resources.__init__ where it's defined
from resources import ErrorHandler

logger = logging.getLogger(__name__)

class PhaseTwoAgentBase(AgentInterface):
    """Base class for Phase Two agents with common functionality"""
    
    def __init__(self, 
                 agent_name: str,
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
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