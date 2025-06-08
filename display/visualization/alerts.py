"""
Alert system for the display interface.
"""
from enum import Enum, auto
from typing import List, Tuple, Optional

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QTextEdit, QWidget
from PyQt6.QtCore import Qt


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


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