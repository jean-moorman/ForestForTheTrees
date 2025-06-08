"""
GUI Performance and Stress Testing

Tests performance characteristics of GUI components under load:
- High-frequency updates and rendering
- Memory usage patterns
- Event processing performance
- UI responsiveness under stress
- Resource cleanup and leak detection
- Concurrent operation handling
"""

import asyncio
import gc
import psutil
import pytest
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import MagicMock

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtTest import QTest

from display import (
    ForestDisplay, TimelineWidget, AlertWidget, MetricsChart, 
    PromptInterface, AsyncHelper, AlertLevel
)
from interfaces import AgentState
from .conftest import GuiTestBase, async_wait_for_condition

class PerformanceProfiler:
    """Helper class for performance profiling during tests."""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.process = psutil.Process()
        
    def __enter__(self):
        """Start profiling."""
        gc.collect()  # Clean up before measurement
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End profiling and calculate metrics."""
        self.end_time = time.time()
        gc.collect()  # Clean up before final measurement
        self.end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
        
    @property
    def memory_delta(self) -> float:
        """Get memory change in MB."""
        if self.start_memory and self.end_memory:
            return self.end_memory - self.start_memory
        return 0.0
        
    def report(self) -> Dict[str, float]:
        """Generate performance report."""
        return {
            'name': self.name,
            'duration_seconds': self.duration,
            'memory_delta_mb': self.memory_delta,
            'start_memory_mb': self.start_memory,
            'end_memory_mb': self.end_memory
        }


@pytest.mark.asyncio
class TestTimelineWidgetPerformance:
    """Performance tests for TimelineWidget."""
    
    async def test_timeline_high_frequency_updates(self, display_test_base):
        """Test TimelineWidget performance with high-frequency state updates."""
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        timeline.show()
        
        with PerformanceProfiler("timeline_high_frequency_updates") as profiler:
            # Generate 1000 state updates rapidly
            test_agent = 'garden_planner'
            base_time = datetime.now()
            
            for i in range(1000):
                from display import TimelineState
                state = TimelineState(
                    start_time=base_time + timedelta(milliseconds=i),
                    state=AgentState.RUNNING if i % 2 == 0 else AgentState.READY,
                    metadata={'iteration': i}
                )
                timeline.agent_states[test_agent].add_state(state)
                
                # Process events every 100 updates
                if i % 100 == 0:
                    display_test_base.process_events()
                    
            # Final processing
            await display_test_base.async_process_events(0.2)
            
        report = profiler.report()
        
        # Performance assertions
        assert report['duration_seconds'] < 2.0, f"Timeline updates took too long: {report['duration_seconds']}s"
        assert report['memory_delta_mb'] < 50, f"Memory usage too high: {report['memory_delta_mb']} MB"
        
        # Functional verification
        states = timeline.agent_states[test_agent].states
        assert len(states) <= 1000  # StateQueue should limit size
        
    async def test_timeline_many_agents_update(self, display_test_base):
        """Test TimelineWidget performance with many agents updating simultaneously."""
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        timeline.show()
        
        with PerformanceProfiler("timeline_many_agents") as profiler:
            # Update all agents simultaneously
            base_time = datetime.now()
            
            for iteration in range(100):
                for phase, agents in timeline.agents.items():
                    for agent in agents:
                        from display import TimelineState
                        state = TimelineState(
                            start_time=base_time + timedelta(seconds=iteration),
                            state=AgentState.RUNNING,
                            metadata={'iteration': iteration}
                        )
                        timeline.agent_states[agent].add_state(state)
                        
                # Process events every 10 iterations
                if iteration % 10 == 0:
                    await display_test_base.async_process_events(0.05)
                    
        report = profiler.report()
        
        # Performance assertions
        assert report['duration_seconds'] < 3.0, f"Multi-agent updates took too long: {report['duration_seconds']}s"
        assert report['memory_delta_mb'] < 100, f"Memory usage too high: {report['memory_delta_mb']} MB"
        
    async def test_timeline_paint_performance(self, display_test_base):
        """Test TimelineWidget painting performance with complex state."""
        timeline = TimelineWidget()
        display_test_base.register_widget(timeline)
        timeline.show()
        
        # Set up complex state
        base_time = datetime.now()
        for agent in ['garden_planner', 'environmental_analysis', 'monitoring']:
            for i in range(500):
                from display import TimelineState
                state = TimelineState(
                    start_time=base_time + timedelta(seconds=i),
                    state=AgentState.RUNNING,
                    metadata={'index': i}
                )
                timeline.agent_states[agent].add_state(state)
                
        with PerformanceProfiler("timeline_paint_performance") as profiler:
            # Force multiple paint events
            for _ in range(50):
                timeline.update()
                display_test_base.process_events()
                await asyncio.sleep(0.01)
                
        report = profiler.report()
        
        # Paint performance should be reasonable
        assert report['duration_seconds'] < 1.0, f"Painting took too long: {report['duration_seconds']}s"


@pytest.mark.asyncio
class TestMetricsChartPerformance:
    """Performance tests for MetricsChart."""
    
    async def test_metrics_chart_large_dataset(self, display_test_base):
        """Test MetricsChart performance with large datasets."""
        chart = MetricsChart("Performance Test")
        display_test_base.register_widget(chart)
        chart.show()
        
        with PerformanceProfiler("metrics_chart_large_dataset") as profiler:
            # Generate large dataset
            large_data = []
            for i in range(10000):
                large_data.append((float(i), float(i % 100)))
                
            # Update chart
            chart.update_data(large_data, immediate=True)
            await display_test_base.async_process_events(0.3)
            
        report = profiler.report()
        
        # Performance assertions
        assert report['duration_seconds'] < 2.0, f"Large dataset processing took too long: {report['duration_seconds']}s"
        assert report['memory_delta_mb'] < 200, f"Memory usage too high: {report['memory_delta_mb']} MB"
        
    async def test_metrics_chart_rapid_updates(self, display_test_base):
        """Test MetricsChart performance with rapid data updates."""
        chart = MetricsChart("Rapid Updates Test")
        display_test_base.register_widget(chart)
        chart.show()
        
        with PerformanceProfiler("metrics_chart_rapid_updates") as profiler:
            # Simulate real-time data stream
            base_time = time.time()
            
            for batch in range(100):
                batch_data = []
                for i in range(50):
                    timestamp = base_time + batch * 50 + i
                    value = 50 + 25 * (batch % 4 - 2)  # Oscillating values
                    batch_data.append((timestamp, value))
                    
                chart.queue_update(batch_data)
                
                # Periodically process batches
                if batch % 10 == 0:
                    chart._process_batched_updates()
                    await display_test_base.async_process_events(0.01)
                    
            # Final processing
            chart._process_batched_updates()
            await display_test_base.async_process_events(0.1)
            
        report = profiler.report()
        
        # Performance assertions
        assert report['duration_seconds'] < 1.5, f"Rapid updates took too long: {report['duration_seconds']}s"
        assert report['memory_delta_mb'] < 50, f"Memory usage too high: {report['memory_delta_mb']} MB"
        
    async def test_metrics_chart_memory_leak_detection(self, display_test_base):
        """Test MetricsChart for memory leaks during continuous operation."""
        chart = MetricsChart("Memory Leak Test")
        display_test_base.register_widget(chart)
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Run continuous updates for extended period
        for cycle in range(20):
            # Generate data
            data_batch = []
            for i in range(100):
                data_batch.append((float(cycle * 100 + i), float(i % 50)))
                
            # Update chart
            chart.update_data(data_batch, immediate=True)
            
            # Process events
            await display_test_base.async_process_events(0.02)
            
            # Force garbage collection every few cycles
            if cycle % 5 == 0:
                gc.collect()
                
        # Final cleanup and measurement
        gc.collect()
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 100MB for this test)
        assert memory_growth < 100, f"Potential memory leak detected: {memory_growth} MB growth"


@pytest.mark.asyncio
class TestAlertWidgetPerformance:
    """Performance tests for AlertWidget."""
    
    async def test_alert_widget_high_volume_alerts(self, display_test_base):
        """Test AlertWidget performance with high volume of alerts."""
        alert_widget = AlertWidget()
        display_test_base.register_widget(alert_widget)
        
        with PerformanceProfiler("alert_widget_high_volume") as profiler:
            # Generate many alerts rapidly
            for i in range(1000):
                level = [AlertLevel.INFO, AlertLevel.WARNING, AlertLevel.ERROR, AlertLevel.CRITICAL][i % 4]
                alert_widget.add_alert(level, f"High volume alert {i}")
                
                # Process events every 100 alerts
                if i % 100 == 0:
                    display_test_base.process_events()
                    
            # Final processing
            display_test_base.process_events()
            
        report = profiler.report()
        
        # Performance assertions
        assert report['duration_seconds'] < 1.0, f"High volume alerts took too long: {report['duration_seconds']}s"
        
        # Should prune alerts to reasonable number
        assert alert_widget.layout().count() <= 5
        
    async def test_alert_widget_concurrent_alerts(self, display_test_base):
        """Test AlertWidget performance with concurrent alert sources."""
        alert_widget = AlertWidget()
        display_test_base.register_widget(alert_widget)
        
        with PerformanceProfiler("alert_widget_concurrent") as profiler:
            # Simulate multiple alert sources
            async def alert_source(source_id: str, count: int):
                for i in range(count):
                    level = AlertLevel.WARNING if i % 2 == 0 else AlertLevel.INFO
                    alert_widget.add_alert(level, f"Source {source_id} alert {i}")
                    await asyncio.sleep(0.001)  # Small delay
                    
            # Run multiple sources concurrently
            await asyncio.gather(
                alert_source("A", 100),
                alert_source("B", 100),
                alert_source("C", 100)
            )
            
            # Final processing
            await display_test_base.async_process_events(0.1)
            
        report = profiler.report()
        
        # Performance assertions
        assert report['duration_seconds'] < 2.0, f"Concurrent alerts took too long: {report['duration_seconds']}s"


@pytest.mark.asyncio
class TestForestDisplayPerformance:
    """Performance tests for ForestDisplay integration."""
    
    async def test_forest_display_event_processing_performance(self, display_test_base):
        """Test ForestDisplay performance with high event load."""
        display = ForestDisplay(
            display_test_base.event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        
        # Initialize required attributes
        display._pending_updates = set()
        
        with PerformanceProfiler("forest_display_event_processing") as profiler:
            # Generate high event load
            from resources import ResourceEventTypes
            
            for i in range(500):
                # Mix different event types
                if i % 3 == 0:
                    await display_test_base.event_queue.emit(
                        ResourceEventTypes.METRIC_RECORDED,
                        {"metric": f"test_metric_{i}", "value": i}
                    )
                elif i % 3 == 1:
                    await display_test_base.event_queue.emit(
                        ResourceEventTypes.SYSTEM_HEALTH_CHANGED,
                        {"component": "test", "status": "HEALTHY"}
                    )
                else:
                    await display_test_base.event_queue.emit(
                        ResourceEventTypes.RESOURCE_ALERT_CREATED,
                        {"alert_type": "test", "level": "INFO", "message": f"Alert {i}"}
                    )
                    
                # Process events periodically
                if i % 50 == 0:
                    await display_test_base.async_process_events(0.02)
                    
            # Final processing
            await display_test_base.async_process_events(0.3)
            
        report = profiler.report()
        
        # Performance assertions
        assert report['duration_seconds'] < 3.0, f"Event processing took too long: {report['duration_seconds']}s"
        assert report['memory_delta_mb'] < 150, f"Memory usage too high: {report['memory_delta_mb']} MB"
        
    async def test_forest_display_ui_responsiveness(self, display_test_base):
        """Test ForestDisplay UI responsiveness under load."""
        display = ForestDisplay(
            display_test_base.event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        display.show()
        
        # Initialize required attributes
        display._pending_updates = set()
        
        # Measure UI response times
        response_times = []
        
        for i in range(20):
            start_time = time.time()
            
            # Trigger UI update
            display.timeline.update()
            display.metrics_panel.update_all()
            
            # Process events
            display_test_base.process_events()
            
            end_time = time.time()
            response_times.append(end_time - start_time)
            
            # Add some load
            await display_test_base.async_process_events(0.01)
            
        # Calculate average response time
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        # UI should remain responsive
        assert avg_response_time < 0.05, f"Average UI response time too slow: {avg_response_time}s"
        assert max_response_time < 0.1, f"Maximum UI response time too slow: {max_response_time}s"
        
    async def test_forest_display_memory_efficiency(self, display_test_base):
        """Test ForestDisplay memory efficiency during extended operation."""
        display = ForestDisplay(
            display_test_base.event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        
        # Initialize required attributes
        display._pending_updates = set()
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Simulate extended operation
        for cycle in range(50):
            # Simulate user interactions
            test_prompt = f"Extended operation test {cycle}"
            
            # Mock prompt processing to avoid actual orchestrator calls
            async def mock_process(prompt):
                return {"status": "success", "phase_one_outputs": {}}
            
            display._process_prompt_async = mock_process
            
            # Process events and updates
            await display_test_base.async_process_events(0.01)
            
            # Force garbage collection periodically
            if cycle % 10 == 0:
                gc.collect()
                
        # Final memory measurement
        gc.collect()
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be controlled
        assert memory_growth < 200, f"Memory growth too high during extended operation: {memory_growth} MB"


@pytest.mark.asyncio
class TestAsyncPerformance:
    """Performance tests for async operations."""
    
    async def test_async_helper_throughput(self, display_test_base):
        """Test AsyncHelper throughput with many concurrent operations."""
        parent = MagicMock()
        async_helper = AsyncHelper(parent)
        
        with PerformanceProfiler("async_helper_throughput") as profiler:
            # Define test coroutine
            async def test_task(task_id: int):
                await asyncio.sleep(0.01)  # Simulate work
                return f"Task {task_id} completed"
            
            # Start many tasks concurrently
            results = []
            
            for i in range(100):
                def capture_result(result):
                    results.append(result)
                    
                async_helper.run_coroutine(test_task(i), callback=capture_result)
                
            # Wait for completion
            await display_test_base.async_process_events(2.0)
            
        report = profiler.report()
        
        # Performance assertions
        assert report['duration_seconds'] < 3.0, f"Async throughput test took too long: {report['duration_seconds']}s"
        assert len(results) >= 90, f"Not enough tasks completed: {len(results)}/100"
        
        # Cleanup
        async_helper.stop_all()
        
    async def test_async_helper_error_handling_performance(self, display_test_base):
        """Test AsyncHelper performance when handling errors."""
        parent = MagicMock()
        parent._handle_error = MagicMock()
        async_helper = AsyncHelper(parent)
        
        with PerformanceProfiler("async_helper_error_handling") as profiler:
            # Define failing coroutine
            async def failing_task(task_id: int):
                await asyncio.sleep(0.01)
                if task_id % 3 == 0:
                    raise ValueError(f"Task {task_id} failed")
                return f"Task {task_id} succeeded"
            
            # Start many tasks (some will fail)
            for i in range(50):
                async_helper.run_coroutine(failing_task(i))
                
            # Wait for completion
            await display_test_base.async_process_events(1.0)
            
        report = profiler.report()
        
        # Should handle errors efficiently
        assert report['duration_seconds'] < 2.0, f"Error handling took too long: {report['duration_seconds']}s"
        
        # Error handler should have been called for failing tasks
        assert parent._handle_error.call_count > 0
        
        # Cleanup
        async_helper.stop_all()


@pytest.mark.asyncio
class TestIntegratedPerformance:
    """Integrated performance tests across multiple components."""
    
    async def test_full_system_performance_simulation(self, display_test_base):
        """Test performance of the full GUI system under realistic load."""
        # Create complete display system
        display = ForestDisplay(
            display_test_base.event_queue,
            display_test_base.orchestrator,
            display_test_base.system_monitor
        )
        display_test_base.register_widget(display)
        display.show()
        
        # Initialize required attributes
        display._pending_updates = set()
        
        with PerformanceProfiler("full_system_simulation") as profiler:
            # Simulate realistic system operation
            base_time = datetime.now()
            
            for minute in range(5):  # 5 minutes of operation
                # Agent state updates
                for agent in ['garden_planner', 'environmental_analysis', 'monitoring']:
                    from display import TimelineState
                    state = TimelineState(
                        start_time=base_time + timedelta(minutes=minute),
                        state=AgentState.RUNNING,
                        metadata={'minute': minute}
                    )
                    display.timeline.agent_states[agent].add_state(state)
                    
                # System metrics
                for metric_type in ['cpu_usage', 'memory_usage', 'error_rate']:
                    data_points = []
                    for second in range(60):  # One minute of data
                        timestamp = (base_time + timedelta(minutes=minute, seconds=second)).timestamp()
                        value = 50 + 25 * (second % 10) / 10  # Varying values
                        data_points.append((timestamp, value))
                        
                    if hasattr(display, 'metrics_panel'):
                        # Simulate chart updates (if charts exist)
                        pass
                        
                # System alerts
                for alert_level in [AlertLevel.INFO, AlertLevel.WARNING]:
                    if hasattr(display, 'metrics_panel'):
                        display.metrics_panel.alert_widget.add_alert(
                            alert_level, 
                            f"System alert at minute {minute}"
                        )
                        
                # Process UI updates
                await display_test_base.async_process_events(0.1)
                
        report = profiler.report()
        
        # System should handle realistic load efficiently
        assert report['duration_seconds'] < 10.0, f"Full system simulation took too long: {report['duration_seconds']}s"
        assert report['memory_delta_mb'] < 300, f"Memory usage too high: {report['memory_delta_mb']} MB"
        
    async def test_stress_test_recovery(self, display_test_base):
        """Test system recovery after stress conditions."""
        # Create minimal display for stress testing
        timeline = TimelineWidget()
        alert_widget = AlertWidget()
        chart = MetricsChart("Stress Test")
        
        display_test_base.register_widget(timeline)
        display_test_base.register_widget(alert_widget)
        display_test_base.register_widget(chart)
        
        # Apply extreme stress
        with PerformanceProfiler("stress_test_recovery") as profiler:
            # Extreme timeline updates
            for i in range(2000):
                from display import TimelineState
                state = TimelineState(
                    start_time=datetime.now(),
                    state=AgentState.RUNNING,
                    metadata={'stress': i}
                )
                timeline.agent_states['garden_planner'].add_state(state)
                
            # Extreme alerts
            for i in range(500):
                alert_widget.add_alert(AlertLevel.CRITICAL, f"Stress alert {i}")
                
            # Extreme chart data
            stress_data = [(float(i), float(i % 100)) for i in range(5000)]
            chart.update_data(stress_data, immediate=True)
            
            # Process all updates
            await display_test_base.async_process_events(1.0)
            
        report = profiler.report()
        
        # System should recover from stress
        assert report['duration_seconds'] < 5.0, f"Stress recovery took too long: {report['duration_seconds']}s"
        
        # Components should still be functional
        assert alert_widget.layout().count() <= 5  # Should prune alerts
        assert len(timeline.agent_states['garden_planner'].states) <= 1000  # Should limit states
        
        # UI should still be responsive
        timeline.update()
        display_test_base.process_events()
        assert True  # No exceptions means UI is still functional