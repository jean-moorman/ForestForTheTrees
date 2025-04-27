import json
import logging
from typing import Dict, List, Any, Optional

from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler, HealthTracker
from resources.monitoring import MemoryMonitor
from interface import AgentInterface

logger = logging.getLogger(__name__)

class EvolutionAgent(AgentInterface):
    """Synthesizes system adaptations based on analysis results"""
    
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("evolution_agent", event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler)
        self._health_tracker = health_tracker
        self._memory_monitor = memory_monitor
        
    async def _process(self, conversation: str, schema: Dict, current_phase: Optional[str] = None,
                      metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Process synthesis data with validation"""
        try:
            analysis_inputs = {
                "conversation": conversation,
                "phase": current_phase or "synthesis",
                "metadata": metadata or {}
            }
            
            return await super().process_with_validation(
                json.dumps(analysis_inputs),
                {
                    "strategic_adaptations": {
                        "key_patterns": List[Dict],
                        "adaptations": List[Dict],
                        "priorities": Dict
                    }
                },
                current_phase=current_phase,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Processing error in evolution synthesis: {e}")
            raise