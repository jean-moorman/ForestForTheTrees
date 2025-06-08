from typing import Dict, List, Optional, Any

from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler, HealthTracker
from resources.monitoring import MemoryMonitor
from phase_zero.base import BaseAnalysisAgent
from phase_zero.prompt_loader import prompt_loader, AgentType, PromptType

# Agents focused on analyzing requirements in phase one outputs

class SoilAgent(BaseAnalysisAgent):
    """Dual-perspective environmental requirements analysis (issues + gaps)."""
    
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("soil", event_queue, state_manager, context_manager, cache_manager, 
                        metrics_manager, error_handler, health_tracker, memory_monitor)
        self._current_prompt_type = PromptType.PHASE_ONE_INITIAL
        
    def get_output_schema(self) -> Dict:
        return {
            "dual_perspective_analysis": {
                "issue_analysis": {
                    "runtime_issues": List[Dict],
                    "deployment_issues": List[Dict],
                    "dependency_issues": List[Dict],
                    "integration_issues": List[Dict]
                },
                "gap_analysis": {
                    "runtime_gaps": List[Dict],
                    "deployment_gaps": List[Dict],
                    "dependency_gaps": List[Dict],
                    "integration_gaps": List[Dict]
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
        system_prompt = prompt_loader.get_prompt(AgentType.SOIL, self._current_prompt_type)
        if system_prompt:
            enhanced_conversation = f"{system_prompt}\n\n## Analysis Input\n{conversation}"
        else:
            enhanced_conversation = conversation
        
        return await super().process_with_validation(
            enhanced_conversation, schema, current_phase, metadata
        )


class MicrobialAgent(BaseAnalysisAgent):
    """Dual-perspective requirements conflict analysis."""
    
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("microbial", event_queue, state_manager, context_manager, cache_manager, 
                        metrics_manager, error_handler, health_tracker, memory_monitor)
        self._current_prompt_type = PromptType.PHASE_ONE_INITIAL
        
    def get_output_schema(self) -> Dict:
        return {
            "dual_perspective_conflicts": {
                "guidelines_vs_requirements": {
                    "task_assumption_conflicts": List[Dict],
                    "data_pattern_conflicts": List[Dict],
                    "component_structure_conflicts": List[Dict],
                    "technical_decision_conflicts": List[Dict]
                },
                "requirements_vs_guidelines": {
                    "runtime_requirement_conflicts": List[Dict],
                    "deployment_specification_conflicts": List[Dict],
                    "integration_requirement_conflicts": List[Dict],
                    "compatibility_requirement_conflicts": List[Dict]
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
        system_prompt = prompt_loader.get_prompt(AgentType.MICROBIAL, self._current_prompt_type)
        if system_prompt:
            enhanced_conversation = f"{system_prompt}\n\n## Analysis Input\n{conversation}"
        else:
            enhanced_conversation = conversation
        
        return await super().process_with_validation(
            enhanced_conversation, schema, current_phase, metadata
        )