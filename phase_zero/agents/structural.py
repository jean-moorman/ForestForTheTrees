from typing import Dict, List, Optional

from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler, HealthTracker
from resources.monitoring import MemoryMonitor
from phase_zero.base import BaseAnalysisAgent

# Agents focused on analyzing structural components in phase one outputs

class InsectAgent(BaseAnalysisAgent):
    """Analyzes critical structure gaps in phase one outputs."""
    
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("insect", event_queue, state_manager, context_manager, cache_manager, 
                        metrics_manager, error_handler, health_tracker, memory_monitor)
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_structure_gaps": {
                "boundary_gaps": List[Dict],
                "sequence_gaps": List[Dict],
                "interface_gaps": List[Dict],
                "dependency_gaps": List[Dict]
            }
        }


class BirdAgent(BaseAnalysisAgent):
    """Analyzes critical guideline conflicts related to structure in phase one outputs."""
    
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
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_guideline_conflicts": {
                "scope_boundary_conflicts": List[Dict],
                "data_sequence_conflicts": List[Dict],
                "environment_requirement_conflicts": List[Dict],
                "dependency_chain_conflicts": List[Dict]
            }
        }


class TreeAgent(BaseAnalysisAgent):
    """Analyzes critical structural issues in phase one outputs."""
    
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
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_structural_issues": {
                "foundation_issues": List[Dict],
                "boundary_issues": List[Dict],
                "balance_issues": List[Dict],
                "coupling_issues": List[Dict],
                "growth_issues": List[Dict]
            }
        }