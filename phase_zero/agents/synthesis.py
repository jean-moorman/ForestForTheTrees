import json
import logging
from typing import Dict, List, Any, Optional

from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler, HealthTracker
from resources.monitoring import MemoryMonitor
from interfaces import AgentInterface
from phase_zero.base import BaseAnalysisAgent
from phase_zero.prompt_loader import prompt_loader, AgentType, PromptType

logger = logging.getLogger(__name__)

class EvolutionAgent(BaseAnalysisAgent):
    """Enhanced synthesis of dual-perspective analyses"""
    
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("evolution_agent", event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, health_tracker, memory_monitor)
        self._health_tracker = health_tracker
        self._memory_monitor = memory_monitor
        self._current_prompt_type = PromptType.PHASE_ONE_INITIAL
        
    async def _process(self, conversation: str, schema: Dict, current_phase: Optional[str] = None,
                      metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Process synthesis data with validation"""
        try:
            analysis_inputs = {
                "conversation": conversation,
                "phase": current_phase or "synthesis",
                "metadata": metadata or {}
            }
            
            # Get system prompt and enhance conversation
            system_prompt = prompt_loader.get_prompt(AgentType.EVOLUTION, self._current_prompt_type)
            if system_prompt:
                enhanced_conversation = f"{system_prompt}\n\n## Analysis Input\n{json.dumps(analysis_inputs)}"
            else:
                enhanced_conversation = json.dumps(analysis_inputs)
            
            return await super().process_with_validation(
                enhanced_conversation,
                {
                    "strategic_adaptations": {
                        "common_patterns": List[Dict],
                        "reinforcing_signals": List[Dict],
                        "strategic_adjustments": List[Dict],
                        "high_impact_opportunities": List[Dict],
                        "integration_strategies": List[Dict],
                        "synthesis": {
                            "priority_adaptations": List[Dict],
                            "implementation_strategy": Dict,
                            "success_metrics": List[Dict]
                        }
                    }
                },
                current_phase=current_phase,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Processing error in evolution synthesis: {e}")
            raise