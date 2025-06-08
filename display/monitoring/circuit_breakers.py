"""
Circuit breaker monitoring panel.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QProgressBar, 
    QScrollArea, QWidget
)
from PyQt6.QtCore import Qt

from resources.monitoring import SystemMonitor, CircuitBreaker
from ..visualization.alerts import AlertWidget, AlertLevel
from ..utils.data_processing import DataProcessor

logger = logging.getLogger(__name__)


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
        
        # Create progress bars for each state
        for state_name, color in [("CLOSED", "#7ED321"), ("OPEN", "#D0021B"), ("HALF_OPEN", "#F5A623")]:
            state_layout = QHBoxLayout()
            state_layout.addWidget(QLabel(state_name))
            
            progress_bar = QProgressBar()
            progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #374151;
                    border-radius: 2px;
                    text-align: center;
                    background-color: #111827;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 2px;
                }}
            """)
            state_layout.addWidget(progress_bar)
            state_bars_layout.addLayout(state_layout)
            
            # Store reference to progress bar
            setattr(widget, f"{state_name.lower()}_bar", progress_bar)
        
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
        time_str = DataProcessor.format_time_duration(time_in_state)
        widget.time_in_state.setText(time_str)
        
        # Update state duration bars
        total_time = 0
        state_durations = metrics.get_state_durations(name)
        for state_name in ["CLOSED", "OPEN", "HALF_OPEN"]:
            total_time += state_durations.get(state_name, 0)
        
        # Set bar values (as percentages of total time)
        if total_time > 0:
            for state_name in ["CLOSED", "OPEN", "HALF_OPEN"]:
                bar = getattr(widget, f"{state_name.lower()}_bar")
                duration = state_durations.get(state_name, 0)
                percentage = int(duration / total_time * 100)
                bar.setValue(percentage)
                bar.setFormat(f"{duration:.1f}s ({percentage}%)")
        else:
            for state_name in ["CLOSED", "OPEN", "HALF_OPEN"]:
                bar = getattr(widget, f"{state_name.lower()}_bar")
                bar.setValue(0)
                bar.setFormat("0.0s (0%)")
        
        # Last failure info
        if breaker.last_failure_time:
            time_ago = (datetime.now() - breaker.last_failure_time).total_seconds()
            time_str = DataProcessor.format_time_duration(time_ago)
            widget.last_failure.setText(f"{time_str} ago")
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