"""
Memory monitoring panel.
"""
from typing import Optional

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QProgressBar, QTextEdit, QWidget

from resources.monitoring.memory import MemoryMonitor


class MemoryMonitorPanel(QFrame):
    """Panel to display memory monitoring information."""
    
    def __init__(self, memory_monitor: MemoryMonitor, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.memory_monitor = memory_monitor
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI components."""
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
        """Update the display with current memory information."""
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