"""
System metrics monitoring panel.
"""
import logging
from collections import deque
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget

from resources.monitoring import SystemMonitor, HealthStatus
from ..visualization.alerts import AlertWidget, AlertLevel
from ..visualization.charts import MetricsChart

logger = logging.getLogger(__name__)


class SystemMetrics:
    """Display and track system metrics"""
    def __init__(self, parent=None):
        self.parent = parent
        self.thresholds = {}
        self.alert_widget = AlertWidget(parent)

    def check_thresholds(self, metrics):
        """Check if any metrics exceed thresholds"""
        for metric_name, value in metrics.items():
            if metric_name in self.thresholds:
                threshold = self.thresholds.get(metric_name)
                if threshold and value > threshold.get('warning', float('inf')):
                    logger.warning(f"Metric {metric_name} exceeds warning threshold: {value}")
                    if self.alert_widget:
                        # Convert string to enum for proper AlertWidget integration
                        alert_level = AlertLevel.WARNING
                        self.alert_widget.add_alert(alert_level, f"Metric {metric_name} exceeds threshold")
        return False


class SystemMetricsPanel(QFrame):
    """Panel for displaying system-wide metrics."""
    
    def __init__(self, system_monitor: SystemMonitor, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.system_monitor = system_monitor
        self.health_tracker = system_monitor.health_tracker
        self.reliability_metrics = system_monitor._metrics
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        
        # Add memory history tracking
        self.memory_history = deque(maxlen=100)  # Keep last 100 data points
        self.last_memory_update = datetime.now()
        self.memory_update_interval = timedelta(seconds=10)  # Update every 10 seconds

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        layout = QVBoxLayout()
        
        # Alert widget
        self.alert_widget = AlertWidget()
        layout.addWidget(self.alert_widget)

        # System health status
        self.health_label = QLabel("System Health")
        layout.addWidget(self.health_label)
        
        # System metrics charts
        self.error_chart = MetricsChart("Error Rate")
        self.resource_chart = MetricsChart("System Resources")
        layout.addWidget(self.error_chart)
        layout.addWidget(self.resource_chart)
        
        self.setLayout(layout)
        self.setMinimumWidth(250)

    def update_all(self):
        """Update all metrics data"""
        try:
            self.update_health_status()
            self.update_error_metrics()
            self.update_memory_metrics()
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            self.alert_widget.add_alert(
                AlertLevel.ERROR,
                f"Failed to update metrics: {str(e)}"
            )

    def update_health_status(self):
        """Update system health status display"""
        health_status = self.system_monitor.health_tracker.get_system_health()
        self.health_label.setText(f"System Health: {health_status.status}")
        self.health_label.setStyleSheet(self._get_health_color(health_status))

    def update_error_metrics(self):
        """Update error metrics chart"""
        error_data = []
        for name, breaker in self.system_monitor._circuit_breakers.items():
            error_density = self.system_monitor._metrics.get_error_density(name)
            error_data.append((datetime.now().timestamp(), error_density))
        
        # If no circuit breakers, use zero value for display
        if not error_data:
            error_data = [(datetime.now().timestamp(), 0.0)]
        
        self.error_chart.update_data(error_data)

    def update_memory_metrics(self):
        """Update memory metrics chart"""
        # Only update memory history at specified intervals
        now = datetime.now()
        
        memory_metrics = self._collect_memory_metrics()
        
        # Check if it's time for a history update
        if now - self.last_memory_update >= self.memory_update_interval:
            self.last_memory_update = now
            
            # Add to history
            for timestamp, value in memory_metrics:
                self.memory_history.append((timestamp, value))
            
            # Use full history for chart
            self.resource_chart.update_data(list(self.memory_history))
        else:
            # Still update chart with current metrics
            self.resource_chart.update_data(memory_metrics)

    def _collect_memory_metrics(self) -> List[Tuple[float, float]]:
        """Collect memory metrics for resource chart visualization"""
        memory_monitor = self.system_monitor.memory_monitor
        current_time = datetime.now().timestamp()
        
        # Calculate overall memory usage percentage
        total_allocated_mb = sum(memory_monitor._resource_sizes.values())
        total_memory_mb = memory_monitor._thresholds.total_memory_mb
        memory_usage_percent = (total_allocated_mb / total_memory_mb) * 100
        
        # Create data point for overall memory usage
        return [(current_time, memory_usage_percent)]
        
    def _get_health_color(self, status: HealthStatus) -> str:
        """Get color based on health status"""
        return {
            "HEALTHY": "color: #7ED321",
            "DEGRADED": "color: #F5A623",
            "UNHEALTHY": "color: #D0021B", 
            "CRITICAL": "color: #B00020"
        }[status.status]  # Use status.status (not status.name)