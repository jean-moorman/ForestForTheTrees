"""
Refactored display.py implementing Qt-based monitoring interface with best practices.
Key improvements:
- Proper separation of concerns
- Dependency injection
- Better error handling
- Type hints
- Docstrings
- Reduced widget coupling
"""
from enum import Enum, auto
import asyncio
import json
import logging
import sys
import threading
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable, Coroutine
from collections import deque
import qasync
from qasync import asyncSlot, asyncClose

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QScrollArea, QSplitter, QFrame, QLabel, QPushButton, QProgressBar,
    QToolTip, QSlider, QLineEdit, QMessageBox, QTextEdit
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSlot, QSize, pyqtSignal, QPoint, QObject, 
    QThread, pyqtSignal, QRect, QMetaObject
)
from PyQt6.QtGui import QColor, QPainter, QPen, QMouseEvent, QFont
from PyQt6.QtCharts import QChartView, QLineSeries, QChart

from resources.state import StateManager
# Update imports to include new monitoring classes
from resources.monitoring import (
    SystemMonitor, HealthTracker, MemoryMonitor, CircuitBreaker,
    CircuitState, ReliabilityMetrics, HealthStatus, EventQueue
)
from interface import AgentState
from resources import ResourceEventTypes

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

class AsyncWorkerError(Exception):
    """Custom exception for async worker errors."""
    pass

@dataclass
class TimelineState:
    """Represents a point-in-time state of an agent."""
    start_time: datetime
    state: AgentState
    metadata: Dict[str, Any]

class AsyncWorker(QObject):
    """Handles asynchronous operations using the shared event loop."""
    
    finished = pyqtSignal(object)
    error = pyqtSignal(dict)
    
    def __init__(self, coro: Coroutine, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._coro = coro
        self._task = None
        
    def start(self) -> None:
        """Start the coroutine using the shared event loop."""
        try:
            # Get the current event loop (should be the qasync loop)
            loop = asyncio.get_event_loop()
            
            # Create a task and add done callback
            self._task = loop.create_task(self._execute())
        except Exception as e:
            self.error.emit({
                'error': str(e),
                'traceback': traceback.format_exc(),
                'context': {'coroutine': str(self._coro)}
            })
    
    async def _execute(self):
        """Execute the coroutine and handle result/errors."""
        try:
            result = await self._coro
            self.finished.emit(result)
        except asyncio.CancelledError:
            self.error.emit({
                'error': 'Operation cancelled',
                'context': {'coroutine': str(self._coro)}
            })
        except Exception as e:
            self.error.emit({
                'error': str(e),
                'traceback': traceback.format_exc(),
                'context': {'coroutine': str(self._coro)}
            })
    
    def cancel(self):
        """Cancel the task if it's running."""
        if self._task and not self._task.done():
            self._task.cancel()

class AsyncHelper:
    """Manages asynchronous operations using qasync."""

    def __init__(self, parent: QObject):
        self.parent = parent
        self._workers = []
        self._shutdown = False

    def run_coroutine(self, coro: Coroutine, callback: Optional[Callable] = None) -> None:
        """Run a coroutine using the shared event loop."""
        if self._shutdown:
            logger.warning("AsyncHelper is shutting down, rejecting new coroutine")
            return
            
        # Create worker
        worker = AsyncWorker(coro, self.parent)
        
        # Connect signals
        if callback:
            worker.finished.connect(callback)
        worker.error.connect(self._handle_worker_error)
        
        # Track worker and start it
        self._workers.append(worker)
        worker.finished.connect(lambda _: self._cleanup_worker(worker))
        worker.error.connect(lambda _: self._cleanup_worker(worker))
        
        # Start the worker
        worker.start()

    def _handle_worker_error(self, error_info: Dict[str, Any]) -> None:
        """Handle worker errors."""
        self.parent._handle_error(
            "Async execution error",
            {"error": error_info, "source": "async_helper"}
        )
    
    def _cleanup_worker(self, worker: AsyncWorker) -> None:
        """Remove finished worker from tracking."""
        if worker in self._workers:
            self._workers.remove(worker)

    def stop_all(self) -> None:
        """Stop all running workers and wait for completion."""
        self._shutdown = True
        
        # Create a copy of workers to avoid modification during iteration
        workers = self._workers.copy()
        
        # Cancel all workers
        for worker in workers:
            worker.cancel()
        
        # Wait for all workers to complete (with timeout)
        start_time = datetime.now()
        timeout = timedelta(seconds=5)
        
        while self._workers and datetime.now() - start_time < timeout:
            QApplication.processEvents()  # Allow Qt events to process
            time.sleep(0.1)  # Small sleep to prevent CPU hogging
        
        # Force clear any remaining workers
        if self._workers:
            logger.warning(f"Forced clearing of {len(self._workers)} workers that didn't stop cleanly")
            self._workers.clear()

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

class AlertWidget(QFrame):
    """Widget for displaying system and agent alerts."""

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize AlertWidget."""
        super().__init__(parent)
        self._setup_ui()
        self.alerts: List[Tuple[AlertLevel, str]] = []

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

    def add_alert(self, level: AlertLevel, message: str) -> None:
        """
        Add a new alert.
        
        Args:
            level: Alert severity level
            message: Alert message
        """
        alert_widget = self._create_alert_widget(level, message)
        self.layout().addWidget(alert_widget)
        self.alerts.append((level, message))
        self._prune_old_alerts()

    def _create_alert_widget(self, level: AlertLevel, message: str) -> QTextEdit:
        """Create widget for individual alert."""
        alert_widget = QTextEdit()
        alert_widget.setReadOnly(True)
        alert_widget.setMaximumHeight(200)
        alert_widget.setText(message)
        alert_widget.setStyleSheet(f"color: {self._get_alert_color(level)}")
        return alert_widget

    def _prune_old_alerts(self) -> None:
        """Remove oldest alerts when limit is reached."""
        while self.layout().count() > 5:
            self.layout().itemAt(0).widget().setParent(None)

    @staticmethod
    def _get_alert_color(level: AlertLevel) -> str:
        """Get color for alert level."""
        return {
            AlertLevel.INFO: "#4A90E2",
            AlertLevel.WARNING: "#F5A623",
            AlertLevel.ERROR: "#D0021B",
            AlertLevel.CRITICAL: "#B00020"
        }[level]

class StateQueue:
    """Manages a queue of agent states with a maximum size."""
    
    def __init__(self, max_size: int = 1000):
        self.states = deque(maxlen=max_size)
        
    def add_state(self, state: TimelineState) -> None:
        """Add a new state to the queue."""
        self.states.append(state)
        
    def get_states_in_window(self, start: datetime, end: datetime) -> List[TimelineState]:
        """Get all states within a time window."""
        return [s for s in self.states if start <= s.start_time <= end]

class MetricsChart(QChartView):
    """Chart for displaying metrics data"""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.chart = QChart()
        self.chart.setTitle(title)
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        self.series = QLineSeries()
        self.chart.addSeries(self.series)
        
        # Create default axes
        self.chart.createDefaultAxes()
        
        # Set the chart to the view
        self.setChart(self.chart)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMinimumHeight(150)
        
    def update_data(self, data_points: List[Tuple[float, float]]):
        """Update chart with new data points"""
        if not data_points:
            return
            
        # Clear existing data
        self.series.clear()
        
        # Add data points
        for timestamp, value in data_points:
            self.series.append(timestamp, value)
        
        # Update axes
        self.chart.createDefaultAxes()
        
        # Update the view
        self.chart.update()


class PhaseMetricsWidget(QFrame):
    """Widget for displaying phase coordination metrics"""
    def __init__(self, metrics_manager, parent=None):
        super().__init__(parent)
        self.metrics_manager = metrics_manager
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        
        # Track metrics history
        self.active_phases_history = deque(maxlen=50)
        self.phase_state_history = {}
        self.phase_type_history = {}
        self.last_update = datetime.now()
        
        # Set up UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the UI components"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Phase Coordination")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Active phases chart
        self.active_chart = MetricsChart("Active Phases")
        layout.addWidget(self.active_chart)
        
        # Phase states summary
        self.phase_states_label = QLabel("Phase States: Loading...")
        layout.addWidget(self.phase_states_label)
        
        # Phase types summary
        self.phase_types_label = QLabel("Phase Types: Loading...")
        layout.addWidget(self.phase_types_label)
        
        # Nested execution status
        self.nested_exec_label = QLabel("Nested Executions: 0")
        layout.addWidget(self.nested_exec_label)
        
        self.setLayout(layout)
        self.setMinimumWidth(250)
        
    async def update_metrics(self):
        """Update the metrics display"""
        try:
            # Get phase states metrics
            self.update_active_phases()
            self.update_phase_states()
            self.update_phase_types()
            self.update_nested_executions()
        except Exception as e:
            logger.error(f"Error updating phase metrics: {e}")
    
    async def update_active_phases(self):
        """Update active phases chart"""
        try:
            # Get metrics for active phases
            metrics = await self.metrics_manager.get_metrics(
                "phase_coordinator:active_phases", 
                window=timedelta(minutes=30),
                limit=50
            )
            
            # Extract data for chart
            current_time = datetime.now().timestamp()
            if metrics:
                # Use metrics data
                data_points = [(datetime.fromisoformat(m.get("timestamp", current_time)).timestamp(), 
                               m.get("value", 0)) for m in metrics]
            else:
                # No data yet, use zero
                data_points = [(current_time, 0)]
                
            # Update chart
            self.active_chart.update_data(data_points)
            
        except Exception as e:
            logger.error(f"Error updating active phases chart: {e}")
    
    async def update_phase_states(self):
        """Update phase states metrics"""
        try:
            # Collect metrics for all possible states
            state_metrics = {}
            for state in ["INITIALIZING", "READY", "RUNNING", "PAUSED", "COMPLETED", "FAILED", "ABORTED"]:
                metrics = await self.metrics_manager.get_metrics(
                    f"phase_coordinator:phases_by_state:{state}",
                    window=timedelta(minutes=5),
                    limit=1
                )
                if metrics:
                    state_metrics[state] = metrics[0].get("value", 0)
                else:
                    state_metrics[state] = 0
            
            # Update label with summary
            states_text = ", ".join([f"{state}: {count}" for state, count in state_metrics.items() if count > 0])
            if not states_text:
                states_text = "No active phases"
            self.phase_states_label.setText(f"Phase States: {states_text}")
            
        except Exception as e:
            logger.error(f"Error updating phase states: {e}")
    
    async def update_phase_types(self):
        """Update phase types metrics"""
        try:
            # Collect metrics for all phase types
            type_metrics = {}
            for phase_type in ["ZERO", "ONE", "TWO", "THREE", "FOUR"]:
                metrics = await self.metrics_manager.get_metrics(
                    f"phase_coordinator:phases_by_type:phase_{phase_type.lower()}",
                    window=timedelta(minutes=5),
                    limit=1
                )
                if metrics:
                    type_metrics[phase_type] = metrics[0].get("value", 0)
                else:
                    type_metrics[phase_type] = 0
            
            # Update label with summary
            types_text = ", ".join([f"{phase_type}: {count}" for phase_type, count in type_metrics.items() if count > 0])
            if not types_text:
                types_text = "No phases by type"
            self.phase_types_label.setText(f"Phase Types: {types_text}")
            
        except Exception as e:
            logger.error(f"Error updating phase types: {e}")
    
    async def update_nested_executions(self):
        """Update nested executions metrics"""
        try:
            # Get nested executions metrics
            metrics = await self.metrics_manager.get_metrics(
                "phase_coordinator:pending_executions",
                window=timedelta(minutes=5),
                limit=1
            )
            
            if metrics:
                pending = metrics[0].get("value", 0)
                total = metrics[0].get("metadata", {}).get("total_executions", 0)
                self.nested_exec_label.setText(f"Nested Executions: {pending} pending, {total} total")
            else:
                self.nested_exec_label.setText("Nested Executions: No data")
                
        except Exception as e:
            logger.error(f"Error updating nested executions: {e}")

class SystemMetricsPanel(QFrame):
    def __init__(self, system_monitor: SystemMonitor, parent=None):
        super().__init__(parent)
        self.system_monitor = system_monitor
        self.health_tracker = system_monitor.health_tracker
        self.reliability_metrics = system_monitor._metrics
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        
        # Add memory history tracking
        self.memory_history = deque(maxlen=100)  # Keep last 100 data points
        self.last_memory_update = datetime.now()
        self.memory_update_interval = timedelta(seconds=10)  # Update every 10 seconds

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
class AgentOutputWidget(QFrame):
    def __init__(self, agent_id: str, parent=None):
        super().__init__(parent)
        self.agent_id = agent_id
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout()
        
        # Alert widget
        self.alert_widget = AlertWidget()
        layout.addWidget(self.alert_widget)

        # Header
        header = QLabel(agent_id.replace('_', ' ').title())
        agent_color = TimelineWidget.agent_colors.get(agent_id, '#808080')  # Default gray if color not found
        header.setStyleSheet(f"font-weight: bold; color: {agent_color}")
        # header.setStyleSheet(f"font-weight: bold; color: {TimelineWidget.agent_colors[agent_id]}")
        layout.addWidget(header)
        
        # Status
        self.status = QLabel()
        layout.addWidget(self.status)
        
        # Progress (for Phase One)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # Output content
        self.content = QLabel()
        self.content.setWordWrap(True)
        layout.addWidget(self.content)
        
        self.setLayout(layout)

    def update_output(self, output: Dict, state: AgentState):
        self.status.setText(f"Status: {state.name}")
        
        if isinstance(output, dict):
            content = ""
            for key, value in output.items():
                content += f"{key}: {value}\n"
            self.content.setText(content)

    def update_validation_status(self, validation_data: Dict):
        if not validation_data:
            return
            
        attempts = validation_data.get('attempts', 0)
        passed = validation_data.get('passed', False)
        
        status_text = f"Validation: {attempts} attempts"
        if passed:
            status_text += " ✓"
            color = "#7ED321"
        else:
            status_text += " ⚠"
            color = "#F5A623"
            
        self.validation_status.setText(status_text)
        self.validation_status.setStyleSheet(f"color: {color}")

class MetricsChart(QChartView):
    """Chart widget for displaying metric data."""
    
    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_chart(title)
        self._setup_update_timer()
        self._decimation_threshold = 1000
        self._comparison_series = {}

    def _setup_chart(self, title: str) -> None:
        """Initialize chart configuration."""
        chart = QChart()
        chart.setTitle(title)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.setChart(chart)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)  # Fix enum access

    def _setup_update_timer(self) -> None:
        """Set up batch update timer."""
        self._batch_timer = QTimer()
        self._batch_updates = []
        self._batch_timer.timeout.connect(self._process_batched_updates)
        self._batch_timer.start(20000)

    def _process_batched_updates(self) -> None:
        """Process accumulated batch updates."""
        try:
            if not self._batch_updates:
                return
                
            # Process all accumulated updates
            combined_data = []
            for data_points in self._batch_updates:
                combined_data.extend(data_points)
                
            # Sort by timestamp and remove duplicates
            combined_data.sort(key=lambda x: x[0])
            self.update_data(combined_data)
            
            # Clear processed updates
            self._batch_updates.clear()
            
        except Exception as e:
            logger.error(f"Error processing batch updates: {e}")
            
    def queue_update(self, data_points: List[Tuple[float, float]]) -> None:
        """Queue data points for batch processing."""
        self._batch_updates.append(data_points)

    def update_data(self, data_points: List[Tuple[float, float]], immediate: bool = False) -> None:
        """
        Update chart with new data points.
        
        Args:
            data_points: List of (timestamp, value) tuples
            immediate: If True, update immediately instead of batching
        """
        if not immediate:
            self.queue_update(data_points)
            return
            
        decimated_data = self._decimate_data(data_points)
        series = QLineSeries()
        for x, y in decimated_data:
            series.append(x, y)
        self.chart().removeAllSeries()
        self.chart().addSeries(series)

    def _decimate_data(self, data_points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Reduce data points using Ramer-Douglas-Peucker algorithm."""
        if len(data_points) <= self._decimation_threshold:
            return data_points
            
        epsilon = 0.1  # Adjust based on desired precision
        return self._rdp_reduce(data_points, epsilon)

    def _rdp_reduce(self, points: List[Tuple[float, float]], epsilon: float) -> List[Tuple[float, float]]:
        """Implement Ramer-Douglas-Peucker algorithm."""
        if len(points) <= 2:
            return points
            
        # Find point with max distance
        dmax = 0
        index = 0
        for i in range(1, len(points) - 1):
            d = self._point_line_distance(points[i], points[0], points[-1])
            if d > dmax:
                index = i
                dmax = d
                
        if dmax > epsilon:
            # Recursive call
            rec_results1 = self._rdp_reduce(points[:index + 1], epsilon)
            rec_results2 = self._rdp_reduce(points[index:], epsilon)
            return rec_results1[:-1] + rec_results2
        else:
            return [points[0], points[-1]]

    @staticmethod
    def _point_line_distance(point: Tuple[float, float], line_start: Tuple[float, float], 
                           line_end: Tuple[float, float]) -> float:
        """Calculate perpendicular distance from point to line."""
        x, y = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        numerator = abs((y2-y1)*x - (x2-x1)*y + x2*y1 - y2*x1)
        denominator = ((y2-y1)**2 + (x2-x1)**2)**0.5
        
        return numerator/denominator if denominator != 0 else 0

class MemoryMonitorPanel(QFrame):
    """New panel to display memory monitoring"""
    def __init__(self, memory_monitor: MemoryMonitor, parent=None):
        super().__init__(parent)
        self.memory_monitor = memory_monitor
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Memory usage display
        self.usage_label = QLabel("Memory Usage: 0%")
        layout.addWidget(self.usage_label)
        
        # Memory progress bar
        self.usage_bar = QProgressBar()
        self.usage_bar.setRange(0, 100)
        layout.addWidget(self.usage_bar)
        
        # Resource allocations
        self.resource_list = QTextEdit()
        self.resource_list.setReadOnly(True)
        layout.addWidget(QLabel("Resource Allocations:"))
        layout.addWidget(self.resource_list)
        
    def update_display(self):
        # Calculate total memory usage
        total_mb = sum(self.memory_monitor._resource_sizes.values())
        total_percent = total_mb / self.memory_monitor._thresholds.total_memory_mb * 100
        
        # Update usage display
        self.usage_label.setText(f"Memory Usage: {total_percent:.1f}%")
        self.usage_bar.setValue(int(total_percent))
        
        # Set color based on thresholds
        if total_percent > self.memory_monitor._thresholds.critical_percent:
            self.usage_bar.setStyleSheet("QProgressBar::chunk { background-color: #D0021B; }")
        elif total_percent > self.memory_monitor._thresholds.warning_percent:
            self.usage_bar.setStyleSheet("QProgressBar::chunk { background-color: #F5A623; }")
        else:
            self.usage_bar.setStyleSheet("QProgressBar::chunk { background-color: #7ED321; }")
            
        # Update resource list
        resources_text = ""
        for res_id, size in sorted(
            self.memory_monitor._resource_sizes.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]:  # Top 10 resources
            resources_text += f"{res_id}: {size:.1f} MB\n"
            
        self.resource_list.setText(resources_text)

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

    def update_metrics(self, agent_id: str):
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

class PhaseContentArea(QScrollArea):
    """Scrollable area for displaying phase-specific content."""
    
    def __init__(self, phase: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.phase = phase
        self._init_ui()
        self._setup_agents()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        self.setWidgetResizable(True)
        self.setMinimumWidth(400)
        
        content = QWidget()
        self.setWidget(content)
        layout = QVBoxLayout(content)
        
        header = QLabel(self.phase.replace('_', ' ').title())
        header.setStyleSheet("font-size: 14px; font-weight: bold")
        layout.addWidget(header)
        
        self.agent_widgets: Dict[str, AgentOutputWidget] = {}

    def _setup_agents(self) -> None:
        """Set up agent configurations."""
        self.agents = {
            'phase_zero': ['monitoring', 'soil', 'microbial', 'root_system', 
                          'mycelial', 'insect', 'bird', 'pollinator', 'evolution'],
            'phase_one': ['garden_planner', 'environmental_analysis', 
                         'root_system_architect', 'tree_placement']
        }

    def update_content(self, agent_outputs: Dict[str, Any], 
                      agent_states: Dict[str, AgentState]) -> None:
        """Update content area with new agent outputs and states."""
        for agent_id, output in agent_outputs.items():
            self._ensure_agent_widget(agent_id)
            self.agent_widgets[agent_id].update_output(
                output, 
                agent_states.get(agent_id, AgentState.READY)
            )

    def _ensure_agent_widget(self, agent_id: str) -> None:
        """Create agent widget if it doesn't exist."""
        if agent_id not in self.agent_widgets:
            widget = AgentOutputWidget(agent_id)
            self.widget().layout().addWidget(widget)
            self.agent_widgets[agent_id] = widget

    def update_phase_one_progress(self, current_agent: str) -> None:
        """Update progress indicators for phase one agents."""
        sequence = self.agents['phase_one']
        try:
            current_idx = sequence.index(current_agent)
            
            for agent in sequence[:current_idx]:
                self.agent_widgets[agent].mark_complete()
                
            if current_idx < len(sequence):
                self.agent_widgets[current_agent].show_progress()
                
        except ValueError:
            logger.error(f"Invalid agent {current_agent} in phase one sequence")

class TimelineWidget(QWidget):
    # Signal emitted when an agent is selected (phase, agent_name)
    agent_selected = pyqtSignal(str, str)
    
    # Color scheme for different agents
    agent_colors = {
        'monitoring': '#4A90E2', 'soil': '#50E3C2', 'microbial': '#F5A623',
        'root_system': '#7ED321', 'mycelial': '#BD10E0', 'insect': '#9013FE',
        'bird': '#417505', 'pollinator': '#D0021B', 'evolution': '#4A4A4A',
        'garden_planner': '#B8E986', 'environmental_analysis': '#7ED321',
        'root_system_architect': '#417505', 'tree_placement': '#50E3C2'
    }

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_state()
        self._init_ui()
        self.setMouseTracking(True)

    def _init_state(self) -> None:
        """Initialize timeline state."""
        self.time_window = timedelta(hours=1)
        self.agents = {
            'phase_zero': ['monitoring', 'soil', 'microbial', 'root_system',
                        'mycelial', 'insect', 'bird', 'pollinator', 'evolution'],
            'phase_one': ['garden_planner', 'environmental_analysis',
                        'root_system_architect', 'tree_placement']
        }
        
        # Initialize agent states dictionary
        self.agent_states = {
            agent: StateQueue() 
            for phase in self.agents.values() 
            for agent in phase
        }
        
        self.selected_agent = None
        self.hovered_agent = None
        self.phase_height = 60   
        self.agent_height = 16   
        self.agent_padding = 2   
        self.phase_padding = 10
        
    def _init_ui(self) -> None:
        """Initialize UI properties."""
        self.setMinimumHeight(self._calculate_total_height())
        self.setMinimumWidth(600)
        # Set widget to use stylesheet background
        self.setAutoFillBackground(True)
        self.setStyleSheet("background-color: white;")

    def _calculate_total_height(self) -> int:
        """Calculate total required height for the widget."""
        total_phases = len(self.agents)
        return (total_phases * self.phase_height) + ((total_phases - 1) * self.phase_padding)

    def _get_agent_rect(self, phase: str, agent: str) -> QRect:
        """Get the rectangle for a specific agent in a specific phase."""
        phase_idx = list(self.agents.keys()).index(phase)
        agent_idx = self.agents[phase].index(agent)
        
        y_offset = phase_idx * (self.phase_height + self.phase_padding)
        y = y_offset + (agent_idx * (self.agent_height + self.agent_padding))
        
        # Fixed bar width instead of full width
        bar_width = 120
        x = 10  # Left padding
        
        return QRect(x, y, bar_width, self.agent_height)

    def _get_agent_at_position(self, pos) -> tuple[Optional[str], Optional[str]]:
        """Get the agent and phase at the given position."""
        for phase in self.agents:
            for agent in self.agents[phase]:
                rect = self._get_agent_rect(phase, agent)
                if rect.contains(pos):
                    return phase, agent
        return None, None

    def mousePressEvent(self, event) -> None:
        """Handle mouse press events for agent selection."""
        phase, agent = self._get_agent_at_position(event.pos())
        if agent:
            self.selected_agent = (phase, agent)
            # Emit signal to update metrics panel
            self.agent_selected.emit(phase, agent)
            self.update()
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move events for hover effects."""
        phase, agent = self._get_agent_at_position(event.pos())
        if (phase, agent) != self.hovered_agent:
            self.hovered_agent = (phase, agent) if agent else None
            self.update()
        event.accept()

    def leaveEvent(self, event) -> None:
        """Handle mouse leave events."""
        if self.hovered_agent:
            self.hovered_agent = None
            self.update()
        event.accept()

    def paintEvent(self, event) -> None:
        """Paint the timeline widget."""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Draw phases and agents
            for phase_idx, (phase, agents) in enumerate(self.agents.items()):
                # Draw phase label
                font = QFont()
                font.setBold(True)
                painter.setFont(font)
                phase_label = phase.replace('_', ' ').title()
                y_offset = phase_idx * (self.phase_height + self.phase_padding)
                painter.drawText(10, y_offset - 5, phase_label)

                # Draw agents
                for agent in agents:
                    rect = self._get_agent_rect(phase, agent)
                    
                    # Draw agent background
                    color = QColor(self.agent_colors[agent])
                    if (phase, agent) == self.selected_agent:
                        painter.fillRect(rect, color.darker(120))
                    elif (phase, agent) == self.hovered_agent:
                        painter.fillRect(rect, color.lighter(120))
                    else:
                        painter.fillRect(rect, color)

                    # Draw agent label
                    painter.setPen(Qt.GlobalColor.white)  # Updated to use GlobalColor enum
                    font = QFont()
                    font.setPointSize(10)
                    painter.setFont(font)
                    agent_label = agent.replace('_', ' ').title()
                    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, agent_label)
        finally:
            painter.end()

    def sizeHint(self) -> QSize:
        """Provide size hint for layout management."""
        return QSize(600, self._calculate_total_height())
    
    def _validate_resource_id(self, resource_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate resource ID format and extract agent ID.
        
        Args:
            resource_id: Resource identifier string
            
        Returns:
            Tuple of (is_valid, agent_id)
        """
        if not resource_id:
            return False, None
            
        parts = resource_id.split(':')
        if len(parts) != 3 or parts[0] != 'agent':
            return False, None
            
        agent_id = parts[1]
        # Verify agent exists in our configuration
        for phase_agents in self.agents.values():
            if agent_id in phase_agents:
                return True, agent_id
                
        return False, None

    def _handle_agent_state_change(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle agent state change events."""
        try:
            resource_id = data.get('resource_id', '')
            is_valid, agent_id = self._validate_resource_id(resource_id)
            
            if not is_valid:
                logger.error(f"Invalid resource ID format: {resource_id}")
                return
                
            if agent_id not in self.agent_states:
                logger.error(f"Unknown agent ID: {agent_id}")
                return
                
            try:
                new_state = AgentState[data.get('value', 'READY')]
            except KeyError:
                logger.error(f"Invalid agent state: {data.get('value')}")
                return
                
            # Add new state to timeline
            self.agent_states[agent_id].add_state(TimelineState(
                start_time=datetime.now(),
                state=new_state,
                metadata=data.get('metadata', {})
            ))
            
            # Queue update
            self._pending_updates.add(('agent_state', agent_id))
            
        except Exception as e:
            logger.error(f"Error handling agent state change: {e}")
            self._handle_error(
                ResourceEventTypes.ERROR_OCCURRED.value,
                {'error': str(e), 'source': 'agent_state_handler'}
            )


class PromptInterface(QWidget):
    """Interface for user task prompts."""
    
    prompt_submitted = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Enter your task prompt...")
        
        self.submit_button = QPushButton("Submit")
        self.submit_button.setEnabled(False)
        
        layout.addWidget(self.prompt_input)
        layout.addWidget(self.submit_button)

    def _connect_signals(self) -> None:
        """Connect signal handlers."""
        self.prompt_input.textChanged.connect(self._handle_input_change)
        self.prompt_input.returnPressed.connect(self._handle_submit)
        self.submit_button.clicked.connect(self._handle_submit)

    def _handle_input_change(self, text: str) -> None:
        """Enable/disable submit button based on input."""
        self.submit_button.setEnabled(bool(text.strip()))

    def _handle_submit(self) -> None:
        """Handle prompt submission."""
        text = self.prompt_input.text().strip()
        if text:
            self.prompt_submitted.emit(text)
            self.prompt_input.clear()
            self.setEnabled(False)

    def reset(self) -> None:
        """Reset interface after processing."""
        self.setEnabled(True)
        self.prompt_input.setFocus()


class CircuitBreakerPanel(QFrame):
    """Panel for displaying circuit breaker status and metrics."""
    
    def __init__(self, system_monitor: SystemMonitor, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.system_monitor = system_monitor
        self.circuit_widgets = {}
        self._init_ui()
        
    def _init_ui(self) -> None:
        """Initialize UI components."""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Header
        header = QLabel("Circuit Breakers")
        header.setProperty("heading", True)
        header.setStyleSheet("font-size: 14px; font-weight: bold")
        layout.addWidget(header)
        
        # Scroll area for circuit widgets
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        layout.addWidget(scroll_area)
        
        # Container for circuit widgets
        self.circuit_container = QWidget()
        self.circuit_layout = QVBoxLayout(self.circuit_container)
        self.circuit_layout.setContentsMargins(0, 0, 0, 0)
        self.circuit_layout.setSpacing(8)
        scroll_area.setWidget(self.circuit_container)
        
        # Add alert widget at the bottom
        self.alert_widget = AlertWidget()
        layout.addWidget(self.alert_widget)
        
        self.setMinimumWidth(300)
        self.setMaximumWidth(500)
        
    def update_circuits(self) -> None:
        """Update all circuit widgets with current data."""
        try:
            # Get all circuit breakers
            circuit_breakers = self.system_monitor._circuit_breakers
            
            # Create or update widgets for each circuit
            for name, breaker in circuit_breakers.items():
                if name not in self.circuit_widgets:
                    # Create new widget
                    self._create_circuit_widget(name)
                
                # Update existing widget
                self._update_circuit_widget(name, breaker)
                
            # Remove widgets for circuits that no longer exist
            for name in list(self.circuit_widgets.keys()):
                if name not in circuit_breakers:
                    self._remove_circuit_widget(name)
                    
        except Exception as e:
            self.alert_widget.add_alert(
                AlertLevel.ERROR,
                f"Failed to update circuit breakers: {str(e)}"
            )
            
    def _create_circuit_widget(self, name: str) -> None:
        """Create a new widget for a circuit breaker."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        widget.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Header with circuit name
        header_layout = QHBoxLayout()
        
        name_label = QLabel(name.replace('_', ' ').title())
        name_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        header_layout.addWidget(name_label)
        
        # State indicator
        state_label = QLabel("UNKNOWN")
        state_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        state_label.setStyleSheet("font-weight: bold; color: #808080;")
        header_layout.addWidget(state_label)
        
        layout.addLayout(header_layout)
        
        # Add divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #374151;")
        layout.addWidget(divider)
        
        # Metrics layout (two columns)
        metrics_layout = QGridLayout()
        metrics_layout.setColumnStretch(0, 1)
        metrics_layout.setColumnStretch(1, 1)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        
        # Failure count
        metrics_layout.addWidget(QLabel("Failures:"), 0, 0)
        failure_count = QLabel("0")
        failure_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        metrics_layout.addWidget(failure_count, 0, 1)
        
        # Error density
        metrics_layout.addWidget(QLabel("Error Rate:"), 1, 0)
        error_density = QLabel("0.0/min")
        error_density.setAlignment(Qt.AlignmentFlag.AlignRight)
        metrics_layout.addWidget(error_density, 1, 1)
        
        # Recovery time
        metrics_layout.addWidget(QLabel("Avg Recovery:"), 2, 0)
        recovery_time = QLabel("N/A")
        recovery_time.setAlignment(Qt.AlignmentFlag.AlignRight)
        metrics_layout.addWidget(recovery_time, 2, 1)
        
        # Time in state
        metrics_layout.addWidget(QLabel("Time in State:"), 3, 0)
        time_in_state = QLabel("0s")
        time_in_state.setAlignment(Qt.AlignmentFlag.AlignRight)
        metrics_layout.addWidget(time_in_state, 3, 1)
        
        layout.addLayout(metrics_layout)
        
        # State durations progress bars
        layout.addWidget(QLabel("State Durations:"))
        
        state_bars_layout = QVBoxLayout()
        
        # CLOSED state
        closed_layout = QHBoxLayout()
        closed_layout.addWidget(QLabel("CLOSED"))
        closed_bar = QProgressBar()
        closed_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #374151;
                border-radius: 2px;
                text-align: center;
                background-color: #111827;
            }
            QProgressBar::chunk {
                background-color: #7ED321;
                border-radius: 2px;
            }
        """)
        closed_layout.addWidget(closed_bar)
        state_bars_layout.addLayout(closed_layout)
        
        # OPEN state
        open_layout = QHBoxLayout()
        open_layout.addWidget(QLabel("OPEN"))
        open_bar = QProgressBar()
        open_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #374151;
                border-radius: 2px;
                text-align: center;
                background-color: #111827;
            }
            QProgressBar::chunk {
                background-color: #D0021B;
                border-radius: 2px;
            }
        """)
        open_layout.addWidget(open_bar)
        state_bars_layout.addLayout(open_layout)
        
        # HALF_OPEN state
        half_open_layout = QHBoxLayout()
        half_open_layout.addWidget(QLabel("HALF_OPEN"))
        half_open_bar = QProgressBar()
        half_open_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #374151;
                border-radius: 2px;
                text-align: center;
                background-color: #111827;
            }
            QProgressBar::chunk {
                background-color: #F5A623;
                border-radius: 2px;
            }
        """)
        half_open_layout.addWidget(half_open_bar)
        state_bars_layout.addLayout(half_open_layout)
        
        layout.addLayout(state_bars_layout)
        
        # Last failure info
        layout.addWidget(QLabel("Last Failure:"))
        last_failure = QLabel("None")
        last_failure.setWordWrap(True)
        layout.addWidget(last_failure)
        
        # Store references to all updatable widgets
        widget.name_label = name_label
        widget.state_label = state_label
        widget.failure_count = failure_count
        widget.error_density = error_density
        widget.recovery_time = recovery_time
        widget.time_in_state = time_in_state
        widget.closed_bar = closed_bar
        widget.open_bar = open_bar
        widget.half_open_bar = half_open_bar
        widget.last_failure = last_failure
        
        # Add to layout and store in dictionary
        self.circuit_layout.addWidget(widget)
        self.circuit_widgets[name] = widget
        
    def _update_circuit_widget(self, name: str, breaker: CircuitBreaker) -> None:
        """Update an existing circuit widget with current data."""
        widget = self.circuit_widgets.get(name)
        if not widget:
            return
            
        # Get metrics
        metrics = self.system_monitor._metrics
        
        # Update state
        state = breaker.state.name
        widget.state_label.setText(state)
        
        # Set state color
        state_colors = {
            "CLOSED": "#7ED321",    # Green
            "OPEN": "#D0021B",      # Red
            "HALF_OPEN": "#F5A623"  # Orange
        }
        widget.state_label.setStyleSheet(f"font-weight: bold; color: {state_colors.get(state, '#808080')};")
        
        # Update metrics
        widget.failure_count.setText(str(breaker.failure_count))
        
        error_density = metrics.get_error_density(name)
        widget.error_density.setText(f"{error_density:.2f}/min")
        
        avg_recovery = metrics.get_avg_recovery_time(name)
        if avg_recovery is not None:
            widget.recovery_time.setText(f"{avg_recovery:.1f}s")
        else:
            widget.recovery_time.setText("N/A")
        
        # Time in current state
        time_in_state = (datetime.now() - breaker.last_state_change).total_seconds()
        if time_in_state < 60:
            time_str = f"{time_in_state:.1f}s"
        elif time_in_state < 3600:
            time_str = f"{time_in_state / 60:.1f}m"
        else:
            time_str = f"{time_in_state / 3600:.1f}h"
        widget.time_in_state.setText(time_str)
        
        # Update state duration bars
        total_time = 0
        state_durations = metrics.get_state_durations(name)
        for state_name in ["CLOSED", "OPEN", "HALF_OPEN"]:
            total_time += state_durations.get(state_name, 0)
        
        # Set bar values (as percentages of total time)
        if total_time > 0:
            widget.closed_bar.setValue(int(state_durations.get("CLOSED", 0) / total_time * 100))
            widget.open_bar.setValue(int(state_durations.get("OPEN", 0) / total_time * 100))
            widget.half_open_bar.setValue(int(state_durations.get("HALF_OPEN", 0) / total_time * 100))
            
            # Also set text
            widget.closed_bar.setFormat(f"{state_durations.get('CLOSED', 0):.1f}s ({widget.closed_bar.value()}%)")
            widget.open_bar.setFormat(f"{state_durations.get('OPEN', 0):.1f}s ({widget.open_bar.value()}%)")
            widget.half_open_bar.setFormat(f"{state_durations.get('HALF_OPEN', 0):.1f}s ({widget.half_open_bar.value()}%)")
        else:
            widget.closed_bar.setValue(0)
            widget.open_bar.setValue(0)
            widget.half_open_bar.setValue(0)
            
            widget.closed_bar.setFormat("0.0s (0%)")
            widget.open_bar.setFormat("0.0s (0%)")
            widget.half_open_bar.setFormat("0.0s (0%)")
        
        # Last failure info
        if breaker.last_failure_time:
            time_ago = (datetime.now() - breaker.last_failure_time).total_seconds()
            if time_ago < 60:
                time_str = f"{time_ago:.1f}s ago"
            elif time_ago < 3600:
                time_str = f"{time_ago / 60:.1f}m ago"
            else:
                time_str = f"{time_ago / 3600:.1f}h ago"
                
            widget.last_failure.setText(f"{time_str}")
        else:
            widget.last_failure.setText("None")
            
    def _remove_circuit_widget(self, name: str) -> None:
        """Remove a circuit widget that is no longer needed."""
        widget = self.circuit_widgets.pop(name, None)
        if widget:
            self.circuit_layout.removeWidget(widget)
            widget.deleteLater()
            
    def handle_circuit_state_change(self, component: str, data: Dict[str, Any]) -> None:
        """Handle circuit state change events."""
        # Extract circuit name from component (format: circuit_breaker_name)
        if component.startswith("circuit_breaker_"):
            circuit_name = component[15:]  # Remove "circuit_breaker_" prefix
            if circuit_name in self.system_monitor._circuit_breakers:
                # Update just this circuit
                self._update_circuit_widget(
                    circuit_name, 
                    self.system_monitor._circuit_breakers[circuit_name]
                )
                
                # Add alert for state changes
                if data.get("state") == "OPEN":
                    self.alert_widget.add_alert(
                        AlertLevel.ERROR,
                        f"Circuit {circuit_name} is OPEN: {data.get('reason', 'failure threshold exceeded')}"
                    )
                elif data.get("state") == "HALF_OPEN":
                    self.alert_widget.add_alert(
                        AlertLevel.WARNING,
                        f"Circuit {circuit_name} is testing recovery"
                    )
                elif data.get("state") == "CLOSED" and data.get("reason") == "recovery_confirmed":
                    self.alert_widget.add_alert(
                        AlertLevel.INFO,
                        f"Circuit {circuit_name} has recovered and is CLOSED"
                    )


class ForestDisplay(QMainWindow):
    """Main application window for forest monitoring system."""

    error_signal = pyqtSignal(str, dict)

    def __init__(self, event_queue: EventQueue, orchestrator, system_monitor: SystemMonitor):
        """Initialize the main window."""
        super().__init__()
        self.event_queue = event_queue
        self.orchestrator = orchestrator
        self.system_monitor = system_monitor
        self.system_metrics = SystemMetrics(self)
        self.async_helper = AsyncHelper(self)
        self._timers = []  # Registry for all timers
        self._setup_window()

        # Use qasync to schedule initialization instead of create_task
        loop = asyncio.get_event_loop()
        loop.create_task(self._init_monitoring())

        self._init_ui()
        self._connect_signals()

    def _create_timer(self, interval, callback):
        """Create and track a QTimer."""
        timer = QTimer()
        timer.timeout.connect(callback)
        timer.start(interval)
        self._timers.append(timer)
        return timer
    
    def _cleanup_timers(self):
        """Stop all timers in registry."""
        for timer in self._timers:
            timer.stop()
        
        # Also find and stop any timers in child widgets
        for timer in self.findChildren(QTimer):
            timer.stop()
            
    @asyncSlot()
    async def setup_async(self):
        """Setup async components"""
        # Start monitoring systems
        await self.system_monitor.memory_monitor.start()
        await self.system_monitor.start()
        
        # Register built-in circuit breakers
        default_circuit = CircuitBreaker("system", self.event_queue)
        await self.system_monitor.register_circuit_breaker("system", default_circuit)

    def _apply_styles(self) -> None:
        """Apply application-wide styles."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #111827;
            }
            QWidget {
                background-color: #111827;
                color: #e5e7eb;
            }
            QLabel {
                color: #e5e7eb;
                font-size: 12px;
                padding: 0;
                background: transparent;
            }
            QLabel[heading="true"] {
                font-size: 14px;
                font-weight: bold;
                color: #f3f4f6;
                padding: 8px;
                background-color: #1f2937;
                border-radius: 4px;
                margin-bottom: 4px;
            }
            QFrame {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 4px;
            }
            QFrame[panel="true"] {
                margin: 4px;
                padding: 8px;
            }
            QPushButton {
                background-color: #3b82f6;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QProgressBar {
                border: 1px solid #374151;
                border-radius: 4px;
                text-align: center;
                height: 6px;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 3px;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #1f2937;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #4b5563;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QSplitter::handle {
                background-color: #374151;
                width: 1px;
            }
            QChartView {
                background-color: #1f2937;
                border-radius: 6px;
            }
            TimelineWidget {
                max-height: 120px;
                background-color: #1f2937;
                border-radius: 6px;
                border: 1px solid #374151;
            }
            QLineEdit {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 4px;
                padding: 6px;
                color: #e5e7eb;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.setWindowTitle("Forest For The Trees - System Monitor")
        self.setMinimumSize(QSize(1200, 800))
        self._apply_styles()

    async def _init_monitoring(self) -> None:
        """Initialize monitoring systems."""
        self._pending_updates = set()
        await self._setup_resource_subscriptions()
        self._setup_update_timer()

    def _setup_update_timer(self) -> None:
        """Set up timer for periodic UI updates."""
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._process_pending_updates)
        self._update_timer.start(1000)  # Update every second
        
    def _process_pending_updates(self) -> None:
        """Process any pending UI updates."""
        try:
            updates = self._pending_updates.copy()
            self._pending_updates.clear()
            
            for update_type, update_id in updates:
                if update_type == 'agent_state':
                    self._update_agent_display(update_id)
                elif update_type == 'metric':
                    self._update_metrics_display(update_id)
            
            # Update circuit panel periodically regardless of specific events
            if hasattr(self, 'circuit_panel'):
                self.circuit_panel.update_circuits()
                    
        except Exception as e:
            self._handle_error(
                "Failed to process updates",
                {'error': str(e), 'source': 'update_processor'}
            )
            
    def _update_agent_display(self, agent_id: str) -> None:
        """Update display for specific agent."""
        if agent_id in self.phase_content.agent_widgets:
            widget = self.phase_content.agent_widgets[agent_id]
            current_state = self.timeline.agent_states[agent_id].states[-1].state
            widget.update_output({}, current_state)  # Update with actual output as needed
            
    def _update_metrics_display(self, metric_id: str) -> None:
        """Update metrics display based on metric type."""
        try:
            # Call the appropriate update method based on metric type
            if metric_id == 'system_health':
                self.metrics_panel.update_health_status()
            elif metric_id == 'error_rate':
                self.metrics_panel.update_error_metrics()
            elif metric_id == 'memory_usage':
                self.metrics_panel.update_memory_metrics()
            else:
                # If unsure which metric changed, update all
                self.metrics_panel.update_all()
                
            # Update agent metrics if an agent is selected
            if hasattr(self, 'agent_metrics') and self.timeline.selected_agent:
                self.agent_metrics.update_metrics(self.timeline.selected_agent[1])
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            self._handle_error(
                "Failed to update metrics",
                {'error': str(e), 'source': 'metrics_updater'}
            )

    def _init_ui(self) -> None:
        """Initialize user interface."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        self._create_header(layout)
        self._create_prompt_interface(layout)
        self._create_timeline(layout)
        self._create_content_area(layout)

    def _connect_signals(self) -> None:
        """Connect signal handlers."""
        self.error_signal.connect(self._handle_error)
        # Connect prompt submission to the non-coroutine handler
        self.prompt_interface.prompt_submitted.connect(self._handle_prompt_submission)

    def _handle_prompt_submission(self, prompt: str) -> None:
        """Non-coroutine handler for prompt submission that launches async processing."""
        try:
            # Disable the interface immediately
            self.prompt_interface.setEnabled(False)
            
            # Schedule coroutine in the shared event loop
            loop = asyncio.get_event_loop()
            task = loop.create_task(self._process_prompt_async(prompt))
            
            # Connect callback with a lambda to handle result
            task.add_done_callback(
                lambda t: self._handle_prompt_result(
                    t.result() if not t.cancelled() and not t.exception() else None
                )
            )
            
        except Exception as e:
            logger.error(f"Failed to submit prompt: {str(e)}", exc_info=True)
            self.error_signal.emit(
                f"Failed to submit prompt: {str(e)}",
                {'error': str(e), 'source': 'prompt_submission'}
            )
            self.prompt_interface.reset()

    async def _process_prompt_async(self, prompt: str) -> Dict[str, Any]:
        """Asynchronous prompt processing."""
        try:
            if not prompt.strip():
                raise ValueError("Empty prompt submitted")
                
            logger.info(f"Processing prompt: {prompt}")
            
            # Process the task and await the result using the orchestrator interface
            result = await self.orchestrator.process_task(prompt)
            
            if result is None:
                raise ValueError("Prompt processing returned no result")
            
            # Validate result structure
            if not isinstance(result, dict):
                raise TypeError(f"Expected dict result, got {type(result)}")
        
            # Validate required fields
            required_fields = ['status', 'phase_one_outputs']
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                raise ValueError(f"Missing required fields in result: {missing_fields}")
            
            logger.info(f"Prompt processed successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Prompt processing failed: {str(e)}", exc_info=True)
            raise

    def _handle_prompt_result(self, result: Optional[Dict[str, Any]]) -> None:
        """Handle the completion of async prompt processing with improved error handling."""
        try:
            # Validate result exists
            if result is None:
                raise ValueError("Prompt processing returned no result")
                
            # Validate result structure before updating UI
            if not isinstance(result, dict):
                raise TypeError(f"Expected dict result, got {type(result)}")
                
            status = result.get('status')
            if status != "success":
                raise ValueError(f"Prompt processing failed with status: {status}")
                
            outputs = result.get('phase_one_outputs')
            if not isinstance(outputs, dict):
                raise TypeError(f"Expected dict outputs, got {type(outputs)}")
                
            # Update UI with validated result
            for agent_id, output in outputs.items():
                if agent_id in self.phase_content.agent_widgets:
                    widget = self.phase_content.agent_widgets[agent_id]
                    if widget is not None:
                        widget.update_output(
                            output or {},  # Ensure we pass a dict even if output is None
                            AgentState.READY
                        )
                        
        except Exception as e:
            error_msg = f"Failed to process prompt result: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error_signal.emit(
                error_msg,
                {
                    'error': str(e),
                    'source': 'prompt_handler',
                    'result': result  # Include result in error context
                }
            )
        finally:
            # Always re-enable the prompt interface
            QTimer.singleShot(100, self.prompt_interface.reset)

    async def _setup_resource_subscriptions(self) -> None:
        """Set up event subscriptions for the monitoring system."""
        subscriptions = [
            (ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value, self._handle_health_change),
            (ResourceEventTypes.RESOURCE_ALERT_CREATED.value, self._handle_resource_alert),
            (ResourceEventTypes.METRIC_RECORDED.value, self._handle_monitoring_status),
            (ResourceEventTypes.ERROR_OCCURRED.value, self._handle_system_error)
        ]
        
        # Subscribe to each event type
        for event_type, handler in subscriptions:
            await self.system_monitor.event_queue.subscribe(event_type, handler)

    def _handle_monitoring_status(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle periodic monitoring status updates."""
        try:
            # Update memory monitoring in metrics panel
            if 'memory_monitor' in data and hasattr(self, 'metrics_panel'):
                self.metrics_panel.update_memory_metrics()
                
            # Update circuit breakers in circuit panel
            if 'circuit_breakers' in data and hasattr(self, 'circuit_panel'):
                self.circuit_panel.update_circuits()
                
            # Update agent count in header
            agent_count = len(data.get('circuit_breakers', {}))
            self.agent_count.setText(f"Active Circuits: {agent_count}")
            
        except Exception as e:
            logger.error(f"Error handling monitoring status: {e}")
            # Don't show UI error for this routine update

    def _handle_system_error(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle system-level errors."""
        try:
            error = data.get('error', 'Unknown error')
            component = data.get('component', 'system')
            
            logger.error(f"System error from {component}: {error}")
            
            # Add to alert widget
            if hasattr(self, 'metrics_panel'):
                self.metrics_panel.alert_widget.add_alert(
                    AlertLevel.ERROR,
                    f"System error in {component}: {error}"
                )
                
            # Update system status
            self.system_status.setText(f"System: Error")
            self.system_status.setStyleSheet("color: #D0021B")
            
        except Exception as e:
            logger.error(f"Error handling system error: {e}")
            self._handle_error(
                "Failed to handle system error event",
                {'error': str(e), 'source': 'error_handler', 'event_data': data}
            )

    def _handle_health_change(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle system health change events."""
        try:
            component = data.get('component', '')
            status = data.get('status', 'UNKNOWN')
            
            # Circuit breaker events
            if component.startswith('circuit_breaker_'):
                # Update circuit panel if it exists
                if hasattr(self, 'circuit_panel'):
                    self.circuit_panel.handle_circuit_state_change(component, data)
                    
                # Add to pending updates to refresh metrics
                self._pending_updates.add(('metric', 'error_rate'))
                    
            # System memory health events
            elif component == 'system_memory':
                # Update memory usage display
                if hasattr(self, 'metrics_panel'):
                    self.metrics_panel.update_memory_metrics()
                    
                # Add alert based on status
                if status == "CRITICAL":
                    self._show_memory_alert(data)
                    
            # Overall system health
            elif component == 'system':
                # Update health status in metrics panel
                if hasattr(self, 'metrics_panel'):
                    self.metrics_panel.update_health_status()
                    
                # Update system status indicator in header
                self.system_status.setText(f"System: {status}")
                self.system_status.setStyleSheet(self._get_system_status_color(status))
                
            # Update pending metrics to refresh displays
            self._pending_updates.add(('metric', component))
                
        except Exception as e:
            logger.error(f"Error handling health change: {e}")
            self._handle_error(
                "Failed to handle health change event",
                {'error': str(e), 'source': 'health_handler', 'event_data': data}
            )
            
    def _get_system_status_color(self, status: str) -> str:
        """Get color for system status display."""
        return {
            "HEALTHY": "color: #7ED321",
            "DEGRADED": "color: #F5A623",
            "UNHEALTHY": "color: #D0021B",
            "CRITICAL": "color: #B00020",
            "ERROR": "color: #D0021B"
        }.get(status, "color: #808080")  # Default to gray
        
    def _show_memory_alert(self, data: Dict[str, Any]) -> None:
        """Show memory alert notification."""
        usage_percentage = data.get('metadata', {}).get('usage_percentage', 0) * 100
        self.metrics_panel.alert_widget.add_alert(
            AlertLevel.CRITICAL,
            f"Memory usage critical: {usage_percentage:.1f}% of available memory used"
        )

    def _handle_resource_alert(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle resource alert events."""
        try:
            alert_type = data.get('alert_type', '')
            level = data.get('level', 'WARNING')
            
            if alert_type == 'memory':
                # Handle memory alerts
                percent = data.get('percent', 0)
                total_mb = data.get('total_mb', 0)
                
                # Map alert level to UI alert level
                alert_level = {
                    'WARNING': AlertLevel.WARNING,
                    'CRITICAL': AlertLevel.CRITICAL
                }.get(level, AlertLevel.WARNING)
                
                # Add alert to metrics panel
                if hasattr(self, 'metrics_panel'):
                    self.metrics_panel.alert_widget.add_alert(
                        alert_level,
                        f"Memory alert: {percent:.1f}% used ({total_mb:.1f} MB)"
                    )
                    
                # Update memory metrics
                self._pending_updates.add(('metric', 'memory_usage'))
                    
            elif alert_type == 'resource_memory':
                # Handle specific resource memory alerts
                resource_id = data.get('resource_id', 'unknown')
                size_mb = data.get('size_mb', 0)
                threshold_mb = data.get('threshold_mb', 0)
                
                # Add alert to metrics panel
                if hasattr(self, 'metrics_panel'):
                    self.metrics_panel.alert_widget.add_alert(
                        AlertLevel.WARNING,
                        f"Resource {resource_id} exceeds memory threshold: {size_mb:.1f} MB (threshold: {threshold_mb:.1f} MB)"
                    )
                    
                # Update memory metrics
                self._pending_updates.add(('metric', 'memory_usage'))
                    
            elif alert_type == 'circuit_breaker':
                # Handle circuit breaker alerts
                circuit_name = data.get('circuit_name', 'unknown')
                message = data.get('message', 'Circuit breaker alert')
                
                # Map alert level to UI alert level
                alert_level = {
                    'WARNING': AlertLevel.WARNING,
                    'ERROR': AlertLevel.ERROR,
                    'CRITICAL': AlertLevel.CRITICAL
                }.get(level, AlertLevel.WARNING)
                
                # Add alert to circuit panel
                if hasattr(self, 'circuit_panel'):
                    self.circuit_panel.alert_widget.add_alert(
                        alert_level,
                        f"Circuit {circuit_name}: {message}"
                    )
                    
                # Update circuit display
                self._pending_updates.add(('metric', f'circuit_{circuit_name}'))
                    
        except Exception as e:
            logger.error(f"Error handling resource alert: {e}")
            self._handle_error(
                "Failed to handle resource alert",
                {'error': str(e), 'source': 'alert_handler', 'event_data': data}
            )

    def _handle_agent_state_change(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Handle agent state change events.
        
        Args:
            event_type: Type of event that occurred
            data: Event data including agent ID and new state
        """
        try:
            # Extract agent ID from resource ID (format: "agent:name:state")
            agent_id = data.get('resource_id', '').split(':')[1]
            if agent_id in self.timeline.agent_states:
                new_state = AgentState[data.get('value', 'READY')]
                
                # Add new state to timeline
                self.timeline.agent_states[agent_id].add_state(TimelineState(
                    start_time=datetime.now(),
                    state=new_state,
                    metadata=data.get('metadata', {})
                ))
                
                # Queue update
                self._pending_updates.add(('agent_state', agent_id))
                
        except Exception as e:
            logger.error(f"Error handling agent state change: {e}")
            self._handle_error(
                ResourceEventTypes.ERROR_OCCURRED.value,
                {'error': str(e), 'source': 'agent_state_handler'}
            )
            
    def _handle_metric_update(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Handle metric update events.
        
        Args:
            event_type: Type of event that occurred
            data: Event data including metric name and value
        """
        try:
            metric_name = data.get('metric')
            if metric_name:
                self._pending_updates.add(('metric', metric_name))
        except Exception as e:
            logger.error(f"Error handling metric update: {e}")
            self._handle_error(
                ResourceEventTypes.ERROR_OCCURRED.value,
                {'error': str(e), 'source': 'metric_handler'}
            )

    def _create_header(self, layout: QVBoxLayout) -> None:
        """Create the application header."""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 8, 8, 8)
        
        # Title
        title = QLabel("Forest For The Trees - System Monitor")
        title.setProperty("heading", True)
        header_layout.addWidget(title)
        
        # System status indicators
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        
        self.system_status = QLabel("System: Healthy")
        self.system_status.setStyleSheet("color: #7ED321")
        status_layout.addWidget(self.system_status)
        
        self.agent_count = QLabel("Active Agents: 0")
        status_layout.addWidget(self.agent_count)
        
        header_layout.addWidget(status_widget)
        header_layout.setStretch(0, 2)
        header_layout.setStretch(1, 1)
        
        layout.addWidget(header)

    def _create_prompt_interface(self, layout: QVBoxLayout) -> None:
        """Create the prompt input interface."""
        self.prompt_interface = PromptInterface()
        layout.addWidget(self.prompt_interface)

    def _create_timeline(self, layout: QVBoxLayout) -> None:
        """Create the timeline visualization."""
        self.timeline = TimelineWidget()
        self.timeline.agent_selected.connect(self._handle_agent_selection)
        layout.addWidget(self.timeline)

    def _create_content_area(self, layout: QVBoxLayout) -> None:
        """Create the main content area with metrics and phase content."""
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Metrics
        metrics_container = QWidget()
        metrics_layout = QVBoxLayout(metrics_container)
        
        self.metrics_panel = SystemMetricsPanel(self.system_monitor)
        self.system_metrics.metric_panel = self.metrics_panel
        self.circuit_panel = CircuitBreakerPanel(self.system_monitor)
        self.agent_metrics = AgentMetricsPanel(self.system_monitor)
        
        metrics_layout.addWidget(self.metrics_panel)
        metrics_layout.addWidget(self.agent_metrics)
        splitter.addWidget(metrics_container)
        
        # Right panel - Phase content
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.phase_zero_content = PhaseContentArea("Phase Zero")
        self.phase_one_content = PhaseContentArea("Phase One")
        
        content_splitter.addWidget(self.phase_zero_content)
        content_splitter.addWidget(self.phase_one_content)
        splitter.addWidget(content_splitter)
        
        # Set stretch factors
        splitter.setStretchFactor(0, 1)  # Metrics panel
        splitter.setStretchFactor(1, 2)  # Content area
        
        layout.addWidget(splitter)

    def _handle_agent_selection(self, phase: str, agent_id: str) -> None:
        """Handle agent selection from timeline."""
        try:
            self.timeline.selected_agent = (phase, agent_id)
            # Use AsyncHelper for potentially long-running metric updates
            self.async_helper.run_coroutine(
                self._update_agent_metrics(agent_id),
                callback=self._handle_metrics_update
            )
        except Exception as e:
            self._handle_error(
                "Failed to handle agent selection",
                {'error': str(e), 'source': 'agent_selection_handler'}
            )

    async def _update_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Asynchronously update agent metrics."""
        # Use the orchestrator interface to get agent metrics
        return await self.orchestrator.get_agent_metrics(agent_id)

    def _handle_metrics_update(self, metrics: Dict[str, Any]) -> None:
        """Handle the result of async metrics update."""
        try:
            self.agent_metrics.update_display(metrics)
        except Exception as e:
            self._handle_error(
                "Failed to update metrics display",
                {'error': str(e), 'source': 'metrics_handler'}
            )
            
    def _handle_resource_error(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Handle resource error events.
        
        Args:
            event_type: Type of event that occurred
            data: Event data including error details
        """
        try:
            error_msg = data.get('error', event_type)
            error_source = data.get('source', 'system')
            
            # Log the error event
            logger.error(f"Resource error from {error_source}: {error_msg}", extra={
                'event_type': event_type,
                'error_data': data
            })
            
            # Update system status
            self.system_status.setText(f"System: Error in {error_source}")
            self.system_status.setStyleSheet("color: #D0021B")
            
            # Emit error signal with full context
            self.error_signal.emit(error_msg, {
                'source': error_source,
                'error': error_msg,
                'event_type': event_type,
                'timestamp': datetime.now().isoformat(),
                'traceback': data.get('traceback', traceback.format_stack())
            })
            
            # Force UI update
            QApplication.processEvents()
            
        except Exception as e:
            logger.critical(f"Failed to handle resource error: {e}", exc_info=True)
            # Ensure UI knows about the failure
            self._show_error_dialog(f"Critical error in resource handling: {e}")

    def _handle_error(self, error_msg: str, error_data: Dict[str, Any]) -> None:
        """
        Handle application errors.
        
        Args:
            error_msg: Primary error message
            error_data: Additional error context
        """
        try:
            # Remove potentially problematic check that might suppress errors
            detailed_error = self._format_error_message(error_msg, error_data)
            
            # Always log the full error context
            logger.error(detailed_error, extra={
                'error_data': error_data,
                'stack_trace': traceback.format_stack()
            })
            
            # Update UI to show error state
            self.system_status.setText("System: Error Detected")
            self.system_status.setStyleSheet("color: #D0021B")
            
            # Show error in metrics panel
            if hasattr(self, 'metrics_panel'):
                self.metrics_panel.alert_widget.add_alert(
                    AlertLevel.ERROR,
                    detailed_error
                )
            
            # Show dialog for user feedback
            self._show_error_dialog(detailed_error)
            
            # Attempt recovery
            # self._attempt_error_recovery(error_data)

        except Exception as handler_error:
            # If error handling itself fails, show critical error
            logger.critical(f"Error handler failed: {handler_error}", exc_info=True)
            QMessageBox.critical(
                self,
                "Critical Error",
                f"Error handling failed: {handler_error}\nOriginal error: {error_msg}"
            )

    def _format_error_message(self, error_msg: str, error_data: Dict[str, Any]) -> str:
        """Format error message with details."""
        detailed_error = f"Error: {error_msg}"
        if error_data and 'traceback' in error_data:
            detailed_error += f"\n\nTraceback:\n{error_data['traceback']}"
        return detailed_error

    def _show_error_dialog(self, message: str) -> None:
        """Display error dialog to user."""
        QMessageBox.critical(self, "Error", message)

    def _attempt_error_recovery(self, error_data: Dict[str, Any]) -> None:
        """Attempt to recover from error based on source."""
        if error_data and 'source' in error_data:
            recovery_actions = {
                'agent_state_handler': self._attempt_state_recovery,
                'metric_handler': self._attempt_metric_recovery
            }
            
            if action := recovery_actions.get(error_data['source']):
                action()

    def closeEvent(self, event):
        """Handle application shutdown with synchronous cleanup."""
        try:
            # Block the close event until cleanup completes
            event.ignore()  # Temporarily ignore to prevent Qt from proceeding
            
            # Stop all timers immediately
            self._cleanup_timers()
            
            # Create and run a blocking cleanup task
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._perform_full_cleanup())
            
            # Now accept the close event
            event.accept()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            event.accept()  # Still close even if cleanup fails

    async def _perform_full_cleanup(self):
        """Complete all async cleanup operations in the correct sequence."""
        # 1. Stop async helper first to prevent new tasks
        if hasattr(self, 'async_helper'):
            self.async_helper.stop_all()
            
        # 2. Cleanup subscriptions
        await self._cleanup_subscriptions()
        
        # 3. Stop system monitor and all its components
        if hasattr(self, 'system_monitor'):
            await self.system_monitor.stop()

    def _cleanup_timers(self) -> None:
        """Stop all running timers."""
        if hasattr(self, '_update_timer'):
            self._update_timer.stop()
        
        for chart in self.findChildren(MetricsChart):
            if hasattr(chart, '_batch_timer'):
                chart._batch_timer.stop()

    async def _cleanup_subscriptions(self) -> None:
        """Set up event subscriptions for the monitoring system."""
        subscriptions = [
            (ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value, self._handle_health_change),
            (ResourceEventTypes.RESOURCE_ALERT_CREATED.value, self._handle_resource_alert),
            (ResourceEventTypes.METRIC_RECORDED.value, self._handle_monitoring_status),
            (ResourceEventTypes.ERROR_OCCURRED.value, self._handle_system_error)
        ]
        
        # Subscribe to each event type
        for event_type, handler in subscriptions:
            await self.system_monitor.event_queue.unsubscribe(event_type, handler)
