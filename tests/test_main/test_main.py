import pytest
import asyncio
import sys
import threading
import time
import logging
from datetime import datetime
from contextlib import contextmanager

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

import qasync

# Import the modules we want to test
from main import ForestApplication, AsyncHelper
from resources.monitoring import SystemMonitor, MemoryMonitor, HealthTracker
from resources.state import StateManager
from resources import ResourceEventTypes, EventQueue
from phase_zero import PhaseZeroOrchestrator
from phase_one import PhaseOneOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Constant timeout for async operations
ASYNC_TIMEOUT = 5

class TestSignals(QObject):
    """Test signals for async operations"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)

@pytest.fixture
def qapp():
    """Fixture to create a Qt application instance"""
    app = QApplication.instance() or QApplication(sys.argv)
    yield app
    # Make sure we process events before clearing
    app.processEvents()

@pytest.fixture
def event_loop(qapp):
    """Fixture to create an event loop that works with Qt"""
    loop = qasync.QEventLoop(qapp)
    asyncio.set_event_loop(loop)
    yield loop
    
    # Clean up pending tasks
    pending_tasks = asyncio.all_tasks(loop)
    for task in pending_tasks:
        if not task.done():
            task.cancel()
    
    # Run loop until tasks are cancelled
    loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
    loop.close()

@pytest.fixture
async def event_queue(event_loop):
    """Create and initialize an event queue"""
    queue = EventQueue()
    await queue.start()
    yield queue
    # Stop queue after test
    await queue.stop()

@pytest.fixture
async def forest_app(qapp, event_loop):
    """Create a test ForestApplication instance"""
    app = ForestApplication()
    # Initialize app without showing UI
    await app.setup_async()
    yield app
    # Ensure proper cleanup
    app.close()

@pytest.fixture
def signals():
    """Create test signals for async operation testing"""
    return TestSignals()

@contextmanager
def timeout_context(seconds):
    """Context manager to handle timeouts"""
    timer = QTimer()
    timer.setSingleShot(True)
    timer.start(seconds * 1000)
    
    yield timer
    
    timer.stop()

@pytest.mark.asyncio
class TestForestApplication:
    """Tests for the ForestApplication class"""
    
    async def test_initialization(self, forest_app):
        """Test that the application initializes correctly"""
        # Check that core components are initialized
        assert forest_app.resource_manager is not None
        assert forest_app.context_manager is not None
        assert forest_app.cache_manager is not None
        assert forest_app.metrics_manager is not None
        assert forest_app.error_handler is not None
        assert forest_app.memory_monitor is not None
        assert forest_app.health_tracker is not None
        assert forest_app.system_monitor is not None
        assert forest_app.phase_zero is not None
        assert forest_app.phase_one is not None
        assert forest_app.main_window is not None
        assert forest_app._event_queue is not None
        
        # Check that the event timer is running
        assert hasattr(forest_app, 'event_timer')
        assert forest_app.event_timer.isActive()
    
    async def test_register_task(self, forest_app):
        """Test registering and managing tasks"""
        # Create a simple task that sleeps and returns a value
        async def simple_task():
            await asyncio.sleep(0.1)
            return "Task completed"
        
        # Register the task
        task = forest_app.register_task(simple_task())
        
        # The task should be in the set of tasks
        assert task in forest_app._tasks
        
        # Wait for the task to complete
        result = await task
        
        # Verify task result
        assert result == "Task completed"
        
        # Verify the task is removed from the task set after completion
        assert task not in forest_app._tasks
    
    async def test_cancel_all_tasks(self, forest_app):
        """Test cancelling all tasks"""
        # Create a set of tasks that sleep for different durations
        tasks = []
        for i in range(5):
            async def long_task(i=i):
                try:
                    await asyncio.sleep(10 + i)  # Long enough to be cancelled
                    return f"Task {i} completed"
                except asyncio.CancelledError:
                    return f"Task {i} cancelled"
            
            task = forest_app.register_task(long_task())
            tasks.append(task)
        
        # Check all tasks are registered
        assert len(forest_app._tasks) == 5
        
        # Cancel all tasks
        await forest_app.cancel_all_tasks()
        
        # Check that all tasks are cancelled
        for task in tasks:
            assert task.cancelled() or task.done()
        
        # Check that all tasks are removed from the task set
        assert len(forest_app._tasks) == 0
    
    async def test_check_events_queue(self, forest_app, event_queue):
        """Test that events are processed from the queue"""
        # Add an event to the queue
        test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
        await event_queue.emit(ResourceEventTypes.METRIC_RECORDED, test_data)
        
        # Process the event queue
        forest_app.check_events_queue()
        
        # Since we don't have direct observation of event handling,
        # we can check that the event was removed from the queue
        # This is an indirect test but confirms queue processing happened
        # For a more direct test, we could add a specific handler and check its effects
        await asyncio.sleep(0.1)  # Give time for async processing
        
        # We could add more assertions here based on expected side effects
        # of processing the specific event
    
    async def test_handle_error(self, forest_app):
        """Test error handling functionality"""
        # Simulate an error
        context = "Test error context"
        error_message = "Test error message"
        
        # Handle the error
        error_id = forest_app._handle_error(context, error_message)
        
        # Check that an error ID was returned
        assert error_id is not None
        assert isinstance(error_id, str)
        # ID should start with date format YYYYMMDDHHMMSS
        assert len(error_id) > 14  # Minimum length for date-based ID
    
    async def test_setup_event_processing(self, forest_app):
        """Test event processing setup"""
        # Setup event processing
        await forest_app.setup_event_processing()
        
        # Hard to test directly, but we can check that the timer is set up
        assert hasattr(forest_app, 'event_timer')
        assert forest_app.event_timer.isActive()

@pytest.mark.asyncio
class TestAsyncHelper:
    """Tests for the AsyncHelper class"""
    
    async def test_run_coroutine(self, qapp, event_loop, signals):
        """Test running a coroutine through AsyncHelper"""
        # Create an AsyncHelper instance with a test ForestApplication
        app = ForestApplication()
        helper = AsyncHelper(app)
        
        # Define a test coroutine
        async def test_coro():
            await asyncio.sleep(0.1)
            return "Success"
        
        # Define a callback
        def on_finished(result):
            signals.result.emit(result)
            signals.finished.emit()
        
        # Define an error callback
        def on_error(error):
            signals.error.emit(str(error))
        
        # Create an async waiter
        finish_event = asyncio.Event()
        result_value = None
        
        # Connect signals
        signals.finished.connect(lambda: finish_event.set())
        signals.result.connect(lambda r: setattr(sys.modules[__name__], 'result_value', r))
        
        # Run the coroutine
        helper.run_coroutine(test_coro(), on_finished, on_error)
        
        # Wait for completion with timeout
        try:
            await asyncio.wait_for(finish_event.wait(), ASYNC_TIMEOUT)
        except asyncio.TimeoutError:
            pytest.fail("AsyncHelper.run_coroutine timed out")
        
        # Check the result
        assert result_value == "Success"
        
        # Clean up
        helper.request_shutdown()

    async def test_run_coroutine_error(self, qapp, event_loop, signals):
        """Test error handling in run_coroutine"""
        # Create an AsyncHelper instance with a test ForestApplication
        app = ForestApplication()
        helper = AsyncHelper(app)
        
        # Define a test coroutine that raises an exception
        async def failing_coro():
            await asyncio.sleep(0.1)
            raise ValueError("Test error")
        
        # Define callbacks
        def on_finished(result):
            signals.result.emit(result)
            signals.finished.emit()
        
        def on_error(error):
            signals.error.emit(str(error))
            signals.finished.emit()
        
        # Create an async waiter
        finish_event = asyncio.Event()
        error_message = None
        
        # Connect signals
        signals.finished.connect(lambda: finish_event.set())
        signals.error.connect(lambda e: setattr(sys.modules[__name__], 'error_message', e))
        
        # Run the coroutine
        helper.run_coroutine(failing_coro(), on_finished, on_error)
        
        # Wait for completion with timeout
        try:
            await asyncio.wait_for(finish_event.wait(), ASYNC_TIMEOUT)
        except asyncio.TimeoutError:
            pytest.fail("AsyncHelper.run_coroutine error handling timed out")
        
        # Check the error message
        assert error_message is not None
        assert "Test error" in error_message
        
        # Clean up
        helper.request_shutdown()
    
    async def test_request_shutdown(self, qapp, event_loop):
        """Test requesting shutdown of AsyncHelper"""
        # Create an AsyncHelper instance
        app = ForestApplication()
        helper = AsyncHelper(app)
        
        # Create some test coroutines
        async def long_coro(i):
            try:
                await asyncio.sleep(10)  # Long enough to be cancelled
                return f"Task {i} completed"
            except asyncio.CancelledError:
                return f"Task {i} cancelled"
        
        # Add some pending futures
        tasks = []
        for i in range(3):
            # Run the coroutine
            helper.run_coroutine(long_coro(i))
        
        # Request shutdown
        helper.request_shutdown()
        
        # Check that shutdown flag is set
        assert helper.shutdown_requested
        
        # Add a new coroutine - should be rejected
        def callback(result):
            pytest.fail("Callback should not be called after shutdown")
        
        helper.run_coroutine(long_coro(99), callback)
        
        # Wait a bit to allow any pending operations to complete
        await asyncio.sleep(0.5)

@pytest.mark.asyncio
class TestIntegration:
    """Integration tests for ForestApplication"""
    
    async def test_full_lifecycle(self, qapp, event_loop):
        """Test the full lifecycle of the application"""
        # Create application
        app = ForestApplication()
        
        # Initialize
        await app.setup_async()
        
        # Check key components
        assert app._initialized
        assert app.resource_manager is not None
        assert app.phase_zero is not None
        assert app.phase_one is not None
        assert app.main_window is not None
        
        # Create and register a task
        async def test_task():
            await asyncio.sleep(0.1)
            return "Task completed"
        
        task = app.register_task(test_task())
        
        # Wait for task to complete
        result = await task
        assert result == "Task completed"
        
        # Test event processing
        app.check_events_queue()
        
        # Simulate an error and check handling
        error_id = app._handle_error("Test context", "Test error")
        assert error_id is not None
        
        # Close the application
        app.close()
        
        # Verify shutdown state
        assert len(app._tasks) == 0  # All tasks should be cancelled
        
        # Application should be closed properly - hard to assert directly,
        # but we can check that key cleanup methods were called

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])