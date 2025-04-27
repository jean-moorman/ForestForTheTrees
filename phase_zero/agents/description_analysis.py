from typing import Dict, List, Optional

from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler, HealthTracker
from resources.monitoring import MemoryMonitor
from phase_zero.base import BaseAnalysisAgent

# Agents focused on analyzing the initial project description

class SunAgent(BaseAnalysisAgent):
    """Analyzes critical description issues in phase one outputs."""
    
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
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_description_issues": {
                "scope_issues": List[Dict],
                "clarity_issues": List[Dict],
                "alignment_issues": List[Dict],
                "feasibility_issues": List[Dict]
            }
        }


class ShadeAgent(BaseAnalysisAgent):
    """Analyzes critical description gaps in phase one outputs."""
    
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
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_description_gaps": {
                "scope_gaps": List[Dict],
                "stakeholder_gaps": List[Dict],
                "context_gaps": List[Dict],
                "success_criteria_gaps": List[Dict]
            }
        }


class WindAgent(BaseAnalysisAgent):
    """Analyzes critical description conflicts in phase one outputs."""
    
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("wind", event_queue, state_manager, context_manager, cache_manager, 
                        metrics_manager, error_handler, health_tracker, memory_monitor)
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_description_conflicts": {
                "scope_conflicts": List[Dict],
                "assumption_conflicts": List[Dict],
                "approach_conflicts": List[Dict],
                "constraint_conflicts": List[Dict]
            }
        }