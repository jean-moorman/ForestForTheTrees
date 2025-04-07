import unittest
import sys
import time
import asyncio
import threading
import pytest
import logging
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QThread, QObject, pyqtSignal
import qasync

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_main_async')

# Import the main module components to test, but NOT directly
# We'll patch these during tests to avoid creating real components

class TestThread(QThread):
    """A test thread class that simulates work for testing thread management"""
    finished_signal = pyqtSignal()
    
    def __init__(self, sleep_time=0.5, should_finish=True):
        super().__init__()
        self.sleep_time = sleep_time
        self.should_finish = should_finish
        self.running = True
        
    def run(self):
        """Run method that simulates work"""
        logger.debug(f"TestThread started (sleep={self.sleep_time})")
        
        # Simulate work with a sleep
        start_time = time.time()
        while self.running and (time.time() - start_time < self.sleep_time):
            time.sleep(0.1)
            
        if self.should_finish and self.running:
            logger.debug("TestThread emitting finished_signal")
            self.finished_signal.emit()
            
        logger.debug("TestThread exiting run method")
        
    def stop(self):
        """Stop the thread's work"""
        logger.debug("TestThread stop requested")
        self.running = False

class TestAsyncTask:
    """A class to help test async task behavior"""
    def __init__(self, sleep_time=0.5, should_complete=True, should_raise=False):
        self.sleep_time = sleep_time
        self.should_complete = should_complete
        self.should_raise = should_raise
        self.started = False
        self.completed = False
        self.cancelled = False
        self.exception = None
        
    async def run(self):
        """Async task that can be used for testing"""
        self.started = True
        logger.debug(f"TestAsyncTask started (sleep={self.sleep_time})")
        
        try:
            # Track progress for the task
            start_time = time.time()
            while time.time() - start_time < self.sleep_time:
                # Check for cancellation - safely handle None case
                current_task = asyncio.current_task()
                if current_task and current_task.cancelled():
                    logger.debug("TestAsyncTask was cancelled")
                    self.cancelled = True
                    raise asyncio.CancelledError()
                    
                # Yield to allow cancellation to be processed
                await asyncio.sleep(0.1)
                
            # Either complete normally or raise an exception
            if self.should_raise:
                logger.debug("TestAsyncTask raising test exception")
                self.exception = ValueError("Test exception")
                raise self.exception
                
            logger.debug("TestAsyncTask completed successfully")
            self.completed = True
            return "Task completed"
        except asyncio.CancelledError:
            logger.debug("TestAsyncTask cancelled")
            self.cancelled = True
            raise
        except Exception as e:
            logger.debug(f"TestAsyncTask failed with exception: {e}")
            self.exception = e
            raise

# We need to test specific components in isolation rather than the full app
class TestThreadManagement(unittest.TestCase):
    """Test cases for thread management functionality"""
    
    def setUp(self):
        """Set up test environment"""
        logger.debug("Setting up thread management test")
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        
        # Create test storage
        self._threads = set()
        self.test_threads = []
        
    def tearDown(self):
        """Clean up after tests"""
        logger.debug("Tearing down thread management test")
        
        # Stop any running threads
        for thread in self.test_threads:
            if thread.isRunning():
                thread.stop()
                thread.quit()
                thread.wait(1000)  # Wait up to 1 second
                if thread.isRunning():
                    logger.warning(f"Force terminating thread: {thread}")
                    thread.terminate()
                    thread.wait(500)  # Wait a bit more
        
    def _thread_finished(self, thread):
        """Handle thread completion."""
        logger.debug(f"Thread finished: {thread}")
        self._threads.discard(thread)

    def register_thread(self, thread):
        """Register a QThread for tracking and cleanup."""
        # Record thread for tracking
        self._threads.add(thread)
        
        # Define a direct handler for each thread to ensure proper capturing
        def on_thread_finished():
            logger.debug(f"Signal handler removing thread from tracking: {thread}")
            self._thread_finished(thread)
        
        # Connect the appropriate signal with a direct handler
        if hasattr(thread, 'finished_signal'):
            thread.finished_signal.connect(on_thread_finished)
        else:
            thread.finished.connect(on_thread_finished)
        
        # Track thread state for debugging
        thread.started.connect(lambda: logger.debug(f"Thread started: {thread}"))
        
        return thread
        
    def test_thread_registration(self):
        """Test that threads are properly registered and tracked"""
        # Create and register a test thread
        thread = TestThread(sleep_time=0.2)
        self.register_thread(thread)
        
        # Add to test threads for cleanup
        self.test_threads.append(thread)
        
        # Verify thread is registered
        self.assertIn(thread, self._threads)
        
        # Start the thread and wait for it to finish
        thread.start()
        result = thread.wait(1000)  # Wait up to 1 second
        
        # Process events multiple times to ensure signal handlers run
        # This is crucial for Qt's signal-slot mechanism to work properly
        for _ in range(3):  # Process events multiple times
            self.app.processEvents()
            time.sleep(0.05)  # Small delay between processing
        
        # Verify thread completed and was removed from tracking
        self.assertTrue(result)
        self.assertNotIn(thread, self._threads)
        
    def test_stop_threads(self):
        """Test stopping threads with the improved method"""
        # Create and register multiple test threads
        threads = [
            TestThread(sleep_time=0.2),  # Short running, should finish quickly
            TestThread(sleep_time=5.0),  # Long running, will need to be terminated
            TestThread(sleep_time=0.3)   # Another short one
        ]
        
        # Register and start all threads
        for thread in threads:
            self.register_thread(thread)
            thread.start()
            
        # Add to test threads for cleanup
        self.test_threads.extend(threads)
        
        # Verify threads are registered
        for thread in threads:
            self.assertIn(thread, self._threads)
            
        # Define the stop_threads method from our improved code
        def _stop_threads():
            """Stop all managed threads safely with improved timeout handling."""
            thread_count = len(self._threads)
            if thread_count == 0:
                logger.debug("No threads to stop")
                return
                
            logger.info(f"Stopping {thread_count} threads...")
            
            # Make a copy to avoid modification during iteration
            threads_to_stop = list(self._threads)
            
            # First ask all threads to quit
            for thread in threads_to_stop:
                if thread.isRunning():
                    logger.debug(f"Requesting thread to quit: {thread}")
                    thread.quit()
            
            # Then wait for them with a timeout, one by one with progress
            deadline = time.time() + 5.0  # 5 second total timeout
            remaining_threads = list(threads_to_stop)
            
            while remaining_threads and time.time() < deadline:
                for thread in list(remaining_threads):  # Use a copy for iteration
                    # Check if the thread has finished
                    if not thread.isRunning():
                        logger.debug(f"Thread stopped gracefully: {thread}")
                        remaining_threads.remove(thread)
                        continue
                        
                    # Wait a bit more with decreasing time
                    remaining_time = max(0.1, deadline - time.time())
                    if thread.wait(int(remaining_time * 1000)):  # wait takes milliseconds
                        logger.debug(f"Thread stopped after waiting: {thread}")
                        remaining_threads.remove(thread)
                
                # Small sleep to prevent CPU spiking in this loop
                time.sleep(0.05)
            
            # Forcefully terminate any remaining threads, one by one with logging
            for thread in remaining_threads:
                logger.warning(f"Thread did not quit gracefully, terminating: {thread}")
                thread.terminate()
                # Small wait to allow the termination to take effect
                thread.wait(100)  # Wait 100ms
                    
            # Clear the set AFTER all threads are confirmed stopped
            self._threads.clear()
            logger.info("All threads stopped")
            
        # Stop all threads using our method
        _stop_threads()
        
        # Verify all threads are stopped and cleared from tracking
        for thread in threads:
            self.assertFalse(thread.isRunning())
            
        self.assertEqual(len(self._threads), 0)


class TestAsyncHelperMock(QObject):
    """A mockable version of AsyncHelper for testing"""
    errorOccurred = pyqtSignal(str)
    taskCompleted = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.shutdown_requested = False
        self._tasks = []
        
    def run_coroutine(self, coro, callback=None, error_callback=None):
        """Mock implementation"""
        if self.shutdown_requested:
            if error_callback:
                error_callback("Operation cancelled: shutdown in progress")
            return None
            
        loop = asyncio.get_event_loop()
        task = loop.create_task(coro)
        self._tasks.append(task)
        
        async def _wrapper():
            try:
                result = await task
                if callback:
                    callback(result)
                self.taskCompleted.emit({"status": "success", "result": result})
                return result
            except Exception as e:
                self.errorOccurred.emit(str(e))
                if error_callback:
                    error_callback(str(e))
                self.taskCompleted.emit({"status": "error", "error": str(e)})
                raise
                
        loop.create_task(_wrapper())
        return task
        
    def request_shutdown(self):
        """Mark shutdown in progress"""
        self.shutdown_requested = True
        
        # Cancel tasks
        for task in self._tasks:
            if not task.done() and not task.cancelled():
                task.cancel()


@pytest.mark.asyncio(scope="function")
class TestAsyncOperations:
    """Test cases for async operations"""

    @pytest.fixture
    def event_loop(self, request):
        """Create an instance of the default event loop for each test case.
        Using pytestmark to set loop scope is the pytest-asyncio recommended approach.
        """
        # Get or create QApplication for Qt integration
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
            
        # Create and set the QEventLoop for this test
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        # Pass the loop to the test
        yield loop
        
        # Clean up
        app.processEvents()
        
        # Close the loop - this is important for pytest-asyncio warnings
        loop.close()

    def setup_method(self):
        """Set up each test method"""
        # Get existing QApplication or create one
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
                
        # Use the event loop provided by the fixture instead of creating a new one
        self.loop = asyncio.get_event_loop()
                
        # Create the async helper
        self.async_helper = TestAsyncHelperMock()
            
        # Tasks for tracking
        self._tasks = set()
        self.test_tasks = []
        
    def teardown_method(self):
        """Clean up after each test method"""
        # Cancel any pending tasks
        for task in self.test_tasks:
            if not task.done() and not task.cancelled():
                task.cancel()
                    
        # Request shutdown
        if hasattr(self, 'async_helper'):
            self.async_helper.request_shutdown()
        
        # Process any pending Qt events
        if hasattr(self, 'app'):
            self.app.processEvents()
        
        # Clean up task references
        self._tasks.clear()
        self.test_tasks.clear()
        
        # DON'T explicitly close the loop - pytest-asyncio will handle this

    def register_task(self, coro):
        """Register an asyncio task for tracking with improved error handling"""
        try:
            # Get the current event loop instead of using self.loop directly
            loop = asyncio.get_event_loop()
            
            # Create the task
            task = loop.create_task(coro)
            
            # Add task lifecycle management
            def _on_task_complete(task):
                # Remove the task from registry
                self._tasks.discard(task)
            
            task.add_done_callback(_on_task_complete)
            self._tasks.add(task)
            self.test_tasks.append(task)
            return task
        except Exception as e:
            logger.error(f"Failed to register task: {e}")
            raise
        
    async def test_async_task_completion(self):
        """Test that async tasks complete properly"""
        # Create a test task
        test_task = TestAsyncTask(sleep_time=0.2)
        
        # Register the task
        task = self.register_task(test_task.run())
        
        # Wait for the task to complete
        await task
        
        # Verify task completed and was removed from tracking
        assert task.done()
        assert task not in self._tasks
        assert test_task.completed
        
    async def test_async_task_cancellation(self):
        """Test that tasks can be cancelled"""
        # Create a test task
        test_task = TestAsyncTask(sleep_time=1.0)
        
        # Register the task
        task = self.register_task(test_task.run())
        
        # Wait a bit then cancel
        await asyncio.sleep(0.1)
        task.cancel()
        
        # Wait for the task to be cancelled
        try:
            await task
        except asyncio.CancelledError:
            pass
            
        # Verify task was cancelled
        assert task.cancelled()
        assert task not in self._tasks
        
    async def test_async_helper(self):
        """Test that AsyncHelper properly runs coroutines"""
        # Create a test task
        test_task = TestAsyncTask(sleep_time=0.2)
        
        # Create callback mocks
        success_callback = MagicMock()
        error_callback = MagicMock()
        
        # Use AsyncHelper to run the coroutine
        self.async_helper.run_coroutine(
            test_task.run(),
            callback=success_callback,
            error_callback=error_callback
        )
        
        # Wait for the task to complete
        while not test_task.completed and not test_task.cancelled and test_task.exception is None:
            await asyncio.sleep(0.1)
            
        # Verify callbacks were called correctly
        assert success_callback.called
        assert not error_callback.called
        
    async def test_async_helper_error_handling(self):
        """Test that AsyncHelper properly handles errors in coroutines"""
        # Create a test task that will raise an exception
        test_task = TestAsyncTask(sleep_time=0.2, should_raise=True)
        
        # Create callback mocks
        success_callback = MagicMock()
        error_callback = MagicMock()
        
        # Use AsyncHelper to run the coroutine
        self.async_helper.run_coroutine(
            test_task.run(),
            callback=success_callback,
            error_callback=error_callback
        )
        
        # Wait for the task to fail
        while not test_task.exception:
            await asyncio.sleep(0.1)
            
        # Verify callbacks were called correctly
        assert not success_callback.called
        assert error_callback.called
        
    async def test_async_helper_shutdown(self):
        """Test that AsyncHelper properly handles shutdown"""
        # Create test task and callbacks
        test_task = TestAsyncTask(sleep_time=5.0)
        error_callback = MagicMock()
        
        # Request shutdown
        self.async_helper.request_shutdown()
        
        # Try to run a coroutine (should be rejected)
        self.async_helper.run_coroutine(
            test_task.run(),
            error_callback=error_callback
        )
        
        # Verify the error callback was called
        assert error_callback.called
        
        # Verify no task was started
        assert not test_task.started

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])