from typing import Dict, List, Optional, Any

from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler, HealthTracker
from resources.monitoring import MemoryMonitor
from phase_zero.base import BaseAnalysisAgent
from phase_zero.prompt_loader import prompt_loader, AgentType, PromptType

# Agents focused on analyzing the initial project description

class SunAgent(BaseAnalysisAgent):
    """Dual-perspective initial task description analysis (issues + gaps)."""
    
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("sun", event_queue, state_manager, context_manager, cache_manager, 
                        metrics_manager, error_handler, health_tracker, memory_monitor)
        self._current_prompt_type = PromptType.PHASE_ONE_INITIAL
        
    def get_output_schema(self) -> Dict:
        return {
            "dual_perspective_analysis": {
                "issue_analysis": {
                    "scope_issues": List[Dict],
                    "clarity_issues": List[Dict],
                    "alignment_issues": List[Dict],
                    "feasibility_issues": List[Dict],
                    "complexity_issues": List[Dict]
                },
                "gap_analysis": {
                    "scope_gaps": List[Dict],
                    "definition_gaps": List[Dict],
                    "alignment_gaps": List[Dict],
                    "constraint_gaps": List[Dict],
                    "complexity_gaps": List[Dict]
                },
                "synthesis": {
                    "key_observations": List[str],
                    "cross_cutting_concerns": List[str],
                    "prioritized_recommendations": List[Dict]
                }
            }
        }
    
    async def process_with_validation(self, conversation: str, schema: Dict, 
                                    current_phase: Optional[str] = None,
                                    metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Process using system prompt with validation."""
        system_prompt = prompt_loader.get_prompt(AgentType.SUN, self._current_prompt_type)
        if system_prompt:
            enhanced_conversation = f"{system_prompt}\n\n## Analysis Input\n{conversation}"
        else:
            enhanced_conversation = conversation
        
        return await super().process_with_validation(
            enhanced_conversation, schema, current_phase, metadata
        )


class ShadeAgent(BaseAnalysisAgent):
    """Dual-perspective conflict analysis for initial task descriptions."""
    
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("shade", event_queue, state_manager, context_manager, cache_manager, 
                        metrics_manager, error_handler, health_tracker, memory_monitor)
        self._current_prompt_type = PromptType.PHASE_ONE_INITIAL
        
    def get_output_schema(self) -> Dict:
        return {
            "dual_perspective_conflicts": {
                "task_vs_guidelines": {
                    "scope_conflicts": List[Dict],
                    "stakeholder_conflicts": List[Dict],
                    "context_conflicts": List[Dict],
                    "criteria_conflicts": List[Dict]
                },
                "guidelines_vs_task": {
                    "scope_conflicts": List[Dict],
                    "stakeholder_conflicts": List[Dict],
                    "context_conflicts": List[Dict],
                    "criteria_conflicts": List[Dict]
                },
                "synthesis": {
                    "key_patterns": List[str],
                    "bidirectional_issues": List[str],
                    "prioritized_resolutions": List[Dict]
                }
            }
        }
    
    async def process_with_validation(self, conversation: str, schema: Dict, 
                                    current_phase: Optional[str] = None,
                                    metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Process using system prompt with validation."""
        system_prompt = prompt_loader.get_prompt(AgentType.SHADE, self._current_prompt_type)
        if system_prompt:
            enhanced_conversation = f"{system_prompt}\n\n## Analysis Input\n{conversation}"
        else:
            enhanced_conversation = conversation
        
        return await super().process_with_validation(
            enhanced_conversation, schema, current_phase, metadata
        )


# WindAgent eliminated - conflict analysis now handled by ShadeAgent's dual-perspective approach