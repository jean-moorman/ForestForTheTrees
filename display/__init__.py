"""
Modular display system for Forest For The Trees (FFTT) monitoring interface.

This package provides a comprehensive Qt-based GUI for monitoring the FFTT system,
broken down into focused modules for better maintainability and extensibility.
"""

from .core.main_window import ForestDisplay
from .core.async_manager import AsyncWorker, AsyncHelper
from .visualization.alerts import AlertWidget, AlertLevel
from .visualization.charts import MetricsChart
from .visualization.timeline import TimelineWidget, TimelineState
from .content.prompt_interface import PromptInterface

# Support legacy import patterns
MainWindow = ForestDisplay  # Alias for legacy compatibility

__all__ = [
    'ForestDisplay',
    'MainWindow',  # Legacy compatibility 
    'AsyncWorker', 
    'AsyncHelper',
    'AlertWidget',
    'AlertLevel',
    'MetricsChart',
    'TimelineWidget',
    'TimelineState',
    'PromptInterface'
]