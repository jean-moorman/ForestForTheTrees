from typing import Dict, List, Optional, Any

from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler, HealthTracker
from resources.monitoring import MemoryMonitor
from phase_zero.base import BaseAnalysisAgent
from phase_zero.prompt_loader import prompt_loader, AgentType, PromptType

# Agent focused on optimizing components based on phase one outputs

class PollinatorAgent(BaseAnalysisAgent):
    """Enhanced cross-guideline optimization analysis."""
    
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("pollinator", event_queue, state_manager, context_manager, cache_manager, 
                        metrics_manager, error_handler, health_tracker, memory_monitor)
        self._current_prompt_type = PromptType.PHASE_ONE_INITIAL
        
    def get_output_schema(self) -> Dict:
        return {
            "cross_guideline_optimization": {
                "alignment_opportunities": List[Dict],
                "optimization_patterns": List[Dict],
                "redundancy_reductions": List[Dict],
                "integration_enhancements": List[Dict],
                "holistic_improvements": List[Dict],
                "synthesis": {
                    "high_impact_low_effort": List[Dict],
                    "high_impact_medium_effort": List[Dict],
                    "recommended_priorities": List[Dict]
                }
            }
        }
    
    async def process_with_validation(self, conversation: str, schema: Dict, 
                                    current_phase: Optional[str] = None,
                                    metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Process using system prompt with validation."""
        system_prompt = prompt_loader.get_prompt(AgentType.POLLINATOR, self._current_prompt_type)
        if system_prompt:
            enhanced_conversation = f"{system_prompt}\n\n## Analysis Input\n{conversation}"
        else:
            enhanced_conversation = conversation
        
        return await super().process_with_validation(
            enhanced_conversation, schema, current_phase, metadata
        )