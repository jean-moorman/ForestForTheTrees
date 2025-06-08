"""
GUI Testing Configuration and Fixtures

Provides shared fixtures and test utilities for GUI testing across the FFTT system.
"""

import asyncio
import logging
import sys
import time
import threading
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, AsyncGenerator
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
import qasync
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from PyQt6.QtTest import QTest
from PyQt6.QtGui import QMouseEvent, QKeyEvent

# Import system components for integration testing
from resources.events import EventQueue
from resources.state import StateManager
from resources.managers import AgentContextManager, CacheManager, MetricsManager
from resources.monitoring import SystemMonitor, MemoryMonitor, HealthTracker
from resources.errors import ErrorHandler
from interfaces import AgentState

logger = logging.getLogger(__name__)

# Global test timeout
GUI_TEST_TIMEOUT = 10.0

class MockOrchestrator:
    """Mock orchestrator for GUI testing that provides realistic responses."""
    
    def __init__(self):
        self.process_task_calls = []
        self.get_agent_metrics_calls = []
        self._task_responses = {}
        self._metrics_responses = {}
        
    async def process_task(self, prompt: str) -> Dict[str, Any]:
        """Mock task processing with realistic structure."""
        self.process_task_calls.append(prompt)
        
        # Return predefined response or generate realistic one
        if prompt in self._task_responses:
            return self._task_responses[prompt]
            
        return {
            "status": "success",
            "phase_one_outputs": {
                "garden_planner": {
                    "strategy": f"Strategic plan for: {prompt[:50]}...",
                    "components": ["component_1", "component_2", "component_3"],
                    "dependencies": []
                },
                "earth_agent": {
                    "validation_result": "passed",
                    "refinement_suggestions": []
                },
                "environmental_analysis": {
                    "analysis": "Environmental factors analyzed",
                    "recommendations": ["rec_1", "rec_2"]
                }
            },
            "structural_components": [
                {
                    "name": "Component 1",
                    "description": "First component description",
                    "dependencies": []
                },
                {
                    "name": "Component 2", 
                    "description": "Second component description",
                    "dependencies": ["Component 1"]
                }
            ],
            "system_requirements": {
                "task_analysis": {
                    "interpreted_goal": f"Goal: {prompt}",
                    "technical_requirements": {
                        "languages": ["Python"],
                        "frameworks": ["PyQt6", "asyncio"]
                    }
                }
            },
            "execution_time": 2.5,
            "message": "Task processed successfully"
        }
        
    async def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Mock agent metrics with realistic data."""
        self.get_agent_metrics_calls.append(agent_id)
        
        if agent_id in self._metrics_responses:
            return self._metrics_responses[agent_id]
            
        return {
            "status": "success",
            "agent_id": agent_id,
            "metrics": {
                "operations_count": 42,
                "success_rate": 0.95,
                "average_response_time": 1.2,
                "error_rate": 0.05,
                "last_activity": time.time()
            },
            "state": "READY",
            "health": "HEALTHY"
        }
        
    def set_task_response(self, prompt: str, response: Dict[str, Any]):
        """Set a specific response for a prompt."""
        self._task_responses[prompt] = response
        
    def set_metrics_response(self, agent_id: str, response: Dict[str, Any]):
        """Set a specific metrics response for an agent."""
        self._metrics_responses[agent_id] = response

class MockSystemMonitor:
    """Mock system monitor for GUI testing."""
    
    def __init__(self):
        self.memory_monitor = MagicMock()
        self.health_tracker = MagicMock()
        self._circuit_breakers = {}
        self._metrics = MagicMock()
        
        # Configure realistic return values
        self.memory_monitor._resource_sizes = {"agent_1": 10.5, "agent_2": 15.2}
        self.memory_monitor._thresholds = MagicMock()
        self.memory_monitor._thresholds.total_memory_mb = 1024
        self.memory_monitor._thresholds.warning_percent = 75
        self.memory_monitor._thresholds.critical_percent = 90
        
        self.health_tracker.get_system_health.return_value = MagicMock()
        self.health_tracker.get_system_health.return_value.status = "HEALTHY"
        
        self._metrics.get_error_density.return_value = 0.05
        self._metrics.get_avg_recovery_time.return_value = 2.3
        self._metrics.get_state_durations.return_value = {
            "CLOSED": 85.0, "OPEN": 10.0, "HALF_OPEN": 5.0
        }
        
        # Add mock event queue with async methods
        self.event_queue = AsyncMock()
        self.event_queue.subscribe = AsyncMock()
        self.event_queue.unsubscribe = AsyncMock()
        
        # Add mock async methods for start/stop
        self.memory_monitor.start = AsyncMock()
        self.start = AsyncMock()
        self.stop = AsyncMock()
        self.register_circuit_breaker = AsyncMock()

class TestSignalWaiter(QObject):
    """Helper class for waiting on Qt signals in tests."""
    
    signal_received = pyqtSignal()
    
    def __init__(self, signal, timeout=GUI_TEST_TIMEOUT):
        super().__init__()
        self.timeout = timeout
        self.result = None
        self.signal_args = None
        self.received = False
        
        # Connect to the signal we're waiting for
        signal.connect(self._on_signal)
        
    def _on_signal(self, *args):
        """Handle signal reception."""
        self.signal_args = args
        self.received = True
        self.signal_received.emit()
        
    async def wait(self):
        """Wait for the signal with timeout."""
        if self.received:
            return self.signal_args
            
        # Create an asyncio event
        event = asyncio.Event()
        self.signal_received.connect(lambda: event.set())
        
        try:
            await asyncio.wait_for(event.wait(), timeout=self.timeout)
            return self.signal_args
        except asyncio.TimeoutError:
            raise TimeoutError(f"Signal not received within {self.timeout} seconds")

@pytest.fixture(scope="session")
def qapp_fixture():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Set up application properties for testing
    app.setApplicationName("FFTT-Tests")
    app.setOrganizationName("FFTT-Testing")
    
    yield app
    
    # Clean up
    app.processEvents()

@pytest.fixture
def event_loop_fixture(qapp_fixture):
    """Create a qasync event loop for each test."""
    loop = qasync.QEventLoop(qapp_fixture)
    asyncio.set_event_loop(loop)
    
    yield loop
    
    # Clean up pending tasks
    try:
        pending_tasks = asyncio.all_tasks(loop)
        for task in pending_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for cancellation to complete
        if pending_tasks:
            loop.run_until_complete(
                asyncio.gather(*pending_tasks, return_exceptions=True)
            )
    except Exception as e:
        logger.warning(f"Error cleaning up tasks: {e}")
    
    # Process final events
    qapp_fixture.processEvents()

@pytest.fixture
async def event_queue_fixture(event_loop_fixture):
    """Create an event queue for testing."""
    queue = EventQueue(queue_id="gui_test_queue")
    await queue.start()
    
    yield queue
    
    try:
        await queue.stop()
    except Exception as e:
        logger.warning(f"Error stopping event queue: {e}")

@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator for GUI testing."""
    return MockOrchestrator()

@pytest.fixture 
def mock_system_monitor():
    """Create a mock system monitor for GUI testing."""
    return MockSystemMonitor()

@pytest.fixture
def display_test_base(qapp_fixture, event_loop_fixture, mock_orchestrator, mock_system_monitor):
    """
    Create a base testing environment with all required dependencies.
    
    This fixture provides:
    - QApplication instance
    - qasync event loop
    - Mock orchestrator and system monitor
    - Event queue for integration testing
    """
    
    class DisplayTestEnvironment:
        def __init__(self, app, loop, orchestrator, monitor):
            self.app = app
            self.loop = loop
            self.orchestrator = orchestrator
            self.system_monitor = monitor
            self.widgets = []
            self.timers = []
            # Create event queue synchronously
            self.event_queue = None
            
        def register_widget(self, widget: QWidget):
            """Register a widget for cleanup."""
            self.widgets.append(widget)
            return widget
            
        def register_timer(self, timer: QTimer):
            """Register a timer for cleanup."""
            self.timers.append(timer)
            return timer
            
        async def get_event_queue(self):
            """Get or create an event queue for testing."""
            if self.event_queue is None:
                self.event_queue = EventQueue(queue_id="gui_test_queue")
                await self.event_queue.start()
            return self.event_queue
            
        async def wait_for_signal(self, signal, timeout=GUI_TEST_TIMEOUT):
            """Wait for a Qt signal with timeout."""
            waiter = TestSignalWaiter(signal, timeout)
            return await waiter.wait()
            
        def process_events(self, iterations=10):
            """Process Qt events multiple times."""
            for _ in range(iterations):
                self.app.processEvents()
                
        async def async_process_events(self, duration=0.1):
            """Process events asynchronously for a duration."""
            end_time = time.time() + duration
            while time.time() < end_time:
                self.app.processEvents()
                await asyncio.sleep(0.01)
                
        def cleanup(self):
            """Clean up all registered resources."""
            # Stop timers
            for timer in self.timers:
                if timer.isActive():
                    timer.stop()
                    
            # Close widgets
            for widget in self.widgets:
                try:
                    if hasattr(widget, 'close'):
                        widget.close()
                    if hasattr(widget, 'deleteLater'):
                        widget.deleteLater()
                except Exception as e:
                    logger.warning(f"Error cleaning up widget: {e}")
                    
            # Clean up event queue if created
            if self.event_queue is not None:
                try:
                    # Schedule cleanup for later
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self.event_queue.stop())
                    else:
                        # If loop is not running, we can't clean up properly
                        pass
                except Exception as e:
                    logger.warning(f"Error stopping event queue: {e}")
                    
            # Process final events
            self.process_events()
            
            # Clear lists
            self.widgets.clear()
            self.timers.clear()
    
    env = DisplayTestEnvironment(
        qapp_fixture, 
        event_loop_fixture, 
        mock_orchestrator, 
        mock_system_monitor
    )
    
    yield env
    
    # Cleanup
    env.cleanup()

@pytest.fixture
def gui_test_timeout():
    """Standard timeout for GUI tests."""
    return GUI_TEST_TIMEOUT

class GuiTestBase:
    """Base class for GUI tests with common utilities."""
    
    @staticmethod
    def simulate_mouse_click(widget: QWidget, button=None, pos=None):
        """Simulate a mouse click on a widget."""
        from PyQt6.QtCore import Qt
        from PyQt6.QtTest import QTest
        
        if pos is None:
            pos = widget.rect().center()
        if button is None:
            button = Qt.MouseButton.LeftButton
            
        QTest.mouseClick(widget, button, Qt.KeyboardModifier.NoModifier, pos)
        
    @staticmethod
    def simulate_key_press(widget: QWidget, key, modifier=None):
        """Simulate a key press on a widget."""
        from PyQt6.QtCore import Qt
        from PyQt6.QtTest import QTest
        
        if modifier is None:
            modifier = Qt.KeyboardModifier.NoModifier
            
        QTest.keyPress(widget, key, modifier)
        
    @staticmethod
    def simulate_text_input(widget: QWidget, text: str):
        """Simulate text input into a widget."""
        from PyQt6.QtTest import QTest
        
        # Clear existing text
        widget.clear() if hasattr(widget, 'clear') else None
        
        # Type the text
        QTest.keyClicks(widget, text)

# Utility functions for GUI testing
def wait_for_widget_update(widget: QWidget, timeout: float = 1.0):
    """Wait for widget updates to complete."""
    app = QApplication.instance()
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        app.processEvents()
        time.sleep(0.01)

async def async_wait_for_condition(condition_func, timeout: float = 5.0, interval: float = 0.1):
    """Wait for a condition to become true."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        await asyncio.sleep(interval)
        
    return False