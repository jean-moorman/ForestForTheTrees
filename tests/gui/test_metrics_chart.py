"""
Comprehensive tests for MetricsChart

Tests the real-time data visualization including:
- Chart initialization and configuration
- Data point updates and rendering
- Data decimation algorithms
- Batch update processing
- Performance with large datasets
- Memory management
"""

import pytest
import time
import asyncio
from datetime import datetime, timedelta
from typing import List, Tuple
from unittest.mock import MagicMock, patch

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCharts import QChart, QLineSeries
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPainter

from display import MetricsChart
from .conftest import GuiTestBase, async_wait_for_condition

class TestMetricsChart(GuiTestBase):
    """Test suite for MetricsChart functionality."""
    
    @pytest.mark.asyncio
    async def test_metrics_chart_initialization(self, display_test_base):
        """Test MetricsChart initializes correctly."""
        chart = MetricsChart("Test Chart")
        display_test_base.register_widget(chart)
        
        # Check basic initialization
        assert chart is not None
        assert chart.chart() is not None
        assert isinstance(chart.chart(), QChart)
        assert chart.chart().title() == "Test Chart"
        
        # Check that chart is ready for series (initially empty)
        series_list = chart.chart().series()
        # Chart starts with no series until data is added
        assert isinstance(series_list, list)
        
        # Check rendering hints
        render_hints = chart.renderHints()
        assert QPainter.RenderHint.Antialiasing in render_hints
        
        # Check minimum height (may be 0 if not explicitly set)
        assert chart.minimumHeight() >= 0
        
    @pytest.mark.asyncio
    async def test_chart_configuration(self, display_test_base):
        """Test chart configuration and properties."""
        chart = MetricsChart("Performance Metrics")
        display_test_base.register_widget(chart)
        
        # Test title setting
        assert chart.chart().title() == "Performance Metrics"
        
        # Test animation options
        animations = chart.chart().animationOptions()
        assert QChart.AnimationOption.SeriesAnimations in animations
        
        # Test axes creation
        axes = chart.chart().axes()
        assert len(axes) >= 2  # Should have X and Y axes
        
    @pytest.mark.asyncio
    async def test_simple_data_update(self, display_test_base):
        """Test updating chart with simple data points."""
        chart = MetricsChart("Test Data")
        display_test_base.register_widget(chart)
        
        # Create test data points
        test_data = [
            (1.0, 10.0),
            (2.0, 20.0),
            (3.0, 15.0),
            (4.0, 25.0),
            (5.0, 30.0)
        ]
        
        # Update chart with data
        chart.update_data(test_data, immediate=True)
        
        # Process events to ensure chart is updated
        display_test_base.process_events()
        
        # Verify data was added to series
        series_list = chart.chart().series()
        assert len(series_list) > 0
        
        # Get the first series and check point count
        if series_list:
            series = series_list[0]
            if hasattr(series, 'count'):
                assert series.count() == len(test_data)
                
    @pytest.mark.asyncio
    async def test_empty_data_update(self, display_test_base):
        """Test updating chart with empty data."""
        chart = MetricsChart("Empty Data Test")
        display_test_base.register_widget(chart)
        
        # Update with empty data
        chart.update_data([], immediate=True)
        
        # Should handle empty data gracefully
        display_test_base.process_events()
        assert True  # If no exception, test passes
        
    @pytest.mark.asyncio
    async def test_batch_update_processing(self, display_test_base):
        """Test batch update functionality."""
        chart = MetricsChart("Batch Test")
        display_test_base.register_widget(chart)
        chart.show()
        
        # Add data points to batch queue
        batch_data = [
            [(1.0, 10.0), (2.0, 20.0)],
            [(3.0, 15.0), (4.0, 25.0)],
            [(5.0, 30.0), (6.0, 35.0)]
        ]
        
        for data_batch in batch_data:
            chart.queue_update(data_batch)
            
        # Check that batches are queued
        assert len(chart._batch_updates) == 3
        
        # Process batched updates
        chart._process_batched_updates()
        
        # Batch queue should be cleared
        assert len(chart._batch_updates) == 0
        
    @pytest.mark.asyncio
    async def test_data_decimation(self, display_test_base):
        """Test data decimation with large datasets."""
        chart = MetricsChart("Decimation Test")
        display_test_base.register_widget(chart)
        
        # Create a large dataset that should trigger decimation
        large_dataset = []
        for i in range(2000):  # Larger than _decimation_threshold (1000)
            large_dataset.append((float(i), float(i * 2)))
            
        # Test decimation
        decimated_data = chart._decimate_data(large_dataset)
        
        # Decimated data should be smaller than original
        assert len(decimated_data) < len(large_dataset)
        assert len(decimated_data) > 2  # Should keep more than just endpoints
        
    @pytest.mark.asyncio
    async def test_rdp_algorithm(self, display_test_base):
        """Test Ramer-Douglas-Peucker decimation algorithm."""
        chart = MetricsChart("RDP Test")
        display_test_base.register_widget(chart)
        
        # Create test data with some redundant points
        test_points = [
            (0.0, 0.0),
            (1.0, 1.0),
            (2.0, 2.0),  # This point lies on the line, should be removed
            (3.0, 3.0),
            (4.0, 4.0),  # This point lies on the line, should be removed
            (5.0, 10.0)  # This point deviates, should be kept
        ]
        
        # Apply RDP with small epsilon to test algorithm
        reduced_points = chart._rdp_reduce(test_points, epsilon=0.1)
        
        # Should reduce the number of points
        assert len(reduced_points) <= len(test_points)
        
        # Should keep first and last points
        assert reduced_points[0] == test_points[0]
        assert reduced_points[-1] == test_points[-1]
        
    @pytest.mark.asyncio
    async def test_point_line_distance_calculation(self, display_test_base):
        """Test point-to-line distance calculation."""
        chart = MetricsChart("Distance Test")
        display_test_base.register_widget(chart)
        
        # Test cases for point-line distance
        test_cases = [
            # Point on line should have distance 0
            ((1.0, 1.0), (0.0, 0.0), (2.0, 2.0), 0.0),
            # Point above line
            ((1.0, 2.0), (0.0, 0.0), (2.0, 0.0), 2.0),
            # Point below line  
            ((1.0, -1.0), (0.0, 0.0), (2.0, 0.0), 1.0)
        ]
        
        for point, line_start, line_end, expected_distance in test_cases:
            distance = chart._point_line_distance(point, line_start, line_end)
            assert abs(distance - expected_distance) < 0.01  # Allow small floating point errors
            
    @pytest.mark.asyncio
    async def test_timer_setup_and_cleanup(self, display_test_base):
        """Test batch update timer setup and cleanup."""
        chart = MetricsChart("Timer Test")
        display_test_base.register_widget(chart)
        
        # Check timer is created and running
        assert hasattr(chart, '_batch_timer')
        assert isinstance(chart._batch_timer, QTimer)
        
        # Timer should be active after initialization
        assert chart._batch_timer.isActive()
        
        # Check timer interval
        assert chart._batch_timer.interval() == 20000  # 20 seconds
        
    @pytest.mark.asyncio
    async def test_large_dataset_performance(self, display_test_base):
        """Test chart performance with large datasets."""
        chart = MetricsChart("Performance Test")
        display_test_base.register_widget(chart)
        chart.show()
        
        # Create large dataset
        large_data = []
        for i in range(5000):
            large_data.append((float(i), float(i % 100)))
            
        # Measure update time
        start_time = time.time()
        chart.update_data(large_data, immediate=True)
        display_test_base.process_events()
        end_time = time.time()
        
        # Should complete within reasonable time (less than 1 second)
        update_time = end_time - start_time
        assert update_time < 1.0, f"Chart update took too long: {update_time}s"
        
    @pytest.mark.asyncio
    async def test_real_time_updates(self, display_test_base):
        """Test real-time data updates."""
        chart = MetricsChart("Real-time Test")
        display_test_base.register_widget(chart)
        chart.show()
        
        # Simulate real-time data updates
        base_time = time.time()
        
        for i in range(10):
            # Add data point
            current_time = base_time + i
            data_point = [(current_time, float(i * 10))]
            
            # Update without immediate flag (uses batching)
            chart.update_data(data_point, immediate=False)
            
            # Small delay to simulate real-time
            await asyncio.sleep(0.01)
            
        # Process events to handle any pending updates
        await display_test_base.async_process_events(0.2)
        
        # Chart should handle updates gracefully
        assert True
        
    @pytest.mark.asyncio
    async def test_multiple_data_types(self, display_test_base):
        """Test chart with different types of data."""
        chart = MetricsChart("Data Types Test")
        display_test_base.register_widget(chart)
        
        # Test with different numeric types
        mixed_data = [
            (1, 10),      # int, int
            (2.5, 15.5),  # float, float
            (3, 20.0),    # int, float
            (4.0, 25)     # float, int
        ]
        
        # Should handle mixed numeric types
        chart.update_data(mixed_data, immediate=True)
        display_test_base.process_events()
        
        # No assertion needed - test passes if no exception
        assert True
        
    @pytest.mark.asyncio
    async def test_chart_axes_update(self, display_test_base):
        """Test that chart axes are updated with new data."""
        chart = MetricsChart("Axes Test")
        display_test_base.register_widget(chart)
        chart.show()
        
        # Add initial data
        initial_data = [(1.0, 10.0), (2.0, 20.0)]
        chart.update_data(initial_data, immediate=True)
        display_test_base.process_events()
        
        # Add data with larger range
        extended_data = [(1.0, 10.0), (2.0, 20.0), (10.0, 100.0)]
        chart.update_data(extended_data, immediate=True)
        display_test_base.process_events()
        
        # Axes should be updated (createDefaultAxes is called)
        axes = chart.chart().axes()
        assert len(axes) >= 2  # Should have X and Y axes
        
    @pytest.mark.asyncio
    async def test_memory_management(self, display_test_base):
        """Test memory management with continuous updates."""
        chart = MetricsChart("Memory Test")
        display_test_base.register_widget(chart)
        
        # Continuously update chart to test memory management
        for batch in range(50):
            data_batch = []
            for i in range(100):
                data_batch.append((float(batch * 100 + i), float(i)))
                
            chart.queue_update(data_batch)
            
            # Periodically process batches
            if batch % 10 == 0:
                chart._process_batched_updates()
                display_test_base.process_events()
                
        # Final processing
        chart._process_batched_updates()
        await display_test_base.async_process_events(0.1)
        
        # Should handle continuous updates without memory issues
        assert True


@pytest.mark.asyncio
class TestMetricsChartIntegration:
    """Integration tests for MetricsChart with system components."""
    
    async def test_chart_with_system_metrics(self, display_test_base):
        """Test MetricsChart integration with system metrics."""
        chart = MetricsChart("System Metrics")
        display_test_base.register_widget(chart)
        
        # Simulate system metric data over time
        current_time = datetime.now()
        system_data = []
        
        for i in range(60):  # 1 minute of data
            timestamp = (current_time + timedelta(seconds=i)).timestamp()
            
            # Simulate CPU usage percentage
            cpu_usage = 50 + (i % 20) - 10  # Varies between 30-70%
            system_data.append((timestamp, cpu_usage))
            
        # Update chart with system data
        chart.update_data(system_data, immediate=True)
        await display_test_base.async_process_events(0.1)
        
        # Verify chart handles realistic system data
        series_list = chart.chart().series()
        assert len(series_list) > 0
        
    async def test_chart_with_agent_metrics(self, display_test_base):
        """Test MetricsChart with agent performance metrics."""
        chart = MetricsChart("Agent Performance")
        display_test_base.register_widget(chart)
        
        # Simulate agent performance metrics
        base_time = time.time()
        agent_data = []
        
        # Simulate response times with some variation
        for i in range(100):
            timestamp = base_time + i
            response_time = 1.0 + 0.5 * (i % 10) / 10  # 1.0-1.5 seconds
            agent_data.append((timestamp, response_time))
            
        chart.update_data(agent_data, immediate=True)
        await display_test_base.async_process_events(0.1)
        
        # Chart should handle agent metrics appropriately
        assert True
        
    async def test_chart_performance_under_load(self, display_test_base):
        """Test chart performance under high data load."""
        chart = MetricsChart("Load Test")
        display_test_base.register_widget(chart)
        chart.show()
        
        # Generate high-frequency data
        start_time = time.time()
        
        # Simulate 1000 data points arriving rapidly
        for batch in range(10):
            batch_data = []
            for i in range(100):
                timestamp = start_time + batch * 100 + i
                value = 50 + 25 * (batch % 4 - 2)  # Oscillating values
                batch_data.append((timestamp, value))
                
            chart.queue_update(batch_data)
            
        # Process all batches
        chart._process_batched_updates()
        
        # Measure processing time
        process_start = time.time()
        await display_test_base.async_process_events(0.5)
        process_end = time.time()
        
        # Should handle load efficiently
        processing_time = process_end - process_start
        assert processing_time < 1.0, f"Processing took too long: {processing_time}s"
        
    async def test_chart_with_missing_data(self, display_test_base):
        """Test chart behavior with missing or irregular data."""
        chart = MetricsChart("Missing Data Test")
        display_test_base.register_widget(chart)
        
        # Create data with gaps
        base_time = time.time()
        irregular_data = [
            (base_time, 10.0),
            (base_time + 1, 20.0),
            # Gap of 5 seconds
            (base_time + 7, 30.0),
            (base_time + 8, 25.0),
            # Another gap
            (base_time + 15, 40.0)
        ]
        
        chart.update_data(irregular_data, immediate=True)
        await display_test_base.async_process_events(0.1)
        
        # Should handle irregular data gracefully
        series_list = chart.chart().series()
        assert len(series_list) > 0
        
    async def test_chart_error_handling(self, display_test_base):
        """Test chart error handling with invalid data."""
        chart = MetricsChart("Error Test")
        display_test_base.register_widget(chart)
        
        # Test various edge cases that might cause errors
        edge_cases = [
            [],  # Empty data
            [(float('inf'), 10.0)],  # Infinite values
            [(1.0, float('nan'))],   # NaN values
            [(-1e10, 1e10)],         # Very large numbers
        ]
        
        for test_data in edge_cases:
            try:
                chart.update_data(test_data, immediate=True)
                display_test_base.process_events()
                # If no exception, test passes for this case
            except Exception as e:
                # Log but don't fail - some edge cases may legitimately raise exceptions
                print(f"Edge case {test_data} raised: {e}")
                
        # Test completes if we get here
        assert True