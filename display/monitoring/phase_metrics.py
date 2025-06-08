"""
Phase coordination metrics widget.
"""
import logging
from collections import deque
from datetime import datetime, timedelta
from typing import Optional

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget

from ..visualization.charts import MetricsChart

logger = logging.getLogger(__name__)


class PhaseMetricsWidget(QFrame):
    """Widget for displaying phase coordination metrics"""
    
    def __init__(self, metrics_manager, parent: Optional[QWidget] = None):
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
            await self.update_active_phases()
            await self.update_phase_states()
            await self.update_phase_types()
            await self.update_nested_executions()
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