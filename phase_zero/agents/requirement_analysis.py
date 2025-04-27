from typing import Dict, List, Optional

from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler, HealthTracker
from resources.monitoring import MemoryMonitor
from phase_zero.base import BaseAnalysisAgent

# Agents focused on analyzing requirements in phase one outputs

class SoilAgent(BaseAnalysisAgent):
    """Analyzes critical requirement gaps in phase one outputs."""
    
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
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_requirement_gaps": {
                "runtime_gaps": List[Dict],
                "deployment_gaps": List[Dict],
                "dependency_gaps": List[Dict],
                "integration_gaps": List[Dict]
            }
        }


class MicrobialAgent(BaseAnalysisAgent):
    """Analyzes critical guideline conflicts in phase one outputs."""
    
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
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_guideline_conflicts": {
                "task_assumption_conflicts": List[Dict],
                "data_pattern_conflicts": List[Dict],
                "component_structure_conflicts": List[Dict],
                "technical_decision_conflicts": List[Dict]
            }
        }


class RainAgent(BaseAnalysisAgent):
    """Analyzes critical requirement issues in phase one outputs."""
    
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("rain", event_queue, state_manager, context_manager, cache_manager, 
                        metrics_manager, error_handler, health_tracker, memory_monitor)
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_requirement_issues": {
                "runtime_issues": List[Dict],
                "deployment_issues": List[Dict],
                "dependency_issues": List[Dict],
                "integration_issues": List[Dict]
            }
        }