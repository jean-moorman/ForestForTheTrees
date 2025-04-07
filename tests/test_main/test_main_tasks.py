import pytest
import asyncio
import sys
import time
import threading
import logging
from datetime import datetime
from contextlib import contextmanager

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, QThread

import qasync

# Import the modules we want to test
from main import ForestApplication, AsyncHelper
from resources import ResourceEventTypes, EventQueue

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Test signals for async operations
class TestSignals(QObject):
    task_completed = pyqtSignal(object)
    task_error = pyqtSignal(str)

# Test worker thread for concurrent operations
class TestWorker(QThread):
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)
    
    def __init__(self, work_func, parent=None):
        super().__init__(parent)
        self.work_func = work_func
    
    def run(self):
        try:
            self.work_func()
            self.finished_signal.emit()
        except Exception as e:
            self.error_signal.emit(str(e))

@pytest.fixture
def qapp():
    """Fixture to create a Qt application instance"""
    app = QApplication.instance() or QApplication(sys.argv)
    yield app
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
async def forest_app(qapp, event_loop):
    """Create a test ForestApplication instance"""
    app = ForestApplication()
    # Initialize app
    await app.setup_async()
    yield app
    # Ensure proper cleanup
    app.close()

@pytest.fixture
def signals():
    """Create test signals for async operation testing"""
    return TestSignals()

@pytest.mark.asyncio
class TestTaskManagement:
    """Tests for task management in ForestApplication"""
    
    async def test_task_registration(self, forest_app):
        """Test registering tasks with the application"""
        # Define a set of test tasks
        async def task1():
            await asyncio.sleep(0.1)
            return "Result 1"
            
        async def task2():
            await asyncio.sleep(0.2)
            return "Result 2"
        
        # Register tasks
        t1 = forest_app.register_task(task1())
        t2 = forest_app.register_task(task2())
        
        # Check that tasks are in the task registry
        assert t1 in forest_app._tasks
        assert t2 in forest_app._tasks
        assert len(forest_app._tasks) == 2
        
        # Wait for tasks to complete
        results = await asyncio.gather(t1, t2)
        
        # Check results
        assert results == ["Result 1", "Result 2"]
        
        # Tasks should be removed from registry after completion
        assert t1 not in forest_app._tasks
        assert t2 not in forest_app._tasks
        assert len(forest_app._tasks) == 0
    
    async def test_task_callback(self, forest_app, signals):
        """Test that task callbacks are executed properly"""
        # Define a task with a result
        async def test_task():
            await asyncio.sleep(0.1)
            return "Task succeeded"
        
        # Define a callback
        result_received = None
        
        def on_complete(task):
            nonlocal result_received
            result_received = task.result()
            signals.task_completed.emit(result_received)
        
        # Register task with callback
        t = forest_app.register_task(test_task(), on_complete)
        
        # Wait for task completion
        await t
        
        # Wait a bit more for the callback to execute
        await asyncio.sleep(0.1)
        
        # Check that callback was executed
        assert result_received == "Task succeeded"
    
    async def test_task_error_handling(self, forest_app, signals):
        """Test error handling in tasks"""
        # Define a task that raises an exception
        async def failing_task():
            await asyncio.sleep(0.1)
            raise ValueError("Task failed intentionally")
        
        # Define callbacks
        error_received = None
        
        def on_complete(task):
            nonlocal error_received
            try:
                # This should raise the original exception
                result = task.result()
                signals.task_completed.emit(result)
            except Exception as e:
                error_received = str(e)
                signals.task_error.emit(str(e))
        
        # Register task with callback
        t = forest_app.register_task(failing_task(), on_complete)
        
        # Wait for task to complete or fail
        try:
            await t
        except ValueError:
            # Expected, continue
            pass
        
        # Wait a bit more for the callback to execute
        await asyncio.sleep(0.1)
        
        # Check that error was received in callback
        assert error_received is not None
        assert "Task failed intentionally" in error_received
    
    async def test_task_cancellation(self, forest_app):
        """Test cancelling tasks"""
        # Define a long-running task
        async def long_task():
            try:
                await asyncio.sleep(10)  # Long enough to be cancelled
                return "Task completed"
            except asyncio.CancelledError:
                return "Task was cancelled"
        
        # Register task
        t = forest_app.register_task(long_task())
        
        # Check task is in registry
        assert t in forest_app._tasks
        
        # Cancel specific task
        t.cancel()
        
        # Wait for cancellation to take effect
        await asyncio.sleep(0.1)
        
        # Check task state
        assert t.cancelled() or t.done()
        
        # Task should be removed from registry
        assert t not in forest_app._tasks
    
    async def test_thread_management(self, forest_app):
        """Test thread registration and management"""
        # Create a test thread
        def thread_work():
            time.sleep(0.2)  # Simulate work
        
        thread = TestWorker(thread_work)
        
        # Register thread with application
        registered_thread = forest_app.register_thread(thread)
        
        # Check thread is in registry
        assert registered_thread in forest_app._threads
        
        # Start thread
        thread.start()
        
        # Wait for thread to finish
        thread.wait(1000)  # 1 second timeout in milliseconds
        
        # Give time for thread finished signal to be processed
        await asyncio.sleep(0.1)
        
        # Thread should be removed from registry
        assert thread not in forest_app._threads
    
    async def test_stop_threads(self, forest_app):
        """Test stopping all threads"""
        # Create multiple test threads
        threads = []
        for i in range(3):
            def thread_work(i=i):
                try:
                    time.sleep(10)  # Long enough to be cancelled
                except:
                    pass  # Thread termination
            
            thread = TestWorker(thread_work)
            threads.append(thread)
            forest_app.register_thread(thread)
            thread.start()
        
        # Check threads are registered
        assert len(forest_app._threads) == 3
        
        # Stop all threads
        forest_app._stop_threads()
        
        # Wait for threads to stop
        await asyncio.sleep(0.5)
        
        # Check threads registry is empty
        assert len(forest_app._threads) == 0
        
        # Check threads are not running
        for thread in threads:
            assert not thread.isRunning()

@pytest.mark.asyncio
class TestErrorHandling:
    """Tests for error handling in ForestApplication"""
    
    async def test_global_exception_handler(self, forest_app, monkeypatch):
        """Test the global exception handler"""
        # Mock show_error_dialog to avoid UI interaction
        dialog_shown = False
        error_message = None
        
        def mock_show_error_dialog(self, title, message):
            nonlocal dialog_shown, error_message
            dialog_shown = True
            error_message = message
        
        monkeypatch.setattr(ForestApplication, '_show_error_dialog', mock_show_error_dialog)
        
        # Simulate an unhandled exception
        exc_type = ValueError
        exc_value = ValueError("Test unhandled exception")
        exc_traceback = None
        
        # Call the handler directly
        forest_app._global_exception_handler(exc_type, exc_value, exc_traceback)
        
        # Check that dialog was shown
        assert dialog_shown
        assert error_message is not None
        assert "Test unhandled exception" in error_message
    
    async def test_handle_error(self, forest_app):
        """Test the error handling method"""
        # Call error handler
        error_id = forest_app._handle_error(
            "Test context",
            "Test error message"
        )
        
        # Check error ID format
        assert error_id is not None
        assert isinstance(error_id, str)
        # Error ID should start with date format YYYYMMDDHHMMSS-
        assert len(error_id) > 15
        
        # More detailed test would require checking logs or UI updates
    
    async def test_handle_fatal_error(self, forest_app, monkeypatch):
        """Test handling of fatal errors"""
        # Mock relevant methods to avoid UI interaction and system exit
        dialog_shown = False
        exit_called = False
        error_details = None
        
        def mock_show_error_dialog(title, message):
            nonlocal dialog_shown, error_details
            dialog_shown = True
            error_details = message
        
        def mock_exit(code):
            nonlocal exit_called
            exit_called = True
            return None
        
        # Patch methods
        monkeypatch.setattr(QApplication, 'exit', lambda code: None)
        monkeypatch.setattr(sys, 'exit', mock_exit)
        monkeypatch.setattr(ForestApplication, '_show_error_dialog', 
                           lambda self, title, message: mock_show_error_dialog(title, message))
        
        # Simulate a fatal error
        test_error = RuntimeError("Fatal test error")
        
        # Handle the fatal error
        try:
            forest_app._handle_fatal_error("Fatal test context", test_error)
        except SystemExit:
            # We're mocking sys.exit, but just in case
            pass
        
        # Check that async helper was shutdown
        assert forest_app.async_helper.shutdown_requested
        
        # Check that dialog was shown
        assert dialog_shown
        assert error_details is not None
        assert "Fatal test error" in error_details
        
        # Check that exit was called
        assert exit_called
    
    async def test_run_async_operation(self, forest_app, signals):
        """Test running an async operation with callbacks"""
        # Define a test coroutine
        async def test_coro():
            await asyncio.sleep(0.1)
            return {"status": "success", "data": "Test result"}
        
        # Define callbacks
        result_received = None
        error_received = None
        
        def on_success(result):
            nonlocal result_received
            result_received = result
            signals.task_completed.emit(result)
        
        def on_error(error):
            nonlocal error_received
            error_received = error
            signals.task_error.emit(error)
        
        # Run the operation
        forest_app.run_async_operation(test_coro(), on_success, on_error)
        
        # Wait for operation to complete
        await asyncio.sleep(0.5)
        
        # Check results
        assert result_received is not None
        assert result_received == {"status": "success", "data": "Test result"}
        assert error_received is None
    
    async def test_run_async_operation_error(self, forest_app, signals):
        """Test error handling in run_async_operation"""
        # Define a failing coroutine
        async def failing_coro():
            await asyncio.sleep(0.1)
            raise ValueError("Test operation error")
        
        # Define callbacks
        result_received = None
        error_received = None
        
        def on_success(result):
            nonlocal result_received
            result_received = result
            signals.task_completed.emit(result)
        
        def on_error(error):
            nonlocal error_received
            error_received = error
            signals.task_error.emit(error)
        
        # Run the operation
        forest_app.run_async_operation(failing_coro(), on_success, on_error)
        
        # Wait for operation to complete
        await asyncio.sleep(0.5)
        
        # Check results
        assert result_received is None
        assert error_received is not None
        assert "Test operation error" in error_received

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])