"""
Pytest configuration file for Forest application tests.
Contains shared fixtures and configuration for all test modules.
"""
import pytest
import asyncio
import sys
import time
import os
import logging
from datetime import datetime

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

import qasync

# Import application modules
from resources import EventQueue

# Configure logging
@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """Configure logging for the test session"""
    log_dir = os.path.join(os.path.dirname(__file__), "test_logs")
    
    # Create log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"test_{timestamp}.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Log test session start
    logger = logging.getLogger("pytest")
    logger.info(f"Starting test session at {datetime.now()}")
    
    yield
    
    # Log test session end
    logger.info(f"Test session completed at {datetime.now()}")

# Qt application fixture
@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session"""
    app = QApplication.instance() or QApplication(sys.argv)
    # Important: don't show any windows during testing
    app.setQuitOnLastWindowClosed(False)
    yield app
    # Make sure we process events before clearing
    app.processEvents()
    
    # Don't quit the app between tests
    # It will be cleaned up at the end of the session

# Event loop fixture
@pytest.fixture
def event_loop(qapp):
    """Create an event loop for each test"""
    loop = qasync.QEventLoop(qapp)
    asyncio.set_event_loop(loop)
    
    # Log event loop creation
    logger = logging.getLogger("pytest")
    logger.debug(f"Created event loop {id(loop)} on thread {hex(id(asyncio.current_task()._loop))}")
    
    yield loop
    
    # Log pending tasks
    pending_tasks = asyncio.all_tasks(loop)
    if pending_tasks:
        logger.warning(f"Found {len(pending_tasks)} pending tasks during loop cleanup")
        
    # Clean up pending tasks
    for task in pending_tasks:
        if not task.done():
            task.cancel()
    
    # Run loop until tasks are cancelled
    loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
    
    # Check if the loop was closed by another fixture
    if not loop.is_closed():
        loop.close()

# Event queue fixture
@pytest.fixture
async def event_queue(event_loop):
    """Create an EventQueue for testing"""
    queue = EventQueue()
    await queue.start()
    
    # Log queue creation
    logger = logging.getLogger("pytest")
    logger.debug(f"Created EventQueue {id(queue)}")
    
    yield queue
    
    # Stop queue after test
    await queue.stop()
    logger.debug(f"Stopped EventQueue {id(queue)}")

# Test signals class
class TestSignals(QObject):
    """Test signals for async operations"""
    task_completed = pyqtSignal(object)
    task_error = pyqtSignal(str)
    event_received = pyqtSignal(str, object)

@pytest.fixture
def signals():
    """Create test signals for async operation testing"""
    return TestSignals()

# Configure pytest 
def pytest_configure(config):
    """Configure pytest"""
    # Register custom markers
    config.addinivalue_line("markers", "asyncio: mark test as asyncio test")
    config.addinivalue_line("markers", "slow: mark test as slow to run")
    config.addinivalue_line("markers", "gui: mark test as requiring GUI")