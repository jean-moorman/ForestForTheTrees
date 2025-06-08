"""
Agent-specific metrics monitoring panel.
"""
import logging
from datetime import datetime
from typing import Optional, Any, List

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget

from resources.monitoring import SystemMonitor
from ..visualization.alerts import AlertWidget, AlertLevel
from ..visualization.charts import MetricsChart

logger = logging.getLogger(__name__)


class AgentMetricsPanel(QFrame):
    """Panel for displaying agent-specific metrics."""
    
    def __init__(self, system_monitor: SystemMonitor, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.system_monitor = system_monitor
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize panel UI components."""
        layout = QVBoxLayout(self)
        self.alert_widget = AlertWidget()
        layout.addWidget(self.alert_widget)
        
        self.status_label = QLabel("Agent Status")
        layout.addWidget(self.status_label)
        
        self.performance_chart = MetricsChart("Performance")
        self.resource_chart = MetricsChart("Resource Usage")
        
        layout.addWidget(self.performance_chart)
        layout.addWidget(self.resource_chart)
        
        self.setMinimumWidth(250)

    def _get_circuit_name(self, agent_id: str) -> str:
        """Map agent ID to circuit breaker name."""
        # Simple mapping - in practice this might be more complex
        return f"agent_{agent_id}"

    def update_metrics(self, agent_id: str):
        """Update metrics for a specific agent."""
        logger.debug(f"Updating metrics for agent {agent_id}")
        try:
            # Map agent ID to circuit name if needed
            circuit_name = self._get_circuit_name(agent_id)
            
            # Get circuit metrics if available
            if circuit_name in self.system_monitor._circuit_breakers:
                # Get error density for performance chart
                error_density = self.system_monitor._metrics.get_error_density(circuit_name)
                perf_data = [(datetime.now().timestamp(), error_density)]
                self.performance_chart.update_data(perf_data)
                
                # Get state durations for resource chart
                state_durations = self.system_monitor._metrics.get_state_durations(circuit_name)
                resource_data = [
                    (datetime.now().timestamp(), state_durations.get('OPEN', 0))
                ]
                self.resource_chart.update_data(resource_data)
                
            # Add alert if no circuit found
            else:
                self.alert_widget.add_alert(
                    AlertLevel.WARNING,
                    f"No circuit data found for agent {agent_id}"
                )
        except Exception as e:
            self.alert_widget.add_alert(
                AlertLevel.ERROR,
                f"Failed to update metrics: {str(e)}"
            )

    def _update_charts(self, performance_metrics: List[Any], resource_metrics: List[Any]) -> None:
        """Update chart displays with new metric data."""
        perf_data = [(m.timestamp.timestamp(), m.value) for m in performance_metrics]
        resource_data = [(m.timestamp.timestamp(), m.value) for m in resource_metrics]
        
        self.performance_chart.update_data(perf_data)
        self.resource_chart.update_data(resource_data)