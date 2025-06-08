from typing import Dict, List, Optional, Any

from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler, HealthTracker
from resources.monitoring import MemoryMonitor
from phase_zero.base import BaseAnalysisAgent
from phase_zero.prompt_loader import prompt_loader, AgentType, PromptType

# Agents focused on analyzing data flow in phase one outputs

# RootSystemAgent eliminated - gap analysis now handled by WormAgent's dual-perspective approach


class MycelialAgent(BaseAnalysisAgent):
    """Dual-perspective data flow conflict analysis."""
    
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("mycelial", event_queue, state_manager, context_manager, cache_manager, 
                        metrics_manager, error_handler, health_tracker, memory_monitor)
        self._current_prompt_type = PromptType.PHASE_ONE_INITIAL
        
    def get_output_schema(self) -> Dict:
        return {
            "dual_perspective_conflicts": {
                "guidelines_vs_dataflow": {
                    "task_scope_conflicts": List[Dict],
                    "environment_conflicts": List[Dict],
                    "component_conflicts": List[Dict],
                    "constraint_conflicts": List[Dict]
                },
                "dataflow_vs_guidelines": {
                    "flow_scope_conflicts": List[Dict],
                    "transformation_conflicts": List[Dict],
                    "persistence_conflicts": List[Dict],
                    "circulation_conflicts": List[Dict]
                },
                "synthesis": {
                    "key_patterns": List[str],
                    "bidirectional_conflicts": List[str],
                    "prioritized_resolutions": List[Dict]
                }
            }
        }
    
    async def process_with_validation(self, conversation: str, schema: Dict, 
                                    current_phase: Optional[str] = None,
                                    metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Process using system prompt with validation."""
        system_prompt = prompt_loader.get_prompt(AgentType.MYCELIAL, self._current_prompt_type)
        if system_prompt:
            enhanced_conversation = f"{system_prompt}\n\n## Analysis Input\n{conversation}"
        else:
            enhanced_conversation = conversation
        
        return await super().process_with_validation(
            enhanced_conversation, schema, current_phase, metadata
        )


class WormAgent(BaseAnalysisAgent):
    """Dual-perspective data flow analysis (issues + gaps)."""
    
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("worm", event_queue, state_manager, context_manager, cache_manager, 
                        metrics_manager, error_handler, health_tracker, memory_monitor)
        self._current_prompt_type = PromptType.PHASE_ONE_INITIAL
        
    def get_output_schema(self) -> Dict:
        return {
            "dual_perspective_analysis": {
                "issue_analysis": {
                    "circulation_issues": List[Dict],
                    "transformation_issues": List[Dict],
                    "bottleneck_issues": List[Dict],
                    "consistency_issues": List[Dict]
                },
                "gap_analysis": {
                    "circulation_gaps": List[Dict],
                    "transformation_gaps": List[Dict],
                    "optimization_gaps": List[Dict],
                    "consistency_gaps": List[Dict]
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
        system_prompt = prompt_loader.get_prompt(AgentType.WORM, self._current_prompt_type)
        if system_prompt:
            enhanced_conversation = f"{system_prompt}\n\n## Analysis Input\n{conversation}"
        else:
            enhanced_conversation = conversation
        
        return await super().process_with_validation(
            enhanced_conversation, schema, current_phase, metadata
        )