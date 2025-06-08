from typing import Dict, List, Optional, Any

from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler, HealthTracker
from resources.monitoring import MemoryMonitor
from phase_zero.base import BaseAnalysisAgent
from phase_zero.prompt_loader import prompt_loader, AgentType, PromptType

# Agents focused on analyzing structural components in phase one outputs

# InsectAgent eliminated - gap analysis now handled by TreeAgent's dual-perspective approach


class BirdAgent(BaseAnalysisAgent):
    """Dual-perspective structural conflict analysis."""
    
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("bird", event_queue, state_manager, context_manager, cache_manager, 
                        metrics_manager, error_handler, health_tracker, memory_monitor)
        self._current_prompt_type = PromptType.PHASE_ONE_INITIAL
        
    def get_output_schema(self) -> Dict:
        return {
            "dual_perspective_conflicts": {
                "guidelines_vs_components": {
                    "scope_boundary_conflicts": List[Dict],
                    "data_sequence_conflicts": List[Dict],
                    "environment_requirement_conflicts": List[Dict],
                    "dependency_chain_conflicts": List[Dict]
                },
                "components_vs_guidelines": {
                    "component_boundary_conflicts": List[Dict],
                    "component_sequence_conflicts": List[Dict],
                    "component_isolation_conflicts": List[Dict],
                    "component_dependency_conflicts": List[Dict]
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
        system_prompt = prompt_loader.get_prompt(AgentType.BIRD, self._current_prompt_type)
        if system_prompt:
            enhanced_conversation = f"{system_prompt}\n\n## Analysis Input\n{conversation}"
        else:
            enhanced_conversation = conversation
        
        return await super().process_with_validation(
            enhanced_conversation, schema, current_phase, metadata
        )


class TreeAgent(BaseAnalysisAgent):
    """Dual-perspective structural analysis (issues + gaps)."""
    
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("tree", event_queue, state_manager, context_manager, cache_manager, 
                        metrics_manager, error_handler, health_tracker, memory_monitor)
        self._current_prompt_type = PromptType.PHASE_ONE_INITIAL
        
    def get_output_schema(self) -> Dict:
        return {
            "dual_perspective_analysis": {
                "issue_analysis": {
                    "foundation_issues": List[Dict],
                    "boundary_issues": List[Dict],
                    "balance_issues": List[Dict],
                    "coupling_issues": List[Dict],
                    "growth_issues": List[Dict]
                },
                "gap_analysis": {
                    "quality_attribute_gaps": List[Dict],
                    "interface_gaps": List[Dict],
                    "isolation_gaps": List[Dict],
                    "cross_cutting_gaps": List[Dict],
                    "extension_point_gaps": List[Dict]
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
        system_prompt = prompt_loader.get_prompt(AgentType.TREE, self._current_prompt_type)
        if system_prompt:
            enhanced_conversation = f"{system_prompt}\n\n## Analysis Input\n{conversation}"
        else:
            enhanced_conversation = conversation
        
        return await super().process_with_validation(
            enhanced_conversation, schema, current_phase, metadata
        )