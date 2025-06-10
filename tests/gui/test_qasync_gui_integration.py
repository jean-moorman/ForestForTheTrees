#!/usr/bin/env python3
"""
Test qasync + GUI integration to reproduce and validate the event loop fix.
"""

import asyncio
import sys
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import pyqtSignal
import qasync
from qasync import asyncSlot

from resources.events.loop_management import EventLoopManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestMainWindow(QMainWindow):
    """Test main window that mimics the real system's event loop usage pattern."""
    
    error_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test qasync GUI Integration")
        self.setGeometry(100, 100, 400, 200)
        
        # Create UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        self.button = QPushButton("Test Async Processing")
        self.button.clicked.connect(self._handle_button_click)
        layout.addWidget(self.button)
        
        # Connect error signal
        self.error_signal.connect(self._handle_error)
    
    def _get_qasync_compatible_loop(self) -> asyncio.AbstractEventLoop:
        """Get event loop with qasync compatibility (same as main_window.py)."""
        from resources.events.loop_management import EventLoopManager
        
        # Strategy 1: Try to get running loop (works in most qasync contexts)
        try:
            current_loop = asyncio.get_running_loop()
            logger.debug(f"Found running loop via asyncio: {id(current_loop)}")
            return current_loop
        except RuntimeError:
            pass
        
        # Strategy 2: Use EventLoopManager primary loop (qasync-aware)
        primary_loop = EventLoopManager.get_primary_loop()
        if primary_loop and not primary_loop.is_closed():
            logger.debug(f"Using EventLoopManager primary loop: {id(primary_loop)}")
            # Ensure this loop is set as the current event loop for the thread
            try:
                asyncio.set_event_loop(primary_loop)
            except Exception as e:
                logger.debug(f"Could not set primary loop as current: {e}")
            return primary_loop
        
        # Strategy 3: Get thread's default event loop
        try:
            thread_loop = asyncio.get_event_loop()
            logger.debug(f"Using thread event loop: {id(thread_loop)}")
            return thread_loop
        except RuntimeError:
            pass
        
        # Strategy 4: Last resort - create new loop
        logger.warning("No event loop found, creating new one")
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        EventLoopManager.set_primary_loop(new_loop)
        return new_loop
    
    def _handle_button_click(self):
        """Handle button click - mirrors _handle_prompt_submission pattern."""
        try:
            logger.info("Button clicked, starting async processing...")
            
            # Get loop using robust method
            loop = self._get_qasync_compatible_loop()
            logger.info(f"Using loop {id(loop)} for task creation")
            
            # Create task in the loop context
            task = loop.create_task(self._process_async())
            task.add_done_callback(self._handle_task_done)
            
        except Exception as e:
            logger.error(f"Failed to start async processing: {e}")
            self.error_signal.emit(f"Failed to start processing: {e}")
    
    async def _process_async(self):
        """Async processing that mirrors _process_prompt_async pattern."""
        logger.info("=== Starting async processing ===")
        
        # Get loop using the same robust method
        current_loop = self._get_qasync_compatible_loop()
        logger.info(f"Using event loop {id(current_loop)} for async processing")
        
        # Test the specific pattern that fails in the real system
        for step in range(3):
            logger.info(f"Step {step + 1}/3: Processing...")
            
            # This mimics the problematic pattern in main_window.py:304
            try:
                # Create a nested task (what fails in production)
                nested_coro = self._nested_async_operation(step)
                nested_task = current_loop.create_task(nested_coro)
                
                # Use wait_for (where the failure occurs)
                result = await asyncio.wait_for(nested_task, timeout=5.0)
                logger.info(f"Step {step + 1} completed: {result}")
                
            except Exception as e:
                logger.error(f"Step {step + 1} failed: {e}")
                raise
        
        logger.info("=== Async processing completed successfully ===")
        return {"status": "success", "steps_completed": 3}
    
    async def _nested_async_operation(self, step: int):
        """Nested async operation that simulates orchestrator calls."""
        await asyncio.sleep(0.1)  # Simulate work
        
        # Test loop detection again (this is where the real system fails)
        try:
            running_loop = asyncio.get_running_loop()
            logger.debug(f"Step {step}: Nested operation has running loop {id(running_loop)}")
        except RuntimeError as e:
            logger.error(f"Step {step}: No running loop in nested operation: {e}")
            raise
        
        return f"step_{step}_result"
    
    def _handle_task_done(self, task):
        """Handle task completion."""
        try:
            if task.exception():
                error = task.exception()
                logger.error(f"Async task failed: {error}")
                self.error_signal.emit(f"Processing failed: {error}")
            else:
                result = task.result()
                logger.info(f"Async task completed successfully: {result}")
        except Exception as e:
            logger.error(f"Error handling task completion: {e}")
    
    def _handle_error(self, message: str):
        """Handle error signal."""
        logger.error(f"GUI Error: {message}")


def main():
    """Main function that mimics run_phase_one.py setup."""
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create qasync loop (same as run_phase_one.py)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    logger.info(f"Created qasync event loop: {id(loop)}")
    
    # Register with EventLoopManager (same as run_phase_one.py)
    result = EventLoopManager.set_primary_loop(loop)
    logger.info(f"Registered main event loop with EventLoopManager: {result}")
    
    # Create and show main window
    window = TestMainWindow()
    window.show()
    
    logger.info("Starting application event loop...")
    
    with loop:
        try:
            return app.exec()
        except Exception as e:
            logger.error(f"Application error: {e}")
            return 1


if __name__ == "__main__":
    sys.exit(main())