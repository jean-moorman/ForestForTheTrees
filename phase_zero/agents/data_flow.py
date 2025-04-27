from typing import Dict, List, Optional

from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler, HealthTracker
from resources.monitoring import MemoryMonitor
from phase_zero.base import BaseAnalysisAgent

# Agents focused on analyzing data flow in phase one outputs

class RootSystemAgent(BaseAnalysisAgent):
    """Analyzes critical data flow gaps in phase one outputs."""
    
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("root_system", event_queue, state_manager, context_manager, cache_manager, 
                        metrics_manager, error_handler, health_tracker, memory_monitor)
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_data_flow_gaps": {
                "entity_gaps": List[Dict],
                "flow_pattern_gaps": List[Dict],
                "persistence_gaps": List[Dict],
                "contract_gaps": List[Dict]
            }
        }


class MycelialAgent(BaseAnalysisAgent):
    """Analyzes critical guideline conflicts related to data flow in phase one outputs."""
    
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
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_guideline_conflicts": {
                "task_scope_conflicts": List[Dict],
                "environment_conflicts": List[Dict],
                "component_conflicts": List[Dict],
                "constraint_conflicts": List[Dict]
            }
        }


class WormAgent(BaseAnalysisAgent):
    """Analyzes critical data flow issues in phase one outputs."""
    
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
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_data_flow_issues": {
                "circulation_issues": List[Dict],
                "transformation_issues": List[Dict],
                "bottleneck_issues": List[Dict],
                "consistency_issues": List[Dict]
            }
        }