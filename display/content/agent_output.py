"""
Agent output display widget.
"""
import logging
from typing import Dict, Optional

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QProgressBar, QWidget

from interfaces import AgentState
from ..visualization.alerts import AlertWidget
from ..visualization.timeline import TimelineWidget

logger = logging.getLogger(__name__)


class AgentOutputWidget(QFrame):
    """Widget for displaying agent output and status."""
    
    def __init__(self, agent_id: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.agent_id = agent_id
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QVBoxLayout()
        
        # Alert widget
        self.alert_widget = AlertWidget()
        layout.addWidget(self.alert_widget)

        # Header
        header = QLabel(self.agent_id.replace('_', ' ').title())
        agent_color = TimelineWidget.agent_colors.get(self.agent_id, '#808080')
        header.setStyleSheet(f"font-weight: bold; color: {agent_color}")
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

    def update_output(self, output: Dict, state: AgentState) -> None:
        """Update the widget with new output and state."""
        self.status.setText(f"Status: {state.name}")
        
        if isinstance(output, dict):
            content = ""
            for key, value in output.items():
                content += f"{key}: {value}\n"
            self.content.setText(content)

    def update_validation_status(self, validation_data: Dict) -> None:
        """Update validation status display."""
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
            
        # Create validation status label if it doesn't exist
        if not hasattr(self, 'validation_status'):
            self.validation_status = QLabel()
            self.layout().addWidget(self.validation_status)
            
        self.validation_status.setText(status_text)
        self.validation_status.setStyleSheet(f"color: {color}")
        
    def mark_complete(self) -> None:
        """Mark the agent as complete."""
        self.status.setText("Status: COMPLETED")
        self.status.setStyleSheet("color: #7ED321")
        
    def show_progress(self) -> None:
        """Show progress indicator."""
        self.progress.setVisible(True)
        self.progress.setValue(50)  # Indeterminate progress