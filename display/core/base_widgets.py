"""
Base widget classes for common functionality.
"""
from PyQt6.QtWidgets import QWidget, QFrame
from PyQt6.QtCore import QTimer
from typing import List, Optional


class BaseWidget(QWidget):
    """Base widget class with common functionality."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._timers: List[QTimer] = []
        
    def create_timer(self, interval: int, callback) -> QTimer:
        """Create and track a QTimer."""
        timer = QTimer()
        timer.timeout.connect(callback)
        timer.start(interval)
        self._timers.append(timer)
        return timer
    
    def cleanup_timers(self) -> None:
        """Stop all timers in registry."""
        for timer in self._timers:
            timer.stop()
        self._timers.clear()
        
    def closeEvent(self, event):
        """Handle widget close event."""
        self.cleanup_timers()
        super().closeEvent(event)