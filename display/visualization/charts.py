"""
Chart components for data visualization.
"""
import logging
from typing import List, Tuple, Optional

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPainter
from PyQt6.QtCharts import QChartView, QLineSeries, QChart

from ..utils.data_processing import DataProcessor

logger = logging.getLogger(__name__)


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
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

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
            
        decimated_data = DataProcessor.decimate_data(data_points, self._decimation_threshold)
        series = QLineSeries()
        for x, y in decimated_data:
            series.append(x, y)
        self.chart().removeAllSeries()
        self.chart().addSeries(series)

    def cleanup(self) -> None:
        """Clean up chart resources."""
        if hasattr(self, '_batch_timer'):
            self._batch_timer.stop()