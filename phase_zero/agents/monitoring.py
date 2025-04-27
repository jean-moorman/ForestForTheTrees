import json
from typing import Dict, Any, Optional
import logging

from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler, HealthTracker
from resources.monitoring import MemoryMonitor
from phase_zero.base import BaseAnalysisAgent

logger = logging.getLogger(__name__)

class MonitoringAgent(BaseAnalysisAgent):
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("system_monitoring", event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, health_tracker, memory_monitor)
        self.metrics_schema = {
            "type": "object",
            "required": ["resource", "error", "development"],
            "properties": {
                "resource": {
                    "type": "object",
                    "additionalProperties": {"type": "number"}
                },
                "error": {
                    "type": "object",
                    "additionalProperties": {"type": "number"}
                },
                "development": {
                    "type": "object",
                    "additionalProperties": {"type": "number"}
                }
            }
        }

    async def analyze_metrics(self, metrics: Dict[str, Any], system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze metrics with validation."""
        metrics_json = json.dumps(metrics)
        return await self.process_with_validation(
            metrics_json,
            self.metrics_schema,
            current_phase="metric_analysis",
            metadata={"system_state": system_state}
        )

    async def _process(self, metrics_json: str,
                      schema: Dict[str, Any],
                      current_phase: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process validated metrics data."""
        try:
            metrics_data = json.loads(metrics_json)
            analysis = {
                "flag_raised": False,
                "flag_type": None,
                "recommendations": []
            }

            # Analysis logic for resource metrics
            if any(value > 80 for value in metrics_data["resource"].values()):
                analysis.update({
                    "flag_raised": True,
                    "flag_type": "high_resource_usage"
                })

            # Analysis logic for error metrics  
            if any(value > 0.05 for value in metrics_data["error"].values()):
                analysis.update({
                    "flag_raised": True,
                    "flag_type": "high_error_rate"
                })

            return analysis

        except json.JSONDecodeError:
            raise ValueError("Invalid metrics data format")
            
    def get_output_schema(self) -> Dict:
        """Get agent-specific output schema."""
        return self.metrics_schema